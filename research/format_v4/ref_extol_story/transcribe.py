import os,json,time,hashlib
from pathlib import Path
os.environ["HF_HUB_OFFLINE"]="1"
os.environ["HF_HUB_DISABLE_TELEMETRY"]="1"
import mlx_whisper
r=Path(__file__).resolve().parent
model=next(p for p in Path("/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots").iterdir() if (p/"config.json").exists())
for label,path in [("reference",r/"reference.wav"),("ours_fast",r.parents[2]/"episodes/v4/n18/out/n18_v4_type2_fast_preview_lowres.mp4")]:
 if label=="ours_fast": path=Path("episodes/v4/n18/out/n18_v4_type2_fast_preview_lowres.mp4").resolve()
 t=time.time()
 result=mlx_whisper.transcribe(str(path),path_or_hf_repo=str(model),language="ko",word_timestamps=True,verbose=False,condition_on_previous_text=True)
 (r/(label+"_transcript.json")).write_text(json.dumps(result,ensure_ascii=False,indent=2))
 (r/(label+"_transcript.txt")).write_text("\n".join(f"{s['start']:.2f}–{s['end']:.2f} {s['text'].strip()}" for s in result["segments"]))
 print(label,"done",round(time.time()-t,1),flush=True)
(r/"transcription_method.json").write_text(json.dumps({"engine":"mlx_whisper","model":"whisper-large-v3-turbo","local_model":str(model),"language":"ko","word_timestamps":True,"offline":True},indent=2))
