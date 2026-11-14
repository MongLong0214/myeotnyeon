"""B3 subtitles: split each line's subtitle into its spec 'chunks' (3-10 chars, one line each). Chunk starts are the
whisper word-start times of the chosen take (word_timestamps, local whisper-large-v3-turbo), mapped by spoken-syllable
count; fallback is syllable share inside the measured voice onset..offset. Rewrites case.json 'subtitles'.
usage: b3post.py <qid>"""
import os, sys, json, re
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pace import heard
import intl
D = Path(__file__).resolve().parent; W = D.parents[3]
q = sys.argv[1]; P = W / 'upload/pkg' / f'{q}_B'; c = json.loads((P / 'case.json').read_text()); L = c.get('locale', 'ko')
def syl(t): return max(1, len(re.sub('[^가-힣]', '', heard(t))) if L == 'ko' else intl.units(t, L))
M = None
def words(path):
    global M
    import mlx_whisper
    if M is None: M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
    r = mlx_whisper.transcribe(str(path), path_or_hf_repo=str(M), language=intl.WL[L], word_timestamps=True, temperature=0, condition_on_previous_text=False, verbose=None)
    return [(w['word'], float(w['start'])) for s in r['segments'] for w in s.get('words', [])]
subs = []; U = c['utterances']
PH = {'', 'auto', 'todo', 'tbd', 'tbc', 'xxx', 'xx', '...', '\u2026', '?', '??', '???', '-', 'placeholder', 'lorem', 'fixme', 'null', 'none'}
ph = [f"{u['id']} chunks {u['chunks']!r}" for u in U if isinstance(u.get('chunks'), str) or any(str(x).strip().lower() in PH for x in u.get('chunks') or [])]
if ph: print('B3 cues FAIL placeholder subtitle text (expand chunks with linebreak.py, or write them): ' + '; '.join(ph)); sys.exit(1)
for i, u in enumerate(U):
    ch = u.get('chunks')
    if not ch: continue
    on, off = u['onset'], u['offset']
    nxt = U[i + 1]['onset'] if i + 1 < len(U) else c['n'] / 30
    starts = [on]
    try:
        ws = words(D / 'cand' / q / f"{u['take']}.wav"); acc = []; n = 0
        for w, st in ws: acc.append((n, st)); n += syl(w)
        k = 0
        for x in ch[:-1]:
            k += syl(x); cand = [st for m, st in acc if m >= k - 1]
            starts.append(round(u['placed'] + cand[0], 3) if cand else None)
    except Exception as e:
        print('whisper fallback', u['id'], e); starts += [None] * (len(ch) - 1)
    tot = sum(syl(x) for x in ch); t = on
    for k in range(1, len(ch)):
        if starts[k] is None or not (starts[k - 1] < starts[k] < off): starts[k] = starts[k - 1] + (off - on) * syl(ch[k - 1]) / tot
    for k, x in enumerate(ch):
        e = min(off + .12, nxt) if k == len(ch) - 1 else starts[k + 1]
        cue = dict(start_s=round(starts[k], 3), end_s=round(e, 3), text=x, parent=u['id'])
        if u.get('emphasis') and u['emphasis'] in x: cue['emphasis'] = u['emphasis']
        subs.append(cue)
if L != 'ko':  # en/ja: a phrase cue shorter than 0.8 s joins its neighbour of the same line as a 2-line cue
    MIN = .8
    def short(i): return subs[i]['end_s'] - subs[i]['start_s'] < MIN
    i = 0
    while i < len(subs):
        if short(i):
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(subs) and subs[j]['parent'] == subs[i]['parent']
                  and subs[j]['text'].count('\n') + subs[i]['text'].count('\n') < 1]
            if nb:
                j = min(nb, key=lambda j: subs[j]['end_s'] - subs[j]['start_s']); a, b = sorted((i, j))
                m = dict(subs[a], end_s=subs[b]['end_s'], text=subs[a]['text'] + '\n' + subs[b]['text'])
                if subs[b].get('emphasis') and not m.get('emphasis'): m['emphasis'] = subs[b]['emphasis']
                subs[a:b + 1] = [m]; i = a; continue
            nxt = subs[i + 1]['start_s'] if i + 1 < len(subs) else c['n'] / 30
            subs[i]['end_s'] = round(min(subs[i]['start_s'] + MIN + .02, nxt), 3)
        i += 1
else:  # ko: a cue shorter than 0.4 s (q049 "정답 C," 0.27 s, "이 내기를" 0.37 s) joins its shorter same-line neighbour
    MIN = .4
    i = 0
    while i < len(subs):
        if subs[i]['end_s'] - subs[i]['start_s'] < MIN:
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(subs) and subs[j]['parent'] == subs[i]['parent']
                  and subs[j]['text'].count('\n') + subs[i]['text'].count('\n') < 1]
            if nb:
                j = min(nb, key=lambda j: subs[j]['end_s'] - subs[j]['start_s']); a, b = sorted((i, j))
                t = subs[a]['text'] + (' ' if len(subs[a]['text']) + len(subs[b]['text']) < 16 else '\n') + subs[b]['text']
                m = dict(subs[a], end_s=subs[b]['end_s'], text=t)
                if subs[b].get('emphasis') and not m.get('emphasis'): m['emphasis'] = subs[b]['emphasis']
                subs[a:b + 1] = [m]; i = a; continue
            nxt = subs[i + 1]['start_s'] if i + 1 < len(subs) else c['n'] / 30
            subs[i]['end_s'] = round(min(subs[i]['start_s'] + MIN + .02, nxt), 3)
        i += 1
c['subtitles'] = subs
(P / 'case.json').write_text(json.dumps(c, ensure_ascii=False, indent=1))
print('B3 cues', len(subs), 'max chars', max(len(s['text']) for s in subs), 'shortest', round(min(s['end_s'] - s['start_s'] for s in subs), 2))
