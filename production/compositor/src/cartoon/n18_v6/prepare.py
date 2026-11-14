"""Align authored clauses to local Whisper words of the final narration."""
import json,math,re,shutil,subprocess
import numpy as np
import soundfile as sf
from audio import E,W,SR,norm
from plan import beats
FPS=30

def align(a,b):
 d=np.zeros((len(a)+1,len(b)+1),np.int16);d[:,0]=np.arange(len(a)+1);d[0]=np.arange(len(b)+1)
 for i in range(1,len(a)+1):
  for j in range(1,len(b)+1):d[i,j]=min(d[i-1,j]+1,d[i,j-1]+1,d[i-1,j-1]+(a[i-1]!=b[j-1]))
 i,j=len(a),len(b);m={}
 while i and j:
  if d[i,j]==d[i-1,j-1]+(a[i-1]!=b[j-1]):m[i-1]=j-1;i-=1;j-=1
  elif d[i,j]==d[i-1,j]+1:i-=1
  else:j-=1
 return m

def wordmap(row,take):
 chars='';times=[];ends=[]
 for w in take['words']:
  c=norm(w['word']);chars+=c
  times.extend(np.linspace(w['start'],max(w['start']+.01,w['end']),len(c),endpoint=False));ends.extend([w['end']]*len(c))
 mapping=align(norm(row['text']),chars)
 def onset(pos):
  if pos in mapping:return float(times[mapping[pos]])
  nearest=min(mapping,key=lambda k:abs(k-pos)) if mapping else 0
  return float(times[mapping[nearest]]) if mapping else row['duration']*pos/max(1,len(norm(row['text'])))
 return onset

def main():
 meta=json.loads((E/'narration.json').read_text());rows={r['id']:r for r in meta['items']}
 takes={r['id']:r for r in json.loads((E/'asr_takes.json').read_text())['items']}
 maps={sid:wordmap(r,takes[sid]) for sid,r in rows.items()}
 shots=beats();positions={};location_run=-1;prev=None;scene_index=0
 for i,s in enumerate(shots):
  sid=s['sentenceId'];r=rows[sid];pos=positions.get(sid,0);onset=maps[sid](pos)
  # First word in trimmed audio can be labelled 0 by Whisper. Preserve it.
  boundary=r['start']+onset
  if i==0:boundary=0
  s.update(id=f'H{i+1:03}',index=i,start=round(boundary*FPS),boundary_s=boundary,word_offset=pos,cut_offset_s=round(round(boundary*FPS)/FPS-boundary,6))
  positions[sid]=pos+len(norm(s['text']))
  if s['location']!=prev:location_run+=1;scene_index=0
  s['scene']=f'S{location_run+1:02}_{s["location"]}';prev=s['location']
  s['size']=['wide','medium','close','medium','close'][min(scene_index,4)] if scene_index<5 else ('medium' if scene_index%2 else 'close')
  s['angle_deg']=0 if s['size']=='wide' else 35 if s['subject'] in ['commander','deputy','defense','defendants'] else -35
  s.update(axis_side='audience side of action axis',screen_direction='right',transition='hard cut',review='MISMATCH',review_note='Awaiting rendered frame review')
  scene_index+=1
 frames=math.ceil(meta['duration']*FPS)
 captions=[]
 for i,s in enumerate(shots):
  s['end']=shots[i+1]['start'] if i+1<len(shots) else frames
  if s['end']<=s['start']:raise ValueError(('non-monotonic alignment',s))
  s['start_s']=s['start']/FPS;s['end_s']=s['end']/FPS
  # Use a shared continuous clock for acting, independent of shot changes.
  r=rows[s['sentenceId']];s['performanceStart']=round(r['start']*FPS);s['performanceEnd']=round(r['end']*FPS)
  if s['action']=='collapse':
   pos=norm(r['text']).find('쓰러졌습니다')
   s['fallStart']=round((r['start']+maps[s['sentenceId']](max(0,pos)))*FPS)
   s['fallEnd']=max(s['fallStart']+12,min(s['end']-3,s['fallStart']+24))
  words=s['text'].split();chunks=[];chunk=''
  for w in words:
   if chunk and len(chunk+' '+w)>24:chunks.append(chunk);chunk=w
   else:chunk+=(' ' if chunk else '')+w
  if chunk:chunks.append(chunk)
  pos=s['word_offset']
  for j,txt in enumerate(chunks):
   f=s['start'] if j==0 else round((r['start']+maps[s['sentenceId']](pos))*FPS)
   captions.append(dict(text=txt,start=f,end=s['end'],startMs=f/FPS*1000,endMs=s['end']/FPS*1000,timestampMs=None,confidence=None,shotId=s['id']))
   if j:captions[-2]['end']=f;captions[-2]['endMs']=f/FPS*1000
   pos+=len(norm(txt))
 data=dict(fps=FPS,durationInFrames=frames,duration_s=frames/FPS,shots=shots,captions=captions,narration=meta['items'])
 (E/'shots_v6.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2));(E/'episode_data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
 (E/'captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2))
 write_alignment(shots)
 public=E/'public';shutil.copy2(W/'production/compositor/node_modules/pretendard/dist/web/static/woff2/Pretendard-Bold.woff2',public/'Pretendard-Bold.woff2')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(E/'audio/narration.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar',str(SR),str(public/'mix.wav')],check=True)
 print('ALIGNED',len(shots),'shots',frames,'frames',len(captions),'captions',flush=True)
 return data

def write_alignment(shots):
 note='최종 MP4의 각 숏과 모든 컷 직전·직후 프레임을 확인했다.' if all(s['review']=='MATCH' for s in shots) else '최종 화면 검수 전 행은 MISMATCH로 남긴다.'
 (E/'alignment.md').write_text('# N18 v6 나레이션–화면 정렬\n\n시각은 최종 로컬 M1 음성의 Whisper 단어 시각을 30fps로 양자화. 문장 사이 쉼은 이전 숏을 유지한다. '+note+' 각도는 축 계획 값이며, 실제 구도 변화는 SVG 카메라 크롭이다.\n\n|컷|시작–끝(s)|해당 구간 나레이션 원문|화면|숏 크기·각도|자체 검수|\n|---|---|---|---|---|---|\n'+''.join(f'|{s["id"]}|{s["start_s"]:.3f}–{s["end_s"]:.3f}|{s["text"]}|{s["shows"]}|{s["size"]} / {s["angle_deg"]}°|{s["review"]}|\n' for s in shots))

if __name__=='__main__':main()
