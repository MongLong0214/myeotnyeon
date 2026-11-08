"""Build voice-driven shots, word-timed subtitles and original local sound."""
from pathlib import Path
import json,re,math,shutil,subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
import audio as V
E=V.E;W=V.W;FPS=30;SR=48000
def align(ref,hyp):
 n,m=len(ref),len(hyp);d=np.zeros((n+1,m+1),dtype=np.int16);d[:,0]=np.arange(n+1);d[0]=np.arange(m+1)
 for i in range(1,n+1):
  for j in range(1,m+1):d[i,j]=min(d[i-1,j]+1,d[i,j-1]+1,d[i-1,j-1]+(ref[i-1]!=hyp[j-1]))
 pairs={};i,j=n,m
 while i and j:
  if d[i,j]==d[i-1,j-1]+(ref[i-1]!=hyp[j-1]):pairs[i-1]=j-1;i-=1;j-=1
  elif d[i,j]==d[i-1,j]+1:i-=1
  else:j-=1
 return pairs
def captions(row,asr):
 chunks=[];current=''
 for word in row['text'].split():
  if current and len(current+' '+word)>22:chunks.append(current);current=word
  else:current+=(' ' if current else '')+word
 if current:chunks.append(current)
 ref=V.norm(row['tts']);hyp='';times=[]
 for w in asr.get('words',[]):
  chars=V.norm(w['word']);hyp+=chars
  times.extend(np.linspace(w['start'],max(w['start']+.01,w['end']),len(chars),endpoint=False).tolist())
 mapping=align(ref,hyp) if hyp else {}
 pos=0;raw=[]
 for chunk in chunks:
  k=len(V.norm(chunk));mapped=mapping.get(min(pos,len(ref)-1))
  start=times[mapped] if mapped is not None and mapped<len(times) else row['duration']*pos/max(1,len(ref))
  raw.append((chunk,max(0,min(row['duration']-.03,float(start)))));pos+=k
 raw[0]=(raw[0][0],0)
 for j,(txt,start) in enumerate(raw):
  end=raw[j+1][1] if j<len(raw)-1 else row['duration']
  # Timestamp failures must not create unreadably brief text flashes.
  if end<=start:end=min(row['duration'],start+.1)
  chunks[j]=dict(text=txt,start=round((row['start']+start)*FPS),end=round((row['start']+end)*FPS),narrationId=row['id'])
 return chunks
def make_data():
 meta=json.loads((E/'narration.json').read_text());rows=meta['items'];frames=math.ceil(meta['duration']*FPS)
 asr={x['id']:x for x in json.loads((E/'asr_takes.json').read_text())['items']}
 subs=[];shots=[]
 for row in rows:
  subs+=captions(row,asr.get(row['id'],{}))
  start=round(row['start']*FPS);end=round(row['end']*FPS)
  end=round(rows[rows.index(row)+1]['start']*FPS) if row!=rows[-1] else frames
  serious=row['beat']=='serious' or bool(re.search('family|memorial',row['scene'])) or row['scene'] in ['medics','witness','witness-pack']
  count=max(1,math.ceil((end-start)/(58 if serious else 49)))
  boundaries=[round(start+(end-start)*j/count) for j in range(count+1)]
  for j in range(count):
   scene=row['scene'];idx=len(shots)
   if row['id']=='N009' and j==1:scene='insert-pack'
   if row['id']=='N073' and j==1:scene='insert-certificate'
   typ=['wide','medium','low-angle','medium','high-angle'][idx%5]
   if scene.startswith('narrator') or (scene in ['court-judge','defense'] and j==1):typ='close-up'
   if scene.startswith('insert'):typ='insert'
   if 'drill' in scene or scene=='witness-collapse':typ='wide' if j%2==0 else 'medium'
   shots.append(dict(id=f'F{idx+1:03}',index=idx,start=boundaries[j],end=boundaries[j+1],scene=scene,type=typ,serious=serious,performanceStart=start,performanceEnd=end,narrationId=row['id'],facts=[x for x in row['facts'] if x!='논평'],characterPresent=not scene.startswith('insert'),characterActing=not scene.startswith('insert') and scene!='hospital-loss' and not (scene=='witness-collapse' and j>0),purpose=row['text']))
 # Reallocate inserts to <=1.5 s while preserving all timeline coverage.
 for i,s in enumerate(shots):
  if s['type']=='insert' and s['end']-s['start']>45:
   excess=s['end']-s['start']-45;s['start']+=excess;shots[i-1]['end']+=excess
 w,sr=sf.read(V.A/'voice.wav');padded=np.pad(w,(0,frames*1600-len(w)));rms=np.sqrt(np.mean(padded.reshape(-1,1600)**2,axis=1));speech=[]
 for k,r in enumerate(rms):speech.append(dict(amplitude=round(float(np.clip((r-.003)/.15,0,1)**.7),4),viseme='rest' if r<.003 else 'A'))
 for row in rows:
  chars=[c for c in row['tts'] if '가'<=c<='힣'];a=round(row['start']*FPS);b=round(row['end']*FPS)
  for k in range(a,min(b,frames)):
   v=(ord(chars[min(len(chars)-1,int((k-a)/max(1,b-a)*len(chars)))])-0xac00)%588//28
   speech[k]['viseme']='rest' if speech[k]['amplitude']<.03 else 'O' if v in [8,9,10,11,12,13,14,15,16,17] else 'E' if v in [1,3,5,7,19,20] else 'A'
 data=dict(fps=FPS,durationInFrames=frames,duration=meta['duration'],shots=shots,captions=subs,speech=speech,narration=rows)
 (E/'episode_data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
 (E/'shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2))
 public=E/'public';public.mkdir(exist_ok=True)
 shutil.copy2(W/'production/compositor/node_modules/pretendard/dist/web/static/woff2/Pretendard-Bold.woff2',public/'Pretendard-Bold.woff2')
 (E/'shot_list.md').write_text('# N18 v5 연기 샷리스트\n\n모든 수치는 실제 음성 기준. 재연 인물은 비식별. 쓰러짐·응급·사망·추모는 진지한 톤.\n\n|컷|초|연기·구도|근거|\n|---|---|---|---|\n'+''.join(f'|{s["id"]}|{s["start"]/30:.2f}–{s["end"]/30:.2f}|{s["scene"]} / {s["type"]}|{", ".join(s["facts"])}|\n' for s in shots))
 print('DATA',frames,len(shots),'captions',len(subs),flush=True)
 return data,w
def make_mix(data,voice):
 n=data['durationInFrames']*1600;voice=np.pad(voice,(0,n-len(voice))).astype(np.float32)
 music=np.zeros(n,np.float32);fx=np.zeros(n,np.float32);rng=np.random.default_rng(1805);bpm=146;beat=60/bpm
 def add(dst,start,v,gain):
  a=round(start*SR);b=min(n,a+len(v))
  if b>a:dst[a:b]+=v[:b-a]*gain
 for k in range(math.ceil(n/SR/beat)):
  start=k*beat;t=np.arange(int(SR*.24))/SR
  kick=np.sin(2*np.pi*(48*t+5*(1-np.exp(-t*32))))*np.exp(-t*24)
  if k%4 in [0,2]:add(music,start,kick,.12)
  if k%4 in [1,3]:
   noise=rng.normal(size=len(t));sn=sosfilt(butter(2,1500,fs=SR,btype='high',output='sos'),noise)*np.exp(-t*32)
   add(music,start,sn,.032)
  t=np.arange(round(SR*beat*.82))/SR;note=[110,110,130.81,98,110,164.81,130.81,98][k%8]
  bass=(np.sin(2*np.pi*note*t)+.22*np.sin(2*np.pi*note*2*t))*np.minimum(1,t*120)*np.exp(-t*5)
  add(music,start,bass,.065)
  for j in range(2):
   t=np.arange(int(SR*.045))/SR;hat=sosfilt(butter(2,6000,fs=SR,btype='high',output='sos'),rng.normal(size=len(t)))*np.exp(-t*95)
   add(music,start+j*beat/2,hat,.012)
  if k%2==0:
   t=np.arange(int(SR*beat*1.8))/SR;chord=sum(np.sin(2*np.pi*v*t) for v in [220,261.63,329.63])/3
   add(music,start,chord*np.minimum(1,t*15)*np.exp(-t*2),.027)
 # Musical/FX tone follows the source beats. No comic sound on suffering.
 tone=np.ones(n,np.float32)
 for s in data['shots']:
  a=s['start']*1600;b=s['end']*1600
  if s['serious']:tone[a:b]=.16
  else:
   t=np.arange(int(SR*.14))/SR
   whoosh=sosfilt(butter(2,[450,6500],fs=SR,btype='bandpass',output='sos'),rng.normal(size=len(t)))*np.sin(np.pi*np.arange(len(t))/len(t))**2
   add(fx,a/SR,whoosh,.026)
   if s['scene'] in ['narrator-wild','court-verdict','appeal-verdict']:
    t=np.arange(int(SR*.3))/SR;sting=np.sin(2*np.pi*(240*t+210*t*t))*np.exp(-t*14)
    add(fx,a/SR,sting,.035)
 for r in data['narration']:
  if r['beat']=='loop' and not re.search('family|memorial',r['scene']):
   t=np.arange(int(SR*.6))/SR;v=np.sin(2*np.pi*(110*t+500*t*t))*np.minimum(1,t*3)*np.exp(-t*3)
   add(fx,max(0,r['start']-.1),v,.025 if r['scene']!='medics' else .004)
 # Continuous voice sidechain; gain reductions are smoothed to avoid pumping.
 env=np.sqrt(np.mean(voice[:n//480*480].reshape(-1,480)**2,axis=1));duck=np.interp(np.arange(n)/480,np.arange(len(env)),env)
 duck=np.clip(.7-duck*4,.18,.7)
 music*=tone*duck
 mix=voice+music+fx
 sf.write(E/'audio/music_original.wav',music,SR,subtype='PCM_24');sf.write(E/'audio/sfx_original.wav',fx,SR,subtype='PCM_24');sf.write(E/'audio/mix_pre.wav',mix,SR,subtype='PCM_24')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(E/'audio/mix_pre.wav'),'-af','loudnorm=I=-14.5:TP=-1.5:LRA=7','-ar',str(SR),str(E/'public/mix.wav')],check=True)
 (E/'audio_manifest.json').write_text(json.dumps(dict(narration='Local Supertonic 3 M1; existing OpenRAIL-M model; fresh synthesis.',music='Original procedural 146 BPM minor synth bass/chords/drums from NumPy sine/noise; no samples.',sfx='Original seeded filtered noise and sine chirps; no external recordings.',third_party_recordings=[],network=False,uploads=False),ensure_ascii=False,indent=2))
 print('MIX READY',flush=True)
if __name__=='__main__':
 data,w=make_data();make_mix(data,w)
