#!/usr/bin/env python3
# Self-contained LF2 Terra remake: original vector-like 2D tableau animation.
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import subprocess, json, math, shutil, textwrap

ROOT=Path(__file__).resolve().parent
W,H=1920,1080
FPS=30
AUDIO=Path('/Users/isaac/projects/verdict-kr/work/episodes/lf2_daejeon_bank/cartoon_v6/public/voice_v6fix2.wav')
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
BOLD='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
try: font=lambda n:ImageFont.truetype(FONT,n)
except: font=lambda n:ImageFont.truetype(BOLD,n)

# Narration-based, factual beats; scenes intentionally show only substantiated actions.
SHOTS=[
 ('T01',0,14,'garage','총격이 있었고 출납과장이 숨졌습니다.', 'arrival'),
 ('T02',14,24,'garage','2001-12-21 오전 10시께 대전 둔산동 은행 건물 지하주차장.', 'block'),
 ('T03',24,36,'garage','현금 운송 관계자 3명과 검은 그랜저XG, 복면 2명.', 'aim'),
 ('T04',36,48,'garage','두 가방 중 한 개, 현금 3억 원이 빼앗겼습니다.', 'bag'),
 ('T05',48,67,'suwon','2001-12-01 수원에서 훔친 차량과 앞선 권총 강탈 사건.', 'road'),
 ('T06',67,84,'garage','CCTV가 없던 현장. 인근 상가 지하에 차량을 버린 뒤, 방화 시도가 보도됐습니다.', 'evidence'),
 ('T07',84,102,'lab','마스크와 손수건은 남았지만 당시 감식으로 DNA를 검출하지 못했습니다.', 'lab'),
 ('T08',102,122,'archive','초기 조사와 2011년 중요미제사건 전담수사팀의 자료 인수.', 'archive'),
 ('T09',122,138,'law','2015년 태완이법 시행 뒤 수사는 계속됐습니다. 2017년 재감식이 돌파구가 됩니다.', 'dna'),
 ('T10',138,156,'lab','DNA는 2015년 충북 불법게임장 담배꽁초 자료와 이어졌습니다.', 'compare'),
 ('T11',156,173,'investigation','2022년 B를 특정하고 8월 25일 검거. B 진술 뒤 A도 체포.', 'arrest'),
 ('T12',173,190,'court','서로 다른 총격·돈 분배 주장이 법정에서 맞섰습니다.', 'testimony'),
 ('T13',190,210,'court','2023-01-16 검찰 구형과 2023-02-17 1심 선고를 구별합니다.', 'verdict1'),
 ('T14',210,230,'court','2023-08-18 항소심은 두 사람 모두 무기징역을 선고했습니다.', 'verdict2'),
 ('T15',230,246,'court','2023-12-14 대법원 상고 기각으로 무기징역이 확정됐습니다.', 'final'),
 ('T16',246,259,'office','돌아오지 못한 사람의 빈 일자리. 범인의 표정이 아닌 상실을 남깁니다.', 'empty'),
]
PALETTE={'ink':'#17242c','paper':'#e7e0cf','red':'#c54c45','blue':'#2e5f77','gold':'#d6a74a','concrete':'#4b5660','light':'#f5ddb1','black':'#202428','skin':'#b87d62','suit':'#30495c','coat':'#8ba09f','floor':'#263039'}

def rgba(c):
 return c

def line(d,pts,fill,w=12): d.line(pts, fill=fill, width=w, joint='curve')
def poly(d,pts,fill,outline=None,w=1): d.polygon(pts,fill=fill); outline and d.line(pts+[pts[0]],fill=outline,width=w,joint='curve')
def txt(d,xy,s,size=38,fill='white',anchor=None,stroke=0): d.text(xy,s,font=font(size),fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=PALETTE['ink'])

def background(d,kind):
 if kind in ('garage','suwon'):
  d.rectangle((0,0,W,H),fill=PALETTE['concrete']); d.rectangle((0,650,W,H),fill=PALETTE['floor'])
  for x in (180,770,1430):
   d.rectangle((x,90,x+135,770),fill='#69747b'); d.rectangle((x+18,90,x+42,770),fill='#879197')
  for y in (230,430): line(d,[(0,y),(W,y-65)],'#788288',7)
  line(d,[(0,930),(W,720)],'#89959a',7)
 elif kind in ('lab','archive','investigation'):
  d.rectangle((0,0,W,H),fill='#24414d'); d.rectangle((0,700,W,H),fill='#183039')
  for x in range(100,1900,240): d.rectangle((x,80,x+110,620),fill='#3c6671'); d.rectangle((x+10,95,x+100,610),outline='#a9c4bf',width=5)
 elif kind in ('court','law'):
  d.rectangle((0,0,W,H),fill='#433833'); d.rectangle((0,760,W,H),fill='#2b2525')
  d.rectangle((0,100,W,170),fill='#785e42'); d.rectangle((100,180,W-100,220),fill='#a8865b')
 elif kind=='office':
  d.rectangle((0,0,W,H),fill='#8da5a1'); d.rectangle((0,750,W,H),fill='#705e50')
  for x in (130,1280): d.rectangle((x,80,x+420,480),fill='#ceded6'); d.rectangle((x+30,110,x+390,450),fill='#a8ced5')

def car(d,x,y,s=1,black=True):
 body='#20282d' if black else '#e2e6e4'; poly(d,[(x,y),(x+430*s,y),(x+500*s,y+80*s),(x+455*s,y+170*s),(x+70*s,y+170*s),(x,y+90*s)],body,'#111820',8)
 poly(d,[(x+110*s,y),(x+300*s,y),(x+365*s,y+78*s),(x+70*s,y+78*s)],'#708b98','#111820',6)
 for cx in (x+110*s,x+390*s): d.ellipse((cx-42*s,y+120*s,cx+42*s,y+204*s),fill='#15191d',outline='#a6afb1',width=8)
 d.rectangle((x+20*s,y+90*s,x+65*s,y+120*s),fill='#f2ce72')

def bag(d,x,y,s=1,tilt=0):
 # handle connects visibly to bag rim
 d.rounded_rectangle((x,y,x+150*s,y+100*s),radius=13*s,fill='#72584a',outline='#1b2429',width=9)
 d.arc((x+38*s,y-42*s,x+112*s,y+35*s),180,360,fill='#1b2429',width=12)
 d.line((x+38*s,y+5*s,x+112*s,y+5*s),fill='#1b2429',width=5)

def person(d,x,y,s,role,pose='stand',face='neutral',flip=False):
 # Full body: pelvis, torso mass, articulated limbs, planted shoes, with hand endpoints.
 col=PALETTE['suit'] if role in ('A','B') else ('#5f7882' if role=='victim' else '#473d55')
 if role=='judge': col='#24252b'
 if role=='analyst': col='#d2d9cf'
 if role=='police': col='#35586b'
 sign=-1 if flip else 1
 hip=(x,y-250*s); shoulder=(x,y-530*s); head=(x+sign*5*s,y-660*s)
 # shadow and grounded shoes
 d.ellipse((x-85*s,y-22*s,x+105*s,y+18*s),fill='#152027')
 # legs with knees, varied pose
 if pose=='fall':
  line(d,[hip,(x+sign*125*s,y-155*s),(x+sign*260*s,y-80*s)],col,48); line(d,[hip,(x-sign*115*s,y-120*s),(x-sign*230*s,y-70*s)],col,48)
  shoulder=(x+sign*95*s,y-360*s); head=(x+sign*195*s,y-420*s)
 else:
  knee1=(x-sign*48*s,y-115*s); foot1=(x-sign*70*s,y)
  knee2=(x+sign*55*s,y-120*s); foot2=(x+sign*100*s,y)
  if pose=='step': knee2=(x+sign*130*s,y-150*s); foot2=(x+sign*210*s,y-85*s)
  line(d,[hip,knee1,foot1],col,48); line(d,[hip,knee2,foot2],col,48)
  for fx,fy in (foot1,foot2): line(d,[(fx-25*s,fy),(fx+45*s,fy)],'#182228',28)
 # pelvis and torso
 d.ellipse((hip[0]-75*s,hip[1]-55*s,hip[0]+75*s,hip[1]+55*s),fill=col,outline=PALETTE['ink'],width=7)
 poly(d,[(shoulder[0]-115*s,shoulder[1]),(shoulder[0]+115*s,shoulder[1]),(hip[0]+68*s,hip[1]),(hip[0]-68*s,hip[1])],col,PALETTE['ink'],7)
 # arms are connected shoulder->elbow->hand; action poses retain held prop contact
 if pose=='aim':
  a1=(shoulder[0]+sign*125*s,shoulder[1]+45*s); hand=(x+sign*340*s,y-450*s)
  a2=(shoulder[0]+sign*100*s,shoulder[1]+75*s); hand2=(x+sign*305*s,y-425*s)
 elif pose=='carry':
  a1=(x+sign*140*s,y-390*s); hand=(x+sign*160*s,y-270*s); a2=(x-sign*95*s,y-385*s); hand2=(x-sign*130*s,y-270*s)
 else:
  a1=(x+sign*125*s,y-410*s); hand=(x+sign*155*s,y-255*s); a2=(x-sign*115*s,y-395*s); hand2=(x-sign*150*s,y-270*s)
 line(d,[shoulder,a1,hand],col,40); line(d,[shoulder,a2,hand2],col,40)
 for h in (hand,hand2): d.ellipse((h[0]-21*s,h[1]-21*s,h[0]+21*s,h[1]+21*s),fill=PALETTE['skin'],outline=PALETTE['ink'],width=4)
 # head and focused face orientation
 d.ellipse((head[0]-86*s,head[1]-86*s,head[0]+86*s,head[1]+86*s),fill=PALETTE['skin'],outline=PALETTE['ink'],width=7)
 if role in ('A','B'): # mask without real identity
  d.rectangle((head[0]-82*s,head[1]-10*s,head[0]+82*s,head[1]+60*s),fill='#d8d7cf',outline=PALETTE['ink'],width=5)
 else:
  eyeX=head[0]+sign*25*s
  d.ellipse((eyeX-12*s,head[1]-12*s,eyeX+12*s,head[1]+12*s),fill=PALETTE['ink'])
  if face=='shock': line(d,[(head[0]-30*s,head[1]+45*s),(head[0]+25*s,head[1]+53*s)],PALETTE['ink'],6)
  else: line(d,[(head[0]-25*s,head[1]+45*s),(head[0]+20*s,head[1]+45*s)],PALETTE['ink'],6)
 return {'hand':hand,'hand2':hand2,'head':head}

def gun(d,hand,flip=False):
 s=1; sign=-1 if flip else 1; x,y=hand
 d.rounded_rectangle((min(x,x+sign*118),y-18,max(x,x+sign*118),y+18),8,fill='#21282c',outline='#091216',width=5)
 poly(d,[(x+sign*35,y+15),(x+sign*75,y+15),(x+sign*55,y+72),(x+sign*20,y+72)],'#20272b','#091216',4)
 # Draw the gripping palm over the handle: visible hand-to-prop attachment, not a floating gun.
 d.ellipse((x+sign*22-20,y+10,x+sign*22+20,y+50),fill=PALETTE['skin'],outline=PALETTE['ink'],width=4)

def label(d,title,sub):
 d.rounded_rectangle((55,45,700,160),24,fill='#152b34',outline='#d6a74a',width=4)
 txt(d,(85,70),title,38,'#f5ddb1'); txt(d,(85,116),sub,25,'#dce9e2')

def frame(shot,phase):
 sid,start,end,kind,desc,act=shot
 im=Image.new('RGB',(W,H),PALETTE['ink']); d=ImageDraw.Draw(im); background(d,kind)
 label(d,sid, f'{start:03.0f}–{end:03.0f}s')
 if kind=='garage':
  car(d,190,650,.95,True); car(d,1200,620,.8,False)
  if act in ('arrival','block','aim'):
   a=person(d,820,900,1.12,'A','aim' if phase>0 else 'stand',flip=False)
   v=person(d,1370,910,1.10,'victim','fall' if phase==2 else 'stand','shock',True)
   e=person(d,1710,910,.78,'employee','stand','shock',True)
   if act=='aim':
    # The wide event tableau explicitly preserves the reported two masked people and three bank staff.
    person(d,330,900,.68,'B','stand',flip=False)
    person(d,1500,910,.62,'employee','stand','shock',True)
   if phase>0: gun(d,a['hand']);
   if phase==1: d.polygon([(a['hand'][0]+130,a['hand'][1]),(a['hand'][0]+190,a['hand'][1]-22),(a['hand'][0]+190,a['hand'][1]+22)],fill='#f7cc68')
  elif act=='bag':
   a=person(d,960,910,1.1,'B','carry',flip=True)
   # Handle centre is aligned under the carrying hand; the second bag remains grounded.
   bag(d,a['hand'][0]-68,a['hand'][1]+2,.9); bag(d,1360,808,.72)
   person(d,1420,910,.95,'employee','stand','shock',True)
  elif act=='evidence':
   car(d,720,700,.95,True); d.rectangle((970,490,1120,610),fill='#e5e1d1',outline='#152027',width=8); d.ellipse((1010,520,1090,575),fill='#789199'); txt(d,(930,630),'CCTV 없음',35,'#f5ddb1')
 elif kind=='suwon':
  car(d,850,680,1.2,True); person(d,610,900,1,'A','step',flip=False); txt(d,(260,290),'2001-12-01  수원',54,'#f5ddb1'); txt(d,(260,360),'시동이 켜진 채 주차된 차량',33,'#dce9e2')
  if phase==2: txt(d,(260,450),'※ 은행 주차장 재사용 아님',29,'#efc679')
 elif kind in ('lab','investigation'):
  d.rounded_rectangle((690,530,1260,830),25,fill='#d7ddd2',outline='#101d22',width=11); d.rectangle((760,600,1190,770),fill='#9ec1c2')
  an=person(d,1450,910,1.05,'analyst','carry',flip=True); de=person(d,390,910,.95,'police','stand',flip=False)
  if act in ('lab','compare','dna'):
   d.ellipse((860,620,1030,760),outline='#24414d',width=18); d.arc((885,640,1010,735),20,330,fill='#c54c45',width=14); txt(d,(810,815),'마스크 · 손수건',31,'#f5ddb1')
  if act=='arrest': txt(d,(760,200),'2022-08-25  B 검거 → 진술 → A 체포',39,'#f5ddb1')
 elif kind=='archive':
  for i,x in enumerate((260,620,980,1340)):
   d.rectangle((x,420,x+230,790),fill='#b4a48b',outline='#17242c',width=8); txt(d,(x+28,505),['2001','2011','기록','증거'][i],40,'#17242c')
  person(d,1660,910,.95,'police','carry',flip=True); txt(d,(240,250),'2011-12  중요미제사건 전담수사팀 인수',45,'#f5ddb1')
 elif kind=='law':
  d.rectangle((520,250,1400,780),fill='#e3dcc8',outline='#201d1d',width=12); txt(d,(960,390),'2015년',70,'#243440',anchor='mm'); txt(d,(960,500),'태완이법 시행',70,'#243440',anchor='mm'); txt(d,(960,620),'살인죄 공소시효 폐지',39,'#c54c45',anchor='mm')
 elif kind=='court':
  d.rectangle((460,460,1460,590),fill='#74583d',outline='#201d1d',width=10)
  # Keep the judge's full head inside the safe frame rather than cropping it at top.
  judge=person(d,960,790,.95,'judge','stand')
  if act=='testimony':
   person(d,520,925,.95,'A','stand',flip=False); person(d,1420,925,.95,'B','stand',flip=True); txt(d,(960,300),'서로 다른 주장',48,'#f5ddb1',anchor='mm')
  elif act=='verdict1':
   txt(d,(960,260),'2023-01-16  검찰 구형',43,'#f5ddb1',anchor='mm'); txt(d,(960,330),'2023-02-17  1심: A 무기 · B 20년',39,'#dce9e2',anchor='mm')
  elif act=='verdict2':
   person(d,650,955,.58,'A','stand',flip=False); person(d,1270,955,.58,'B','stand',flip=True)
   txt(d,(960,280),'2023-08-18  항소심',52,'#f5ddb1',anchor='mm'); txt(d,(960,355),'A · B  모두 무기징역',55,'#efc679',anchor='mm')
  elif act=='final':
   person(d,650,955,.58,'A','stand',flip=False); person(d,1270,955,.58,'B','stand',flip=True)
   txt(d,(960,280),'2023-12-14  대법원',52,'#f5ddb1',anchor='mm'); txt(d,(960,355),'상고 기각 · 무기징역 확정',48,'#efc679',anchor='mm')
 elif kind=='office':
  d.rectangle((900,500,1290,780),fill='#596b70',outline='#17242c',width=12); d.rectangle((970,370,1220,520),fill='#5f7882',outline='#17242c',width=11); d.rectangle((780,780,1500,825),fill='#3e332e')
  txt(d,(960,260),'돌아오지 못한 사람의 자리',55,'#f5ddb1',anchor='mm')
 # captions as concise overlay, not prose wall
 wrapped=textwrap.wrap(desc,width=33)
 d.rounded_rectangle((210,910,1710,1035),18,fill='#10191fcc')
 for i,s in enumerate(wrapped[:2]): txt(d,(960,945+i*45),s,35,'#ffffff',anchor='mm')
 return im

def save_scene_images(shots):
 out=ROOT/'frames'; out.mkdir(parents=True,exist_ok=True)
 manifest=[]
 for shot in shots:
  dur=shot[2]-shot[1]
  names=[]
  for phase in range(3):
   p=out/f'{shot[0]}_{phase}.png'; frame(shot,phase).save(p); names.append(str(p))
  manifest.append({'id':shot[0],'start_s':shot[1],'end_s':shot[2],'narration':shot[4],'frames':names})
 (ROOT/'shot_alignment.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 return manifest

def render(manifest):
 # each tableau phase persists, creating actions (prepare->action->settle), with short dissolves.
 concat=ROOT/'timeline.txt'; lines=[]
 for s in manifest:
  total=s['end_s']-s['start_s']; ds=[total*.32,total*.36,total*.32]
  for p,dur in zip(s['frames'],ds): lines += [f"file '{p}'",f'duration {dur:.3f}']
 # repeat final required by concat demuxer
 lines.append(f"file '{manifest[-1]['frames'][-1]}'")
 concat.write_text('\n'.join(lines))
 silent=ROOT/'lf2_terra_remake_1080p_silent.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-vf',f'fps={FPS},format=yuv420p','-c:v','libx264','-preset','medium','-crf','17',str(silent)],check=True)
 final=ROOT/'lf2_terra_remake_1080p.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(AUDIO),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(final)],check=True)
 low=ROOT/'lf2_terra_remake_360p.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(final),'-vf','scale=-2:360','-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','112k',str(low)],check=True)
 # proof: first key event, evidence, verdict scenes with their authentic narration ranges.
 proof=ROOT/'lf2_terra_proof.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-ss','14','-to','48','-i',str(final),'-ss','122','-to','156','-i',str(final),'-ss','190','-to','230','-i',str(final),'-filter_complex','[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]','-map','[v]','-map','[a]','-c:v','libx264','-crf','17','-c:a','aac','-b:a','192k',str(proof)],check=True)

def sheet(manifest):
 # readable storyboard contact sheet: one representative frame per shot, ID/time/narration linked.
 thumbW,thumbH=480,270; canvas=Image.new('RGB',(thumbW*2, (thumbH+105)*8),(20,30,35)); d=ImageDraw.Draw(canvas)
 for i,s in enumerate(manifest):
  im=Image.open(s['frames'][1]).resize((thumbW,thumbH))
  x=(i%2)*thumbW;y=(i//2)*(thumbH+105); canvas.paste(im,(x,y)); dd=ImageDraw.Draw(canvas)
  txt(dd,(x+15,y+thumbH+12),f"{s['id']}  {s['start_s']:.0f}–{s['end_s']:.0f}s",25,'#f5ddb1'); summary=textwrap.wrap(s['narration'],width=30)
  for j,line_ in enumerate(summary[:2]): txt(dd,(x+15,y+thumbH+48+j*24),line_,18,'#ffffff')
 canvas.save(ROOT/'lf2_terra_frame_sheet.png')

def report(manifest):
 md=['# Terra remake delivery','', '새 원화/연기: 관절·골반·무게 중심·접지·소품 접촉을 갖춘 독창적 2D 장면. 각 숏은 준비→행동→정착 3개 포즈로 구성했다.','', '|샷|시간|발화/화면 연결|','|---|---|---|']
 for s in manifest: md.append(f"|{s['id']}|{s['start_s']:.0f}–{s['end_s']:.0f}s|{s['narration']}|")
 md+=['','잔여 한계: 인물은 비식별 2D 도상이며, 정지 포즈 간 디졸브 기반의 제한된 동작이다. 청감·연속 재생은 자동 stream 검증만 했고 사람의 전편 연속 청취는 수행하지 않았다.']
 (ROOT/'alignment_and_limits.md').write_text('\n'.join(md))

if __name__=='__main__':
 if not AUDIO.exists(): raise SystemExit(f'missing audio: {AUDIO}')
 m=save_scene_images(SHOTS); sheet(m); report(m); render(m)
 print('RENDERED',len(m),'shots',sum(x[2]-x[1] for x in SHOTS),'seconds')
