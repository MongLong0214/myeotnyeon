#!/usr/bin/env python3
"""Re-synthesize chosen sentences N times; keep the take with the lowest ASR CER."""
import json, pathlib, re, sys, hashlib
import numpy as np, soundfile as sf, mlx_whisper
from scipy.signal import resample_poly
from supertonic import TTS
import tts as T
HERE = pathlib.Path(__file__).parent
ids = sys.argv[1].split(','); N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
idxf = HERE / 'audio/na/index.json'; meta = json.load(open(idxf))
script = {f"{c['cue_id']}_{i+1}": s for c in json.load(open(HERE / 'script_text.json'))['cues'] for i, s in enumerate(c['narration'])}
norm = lambda s: re.sub(r'[^가-힣0-9A-Za-z]', '', s)
def cer(a, b):
    a, b = norm(a), norm(b); d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, cb in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (ca != cb))
    return d[-1] / max(1, len(a))
tts = TTS(auto_download=True); style = tts.get_voice_style(voice_name=meta['voice'])
for sid in ids:
    text = script[sid]; t = T.tts_text(text); best = None
    for k in range(N):
        wav, _ = tts.synthesize(t, voice_style=style, lang='ko', speed=meta['speed'], total_steps=meta['steps'])
        w = T.trim(np.asarray(wav, dtype=np.float32).reshape(-1), 44100)
        w48 = resample_poly(w, 160, 147).astype(np.float32)
        tmp = HERE / f'audio/na/_tmp_{sid}_{k}.wav'; sf.write(tmp, w48, 48000, subtype='PCM_24')
        asr = mlx_whisper.transcribe(str(tmp), path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ko')['text'].strip()
        c = cer(text, asr); print(sid, k, round(c, 3), asr)
        if best is None or c < best[0]: best = (c, tmp, len(w48) / 48000, asr)
    f = HERE / f'audio/na/{sid}.wav'; best[1].replace(f)
    for x in (HERE / 'audio/na').glob(f'_tmp_{sid}_*.wav'): x.unlink()
    item = next((x for x in meta['items'] if x['id'] == sid), None)
    rec = dict(id=sid, cue=sid.split('_')[0], text=text, tts_text=t, file=str(f.relative_to(HERE)), dur=round(best[2], 3),
               sha256=hashlib.sha256(f.read_bytes()).hexdigest(), best_of=N, asr=best[3], cer=round(best[0], 3))
    if item: meta['items'][meta['items'].index(item)] = rec
    else: meta['items'].append(rec)
    print('KEEP', sid, rec['cer'], rec['dur'])
json.dump(meta, open(idxf, 'w'), ensure_ascii=False, indent=1)
