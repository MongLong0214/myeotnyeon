from pathlib import Path
import sys,math,json,re
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
D=Path(__file__).parent;W=D.parents[3];sys.path.insert(0,str(W/'factory'))
from fresh import trim
from supertonic import TTS
import mlx_whisper
tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);v=tts.get_voice_style('M1');model=next((Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
rows=[('07','일심 선고. 징역 일 년, 집행유예 이 년, 사회봉사 백팔십 시간.',['징역','1년','2년','180']),('04','반성, 합의, 처벌을 원치 않는 점도 참작했습니다.',['반성','합의','원치'])]
for stem,text,wanted in rows:
 for take,speed in enumerate([1.28,1.22,1.16,1.10]):
  raw,_=tts.synthesize(text,voice_style=v,lang='ko',speed=speed,total_steps=24,silence_duration=.18);x=resample_poly(trim(np.asarray(raw,np.float32).reshape(-1),44100),160,147).astype(np.float32)
  f=W/f'upload/pkg/q005_std/audio/{stem}_take{take}.wav';sf.write(f,x,48000,subtype='PCM_24')
  a=mlx_whisper.transcribe(str(f),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0)
  print(stem,take,len(x)/48000,len(re.findall('[가-힣]',text))/(len(x)/48000),a['text'],flush=True)
  if all(w in a['text'] for w in wanted):
   out=f.parent/f'{stem}.wav';sf.write(out,x,48000,subtype='PCM_24');out.with_suffix('.text').write_text(text);print('SELECTED',stem,take,flush=True);break
 else:raise RuntimeError('No clear take for '+stem)
