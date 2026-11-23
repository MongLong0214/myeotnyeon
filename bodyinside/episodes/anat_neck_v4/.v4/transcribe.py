import os
import sys
from pathlib import Path
import mlx_whisper
os.environ['HF_HUB_OFFLINE'] = '1'
model = str(next(Path.home().joinpath('.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent)
for file in sys.argv[1:]:
 result = mlx_whisper.transcribe(file, path_or_hf_repo=model, language='ko', temperature=0, condition_on_previous_text=False, word_timestamps=True, verbose=None)
 print(file,result['text'])
 print([(round(w['start'],2),round(w['end'],2),w['word']) for s in result['segments'] for w in s['words']])
