"""Measure every Kokoro take, whisper-check it (local mlx whisper-large-v3-turbo, offline), lay the lines on the
timeline, cut scenes 1 frame before each voice onset, chunk subtitles (<=2 lines x <=28 chars, word breaks) on
whisper word starts, write upload/pkg/<id>_B/{case.json,narration.wav,subs.srt,whisper.json}.
usage: build.py <id>"""
import os, sys, json, re, subprocess, difflib
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from pathlib import Path
import numpy as np, soundfile as sf
D = Path(__file__).resolve().parent; W = D.parents[1]; q = sys.argv[1]
sp = json.loads((D / 'specs' / f'{q}.json').read_text()); P = W / 'upload/pkg' / f'{q}_B'; P.mkdir(parents=True, exist_ok=True)
M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
import mlx_whisper
ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
def w3(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' ' + w3(n % 100))
def words(n): return w3(n) if n < 1000 else w3(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + w3(n % 1000))
def norm(s):
    s = re.sub(r'\bvs\b\.?', 'versus', s.lower().replace('-', ' ').replace('’', "'"))
    s = re.sub(r'\d[\d,]*', lambda m: words(int(m.group().replace(',', ''))), s)
    return re.sub(r"[^a-z' ]", ' ', s).split()
def voiced(x, sr):
    e = np.sqrt(np.convolve(x ** 2, np.ones(int(.01 * sr)) / int(.01 * sr), 'same')); th = e.max() * 10 ** (-38 / 20)
    i = np.where(e > th)[0]; return i[0] / sr, i[-1] / sr
SR = 24000; out = []; cur = 0.0; report = []
for l in sp['lines']:
    x, sr = sf.read(D / 'cand' / q / f"{l['id']}.wav", dtype='float32'); assert sr == SR
    a, b = voiced(x, sr); a = max(0, a - .02); b = min(len(x) / sr, b + .05); clip = x[int(a * sr):int(b * sr)]
    c16 = np.interp(np.arange(0, len(clip), sr / 16000), np.arange(len(clip)), clip).astype(np.float32)
    r = mlx_whisper.transcribe(c16, path_or_hf_repo=str(M), language='en', word_timestamps=True, temperature=0, condition_on_previous_text=False, verbose=None)
    heard = ' '.join(s['text'].strip() for s in r['segments']); ws = [(w['word'].strip(), float(w['start'])) for s in r['segments'] for w in s.get('words', [])]
    ratio = difflib.SequenceMatcher(None, norm(l['tts']), norm(heard)).ratio()
    report.append(dict(id=l['id'], expected=l['tts'], heard=heard, match=round(ratio, 3)))
    on = cur; off = on + len(clip) / sr
    e = np.sqrt(np.convolve(clip ** 2, np.ones(240) / 240, 'same')); v = e > e.max() * 10 ** (-35 / 20); ons = []; quiet = 0
    for j in range(0, len(v), 48):
        if not v[j]: quiet += 48
        else:
            if quiet >= int(.07 * sr): ons.append(j / sr)
            quiet = 0
    out.append(dict(l=l, clip=clip, on=on, off=off, ws=ws, ons=ons))
    cur = off + sp.get('gap', .14) + l.get('hold', 0)
n = int(round((out[-1]['off'] + .2) * 30))
lines = []
for i, o in enumerate(out):
    fr = 0 if i == 0 else int(round(o['on'] * 30)) - 1
    lines.append(dict(id=o['l']['id'], mode=o['l']['mode'], k=o['l'].get('k'), shots=o['l'].get('shots'), shown=o['l']['shown'], from_=fr, onset=round(o['on'], 3), offset=round(o['off'], 3)))
for i, L in enumerate(lines): L['from'] = L.pop('from_'); L['dur'] = (lines[i + 1]['from_'] if i + 1 < len(lines) and 'from_' in lines[i + 1] else (lines[i + 1]['from'] if i + 1 < len(lines) else n)) - L['from'] if i + 1 < len(lines) else n - L['from']
# subtitles: pack words into cues of <=2 lines x <=28 chars
def wrap(ws, lim=26):
    rows = [''];
    for w in ws:
        if rows[-1] and len(rows[-1]) + 1 + len(w) > lim: rows.append(w)
        else: rows[-1] = (rows[-1] + ' ' + w).strip()
    return rows
def cues_for(text):
    ws = text.split()
    if len(wrap(ws)) <= 2: return [balanced(ws) if len(text) > 26 else text]
    best = None
    for k in range(1, len(ws)):
        A, B = ws[:k], ws[k:]
        if len(wrap(A)) > 2 or len(wrap(B)) > 2: continue
        sc = abs(len(' '.join(A)) - len(' '.join(B))) - (14 if re.search(r'[,.?!:]$', ws[k - 1]) else 0)
        if best is None or sc < best[0]: best = (sc, A, B)
    return [balanced(x) if len(' '.join(x)) > 26 else ' '.join(x) for x in best[1:]]
def balanced(ws):
    best = None
    for k in range(1, len(ws)):
        a, b = ' '.join(ws[:k]), ' '.join(ws[k:])
        if len(a) <= 26 and len(b) <= 26:
            sc = abs(len(a) - len(b)) - (6 if re.search(r'[,.?!:]$', ws[k - 1]) else 0)
            if best is None or sc < best[0]: best = (sc, a + '\n' + b)
    return best[1] if best else ' '.join(ws)
subs = []
def spoken_len(ws): return max(1, len(''.join(norm(' '.join(ws)))))
import captions  # 1-3 word captions, phrase-aware breaks, one font size (episodes/beastclash/captions.py)
need_s = captions.need_s
for i, o in enumerate(out):
    sh = o['l']['shown']
    if not sh: continue
    nxt = out[i + 1]['on'] if i + 1 < len(out) else n / 30
    if sp.get('caps') == 'words':
        tx = captions.split(sh, sp.get('keep', [])); parts = [x.split() for x in tx]; end = min(o['off'] + .2, nxt - 1 / 30 - .02); t0 = o['on']
        need = [need_s(x) for x in tx]; wts = [spoken_len(p) for p in parts]; span = end - t0
        # every cue gets its per-word minimum first; what is left of the line is shared by spoken length
        durs = [nd + (span - sum(need)) * w / sum(wts) for nd, w in zip(need, wts)] if span >= sum(need) else [span * len(x.split()) / len(sh.split()) for x in tx]
        a0 = t0
        for x, dd in zip(tx, durs):
            subs.append(dict(s=round(a0, 3), e=round(a0 + dd, 3), text=x, line=o['l']['id'])); a0 += dd
        continue
    parts = cues_for(sh); ws = o['ws']; starts = [o['on']]; nw = 0
    for p in parts[:-1]:
        nw += len(p.split()); st = o['on'] + ws[min(nw, len(ws) - 1)][1] if ws else None
        if st is not None and o['ons']:
            near = min(o['ons'], key=lambda z: abs(o['on'] + z - st))
            if abs(o['on'] + near - st) < .45: st = o['on'] + near
        starts.append(st if st is not None and starts[-1] + .5 < st < o['off'] - .4 else starts[-1] + (o['off'] - o['on']) * len(p) / len(sh))
    for k, p in enumerate(parts):
        e = starts[k + 1] if k + 1 < len(parts) else min(o['off'] + .25, nxt - 1 / 30 - .02)
        subs.append(dict(s=round(starts[k], 3), e=round(e, 3), text=p, line=o['l']['id']))
case = dict(id=q, a=sp['a'], b=sp['b'], winner=sp['winner'], bg=sp['bg'], title=sp['title'], tag=sp.get('tag'), stats=sp['stats'], verdict=sp['verdict'], lines=lines, subs=subs, n=n, voice=sp['voice'], speed=sp['speed'])
(P / 'case.json').write_text(json.dumps(case, ensure_ascii=False, indent=1))
nar = np.zeros(int(n / 30 * SR) + SR, np.float32)
for o in out: s = int(o['on'] * SR); nar[s:s + len(o['clip'])] += o['clip']
nar = nar[:int(n / 30 * SR)]; sf.write(P / 'narration24.wav', nar, SR)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'narration24.wav'), '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s24le', str(P / 'narration.wav')], check=True); (P / 'narration24.wav').unlink()
def ts(t): return f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)):03d}'.replace(',1000', ',999')
(P / 'subs.srt').write_text(''.join(f"{i + 1}\n{ts(s['s'])} --> {ts(s['e'])}\n{s['text']}\n\n" for i, s in enumerate(subs)))
(P / 'whisper.json').write_text(json.dumps(report, indent=1))
print('n', n, round(n / 30, 2), 's | lines', ' '.join(f"{L['id']}:{L['mode']}@{L['onset']:.2f}-{L['offset']:.2f}" for L in lines))
print('whisper', ' '.join(f"{r['id']}={r['match']}" for r in report), '| low:', [(r['id'], r['heard']) for r in report if r['match'] < .9])
print('subs', len(subs), 'max row', max(len(r) for s in subs for r in s['text'].split('\n')), 'rows', max(s['text'].count('\n') + 1 for s in subs))
