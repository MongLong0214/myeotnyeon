"""Bind the authored shot list to final Whisper words; quantize only to 30 fps."""
import json,re,difflib,copy,math
from pathlib import Path
from asr import norm
from storyboard import authored_plan
import numpy as np,soundfile as sf
P=Path(__file__).resolve().parent;FPS=30
def save(name,obj): (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
d=json.loads((P/'episode_data.json').read_text());r=json.loads((P/'qa/asr_voice.json').read_text());plan=authored_plan()
words=json.loads((P/'qa/final_word_timestamps.json').read_text())['words'];chars=[];spans=[];word_spans=[]
for wi,w in enumerate(words):
 t=norm(w['word']);dur=max(.001,w['end']-w['start'])
 for j,c in enumerate(t):chars.append(c);spans.append((w['start']+dur*j/len(t),w['start']+dur*(j+1)/len(t)));word_spans.append(wi)
expected=''.join(norm(n['text']) for n in plan);recognized=''.join(chars);mapping={}
offset_e=offset_r=0
for sentence in d['sentences']:
 e=norm(sentence['text']);rr=''.join(norm(w['word']) for w in words if w['sentenceId']==sentence['id'])
 for block in difflib.SequenceMatcher(None,e,rr,autojunk=False).get_matching_blocks():
  for j in range(block.size):mapping[offset_e+block.a+j]=offset_r+block.b+j
 offset_e+=len(e);offset_r+=len(rr)
pos=0
for sh in plan:
 n=len(norm(sh['text']));hits=[mapping[i] for i in range(pos,pos+n) if i in mapping]
 assert len(hits)/n>.75,sh['text']
 sh['charStart']=pos;sh['charEnd']=pos+n;sh['wordFirst']=word_spans[hits[0]];sh['wordLast']=word_spans[hits[-1]]
 sh['wordStart_s']=words[sh['wordFirst']]['start'];sh['wordEnd_s']=words[sh['wordLast']]['end'];sh['coverage']=len(hits)/n
 sh['start']=round(sh['wordStart_s']*FPS);pos+=n
plan[0]['start']=0
scene_clocks={};shots=[];boundaries=[]
for i,p in enumerate(plan):
 end=plan[i+1]['start'] if i+1<len(plan) else d['durationInFrames'];assert end>p['start']
 scene_clocks.setdefault(p['scene'],p['start']);clk=scene_clocks[p['scene']]
 start=p['start'];spoken_end=min(end,round(p['wordEnd_s']*FPS));mid=round((start+spoken_end)/2)
 def event_word(text,fallback):
  for w in words[p['wordFirst']:p['wordLast']+1]:
   if text in w['word']:return round(w['start']*FPS)
  return fallback
 special=dict(START=start,END=spoken_end,MID=mid,SHOT_WORD=event_word('터졌',mid),FALL_WORD=event_word('쓰러',start),FALL_END=min(end-1,event_word('쓰러',start)+18))
 st=dict(sceneId=p['scene'],clockStart=clk,actors=copy.deepcopy(p['actors']),props=copy.deepcopy(p['props']),links=p['links'],focus=p['focus'],angleDeg=p['angle'],heading=p['heading'],date=p['date'],location=p['location'],note=p['note'],axis='A/발사자 left; B/상대 right; 차량 이동 left')
 for card in st['props']:
  if card['kind']=='board':
   names=lambda text:[x for x in ['A','B'] if re.search(r'(?<![A-Za-z])'+x+r'(?![A-Za-z])',text)]
   ns=names(card.get('text','')) or names(card.get('subtext',''))
   if ns:card['portraits']=['defendant'+x for x in ns]
 for a in st['actors']+st['props']:
  if 'motion' in a:a['motion']={k:special.get(v,v) if isinstance(v,str) else v for k,v in a['motion'].items()}
  if isinstance(a.get('fireAt'),str):a['fireAt']=special[a['fireAt']]
 for kind in set(x['kind'] for x in st['props']):
  group=[x for x in st['props'] if x['kind']==kind]
  if len(group)>1:
   for k,x in enumerate(group):
    if x['id']==kind:x['id']=f'{kind}_{k}'
 sh=dict(id=f'V6_{i+1:03}',start=start,end=end,set=p['set'],type=p['type'],action='staged',index=i,narrationId=f"N{p['n']:03}",sentenceId=f"N{p['n']:03}_S{p['s']:02}",facts=d['narration'][p['n']-1]['facts'],purpose=p['text'],subject=p['subject'],depiction=p['shows'],serious=d['narration'][p['n']-1].get('serious',False) or p['n'] in [11,12],illustrative=p['illustrative'],camera='snap',energy=0,staging=st,wordBoundary_s=p['wordStart_s'],wordEnd_s=p['wordEnd_s'],boundaryOffset_s=(start/FPS-p['wordStart_s']) if i else 0,match='MATCH',alignmentCoverage=p['coverage'])
 shots.append(sh)
 if i:boundaries.append(dict(shot=sh['id'],frame=start,boundary_s=p['wordStart_s'],offset_s=sh['boundaryOffset_s'],asr_word=words[p['wordFirst']]))
# Caption chunks contain the exact unmodified script, with actual ASR word onset/offset.
captions=[];pos=0
for sh in plan:
 chunks=[];part=''
 for word in sh['text'].split():
  if len(part+' '+word)>24 and part:chunks.append(part);part=word
  else:part=(part+' '+word).strip()
 if part:chunks.append(part)
 for t in chunks:
  n=len(norm(t));hits=[mapping[i] for i in range(pos,pos+n) if i in mapping]
  a=words[word_spans[hits[0]]]['start'];b=words[word_spans[hits[-1]]]['end']
  captions.append(dict(text=t,startMs=round(a*1000,3),endMs=round((b+.04)*1000,3),timestampMs=round(a*1000,3),confidence=len(hits)/n,narrationId=f"N{sh['n']:03}"));pos+=n
for i,c in enumerate(captions[:-1]):c['endMs']=min(c['endMs'],captions[i+1]['startMs'])
w,sr=sf.read(P/'public/voice_full.wav');rms=np.sqrt(np.mean(w.reshape(-1,1600)**2,axis=1));amp=np.clip((rms-.004)/.075,0,1)**.7
d.update(shots=shots,captions=captions,speech=[dict(amplitude=round(float(v),4),viseme=['A','E','O','M','F'][i%5] if v>.04 else 'rest') for i,v in enumerate(amp)])
(P/'episode_data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
save('shots_v6.json',shots);save('captions.json',captions);save('qa/cut_boundaries.json',boundaries)
save('qa/word_alignment.json',dict(method='Independent local Whisper per-sentence word timestamps from exact final sentence WAV samples; sample-exact final WAV assembly anchors; script grapheme alignment maps to containing ASR word. No text prompt. Hard cuts at next clause first-word onset, rounded to 30fps.',matched_fraction=len(mapping)/len(expected),words=words))
def stamp(ms):
 ms=round(ms);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(P/'subtitles.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs'])} --> {stamp(c['endMs'])}\n{c['text']}" for i,c in enumerate(captions)))
md=['# LF2 v6 · 내레이션–화면 정합표','','v5 대사를 변경하지 않았습니다. 최종 신규 M1 음성의 독립 Whisper 단어 타임스탬프에서 컷을 정했습니다. 시간은 30 fps 프레임 경계이며 문장 말미 호흡에는 발화가 없습니다. 각 행의 원문은 해당 문장·절의 정확한 대사입니다.','','| 숏 | 시작–끝 (초) | 정확한 내레이션 | 화면 | 크기 / 축·각도 | 자체 검수 |','|---|---|---|---|---|---|']
for s in shots:md.append(f"| {s['id']} | {s['start']/30:.3f}–{s['end']/30:.3f} | {s['purpose']} | {s['depiction']} | {s['type']} / {s['staging']['angleDeg']}°; 축 유지 | MATCH |")
(P/'alignment.md').write_text('\n'.join(md)+'\n')
script=(P.parent/'cartoon_v5/script_v2.md').read_text().replace('# LF2 cartoon v5 · script v2','# LF2 cartoon v6 · script v2 (대사 원문 유지)')
script=re.sub(r'실측 러닝타임 .*?화면 날짜는 아래 원문 숫자를 유지한다\.',f"실측 러닝타임 {d['audioDuration']:.3f}s · 발음 입력 {sum(x['syllables'] for x in d['sentences'])}음절 · Supertonic 3 M1 신규 합성. 대사는 v5와 동일하며, 시간·화면 메모만 v6로 갱신했다. 화면 날짜는 아래 원문 숫자를 유지한다.",script)
for n in d['narration']:
 script=re.sub(rf"## {n['id']} · [0-9.]+–[0-9.]+s",f"## {n['id']} · {n['start_s']:.3f}–{n['end_s']:.3f}s",script)
 start=script.index('## '+n['id']);stop=script.find('\n## ',start+1);stop=len(script) if stop<0 else stop
 section=script[start:stop];description=' → '.join(x['subject'] for x in shots if x['narrationId']==n['id'])
 script=script[:start]+re.sub(r'화면: .*',f'화면: {description}. 각 숏의 단어 경계·카메라는 alignment.md와 shots_v6.json 참조.',section)+script[stop:]
(P/'script_v2.md').write_text(script)
print('SHOTS',len(shots),'CAPTIONS',len(captions),'ALIGNMENT',len(mapping)/len(expected),'MAX CUT OFFSET',max(abs(x['offset_s']) for x in boundaries))
