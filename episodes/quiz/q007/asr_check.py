#!/usr/bin/env python3
"""Re-recognise every narration sentence with Whisper and report character error rate.
Writes audio/na/asr_check.json; prints sentences above the threshold (default 0.08)."""
import json, re, sys, mlx_whisper
THR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.08
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
norm = lambda s: re.sub(r'[^가-힣0-9]', '', s.replace('A씨', '에이씨').replace('B씨', '비씨').replace('CCTV', '씨씨티비'))
asr_norm = lambda s: re.sub(r'[^가-힣0-9]', '', re.sub(r'(?i)\b(ac|a씨|에이씨)', '에이씨', re.sub(r'(?i)\b(bc|b씨|비씨)', '비씨', re.sub(r'(?i)cctv', '씨씨티비', s))))
def cer(a, b):
    a, b = norm(a), asr_norm(b); d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, cb in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (ca != cb))
    return d[-1] / max(1, len(a))
items = json.load(open('audio/na/index.json'))['items']
prev = {r['id']: r for r in json.load(open('audio/na/asr_check.json'))} if ONLY else {}
res = []
for it in items:
    if ONLY and it['id'] not in ONLY and it['id'] in prev:
        res.append(prev[it['id']]); continue
    asr = mlx_whisper.transcribe(it['file'], path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ko')['text'].strip()
    res.append(dict(id=it['id'], text=it['text'], asr=asr, cer=round(cer(it['text'], asr), 3), dur=it['dur']))
json.dump(res, open('audio/na/asr_check.json', 'w'), ensure_ascii=False, indent=1)
bad = [r for r in res if r['cer'] > THR]
print('sentences', len(res), 'mean cer', round(sum(r['cer'] for r in res) / len(res), 3), 'over', THR, ':', len(bad))
for r in bad:
    print('BAD', r['id'], r['cer'], '|', r['text'], '|', r['asr'])
