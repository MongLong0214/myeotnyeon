"""Fresh local M1 synthesis. Sentence pauses are audio, not guessed edit gaps."""
from pathlib import Path
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',PYTHONDONTWRITEBYTECODE='1')
import json,re,sys,subprocess,time
import numpy as np
import soundfile as sf
W=Path(__file__).resolve().parents[5]
E=W/'episodes/v4/n18/cartoon_v6'
A=E/'audio/takes'
SR=48000
PACE=7.08

def sino(v):
 n=int(v)
 if n==0:return '영'
 if n>=10000:
  q,r=divmod(n,10000);return (sino(q) if q>1 else '')+'만'+(sino(r) if r else '')
 out=''
 for base,unit in [(1000,'천'),(100,'백'),(10,'십')]:
  q,n=divmod(n,base)
  if q:out+=('' if q==1 else '일이삼사오육칠팔구'[q-1])+unit
 return out+('일이삼사오육칠팔구'[n-1] if n else '')

def spoken(s):
 s=s.replace('6명','여섯 명').replace('251명','이백오십일 명')
 s=re.sub(r'(\d+)월',lambda m:('유' if m[1]=='6' else '시' if m[1]=='10' else sino(m[1]))+'월',s)
 return re.sub(r'\d+',lambda m:sino(m[0]),s)

def norm(s):
 s=re.sub(r'\s+','',spoken(re.sub(r'\s+','',s))).replace('육월','유월')
 for a,b in [('한','일'),('두','이'),('세','삼'),('네','사'),('다섯','오'),('여섯','육'),('마흔','사십')]:
  s=re.sub(a+r'(?=바퀴|명|사람|개|시간|권|차례)',b,s)
 return re.sub('[^가-힣]','',s)

def distance(a,b):
 a,b=norm(a),norm(b);d=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  prev=d[:];d[0]=i
  for j,cb in enumerate(b,1):d[j]=min(prev[j]+1,d[j-1]+1,prev[j-1]+(ca!=cb))
 return d[-1],len(a)

def script():
 rows=[]
 for l in (E/'script_v2.md').read_text().splitlines():
  if not re.match(r'\| N\d',l):continue
  p=[x.strip() for x in l.split('|')]
  for k,t in enumerate(re.findall(r'[^.!?]+[.!?]?',p[2])):
   t=t.strip()
   if t:rows.append(dict(id=f'{p[1]}_{k+1:02}',narrationId=p[1],text=t,tts=spoken(t),facts=p[3].split(','),beat=p[5]))
 return rows

def trim(w,sr,max_s=.105):
 hop=round(sr*.005);rms=np.array([np.sqrt(np.mean(w[i:i+hop]**2)) for i in range(0,len(w),hop)])
 quiet=rms<.0025;changes=np.diff(np.r_[False,quiet,False].astype(int));keep=np.ones(len(w),bool)
 for a,b in zip(np.where(changes==1)[0],np.where(changes==-1)[0]):
  lo=a*hop;hi=min(len(w),b*hop)
  if hi-lo>sr*max_s:keep[lo+round(sr*max_s/2):hi-round(sr*max_s/2)]=False
 w=w[keep];active=np.where(np.abs(w)>.004)[0]
 return w[max(0,active[0]-round(sr*.008)):min(len(w),active[-1]+round(sr*.008))] if len(active) else w

def synth(ids=None):
 from supertonic import TTS
 tts=TTS(auto_download=False,intra_op_num_threads=3,inter_op_num_threads=1)
 style=tts.get_voice_style(voice_name='M1')
 for r in script():
  if ids and r['id'] not in ids:continue
  raw=A/(r['id']+'_native.wav');dest=A/(r['id']+'.wav')
  if dest.exists() and not ids:continue
  wav,_=tts.synthesize(r['tts'],voice_style=style,lang='ko',speed=1.05,total_steps=20,silence_duration=.06)
  w=trim(np.asarray(wav,dtype=np.float32).reshape(-1),44100)
  sf.write(raw,w,44100,subtype='PCM_24')
  syl=len(re.findall('[가-힣]',r['tts']));target=syl/PACE
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={len(w)/44100/target:.8f}','-ar',str(SR),str(dest)],check=True)
  w,_=sf.read(dest);w=trim(w,SR,.12)
  # A second small tempo fit preserves the target after silence compression.
  sf.write(raw,w,SR,subtype='PCM_24')
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={len(w)/SR/target:.8f}','-ar',str(SR),str(dest)],check=True)
  w,_=sf.read(dest);w*=.76/max(.001,np.max(np.abs(w)));sf.write(dest,w,SR,subtype='PCM_24')
  print(r['id'],r['tts'],round(len(w)/SR,3),flush=True)
 assemble()

def assemble():
 waves=[];pos=0;items=[]
 for r in script():
  w,sr=sf.read(A/(r['id']+'.wav'));assert sr==SR
  r.update(start=pos/SR,end=(pos+len(w))/SR,duration=len(w)/SR,syllables=len(re.findall('[가-힣]',r['tts'])))
  items.append(r);waves.extend([w,np.zeros(round(SR*.235))]);pos+=len(w)+round(SR*.235)
 sf.write(E/'audio/narration.wav',np.concatenate(waves),SR,subtype='PCM_24')
 meta=dict(voice='M1',model='Supertone/supertonic-3',native_speed=1.05,target_syl_s=PACE,sentence_gap_s=.235,duration=pos/SR,syllables=sum(r['syllables'] for r in items),items=items)
 (E/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 print('TOTAL',meta['duration'],'RATE',meta['syllables']/sum(r['duration'] for r in items),flush=True)

def asr(ids=None):
 import mlx_whisper
 dest=E/'asr_takes.json';old=json.loads(dest.read_text()) if dest.exists() else {'items':[]};prior={r['id']:r for r in old['items']};results=[];start=time.time()
 for row in script():
  path=A/(row['id']+'.wav')
  if not path.exists():break
  if row['id'] in prior and prior[row['id']].get('mtime')==path.stat().st_mtime:
   rec=prior[row['id']];err,n=distance(row['tts'],rec['asr']);rec.update(errors=err,characters=n,match=1-err/n);results.append(rec);continue
  r=mlx_whisper.transcribe(str(path),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='ko',condition_on_previous_text=False,temperature=0,verbose=False,word_timestamps=True)
  err,n=distance(row['tts'],r['text'])
  results.append(dict(id=row['id'],expected=row['text'],asr=r['text'].strip(),errors=err,characters=n,match=1-err/n,mtime=path.stat().st_mtime,words=[w for seg in r['segments'] for w in seg.get('words',[])]))
  data=dict(model='local cached whisper-large-v3-turbo',initial_prompt=None,items=results,match=1-sum(x['errors'] for x in results)/sum(x['characters'] for x in results),elapsed=time.time()-start)
  dest.write_text(json.dumps(data,ensure_ascii=False,indent=2));print(row['id'],round(1-err/n,3),r['text'].strip(),flush=True)

if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'synth'
 if mode=='synth':synth(set(sys.argv[2].split(',')) if len(sys.argv)>2 else None)
 elif mode=='assemble':assemble()
 elif mode=='asr':asr()
