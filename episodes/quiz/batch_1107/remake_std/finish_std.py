"""Use the existing factory facts/review gates; record raw results, never approve."""
from pathlib import Path
import json,hashlib,sys,re,subprocess,math,difflib
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path.insert(0,str(W/'factory'));sys.path.insert(0,str(W/'episodes/quiz/v52_q013_q014_support'))
from review_gates import load_review,evaluate,write_json,korean_number
from gates import fact_gate,finalize_review
from alignment_word_clock import character_clock
def load(p):return json.loads(Path(p).read_text())
def dump(p,x):write_json(p,x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):return subprocess.run(list(map(str,args)),check=True)
def norm(s):
 s=re.sub(r'(?<=\d),(?=\d)','',s)
 s=re.sub(r'(\d+)m',r'\1미터',s)
 for a,b in [('1억','일억'),('5호선','오호선')]:s=s.replace(a,b)
 return re.sub('[^가-힣]','',re.sub(r'\d+',lambda m:korean_number(m[0]),s))
def wrap(text):
 groups=[]
 for parent in text.split('\n'):
  out=[];line=''
  for w in re.findall(r'(?:사회봉사)\s+\d+시간[가-힣]*[.,]?|(?:징역|집행유예|보호관찰)\s+\d+(?:년|개월)[가-힣]*[.,]?|1억\s+원[가-힣]*[.,]?|\S+',parent):
   assert len(w)<=14,w
   if len(line)+len(w)+bool(line)>14:out.append(line);line=w
   else:line+=(' ' if line else '')+w
  if line:out.append(line)
  groups.append(out)
 if sum(map(len,groups))<=2:return ['\n'.join(line for g in groups for line in g)]
 return ['\n'.join(g[i:i+2]) for g in groups for i in range(0,len(g),2)]
def align(q):
 import mlx_whisper
 p=W/'upload/pkg'/f'{q}_std';c=load(p/'case.json');model=next((Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 ar=mlx_whisper.transcribe(str(p/'mix_master.wav'),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0,word_timestamps=True)
 dump(p/'asr_master.json',ar)
 actual,starts,ends=character_clock(ar,norm);expected=norm(' '.join(u['text'] for u in c['utterances']))
 sm=difflib.SequenceMatcher(None,expected,actual,autojunk=False);mapping={}
 for b in sm.get_matching_blocks():
  for i in range(b.size):mapping[b.a+i]=b.b+i
 offset=0;subs=[]
 for u in c['utterances']:
  assert norm(u['shown'])==norm(u['text']),(q,u)
  pages=wrap(u['shown']);prev=u['start_s']
  for i,page in enumerate(pages):
   size=len(norm(page));ids=[mapping[z] for z in range(offset,offset+size) if z in mapping]
   assert ids,(q,page)
   a=max(u['start_s'],float(starts[min(ids)]));b=min(u['end_s'],float(ends[max(ids)]))
   if i==0:a=u['start_s']
   sub=dict(start_s=a,end_s=max(a+.04,b),text=page,reference=page.replace('\n',' '),parent=u['id'])
   if u['mode']=='answer':sub['emphasis']=('무죄' if q=='q004' else '집행유예 2년')
   subs.append(sub);offset+=size
 for a,b in zip(subs,subs[1:]):a['end_s']=min(a['end_s'],b['start_s'])
 c['subtitles']=subs;dump(p/'case.json',c)
 shots=[]
 court_modes={'first','claim','evidence','harm','demand','recovery','trust','deposit','victim','factor','choices','answer','wife'}
 for i,u in enumerate(c['utterances']):
  mode=u['mode'];loc='court' if mode in court_modes else c['kind'] if mode!='next' else 'next_'+c['next']
  previous=shots[-1] if shots else None
  first=not any(s['location']==loc for s in shots)
  size='wide' if first or mode=='choices' else 'medium' if i%2 else 'medium-wide'
  # Values describe actual stages in Scenes.tsx, not approval or fabricated MATCH.
  action={'snack':'열린 회사 냉장고에서 간식을 꺼내는 성인과 450원 간식·형사법정 대비','amount':'초코파이와 커스터드 실물 소품, 450원·600원, 성인 피고인이 손짓','first':'판사·피고인 투샷, 과거 1심 벌금 5만 원 도장과 반응','lift':'별도 원작 스리랑카 국적 성인 노동자를 벽돌과 산업용 비닐로 결박, 팔레트와 함께 지게차가 서서히 들어 올림','move':'같은 결박 화물을 지게차로 이동, 약 10m의 대표 동작, 피해자 비희화화','reason':'벽돌 작업 중인 노동자·가해자, 업무 미숙이라는 조사된 이유, 피해 비난 없음','harm':'법정 판사·피고인 투샷, 정신적 피해 지적과 저울·도장','pour':'휘발유 붓기 → 불길 성장 → 성인 승객 반응을 같은 구도 안에서 연기','evacuate':'연기 속 성인 승객들이 열린 문 방향으로 대피','charge':'성인 승객과 160명 살인미수 혐의, 사망자 수와 구별','passenger':'신중한 성인 승객 반응, 희화화 없음','assault':'주차장 두 인물, 주먹 동작과 피해자 보호 동작','hurt':'발길질 대표 동작 → 성인 여성 피해자의 부상 반응','trip':'남편의 다리 걸기와 성인 기사의 넘어짐','kick':'아내의 발길질 대표 동작 → 바로 철회, 고어 없음','injury':'성인 피해자가 통증 부위를 감싸는 후속 장면','claim':'법정 투샷, 피고인의 허용받았다는 주장·판사 반응','evidence':'판사·피고인 투샷, 동료들의 간식 관행 진술과 저울','demand':'판사와 피고인 투샷, 1심 검찰 구형 20년은 선고 아님','deposit':'법정 투샷과 법원 공탁 문서, 피고인 태도는 각색','victim':'피해자가 엄벌 의사를 나타내고 판사와 피고인이 반응','recovery':'반성·합의·피해자의 처벌불원, 판사·피고인 투샷과 저울','trust':'판사의 신뢰 침해 지적과 피고인 반응, 도장·저울','factor':'q004는 항소심 절도 고의 쟁점, q005는 합의≠자동결정. 법정 투샷·한 줄 한 샷·저울','choices':'큰 A/B/C 카드·댓글로 골라보세요, 법정 인물 연기','answer':'망치와 3프레임 스냅 줌 → 0.5초 표정 홀드 → 피고인 반응, 정답 카드만 점등','wife':'부부와 판사, 아내의 집행유예와 이후 상고, 정답 강조 유지','next':'다음 사건 카툰과 구독 요청, 별도 엔딩 카드 없음'}[mode]
  shots.append(dict(id=u['id'],start_s=u['start_s'],end_s=u['end_s'],subject=mode,location=loc,shot_size=size,screen_direction='left_to_right',axis_side='A',character_acting=True,action=action,intended_label=action,camera='3-frame snap at act' if i==0 else '3-frame snap at answer' if mode=='answer' else 'locked composition; in-shot acting',actors=[dict(role='original adult toon defendant',acting=True),dict(role='original adult toon victim or judge',acting=True)],facts=[f'F{i+1}'] if mode!='next' else [],graphic=[],CTO_match=None))
 dump(p/'shots.json',dict(shots=shots,subtitles=subs,narration=c['utterances']))
 dump(p/'subtitle_alignment.json',dict(method='Local Whisper word clock; line-level source audio is synthesized separately. Cut only at complete spoken-line boundaries. No producer MATCH.',accuracy=sm.ratio(),reference=expected,actual=actual,clauses=subs))
 print('ALIGNED',q,sm.ratio(),len(subs),flush=True)

def encode(q,rough=False):
 p=W/'upload/pkg'/f'{q}_std';c=load(p/'case.json');x,sr=sf.read(p/'mix_master.wav',dtype='float32')
 # Two narrative impact sounds only, plus subtle functional option accents.
 events=[(0,.035,95),(c['answer_frame']/30,.07,82)]+[(c['choice_frame']/30+i*4/30,.022,fr) for i,fr in enumerate([480,740,980])]
 for at,amp,hz in events:
  start=round(at*sr);n=min(round(sr*.12),len(x)-start);t=np.arange(n)/sr
  y=amp*(np.sin(2*np.pi*hz*t)*np.exp(-t*38)+.25*np.sin(2*np.pi*1250*t)*np.exp(-t*90));x[start:start+n]+=y[:,None]
 sf.write(p/'mix_effects.wav',x,sr,subtype='PCM_24')
 run(['ffmpeg','-v','error','-y','-i',p/('animatic_muted.mp4' if rough else 'video_muted.mp4'),'-i',p/'mix_effects.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-movflags','+faststart',p/('animatic.mp4' if rough else 'video.mp4')])

def sheet(frames,ids,out,cols=6,tw=180):
 th=tw*16//9;im=Image.new('RGB',(cols*tw,math.ceil(len(ids)/cols)*(th+24)),'#171C20');dr=ImageDraw.Draw(im)
 for i,n in enumerate(ids):
  pic=Image.open(frames[n]).convert('RGB').resize((tw,th),Image.Resampling.LANCZOS);x=i%cols*tw;y=i//cols*(th+24);im.paste(pic,(x,y+24));dr.text((x+4,y+3),f'f{n} / {n/30:.3f}s',fill='white')
 im.save(out)

def qa(q):
 p=W/'upload/pkg'/f'{q}_std';c=load(p/'case.json');out=W/'episodes/review_full/shorts'/q/'std';out.mkdir(parents=True,exist_ok=True)
 src=load(p/'research.json')['sources'];rank=load(p/'topic_evidence.json');bible=D/'style.txt'
 bible.write_text((W/'factory/unslop/STYLE_VIDEO.md').read_text()+'\nLatest owner-approved q013 v3 template: 72px/800/black10 centered subtitles, all 2D toon, disclosures only in description. H14: line-boundary 2–3s shots; action/answer snap only. CTO fix1: 2–3s line-boundary low bench / defendant close-up / evidence insert / over-shoulder; no top stamp badges. MOTION_NUMBERS applied to revised shots: hero, anticipation, follow-through, absolute sin/cos ambient; gavel contact 1f before unchanged AAC impact. H10 functional choices explicitly requested.\n')
 reference=W/'upload/v52_q013_n16_v3.mp4'
 cfg=dict(subtitle_band=[.62,.70],topic_criteria=c['reason'],interest_evidence=[dict(kind='search_volume',file=str(p/'topic_evidence.json'),value=rank.get('search_summary'),metric='Naver measured search evidence; relative index, not absolute count'),dict(kind='community',file=str(p/'topic_evidence.json'),value=rank.get('demand_inputs'),metric='YouTube case-matched source performance; not public opinion')],references=[dict(channel='몇년나옴 / owner-approved q013 v3',video=str(reference),metrics=dict(owner_approved='2026-11-06 ㅇㅇ좋아 합격',sha256=sha(reference)),time_s=14,our_time_s=next(u['start_s'] for u in c['utterances'] if u['mode']=='factor' or u['mode']=='recovery'))],style_bible=str(bible),renderers=['2D SVG / q013 v3 FightRig + CourtDynamic'],sources=[dict(s,file=str(W/s['file'])) for s in src],pronunciation_lexicon={'1억':'일억'},tts_cues=c['utterances'],batch_overrides=['Latest owner 11-07 explicitly requests q004/q005 remakes. Previous uploaded/used status is not a new-topic selection. Preserve q018/q020/q022 outputs.','H14 supersedes earlier 1–1.5s court cuts / rapid reaction chain. Base shot 2–3s, no mid-line cuts, snaps only act and answer.','H9 no on-screen disclosure; description only. Demand versus sentence stays factual.','H10 functional colored choices, >=2s selection and correct-card-only illumination explicitly requested.','CTO fix1: original narration, subtitle data and AAC payload/timing copied byte-identically. Revised courtroom framings; top labels removed; approved hooks, ABC cards, answer frames and CTA retained.','No producer PASS or MATCH, no number assignment, no uploads. All A1–H14 fail conditions retained; raw diagnostics are never self-waived.'])
 dump(p/'review_inputs.json',cfg)
 context=load_review(p/'video.mp4',out,p/'shots.json',p/'script.md',p/'facts.md',review_inputs=p/'review_inputs.json',format='shorts')
 gates=evaluate(context);gates['factory_facts']=fact_gate(p,q)
 root=out.parent;sheet(context.images,list(range(0,context.frames,15)),root/'std_2fps.png',cols=6,tw=180)
 sheet(context.images,list(range(0,context.frames,30)),root/'std_1fps.png',cols=6,tw=180)
 sheet(context.images,list(range(0,min(91,context.frames),5)),root/'std_0-3s.png',cols=5,tw=216)
 sheet(context.images,list(range(min(91,context.frames))),root/'std_action_consecutive.png',cols=7,tw=180)
 sheet(context.images,list(range(c['answer_frame'],min(c['answer_frame']+30,context.frames))),root/'std_answer_consecutive.png',cols=6,tw=180)
 for path in [root/'std_1fps.png',root/'std_0-3s.png',root/'std_2fps.png',root/'std_action_consecutive.png',root/'std_answer_consecutive.png']:context.artifacts[str(path)]=sha(path)
 report=finalize_review(context,gates)
 report.update(qid=q,number=None,video_sha256=sha(p/'video.mp4'),producer_status='RENDERED_FOR_CTO_REVIEW',ready=False,ceo_review_eligible=False,owner_delivery_ready=False,all_A1_H14_items_are_fail_conditions=True,template=dict(path=str(reference),sha256=sha(reference)),answer_window=[c['answer_frame']/30,c['cta_frame']/30],cta_window=[c['cta_frame']/30,c['n']/30],planned_publish_time='CTO 검토 후 별도 확정 · 업로드/예약 없음',limits=[*report['limits'],'CTO 전체 30fps 시각 검수·사실 의미/출처 독립성·음화 MATCH·CEO 검수 대기.','자동 진단 원문을 유지하며 제작자 PASS/MATCH는 없음.'])
 dump(p/'qa.json',report)
 print(json.dumps(dict(qid=q,defects=report['defects'],input_missing=report['input_missing'],video_sha256=report['video_sha256']),ensure_ascii=False),flush=True)

if __name__=='__main__':
 q,mode=sys.argv[1:3]
 if mode=='rough_audio':encode(q,True)
 else:{'align':align,'encode':encode,'qa':qa}[mode](q)
