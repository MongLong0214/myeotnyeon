"""Edit decisions, captions and full script for the N18 middle-act rewrite."""
from pathlib import Path
import json,re,sys,copy,math,hashlib
HERE=Path(__file__).resolve().parent;W=HERE.parents[4];E=W/'episodes/v4/n18/cartoon_v6';FPS=30
sys.path.insert(0,str(HERE.parent/'n18_v6'))
from audio import norm
from prepare import wordmap
old=json.loads((E/'episode_data_v6fix.json').read_text())
orig=json.loads((E/'episode_data.json').read_text());original_shots={s['id']:s for s in orig['shots']}
audio=json.loads((E/'narration_v6fix2.json').read_text());takes={r['id']:r for r in json.loads((E/'asr_v6fix2_middle.json').read_text())}
A,B=audio['old_picture_frames'];D=audio['removed_frames'];F=old['durationInFrames']-D
old_narr=json.loads((E/'narration.json').read_text())['items'];old_nid={}
for n in old_narr:old_nid.setdefault(n['narrationId'],n['start'])
shots=[];joins=[]
def add(s,a=None,b=None,drawing=None,id=None,shift=0,visual_start=None):
 row=copy.deepcopy(s);a=s['start'] if a is None else a;b=s['end'] if b is None else b
 row.update(id=id or s['id'],start=a-shift,end=b-shift,start_s=(a-shift)/30,end_s=(b-shift)/30,sourceStart=a if visual_start is None else visual_start,sourceEnd=(b if visual_start is None else visual_start+b-a),reference_s=a/30,reference_end_s=b/30,
 sourcePicture='v6fix',review='EXTERNAL_REVIEW_PENDING')
 if drawing:row['drawing']=drawing
 row['action']=row['drawing'];row['index']=len(shots)
 shots.append(row);return row
# Early-act picture corrections, with unchanged narration and exact source timing.
for s in old['shots']:
 if s['start']>=A:break
 id=s['id']
 if id=='H007':
  row=add(s,drawing='report_wide');row['shot_size']=row['size']='wide';row['shows']='보고하는 부중대장과 듣는 중대장, 두 사람 사이 책상을 함께 보여 주는 설정 와이드.'
 elif id=='H028':
  for hid,drawing,size in [('H028','fallen','wide'),('H029','patient_reverse','medium')]:
   source=original_shots[hid];row=add(source,drawing=drawing);row['source_ids']=[hid];row['shot_size']=row['size']=size;row['shows']='쓰러진 훈련병을 바라보는 동료의 시선과 역방향 반응.'
  # Keep the same scene across the clause into the police finding, then cut to the confirmed later transfer.
  boundary=next(c['start'] for c in old['captions'] if c['shotId']=='H031' and c['start']>original_shots['H031']['start'])
  row=add(s,a=original_shots['H030']['start'],b=boundary,drawing='delay',id='H030');row['source_ids']=['H030','H031'];row['text']=' '.join(original_shots[x]['text'] for x in ['H030','H031']);row['shows']='쓰러진 사람과 간부의 시선 관계. 특정 응급처치를 새로 만들지 않는다.'
  row=add(s,a=boundary,b=original_shots['H032']['end'],drawing='medical_transfer',id='H031B',visual_start=0);row['location']='gangneung';row['source_ids']=['H031','H032'];row['facts']=list(dict.fromkeys(s['facts']+['F13','F16']));row['shows']='뒤이은 병원 이송(F16)의 재현으로 전환. 지체 당시 즉시 이송됐다고 표현하지 않도록 자막에 이후 이송임을 표시.'
 elif id=='H031':continue
 elif id=='H046':
  row=add(s,drawing='medical_transfer',visual_start=0);row['location']='gangneung';row['facts']=list(dict.fromkeys(row['facts']+['F16']));row['shows']='사인 보도에 이미 확인된 병원 이송(F16)을 연결. 어머니와 혼동되는 일반 독자 인물을 제거.'
 elif id=='H047':
  row=add(s,drawing='mother_letter');row['shows']='기존 청록색 옷과 짙은 머리의 어머니가 공개편지를 쓰는 재구성. 첫 통화 내용은 편지에 기록된 것으로만 전달.'
 else:
  row=add(s)
  if id in ['H044']:row['facts']=list(dict.fromkeys(row['facts']+['E05']))
# Authorized middle-act sentences, individually matched to adopted facts.
new_narr=[];new_caption=[]
def display(text):
 return re.sub(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',lambda m:f'{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}',text)
for r in audio['items']:
 base=audio['replace_seconds'][0]+r['start'];onset=wordmap(r,takes[r['id']]);duration=r['duration']
 f=round(base*30);nextrow=audio['items'][audio['items'].index(r)+1] if audio['items'].index(r)+1<len(audio['items']) else None
 end=round((audio['replace_seconds'][0]+nextrow['start'])*30) if nextrow else B-D
 before=r['before'];reference=old_nid[before[0]]
 common=dict(id=r['id'],start=f,end=end,start_s=f/30,end_s=end/30,sourceStart=0,sourceEnd=end-f,sourcePicture='new middle',reference_s=reference,reference_end_s=reference+(end-f)/30,source_ids=before,subject=r['id'],facts=list(dict.fromkeys(r['facts']+r.get('visual_facts',[]))),text=r['text'],shows=r['check'],drawing=r['drawing'],location='court' if 'court' in r['drawing'] or 'supreme' in r['drawing'] else 'ground',shot_size='wide' if any(w in r['drawing'] for w in ['wide','cut_','run','march','medical']) else 'medium',character_acting=True,axis_side='audience side of action axis',screen_direction='right',transition='hard cut',review='EXTERNAL_REVIEW_PENDING',narrationId=r['id'],index=len(shots))
 if r['id']=='M013':common['location']='gangneung'
 if r['id']=='M014':common['location']='supreme'
 cuts=[]
 if r['id']=='M010':cuts=[('피해자별','cut_individual')];common['drawing']='march'
 if r['id']=='M011':cuts=[('부중대장은','court_deputy')];common['drawing']='court_commander'
 if r['id']=='M014':cuts=[('중대장의','court_commander')]
 if cuts:
  splittext,newdrawing=cuts[0];pos=norm(r['text']).find(norm(splittext));split=max(f+8,min(end-8,round((base+onset(max(0,pos)))*30)))
  first=dict(common,end=split,end_s=split/30,sourceEnd=split-f,index=len(shots),action=common['drawing'],text=r['text'].split(splittext,1)[0].rstrip(', '));shots.append(first)
  second=dict(common,id=r['id']+'B',start=split,start_s=split/30,sourceStart=split-f,sourceEnd=end-f,drawing=newdrawing,action=newdrawing,index=len(shots),text=splittext+r['text'].split(splittext,1)[1]);shots.append(second)
 else:common['action']=common['drawing'];shots.append(common)
 new_narr.append(dict(r,id=r['id'],narrationId=r['id'],start=base,end=base+duration,start_s=base,end_s=base+duration,beat='fact'))
 words=r['text'].split();chunks=[];chunk=''
 for w in words:
  if chunk and len(chunk+' '+w)>25:chunks.append(chunk);chunk=w
  else:chunk+=(' ' if chunk else '')+w
 if chunk:chunks.append(chunk)
 pos=0
 for j,text in enumerate(chunks):
  cf=f if j==0 else max(f,min(end-1,round((base+onset(pos))*30)))
  if new_caption and new_caption[-1].get('sentenceId')==r['id']:new_caption[-1]['end']=cf;new_caption[-1]['endMs']=cf/30*1000
  new_caption.append(dict(text=display(text),start=cf,end=end,startMs=cf/30*1000,endMs=end/30*1000,sentenceId=r['id'],shotId=r['id']))
  pos+=len(norm(text))
# Unchanged outside narration, shifted exactly by the removed frame count.
for s in old['shots']:
 if s['start']<B:continue
 if s['id']=='H149':continue
 if s['id']=='H147':
  row=add(s,b=old['durationInFrames'],shift=D);row['source_ids']=['H147','H148','H149','H150'];row['facts']=list(dict.fromkeys(row['facts']+['C06','D05','J12']));row['shows']='같은 부모가 용산역 분향소에서 조문객을 맞고 고개를 숙인다. 마지막 책임 발화까지 한 숏으로 유지해 H149 중복 경계를 제거.'
 elif s['id']=='H144':
  row=add(s,drawing='mother_letter',shift=D);row['shows']='같은 어머니가 쓴 공개편지의 수료생·아들 부재 대목. 실제 수료식 현장에서 글을 쓰는 행위로 특정하지 않는 편지 재구성.'
 else:row=add(s,shift=D)
# Preserve exact picture clocks, including the original collapse and the continuous parents' scene.
for i,s in enumerate(shots):s['index']=i;s['size']=s['shot_size'];s.pop('angle_deg',None);s.pop('review_note',None)
assert shots[0]['start']==0 and shots[-1]['end']==F
assert all(a['end']==b['start'] for a,b in zip(shots,shots[1:]))
caption=[]
for c in old['captions']:
 if A<=c['start']<B:continue
 c=copy.deepcopy(c)
 if c['start']>=B:
  for key in ['start','end']:c[key]-=D
  c['startMs']=c['start']/30*1000;c['endMs']=c['end']/30*1000
 if c['shotId']=='H047':c['text']=c['text'].replace('어머니 편지에는','어머니의 공개편지에는')
 if c['shotId']=='H049':c['text']='[어머니 공개편지에 기록된] 아들이 쓰러졌다는 전화.'
 if c['shotId']=='H135' and '07-01' in c['text']:c['text']='혹서기 관리 시작일 07-01→06-01'
 elif c['shotId']=='H135':c['text']='관리 기간 확대.'
 if c['shotId']=='H136':c['text']='종료일 08-31 유지.'
 if c['shotId']=='H031' and c['start']>=next(s['start'] for s in shots if s['id']=='H031B'):c['text']='[뒤이은 병원 이송] '+c['text']
 caption.append(c)
caption=sorted(caption+new_caption,key=lambda c:c['start'])
narr=[]
for n in old_narr:
 if n['narrationId']>='N035' and n['narrationId']<='N063':continue
 n=copy.deepcopy(n)
 if n['start']>=audio['replace_seconds'][1]:n['start']-=D/30;n['end']-=D/30
 n['start_s']=n['start'];n['end_s']=n['end'];narr.append(n)
narr=sorted(narr+new_narr,key=lambda n:n['start_s'])
for s in shots:
 if s['sourcePicture']=='v6fix':
  lo=round(s['reference_s']*30);hi=round(s['reference_end_s']*30)
  s['text']=' '.join(o['text'] for o in orig['shots'] if o['end']>lo and o['start']<hi)
data=dict(fps=30,durationInFrames=F,duration_s=F/30,shots=shots,captions=caption,narration=narr,audio='public_v6fix2/mix.wav')
(E/'episode_data_v6fix2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');(E/'shots_v6fix2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# Keep all original script rows outside the authorized act byte-for-byte.
script=(E/'script_v2.md').read_text();out=[];inserted=False
for line in script.splitlines():
 m=re.match(r'\| (N\d+) \|',line)
 if m and 'N035'<=m[1]<='N063':
  if not inserted:
   out.extend(f"| {r['id']} | {r['text']} | {','.join(r['facts'])} | {r['drawing']} | fact |" for r in audio['items']);inserted=True
  continue
 out.append(line)
(E/'script_v6fix2.md').write_text('\n'.join(out)+'\n')
md=['# N18 v6fix2 narration/picture alignment','','Same M1/model/rate; new audio only N035–N063. Outside PCM is sample-identical. No production MATCH or PASS.','','|Shot|Time(s)|Narration / facts|Picture|','|---|---|---|---|']
for s in shots:
 if s['sourcePicture']=='v6fix':
  lo=round(s['reference_s']*30);hi=round(s['reference_end_s']*30)
  s['text']=' '.join(o['text'] for o in orig['shots'] if o['end']>lo and o['start']<hi)
for s in shots:md.append(f"|{s['id']}|{s['start_s']:.3f}–{s['end_s']:.3f}|{s['text']} / {','.join(s['facts'])}|{s['shows']}|")
(E/'alignment_v6fix2.md').write_text('\n'.join(md)+'\n')
# The edit-join list is used to generate the requested before/after frame sheet.
for s in shots[1:]:
 previous=shots[shots.index(s)-1]
 changed=s['sourcePicture']=='new middle' or previous['sourcePicture']=='new middle' or s['start']>=A or s['id'] in ['H007','H008','H028','H029','H030','H031B','H033','H035','H036','H037','H039','H040','H044','H046','H047','H050','H062']
 if changed:joins.append(dict(kind='current join',id=s['id'],before_frame=round(s['reference_s']*30),after_frame=s['start']))
retained={s['source_ids'][0] for s in shots if s['sourcePicture']=='v6fix'}
for s in old['shots'][1:]:
 if A<=s['start']<B or s['id']=='H149' or s['id']=='H031':
  middle=next((n for n in new_narr if s.get('narrationId') in n.get('before',[])),None)
  af=s['start'] if s['start']<A else s['start']-D if s['start']>=B else round(middle['start_s']*30) if middle else A
  if not any(j['before_frame']==s['start'] and j['after_frame']==af for j in joins):
   joins.append(dict(kind='removed/replaced old join',id=s['id'],before_frame=s['start'],after_frame=max(1,min(F-1,af)),mapping='same retained audio time' if not A<=s['start']<B else 'semantic replacement: middle narration rewritten'))
(E/'joins_v6fix2.json').write_text(json.dumps(joins,ensure_ascii=False,indent=2)+'\n')
print('FILM',F,'frames',F/30,'s;',len(shots),'picture shots;',D/30,'s removed;',len(joins),'affected join comparisons')
