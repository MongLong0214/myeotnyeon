"""Beast Clash (variant BC, locale en) for make_short.py: spec checks, compile to episodes/beastclash/specs/<id>.json,
and the build steps that drive the existing episodes/beastclash scripts (synth.py, build.py, render.cjs, mix.py)."""
import hashlib
import json
import re
import time

from factory.shorts import core
from factory.shorts.core import BC_DIR, LIB, ROOT, Fail

ORDER = re.compile(r'^face (stat ){3}prompt (clash ){2,5}(verdict ){1,2}loop$')
CONV = {'lb': ('kg', .4536), 'lbs': ('kg', .4536), 'pounds': ('kg', .4536), 'pound': ('kg', .4536), 'ft': ('m', .3048), 'feet': ('m', .3048),
        'foot': ('m', .3048), 'in': ('cm', 2.54), 'inches': ('cm', 2.54), 'mph': ('km/h', 1.609), 'kg': ('lb', 2.2046), 'm': ('ft', 3.281), 'km/h': ('mph', .6214),
        'miles per hour': ('km/h', 1.609)}
NO_CONV = {'ton', 'tons'}  # short, long and metric tons differ: show the source's word, never a conversion
CANON = {'lbs': 'LB', 'lb': 'LB', 'pounds': 'LB', 'pound': 'LB', 'inches': 'IN', 'in': 'IN', 'feet': 'FT', 'foot': 'FT', 'ft': 'FT', 'mph': 'MPH', 'kg': 'KG', 'm': 'M', 'km/h': 'KM/H',
         'miles per hour': 'MPH', 'ton': 'TON', 'tons': 'TONS'}
GATE_BLOCKING = ['static_holds', 'jump_cuts', 'hook_text_over_face_ocr', 'subtitle_over_face', 'onscreen_text_clip_size', 'hook_title_overstatement',
                 'loudness_true_peak', 'thumbnail_reuses_frame']
MATCH_MIN = .85


def stat(v):
    big = f'{core.fmt_num(v.v)} {CANON.get(v.unit, v.unit.upper())}'
    if v.unit in NO_CONV or v.unit not in CONV:
        return {'big': big, 'small': ''}
    u, f = CONV[v.unit]
    return {'big': big, 'small': f'≈{approx(v.v * f)} {u}'}


def approx(c):
    """2 significant figures: a converted value never looks more precise than the rounded source (CEO bc004: 22,000 lb -> ≈10,000 kg, not 9,979)"""
    if c <= 0:
        return '0'
    from math import floor, log10
    r = round(c, 1 - int(floor(log10(c))))
    return f'{r:,.1f}' if r < 10 and r != int(r) else f'{int(r):,}'


MAX_CUE = re.compile(r'\b(up to|as much as|largest|biggest|record|maximum|max\.?|can reach|reach(?:es)?|at most|to)\s*$', re.I)
MAX_LABEL = re.compile(r'\b(MAX|UP TO|RECORD|TOP|LARGEST|BIGGEST)\b')


def max_quote(spec, ref, val):
    """the quote snippet when the source states this value as an upper bound ('weigh up to 9,920 pounds'), else None"""
    fid = ref.split('.')[0]
    for f in spec.get('facts', []):
        if f['id'] != fid:
            continue
        for q in f['quotes']:
            i = q['text'].find(val)
            if i > 0 and MAX_CUE.search(q['text'][max(0, i - 24):i]):
                return q['text'][max(0, i - 24):i + len(val)]
    return None


def spec_value_text(spec, ref):
    fid, key = (ref.split('.') + [''])[:2]
    for f in spec.get('facts', []):
        if f['id'] == fid:
            return (f.get('values', {}).get(key) or {}).get('text')
    return None


def compile_spec(spec):
    """-> (errors, warnings, legacy spec)"""
    E, W = [], []
    bc, L = spec['bc'], 'en'
    vals = core.fact_values(spec)
    if spec['locale'] != 'en':
        E.append('locale: Beast Clash is en only')
    if bc['a'] == bc['b']:
        E.append('bc: a and b must be different animals')
    beats = ' '.join(ln['beat'] for ln in spec['lines'])
    if not ORDER.match(beats):
        E.append(f'lines: beat order is "{beats}" -> must be {LIB["bc"]["beats"]}')
    facts = {f['id']: f for f in spec['facts']}
    names = LIB['bc']['animals']
    for i, ln in enumerate(spec['lines']):
        f = facts.get(ln['fact'])
        if not f:
            E.append(f'lines[{i}].fact: {ln["fact"]} is not a fact id')
            continue
        quotes = ' '.join(q['text'] for q in f['quotes']) + ' ' + f['claim']
        allowed = core.nums_in(quotes, L)
        if ln['beat'] == 'stat':  # a stat line may say every number of its card (facts of both animals)
            k = [x for x in spec['lines'][:i] if x['beat'] == 'stat'].__len__()
            st = bc['stats'][k] if k < len(bc['stats']) else {}
            allowed |= {int(vals[st[sd]].v) for sd in ('a', 'b') if st.get(sd) in vals}
        miss = core.nums_in(ln['text'], L) - allowed if ln['beat'] != 'loop' else set()
        if miss:
            E.append(f'lines[{i}] ({ln["beat"]}): numbers {sorted(miss)} are not in {f["id"]} quotes')
        if ln['beat'] == 'clash' and not ln.get('shots'):
            E.append(f'lines[{i}] (clash): needs 1-2 shots (charge, rear, strike, impact, retreat)')
        if ln['beat'] != 'clash' and ln.get('shots'):
            E.append(f'lines[{i}] ({ln["beat"]}): only clash lines have shots')
        if re.search(r'\bcomment\b', ln['text'] + ' ' + ln.get('say', ''), re.I):
            E.append(f'lines[{i}]: asks viewers to comment -> the owner does not want comment calls-to-action; use "Who wins? Take your pick!"')
        if len(ln['text']) > 64:
            E.append(f'lines[{i}]: too long')
    for k, x in enumerate(bc['stats']):
        if not (x.get('a') or x.get('b')):
            E.append(f'bc.stats[{k}]: needs a value for a, b or both')
        for side in ('a', 'b'):
            ref = x.get(side)
            if ref and (ref not in vals or vals[ref].kind != 'measure'):
                E.append(f'bc.stats[{k}].{side}: {ref} must name a measure value (e.g. "3,000 pounds" with kind measure)')
        for side in ('a', 'b'):
            ref = x.get(side)
            fv = spec_value_text(spec, ref) if ref else None
            mq = max_quote(spec, ref, fv) if fv else None
            if mq and not MAX_LABEL.search(x['label'].upper() + ' ' + x.get(side + '_cond', '').upper()):
                E.append(f'bc.stats[{k}]: the source gives {fv} as an upper bound ("...{mq}") -> the label must say so on the card '
                         f'(e.g. "MAX {x["label"]}"), and the stat line should say it too (CEO bc004)')
    stat_lines = [ln for ln in spec['lines'] if ln['beat'] == 'stat']
    for k, (x, ln) in enumerate(zip(bc['stats'], stat_lines)):
        need = {int(vals[x[s]].v) for s in ('a', 'b') if x.get(s) in vals}
        if need and not need & core.nums_in(ln['text'], L):
            E.append(f'stat line {k + 1} "{ln["text"]}" does not say the card number(s) {sorted(need)} of bc.stats[{k}]')
    if E:
        return E, W, None
    def side(x, s):
        st = stat(vals[x[s]])
        if x.get(s + '_cond'):  # the source condition sits on the card next to the number (CEO bc006)
            st['small'] = x[s + '_cond'].upper() + (' · ' + st['small'] if st['small'] else '')
        return st
    stats = [dict(label=x['label'], **({'a': side(x, 'a')} if x.get('a') else {}), **({'b': side(x, 'b')} if x.get('b') else {}), win=x['win'])
             for x in bc['stats']]
    sp = LIB['bc']['speeds']
    clashes = [i for i, ln in enumerate(spec['lines']) if ln['beat'] == 'clash']
    lines, ks, kv = [], 0, 0
    for i, ln in enumerate(spec['lines']):
        d = dict(id=f'L{i + 1:02d}', mode=ln['beat'], tts=ln.get('say') or core.say(ln['text'], 'en'), shown=ln['text'])
        if ln['beat'] == 'stat':
            d['k'], ks = ks, ks + 1
        if ln['beat'] == 'verdict':
            d['k'], kv = kv, kv + 1
        if ln['beat'] == 'clash':
            d['shots'] = [dict(s=x['scene'], who=x['who'], **{k: True for k in ('tank', 'pin') if x.get(k)}) for x in ln['shots']]
            d['hold'] = LIB['bc']['holds']['last_clash' if i == clashes[-1] else 'clash']
        if ln['beat'] in sp:
            d['speed'] = sp[ln['beat']]
        lines.append(d)
    win = bc[bc['winner']]
    leg = dict(id=spec['id'], voice=bc.get('voice', 'af_bella'), speed=sp['default'], a=bc['a'], b=bc['b'], winner=bc['winner'], bg=bc['bg'],
               title=[names[bc['a']], names[bc['b']]], tag=[stats[0].get('a', {}).get('big', ''), stats[0].get('b', {}).get('big', '')],
               gap=LIB['bc']['holds'].get('gap', .14), caps='words',
               keep=sorted({names[bc['a']].lower(), names[bc['b']].lower(), *LIB['bc'].get('aliases', {}).get(bc['a'], []), *LIB['bc'].get('aliases', {}).get(bc['b'], [])}), stats=stats, verdict=dict(**bc['verdict'], head='HYPOTHETICAL WINNER', name=names[win]), lines=lines)
    return E, W, leg


def _sh(b, cmd, **kw):
    from factory.make_short import sh
    return sh(cmd, cwd=BC_DIR, **kw)


def step_tts(b):
    from factory.make_short import K
    t = time.time()
    _sh(b, [K, 'synth.py', b.id], tail=3)
    return f'{len(list((BC_DIR / "cand" / b.id).glob("*.wav")))} takes in {time.time() - t:.0f}s'


PACE_MAX = 3.9  # caption words per second a line may reach: gate --cue-rule per_word needs 0.25 s per word


def _slow_fast_lines(b):
    """Lower the TTS speed of every line whose on-screen words pass faster than PACE_MAX; -> [(id, pace, new speed)]"""
    c = json.loads((b.P / 'case.json').read_text())
    p = BC_DIR / 'specs' / f'{b.id}.json'
    leg = json.loads(p.read_text())
    out = []
    import importlib.util
    cs = importlib.util.spec_from_file_location('bc_captions', BC_DIR / 'captions.py')
    cap = importlib.util.module_from_spec(cs)
    cs.loader.exec_module(cap)
    for ln, u in zip(leg['lines'], c['lines']):
        span = max(.1, u['offset'] - u['onset'])
        pace = len((ln['shown'] or '').split()) / span
        need = sum(cap.need_s(x) for x in cap.split(ln['shown'] or '', leg.get('keep', []))) / .97  # every caption's minimum must fit
        k = max(pace / (PACE_MAX - .1), need / span)
        if pace > PACE_MAX or need > span:
            ln['speed'] = round(ln.get('speed', leg['speed']) / k, 2)
            out.append((ln['id'], round(pace, 2), ln['speed']))
    if out:
        p.write_text(json.dumps(leg, ensure_ascii=False, indent=1))
    return out


def step_voice(b):
    from factory.make_short import K, V
    notes = []
    for rnd in range(5):
        _sh(b, [V, 'build.py', b.id], tail=4)
        rep = json.loads((b.P / 'whisper.json').read_text())
        bad = [r for r in rep if r['match'] < MATCH_MIN]
        if not bad:
            pace = _slow_fast_lines(b)
            if pace and rnd < 4:  # a line spoken faster than captions can follow: slower take, then check it again
                notes.append(pace)
                _sh(b, [K, 'synth.py', b.id], tail=3)
                continue
            return {'rounds': rnd + 1, 'min_match': min(r['match'] for r in rep), 'notes': notes}
        notes.append([(r['id'], r['match'], r['heard']) for r in bad])
        if rnd == 4:
            break
        p = BC_DIR / 'specs' / f'{b.id}.json'
        leg = json.loads(p.read_text())
        for ln in leg['lines']:  # slower read for the misheard lines, then a fresh take
            if ln['id'] in {r['id'] for r in bad}:
                ln['speed'] = round(ln.get('speed', leg['speed']) - .1, 2)
        p.write_text(json.dumps(leg, ensure_ascii=False, indent=1))
        _sh(b, [K, 'synth.py', b.id], tail=3)
    raise Fail('voice', [f'{r["id"]}: whisper heard "{r["heard"]}" for "{r["expected"]}" (match {r["match"]} < {MATCH_MIN}) after 3 rounds -> '
                         f'rewrite that line with plainer words, rerun --from compile --force-tts' for r in bad])


def step_timing(b):
    c = json.loads((b.P / 'case.json').read_text())
    E = []
    if not 18 <= c['n'] / 30 <= 40:
        E.append(f'duration {c["n"] / 30:.1f}s outside 18-40 s -> {"add" if c["n"] / 30 < 18 else "cut"} a clash line')
    for s in c['subs']:
        if s['e'] - s['s'] < .4:
            E.append(f'subtitle "{s["text"]}" shows {s["e"] - s["s"]:.2f}s (< 0.4 s) -> shorten the line or merge')
    if E:
        raise Fail('timing', E)
    return {'duration_s': round(c['n'] / 30, 2), 'cues': len(c['subs'])}


def step_render(b):
    t = time.time()
    _, out = _sh(b, ['node', 'render.cjs', b.id, 'video'], tail=4)
    if not any(x.startswith('DONE') for x in out):
        raise Fail('render', out[-3:])
    _sh(b, ['node', 'render.cjs', b.id, 'cover'])
    return f'{time.time() - t:.0f}s'


def step_assemble(b):
    from factory.make_short import V
    _sh(b, [V, 'mix.py', b.id])
    _sh(b, ['rm', '-rf', str(b.P / 'sheets')])
    _sh(b, [V, str(core.BF / 'sheets.py'), b.P / 'video.mp4', b.P / 'sheets', 60])
    _, out = _sh(b, [V, str(core.BF / 'measure_b3.py'), b.P / 'video.mp4'])
    (b.P / 'measure.json').write_text(out[-1])
    return json.loads(out[-1])


def step_gate(b):
    from factory.make_short import V, sh
    sh(['rm', '-rf', str(b.P / 'gate')], cwd=ROOT)
    rc, out = sh([V, 'factory/qa/gate.py', b.P / 'video.mp4', '--srt', b.P / 'subs.srt', '--out', b.P / 'gate', '--format', 'shorts', '--lang', 'en',
                  '--voice', b.P / 'narration.wav', '--thumbnail', b.P / 'cover.jpg', '--max-cps', 22, '--line-max', 28, '--cue-rule', 'per_word'], cwd=ROOT, check=False)
    (b.P / 'gate.log').write_text('\n'.join(out))
    if not (b.P / 'gate/gate.json').exists():
        raise Fail('gate', ['gate.py crashed: ' + ' | '.join(out[-4:])])
    g = json.loads((b.P / 'gate/gate.json').read_text())
    return {'pass': sum(1 for i in g['items'] if i['status'].startswith('PASS')), 'items': len(g['items'])}


def step_post(b):
    from factory.shorts import post
    F = post.frames(b.P / 'video.mp4')
    m, _ = post.cadence(F)
    L = post.LIMITS
    g = json.loads((b.P / 'gate/gate.json').read_text())
    gi = {i['check']: i for i in g['items']}
    rows = [('motion', m['motion_pct'] >= L['motion_pct_min'], f"{m['motion_pct']}% (min {L['motion_pct_min']})"),
            ('static_hold', m['static_hold_s'] <= L['static_hold_s_max'], f"{m['static_hold_s']} s (max {L['static_hold_s_max']})"),
            ('bg_change_rate', L['bg_changes_per_min_min'] <= m['bg_changes_per_min'] <= L['bg_changes_per_min_max'], f"{m['bg_changes_per_min']}/min"),
            ('longest_same_bg', m['longest_same_bg_s'] <= L['longest_same_bg_s_max'], f"{m['longest_same_bg_s']} s"),
            ('loop_seam', m['loop_seam'] <= L['loop_seam_max'], f"{m['loop_seam']}/255 (max {L['loop_seam_max']})")]
    rows += [(f'gate:{k}', bool(gi.get(k)) and gi[k]['status'].startswith('PASS'), (gi.get(k) or {}).get('summary', 'missing')[:140]) for k in GATE_BLOCKING]
    review = [dict(check=i['check'], id=i['id'], status=i['status'], summary=i['summary'][:160]) for i in g['items'] if i['check'] not in GATE_BLOCKING and not i['status'].startswith('PASS')]
    n = post.sheet_1fps(b.P / 'video.mp4', b.P / 'sheet_1fps.jpg', m['frames'])
    if (b.P / 'head_boxes.json').exists():
        post.faces_1fps(b.P / 'video.mp4', b.P / 'head_boxes.json', b.P / 'faces_1fps.jpg')
    res = dict(pkg=str(b.P), variant='BC', metrics=m, limits=L, checks=[dict(check=a, ok=bool(x), detail=d) for a, x, d in rows],
               gate_pass=sum(1 for i in g['items'] if i['status'].startswith('PASS')), gate_items=len(g['items']), gate_review=review, sheet_1fps=n,
               ok=all(x for _, x, _ in rows), note='BC: no character-box checks (animals are not ArticulatedGuy); subject size is a REVIEW question')
    (b.P / 'shorts_checks.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    md = [f"# shorts checks — {b.P.name} (BC): {'PASS' if res['ok'] else 'FAIL'}", '', '| check | ok | detail |', '|---|---|---|']
    md += [f"| {a} | {'PASS' if x else 'FAIL'} | {d} |" for a, x, d in rows]
    md += ['', f"gate.py: {res['gate_pass']}/{res['gate_items']} PASS. Non-blocking items for REVIEW.md:"] + [f"- {x['check']}: {x['status']} — {x['summary']}" for x in review]
    (b.P / 'shorts_checks.md').write_text('\n'.join(md) + '\n')
    if not res['ok']:
        raise Fail('post', [f'{a}: {d}' for a, x, d in rows if not x])
    return {'metrics': m, 'gate_pass': res['gate_pass']}


def step_package(b):
    s = b.spec
    meta = ['[Title]', s['title'], '', '[Description]', s['description'], '',
            'Stats come from the sources below; cards convert units (1 lb = 0.4536 kg, 1 in = 2.54 cm, 1 mph = 1.609 km/h).', '',
            'Original 2D cartoon animals; this is a fun what-if based on published facts, not real footage.',
            'Narration: synthesized locally with Kokoro-82M, an AI text-to-speech model.', ' '.join(s['hashtags']), '',
            '[Pinned comment]', 'Who wins? Take your pick!', '', '[Sources]'] + [f"{x['outlet']} | {x['url']}" for x in s['sources']]
    (b.P / 'meta.txt').write_text('\n'.join(meta) + '\n')
    fs = [f'# {s["title"]}', '']
    for f in s['facts']:
        fs.append(f'- {f["id"]}: {f["claim"]}')
        fs += [f'  - {q["source"]}: "{q["text"]}"' for q in f['quotes']]
    fs += ['', 'Sources:'] + [f"- {x['id']} {x['outlet']} {x['url']}" for x in s['sources']]
    (b.P / 'facts_source.md').write_text('\n'.join(fs) + '\n')
    sha = hashlib.sha256((b.P / 'video.mp4').read_bytes()).hexdigest()
    chk = json.loads((b.P / 'shorts_checks.json').read_text())
    m = chk['metrics']
    ev = b.id.startswith('zz')
    (b.P / 'READY.txt').write_text('\n'.join([
        ('EVAL BUILD — never upload. ' if ev else '') + f'{b.id.upper()}_B · {s["title"]} · Beast Clash · make_short.py (spec {b.path.name}) · producer self-check, no upload',
        f'file: upload/pkg/{b.id}_B/video.mp4  SHA256 {sha}',
        f'{m["frames"]} frames ({m["frames"] / 30:.2f}s) · motion {m["motion_pct"]}% · bg {m["bg_changes_per_min"]}/min · loop {m["loop_seam"]}/255',
        f'shorts checks: all PASS · gate.py {chk["gate_pass"]}/{chk["gate_items"]} PASS; review items: ' + ', '.join(x['check'] for x in chk['gate_review']),
        'next: factory/runbooks/REVIEW.md, then UPLOAD.md']) + '\n')
    return {'sha256': sha[:12], 'eval_build': ev}
