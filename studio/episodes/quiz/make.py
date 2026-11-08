#!/usr/bin/env python3
"""Build '형량 맞히기' Shorts end to end (except the Remotion render).

usage: make.py [q001 ...] [--voice=M1] [--speed=1.3] [--skip-tts] [--music=track.mp3 --music-offset=SEC]   (M1 1.3 chosen 2026-10-26: tts_lab pitch spread 11+ vs M2 7.8, 0% CER)
Per episode dir episodes/quiz/<id>/: script_text.json → TTS (Supertonic via ../../.venv) → ASR check
(+ best-of-6 retakes) → layout (script.json, timing.json, subtitles) → compositor/public/<id>/render.json
→ procedural sound (mix_master.wav, -14 LUFS).
"""
import json, pathlib, re, shutil, subprocess, sys
import numpy as np

HERE = pathlib.Path(__file__).parent
WORK = HERE.parents[1]
PY = str(WORK / '.venv' / 'bin' / 'python')
PUB = WORK / 'production' / 'compositor' / 'public'
S001 = WORK / 'episodes' / 'S001'
sys.path.insert(0, str(HERE))
from episodes import EPISODES, CHOICES

EXTRA_LEX = [
    ('131미터', '백삼십일 미터'), ('200미터', '이백 미터'), ('4미터', '사 미터'), ('10미터', '십 미터'),
    ('1년 6개월', '일 년 육 개월'), ('징역 4년', '징역 사 년'), ('6개월', '육 개월'),
    ('8주', '팔 주'), ('6주', '육 주'), ('20대', '이십 대'), ('30대', '삼십 대'),
    ('새벽 4시', '새벽 네 시'), ('40대', '사십 대'), ('50대', '오십 대'), ('5만 원', '오만 원'), ('2심', '이심'),
    ('징역 10개월', '징역 십 개월'),
    ('800여', '팔백여'), ('500여', '오백여'), ('760억', '칠백육십억'), ('13억', '십삼억'), ('15년', '십오 년'), ('징역 6년', '징역 육 년'), ('징역 4년', '징역 사 년'),
    ('500명', '오백 명'),
    ('92세', '구십이 세'), ('15분간', '십오 분간'), ('2천만 원', '이천만 원'),
    ('1,270만 원', '천이백칠십만 원'), ('15년일까요', '십오 년일까요'), ('20년일까요', '이십 년일까요'), ('25년일까요', '이십오 년일까요'),
    ('징역 25년', '징역 이십오 년'), ('징역 30년', '징역 삼십 년'), ('구형 20년', '구형 이십 년'), ('7명 중 5명', '일곱 명 중 다섯 명'),
    ('5마리', '다섯 마리'), ('6마리', '여섯 마리'), ('11마리', '열한 마리'), ('20대', '이십 대'),
]


def tools(d, split, lex=()):
    """Copy the S001 TTS/layout tools, with extra number readings (this episode's `lex` first) and its caption splits."""
    for f in ('tts.py', 'tts_best.py', 'asr_check.py', 'layout.py'):
        shutil.copy(S001 / f, d / f)
    t = (d / 'tts.py').read_text()
    t = t.replace("LEX = [  # order matters: longer first\n", "LEX = [  # order matters: longer first\n" + ''.join(f"    ({a!r}, {b!r}),\n" for a, b in [*lex, *EXTRA_LEX]), 1)
    (d / 'tts.py').write_text(t)
    l = (d / 'layout.py').read_text()
    a = l.index('CAPTION_SPLIT = {'); b = l.index('}\n', a) + 2
    l = l[:a] + f'CAPTION_SPLIT = {split!r}\n' + l[b:]
    # Review 2026-10-26: auto splits left "약" / "징역" / "다른" at a line end ("매단 채 약 / 131미터",
    # "징역 / 4년"). Glue those words to the next one before chunking.
    l = l.replace('\ndef weight(s):', '''
_chunks = chunks
NOBREAK_AFTER = ('약', '징역', '집행유예', '다른', '이미')


def chunks(text, maxline=11):
    glued = re.sub(r'(?<!\\S)(' + '|'.join(NOBREAK_AFTER) + r') ', lambda m: m.group(1) + '\\u00a0', text)
    return [c.replace('\\u00a0', ' ') for c in _chunks(glued, maxline)]


def weight(s):''', 1)
    (d / 'layout.py').write_text(l)


def run(cmd, d):
    r = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
    out = '\n'.join(x for x in (r.stdout + r.stderr).splitlines() if 'warn' not in x.lower() and 'fetch' not in x.lower())
    if r.returncode:
        raise SystemExit(f'{cmd} failed in {d}:\n{out[-2000:]}')
    return out


def script_text(eid, ep, d):
    cues = [dict(cue_id=i, act=sc, block_name=sc, narration=na, claim_ids=cl, pad_s=pad, note='', p=p) for i, sc, na, cl, pad, p in ep['cues']]
    json.dump(dict(episode_id=eid, version='quiz-1', hud_case=ep['source'], cues=cues), open(d / 'script_text.json', 'w'), ensure_ascii=False, indent=1)


# Timing anchors (#11+): in a cue's staging, at/until/leverAt/handAt/... and punch beats may be 'sN±k' / 'eN±k' — the
# start or end of the cue's N-th sentence ± frames. They become frames after s1 here, once the voice is measured.
ANCHOR_KEYS = {'at', 'until', 'leverAt', 'handAt', 'moneyAt', 'bigAt', 'logoAt', 'punch'}


def anchor(v, a):
    if not isinstance(v, str):
        return v
    m = re.fullmatch(r'([se])(\d+)([+-]\d+)?', v)
    assert m and f'{m[1]}{m[2]}' in a, f'bad timing anchor {v!r} (cue has {sorted(a)})'
    return a[f'{m[1]}{m[2]}'] - a['s1'] + int(m[3] or 0)


def resolve(x, a, key=None):
    if isinstance(x, dict):
        return {k: resolve(v, a, k) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [resolve(v, a, key if key == 'punch' else None) for v in x]
    return anchor(x, a) if key in ANCHOR_KEYS else x


def build(eid, ep, d):
    script = json.load(open(d / 'script.json')); timing = json.load(open(d / 'timing.json'))
    sent = {i['id']: i for i in timing['items']}
    pmap = {i: p for i, _, _, _, _, p in ep['cues']}
    cues = []
    for c in script['cues']:
        a = {}
        for k in range(len(c['narration'])):
            it = sent[f"{c['cue_id']}_{k + 1}"]
            a[f's{k + 1}'] = it['start'] - c['in_frame']; a[f'e{k + 1}'] = it['end'] - c['in_frame']
        cues.append(dict(id=c['cue_id'], scene=c['act'], **{'from': c['in_frame'], 'dur': c['duration_frames']}, a=a, p=resolve(pmap[c['cue_id']], a)))
    out = PUB / eid; out.mkdir(parents=True, exist_ok=True)
    doc = dict(fps=30, durationInFrames=script['duration_frames'],
               ep=dict(no=ep['no'], head=ep['head'], ask='몇 년 받았을까?', answerHead=ep['answerHead'], choices=ep.get('choices', CHOICES), answer=ep['answer'], source=ep['source'],
                       **({'hook': {k: ep['hook'][k] for k in ('style', 'lines', 'ask', 'narration') if k in ep['hook']}} if 'hook' in ep else {}),
                       **({'quizStyle': ep['quizStyle']} if 'quizStyle' in ep else {})),
               cues=cues, subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text']) for s in timing['subtitles']],
               audio=f'{eid}/mix_master.wav')
    json.dump(doc, open(out / 'render.json', 'w'), ensure_ascii=False, indent=1)
    return doc


def music_bed(path, offset, n, sr):
    """A licensed track (YouTube Audio Library, no attribution) cut to n samples from offset seconds, looped if short,
    with a 0.25 s fade-in and a 1.2 s fade-out so the Shorts loop seam is soft."""
    import soundfile as sf
    d_tmp = None
    y, r = sf.read(path, always_2d=True); y = y.mean(1)
    if r != sr:
        import subprocess, tempfile
        d_tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(sr), d_tmp], check=True)
        y, _ = sf.read(d_tmp)
    y = y[int(offset * sr):]
    while len(y) < n:
        y = np.concatenate([y, y])
    y = y[:n].copy()
    fi, fo = int(0.25 * sr), int(1.2 * sr)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    return y / (np.abs(y).max() + 1e-9) * 0.5


def sound(eid, ep, d, doc, music=None):
    sys.path.insert(0, str(WORK / 'production' / 'audio'))
    import soundfile as sf
    from synth import SR, f2s, stereo
    sys.path.insert(0, str(S001))
    import synth_short as SS
    total = doc['durationInFrames']; N = f2s(total)
    mus = np.zeros(N); fx = np.zeros(N)
    place = SS.place
    if ep.get('serious'):
        music = ('none', 0)  # death cases never get a music bed, even if one is passed (same as --music=none)
    if music and music[0] == 'none':
        pass  # cases with a death: no music bed (ops doc red lines — serious tone)
    elif music:
        mus[:] = music_bed(music[0], music[1], N, SR)
    else:
        place(mus, SS.bed(0, total, SS.PROG, energy=0.6), 0)
    for c in doc['cues']:
        c0, a = c['from'], c['a']
        # Premium judgment beats use the voice and silence; no countdown ticks or gavel hits.
        if ep.get('quizStyle') == 'premium' and c['scene'] in ('quiz', 'weigh', 'reason', 'reveal'):
            continue
        if c['scene'] in ('cling', 'push2'):
            place(fx, SS.engine(1.4, 0.28), f2s(c0 + a['s1']))
        if c['scene'] == 'push2':
            place(fx, SS.crash(0.28), f2s(c0 + a['e1'] - 6))
        if c['scene'] in ('hurt', 'remorse', 'confiscate'):
            place(fx, SS.thunk(0.22), f2s(c0 + a['s1'] + 8 if c['scene'] != 'hurt' else c0 + a['s1'] + 10))
        if c['scene'] == 'record':
            n = len(c['p']['items'])
            for i in range(n):
                place(fx, SS.thunk(0.2), f2s(c0 + a['s1'] + 6 + i * max(8, round(((a['e1'] - a['s1']) * 0.6) / n))))
        if c['scene'] == 'incident':
            q = c['p']
            if q.get('burst'):
                place(fx, SS.crash(0.26), f2s(c0 + a['s1'] + q['burst']['at']))
            if q.get('stamp'):
                place(fx, SS.thunk(0.22), f2s(c0 + a['s1'] + q['stamp'].get('at', 10)))
            for s in q.get('sfx', []):
                place(fx, SS.thunk(0.14), f2s(c0 + a['s1'] + s.get('at', 0)))
            for st in q.get('stamps', []):
                place(fx, SS.thunk(0.22), f2s(c0 + a['s1'] + st.get('at', 10)))
        if c['scene'] == 'weigh':
            k0 = c['p'].get('cardFrom', 2)
            for i in range(len(c['p']['cards'])):
                if f's{k0 + i}' in a:
                    place(fx, SS.thunk(0.16), f2s(c0 + a[f's{k0 + i}']))
        if c['scene'] == 'quiz':
            cd0 = c0 + a.get('e2', a['e1'])
            for i in range(3):
                place(fx, SS.tick(0.08), f2s(cd0 + i * 30))
            # fade the music under the countdown so the pause reads
            s0, s1 = f2s(cd0), f2s(cd0 + 92)
            mus[s0:s1] *= np.linspace(1, 0.15, s1 - s0)
        if c['scene'] == 'reveal':
            place(fx, SS.knock(0.45), f2s(c0 + a['s1'] + 2))
            place(fx, SS.thunk(0.25), f2s(c0 + a['s1'] + 8))
            if ep['answer'] == 2 and not ep.get('serious'):
                place(fx, SS.crash(0.18), f2s(c0 + a['s1'] + 10))
            for st in c['p'].get('steps', []):
                if f"s{st['s']}" in a:
                    place(fx, SS.thunk(0.22), f2s(c0 + a[f"s{st['s']}"]))
    timing = json.load(open(d / 'timing.json'))
    na = np.zeros(N); g = np.zeros(N)
    for it in timing['items']:
        x, sr = sf.read(d / it['file']); x = x.mean(1) if x.ndim > 1 else x
        place(na, x, f2s(it['start'])); g[f2s(it['start']):f2s(it['end'])] = 1
    k = int(0.12 * SR); sm = np.clip(np.convolve(g, np.ones(k) / k, mode='same') * 1.5, 0, 1)
    # licensed track: duck 14 dB under speech and sit 3 dB lower overall → ~16 dB below the voice (phone speakers)
    duck, gain = (14, 0.6) if music else (9, 0.85)
    mix = stereo(na, 0, 0) + stereo(mus * 10 ** (-duck * sm / 20), 0.35) * gain + stereo(fx, 0.3) * 0.9
    raw = d / 'audio' / 'mix_raw.wav'; master = d / 'audio' / 'mix_master.wav'
    sf.write(raw, mix.astype(np.float32), SR, subtype='FLOAT')
    p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex('{'):p1.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', str(master)], check=True)
    shutil.copy(master, PUB / eid / 'mix_master.wav')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = dict(a[2:].split('=', 1) if '=' in a else (a[2:], '1') for a in sys.argv[1:] if a.startswith('--'))
    voice, speed = opts.get('voice', 'M1'), opts.get('speed', '1.3')
    music = (opts['music'], float(opts.get('music-offset', '0'))) if 'music' in opts else None
    for eid in (args or list(EPISODES)):
        ep = EPISODES[eid]; d = HERE / eid; (d / 'audio' / 'na').mkdir(parents=True, exist_ok=True)
        tools(d, ep.get('split', {}), ep.get('lex', [])); script_text(eid, ep, d)
        if 'skip-tts' not in opts:
            run([PY, 'tts.py', voice, speed], d)
            out = run([PY, 'asr_check.py', '0.08'], d)
            bad = [l.split()[1] for l in out.splitlines() if l.startswith('BAD')]
            if bad:
                run([PY, 'tts_best.py', ','.join(bad), '6'], d)
                out = run([PY, 'asr_check.py', '0.08', ','.join(bad)], d)
            print(eid, [l for l in out.splitlines() if l.startswith(('sentences', 'BAD'))])
        print(run(['python3', 'layout.py'], d).splitlines()[-1])
        doc = build(eid, ep, d)
        sound(eid, ep, d, doc, music)
        print(eid, 'frames', doc['durationInFrames'], f"({doc['durationInFrames'] / 30:.1f}s)")


if __name__ == '__main__':
    main()
