import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
import numpy as np
from supertonic import TTS

raw = Raw('supertonic3')
tts = TTS(auto_download=False)
SPEEDS = [1.0, 1.1, 1.2, 1.35]
for v in [f'{g}{i}' for g in 'MF' for i in range(1, 6)]:
    style = tts.get_voice_style(voice_name=v)
    for sp in SPEEDS:
        st = f'sp{int(round(sp*100))}'
        for ln in LINES:
            if raw.have(v, st, ln['id']):
                continue
            t = timer()
            wav, _ = tts.synthesize(ln['tts'], voice_style=style, lang='ko', speed=sp, total_steps=16)
            raw.save(v, st, ln['id'], np.asarray(wav).reshape(-1), tts.sample_rate if hasattr(tts, 'sample_rate') else 44100,
                     params=dict(speed=sp, total_steps=16, lang='ko'), gen_s=t(), text=ln['tts'])
