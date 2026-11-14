"""Fresh offline Supertonic 3 M1 takes, never reusing stale audio."""
import os,json,re,subprocess,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(P/'tmp'))
import socket
def denied(*a,**k):raise RuntimeError('Network disabled')
socket.create_connection=denied;socket.socket.connect=denied
import numpy as np,soundfile as sf
from supertonic import TTS
DIG='영일이삼사오육칠팔구'
def korean(n):
 n=int(n)
 if n==0:return '영'
 out=''
 for base,unit in [(10000,'만'),(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
  q,n=divmod(n,base)
  if q:out+=('' if q==1 and base>1 else korean(q) if q>9 else DIG[q])+unit
 return out
LEX={'DNA':'디엔에이','CCTV':'씨씨티비','A':'에이','B':'비','38구경':'삼십팔 구경','2인조':'이인조','2개':'두 개','3명이':'세 명이','3명도':'세 명도','10시':'열 시','10월':'시월','1심':'일심','9000만':'구천만','2억1000만':'이억 천만','1만5000':'일만 오천','15만':'십오만','40대':'사십 대'}
def spoken(s):
 for a,b in sorted(LEX.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return re.sub(r'\d+',lambda m:korean(m[0])+' ',s)
def tighten(w,sr,limit=.11):
 hop=int(sr*.005);n=len(w)//hop
 rms=np.sqrt(np.mean(w[:n*hop].reshape(n,hop)**2,axis=1));quiet=rms<.01
 spans=[];start=None
 for i,q in enumerate(np.r_[quiet,False]):
  if q and start is None:start=i
  if not q and start is not None:
   if (i-start)*.005>limit:spans.append((start*hop,i*hop))
   start=None
 for a,b in reversed(spans):
  keep=int(sr*limit)//2;w=np.concatenate([w[:a+keep],w[b-keep:]])
 return w
def finish(w,sr):
 hop=round(sr*.005);n=len(w)//hop;r=np.sqrt(np.mean(w[:n*hop].reshape(-1,hop)**2,axis=1));active=np.flatnonzero(r>=.01)
 w=w[max(0,active[0]*hop-hop):min(len(w),(active[-1]+1)*hop+hop)]
 return tighten(w,sr,limit=.10)
def main():
 src=json.loads((P/'script_source.json').read_text());out=[]
 tts=TTS(model_dir='/Users/isaac/.cache/supertonic3',auto_download=False,intra_op_num_threads=4,inter_op_num_threads=1);style=tts.get_voice_style(voice_name='M1')
 for i,c in enumerate(src['cues']):
  for j,txt in enumerate(re.split(r'(?<=[.!?])\s+',c['text'])):
   sid=f'N{i+1:03}_S{j+1:02}';t=spoken(txt);raw=P/'audio'/f'{sid}_raw.wav';f=P/'audio'/f'{sid}.wav'
   if not raw.exists():
    np.random.seed(611106+i*19+j)
    wav,_=tts.synthesize(t,voice_style=style,lang='ko',speed=1.12,total_steps=20,silence_duration=.12)
    sf.write(raw,np.asarray(wav).reshape(-1),tts.sample_rate,subtype='PCM_24')
   w,sr=sf.read(raw);idx=np.flatnonzero(np.abs(w)>.008);w=w[max(0,idx[0]-int(sr*.01)):idx[-1]+int(sr*.015)];w=tighten(w,sr,limit=.10)
   syl=len(re.findall('[가-힣]',t));target=syl/7.65
   tmp=P/'audio'/f'{sid}_trim.wav';sf.write(tmp,w,sr,subtype='PCM_24')
   factor=(len(w)/sr)/target
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(tmp),'-af',f'atempo={factor:.8f},alimiter=limit=0.94:level=false','-ar','48000',str(f)],check=True)
   w,sr=sf.read(f);w=finish(w,sr);sf.write(f,w,sr,subtype='PCM_24');tmp.unlink()
   item=dict(id=sid,narrationId=f'N{i+1:03}',text=txt,tts_text=t,syllables=syl,duration=len(w)/sr,rate=syl/(len(w)/sr),atempo=factor,sha256=hashlib.sha256(f.read_bytes()).hexdigest());out.append(item)
   print(sid,round(item['duration'],3),txt,flush=True)
   (P/'audio/index.json').write_text(json.dumps(dict(model='supertonic-3',voice='M1',speed=1.12,steps=20,sentence_pause_s=.24,articulation_target=7.65,fresh_generation='Task G v6, 2026-11-01',items=out),ensure_ascii=False,indent=2))
 print('TOTAL',sum(c['duration'] for c in out)+.24*(len(out)-1),sum(c['syllables'] for c in out),flush=True)
if __name__=='__main__':main()
