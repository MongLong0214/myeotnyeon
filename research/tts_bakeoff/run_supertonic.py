import os, sys, time, json; os.environ.update(HF_HUB_OFFLINE='1')
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__)); from common import SPOKEN, trim
from supertonic import TTS
tts = TTS(model_dir='/Users/isaac/.cache/supertonic3', auto_download=False, intra_op_num_threads=2, inter_op_num_threads=1)
voice = sys.argv[1] if len(sys.argv) > 1 else 'M1'
st = tts.get_voice_style(voice); SR = tts.sample_rate if hasattr(tts, 'sample_rate') else 44100
tts.synthesize('워밍업', voice_style=st, lang='ko', speed=1.05, total_steps=16)
meta = []
for i, t in enumerate(SPOKEN):
    t0 = time.time()
    a, _ = tts.synthesize(t, voice_style=st, lang='ko', speed=1.05, total_steps=16, silence_duration=.08, max_chunk_length=250)
    dt = time.time() - t0; x = trim(np.asarray(a, np.float32).reshape(-1), SR)
    sf.write(f'raw/supertonic3_{voice}_{i}.wav', x, SR); meta.append(dict(line=i, synth_s=dt, sr=SR))
json.dump(meta, open(f'raw/supertonic3_{voice}.json', 'w'))
print('ok', SR, meta)
