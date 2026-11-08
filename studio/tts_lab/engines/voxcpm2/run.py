import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
from personas import PERSONAS
import numpy as np, mlx.core as mx
from mlx_audio.tts.utils import load

REPO = 'mlx-community/VoxCPM2-bf16'
model = load(REPO)
raw = Raw('voxcpm2')
for v, (timbre, neu, com) in PERSONAS.items():
    for style, d in (('neutral', neu), ('comic', com)):
        ins = f'{timbre} {d}'
        for ln in LINES:
            if raw.have(v, style, ln['id']):
                continue
            mx.random.seed(1000 + ln['id'])
            t = timer()
            res = list(model.generate(text=ln['tts'], instruct=ins))
            wav = np.concatenate([np.array(r.audio, dtype=np.float32).reshape(-1) for r in res])
            raw.save(v, style, ln['id'], wav, res[0].sample_rate, params=dict(model=REPO, instruct=ins, seed='1000+line',
                     inference_timesteps=10, cfg_value=2.0), gen_s=t(), text=ln['tts'])
