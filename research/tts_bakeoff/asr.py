"""Local Whisper (mlx large-v3-turbo) on every raw line. Runs in the project .venv; writes raw/asr.json."""
import os, sys, json, glob; os.environ.update(HF_HUB_OFFLINE='1')
from pathlib import Path
import mlx_whisper
M = str(next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent)
HERE = os.path.dirname(os.path.abspath(__file__)); out_f = f'{HERE}/raw/asr.json'
out = json.load(open(out_f)) if os.path.exists(out_f) else {}
for f in sorted(glob.glob(f'{HERE}/raw/*_[0-9].wav')):
    k = os.path.basename(f)[:-4]
    if k in out and '--force' not in sys.argv: continue
    out[k] = mlx_whisper.transcribe(f, path_or_hf_repo=M, language='ko', temperature=0, condition_on_previous_text=False, verbose=None)['text'].strip()
    print(k, out[k], flush=True)
json.dump(out, open(out_f, 'w'), ensure_ascii=False, indent=1)
