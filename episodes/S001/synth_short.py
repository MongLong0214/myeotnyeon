#!/usr/bin/env python3
"""S001 Shorts sound: quirky sci-fi synth bed, cartoon SFX on the scene anchors, narration, mix, master.

All procedural (numpy) — no third-party audio. Uses anchors.json (from build.py) and timing.json.
Writes audio/mix_master.wav (-14 LUFS, true peak -1.5 dBTP; Shorts are played louder than long-form).
"""
import json, pathlib, subprocess, sys
import numpy as np, soundfile as sf
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / 'production' / 'audio'))
from synth import SR, FPS, f2s, lp, hp, bp, env, note, midi, stereo, reverb
from synth2 import place, kick, clap, shaker, riser, impact

HERE = pathlib.Path(__file__).parent
rng = np.random.default_rng(7)
A = json.load(open(HERE / 'anchors.json'))
TOTAL = A['total']
N = f2s(TOTAL)
CUE = A['cues']


def at(c, k, d=0):
    return CUE[c]['from'] + CUE[c]['a'][k] + d


def t_(n):
    return np.arange(n) / SR


# ------------------------------------------------------------------ sfx voices
def boing(g=0.25, f0=260, dur=0.45):
    n = int(dur * SR); t = t_(n)
    fr = f0 * (1 + 0.6 * np.exp(-t * 9) * np.sin(2 * np.pi * 18 * t))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return g * np.sin(ph) * np.exp(-t * 5)


def slide(f0, f1, dur=0.5, g=0.15):
    n = int(dur * SR); t = t_(n)
    fr = np.geomspace(f0, f1, n); ph = 2 * np.pi * np.cumsum(fr) / SR
    return g * np.sin(ph) * env(n, int(0.01 * SR), int(0.08 * SR))


def engine(dur=0.9, g=0.35):
    n = int(dur * SR); t = t_(n)
    fr = 45 + 110 * (t / dur) ** 0.7
    ph = 2 * np.pi * np.cumsum(fr) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = lp(saw + 0.4 * bp(rng.standard_normal(n), 80, 900), 1400)
    return g * x * env(n, int(0.03 * SR), int(0.2 * SR))


def crash(g=0.5):
    n = int(1.4 * SR); t = t_(n)
    x = bp(rng.standard_normal(n), 120, 6000) * np.exp(-t * 4) + 0.8 * np.sin(2 * np.pi * (60 + 80 * np.exp(-t * 20)) * t) * np.exp(-t * 6)
    return g * x


def thunk(g=0.35):
    n = int(0.35 * SR); t = t_(n)
    return g * (np.sin(2 * np.pi * (110 + 90 * np.exp(-t * 35)) * t) * np.exp(-t * 14) + bp(rng.standard_normal(n), 300, 2500) * np.exp(-t * 60) * 0.4)


def knock(g=0.6):          # gavel on wood
    n = int(0.5 * SR); t = t_(n)
    x = sum(np.sin(2 * np.pi * fq * t) * np.exp(-t * d) for fq, d in ((420, 30), (780, 45), (1250, 60)))
    return g * (x / 3 + bp(rng.standard_normal(n), 800, 5000) * np.exp(-t * 90) * 0.5)


def beep(f=1800, dur=0.12, g=0.08):
    n = int(dur * SR); return g * np.sign(np.sin(2 * np.pi * f * t_(n))) * env(n, 20, 200)


def pop(g=0.12):
    n = int(0.12 * SR); t = t_(n)
    return g * np.sin(2 * np.pi * (700 + 1200 * np.exp(-t * 40)) * t) * np.exp(-t * 35)


def tick(g=0.09):
    n = int(0.05 * SR); return g * hp(rng.standard_normal(n), 3000) * np.exp(-t_(n) * 120)


def ding(g=0.12, f=1320):
    return note(f, 1.4, 'bell', g * 2.5)


# ------------------------------------------------------------------ music: quirky synth bed
BPM = 118; BEAT = 60 / BPM


def saw(f, dur, g, det=0.006):
    n = int(dur * SR); t = t_(n)
    x = sum(2 * ((f * (1 + d) * t) % 1) - 1 for d in (-det, 0, det)) / 3
    return g * lp(x, 2600) * env(n, int(0.005 * SR), int(0.06 * SR))


def bed(a_f, b_f, prog, drums=True, energy=1.0):
    n = f2s(b_f) - f2s(a_f); x = np.zeros(n)
    bar = 4 * BEAT; k = 0; t = 0.0
    arp = [0, 2, 1, 2, 3, 2, 1, 2]
    while t < n / SR:
        ch = prog[k % len(prog)]; s = int(t * SR)
        for i in range(8):
            m = ch[arp[i] % len(ch)] + 12
            place(x, saw(midi(m), BEAT / 2 * 0.9, 0.05 * energy), s + int(i * BEAT / 2 * SR))
        for i in range(4):
            place(x, lp(saw(midi(ch[0] - 12), BEAT * 0.8, 0.16 * energy, 0.01), 500), s + int(i * BEAT * SR))
        if drums:
            for b in range(4):
                bs = s + int(b * BEAT * SR)
                if b in (0, 2): place(x, kick(0.38 * energy), bs)
                if b in (1, 3): place(x, clap(0.08 * energy), bs)
                place(x, shaker(0.025 * energy), bs + int(BEAT / 2 * SR))
        t += bar; k += 1
    f = f2s(6); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    return x


PROG = [[57, 60, 64, 67], [53, 57, 60, 64], [55, 58, 62, 65], [52, 56, 59, 62]]    # Am7 Fmaj7 Gm7 E7 (sci-fi tilt)


def main():
    mus = np.zeros(N); fx = np.zeros(N)
    v = CUE['C7']['from']
    place(mus, bed(0, CUE['C6']['from'], PROG, energy=0.7), 0)
    c6 = CUE['C6']['from']
    for i in range(int((v - c6) / FPS * 2)):
        place(fx, tick(0.045 if i % 2 else 0.03), f2s(c6) + int(i * 0.5 * SR))
    place(mus, riser((v - c6) / FPS * 0.85, 0.08), f2s(v) - int((v - c6) / FPS * 0.85 * SR) - int(0.4 * SR))
    mus[f2s(v) - int(0.4 * SR):f2s(v)] = 0
    place(mus, impact(0.5), f2s(v))
    place(mus, bed(CUE['C8']['from'], TOTAL, PROG[::-1], energy=0.65), f2s(CUE['C8']['from']))
    # scene sfx — only sounds that belong to the scene (owner: no pops/boings on cuts)
    place(fx, engine(0.7, 0.3), f2s(at('C1', 's2')))
    place(fx, thunk(0.22), f2s(at('C1', 's2', 6)))
    for d in (2, 12, 22):
        place(fx, thunk(0.14), f2s(at('C2', 's1', d)))
    for i in range(4):
        place(fx, beep(1400, 0.14, 0.035), f2s(at('C2', 'back')) + int(i * 0.34 * SR))
    place(fx, engine(0.8, 0.32), f2s(at('C2', 'again')))
    place(fx, crash(0.32), f2s(at('C2', 'hit')))
    place(fx, thunk(0.22), f2s(at('C5', 'court', 4)))
    place(fx, knock(0.45), f2s(at('C7', 's1', 2)))
    place(fx, thunk(0.22), f2s(at('C7', 'jing'))); place(fx, thunk(0.25), f2s(at('C7', 'yu')))
    fx = reverb(fx, 0.8, 0.12)
    # narration + duck
    timing = json.load(open(HERE / 'timing.json'))
    na = np.zeros(N); g = np.zeros(N)
    for it in timing['items']:
        x, sr = sf.read(HERE / it['file']); x = x.mean(1) if x.ndim > 1 else x
        place(na, x, f2s(it['start'])); g[f2s(it['start']):f2s(it['end'])] = 1
    k = int(0.12 * SR); sm = np.clip(np.convolve(g, np.ones(k) / k, mode='same') * 1.5, 0, 1)
    duck = 10 ** (-9 * sm / 20)
    mix = stereo(na, 0, 0) + stereo(mus * duck, 0.35) * 0.85 + stereo(fx, 0.3) * 0.9
    out = HERE / 'audio'; out.mkdir(exist_ok=True)
    sf.write(out / 'mix_raw.wav', mix.astype(np.float32), SR, subtype='FLOAT')
    p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(out / 'mix_raw.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex('{'):p1.rindex('}') + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(out / 'mix_raw.wav'), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', str(out / 'mix_master.wav')], check=True)
    print('seconds', round(N / SR, 2))


if __name__ == '__main__':
    main()
