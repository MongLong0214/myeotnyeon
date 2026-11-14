"""Voice steps that need whisper: per-line recognition check and option onsets. Run with the venv of the locale
(ko: work/.venv, en/ja: research/tts_kokoro/.venv) from the work root:
  python -m factory.shorts.voice check <id>     -> JSON {bad: [[line, cer, heard], ...]}
  python -m factory.shorts.voice options <id>   -> writes case.json option_onsets from whisper word starts"""
import json
import os
import re
import sys
from pathlib import Path

os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from factory.shorts.core import BF, PKG, say  # noqa: E402

LIMIT = {'ko': .08, 'en': .08, 'ja': .10}


def cer(a, b):
    d = list(range(len(b) + 1))
    for i, c in enumerate(a, 1):
        prev = d[:]
        d[0] = i
        for j, v in enumerate(b, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (c != v))
    return d[-1] / max(1, len(a))


def norm(t, L):
    if L == 'ko':
        return re.sub('[^가-힣]', '', say(t, 'ko'))
    if L == 'en':
        return re.sub('[^a-z]', '', say(t, 'en').lower())
    sys.path.insert(0, str(BF))
    import intl
    return intl.norm(t, 'ja')


def check(q):
    c = json.loads((PKG / f'{q}_B/case.json').read_text())
    L = c.get('locale', 'ko')
    bad = []
    for u in c['utterances']:
        e = cer(norm(u['tts'], L), norm(u['asr'], L))
        if e > LIMIT[L]:
            bad.append([u['id'], round(e, 3), u['asr'].strip()])
    return dict(bad=bad, limit=LIMIT[L])


def options(q):
    sys.path.insert(0, str(BF))
    import intl
    import mlx_whisper
    P = PKG / f'{q}_B'
    c = json.loads((P / 'case.json').read_text())
    L = c.get('locale', 'ko')
    u = next((x for x in c['utterances'] if x['mode'] == 'options'), None)
    if u is None:  # result_first format: no options line
        return {'offsets': [], 'how': 'no quiz'}
    M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
    r = mlx_whisper.transcribe(str(BF / 'cand' / q / f"{u['take']}.wav"), path_or_hf_repo=str(M), language=intl.WL[L], word_timestamps=True,
                               temperature=0, condition_on_previous_text=False, verbose=None)
    words = [(w['word'], float(w['start'])) for s in r['segments'] for w in s.get('words', [])]

    def n(t):
        return max(1, intl.units(say(t, L), L)) if L != 'ko' else max(1, len(re.sub('[^가-힣]', '', say(t, L))))
    acc, k = [], 0
    for w, st in words:
        acc.append((k, st))
        k += n(w) if re.search(r'\w', w) else 0
    offs, before = [0.0], 0
    for ch in c['choices'][:-1]:
        before += n(ch)
        cand = [st for m, st in acc if m >= before - 1]
        offs.append(round(cand[0], 3) if cand else None)
    if None in offs or offs != sorted(offs):
        dur = u['offset'] - u['onset']
        tot = sum(n(x) for x in c['choices'])
        offs = [0.0, round(dur * n(c['choices'][0]) / tot, 3), round(dur * (n(c['choices'][0]) + n(c['choices'][1])) / tot, 3)]
        how = 'syllable share (whisper words did not line up)'
    else:
        how = 'whisper word starts'
    c['option_offsets'] = offs
    c['option_onsets'] = [round(u['placed'] + o, 3) for o in offs]
    (P / 'case.json').write_text(json.dumps(c, ensure_ascii=False, indent=1))
    return dict(offsets=offs, how=how)


if __name__ == '__main__':
    cmd, q = sys.argv[1], sys.argv[2]
    print(json.dumps(check(q) if cmd == 'check' else options(q), ensure_ascii=False))
