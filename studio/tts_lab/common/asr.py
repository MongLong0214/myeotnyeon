"""Whisper re-recognition + CER for every samples/*.wav not yet in metrics/asr.json.
Run with the existing work/.venv (mlx_whisper), HF_HUB_OFFLINE=1. Usage: asr.py [name-prefix ...]"""
import json, pathlib, re, sys
import mlx_whisper

LAB = pathlib.Path(__file__).resolve().parents[1]
LINES = {l['id']: l for l in json.load(open(LAB / 'common' / 'texts.json'))['lines']}
DIG = '영일이삼사오육칠팔구'


def sino(n):
    if n == 0:
        return '영'
    out = ''
    for big, name in ((10 ** 8, '억'), (10 ** 4, '만')):
        if n >= big:
            q, n = divmod(n, big); out += (sino(q) if q > 1 or name != '만' else '') + name
    for p, name in ((1000, '천'), (100, '백'), (10, '십')):
        if n >= p:
            q, n = divmod(n, p); out += ('' if q == 1 else DIG[q]) + name
    return out + (DIG[n] if n else '')


def norm(s):
    s = re.sub(r'\d+', lambda m: sino(int(m.group())), s.replace(',', ''))
    return re.sub(r'[^가-힣]', '', s)


def cer(ref, hyp):
    a, b = norm(ref), norm(hyp); d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, cb in enumerate(b, 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (ca != cb))
    return d[-1] / max(1, len(a))


assert norm('30대 20대 8개월 2년') == norm('삼십 대 이십대 팔 개월 이 년')
apath = LAB / 'metrics' / 'asr.json'
res = json.load(open(apath)) if apath.exists() else {}
pre = sys.argv[1:]
files = sorted((LAB / 'samples').glob('*.wav'))
for f in files:
    n = f.stem
    if n in res or (pre and not any(n.startswith(p) for p in pre)):
        continue
    line = int(n.rsplit('_', 1)[1])
    txt = mlx_whisper.transcribe(str(f), path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ko',
                                 condition_on_previous_text=False)['text'].strip()
    res[n] = dict(asr=txt, cer=round(cer(LINES[line]['ref'], txt), 4))
    print(n, res[n]['cer'], txt, flush=True)
    json.dump(res, open(apath, 'w'), ensure_ascii=False, indent=1)
