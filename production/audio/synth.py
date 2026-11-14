#!/usr/bin/env python3
"""Procedural score, ambience and effects for EP001, plus the narration stem and mix.

All sound is generated here (numpy), so no third-party music/SFX licence is involved.
Cue names follow the house audio column (MUS01..06, ST01/02, AMB01/02, FX01..06).
Usage: synth.py EPISODE_DIR  → EPISODE_DIR/audio/{mus,amb,fx,na}.wav, mix_raw.wav
"""
import json, pathlib, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, lfilter

SR = 48000
FPS = 30
N = 14400 * SR // FPS  # 480 s exactly
rng = np.random.default_rng(20261025)


def f2s(f):
    return int(round(f * SR / FPS))


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def env(n, a, r, sustain=1.0):
    e = np.ones(n) * sustain
    a = min(a, n); r = min(r, n)
    if a: e[:a] = np.linspace(0, sustain, a)
    if r: e[-r:] = np.linspace(e[-r] if r < n else sustain, 0, r)
    return e


def note(freq, dur, kind='pad', amp=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == 'pad':
        s = sum(np.sin(2 * np.pi * freq * d * t + rng.uniform(0, 6.28)) for d in (1.0, 1.003, 0.997))
        s += 0.35 * sum(np.sin(2 * np.pi * 2 * freq * d * t) for d in (1.002, 0.998))
        s += 0.12 * np.sin(2 * np.pi * 3 * freq * t)
        s *= env(n, int(1.6 * SR), int(1.8 * SR))
    elif kind == 'pluck':
        s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * 2 * freq * t) + 0.15 * np.sin(2 * np.pi * 3.01 * freq * t)
        s *= np.exp(-t * 3.2) * env(n, int(0.004 * SR), int(0.05 * SR))
    elif kind == 'bell':
        s = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * 2.76 * freq * t) + 0.25 * np.sin(2 * np.pi * 5.4 * freq * t)
        s *= np.exp(-t * 1.6) * env(n, int(0.003 * SR), int(0.1 * SR))
    elif kind == 'sub':
        s = np.sin(2 * np.pi * freq * t) * env(n, int(1.2 * SR), int(1.5 * SR))
    return amp * s / 2.5


def place(buf, x, start, gain=1.0):
    if start >= len(buf):
        return
    e = min(len(buf), start + len(x))
    if start < 0:
        x = x[-start:]; start = 0; e = min(len(buf), len(x))
    buf[start:e] += gain * x[:e - start]


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def stereo(x, width=0.25, delay_ms=11):
    d = int(delay_ms * SR / 1000)
    l = x.copy(); r = np.concatenate([np.zeros(d), x[:-d]]) if d else x.copy()
    return np.stack([l * (1 - width * 0.3) + r * width * 0.3, r * (1 - width * 0.3) + l * width * 0.3], 1)


def reverb(x, decay=2.2, mix=0.25):
    """Cheap feedback-comb reverb (Schroeder-style)."""
    out = np.zeros_like(x)
    for dms, g in ((29.7, 0.77), (37.1, 0.74), (41.1, 0.72), (43.7, 0.70)):
        d = int(dms * SR / 1000)
        g = g ** (2.2 / decay)
        a = np.zeros(d + 1); a[0] = 1; a[-1] = -g
        out += lfilter([1.0], a, x)
    for dms in (5.0, 1.7):
        d = int(dms * SR / 1000)
        b = np.zeros(d + 1); b[0] = -0.7; b[-1] = 1
        a = np.zeros(d + 1); a[0] = 1; a[-1] = -0.7
        out = lfilter(b, a, out)
    return (1 - mix) * x + mix * out / 4


# --------------------------------------------------------------- score sections
def section(a_f, b_f, chords, kind, bpm=60, plucks=None, bells=None, sub=True, pad_amp=0.16, fade_in=15, fade_out=15):
    """Render chord pads (one chord per bar of 4 beats) between frames a..b."""
    n = f2s(b_f) - f2s(a_f)
    x = np.zeros(n)
    bar = 4 * 60 / bpm
    t = 0.0; k = 0
    while t < n / SR:
        ch = chords[k % len(chords)]
        dur = bar + 1.8
        for m in ch:
            place(x, note(midi(m), dur, 'pad', pad_amp), int(t * SR))
        if sub:
            place(x, note(midi(ch[0] - 12), dur, 'sub', 0.22), int(t * SR))
        if plucks:
            for j, (beat, deg) in enumerate(plucks):
                m = ch[deg % len(ch)] + 12 * (deg // len(ch)) + 12
                place(x, note(midi(m), 2.2, 'pluck', 0.11), int((t + beat * 60 / bpm) * SR))
        if bells and k % 2 == 1:
            for beat, deg in bells:
                place(x, note(midi(ch[deg % len(ch)] + 24), 3.0, 'bell', 0.05), int((t + beat * 60 / bpm) * SR))
        t += bar; k += 1
    x = lp(x, 3800)
    fi, fo = f2s(fade_in) if fade_in else 0, f2s(fade_out) if fade_out else 0
    if fi: x[:fi] *= np.linspace(0, 1, fi)
    if fo: x[-fo:] *= np.linspace(1, 0, fo)
    return x


def build_music():
    mus = np.zeros(N)
    # MUS01 suspense (D minor, sparse): Q02 → Q13 in
    mus_sec = section(240, 3780, [[50, 57, 62, 65], [46, 53, 58, 62], [48, 55, 60, 63], [45, 52, 57, 61]], 'pad', bpm=52,
                      plucks=[(0, 4), (2.5, 6)], pad_amp=0.13, fade_in=15, fade_out=18)
    place(mus, mus_sec, f2s(240))
    # MUS02 explanation (A minor, steady plucks): Q13 → Q18 end
    place(mus, section(3780, 6150, [[45, 52, 57, 60], [41, 48, 53, 57], [48, 55, 60, 64], [43, 50, 55, 59]], 'pad', bpm=72,
                       plucks=[(0, 4), (1, 5), (2, 6), (3, 5)], pad_amp=0.10, fade_in=18, fade_out=15), f2s(3780))
    # MUS03 dispute (suspended, ticking): Q19 → Q23 end
    place(mus, section(6150, 8250, [[50, 55, 57, 62], [48, 53, 55, 60], [46, 51, 53, 58], [48, 53, 55, 60]], 'pad', bpm=66,
                       plucks=[(0, 4), (1.5, 5), (3, 4)], pad_amp=0.11, fade_in=15, fade_out=15), f2s(6150))
    # MUS04 judgment (low, slow): Q24 → Q28 minus 18f silence
    place(mus, section(8250, 9900 - 18, [[38, 45, 50, 53], [36, 43, 48, 51], [34, 41, 46, 50], [33, 40, 45, 49]], 'pad', bpm=48,
                       bells=[(0, 4)], pad_amp=0.13, fade_in=18, fade_out=15), f2s(8250))
    # MUS05 after verdict (reflective): Q30 → Q36 end
    place(mus, section(10260, 13200, [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 55]], 'pad', bpm=58,
                       plucks=[(0, 4), (2, 5)], bells=[(1, 6)], pad_amp=0.10, fade_in=15, fade_out=18), f2s(10260))
    # MUS06 ending (resolving, F major-ish): Q37 → end
    place(mus, section(13200, 14400, [[41, 48, 53, 57], [43, 50, 55, 58], [45, 52, 57, 60], [48, 55, 60, 64]], 'pad', bpm=56,
                       plucks=[(0, 4), (1, 5), (2, 6)], pad_amp=0.11, fade_in=18, fade_out=24), f2s(13200))
    return reverb(mus, 2.6, 0.32)


def stings():
    st = np.zeros(N)
    # ST01 ident swell 4 s at 720
    n = f2s(120)
    sw = bp(rng.standard_normal(n), 300, 3000) * np.linspace(0, 1, n) ** 2 * 0.08
    sw *= env(n, 1, f2s(12))
    place(st, sw, f2s(720))
    for m, off in ((62, 1.9), (69, 1.95), (74, 2.0)):
        place(st, note(midi(m), 3.5, 'bell', 0.09), f2s(720) + int(off * SR))
    place(st, note(midi(38), 2.5, 'sub', 0.25), f2s(720) + int(1.9 * SR))
    # ST02 verdict: single low tone, no gavel
    n = int(4.5 * SR); t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 49 * t) + 0.5 * np.sin(2 * np.pi * 98 * t) + 0.2 * np.sin(2 * np.pi * 147.3 * t)) * np.exp(-t * 0.9)
    tone *= env(n, int(0.01 * SR), int(0.3 * SR))
    place(st, 0.32 * tone, f2s(9900))
    place(st, note(midi(57), 4.0, 'bell', 0.05), f2s(9900) + int(0.05 * SR))
    return reverb(st, 3.0, 0.35)


def ambience():
    amb = np.zeros(N)
    def bed(a, b, fade):
        n = f2s(b) - f2s(a)
        x = lp(np.cumsum(rng.standard_normal(n)) * 0.002, 260)  # brown-ish hum
        x = hp(x, 30)
        x += hp(lp(rng.standard_normal(n), 6000), 2500) * 0.0035  # air
        x *= 0.9 + 0.1 * np.sin(2 * np.pi * 0.07 * np.arange(n) / SR)
        fo = f2s(fade)
        x[:fo] *= np.linspace(0, 1, fo); x[-fo:] *= np.linspace(1, 0, fo)
        return x
    place(amb, bed(0, 1188, 12), 0)              # AMB01 night lot
    place(amb, bed(1800, 3768, 12), f2s(1800))   # AMB02
    # distant pass-bys (filtered noise swells)
    for fr in (420, 2300, 3300):
        n = int(5 * SR)
        x = bp(rng.standard_normal(n), 120, 900) * np.hanning(n) * 0.03
        place(amb, x, f2s(fr))
    return amb


def fx(timing):
    out = np.zeros(N)
    def whoosh(at, dur=1.2, g=0.06, lo=200, hi=2400):
        n = int(dur * SR)
        x = bp(rng.standard_normal(n), lo, hi) * np.hanning(n) ** 1.5 * g
        place(out, x, f2s(at))
    def click(at, g=0.07):
        n = int(0.09 * SR); t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 1800 * t) * 0.5 + hp(rng.standard_normal(n), 2000) * 0.4) * np.exp(-t * 60)
        place(out, g * x, f2s(at))
    def bell(at, m=81, g=0.06):
        place(out, note(midi(m), 2.5, 'bell', g), f2s(at))
    def thud(at, g=0.18):
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (55 * np.exp(-t * 2) + 30) * t) * np.exp(-t * 4.5)
        place(out, g * lp(x, 300), f2s(at))
    whoosh(12, 2.4, 0.05, 150, 1600)          # FX01 Q01 light rise
    whoosh(480 + 140, 1.4, 0.05)                # FX02 Q03 -6 dB
    click(1500 + 30); click(1500 + 160)         # FX03 relation draw Q07
    thud(2520 + int(420 * 0.40), 0.12)          # FX04 Q10 (non-violent, at the omit card)
    for at in (4200, 5250, 10950):              # chapter cards
        whoosh(at, 1.6, 0.05, 250, 3000)
    click(4560 + 20)                            # FX05 Q15 card
    bell(6570 + 40, 84, 0.04)                   # FX06 Q20
    bell(7410 + 60, 84, 0.035)                  # FX06 Q22
    bell(12300 + 20, 84, 0.035)                 # FX06 Q35
    for c in ('Q05', 'Q12', 'Q16', 'Q19', 'Q21', 'Q24', 'Q30', 'Q32', 'Q33', 'Q36', 'Q37'):
        pass
    return out


def narration(epdir, timing):
    na = np.zeros(N)
    for it in timing['items']:
        x, sr = sf.read(epdir / it['file'])
        assert sr == SR
        if x.ndim > 1:
            x = x.mean(1)
        place(na, x, f2s(it['start']))
    return na


def duck_curve(timing, depth_db=-9.0, att=0.12, rel=0.6):
    """Music gain envelope: lowered while narration plays."""
    g = np.zeros(N)
    for it in timing['items']:
        g[f2s(it['start']):f2s(it['end'])] = 1
    # smooth
    k = int(att * SR)
    sm = np.convolve(g, np.ones(k) / k, mode='same')
    sm = np.maximum(sm, np.convolve(g, np.ones(int(rel * SR)) / int(rel * SR), mode='same'))
    sm = np.clip(sm * 1.5, 0, 1)
    return 10 ** (depth_db * sm / 20)


def main():
    ep = pathlib.Path(sys.argv[1])
    timing = json.load(open(ep / 'timing.json'))
    out = ep / 'audio'
    na = narration(ep, timing)
    mus = build_music() + stings()
    amb = ambience()
    fxs = fx(timing)
    duck = duck_curve(timing)
    mus *= duck
    amb *= 10 ** (-4 * (1 - duck) / 9)  # slight duck for ambience too
    # Q28 last 18 frames: hard silence for everything except nothing
    s0, s1 = f2s(9900 - 18), f2s(9900)
    for x in (mus, amb, fxs):
        x[s0:s1] = 0
    stems = {'na': na, 'mus': mus, 'amb': amb, 'fx': fxs}
    for k, v in stems.items():
        sf.write(out / f'stem_{k}.wav', stereo(v, 0.0 if k == 'na' else 0.35, 0 if k == 'na' else 11).astype(np.float32), SR, subtype='FLOAT')
    # relative balance: NA 0 dB, music ~ -14 dB under NA (with ducking), amb, fx
    mix = stereo(na, 0, 0) * 1.0 + stereo(mus, 0.35) * 0.55 + stereo(amb, 0.5) * 0.8 + stereo(fxs, 0.3) * 0.9
    sf.write(out / 'mix_raw.wav', mix.astype(np.float32), SR, subtype='FLOAT')
    print('samples', len(mix), 'seconds', len(mix) / SR)


if __name__ == '__main__':
    main()
