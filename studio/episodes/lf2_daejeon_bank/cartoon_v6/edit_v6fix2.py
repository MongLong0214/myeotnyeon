"""Production edit for CEO decision A: replace the middle, retain the outer PCM."""
import copy,difflib,hashlib,json,math,re,sys
from pathlib import Path
import numpy as np,soundfile as sf
P=Path(__file__).resolve().parent;E=P/'fix2_evidence';FPS=30;SR=48000

def read(name):return json.loads((P/name).read_text())
def save(name,value): (P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def display(text):
 text=re.sub(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',lambda m:f'{m[1]}-{int(m[2]):02}-{int(m[3]):02}',text)
 return re.sub(r'(\d{4})년\s*(\d{1,2})월',lambda m:f'{m[1]}-{int(m[2]):02}',text)

def assemble():
 old=read('fix2_evidence/previous_episode_data.json');plan=read('middle_v6fix2.json');index=read('fix2_evidence/audio_index.json');takes=index['items'];assert len(takes)==sum(len(r['sentences']) for r in plan)
 original,sr=sf.read(P/'public/voice_full.wav',dtype='int32');assert sr==SR
 a=round(old['narration'][21]['start_s']*SR);b=round(old['narration'][55]['start_s']*SR)
 parts=[original[:a]];cursor=a;sentences=[]
 for s in old['sentences']:
  if int(s['narrationId'][1:])<=21:sentences.append(dict(s,audio_path=f"audio/{s['id']}.wav"))
 for s in takes:
  s=copy.deepcopy(s);w,sr=sf.read(P/s['audio_path'],dtype='int32');assert sr==SR
  s.update(start_s=cursor/SR,end_s=(cursor+len(w))/SR);sentences.append(s);parts.extend([w,np.zeros(11520,dtype=np.int32)]);cursor+=len(w)+11520
 suffix_start=cursor;delta=(cursor-b)/SR;parts.append(original[b:])
 for s in old['sentences']:
  if int(s['narrationId'][1:])>=56:sentences.append(dict(s,start_s=s['start_s']+delta,end_s=s['end_s']+delta,audio_path=f"audio/{s['id']}.wav"))
 wave=np.concatenate(parts);frames=math.ceil(len(wave)/1600);wave=np.pad(wave,(0,frames*1600-len(wave)))
 sf.write(P/'public/voice_v6fix2.wav',wave,SR,subtype='PCM_24')
 rendered,_=sf.read(P/'public/voice_v6fix2.wav',dtype='int32')
 assert np.array_equal(original[:a],rendered[:a]) and np.array_equal(original[b:],rendered[suffix_start:suffix_start+len(original)-b])
 narration=[copy.deepcopy(n) for n in old['narration'] if int(n['id'][1:])<=21]
 for row in plan:
  ss=[s for s in sentences if s['narrationId']==row['id']]
  narration.append(dict(id=row['id'],text=' '.join(s['text'] for s in row['sentences']),facts=list(dict.fromkeys(f for s in row['sentences'] for f in s['facts'])),start_s=ss[0]['start_s'],end_s=ss[-1]['end_s'],before=row['before']))
 narration.extend(dict(n,start_s=n['start_s']+delta,end_s=n['end_s']+delta) for n in old['narration'] if int(n['id'][1:])>=56)
 amp=np.clip((np.sqrt(np.mean((wave.astype(float)/2147483648).reshape(-1,1600)**2,axis=1))-.004)/.075,0,1)**.7
 d=dict(fps=30,durationInFrames=frames,audioDuration=frames/30,narration=narration,sentences=sentences,shots=[],captions=[],speech=[dict(amplitude=round(float(v),4),viseme='A' if v>.04 else 'rest') for v in amp],audio_edits=dict(old_middle=[a/SR,b/SR],new_middle=[a/SR,suffix_start/SR],suffix_delta_s=delta,prefix_sample_identical=True,suffix_sample_identical=True,prefix_samples=a,suffix_samples=len(original)-b,new_suffix_sample=suffix_start,settings={k:index[k] for k in ['model','voice','speed','steps','sentence_pause_s','articulation_target']}))
 save('episode_data_v6fix2.json',d)
 print('ASSEMBLED',frames/30,'s; reduction',old['audioDuration']-frames/30,'s; outer PCM identical')

# Cuts are authored clauses, bound below to the matching spoken words. The
# source scenes show adopted facts, not invented filler conversations.
BEATS={
'M01':[('2015년 태완이법 시행으로 살인죄 공소시효가 폐지되면서,',48),('이 사건도 수사를 계속할 수 있었습니다.',42)],
'M02':[('2017년 재감식에서',51),('마스크와 손수건의 DNA가 돌파구가 됐습니다.',52),('2015년 충북 불법게임장에서 수거한 담배꽁초의 DNA와',55),('일치한 겁니다.',56)],
'M03':[('게임장 DNA도 신원불명이었습니다.',61),('경찰은 출입 가능자 약 1만5000명을 수사 대상으로 삼고,',55),('몽타주와 목격자 인상착의,',65),('차량 절도 수법을 대조했습니다.',20),('전원의 DNA를 뽑았다는 뜻은 아닙니다.',65)],
'M04':[('2022년 3월 B를 특정한 경찰은 과거 행적과 주변인을 조사했습니다.',67),('2022년 8월 25일, 대전에서 B를 붙잡았습니다.',70)],
'M05':[('B는 A와 함께 범행했다고 진술했고,',72),('그 진술을 단서로 A를 강원도 정선의 찜질방에서 붙잡았습니다.',75),('고등학교 동창인 두 사람은 2022년 8월 27일 구속됐습니다.',77),('A까지 같은 DNA로 특정한 건 아닙니다.',73)],
'M06':[('검거까지 약 20년 8개월,',70),('쌓인 수사기록은 약 15만 쪽이라고 보도됐습니다.',79)],
'M07':[('두 사람은 서로 상대가 총을 쐈다고 주장했습니다.',[82,83]),('A는 처음 부인하다 총격을 시인했다고 경찰이 발표했지만,',84),('재판에서는 다시 부인했습니다.',85)],
'M08':[('돈 분배도 B는 자신이 9000만 원, A가 2억1000만 원을 가졌다고 했고,',87),('A는 절반씩이라고 했습니다.',88),('서로 다른 주장일 뿐, 실제 분배액으로 확정된 건 아닙니다.',[87,88])],
'M09':[('2023년 1월 16일, 검찰은 A에게 사형,',94),('B에게 무기징역을 구형했습니다.',105),('법원의 판결이 아닌 검찰의 요구입니다.',94)],
'M10':[('2023년 2월 17일, 1심은 A에게 무기징역,',101),('B에게 징역 20년을 선고했습니다.',105)],
'M11':[('A의 총기 경험과 권총을 쥐고 조준한 정황,',12),('진술 신빙성을 보고 A의 총격을 인정했습니다.',104),('B에게는 보조 역할과',31),('사건 규명에 도움이 된 자백을 고려했습니다.',72)],
'M12':[('하지만 2023년 8월 18일, 항소심은',110),('둘 다 무기징역을 선고했습니다.',111)],
'M13':[('당시 적용법상 강도살인의 법정형은',1),('사형 또는 무기징역.',113),('감경해도 유기징역 상한이 15년이어서,',119),('1심의 20년 선고가 잘못됐다는 판단입니다.',115)],
'M14':[('항소심은 B에게 불리한 사정이 유리한 사정을 압도한다고 보고', [31,72]),('감경하지 않았습니다.',117),('그래서 15년이 아니라 무기징역입니다.',119)],
'M15':[('A가 권총을 발사했다는 판단은',12),('항소심에서도 유지됐습니다.',122)],
'M16':[('두 사람은 형이 무겁다며 상고했지만,',123),('2023년 12월 14일 대법원이 상고를 기각해',126),('모두 무기징역이 확정됐습니다.',[102,105])],
'M17':[('대법원은 원심의 형이 부당하다고 볼 수 없다고 판단했습니다.',128),('이를 가석방 없는 종신형으로 바꿔 말할 수는 없습니다.',127)]}

def repair(s,source):
 p=s['performance'];s['split']=None
 if source in [19,20]:s['set']='suwon';p['room']='suwon';p['place']='수원'
 if source==3:p['actors']=[a for a in p['actors'] if a['role']!='employee'];s['depiction']='가방을 든 두 강도의 도주. 확인되지 않은 직원의 추격은 제거.'
 if source==26:p['actors']=[a for a in p['actors'] if a['role']=='police'];s['depiction']='익명의 다친 순찰 경찰관만 유지. 은행 직원으로 읽힌 구조 인물은 제거.'
 if source in [14,130,132]:p['actors']=[];p['props']=[x for x in p['props'] if x['kind']!='flowers'];s['depiction']='빈 업무 의자로 부재를 표현. 특정 동료나 유족의 행위를 재현하지 않음.'
 if re.fullmatch(r'\d{4}',p.get('date','')):p['date']+='년'
 if source==33:s['depiction']='차량 옆에서 가시적인 불꽃으로 증거인멸을 위한 방화 시도를 표현. 전소·점화 장치 작동은 재현하지 않음.'
 return s

def picture():
 from asr import norm
 old=read('fix2_evidence/previous_episode_data.json');d=read('episode_data_v6fix2.json');plan=read('middle_v6fix2.json');words=read('fix2_evidence/final_word_timestamps.json')['words'];original_caps=read('fix_evidence/original_episode_data.json')['captions'];templates={int(s['id'][3:]):s for s in old['shots']};shots=[];captions=[]
 start=d['audio_edits']['new_middle'][0];end=d['audio_edits']['new_middle'][1];delta=d['audio_edits']['suffix_delta_s'];new_end_frame=round(end*30)
 for s in old['shots']:
  if s['start']<round(start*30):
   s=repair(copy.deepcopy(s),int(s['id'][3:]));s['end']=min(s['end'],round(start*30));s['performance']['duration']=s['end']-s['start'];s['beforeTime_s']=(s['start']+s['end'])/60;shots.append(s)
 for c in original_caps:
  if c['startMs']<start*1000 or c['startMs']>=342.195*1000:
   c=copy.deepcopy(c);shift=0 if c['startMs']<start*1000 else delta*1000
   for k in ['startMs','endMs','timestampMs']:c[k]+=shift
   c['text']=display(c['text']);captions.append(c)
 for row in plan:
  mid=row['id'];ss=[s for s in d['sentences'] if s['narrationId']==mid];ww=[w for w in words if w['sentenceId'].startswith(mid+'_')];text=' '.join(s['text'] for s in row['sentences']);expected=norm(text);recognized='';spans=[]
  for w in ww:
   ns=norm(w['word']);recognized+=ns;spans.extend([(w['start'],w['end'])]*len(ns))
  mapping={}
  for block in difflib.SequenceMatcher(None,expected,recognized,autojunk=False).get_matching_blocks():
   for j in range(block.size):mapping[block.a+j]=block.b+j
  beats=BEATS[mid];assert ''.join(norm(t) for t,_ in beats)==expected,(mid,text)
  pos=0;local=[]
  for bi,(text,source) in enumerate(beats):
   n=len(norm(text));hits=[mapping[i] for i in range(pos,pos+n) if i in mapping];assert len(hits)/n>.70,(mid,text)
   a=spans[hits[0]][0];b=spans[hits[-1]][1];f=round(a*30);f=round(ss[0]['start_s']*30) if bi==0 else f
   sources=source if isinstance(source,list) else [source];base=repair(copy.deepcopy(templates[sources[0]]),sources[0]);base.update(id=f'FIX2_{mid}_{bi+1:02}',start=f,end=0,narrationId=mid,purpose=text,facts=list(dict.fromkeys(k for s in row['sentences'] for k in s['facts'])),sourceShots=[f'V6_{i:03}' for i in sources],character_acting=True,action='reaction' if sources[0] in [102,105,111,119,127] else 'performance',beforeTime_s=(templates[sources[0]]['start']+templates[sources[0]]['end'])/60)
   p=base['performance'];p.pop('fire',None);p['date']='';p['clock']=f
   # Carry dates only for the event currently narrated, never an inherited title.
   match=re.search(r'\d{4}년(?:\s*\d{1,2}월)?(?:\s*\d{1,2}일)?',text)
   if match:p['date']=display(match[0])
   if sources[0] in [1,2,12,20,31]:p['date']={1:'2001-12-21',2:'2001-12-21',12:'2001-12-21',20:'2001-12-01'}.get(sources[0],'');p['place']='수원' if sources[0]==20 else '인근 상가 지하' if sources[0]==31 else '은행 지하'
   if len(sources)>1:
    base['split']=[repair(copy.deepcopy(templates[i]),i)['performance'] for i in sources]
    for pi,pp in enumerate(base['split']):
     pp['date']='';pp['place']='';pp.pop('fire',None);pp['clock']=f
     if pp['room']=='court':pp['actors']=[aa for aa in pp['actors'] if aa['role'].startswith('defendant')]
     for aa in pp['actors']:
      if aa['role'].startswith('defendant'):aa['flip']=pi!=0
    base['depiction']='분할 화면: '+' / '.join(templates[i]['depiction'] for i in sources)
   local.append(base)
   # Caption lengths are editorial chunks; timings come from the corresponding words.
   cap_pos=pos;part='';chunks=[]
   for word in re.findall(r'\d{4}년\s+\d{1,2}월(?:\s+\d{1,2}일)?[,.:]?|\S+',text):
    if len(part+' '+word)>24 and part:chunks.append(part);part=word
    else:part=(part+' '+word).strip()
   if part:chunks.append(part)
   for chunk in chunks:
    ln=len(norm(chunk));hh=[mapping[i] for i in range(cap_pos,cap_pos+ln) if i in mapping]
    if hh:captions.append(dict(text=display(chunk),startMs=spans[hh[0]][0]*1000,endMs=(spans[hh[-1]][1]+.04)*1000,timestampMs=spans[hh[0]][0]*1000,confidence=len(hh)/ln,narrationId=mid))
    cap_pos+=ln
   pos+=n
  nextrow=next((n for n in d['narration'] if n['start_s']>ss[-1]['end_s']),None);stop=round(nextrow['start_s']*30) if nextrow else new_end_frame
  for i,s in enumerate(local):
   s['end']=local[i+1]['start'] if i+1<len(local) else stop;assert s['end']>s['start'],s['id'];s['performance']['duration']=s['end']-s['start']
   for pp in s.get('split') or []:pp['duration']=s['end']-s['start']
  shots.extend(local)
 shift=new_end_frame-round(342.195*30)
 for s in old['shots']:
  if s['start']>=round(342.195*30):
   s=repair(copy.deepcopy(s),int(s['id'][3:]));s['beforeTime_s']=(s['start']+s['end'])/60;s['start']+=shift;s['end']+=shift;s['performance']['clock']+=shift;shots.append(s)
 shots[-1]['end']=d['durationInFrames'];shots[-1]['performance']['duration']=shots[-1]['end']-shots[-1]['start']
 for i,s in enumerate(shots):s['index']=i;s.pop('match',None)
 assert all(a['end']==b['start'] for a,b in zip(shots,shots[1:]));assert shots[0]['start']==0
 captions.sort(key=lambda c:c['startMs'])
 for a,b in zip(captions,captions[1:]):a['endMs']=min(a['endMs'],b['startMs'])
 d.update(shots=shots,captions=captions);save('episode_data_v6fix2.json',d);save('shots_v6fix2.json',{k:d[k] for k in ['fps','shots','narration','sentences','captions']});save('captions_v6fix2.json',captions)
 def stamp(ms):
  ms=round(ms);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (P/'subtitles_v6fix2.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs'])} --> {stamp(c['endMs'])}\n{c['text']}" for i,c in enumerate(captions))+'\n')
 # Keep the outer narration verbatim; the middle is the reviewed replacement text.
 factcells={}
 for line in (P.parent/'facts.md').read_text().splitlines():
  cells=[v.strip() for v in line.split('|')]
  if len(cells)>2 and re.fullmatch('F[0-9]+',cells[1]):factcells[cells[1]]=cells[2]
 script=['# LF2 v6fix2 · CEO Decision A','','앞부분 N001–N021 및 끝부분 N056–N057 음성은 원본 PCM 샘플 보존. 중간 M01–M17만 같은 Supertonic 3 M1 설정으로 교체.','']
 for n in d['narration']:
  script +=[f"## {n['id']} · {n['start_s']:.3f}–{n['end_s']:.3f}s",'',n['text'],'',*['- '+f+': '+factcells.get(f,'../facts.md 참조') for f in n['facts']],'']
 (P/'script_v6fix2.md').write_text('\n'.join(script)+'\n')
 alignment=['# LF2 v6fix2 내레이션–화면 정합표','','제작 MATCH·PASS를 부여하지 않음. 사건 장면은 해당 F행의 확인된 사실을 재구성하며, 동기·범행 중 대사·미확인 장소를 추가하지 않음.','','| 숏 | 시간(초) | 발화 | 그림 | 근거 |','|---|---|---|---|---|']
 for s in shots:alignment.append(f"| {s['id']} | {s['start']/30:.3f}–{s['end']/30:.3f} | {s['purpose']} | {s['depiction']} | {', '.join(s['facts'])} |")
 (P/'alignment_v6fix2.md').write_text('\n'.join(alignment)+'\n')
 oldn={n['id']:n for n in old['narration']};diff=[]
 for row in plan:
  diff.extend([f"### {row['id']} ← {', '.join(row['before'])}",'','```diff'])
  diff +=['- '+oldn[n]['text'] for n in row['before']]+['+ '+s['text'] for s in row['sentences']]+['```','']
  for s in row['sentences']:diff.append('+ '+s['text']+'\n  근거 대조: '+'; '.join(f+': '+factcells[f] for f in s['facts']))
  diff.append('')
 diff +=['### 삭제한 반복 구간','- N041(F32): 구형 직후 감사 발언 소개. 핵심 선고 이유·절차·일자에 해당하지 않는 부가 일화라 삭제.','- N042: 앞뒤에 반복되는 판단·형량 예고 질문 삭제. F37/F40의 판단·선고 내용은 M10–M12에 유지.','- N034/N039/N046/N051/N053의 반복 논평·질문은 사실 내용만 M06/M08/M12/M14/M16에 통합.']
 (E/'script_before_after.md').write_text('\n'.join(diff)+'\n')
 print('PICTURE',len(shots),'shots;',sum(bool(s.get('split')) for s in shots),'split scenes;',d['audioDuration'],'s')

if __name__=='__main__':
 if 'assemble' in sys.argv:assemble()
 else:picture()
