"""Offline Supertonic 3 M1 narration, pitch-preserving pace and local ASR."""
from pathlib import Path
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import json,re,sys,subprocess,time
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
W=Path(__file__).resolve().parents[5]
E=W/'episodes/v4/n18/cartoon_v5'
A=E/'audio/voice_v2';A.mkdir(parents=True,exist_ok=True)
RATE=48000
PACE=8.6
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
 s=re.sub(r'(\d+)월',lambda m:('유' if m[1]=='6' else '시' if m[1]=='10' else sino(m[1]))+' 월',s)
 s=re.sub(r'\d+',lambda m:sino(m[0]),s)
 return s.replace('1심','일심').replace('2심','이심')
def norm(s):
 s=re.sub(r'\s+','',s)
 # Canonical numeric readings; no expected text is supplied to ASR.
 s=spoken(s).replace('육월','유월').replace('이틀후','이틀뒤')
 s=re.sub(r'\s+','',s)
 for a,b in [('한','일'),('두','이'),('세','삼'),('네','사'),('다섯','오'),('여섯','육'),('일곱','칠'),('여덟','팔'),('아홉','구'),('마흔','사십')]:
  s=re.sub(a+r'(?=바퀴|명|사람|개|시간|권|차례)',b,s)
 return re.sub('[^가-힣]','',s)
def distance(a,b):
 a,b=norm(a),norm(b);d=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  prev=d[:];d[0]=i
  for j,cb in enumerate(b,1):d[j]=min(prev[j]+1,d[j-1]+1,prev[j-1]+(ca!=cb))
 return d[-1],len(a)
def read_script():
 rows=[]
 for l in (E/'script_v2.md').read_text().splitlines():
  if not re.match(r'\| N\d',l):continue
  p=[x.strip() for x in l.split('|')]
  rows.append(dict(id=p[1],text=p[2],tts=spoken(p[2]),facts=p[3].split(','),scene=p[4],beat=p[5]))
 return rows
def trim_silence(w,sr,max_s=.09):
 # Keep short articulation gaps, shorten only quiet runs exceeding the limit.
 hop=int(sr*.005);pad=int(sr*.012)
 rms=np.array([np.sqrt(np.mean(w[i:i+hop]**2)) for i in range(0,len(w),hop)])
 quiet=rms<.0032;changes=np.diff(np.r_[False,quiet,False].astype(int))
 cuts=[]
 for a,b in zip(np.where(changes==1)[0],np.where(changes==-1)[0]):
  lo=a*hop;hi=min(b*hop,len(w))
  if hi-lo>sr*max_s:cuts.append((lo+int(sr*max_s/2),hi-int(sr*max_s/2)))
 keep=np.ones(len(w),bool)
 for a,b in cuts:keep[a:b]=False
 w=w[keep];active=np.where(np.abs(w)>.006)[0]
 if len(active):w=w[max(0,active[0]-pad):min(len(w),active[-1]+pad)]
 return w
def synthesize(rows,ids=None):
 from supertonic import TTS
 tts=TTS(auto_download=False,intra_op_num_threads=3,inter_op_num_threads=1)
 style=tts.get_voice_style(voice_name='M1')
 for row in rows:
  sid=row['id']
  if ids and sid not in ids:continue
  raw=A/f'{sid}_native.wav';out=A/f'{sid}.wav'
  if not raw.exists() or ids:
   wav,_=tts.synthesize(row['tts'],voice_style=style,lang='ko',speed=1.3,total_steps=16,silence_duration=.06)
   w=np.asarray(wav,dtype=np.float32).reshape(-1)
   sf.write(raw,trim_silence(w,44100),44100,subtype='PCM_24')
  w,sr=sf.read(raw);syl=len(re.findall('[가-힣]',row['tts']))
  target=3.847375 if sid=='N019' else syl/(7.9 if sid in ['N003','N004','N015'] else PACE)
  tempo=(len(w)/sr)/target
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={tempo:.7f}','-ar',str(RATE),str(out)],check=True)
  w,sr=sf.read(out);w=trim_silence(w,sr,.09)
  if sid=='N019':
   count=round(3.847375*sr)
   if len(w)>count:
    sf.write(A/'_n19_tempo.wav',w,sr)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(A/'_n19_tempo.wav'),'-af',f'atempo={len(w)/(count-480):.8f}',str(A/'_n19_fit.wav')],check=True)
    w,_=sf.read(A/'_n19_fit.wav')
   w=np.pad(w,(0,max(0,count-len(w))))[:count]
  w=w*(.77/max(.001,np.max(np.abs(w))))
  sf.write(out,w,sr,subtype='PCM_24')
  print(sid,'syl',syl,'s',round(len(w)/sr,3),'tempo',round(tempo,3),flush=True)
 assemble(rows)
def assemble(rows):
 waves=[];pos=0;gap=np.zeros(round(RATE*.035));items=[]
 for row in rows:
  w,sr=sf.read(A/f'{row["id"]}.wav');assert sr==RATE
  row=dict(row,start=pos/RATE,end=(pos+len(w))/RATE,syllables=len(re.findall('[가-힣]',row['tts'])),duration=len(w)/RATE)
  items.append(row);waves.extend([w,gap]);pos+=len(w)+len(gap)
 sf.write(A/'voice.wav',np.concatenate(waves),RATE,subtype='PCM_24')
 meta=dict(voice='M1',model='Supertone/supertonic-3',native_speed=1.3,target_syl_s=PACE,items=items,duration=pos/RATE,syllables=sum(x['syllables'] for x in items))
 (E/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 print('TOTAL',meta['duration'],'PACE',meta['syllables']/meta['duration'],flush=True)
def asr(rows,mode='takes'):
 import mlx_whisper
 items=[r for r in rows if (A/f'{r["id"]}.wav').exists()];results=[];start=time.time()
 file=E/f'asr_{mode}.json'
 prior=json.loads(file.read_text()) if file.exists() else {'items':[]}
 prior={r['id']:r for r in prior['items']}
 for row in items:
  f=A/f'{row["id"]}.wav'
  if row['id'] in prior and prior[row['id']].get('mtime')==f.stat().st_mtime:
   rec=prior[row['id']];err,n=distance(row['tts'],rec['asr']);rec.update(text=row['text'],errors=err,characters=n,match=1-err/n);results.append(rec);continue
  r=mlx_whisper.transcribe(str(f),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='ko',condition_on_previous_text=False,temperature=0,verbose=False,word_timestamps=True)
  errors,n=distance(row['tts'],r['text'])
  results.append(dict(id=row['id'],text=row['text'],asr=r['text'].strip(),errors=errors,characters=n,match=1-errors/n,mtime=f.stat().st_mtime,words=[w for seg in r['segments'] for w in seg.get('words',[])]))
  file.write_text(json.dumps(dict(model='local cached whisper-large-v3-turbo',prompt=None,normalization='numeric readings; whitespace/punctuation; 육월→유월; 이틀후→이틀뒤',items=results,match=1-sum(x['errors'] for x in results)/sum(x['characters'] for x in results),elapsed=time.time()-start),ensure_ascii=False,indent=2))
  print(row['id'],round(1-errors/n,4),r['text'].strip(),flush=True)
 file.write_text(json.dumps(dict(model='local cached whisper-large-v3-turbo',prompt=None,normalization='numeric cardinal/native counter readings; whitespace/punctuation; 육월→유월; 이틀후→이틀뒤',items=results,match=1-sum(x['errors'] for x in results)/sum(x['characters'] for x in results),elapsed=time.time()-start),ensure_ascii=False,indent=2))
if __name__=='__main__':
 rows=read_script();mode=sys.argv[1] if len(sys.argv)>1 else 'synth'
 if mode=='synth':synthesize(rows,set(sys.argv[2].split(',')) if len(sys.argv)>2 else None)
 elif mode=='assemble':assemble(rows)
 elif mode=='asr':asr(rows)
