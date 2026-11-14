"""ja B3 narration takes: VOICEVOX engine 0.26.1, local only (research/tts_voicevox/macos-arm64/run --port 50121).
Voice: 冥鳴ひまり ノーマル (style 14); credit 「VOICEVOX:冥鳴ひまり」 (terms: research/tts_voicevox/policy_8eaad775-*.md).
Spec keys: "vv_style" (default 14), "vv_speeds" (default [1.15, 1.25, 1.35]); per line optional "vv_text" (reading override).
usage: synth_voicevox.py <qid> [line ids...] -> raw/<qid>/<id>_v<speed>_t1.wav (24 kHz, edges trimmed)"""
import sys, json, io, urllib.request, urllib.parse
from pathlib import Path
import numpy as np, soundfile as sf
D = Path(__file__).resolve().parent; B = 'http://127.0.0.1:50121'
def trim(x, sr, db=-45, pad=.03):
    w = int(sr * .01); n = len(x) // w; r = 20 * np.log10(np.sqrt(np.mean(x[:n*w].reshape(-1, w) ** 2, 1)) + 1e-9)
    on = np.where(r > r.max() + db)[0]; a, b = on[0] * w, (on[-1] + 1) * w
    return x[max(0, a - int(pad * sr)):min(len(x), b + int(pad * sr))]
def synth(style, speed, text):
    q = json.load(urllib.request.urlopen(urllib.request.Request(f'{B}/audio_query?speaker={style}&text={urllib.parse.quote(text)}', method='POST')))
    q.update(speedScale=speed, prePhonemeLength=.05, postPhonemeLength=.05, outputSamplingRate=24000)
    w = urllib.request.urlopen(urllib.request.Request(f'{B}/synthesis?speaker={style}', data=json.dumps(q).encode(), headers={'Content-Type': 'application/json'})).read()
    x, sr = sf.read(io.BytesIO(w), dtype='float32'); return (x if x.ndim == 1 else x.mean(1)), sr
if __name__ == '__main__':
    q = sys.argv[1]; ids = set(sys.argv[2:]); spec = json.loads((D / 'specs' / f'{q}.json').read_text())
    R = D / 'raw' / q; R.mkdir(parents=True, exist_ok=True)
    for s in spec['lines']:
        if ids and s['id'] not in ids: continue
        for sp in s.get('vv_speeds', spec.get('vv_speeds', [1.15, 1.25, 1.35])):
            x, sr = synth(spec.get('vv_style', 14), sp, s.get('vv_text', s['tts'])); x = trim(x, sr)
            sf.write(R / f"{s['id']}_v{sp:.2f}_t1.wav", x, sr); print('SYN', s['id'], sp, round(len(x) / sr, 2), flush=True)
