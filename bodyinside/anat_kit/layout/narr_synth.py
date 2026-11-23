"""Worker (mlx venv): synthesize candidate spoken texts for one narration line, same processing as narration.py (trim, squeeze, atempo to ~6.4 syll/s, fit to the beat slot).
usage: python narr_synth.py EPISODE_DIR LINE CANDIDATES.json TAKES -> audio/cand/L<line>_c<i>_t<j>.wav + audio/cand/L<line>.json"""
import os, sys, json, re, subprocess
HERE = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/tts_bakeoff'); os.environ.update(HF_HOME=f'{HERE}/hf', HF_HUB_OFFLINE='1')
import numpy as np, soundfile as sf
from mlx_audio.tts.utils import load_model
E, LINE, CANDS, TAKES = sys.argv[1], int(sys.argv[2]), json.load(open(sys.argv[3])), int(sys.argv[4]); ep = json.load(open(E + '/episode.json')); A = E + '/audio'; os.makedirs(A + '/cand', exist_ok=True)
STYLE = "Warm, clear, brisk documentary narration. Natural Korean, steady, not dramatic."
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
ln = ep['narration'][LINE]; b = ep['beats'][ln['beat']]; slot = (b['t1'] - b['t0']) - 0.3; ssr = 48000; info = []
for ci, text in enumerate(CANDS):
    n = syl(text)
    for tj in range(TAKES):
        inst = STYLE if tj % 2 == 0 else STYLE + ' Speak quickly and briskly, about 7 syllables per second.'
        rs = list(m.generate_custom_voice(text=text, speaker='sohee', language='Korean', instruct=inst)); sr = rs[0].sample_rate
        x = np.concatenate([np.asarray(np.array(r.audio), np.float32).reshape(-1) for r in rs]); x = squeeze(trim(x, sr), sr)
        f = 6.4 / (n / (len(x) / sr)); f = min(1.45, max(0.95, f)); f = min(1.45, max(f, (len(x) / sr) / slot))
        tmp = f'{A}/cand/_t.wav'; sf.write(tmp, x, sr); out = f'{A}/cand/L{LINE}_c{ci}_t{tj}.wav'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-af', f'atempo={f:.4f},aresample={ssr}', out], check=True); y, _ = sf.read(out, dtype='float32'); y = y.reshape(-1)
        info.append({'cand': ci, 'take': tj, 'text': text, 'file': out, 'syll': n, 'rate': round(n / (len(y) / ssr), 2), 'atempo': round(f, 3), 'dur': round(len(y) / ssr, 3)}); print(info[-1], flush=True)
json.dump(info, open(f'{A}/cand/L{LINE}.json', 'w'), ensure_ascii=False, indent=1)
