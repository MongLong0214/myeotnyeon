"""Voice-led shots, numeric subtitles, source citations and speech envelopes."""
from pathlib import Path
import json,re,math,shutil
import numpy as np,soundfile as sf
from voice import spoken
P=Path(__file__).resolve().parent;W=P.parents[2];FPS=30
def build():
 src=json.loads((P/'audio/index.json').read_text());items=src['items'];voice=[];pos=0
 for ni,n in enumerate(items):
  w,sr=sf.read(P/'audio'/f"{n['id']}.wav");assert sr==48000
  n.update(start_s=pos/sr,end_s=(pos+len(w))/sr)
  voice.append(w);pos+=len(w)
  if ni+1<len(items):voice.append(np.zeros(2640));pos+=2640
 frames=math.ceil(pos/48000*FPS);allw=np.concatenate(voice);allw=np.pad(allw,(0,frames*1600-len(allw)))
 sf.write(P/'public/voice_full.wav',allw,48000,subtype='PCM_24')
 rms=np.sqrt(np.mean(allw.reshape(-1,1600)**2,axis=1));speech=[dict(amplitude=round(float(v),4),viseme=['A','E','O','M','F'][i%5] if v>.04 else 'rest') for i,v in enumerate(np.clip((rms-.004)/.075,0,1)**.7)]
 captions=[]
 for n in items:
  # Phrase units keep subtitles large. Boundaries are replaced by ASR word alignment when available.
  phrases=[]
  for sent in re.split(r'(?<=[.!?])\s+',n['text']):
   words=sent.split();part=''
   for word in words:
    if len(part+' '+word)>23 and part:phrases.append(part);part=word
    else:part=(part+' '+word).strip()
   if part:phrases.append(part)
  weights=[len(re.findall('[가-힣]',spoken(t))) for t in phrases];total=sum(weights);elapsed=0
  for text,weight in zip(phrases,weights):
   a=n['start_s']+n['duration']*elapsed/total;elapsed+=weight;b=n['start_s']+n['duration']*elapsed/total
   captions.append(dict(text=text,startMs=round(a*1000,2),endMs=round(b*1000,2),timestampMs=round(a*1000,2),confidence=None,narrationId=n['id']))
 plans={
 'shoot':['shoot','aftermath'],'mask':['mask','cloth','host'],'hook':['clock','mask','scale','hosttake'],
 'parking':['parking','staff','parking','bags'],'block':['block','approach','block'],'aftermath':['aftermath'],
 'memorial':['memorial'],'bags':['bags','staff','bags'],'car':['car','getaway','car'],
 'gun':['gun','weapontrace','policehurt'],'policehit':['policehit','police','gun'],'nocamera':['nocamera','host'],
 'switch':['switch','getaway','switch'],'burn':['burn','mask','cloth'],'gagdelete':['gagdelete','hosttake'],
 'lab':['lab','mask','dna'],'archive':['archive','records','investigation'],'crowd':['crowd','filter','clues'],
 'wrong':['wrong','investigation'],'clock':['clock','law','clock'],'dna':['dna','lab','cigarette'],
 'arcade':['arcade','cigarette','arcade'],'match':['match','dna','match'],'gagtrash':['gagtrash','hosttake'],
 'identity':['identity','filter','identity'],'links':['links','clues','car'],'arrest':['arrest','identity','arrest'],
 'trace':['trace','statement','links'],'spa':['spa','statement','spa'],'paper':['paper','papers','paper'],
 'blame':['blame','split','blame'],'statement':['statement','testimony','statement'],'money':['money','split','money'],
 'split':['split','money','statement'],'gagparcel':['gagparcel','blame'],'prosecutor':['prosecutor','law','testimony'],
 'hosttake':['hosttake','testimony'],'scale':['scale','testimony','scale'],'verdict':['verdict','judge','verdict'],
 'ruling':['ruling','testimony','ruling'],'trap':['trap','number','scale'],'door':['door','appeal','door'],
 'final':['final','judge','final']}
 shots=[];types=['wide','medium','close-up','insert','low-angle','high-angle','over-the-shoulder'];cameras=['snap','whip','crash','push','dutch','pull']
 graphic={'mask','cloth','cigarette','dna','match','gun','nocamera','clock','law','number','ruling','door'}
 for ni,n in enumerate(items):
  start=round(n['start_s']*FPS);end=round(items[ni+1]['start_s']*FPS) if ni+1<len(items) else frames
  scene=n['scene'];plan=plans[scene];count=max(1,math.ceil((end-start)/43));bounds=[round(start+(end-start)*j/count) for j in range(count+1)]
  if ni==0:bounds=[0,45,end];count=2
  for j in range(count):
   idx=len(shots);action=plan[j%len(plan)]
   if scene=='policehit' and j>0:action='policehurt' if j%2 else 'weapontrace' # Only the initial collision is reconstructed, no repeated collision.
   stype=types[(ni*2+j)%len(types)]
   if action in graphic:stype='insert' if j%2 else 'medium'
   if action in ['shoot','aftermath','policehit']:stype='wide'
   setname='parking' if action in ['shoot','aftermath','parking','staff','block','approach','bags','car','switch','burn','getaway'] else 'street' if action in ['policehit','police','trace'] else 'court' if action in ['prosecutor','verdict','judge','scale','ruling','testimony','final','appeal','split','blame','trap','door','statement','money'] else 'memorial' if scene=='memorial' else 'lab' if action in ['lab','mask','cloth','dna','match','links','identity'] else 'arcade' if action in ['arcade','cigarette'] else 'investigation'
   serious=n.get('serious',False) or action in ['shoot','aftermath','policehit','policehurt'];illustrative=(n.get('illustrative',False) and action in ['gagdelete','gagtrash','gagparcel','hosttake','paper','papers']) or action in ['paper','papers','archive','wrong','number']
   shot=dict(id=f'V5_{idx+1:03}',start=bounds[j],end=bounds[j+1],set=setname,type=stype,action=action,mood='reflective' if scene=='memorial' else 'tense' if setname in ['parking','street'] else 'courtroom' if setname=='court' else 'day',index=idx,variant=j,facts=n['facts'],narrationId=n['id'],purpose=n['text'],serious=serious,illustrative=illustrative,camera='push' if serious else cameras[idx%len(cameras)],energy=0 if serious else 1)
   shots.append(shot)
 (P/'episode_data.json').write_text(json.dumps(dict(fps=FPS,durationInFrames=frames,audioDuration=len(allw)/48000,shots=shots,captions=captions,speech=speech,narration=items),ensure_ascii=False,separators=(',',':')))
 (P/'shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2))
 (P/'captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2))
 (P/'timing.json').write_text(json.dumps(dict(duration_s=len(allw)/48000,syllables=sum(n['syllables'] for n in items),items=items),ensure_ascii=False,indent=2))
 facts={}
 for line in (P.parent/'facts.md').read_text().splitlines():
  if line.startswith('| F'):
   cols=line.split('|');facts[cols[1].strip()]=dict(fact=cols[2].strip(),sources=cols[3].strip())
 md=['# LF2 cartoon v5 · script v2','', '사실 출처: ../facts.md의 채택 사실만 사용. 모든 F행은 독립 보도 2계열 이상. 장면은 가상 인물·공간의 재구성. 발사 횟수·발화장치·확인되지 않은 월일은 재현하지 않는다. 피해자 식별·사망 희화화·상처 확대 없음. 풍자는 가해자의 책임 회피와 증거인멸의 모순에 한정한다.','',f"실측 러닝타임 {len(allw)/48000:.3f}s · 발음 입력 {sum(n['syllables'] for n in items)}음절 · M1/Supertonic 3 신규 합성. 화면 날짜는 아래 원문 숫자를 유지한다.",'']
 for n in items:
  flags=(' · CLIFFHANGER' if n.get('loop') else '')+(' · 진지한 사건 재현' if n.get('serious') else '')+(' · 비사실적 비유 표기' if n.get('illustrative') else '')
  md+= [f"## {n['id']} · {n['start_s']:.3f}–{n['end_s']:.3f}s{flags}", '',n['text'],'',f"화면: {n['scene']} · {'총 인출→발사광·충격→익명 피해자 쓰러짐. 희화화 없음.' if n['scene']=='shoot' else '짧은 행동 컷과 카메라 변주.'}",'']
  for fid in n['facts']:md+=[f"- {fid}: {facts[fid]['fact']} — {facts[fid]['sources']}"]
  md+=['']
 (P/'script_v2.md').write_text('\n'.join(md))
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (P/'subtitles.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs']/1000)} --> {stamp(c['endMs']/1000)}\n{c['text']}" for i,c in enumerate(captions)))
 print('BUILT',frames/30,'seconds',len(shots),'shots',sum(n['syllables'] for n in items),'syllables')
if __name__=='__main__':build()
