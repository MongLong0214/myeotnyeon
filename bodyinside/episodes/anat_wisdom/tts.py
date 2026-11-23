"""Narration: Qwen3-TTS 12Hz-1.7B CustomVoice 6bit, speaker sohee (same engine as factory/make_short.py). usage: tts.py [take] [ids...]"""
import os, sys, json
BF=(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/tts_bakeoff')
os.environ.update(HF_HOME=f'{BF}/hf'); os.environ.setdefault('HF_HUB_OFFLINE','1')
import numpy as np, soundfile as sf
from mlx_audio.tts.utils import load_model
HERE=os.path.dirname(os.path.abspath(__file__))
LINES=json.load(open(f'{HERE}/lines.json'))
STYLE="Calm, warm Korean medical documentary narration. Clear, measured, confident; crisp diction; gentle pace."
take=int(sys.argv[1]) if len(sys.argv)>1 else 1
ids=sys.argv[2:] or [l['id'] for l in LINES]
m=load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit')
import mlx.core as mx
mx.random.seed(1000+take)
def arr(r): return np.asarray(np.array(r.audio),np.float32).reshape(-1)
for l in LINES:
    if l['id'] not in ids: continue
    rs=list(m.generate_custom_voice(text=l['tts'],speaker='sohee',language='Korean',instruct=STYLE))
    x=np.concatenate([arr(r) for r in rs]); sr=rs[0].sample_rate
    # trim silence
    a=np.abs(x); th=0.01*a.max(); nz=np.where(a>th)[0]
    x=x[max(0,nz[0]-int(0.03*sr)):nz[-1]+int(0.08*sr)]
    sf.write(f'{HERE}/audio/{l["id"]}_t{take}.wav',x,sr); print(l['id'],take,round(len(x)/sr,2),flush=True)
