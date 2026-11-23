"""ALL SFX from earshot (MIT, github.com/Leonxlnx/earshot 7a7f7c5; CPU) -- replaces the numpy synth. usage: python sfx_earshot.py EPISODE_DIR -> audio/sfx.wav + audio/sfx_report.json
episode.json: "sfx_parts": [{"id","want","listen","alts":[...],"gain","dur"?}], "sfx": [{"part": id, "t": seconds, "gain"?}], "sfx_bed": {"part": id, "gain": g}  (looped under the whole video)
Each part is made with `earshot make "<want>"`, then checked with `earshot match <wav> "<listen>"` (z >= 2.0); on failure the next entry of "alts" is tried. The report lists every part, the request that passed and its z."""
import sys, os, json, subprocess, re, hashlib
import numpy as np, soundfile as sf, soxr
E = sys.argv[1]; ep = json.load(open(E + '/episode.json')); SR = 48000; N = int(SR * ep['duration']); V = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../.venv/bin/earshot')
os.makedirs(E + '/audio/parts', exist_ok=True); rep = {}
def make(pid, want, dur=None):
    out = f'{E}/audio/parts/{pid}.wav'; cmd = [V, 'make', want, '-o', out] + (['--dur', str(dur)] if dur else [])
    subprocess.run(cmd, capture_output=True, text=True); return out
def listen(path, q):
    r = subprocess.run([V, 'match', path, q, '--json'], capture_output=True, text=True)
    try: j = json.loads(r.stdout[r.stdout.index('{'):r.stdout.rindex('}') + 1]); return float(j['z']), j.get('verdict')
    except Exception: return -9.0, 'error'
parts = {}
for p in ep['sfx_parts']:
    tried = []
    for want in [p['want']] + p.get('alts', []):
        path = make(p['id'], want, p.get('dur')); z, v = listen(path, p.get('listen', want)); tried.append({'want': want, 'z': round(z, 2), 'verdict': v})
        if z >= 2.0: break
    rep[p['id']] = {'used': tried[-1]['want'], 'z': tried[-1]['z'], 'verdict': tried[-1]['verdict'], 'tried': tried, 'pass': tried[-1]['z'] >= 2.0}
    x, sr = sf.read(f'{E}/audio/parts/{p["id"]}.wav', always_2d=True); x = x.mean(1)
    if sr != SR: x = soxr.resample(x, sr, SR)
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(fr)
    g[fr < 120] *= 0.15; g[(fr >= 120) & (fr < 250)] *= 0.6; g[(fr >= 500) & (fr <= 3000)] *= p.get('mid_boost', 3.2)   # phones: cut the sub-bass, lift 500 Hz-3 kHz
    x = np.fft.irfft(X * g, len(x)); parts[p['id']] = (x * (p.get('norm', 0.8) / (np.abs(x).max() + 1e-9))).astype(np.float32)
mix = np.zeros(N, np.float32)
bed = ep.get('sfx_bed')
if bed:
    b = parts[bed['part']]; reps = int(np.ceil(N / len(b))); b = np.tile(b, reps)[:N]; fade = int(0.5 * SR); b[:fade] *= np.linspace(0, 1, fade); b[-fade:] *= np.linspace(1, 0, fade); env = np.ones(N, np.float32) * bed['gain']
    for (t0, g0), (t1, g1) in zip(bed.get('curve', []), bed.get('curve', [])[1:]): i0, i1 = int(t0 * SR), min(N, int(t1 * SR)); env[i0:i1] = np.linspace(g0, g1, i1 - i0)
    if bed.get('curve'): env[int(bed['curve'][-1][0] * SR):] = bed['curve'][-1][1]
    mix += env * b
for e in ep['sfx']:
    x = parts[e['part']] * e.get('gain', 1.0); s = int(e['t'] * SR); m = min(len(x), N - s)
    if m > 0: mix[s:s + m] += x[:m]
mix = np.tanh(1.8 * mix) / np.tanh(1.8)   # soft limiter: tames transient peaks so loudnorm can reach -14 LUFS with true peak <= -1.5
pk = float(np.abs(mix).max()) or 1.0
if pk > 0.95: mix *= 0.95 / pk
sf.write(E + '/audio/sfx.wav', np.stack([mix, np.concatenate([np.zeros(15, np.float32), mix[:-15]])], 1), SR)
json.dump(rep, open(E + '/audio/sfx_report.json', 'w'), indent=1, ensure_ascii=False); print('sfx ok', {k: (v['z'], v['pass']) for k, v in rep.items()})
