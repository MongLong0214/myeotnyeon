"""Procedural SFX from episode.json 'sfx' events (numpy only, no third-party audio). usage: python sfx.py EPISODE_DIR -> audio/sfx.wav
events: {"drill":[spin_up, cut_start, cut_end, spin_down]}, {"crack":t}, {"clink":[t,gain]}, {"thump":t}, {"whoosh":t}"""
import numpy as np, soundfile as sf, json, sys, os
from scipy.signal import butter, sosfilt
E = sys.argv[1]; ep = json.load(open(f'{E}/episode.json')); SR = 48000; N = int(SR * ep['duration']); rng = np.random.default_rng(11)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
out = 0.004 * lp(rng.normal(0, 1, N), 400); t = np.arange(N) / SR
def add(at, x, g):
    s = int(at * SR); m = min(len(x), N - s)
    if m > 0: out[s:s + m] += g * x[:m]
for ev in ep['sfx']:
    k, v = next(iter(ev.items()))
    if k == 'drill':
        a0, c0, c1, a1 = v
        f = np.where(t < a0, 0, np.where(t < c0, 2600 + 1600 * (t - a0) / (c0 - a0), 4200))
        load = ((t > c0) & (t < c1)) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.7 * (t - c0)) ** 2); f = f - 650 * load
        f = np.where(t > c1, 4200 * np.clip(1 - (t - c1) / (a1 - c1) * 0.7, 0.3, 1), f)
        amp = np.clip((t - a0) / 0.15, 0, 1) * np.clip((a1 - t) / 0.35, 0, 1); ph = 2 * np.pi * np.cumsum(f) / SR
        out += 0.11 * amp * (0.5 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph + 0.3) + bp(rng.normal(0, 1, N), 1500, 6000) * load * 0.5)
    elif k == 'crack':
        for lo, hi, g, dec, dt in ((1200, 7000, 0.55, 60, 0), (300, 1500, 0.35, 70, 0.03)):
            n = int(0.12 * SR); add(v + dt, bp(rng.normal(0, 1, n), lo, hi) * np.exp(-np.arange(n) / SR * dec), g)
    elif k == 'clink':
        tk = np.arange(int(0.4 * SR)) / SR; add(v[0], (np.sin(2 * np.pi * 3100 * tk) + 0.6 * np.sin(2 * np.pi * 5230 * tk)) * np.exp(-tk * 14), v[1])
    elif k == 'thump':
        tn = np.arange(int(0.35 * SR)) / SR; add(v, np.sin(2 * np.pi * (58 + 30 * np.exp(-tn * 20)) * tn) * np.exp(-tn * 9) * np.clip(tn / 0.008, 0, 1), 0.35)
    elif k == 'whoosh':
        n = int(0.35 * SR); add(v - 0.2, hp(rng.normal(0, 1, n), 2500) * np.sin(np.linspace(0, np.pi, n)) ** 2, 0.05)
os.makedirs(f'{E}/audio', exist_ok=True)
sf.write(f'{E}/audio/sfx.wav', np.stack([out, np.concatenate([np.zeros(15), out[:-15]])], 1).astype(np.float32), SR); print('ok')
