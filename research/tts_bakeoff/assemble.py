"""Metrics + -16 LUFS samples + compare_all.mp3. Runs in venvs/mlx."""
import os, re, json, subprocess, sys
import warnings; warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly
from math import gcd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import SPOKEN, syl
SR = 48000
ORDER = ['supertonic3_M1', 'qwen3tts-design_male', 'qwen3tts-design_male-paced', 'qwen3tts-cv_sohee', 'qwen3tts-cv_sohee-paced', 'qwen3tts-design_female', 'qwen3tts-cv_ryan',
         'voxcpm2-design_male', 'voxcpm2-design_female', 'chatterbox-ml_male', 'chatterbox-ml_female',
         'melotts_KR', 'moss-nano_female', 'moss-nano_male']
def sino(n):
    n = int(n)
    if n >= 10000: q, r = divmod(n, 10000); return sino(q) + '만' + (sino(r) if r else '')
    o = ''
    for v, u in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        q, n = divmod(n, v)
        if q: o += ('' if q == 1 and v > 1 else '일이삼사오육칠팔구'[q-1]) + u
    return o or '영'
def limit(y):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af',
                          'alimiter=limit=0.89:attack=2:release=60:level=disabled', '-f', 'f32le', '-'], input=y.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def hang(t): return re.sub('[^가-힣]', '', re.sub(r'\d+', lambda m: sino(m[0]), t))
def cer(a, b):
    d = list(range(len(b) + 1))
    for i, c in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, v in enumerate(b, 1): d[j] = min(p[j] + 1, d[j-1] + 1, p[j-1] + (c != v))
    return d[-1] / max(1, len(a))
asr = json.load(open(f'{HERE}/raw/asr.json')); meter = pyln.Meter(SR); rows = []; parts = []
for tag in ORDER:
    meta = json.load(open(f'{HERE}/raw/{tag}.json')); xs = []; r = dict(tag=tag, lines=[])
    for m in meta:
        x, sr = sf.read(f"{HERE}/raw/{tag}_{m['line']}.wav", dtype='float32')
        if x.ndim > 1: x = x.mean(1)
        dur = len(x) / sr; g = gcd(SR, sr); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
        a = asr[f"{tag}_{m['line']}"]; e = cer(hang(SPOKEN[m['line']]), hang(a))
        r['lines'].append(dict(dur=dur, sps=syl(SPOKEN[m['line']]) / dur, rtf=m['synth_s'] / dur, cer=e, asr=a)); xs += [x, np.zeros(int(.5 * SR), np.float32)]
    y = np.concatenate(xs[:-1]); y = pyln.normalize.loudness(y, meter.integrated_loudness(y), -16.0)
    for _ in range(4):  # peak limiter at -1 dBFS, then re-gain; converges to -16 LUFS within ~0.1 LU
        if np.abs(y).max() <= 0.891: break
        y = limit(y); y = pyln.normalize.loudness(y, meter.integrated_loudness(y), -16.0)
    y = np.clip(y, -0.891, 0.891)
    r.update(lufs=meter.integrated_loudness(y), peak_db=20 * np.log10(np.abs(y).max()),
             sps=sum(syl(t) for t in SPOKEN) / sum(l['dur'] for l in r['lines']),
             cer=float(np.mean([l['cer'] for l in r['lines']])), rtf=float(np.mean([l['rtf'] for l in r['lines']])))
    sf.write(f'{HERE}/samples/{tag}.wav', y, SR, subtype='PCM_24'); parts += [y, np.zeros(SR, np.float32)]; rows.append(r)
    print(f"{tag:26s} sps={r['sps']:.2f} cer={r['cer']:.3f} rtf={r['rtf']:.2f} lufs={r['lufs']:.1f} pk={r['peak_db']:.1f}")
sf.write(f'{HERE}/raw/compare_all.wav', np.concatenate(parts[:-1]), SR, subtype='PCM_24')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{HERE}/raw/compare_all.wav', '-codec:a', 'libmp3lame', '-b:a', '192k', f'{HERE}/compare_all.mp3'], check=True)
json.dump(rows, open(f'{HERE}/metrics.json', 'w'), ensure_ascii=False, indent=1)
