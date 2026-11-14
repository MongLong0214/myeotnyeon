import os, sys, time, json
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import SPOKEN, trim
from melo.api import TTS
m = TTS(language='KR', device='mps' if len(sys.argv) < 2 else sys.argv[1]); spk = m.hps.data.spk2id['KR']; SR = m.hps.data.sampling_rate
m.tts_to_file('워밍업 문장입니다.', spk, 'raw/_w.wav', speed=1.1, quiet=True)
meta = []
for i, t in enumerate(SPOKEN):
    t0 = time.time(); a = m.tts_to_file(t, spk, None, speed=1.1, quiet=True); dt = time.time() - t0
    sf.write(f'raw/melotts_KR_{i}.wav', trim(np.asarray(a, np.float32), SR), SR); meta.append(dict(line=i, synth_s=dt, sr=SR))
json.dump(meta, open('raw/melotts_KR.json', 'w')); print('ok', meta)
