#!/usr/bin/env python3
"""One command from an episode spec to an upload package. Fixed order, fail closed, actionable errors.

  .venv/bin/python factory/make_short.py fetch    episodes/specs/<id>.json     download sources[] of a skeleton spec (before validate)
  .venv/bin/python factory/make_short.py validate episodes/specs/<id>.json     steps 1-4 (seconds; no TTS, no render)
  .venv/bin/python factory/make_short.py build    episodes/specs/<id>.json [--from STEP] [--force-tts]
  .venv/bin/python factory/make_short.py stages   [--tags money,bank] [--channel myeotnyeon]
  .venv/bin/python factory/make_short.py selftest
  .venv/bin/python factory/make_short.py post     upload/pkg/<id>_B

Steps: schema -> facts -> policy -> compile (+ layout checks) -> tts -> voice (whisper match, retries, rewrites)
-> timing (option onsets, cues, lip) -> render -> assemble -> gate -> post -> package.
Writes upload/pkg/<id>_B/build.json (every step, status, detail). READY.txt is written only when every step passes.
The legacy b_format path (specs/<id>.json + build_intl.sh / manual ko steps) is untouched and still works."""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from factory.shorts import core, policy  # noqa: E402
from factory.shorts.core import BF, PKG, LIB, Fail  # noqa: E402

V = ROOT / '.venv/bin/python'
K = ROOT / 'research/tts_kokoro/.venv/bin/python'
MLX = ROOT / 'research/tts_bakeoff/venvs/mlx/bin/python'
STEPS = ['schema', 'facts', 'policy', 'compile', 'tts', 'voice', 'timing', 'render', 'assemble', 'gate', 'post', 'package']
SYN = json.loads((ROOT / 'factory/shorts/synonyms.json').read_text())


def sh(cmd, cwd=BF, env=None, check=True, tail=6):
    r = subprocess.run([str(x) for x in cmd], cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    out = (r.stdout + r.stderr).strip().splitlines()
    if check and r.returncode != 0:
        raise Fail('run', [f'{" ".join(str(x) for x in cmd[:3])} exited {r.returncode}: ' + ' | '.join(out[-tail:])])
    return r.returncode, out


class Build:
    def __init__(self, spec_path, force_tts=False):
        self.path = Path(spec_path).resolve()
        self.spec = json.loads(self.path.read_text())
        self.id = self.spec.get('id', 'unknown')
        self.L = self.spec.get('locale', 'ko')
        self.P = PKG / f'{self.id}_B'
        self.force_tts = force_tts
        self.log = dict(spec=str(self.path), id=self.id, started=dt.datetime.now().isoformat(timespec='seconds'), steps=[])
        self.values = {}
        self.py = V if self.L == 'ko' else K
        self.dry = False

    def save(self):
        if self.dry:  # validate never touches upload/pkg or b_format/specs
            d = ROOT / 'episodes/specs/_compiled'
            d.mkdir(parents=True, exist_ok=True)
            (d / f'{self.id}.validate.json').write_text(json.dumps(self.log, ensure_ascii=False, indent=1))
            return
        self.P.mkdir(parents=True, exist_ok=True)
        (self.P / 'build.json').write_text(json.dumps(self.log, ensure_ascii=False, indent=1))

    # ---- 1-3
    def s_schema(self):
        e = core.validate(self.spec, core.SCHEMA)
        e = e or core.placeholder_text(self.spec)
        if not e and self.L == 'ko' and self.spec.get('variant') != 'BC':
            e = core.title_rules_ko(self.spec.get('title'))
        if e:
            raise Fail('schema', e)
        return 'valid'

    def s_facts(self):
        got = policy.fetch_sources(self.spec)
        policy.check_facts(self.spec, got)
        self.values = core.fact_values(self.spec)
        return {k: v[0] for k, v in got.items()} | {'values': len(self.values)}

    def s_policy(self):
        e, w = policy.lint(self.spec)
        if e:
            raise Fail('policy', e)
        return {'warnings': w}

    # ---- 4
    def s_compile(self):
        if self.spec['variant'] == 'BC':
            return self.compile_bc()
        self.values = self.values or core.fact_values(self.spec)
        e, w = core.check_b3(self.spec, self.values)
        if e:
            raise Fail('layout', e)
        leg = core.compile_b3(self.apply_rewrites(self.spec), self.values)
        out_path = BF / 'specs' / f'{self.id}.json' if not self.dry else ROOT / 'episodes/specs/_compiled' / f'{self.id}.json'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(leg, ensure_ascii=False, indent=1))
        if self.L != 'ko':  # en/ja chunks: linebreak.py rules (Kokoro venv: fugashi for ja)
            code = ('import json,sys;sys.path.insert(0,".");import linebreak as lb;p=sys.argv[1];s=json.load(open(p));bad=[]\n'
                    'for l in s["lines"]:\n if l.get("shown") and l.get("chunks") in (None,"auto"): l["chunks"]=lb.chunks(l["shown"],s["locale"])\n'
                    ' if l.get("shown"): bad+=[l["id"]+" "+b for b in lb.check(l["chunks"],s["locale"])]\n'
                    'json.dump(s,open(p,"w"),ensure_ascii=False,indent=1);print(json.dumps(bad))')
            _, o = sh([K, '-c', code, out_path])
            if json.loads(o[-1]):
                raise Fail('layout', ['subtitle chunks: ' + ' | '.join(json.loads(o[-1]))])
        leg = json.loads(out_path.read_text())
        bad = core.placeholder_text(leg, ('shown', 'chunks')) + self.lint_chunks(leg) + core.desk_repeats(leg)
        if bad:
            raise Fail('layout', bad)
        return {'warnings': w, 'lines': len(leg['lines']), 'pops': [p['big'] for p in leg['pops']]}

    def lint_chunks(self, leg):
        errs = []
        mx = {'ko': 14, 'en': 32, 'ja': 14}[self.L]
        for ln in leg['lines']:
            for x in ln.get('chunks') or []:
                if len(x) > mx:
                    errs.append(f'{ln["id"]} subtitle chunk "{x}" is {len(x)} chars > {mx} -> add a comma or shorten the line')
        if self.L == 'ko':
            flat = [x for ln in leg['lines'] for x in (ln.get('chunks') or [])]
            errs += [f'subtitle break "{a} / {b}" splits one amount in two cues -> remove the comma or reword so the amount stays together'
                     for a, b in zip(flat, flat[1:]) if core.split_number(a, b)]
            from factory.qa import subtitle_ko
            cues = [dict(idx=i, lines=[x], text=x, start=0, end=0) for i, x in enumerate(x for ln in leg['lines'] for x in (ln.get('chunks') or []))]
            rows, _ = subtitle_ko.lint_cues(cues, line_max=14)
            errs += [f'subtitle break "{r.get("before", r.get("text", ""))} / {r.get("after", "")}": {r["code"]} -> rephrase or move the comma'
                     for r in rows if r.get('severity') == 'FAIL']
        return errs

    def apply_rewrites(self, spec):
        rw = self.rewrites()
        if not rw:
            return spec
        s = json.loads(json.dumps(spec))
        for k, ln in zip(core.beat_keys(s['lines']), s['lines']):
            for a, b in rw.get(k, []):
                ln['text'] = ln['text'].replace(a, b)
                if ln.get('say'):
                    ln['say'] = ln['say'].replace(a, b)
        return s

    def rewrites(self):
        p = self.path.with_suffix('.rewrites.json')
        return json.loads(p.read_text()) if p.exists() else {}

    def compile_bc(self):
        from factory.shorts import bc
        e, w, leg = bc.compile_spec(self.spec)
        if e:
            raise Fail('layout', e)
        leg['source_spec'] = str(self.path.relative_to(ROOT))
        out = core.BC_DIR / 'specs' / f'{self.id}.json'
        if self.dry or (out.exists() and 'source_spec' not in json.loads(out.read_text())):
            out = ROOT / 'episodes/specs/_compiled' / f'{self.id}.bc.json'  # never overwrite a hand-made BC spec
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(leg, ensure_ascii=False, indent=1))
        return {'warnings': w, 'bc_spec': str(out.relative_to(ROOT)), 'stats': [[x.get('a', {}).get('big'), x.get('b', {}).get('big')] for x in leg['stats']]}

    # ---- 5-6
    def s_tts(self):
        R = BF / 'raw' / self.id
        # takes are reused only when every line's spoken text is unchanged (q049 11-14: a rewritten spec reused the old takes by line id)
        want = {l['id']: l['tts'] for l in json.loads((BF / 'specs' / f'{self.id}.json').read_text())['lines'] if l.get('tts')}
        man = R / '_tts.json'
        same = man.exists() and json.loads(man.read_text()) == want
        if R.exists() and any(R.glob('*.wav')) and not self.force_tts and same:
            return f'reused {len(list(R.glob("*.wav")))} takes (use --force-tts to redo)'
        # no manifest: nothing says what the old takes speak, so they are synthesized again, never reused
        t = time.time()
        if self.L == 'ko':
            for style, take in [('normal', 1), ('fast', 1), ('normal', 2), ('fast', 2)]:
                sh([MLX, 'synth.py', self.id, style, take], tail=3)
        elif self.L == 'ja':
            self.voicevox_up()
            sh([K, 'synth_voicevox.py', self.id], tail=3)
        else:
            sh([K, 'synth_kokoro.py', self.id], tail=3)
        man.write_text(json.dumps(want, ensure_ascii=False))
        return f'{len(list(R.glob("*.wav")))} takes in {time.time() - t:.0f}s'

    def voicevox_up(self):
        import urllib.request
        def ok():
            try:
                return urllib.request.urlopen('http://127.0.0.1:50121/version', timeout=2).status == 200
            except OSError:
                return False
        if ok():
            return
        run = ROOT / 'research/tts_voicevox/macos-arm64/run'
        if not run.exists():
            raise Fail('tts', [f'VOICEVOX engine missing at {run} -> ask the coordinator'])
        subprocess.Popen([str(run), '--port', '50121'], cwd=run.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(60):
            time.sleep(2)
            if ok():
                return
        raise Fail('tts', ['VOICEVOX engine did not start on port 50121 within 120 s'])

    def s_voice(self):
        notes = []
        for rnd in range(3):
            sh([self.py, 'pace.py', self.id], tail=4)
            _, out = sh([self.py, '-m', 'factory.shorts.voice', 'check', self.id], cwd=ROOT)
            bad = json.loads(out[-1])['bad']
            if not bad:
                return {'rounds': rnd + 1, 'notes': notes}
            ids = [b[0] for b in bad]
            notes.append(f'round {rnd + 1}: {bad}')
            if rnd == 2:
                break
            # new takes for the failing lines only (different seed for Qwen, different speeds for Kokoro)
            if self.L == 'ko':
                for style in ('normal', 'fast'):
                    sh([MLX, 'synth.py', self.id, style, 3 + rnd, *ids], tail=3)
            else:
                spec = json.loads((BF / 'specs' / f'{self.id}.json').read_text())
                key = 'vv_speeds' if self.L == 'ja' else 'speeds'
                for ln in spec['lines']:
                    if ln['id'] in ids:
                        ln[key] = [[1.05, 1.15], [0.95, 1.25]][rnd] if self.L == 'en' else [[0.95, 1.1], [0.9, 1.2]][rnd]
                (BF / 'specs' / f'{self.id}.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1))
                if self.L == 'ja':
                    self.voicevox_up()
                sh([K, 'synth_voicevox.py' if self.L == 'ja' else 'synth_kokoro.py', self.id, *ids], tail=3)
        # deterministic rewording from the synonym table, then a fresh compile + tts for those lines
        leg = json.loads((BF / 'specs' / f'{self.id}.json').read_text())
        by_id = {ln['id']: ln for ln in leg['lines']}
        keys = core.beat_keys(self.spec['lines'])
        id2key = dict(zip(core.legacy_ids(keys), keys))
        rw, applied = self.rewrites(), []
        for lid, e, heard in bad:
            key = id2key.get(lid)
            text = by_id[lid]['shown'] or ''
            pair = next(([a, b] for a, b in SYN.get(self.L, []) if a in text and [a, b] not in rw.get(key or '', [])), None)
            if key and pair:
                rw.setdefault(key, []).append(pair)
                applied.append((lid, *pair))
        if not applied or len(applied) < len(bad):
            raise Fail('voice', [self.voice_fix(lid, e, heard, by_id[lid], id2key.get(lid))
                                 for lid, e, heard in bad if lid not in [a[0] for a in applied]] + [f'rewrote {a}' for a in applied])
        self.path.with_suffix('.rewrites.json').write_text(json.dumps(rw, ensure_ascii=False, indent=1))
        raise Fail('voice', [f'applied synonym rewrite {a[0]}: "{a[1]}" -> "{a[2]}"; rerun: make_short.py build {self.path} --from compile --force-tts' for a in applied])

    def voice_fix(self, lid, e, heard, ln, key):
        """one exact instruction per misheard line: which spec field to edit and the command to run next (zzh054: the operator stopped here)"""
        rel = os.path.relpath(self.path, ROOT)
        cmd = f'.venv/bin/python factory/make_short.py build {rel} --from compile --force-tts'
        head = f'{lid}: whisper heard "{heard}" (CER {e}) for "{ln["tts"]}" after 3 rounds of takes'
        if key is None:  # compiler-made line (choices, options, answer, opinion): the operator cannot reword it
            return f'{head} -> this line is fixed compiler text, not yours to edit: stop and report "{lid} {ln["mode"]} misheard" to the coordinator'
        n = core.beat_keys(self.spec['lines']).index(key)
        return (f'{head} -> edit lines[{n}].text (beat {key}) in {rel}: use plainer words with the same meaning (no rare names, no abbreviations, '
                f'no letters), keep every fact value, then run: {cmd}')

    def s_timing(self):
        _, out = sh([self.py, '-m', 'factory.shorts.voice', 'options', self.id], cwd=ROOT)
        opt = json.loads(out[-1])
        sh([self.py, 'b3post.py', self.id], tail=3)
        sh(['python3', 'look/v2/lipdata.py', self.id])
        sh(['python3', 'lip_case.py', self.id])
        c = json.loads((self.P / 'case.json').read_text())
        E = core.lead_silence_rule(core.first_sound_s(self.P / 'narration.wav'), c['utterances'][0].get('take', ''))  # R2, every locale
        for u in c['utterances']:
            n = len(u.get('shots') or []) or 1
            if u['dur'] / n < 15 and u['mode'] not in ('loop', 'choices'):
                E.append(f'{u["id"]}: {u["dur"]} frames for {n} shots (< 0.5 s per shot) -> lengthen the line or drop a shot')
        E += [f'two shots in a row look the same ({r}) -> change the scene or expression of the second shot' for r in core.repeated_shots(c['utterances'])]
        for s in c['subtitles']:
            if s['end_s'] - s['start_s'] < .4:
                E.append(f'subtitle "{s["text"]}" shows {s["end_s"] - s["start_s"]:.2f}s (< 0.4 s) -> merge with a neighbour (fewer commas)')
        if not 18 <= c['duration'] <= 40:
            E.append(f'duration {c["duration"]:.1f}s outside 18-40 s -> {"add" if c["duration"] < 18 else "cut"} a fact line')
        if E:
            raise Fail('timing', E)
        return {'duration_s': round(c['duration'], 2), 'options': opt, 'cues': len(c['subtitles'])}

    # ---- 7-9
    def s_render(self):
        env = {'B3_BUNDLE': f'bundle_{self.id}'}
        t = time.time()
        _, out = sh(['node', 'render.cjs', self.id, 'video'], env=env, tail=4)
        bad = [x for x in out if re.search(r'EMPTY|MISMATCH|Error', x)]
        if bad or not any(x.startswith('DONE') for x in out):
            raise Fail('render', bad or out[-3:])
        from factory.shorts import post
        c = json.loads((self.P / 'case.json').read_text())
        bad = post.subtitle_over_head(c, json.loads((self.P / 'head_boxes.json').read_text()))
        if bad:
            raise Fail('render', [f'subtitle covers a face on {sorted({x[1] for x in bad})} (frames {[x[0] for x in bad][:6]}) -> use a react shot or another '
                                  f'stage for those lines; if it is the stage itself, the stage layout is a library bug: report it, do not edit TSX'])
        sh(['node', 'render.cjs', self.id, 'cover'], env=env)
        return f'{time.time() - t:.0f}s'

    def s_assemble(self):
        sh([V, 'mix.py', self.id])
        sh([V, 'cues.py', self.id])
        sh(['python3', 'cues_pops.py', self.id])
        c = json.loads((self.P / 'case.json').read_text())

        def ts(x):
            return f'{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}'
        (self.P / 'subs.srt').write_text('\n'.join(f"{i}\n{ts(s['start_s'])} --> {ts(s['end_s'])}\n{s['text']}\n" for i, s in enumerate(c['subtitles'], 1)))
        sh(['rm', '-rf', str(self.P / 'sheets')])
        sh([V, 'sheets.py', self.P / 'video.mp4', self.P / 'sheets'])
        _, out = sh([V, 'measure_b3.py', self.P / 'video.mp4'])
        (self.P / 'measure.json').write_text(out[-1])
        return json.loads(out[-1])

    def s_gate(self):
        sh(['rm', '-rf', str(self.P / 'gate')])
        cmd = [V, 'factory/qa/gate.py', self.P / 'video.mp4', '--srt', self.P / 'subs.srt', '--format', 'shorts', '--lang', self.L,
               '--thumbnail', self.P / 'cover.jpg', '--out', self.P / 'gate']
        if self.L == 'ko':
            cmd += ['--voice', self.P / 'narration.wav']
        rc, out = sh(cmd, cwd=ROOT, check=False)
        (self.P / 'gate.log').write_text('\n'.join(out))
        if not (self.P / 'gate/gate.json').exists():
            raise Fail('gate', ['gate.py crashed: ' + ' | '.join(out[-4:])])
        g = json.loads((self.P / 'gate/gate.json').read_text())
        return {'pass': sum(1 for i in g['items'] if i['status'].startswith('PASS')), 'items': len(g['items'])}

    def s_post(self):
        from factory.shorts import post
        r = post.run(self.P)
        if not r['ok']:
            raise Fail('post', [f"{x['check']}: {x['detail']}" for x in r['checks'] if not x['ok']])
        return {'metrics': r['metrics'], 'gate_pass': r['gate_pass']}

    # ---- 10
    def s_package(self):
        s, c = self.spec, self.spec['case']
        foot = {
            'ko': ['다음 판결도 채널에서 이어집니다.', '',
                   '판결·보도를 바탕으로 만든 독창 캐릭터의 2D 애니메이션 재구성입니다. 실제 현장 영상이 아니며 관련자의 신상·외모는 쓰지 않았습니다.',
                   '내레이션: Qwen3-TTS 12Hz-1.7B CustomVoice(화자 Sohee) 로컬 AI 합성.'],
            'en': ['More verdicts coming on this channel.', '',
                   'This is a 2D animated reconstruction with original characters, based on court records and news reports. It is not real footage, and the characters do not depict anyone\'s real appearance.',
                   'Narration: synthesized locally with Kokoro-82M, an AI text-to-speech model.'],
            'ja': ['次の判決もチャンネルで。', '', '判決・報道をもとにしたオリジナルキャラクターの2Dアニメ再構成です。実際の映像ではありません。', 'ナレーション: VOICEVOX:冥鳴ひまり（ローカル音声合成）。'],
        }[self.L]
        leg = json.loads((BF / 'specs' / f'{self.id}.json').read_text())
        calc = [h for p in leg['pops'] for h in p.get('human', [])]
        conv = {'ko': '화면의 환산은 이해를 돕기 위한 계산입니다: ', 'en': 'On-screen conversions are arithmetic: ', 'ja': '画面の換算は計算です: '}[self.L]
        desc = [s['description'], core.finality_text(c['finality'], self.L)] + ([conv + ' / '.join(calc)] if calc else []) + [''] + foot + [' '.join(s['hashtags'])]
        meta = ['[제목]', s['title'], '', '[설명]', '\n'.join(desc), '', '[고정 댓글]', s.get('pinned') or leg['opinion'], '', '[출처]'] + [f"{x['outlet']} | {x['url']}" for x in s['sources']]
        leak = core.meta_leaks('\n'.join(meta))
        if leak:
            raise Fail('package', leak)
        (self.P / 'meta.txt').write_text('\n'.join(meta) + '\n')
        fs = [f'# {s["title"]}', '', f'court {c["court"]} · {c["instance"]} · {c["finality"]} · {"verdict date not in sources" if c["verdict_date"] == "unknown" else "verdict " + c["verdict_date"]}', '']
        for f in s['facts']:
            fs.append(f'- {f["id"]}: {f["claim"]}')
            fs += [f'  - {q["source"]}: "{q["text"]}"' for q in f['quotes']]
        fs += ['', 'Sources:'] + [f"- {x['id']} {x['outlet']} {x['url']}" for x in s['sources']]
        (self.P / 'facts_source.md').write_text('\n'.join(fs) + '\n')
        sha = hashlib.sha256((self.P / 'video.mp4').read_bytes()).hexdigest()
        chk = json.loads((self.P / 'shorts_checks.json').read_text())
        m = chk['metrics']
        eval_build = self.id.startswith('zz')
        ready = [('EVAL BUILD — never upload. ' if eval_build else '') + f'{self.id.upper()}_B · {s["title"]} · make_short.py (spec {self.path.name}) · CTO/CEO 판정 대기, 업로드 없음',
                 f'file: upload/pkg/{self.id}_B/video.mp4  SHA256 {sha}',
                 f'{m["frames"]} frames ({m["frames"] / 30:.2f}s) · motion {m["motion_pct"]}% · bg {m["bg_changes_per_min"]}/min · still max {m["static_hold_s"]}s · loop {m["loop_seam"]}/255',
                 f'shorts checks: all PASS · gate.py {chk["gate_pass"]}/{chk["gate_items"]} PASS; review items: ' + ', '.join(x['check'] for x in chk['gate_review']),
                 'next: factory/runbooks/REVIEW.md (fill review.json), then UPLOAD.md']
        (self.P / 'READY.txt').write_text('\n'.join(ready) + '\n')
        return {'sha256': sha[:12], 'eval_build': eval_build}

    def run(self, start='schema', stop='package'):
        steps = STEPS[STEPS.index(start):STEPS.index(stop) + 1]
        if not self.dry and self.P.exists() and (self.P / 'video.mp4').exists() and not (self.P / 'build.json').exists():
            print(f'REFUSED: upload/pkg/{self.id}_B was made by the legacy path; never overwrite it. Use a new id (zz{self.id} for evaluation).', file=sys.stderr)
            return 2
        if start != 'schema':  # facts values are needed by later steps
            self.values = core.fact_values(self.spec)
        if not self.dry and self.P.exists():
            (self.P / 'READY.txt').unlink(missing_ok=True)
        for name in steps:
            t = time.time()
            try:
                fn = getattr(self, 's_' + name)
                if self.spec.get('variant') == 'BC' and name not in ('schema', 'facts', 'policy', 'compile'):
                    from factory.shorts import bc
                    fn = lambda: getattr(bc, 'step_' + name)(self)  # noqa: E731
                detail = fn()
                self.log['steps'].append(dict(step=name, status='PASS', seconds=round(time.time() - t, 1), detail=detail))
                print(f'PASS {name:9s} {json.dumps(detail, ensure_ascii=False, default=str)[:160]}', flush=True)
            except Fail as e:
                self.log['steps'].append(dict(step=name, status='FAIL', seconds=round(time.time() - t, 1), errors=e.errors))
                self.log['result'] = f'FAIL at {name}'
                self.save()
                print(f'FAIL {name}: fix these, then rerun with --from {name if name not in ("voice",) else "compile"}', file=sys.stderr)
                for x in e.errors:
                    print('  - ' + x, file=sys.stderr)
                return 2
            self.save()
        self.log['result'] = 'PASS' if stop == 'package' else f'PASS through {stop}'
        self.save()
        print(self.log['result'])
        return 0


def selftest():
    """library <-> TSX <-> schema agreement and unit checks of the deterministic helpers"""
    E = []
    src = (BF / 'B3Kit.tsx').read_text()
    stages = set(re.findall(r"shot\.s==='(\w+)'\)return <", src))
    scenes = set(re.search(r'const SCENES[^{]*{([^}]*)}', src).group(1).replace(' ', '').split(','))
    scenes = {x.split(':')[0] for x in scenes}
    sch = core.SCHEMA['$defs']
    if set(LIB['stages']) != stages:
        E.append(f'library stages != B3Kit stages: {sorted(set(LIB["stages"]) ^ stages)}')
    if set(sch['stage']['enum']) != set(LIB['stages']):
        E.append('schema stage enum != library stages')
    for s in LIB['scenes']:
        if s != 'stage' and s not in scenes:
            E.append(f'library scene {s} missing from B3Kit SCENES')
    looks = set(re.search(r'export type Look = ([^;]+);', (BF / 'FightRig.tsx').read_text()).group(1).replace("'", '').replace(' ', '').split('|'))
    if set(sch['look']['enum']) != looks:
        E.append(f'schema looks != FightRig Look: {sorted(set(sch["look"]["enum"]) ^ looks)}')
    pal = core.look_palette()
    for k, st in LIB['stages'].items():
        for a in st['chars']:
            if a not in looks:
                E.append(f'stage {k}: unknown look {a}')
        for t in st['tags']:
            if t not in LIB['tag_words'] and t not in ('deal', 'elderly', 'parking', 'motel', 'night', 'crash', 'fire', 'factory', 'workplace', 'home', 'kitchen', 'animal', 'gun',
                                                         'escape', 'theft', 'computer', 'police', 'labor', 'abuse', 'debt', 'street', 'argument', 'stream', 'speed', 'traffic', 'stalking', 'office', 'wages', 'protest'):
                E.append(f'stage {k}: tag {t} unknown')
    cases = [('고객 도장으로, 14억.', '고객 도장으로, 십사억.'), ('서류 위조만, 12번이었습니다.', '서류 위조만, 열두 번이었습니다.'),
             ('아직 못 갚은 돈만, 4억 8,000만 원.', '아직 못 갚은 돈만, 사억 팔천만 원.'), ('정답 B, 징역 3년.', '정답 비, 징역 삼 년.')]
    for a, b in cases:
        if core.ko_say(a) != b:
            E.append(f'ko_say({a}) = {core.ko_say(a)} != {b}')
    if core.en_say('14 felony charges. She pleaded guilty to 4.') != 'Fourteen felony charges. She pleaded guilty to four.':
        E.append('en_say regression')
    v = {'F1.a': core.parse_value('date', '2020년 12월', 'ko'), 'F1.b': core.parse_value('date', '2024년 3월', 'ko'), 'F2.s': core.parse_value('duration', '징역 3년', 'ko')}
    if core.render_pop({'big': '{x}', 'small': '{m} ≈ {d}', 'vars': {'x': 'span(F1.a, F1.b)', 'm': 'months(F2.s)', 'd': 'days(F2.s)'}}, v, 'ko')[:2] != ('3년 4개월', '36개월 ≈ 1,096일'):
        E.append('pop arithmetic regression')
    bad = core.validate({'spec_version': 1}, core.SCHEMA)
    if not any('missing required field "id"' in x for x in bad):
        E.append('validator does not report missing fields')
    print('selftest', 'OK' if not E else 'FAIL', f'({len(stages)} stages, {len(looks)} looks, {len(pal)} palettes)')
    for x in E:
        print('  -', x)
    return 0 if not E else 1


def stages(tags, channel):
    want = [t for t in (tags or '').split(',') if t]
    prev = None
    if channel:
        reg = json.loads((ROOT / 'factory/channels/registry.json').read_text())
        pre = next(c['package_prefix'] for c in reg['channels'] if c['key'] == channel)
        ps = sorted(PKG.glob(f'{pre}[0-9][0-9][0-9]_B'))
        prev = json.loads((ps[-1] / 'case.json').read_text()).get('stage') if ps and (ps[-1] / 'case.json').exists() else None
    rows = sorted(LIB['stages'].items(), key=lambda kv: -len(set(want) & set(kv[1]['tags'])))
    for k, s in rows:
        hit = len(set(want) & set(s['tags']))
        if want and not hit:
            continue
        print(f"{k:10s} match {hit}  chars {','.join(s['chars']) or '-':22s} tags {','.join(s['tags']):40s} {'(previous episode: not allowed)' if k == prev else ''}  {s['about']}")
    return 0


def fetch(spec_path, refresh=False):
    """Download every source of a spec that may still be a skeleton (only sources[].id/url needed), so the article text
    can be read and quoted before the spec is complete (zzh054 11-14: validate stops at schema before any fetch)."""
    spec = json.loads(Path(spec_path).read_text())
    src = [x for x in spec.get('sources') or [] if isinstance(x, dict) and x.get('id') and x.get('url')]
    if not spec.get('id') or not src:
        print('fetch needs "id" and "sources": [{"id": "S1", "url": "https://..."}] in the spec')
        return 1
    got = policy.fetch_sources({'id': spec['id'], 'sources': src}, refresh=refresh)
    d = policy.snapshot_dir(spec)
    for k, (st, text) in got.items():
        print(f'{k}: {st}, {len(text or "")} chars -> {os.path.relpath(d / f"{k}.txt", ROOT)}')
    bad = [k for k, (st, _) in got.items() if st.startswith('error')]
    if bad:
        print(f'not fetched: {bad} -> find another article for those ids (same facts, another outlet) and run fetch again')
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['fetch', 'validate', 'build', 'stages', 'selftest', 'post'])
    ap.add_argument('--refresh', action='store_true', help='fetch: download again even when a snapshot exists')
    ap.add_argument('target', nargs='?')
    ap.add_argument('--from', dest='start', default='schema', choices=STEPS)
    ap.add_argument('--force-tts', action='store_true')
    ap.add_argument('--tags')
    ap.add_argument('--channel')
    a = ap.parse_args(argv)
    if a.cmd == 'selftest':
        return selftest()
    if a.cmd == 'stages':
        return stages(a.tags, a.channel)
    if a.cmd == 'post':
        from factory.shorts import post
        r = post.run(a.target)
        print(Path(a.target, 'shorts_checks.md').read_text())
        return 0 if r['ok'] else 1
    if a.cmd == 'fetch':
        return fetch(a.target, a.refresh)
    b = Build(a.target, force_tts=a.force_tts)
    if a.cmd == 'validate':
        b.dry = True
        return b.run('schema', 'compile')
    return b.run(a.start, 'package')


if __name__ == '__main__':
    sys.exit(main())
