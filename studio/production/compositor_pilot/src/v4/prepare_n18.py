"""Build the full-film shot/subtitle manifest from the approved source timeline."""
from pathlib import Path
import json,re,sys
W=Path(__file__).resolve().parents[4]; E=W/'episodes/v4/n18'; D=json.loads((E/'shots.json').read_text()); FPS=30; LEAD=45
sys.path.insert(0,str(W/'episodes/S001'))
import layout
N={x['id']:x for x in D['narration']}
chap={x['id']:x for x in D['chapters']}
# Digits on display, explicit readings in the speech input, as in S001.
lex=json.loads((E/'lex.json').read_text())
def display(s):
 for a,b in lex: s=s.replace(b,a)
 return s

def chunks(s):
 out=[];cur=''
 # Single-line, word-boundary captions. Commas retain natural clause breaks.
 for w in s.split():
  if cur and (len(cur+' '+w)>26 or (cur.endswith(',') and len(cur)>11)):
   out.append(cur);cur=''
  cur=(cur+' '+w).strip()
 if cur:out.append(cur)
 return out
subs=[]
for n in D['narration']:
 start=round(n['t_start']*FPS)+LEAD;end=round(n['t_end']*FPS)+LEAD; cc=chunks(display(n['text']));weights=[layout.weight(c) for c in cc]; tot=sum(weights);at=start
 for i,c in enumerate(cc):
  to=end if i==len(cc)-1 else at+round((end-start)*weights[i]/tot)
  subs.append(dict(from_=at,to=to,text=c,narration=n['id']));at=to
shots=[dict(id='S000',from_=0,dur=45,kind='chapter',art='verdict',chapterTitle='01 연병장',chapterLabel='',date='',lines=[],label='',source='',category='',numeric=False,multiple=False,empty=True)]
for i,s in enumerate(D['shots']):
 nid=s['narration_ids'][-1] if s['narration_ids'] else ''; n=int(nid[1:]) if nid else 0
 c=s['chapter']; kind=s['kind']; text=s['on_screen_text'][0].strip();art='dossier';empty=True;multiple=n>=41;lines=[text];cat='';numeric=False
 if c=='01':
  art='opening' if n in (1,3,4) else 'spatial' if n==2 else 'verdict' if n==7 else 'diagram' if n==8 else 'opening'
  empty=n in (5,6,7);lines=[] if n==1 else ['훈련병 6명'] if n==2 else [text]
 elif c=='04':
  art='diagram' if 39<=n<=48 else 'opening' if n==50 else 'verdict'
 elif c=='03':
  art='diagram' if n in (31,32) else 'verdict' if n in (21,24,33,34,35,36,37) else 'dossier'
 elif c=='05':
  art='diagram' if n==62 else 'opening' if n==63 else 'verdict'
 elif n==16:art='verdict'
 if n in (17,18,19,20,34,35,36,37,52,53,54,55,59,60):
  art='verdict';numeric=True
  vals={17:('중대장 · 1심 검찰 구형',['징역 10년']),18:('부중대장 · 1심 검찰 구형',['징역 7년']),19:('중대장 · 1심 검찰 구형',['징역 10년']),20:('부중대장 · 1심 검찰 구형',['징역 7년']),34:('중대장 · 1심 선고',['징역 5년']),35:('중대장 · 1심',['구형 10년 / 선고 5년']),36:('부중대장 · 1심 선고',['징역 3년']),37:('부중대장 · 1심',['구형 7년 / 선고 3년']),52:('중대장 · 2심 선고',['징역 5년 6개월']),53:('중대장 · 1심보다',['6개월 증가']),54:('부중대장 · 2심 선고',['징역 3년']),55:('부중대장 · 2심',['1심과 같은 형량']),59:('중대장 · 대법원 확정',['징역 5년 6개월']),60:('부중대장 · 확정 상태',['징역 3년'])}
  cat,lines=vals[n]
 if n in (9,12):
  cat='중대장 · 기소 혐의' if n==9 else '부중대장 · 기소 혐의';lines=['학대치사','직권남용 가혹행위']
 # One primary panel; labels preserve attribution and avoid invented evaluation.
 if len(lines)==1 and len(lines[0])>35:
  parts=lines[0].split(' · ');cat=parts[0];lines=[' · '.join(parts[1:])]
 date=''
 if c=='01':date='2024년 5월 23일'
 elif 16<=n<=20:date='1심 결심공판 · 2024년 11월 12일'
 elif c=='03':date='1심 · 2025년 1월 7일'
 elif c=='04' or 52<=n<=55:date='2심 · 2025년 6월 18일'
 elif 57<=n<=59:date='대법원 · 2025년 9월 25일'
 elif n in (60,61):date='2025년 9월 25일 보도 기준'
 label=('재구성 · 개념도 · 실제 배치·범죄 개수 아님' if art=='diagram' else '법정 재구성 · 개념도 · 실제 배치 아님' if art=='verdict' else '재구성 · 개념도 · 실제 배치·거리·축척 아님' if art=='spatial' else '재구성 · 개념도 · 실제 배치 아님' if art=='opening' else '보도 요지 · 직접 그린 기록 카드')
 source='문화일보 · 세계일보 · 경향신문 / 2025.06.18' if n==52 else ''
 if kind=='chapter':lines=[];art='verdict'
 if kind=='credits':lines=[x.strip() for x in text.replace('출처 · ','').split(' · ')];art='verdict'
 shots.append(dict(id=s['id'],from_=s['frame_start']+LEAD,dur=s['frame_end_exclusive']-s['frame_start'],kind=kind,art=art,chapterTitle=c+' '+chap[c]['title'],chapterLabel=c+' / '+chap[c]['title'],date=date,lines=lines,label=label,source=source,category=cat,numeric=numeric,multiple=multiple,empty=empty))
for s in shots:s['from']=s.pop('from_')
film=dict(durationInFrames=D['duration_frames']+LEAD,fps=FPS,shots=shots,subtitles=subs)
Path(__file__).with_name('n18-film.json').write_text(json.dumps(film,ensure_ascii=False,indent=1)+'\n')
(E/'out/n18_v4.srt').write_text(''.join(f"{i}\n{layout.tc(s['from_'])} --> {layout.tc(s['to'])}\n{s['text']}\n\n" for i,s in enumerate(subs,1)))
(E/'out/shot_coverage.json').write_text(json.dumps(dict(source_shots=120,rendered_shots=len(shots),source_ids=[s['id'] for s in D['shots']],max_shot_seconds=max(s['dur'] for s in shots)/FPS,lead_chapter_seconds=1.5),indent=2))
facts=(E/'facts.md').read_text();sources=[]
for line in facts.splitlines():
 if re.match(r'- \*\*S\d+',line):
  name=re.search(r'\*\*S\d+ (.*?) · (.*?)\*\*',line);url=re.search(r'\]\((https?[^)]+)\)',line)
  sources.append(f"{name[1]} · {name[2]}\n{url[1]}")
(E/'out/meta.txt').write_text('[제목]\n얼차려로 숨진 훈련병, 항소심에서 형이 늘었다 — 왜\n\n[설명]\n2024년 5월 23일 군기훈련에서 시작된 사건의 기소, 구형, 선고와 확정 과정을 보도에 근거해 정리했습니다. 검찰 구형과 법원 선고를 구분하고 두 피고인의 재판 경과를 각각 설명합니다.\n\n모든 화면은 직접 그린 SVG 재구성·개념도이며 실제 인물, 현장 배치, 동선, 거리와 다릅니다. 실제 사진·영상·음성은 사용하지 않았습니다. 내레이션은 합성 음성입니다.\n\n중대장에 대한 대법원 판단은 2025년 9월 25일입니다. 부중대장의 확정 상태는 같은 날 보도 기준이며, 확정일을 뜻하지 않습니다. 판결문을 직접 확보한 것이 아니라 보도에 인용된 이유를 정리했습니다.\n\n출처\n'+'\n\n'.join(sources)+'\n\n[태그]\n몇년나옴, 훈련병 사망 사건, 군기훈련, 얼차려, 항소심, 상상적 경합, 실체적 경합, 판결 기록, 재구성, 다큐멘터리\n')
print('frames',film['durationInFrames'],'subtitles',len(subs),'max_caption',max(len(s['text']) for s in subs))
