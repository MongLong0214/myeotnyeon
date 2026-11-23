import os
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

stage = Path(__file__).resolve().parent
cache = stage.parents[2] / 'research/tts_bakeoff/hf'
os.environ.update(HF_HOME=str(cache), HF_HUB_OFFLINE='1')
# Reuse the production narrator's trim and pause handling without invoking its CLI.
source = (stage.parents[2] / 'anat_kit/layout/narr_synth.py').read_text()
helpers = source[source.index('STYLE = '):source.index('m = load_model')]
exec(helpers)
model = load_model(str(next(cache.glob('hub/models--mlx-community--Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit/snapshots/*'))))
lines = json.loads((stage / 'lines.json').read_text())
for i in (1, 5):
    target = stage / f'audio/narr_{i}.wav'
    if target.exists():
        continue
    spoken = lines[i][1]
    takes = list(model.generate_custom_voice(text=spoken, speaker='sohee', language='Korean', instruct=STYLE))
    sr = takes[0].sample_rate
    x = squeeze(trim(np.concatenate([np.asarray(t.audio).astype('float32').reshape(-1) for t in takes]), sr), sr)
    factor = min(1.4, max(.95, (len(x) / sr) * 6.55 / syl(spoken)))
    temp = stage / 'audio/raw.wav'
    sf.write(temp, x, sr)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(temp),
                    '-af', f'atempo={factor:.4f},aresample=48000', str(target)], check=True)
    print(i, spoken, round(sf.info(target).duration, 2), flush=True)
