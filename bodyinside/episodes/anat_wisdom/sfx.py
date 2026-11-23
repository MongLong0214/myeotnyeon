"""Procedural SFX for the 10 s clip (numpy only, no third-party audio): drill whine, crack click, lift clink, nerve pulses, room tone."""
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
SR = 48000; N = SR * 10; rng = np.random.default_rng(11)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
out = np.zeros(N)
t = np.arange(N) / SR
# room tone
out += 0.004 * lp(rng.normal(0, 1, N), 400)
# drill: spin-up 2.55 s, cutting 2.83-5.23 s (load dips pitch), spin-down 5.45 s
f = np.zeros(N); amp = np.zeros(N)
for i, tt in enumerate(t):
    pass
a0, c0, c1, a1 = 2.75, 3.27, 5.07, 5.55
f = np.where(t < a0, 0, np.where(t < c0, 2600 + 1600 * (t - a0) / (c0 - a0), 4200))
load = ((t > c0) & (t < c1)) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.7 * (t - c0)) ** 2)
f = f - 650 * load
f = np.where(t > c1, 4200 * np.clip(1 - (t - c1) / (a1 - c1) * 0.7, 0.3, 1), f)
amp = np.clip((t - a0) / 0.15, 0, 1) * np.clip((a1 - t) / 0.35, 0, 1)
ph = 2 * np.pi * np.cumsum(f) / SR
drill = 0.5 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph + 0.3)
grind = bp(rng.normal(0, 1, N), 1500, 6000) * load * 0.5
out += 0.11 * amp * (drill + grind)
# crack click at 6.02 s, lift clink at 6.73 s
def burst(at, dur, lo, hi, g, decay):
    n = int(dur * SR); e = np.exp(-np.arange(n) / SR * decay)
    x = bp(rng.normal(0, 1, n), lo, hi) * e; s = int(at * SR); out[s:s + n] += g * x
burst(5.40, 0.12, 1200, 7000, 0.55, 60); burst(5.43, 0.08, 300, 1500, 0.35, 70)
k = int(0.4 * SR); tk = np.arange(k) / SR
clink = (np.sin(2 * np.pi * 3100 * tk) + 0.6 * np.sin(2 * np.pi * 5230 * tk)) * np.exp(-tk * 14)
s = int(6.05 * SR); out[s:s + k] += 0.06 * clink
s = int(7.45 * SR); out[s:s + k] += 0.045 * clink
# nerve pulses: soft low thumps
for at in (0.53, 8.20, 8.73, 9.27):
    n = int(0.35 * SR); tn = np.arange(n) / SR
    x = np.sin(2 * np.pi * (58 + 30 * np.exp(-tn * 20)) * tn) * np.exp(-tn * 9) * np.clip(tn / 0.008, 0, 1)
    s = int(at * SR); m = min(n, N - s); out[s:s + m] += 0.35 * x[:m]
# cut swishes at shot changes
for at in ():
    n = int(0.35 * SR); e = np.sin(np.linspace(0, np.pi, n)) ** 2
    s = int((at - 0.2) * SR); out[s:s + n] += 0.05 * hp(rng.normal(0, 1, n), 2500) * e
st = np.stack([out, np.concatenate([np.zeros(15), out[:-15]])], 1)
sf.write('audio/sfx10.wav', st.astype(np.float32), SR)
print('ok', np.abs(st).max())
