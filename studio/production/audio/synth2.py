#!/usr/bin/env python3
"""v2 light cut sound: upbeat procedural music, edit-synced effects, narration, mix and master.

All sound is generated here (numpy), so no third-party music/SFX licence is involved.
Reads EPISODE_DIR/{script.json, timing.json, edit_fx.json}; writes EPISODE_DIR/audio/
stem_{na,mus,amb,fx}.wav, mix_raw.wav and mix_master.wav (two-pass loudnorm to -16 LUFS,
true peak -1.5 dBFS).
Usage: synth2.py EPISODE_DIR
"""
import json, pathlib, subprocess, sys
import numpy as np, soundfile as sf
from synth import SR, FPS, f2s, lp, hp, bp, env, note, midi, stereo, reverb

rng = np.random.default_rng(20261026)
BPM = 104
BEAT = 60 / BPM


def place(buf, x, start, gain=1.0):
    if start >= len(buf) or start + len(x) <= 0:
        return
    if start < 0:
        x = x[-start:]; start = 0
    e = min(len(buf), start + len(x))
    buf[start:e] += gain * x[:e - start]


# ------------------------------------------------------------------ drum voices
def kick(g=0.5):
    n = int(0.35 * SR); t = np.arange(n) / SR
    return g * np.sin(2 * np.pi * (48 + 90 * np.exp(-t * 28)) * t) * np.exp(-t * 9)


def clap(g=0.12):
    n = int(0.22 * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 900, 5000) * (np.exp(-t * 26) + 0.5 * np.exp(-((t - 0.012) ** 2) / 1e-5))
    return g * x


def shaker(g=0.035):
    n = int(0.07 * SR); t = np.arange(n) / SR
    return g * hp(rng.standard_normal(n), 6000) * np.exp(-t * 55)


def pluck(m, g=0.1, dur=0.9):
    return note(midi(m), dur, 'pluck', g)


def bass(m, dur, g=0.18):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * midi(m) * t) + 0.25 * np.sin(2 * np.pi * 2 * midi(m) * t)
    return g * lp(x, 400) * env(n, int(0.01 * SR), int(0.08 * SR))


PROG_MAIN = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]       # Am F C G
PROG_LIFT = [[53, 57, 60], [55, 59, 62], [52, 55, 59], [57, 60, 64]]       # F G Em Am
PROG_DARK = [[57, 60, 64], [57, 60, 63], [53, 57, 60], [52, 56, 59]]       # Am Am(b) F E


def groove(a_f, b_f, prog, drums=True, plucks=True, pad=0.06, kick_g=0.42, energy=1.0, fade=10):
    """Bars of 4 beats from frame a to b."""
    n = f2s(b_f) - f2s(a_f)
    x = np.zeros(n)
    bar = 4 * BEAT
    k = 0; t = 0.0
    pattern = [0, 2, 1, 2, 0, 2, 1, 2]   # arpeggio degrees on 8ths
    while t < n / SR:
        ch = prog[k % len(prog)]
        s = int(t * SR)
        for m in ch:
            place(x, note(midi(m), bar + 1.0, 'pad', pad * energy), s)
        place(x, bass(ch[0] - 24, bar * 0.48, 0.16 * energy), s)
        place(x, bass(ch[0] - 24, bar * 0.48, 0.13 * energy), s + int(bar * 0.5 * SR))
        if drums:
            for b in range(4):
                bs = s + int(b * BEAT * SR)
                if b in (0, 2):
                    place(x, kick(kick_g * energy), bs)
                if b in (1, 3):
                    place(x, clap(0.10 * energy), bs)
                for h in (0, 0.5):
                    place(x, shaker(0.03 * energy * (1.3 if h else 1.0)), bs + int(h * BEAT * SR))
        if plucks:
            for j, d in enumerate(pattern):
                m = ch[d] + 12
                place(x, pluck(m, 0.075 * energy), s + int(j * BEAT / 2 * SR))
        t += bar; k += 1
    f = f2s(fade)
    x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    return x


def pulse(a_f, b_f, root=45, g=0.12):
    """Tense cold-open bed: sub pulse on every beat + ticking 16ths, minor pad."""
    n = f2s(b_f) - f2s(a_f)
    x = np.zeros(n)
    t = 0.0; i = 0
    while t < n / SR:
        s = int(t * SR)
        if i % 4 == 0:
            place(x, note(midi(root - 12), BEAT * 1.2, 'sub', g * 1.4), s)
        place(x, shaker(0.022 if i % 2 else 0.032), s)
        t += BEAT / 2; i += 1
    for m in (root + 12, root + 15, root + 19):
        place(x, note(midi(m), n / SR + 1.0, 'pad', 0.05), 0)
    x[:f2s(8)] *= np.linspace(0, 1, f2s(8))
    return x


def riser(dur, g=0.08):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 400, 6000) * (t / dur) ** 2.2
    tone = np.sin(2 * np.pi * (200 + 600 * (t / dur) ** 2) * t) * 0.3 * (t / dur) ** 2
    return g * (x + tone)


def impact(g=0.4):
    n = int(3.5 * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 46 * t) + 0.5 * np.sin(2 * np.pi * 92 * t)) * np.exp(-t * 1.2)
    x += bp(rng.standard_normal(n), 60, 900) * np.exp(-t * 6) * 0.6
    return g * x * env(n, int(0.004 * SR), int(0.3 * SR))


def build_music(script, total):
    N = f2s(total)
    mus = np.zeros(N)
    c = {q['cue_id']: q for q in script['cues']}
    ci = lambda q: c[q]['in_frame']
    co = lambda q: c[q]['out_frame_exclusive']
    place(mus, pulse(0, ci('Q04')), 0)
    # ident sting
    place(mus, riser(1.2, 0.05), f2s(ci('Q04')) - int(1.2 * SR))
    for m, off in ((69, 0.0), (76, 0.06), (81, 0.12)):
        place(mus, note(midi(m), 2.6, 'bell', 0.09), f2s(ci('Q04')) + int(off * SR))
    place(mus, note(midi(33), 2.2, 'sub', 0.3), f2s(ci('Q04')))
    place(mus, groove(ci('Q05'), ci('Q07'), PROG_MAIN, drums=False, energy=0.8), f2s(ci('Q05')))
    place(mus, groove(ci('Q07'), ci('Q12'), PROG_DARK, plucks=False, energy=0.85), f2s(ci('Q07')))
    place(mus, groove(ci('Q12'), co('Q21'), PROG_MAIN, energy=1.0), f2s(ci('Q12')))
    # I: build to the verdict, then silence for 0.5 s
    a, b = ci('Q22'), ci('Q23')
    place(mus, pulse(a, b, root=45, g=0.1), f2s(a))
    place(mus, riser((b - a) / FPS * 0.8, 0.07), f2s(b) - int((b - a) / FPS * 0.8 * SR) - int(0.5 * SR))
    mus[f2s(b) - int(0.5 * SR):f2s(b)] = 0
    v = f2s(ci('Q23'))
    place(mus, impact(0.45), v)
    for m in (45, 52, 57):
        place(mus, note(midi(m), 6.0, 'pad', 0.07), v)
    place(mus, groove(ci('Q24'), ci('Q26'), PROG_MAIN, drums=False, energy=0.7), f2s(ci('Q24')))
    place(mus, groove(ci('Q26'), ci('Q32'), PROG_LIFT, energy=1.0), f2s(ci('Q26')))
    place(mus, groove(ci('Q32'), total, PROG_MAIN, energy=0.9, fade=45), f2s(ci('Q32')))
    return mus


def build_fx(efx, total):
    N = f2s(total)
    out = np.zeros(N)

    def swish(at, g=0.03):
        n = int(0.35 * SR)
        x = bp(rng.standard_normal(n), 1200, 7000) * np.hanning(n) ** 2 * g
        place(out, x, f2s(at) - n // 2)

    def pop(at, g=0.06, f0=900):
        n = int(0.12 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (f0 + 900 * np.exp(-t * 40)) * t) * np.exp(-t * 38)
        place(out, g * x, f2s(at))

    def stamp(at, g=0.3):
        n = int(0.6 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 10) + bp(rng.standard_normal(n), 200, 3000) * np.exp(-t * 40) * 0.5
        place(out, g * x, f2s(at) + 2)

    def ticks(at, n_ticks=10, g=0.03):
        for i in range(n_ticks):
            pop(at + i * 2.4, g, 2200)

    for f in efx['cuts']:
        swish(f)
    typ = efx['types']
    for f in efx['pops']:
        t = typ.get(str(f))
        if t == 'stamp':
            stamp(f)
        elif t == 'counter':
            ticks(f + 16)
        elif t == 'verdict':
            pass                       # carried by the music impact
        else:
            pop(f + 2)
    return reverb(out, 1.0, 0.15)


def ambience(script, total):
    N = f2s(total)
    amb = np.zeros(N)
    c = {q['cue_id']: q for q in script['cues']}
    for a, b in (('Q01', 'Q03'), ('Q06', 'Q11')):
        s, e = c[a]['in_frame'], c[b]['out_frame_exclusive']
        n = f2s(e) - f2s(s)
        x = lp(np.cumsum(rng.standard_normal(n)) * 0.002, 260)
        x = hp(x, 30) + hp(lp(rng.standard_normal(n), 6000), 2500) * 0.003
        fo = f2s(10)
        x[:fo] *= np.linspace(0, 1, fo); x[-fo:] *= np.linspace(1, 0, fo)
        place(amb, x, f2s(s))
    return amb


def narration(epdir, timing, total):
    na = np.zeros(f2s(total))
    for it in timing['items']:
        x, sr = sf.read(epdir / it['file'])
        assert sr == SR
        if x.ndim > 1:
            x = x.mean(1)
        place(na, x, f2s(it['start']))
    return na


def duck_curve(timing, total, depth_db=-11.0):
    N = f2s(total)
    g = np.zeros(N)
    for it in timing['items']:
        g[f2s(it['start']):f2s(it['end'])] = 1
    k = int(0.15 * SR)
    sm = np.convolve(g, np.ones(k) / k, mode='same')
    sm = np.maximum(sm, np.convolve(g, np.ones(int(0.5 * SR)) / int(0.5 * SR), mode='same'))
    sm = np.clip(sm * 1.5, 0, 1)
    return 10 ** (depth_db * sm / 20)


def master(raw, dst):
    p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(raw), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                        capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex('{'):p1.rindex('}') + 1])
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=summary")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', str(dst)], check=True)


def main():
    ep = pathlib.Path(sys.argv[1])
    script = json.load(open(ep / 'script.json'))
    timing = json.load(open(ep / 'timing.json'))
    efx = json.load(open(ep / 'edit_fx.json'))
    total = script['duration_frames']
    out = ep / 'audio'
    na = narration(ep, timing, total)
    mus = build_music(script, total) * duck_curve(timing, total)
    amb = ambience(script, total)
    fxs = build_fx(efx, total)
    stems = {'na': na, 'mus': mus, 'amb': amb, 'fx': fxs}
    for k, v in stems.items():
        sf.write(out / f'stem_{k}.wav', stereo(v, 0.0 if k == 'na' else 0.35, 0 if k == 'na' else 11).astype(np.float32), SR, subtype='FLOAT')
    mix = stereo(na, 0, 0) * 1.0 + stereo(mus, 0.35) * 1.0 + stereo(amb, 0.5) * 0.8 + stereo(fxs, 0.3) * 1.4
    sf.write(out / 'mix_raw.wav', mix.astype(np.float32), SR, subtype='FLOAT')
    master(out / 'mix_raw.wav', out / 'mix_master.wav')
    print('seconds', round(len(mix) / SR, 3), '→', out / 'mix_master.wav')


if __name__ == '__main__':
    main()
