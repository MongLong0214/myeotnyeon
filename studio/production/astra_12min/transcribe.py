import os,json
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
import mlx_whisper
P=Path('production/astra_12min');R=P.parents[1]
model=next(Path('$HOME/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').iterdir())
result=[]
for r in json.loads((P/'render_verification.json').read_text()):
 t=mlx_whisper.transcribe(r['video'],path_or_hf_repo=str(model),language='ko',verbose=False)
 result.append(dict(video=r['video'],sha256=r['sha256'],asr_text=t['text'],segments=t['segments'],note='ASR only; not independent listening or visual quality PASS'))
 (P/'representatives_asr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(r['video'],t['text'],flush=True)
