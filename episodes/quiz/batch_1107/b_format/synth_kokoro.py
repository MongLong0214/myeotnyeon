"""en/ja B3 narration takes: Kokoro-82M (Apache-2.0), local only (research/tts_kokoro, HF cache offline). Spec keys:
"voice" (e.g. af_heart, jf_alpha), "kokoro_speeds" (default [1.1, 1.2]); per line optional "speeds".
usage (Kokoro venv): synth_kokoro.py <qid> [line ids...] -> raw/<qid>/<id>_k<speed>_t1.wav (24 kHz, edges trimmed)"""
import os, sys, json
K = '/Users/isaac/projects/verdict-kr/work/research/tts_kokoro'
os.environ.update(HF_HOME=f'{K}/hf', HF_HUB_OFFLINE='1')
sys.path.insert(0, K)
from pathlib import Path
import numpy as np, soundfile as sf
from gen import synth
D = Path(__file__).resolve().parent
def trim(x, sr, db=-45, pad=.03):
    w = int(sr * .01); n = len(x) // w; r = 20 * np.log10(np.sqrt(np.mean(x[:n*w].reshape(-1, w) ** 2, 1)) + 1e-9)
    on = np.where(r > r.max() + db)[0]; a, b = on[0] * w, (on[-1] + 1) * w
    return x[max(0, a - int(pad * sr)):min(len(x), b + int(pad * sr))]
if __name__ == '__main__':
    q = sys.argv[1]; ids = set(sys.argv[2:])
    spec = json.loads((D / 'specs' / f'{q}.json').read_text()); lang = {'en': 'a', 'ja': 'j'}[spec['locale']]
    R = D / 'raw' / q; R.mkdir(parents=True, exist_ok=True)
    for s in spec['lines']:
        if ids and s['id'] not in ids: continue
        for sp in s.get('speeds', spec.get('kokoro_speeds', [1.1, 1.2])):
            x, sr = synth(lang, spec['voice'], sp, s['tts']); x = trim(x, sr)
            sf.write(R / f"{s['id']}_k{sp:.2f}_t1.wav", x, sr); print('SYN', s['id'], sp, round(len(x) / sr, 2), flush=True)
