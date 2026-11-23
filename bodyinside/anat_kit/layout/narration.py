"""Korean narration (Qwen3-TTS 12Hz-1.7B CustomVoice, speaker Sohee, local MLX) mixed over the SFX with ducking. usage (mlx venv): python narration.py EPISODE_DIR
episode.json "narration": [{"beat": i, "text": ...}]. Per line: synth -> trim -> pauses > 0.18 s squeezed to 0.18 s -> atempo to ~6.4 syll/s (clamped 0.95-1.45, raised to fit the beat) ->
placed at beat.t0 + 0.15 s. Writes audio/narr_<i>.wav, audio/narration.json (start/end per line), and replaces audio/sfx.wav by the mix (the untouched SFX stays in audio/sfx_only.wav)."""
import os, sys, json, re, shutil, subprocess
HERE = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/tts_bakeoff'); os.environ.update(HF_HOME=f'{HERE}/hf', HF_HUB_OFFLINE='1')
import numpy as np, soundfile as sf
from mlx_audio.tts.utils import load_model
E = sys.argv[1]; ep = json.load(open(E + '/episode.json')); A = E + '/audio'
STYLE = "Warm, clear, brisk documentary narration. Natural Korean, steady, not dramatic."
LEXICON = {'C자': '씨짜', 'S자': '에스짜', '하중': '하-중', '눌린': '눌-린', '신경 쪽으로': '신경, 쪽으로', '휠 수도': '휠 쑤도'}
def spoken(t):
    for a, b in LEXICON.items(): t = t.replace(a, b)
    return t
def syl(t): return len(re.sub('[^가-힣]', '', t))
def trim(x, sr, db=-41):
    w = int(sr * .005); n = len(x) // w; r = np.sqrt(np.mean(x[:n * w].reshape(-1, w) ** 2, 1)); ix = np.where(r > 10 ** (db / 20))[0]
    return x[max(0, (ix[0] - 2) * w):(ix[-1] + 3) * w] if len(ix) else x
def squeeze(x, sr, keep=.10, db=-28):
    w = int(sr * .01); n = len(x) // w; r = 20 * np.log10(np.sqrt(np.mean(x[:n * w].reshape(-1, w) ** 2, 1)) + 1e-9); q = r < r.max() + db; out = []; i = 0
    while i < n:
        j = i
        while j < n and q[j] == q[i]: j += 1
        seg = x[i * w:j * w]
        if q[i] and (j - i) * w > keep * sr and 0 < i and j < n: h = int(keep * sr / 2); seg = np.r_[seg[:h], seg[-h:]]
        out.append(seg); i = j
    return np.concatenate(out + [x[n * w:]])
m = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit'); m.generate_custom_voice(text='워밍업입니다.', speaker='sohee', language='Korean', instruct=STYLE).__next__()
if not os.path.exists(A + '/sfx_only.wav') or '--keep-sfx' not in sys.argv: shutil.copyfile(A + '/sfx.wav', A + '/sfx_only.wav')
sfx, ssr = sf.read(A + '/sfx_only.wav', dtype='float32', always_2d=True); sfx = sfx.mean(1); voice = np.zeros(len(sfx), np.float32); info = []
for k, ln in enumerate(ep['narration']):
    b = ep['beats'][ln['beat']]; ln = dict(ln, text=spoken(ln['text'])); n = syl(ln['text'])
    start = b['t0'] + 0.15 + ln.get('dt', 0.0)
    slot = b['t1'] - start - 0.15
    if start < b['t0'] or slot <= 0: raise ValueError(f'invalid speech offset for beat {ln["beat"]}')
    for attempt in range(4):   # a take that needs more than 1.45x tempo is re-synthesised with a faster instruction (memory: never stretch past 1.4x)
        rs = list(m.generate_custom_voice(text=ln['text'], speaker='sohee', language='Korean', instruct=STYLE if attempt == 0 else STYLE + ' Speak quickly and briskly, about 7 syllables per second.')); sr = rs[0].sample_rate
        x = np.concatenate([np.asarray(np.array(r.audio), np.float32).reshape(-1) for r in rs]); x = squeeze(trim(x, sr), sr)
        f = 6.4 / (n / (len(x) / sr))
        if f <= 1.45: break
    f = min(1.45, max(0.95, f)); f = min(1.45, max(f, (len(x) / sr) / slot))
    tmp = f'{A}/_n{k}.wav'; sf.write(tmp, x, sr); out = f'{A}/narr_{k}.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-af', f'atempo={f:.4f},aresample={ssr}', out], check=True); y, _ = sf.read(out, dtype='float32'); y = y.reshape(-1)
    s0 = int(start * ssr); e0 = min(len(voice), s0 + len(y)); voice[s0:e0] = y[:e0 - s0]
    info.append({'line': k, 'beat': ln['beat'], 'text': ln['text'], 'start': s0 / ssr, 'end': e0 / ssr, 'syll': n, 'rate': round(n / (len(y) / ssr), 2), 'atempo': round(f, 3), 'file': f'narr_{k}.wav'})
    print(info[-1], flush=True)
json.dump(info, open(A + '/narration.json', 'w'), ensure_ascii=False, indent=1)
w = int(ssr * 0.02); env = np.sqrt(np.convolve(voice ** 2, np.ones(w) / w, 'same')); g = (env > 0.01).astype(np.float32); g = np.convolve(g, np.ones(int(ssr * .25)) / int(ssr * .25), 'same')   # duck: voice present -> SFX -16 dB (owner round 13: SFX masked the speech at 4-5.5 s, 12.5-14 s, 25-27 s)
mix = sfx * (1 - 0.84 * np.clip(g, 0, 1)) + voice * 1.2; mix = np.tanh(1.5 * mix) / np.tanh(1.5) * 0.96
sf.write(A + '/sfx.wav', mix.astype(np.float32), ssr); print('narration mixed', len(info), 'lines')
sf.write(A + '/sfx_ducked.wav', (sfx * (1 - 0.84 * np.clip(g, 0, 1))).astype(np.float32), ssr)   # stem for gates/media_checks.narration_snr
