#!/usr/bin/env python3
"""Audio for the reworked cut without re-synthesizing approved lines. usage (.venv): python build_audio_v3.py EPISODE_DIR
- SFX: the APPROVED earshot parts (audio/parts) placed per episode.json 'sfx' with the same processing as sfx_earshot.py (no new randomness)
- voice: approved takes for lines whose text did not change (audio/approved/narr_*.wav), new Sohee takes (audio/cand_pick/narr_<line>.wav) for the changed lines, each at beat.t0 + 0.15 s
- mix: same ducking / tanh recipe as narration.py, then the two-pass loudnorm of assemble.py -> audio/sfx_norm.wav; audio/narration.json for the gates"""
import sys, os, json, subprocess, numpy as np, soundfile as sf, soxr
E = sys.argv[1]; A = E + '/audio'; ep = json.load(open(E + '/episode.json')); SR = 48000; N = int(SR * ep['duration'])
parts = {}
for p in ep['sfx_parts']:
    x, sr = sf.read(f'{A}/parts/{p["id"]}.wav', always_2d=True); x = x.mean(1)
    if sr != SR: x = soxr.resample(x, sr, SR)
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(fr); g[fr < 120] *= 0.15; g[(fr >= 120) & (fr < 250)] *= 0.6; g[(fr >= 500) & (fr <= 3000)] *= p.get('mid_boost', 3.2)
    x = np.fft.irfft(X * g, len(x)); parts[p['id']] = (x * (p.get('norm', 0.8) / (np.abs(x).max() + 1e-9))).astype(np.float32)
mix = np.zeros(N, np.float32); bed = ep.get('sfx_bed')
if bed:
    b = parts[bed['part']]; b = np.tile(b, int(np.ceil(N / len(b))))[:N]; fade = int(0.5 * SR); b[:fade] *= np.linspace(0, 1, fade); b[-fade:] *= np.linspace(1, 0, fade); env = np.ones(N, np.float32) * bed['gain']
    for (t0, g0), (t1, g1) in zip(bed.get('curve', []), bed.get('curve', [])[1:]): i0, i1 = int(t0 * SR), min(N, int(t1 * SR)); env[i0:i1] = np.linspace(g0, g1, i1 - i0)
    if bed.get('curve'): env[int(bed['curve'][-1][0] * SR):] = bed['curve'][-1][1]
    mix += env * b
for e in ep['sfx']:
    x = parts[e['part']] * e.get('gain', 1.0); s = int(e['t'] * SR); m = min(len(x), N - s)
    if m > 0: mix[s:s + m] += x[:m]
mix = np.tanh(1.8 * mix) / np.tanh(1.8); pk = float(np.abs(mix).max()) or 1.0
if pk > 0.95: mix *= 0.95 / pk
sf.write(A + '/sfx_only.wav', np.stack([mix, np.concatenate([np.zeros(15, np.float32), mix[:-15]])], 1), SR)
sfx = mix; voice = np.zeros(N, np.float32); info = []
src = {0: 'approved/narr_0.wav', 1: 'approved/narr_1.wav', 5: 'approved/narr_6.wav'}
for k, ln in enumerate(ep['narration']):
    b = ep['beats'][ln['beat']]; f = f'{A}/' + src.get(k, f'cand_pick/narr_{k}.wav'); y, sr = sf.read(f, dtype='float32', always_2d=True); y = y.mean(1)
    if sr != SR: y = soxr.resample(y, sr, SR)
    s0 = int((b['t0'] + 0.15) * SR); e0 = min(N, s0 + len(y)); voice[s0:e0] = y[:e0 - s0]; sy = len([c for c in ln['text'] if '가' <= c <= '힣'])
    shutil_dst = f'{A}/narr_{k}.wav'; sf.write(shutil_dst, y, SR)
    info.append({'line': k, 'beat': ln['beat'], 'text': ln.get('spoken') or ln['text'], 'start': s0 / SR, 'end': e0 / SR, 'syll': sy, 'rate': round(sy / (len(y) / SR), 2), 'atempo': 1.0, 'file': f'narr_{k}.wav'})
json.dump(info, open(A + '/narration.json', 'w'), ensure_ascii=False, indent=1)
w = int(SR * 0.02); env = np.sqrt(np.convolve(voice ** 2, np.ones(w) / w, 'same')); g = (env > 0.01).astype(np.float32); g = np.convolve(g, np.ones(int(SR * .25)) / int(SR * .25), 'same')
out = sfx * (1 - 0.92 * np.clip(g, 0, 1)) + voice * 1.2; out = np.tanh(1.5 * out) / np.tanh(1.5) * 0.96; sf.write(A + '/sfx.wav', out.astype(np.float32), SR)
L = ep['lufs']; r = subprocess.run(['ffmpeg', '-hide_banner', '-i', A + '/sfx.wav', '-af', f'loudnorm=I={L}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', A + '/sfx.wav', '-af', f"loudnorm=I={L}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:linear=true,aresample=48000", A + '/sfx_norm.wav'], check=True)
print('audio ok', [(i['line'], i['start'], i['rate']) for i in info])
