"""Pace-matched listening variants (post-processing, not native): internal pauses >0.18 s cut to 0.18 s
(production rule: pauses <=0.2 s), then ffmpeg atempo per line to 6.4 syll/s."""
import os, sys, json, subprocess, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); from common import SPOKEN, syl
def squeeze(x, sr, keep=.18, db=-40):
    w = int(sr * .01); n = len(x) // w; r = 20 * np.log10(np.sqrt(np.mean(x[:n*w].reshape(-1, w)**2, 1)) + 1e-9)
    q = r < r.max() + db; out = []; i = 0
    while i < n:
        j = i
        while j < n and q[j] == q[i]: j += 1
        seg = x[i*w:j*w]
        if q[i] and (j - i) * w > keep * sr and 0 < i and j < n: h = int(keep * sr / 2); seg = np.r_[seg[:h], seg[-h:]]
        out.append(seg); i = j
    return np.concatenate(out + [x[n*w:]])
for tag in ['qwen3tts-design_male', 'qwen3tts-cv_sohee']:
    meta = json.load(open(f'{HERE}/raw/{tag}.json'))
    for m in meta:
        i = m['line']; x, sr = sf.read(f'{HERE}/raw/{tag}_{i}.wav', dtype='float32'); x = squeeze(x, sr)
        tmp = f'{HERE}/raw/_sq.wav'; sf.write(tmp, x, sr); f = 6.4 / (syl(SPOKEN[i]) / (len(x) / sr)); m['atempo'] = f
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-af', f'atempo={f:.4f}', f'{HERE}/raw/{tag}-paced_{i}.wav'], check=True)
        print(tag, i, round(f, 3))
    json.dump(meta, open(f'{HERE}/raw/{tag}-paced.json', 'w'))
