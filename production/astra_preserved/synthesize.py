"""Offline-only synthesis; no downloads or paid APIs. Native speaking rate, no stretch."""
import os,json,sys,hashlib
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
import numpy as np
import soundfile as sf
from supertonic import TTS
ROOT=Path('/Users/isaac/projects/verdict-kr/work'); P=ROOT/'production/astra_12min'
tts=TTS(model_dir='/Users/isaac/.cache/supertonic3',auto_download=False,intra_op_num_threads=2,inter_op_num_threads=1)
style=tts.get_voice_style(voice_name='M1'); sr=tts.sample_rate
source=Path(sys.argv[1]) if len(sys.argv)>1 else P/'representatives.json'
for name,clip in json.loads(source.read_text()).items():
 out=ROOT/'episodes'/clip['episode']/'astra_12min'; (out/'audio').mkdir(exist_ok=True,parents=True)
 samples=[]; cursor=0; cues=[]
 for item in clip['items']:
  path=out/'audio'/f"{item['id']}.wav"
  if path.exists(): a,s=sf.read(path); assert s==sr
  else:
   a,d=tts.synthesize(item['text'],voice_style=style,lang='ko',speed=clip.get('speed',1.1),total_steps=clip.get('steps',16))
   a=np.asarray(a).reshape(-1)
   # Remove model trailing allocation only; no alteration of speech tempo.
   nz=np.flatnonzero(abs(a)>.001)
   if len(nz): a=a[max(0,nz[0]-int(.05*sr)):min(len(a),nz[-1]+int(.12*sr))]
   sf.write(path,a,sr)
  cue=dict(item,start=cursor/sr,end=(cursor+len(a))/sr,audio=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  cues.append(cue); samples.append(a); cursor+=len(a)
  print(name,item['id'],round(len(a)/sr,3),flush=True)
  # Brief sentence boundary only, never duration padding.
  if item!=clip['items'][-1]: gap=np.zeros(round(sr*.17));samples.append(gap);cursor+=len(gap)
  (out/f'{name}_cues.json').write_text(json.dumps(dict(clip,cues=cues,duration=cursor/sr,engine='local Supertonic 3 M1',speed=clip.get('speed',1.1),sample_rate=sr,offline=True),ensure_ascii=False,indent=2))
 sf.write(out/f'{name}.wav',np.concatenate(samples),sr)
 print('DONE',name,cursor/sr,flush=True)
