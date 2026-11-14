"""Narration + synthesized SFX v2 (all numpy, no samples): layered impact per hit (sub sweep + crack + body + debris tail),
whooshes, footfalls, rear rumble, stat count-up ticks + ding, A/B pops, brass sting on the verdict, quiet ambience bed.
Event times mirror Film.tsx through choreo.json. Two-pass loudnorm to -14 LUFS / -1.5 dBTP, mux with video_muted.mp4.
usage: mix.py <id>"""
import sys, json, re, subprocess, importlib.util
from pathlib import Path
import numpy as np, soundfile as sf
D = Path(__file__).resolve().parent; W = D.parents[1]; SR = 48000
q = sys.argv[1]; SUF = sys.argv[2] if len(sys.argv) > 2 else ''; P = W / 'upload/pkg' / f'{q}_B'; c = json.loads((P / 'case.json').read_text())
CH = json.loads((D / 'choreo.json').read_text()); rng = np.random.default_rng(7)
x, sr = sf.read(P / 'narration.wav', dtype='float32'); assert sr == SR
# ---- synthesized SFX (numpy only; no samples, no third-party audio) ----
def T(d): return np.arange(int(d * SR)) / SR
def noise(d, lo, hi):
    n = int(d * SR); X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
def sweep(d, f0, f1): t = T(d); return np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR)
def whoosh(d=.34):
    t = T(d); e = np.sin(np.pi * t / d) ** 2; u = t / d
    return .5 * e * (noise(d, 300, 1400) * (1 - u) + noise(d, 900, 5200) * u)
def thud(g=1.0): d = .22; return g * .8 * sweep(d, 105, 46) * np.exp(-T(d) * 16) + g * .25 * noise(d, 80, 700) * np.exp(-T(d) * 40)
def impact(g=1.0):
    d = .62; t = T(d)
    sub = sweep(d, 120, 36) * np.exp(-t * 7.5); crack = noise(d, 700, 6500) * np.exp(-t * 55); body = noise(d, 120, 900) * np.exp(-t * 18)
    gate = np.repeat(rng.random(int(d * 60) + 1) > .45, SR // 60)[:len(t)]; tail = noise(d, 1500, 9000) * gate * np.exp(-t * 6) * (t > .05)
    return g * (.95 * sub + .7 * crack + .55 * body + .16 * tail)
def rumble(d=.5): t = T(d); return .7 * noise(d, 35, 150) * np.sin(np.pi * t / d) ** 1.5
def ticks(n=8, d=.5):
    y = np.zeros(int(d * SR) + 2400)
    for i in range(n):
        t = T(.035); s = int(i * d / n * SR); y[s:s + len(t)] += .32 * np.sin(2 * np.pi * (880 * 2 ** (i / n)) * t) * np.exp(-t * 90)
    return y
def ding(): t = T(.45); return .3 * (np.sin(2 * np.pi * 1318.5 * t) + .6 * np.sin(2 * np.pi * 1975.5 * t) + .3 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 9)
def pop(f=520): t = T(.09); return .5 * np.sin(2 * np.pi * np.cumsum(f * (1 + 1.2 * np.exp(-t * 50))) / SR) * np.exp(-t * 38)
def brass(f, d):
    t = T(d); y = sum(np.sin(2 * np.pi * f * k * t * (1 + .002 * np.sin(2 * np.pi * 5.5 * t))) / k ** 1.25 for k in range(1, 9))
    return y * np.minimum(1, t / .012) * np.exp(-t * 3.2)
def sting():
    y = np.zeros(int(1.25 * SR)); a = .11 * brass(196.0, .16); y[:len(a)] += a
    for f in (261.63, 329.63, 392.0, 523.25):
        b = .085 * brass(f, 1.05); s = int(.15 * SR); y[s:s + len(b)] += b
    h = thud(.9); s = int(.15 * SR); y[s:s + len(h)] += h; return y
KIND = dict(whoosh=whoosh, thud=thud, step=lambda: thud(.45), impact=impact, big=lambda: impact(1.25), rumble=rumble, ticks=ticks, ding=ding, pop=pop, pop2=lambda: pop(690), sting=sting)
ev = []
for L in c['lines']:
    f0 = L['from']; m = L['mode']
    if m == 'face': ev += [(0, 'whoosh'), (f0 + 5, 'impact'), (f0 + 13, 'rumble')]
    if m == 'loop': ev.append((f0 + L['dur'] - 22, 'whoosh'))
    if m == 'stat': ev += [(f0, 'whoosh'), (f0 + 2, 'ticks'), (f0 + 9, 'thud'), (f0 + 14, 'ding')]
    if m == 'prompt': bA = round(L['onset'] * 30) + 24; ev += [(f0, 'thud'), (bA, 'pop'), (bA + 12, 'pop2')]
    if m == 'verdict':
        ev += [(f0, 'sting'), (f0 + 2, 'impact')] if L.get('k') == 0 else [(f0, 'thud')]
        ev += [(f0 + k, 'thud') for k in range(40, L['dur'] - 10, 40)]
    if m == 'clash':
        sh = L['shots']; seg = L['dur'] // len(sh)
        for i, s in enumerate(sh):
            a = f0 + i * seg; Dd = L['dur'] - i * seg if i == len(sh) - 1 else seg
            if s['s'] == 'charge': ev += [(a + CH['charge']['launch'], 'whoosh')] + [(a + k, 'step') for k in range(CH['charge']['launch'] + 3, Dd - 3, 6)]
            if s['s'] == 'rear': ev += [(a + 2, 'rumble'), (a + CH['rear']['up'], 'thud')]
            if s['s'] == 'strike': ev += [(a + CH['strike']['hit'] - 6, 'whoosh'), (a + CH['strike']['hit'], 'impact')]
            if s['s'] == 'impact':
                h = CH['impact']['hit']; ct = round(Dd * CH['impact']['counter']); ev += [(a + max(0, h - 6), 'whoosh'), (a + h, 'impact')]
                ev += [(a + ct - 5, 'whoosh'), (a + ct, 'big'), (a + ct + 16, 'thud')] if s.get('tank') else [(a + h + 14, 'thud')]
            if s['s'] == 'retreat': ev += [(a + CH['retreat']['slam'] - 7, 'whoosh'), (a + CH['retreat']['slam'], 'big'), (a + CH['retreat']['land'], 'thud')]
ev = [(round(float(fr) / 30, 3), k) for fr, k in ev]
fx = np.zeros(len(x), np.float64)
for at, kind in ev:
    y = KIND[kind](); s = int(at * SR); n = min(len(y), len(fx) - s)
    if n > 0: fx[s:s + n] += y[:n]
# duck SFX ~10 dB under narration so effects never mask words (CEO bc004 review: stat SFX hid "Record male")
w = int(.05 * SR); env = np.sqrt(np.convolve(np.asarray(x, np.float64) ** 2, np.ones(w) / w, 'same'))
duck = np.where(env > .01, .32, 1.0); duck = np.convolve(duck, np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); fx *= duck
bed = noise(len(x) / SR, 60, 420 if c['bg'] == 'ocean' else 900)[:len(x)]; bed = bed * (.75 + .25 * np.sin(2 * np.pi * .23 * np.arange(len(bed)) / SR)) * .012
fx = (.42 * fx + bed).astype(np.float32); fx = np.tanh(fx * 1.4) / 1.4
sf.write(P / 'sfx.wav', fx, SR, subtype='PCM_24'); sf.write(P / 'mix_pre.wav', x + fx, SR, subtype='PCM_24')
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(P / 'mix_pre.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'mix_pre.wav'), '-af', af + ',aresample=48000', '-ac', '2', '-c:a', 'pcm_s24le', str(P / 'mix_master.wav')], check=True)
def meas(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    sm = r[r.rindex('Summary:'):]; return float(re.search(r'I:\s+(-?[\d.]+) LUFS', sm)[1]), float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', sm)[1])
I0, T0 = meas(P / 'mix_master.wav'); g = min(-14 - I0, -1.6 - T0)
if abs(g) > .05:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'mix_master.wav'), '-af', f'volume={g:.2f}dB', '-c:a', 'pcm_s24le', str(P / 'mix_tmp.wav')], check=True); (P / 'mix_tmp.wav').replace(P / 'mix_master.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / f'video_muted{SUF}.mp4'), '-i', str(P / 'mix_master.wav'), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', str(P / f'video{SUF}.mp4')], check=True)
I, TP = meas(P / f'video{SUF}.mp4')
(P / f'loudness{SUF}.json').write_text(json.dumps(dict(integrated_lufs=I, true_peak_dbtp=TP, events=ev), indent=1)); print('MIX', q, 'I', I, 'TP', TP, 'events', len(ev))
