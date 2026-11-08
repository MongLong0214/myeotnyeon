"""Original drawn reconstruction. Articulated poses, action-specific staging, no legacy images."""
import math,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('.'); W,H=960,540; FPS=15
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
font=ImageFont.truetype(FONT,25); small=ImageFont.truetype(FONT,18); label=ImageFont.truetype(FONT,21)
def ease(t): return (1-math.cos(math.pi*min(1,max(0,t))))/2
def lerp(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def limb(d,a,b,width,c):
 d.line([a,b],fill='#18202a',width=width+3);d.line([a,b],fill=c,width=width)
def ik(a,b,L,side=1):
 dx,dy=b[0]-a[0],b[1]-a[1]; dist=max(.01,math.hypot(dx,dy)); h=math.sqrt(max(0,L*L-dist*dist/4));return ((a[0]+b[0])/2-side*dy/dist*h,(a[1]+b[1])/2+side*dx/dist*h)
def human(d,x,y,scale=1,phase=0,mode='stand',color='#626c55',face=1,mask=False,pack=False,gesture=0,collapse=0,tag=None):
 # Anatomical profile with bent knee/elbow, trouser/shoe/neck/face silhouettes.
 s=scale
 def p(a):
  xx,yy=a
  if collapse:
   # Knees buckle before torso lowers and rolls; final upper body contacts ground.
   yy+=25*ease(collapse/.4)
   if yy<-70:
    theta=-1.37*ease((collapse-.2)/.8);ox,oy=0,-52
    xx,yy=ox+(xx-ox)*math.cos(theta)-(yy-oy)*math.sin(theta),oy+(xx-ox)*math.sin(theta)+(yy-oy)*math.cos(theta)
   else:
    xx+=22*collapse;yy+=12*collapse
  if mode=='run' and yy<-77:xx+=(-yy-77)*.15
  return (x+face*xx*s,y+yy*s)
 skin='#c7a282';outline='#1d2630'; c=color
 walk=mode in ['walk','run']; amp=25 if mode=='walk' else 40; stride=math.sin(phase)*amp if walk else 0
 bob=-abs(math.cos(phase))* (2 if mode=='walk' else 7) if walk else 0
 hip=(0,-77+bob); shoulder=(7,-139+bob)
 for j in [-1,1]:
  theta=phase+(math.pi if j==1 else 0)
  swing=math.sin(theta)
  foot=(math.cos(theta)*amp,-max(0,swing)*(17 if mode=='walk' else 51)) if walk else ((-5 if j==-1 else 9),0)
  knee=ik(hip,foot,43,side=-1)
  limb(d,p(hip),p(knee),round(15*s),c);limb(d,p(knee),p(foot),round(12*s),c)
  d.polygon([p((foot[0]-7,foot[1]-4)),p((foot[0]+14,foot[1]-3)),p((foot[0]+17,foot[1]+3)),p((foot[0]-8,foot[1]+3))],fill='#202629')
 d.polygon([p((-10,-145+bob)),p((16,-144+bob)),p((20,-91+bob)),p((12,-73+bob)),p((-17,-74+bob)),p((-19,-120+bob))],fill=c,outline=outline,width=2)
 d.line([p((-16,-86+bob)),p((19,-86+bob))],fill='#30372d',width=max(2,round(5*s)))
 d.line([p((7,-133+bob)),p((10,-90+bob))],fill='#869075',width=1)
 if pack:
  d.polygon([p((-16,-138+bob)),p((-39,-135+bob)),p((-44,-95+bob)),p((-21,-88+bob))],fill='#414a37',outline='#181e17',width=2)
  d.line([p((-19,-140+bob)),p((10,-134+bob)),p((13,-93+bob))],fill='#bab29a',width=max(2,round(4*s)))
  d.line([p((-38,-123+bob)),p((-23,-122+bob))],fill='#808067',width=2)
 # neck and drawn facial profile, not a sphere head
 d.polygon([p((1,-149+bob)),p((13,-149+bob)),p((12,-135+bob)),p((0,-136+bob))],fill=skin)
 head=[(-9,-171),(1,-180),(16,-177),(20,-164),(25,-159),(21,-154),(20,-145),(8,-142),(-5,-149),(-10,-161)]
 d.polygon([p((a,b+bob)) for a,b in head],fill=skin,outline=outline,width=1)
 d.polygon([p((a,b+bob)) for a,b in [(-10,-161),(-11,-173),(0,-183),(17,-179),(19,-171),(2,-173),(-3,-159)]],fill='#282b2a')
 if mask:d.polygon([p((a,b+bob)) for a,b in [(-8,-177),(17,-177),(22,-151),(19,-143),(1,-145),(-10,-157)]],fill='#323843');d.line([p((10,-165+bob)),p((19,-165+bob))],fill=skin,width=3)
 else:
  eye=p((15,-165+bob));d.ellipse((eye[0]-1,eye[1]-1,eye[0]+1,eye[1]+1),fill=outline)
  d.line([p((15,-151+bob)),p((20,-152+bob))],fill='#654e43',width=1)
 for j in [-1,1]:
  hand=(j*-stride*.7+8,-89+bob) if walk else (15,-91+bob)
  if gesture:hand=lerp(hand,(65,-120+bob),gesture)
  elbow=ik(shoulder,hand,32,side=-1)
  limb(d,p(shoulder),p(elbow),round(11*s),c);limb(d,p(elbow),p(hand),round(9*s),c)
  d.ellipse((p((hand[0]-4,hand[1]-5))[0],p((hand[0]-4,hand[1]-5))[1],p((hand[0]+4,hand[1]+5))[0],p((hand[0]+4,hand[1]+5))[1]) if face==1 and not collapse else (p(hand)[0]-4*s,p(hand)[1]-4*s,p(hand)[0]+4*s,p(hand)[1]+4*s),fill=skin)
 if tag:d.text((x-22*s,y-205*s),tag,font=small,fill='#e3dccb')
def car(d,x,y,scale=1,black=True):
 c='#303b47' if black else '#9a9e94';s=scale
 def p(q):return(x+q[0]*s,y+q[1]*s)
 d.polygon([p(q) for q in [(0,0),(10,-42),(65,-53),(100,-87),(225,-87),(270,-53),(310,-42),(317,0)]],fill=c,outline='#172029',width=3)
 d.polygon([p(q) for q in [(80,-54),(110,-79),(157,-79),(157,-54)]],fill='#72818a')
 d.polygon([p(q) for q in [(168,-79),(220,-79),(250,-54),(168,-54)]],fill='#72818a')
 for xx in [61,258]:d.ellipse((x+(xx-22)*s,y-14*s,x+(xx+22)*s,y+29*s),fill='#151b20',outline='#828889',width=3)
 d.line([p((164,-53)),p((164,-3))],fill='#57626a',width=2)
def bag(d,x,y,s=1):
 d.rounded_rectangle((x-22*s,y-23*s,x+22*s,y+9*s),radius=3,fill='#40392f',outline='#a89979',width=2)
 d.arc((x-10*s,y-34*s,x+10*s,y-15*s),180,360,fill='#ccbd99',width=3)
def base(setting):
 im=Image.new('RGB',(W,H),'#26333d');d=ImageDraw.Draw(im)
 if setting=='garage':
  d.rectangle((0,0,W,294),fill='#354048');d.polygon([(0,294),(W,294),(W,H),(0,H)],fill='#515553')
  for x in [-70,360,790]:d.polygon([(x,0),(x+50,0),(x+68,365),(x-12,365)],fill='#747972');d.rectangle((x,235,x+52,260),fill='#d8b66a')
  for x in [70,430,800]:d.line((480,265,x,540),fill='#a8a592',width=3)
  for x in [180,640]:d.polygon([(x,28),(x+200,28),(x+180,36),(x-20,36)],fill='#ddd2ae')
 elif setting=='ground':
  d.rectangle((0,0,W,205),fill='#8eaaa9');d.polygon([(0,145),(130,105),(270,166),(430,91),(630,160),(830,106),(960,151),(960,240),(0,240)],fill='#52675d')
  d.rectangle((0,220,W,H),fill='#b7a182');d.rectangle((570,135,930,225),fill='#aeb5a8');d.polygon([(550,139),(749,93),(945,139)],fill='#555e54')
  for x in range(592,920,46):d.rectangle((x,158,x+23,185),fill='#475954')
  for yy in [320,410,500]:d.line((0,yy,960,yy-12),fill='#dac4a0',width=2)
 else:
  d.rectangle((0,0,W,315),fill='#5c504b');d.rectangle((320,45,830,270),fill='#493b39')
  for x in range(0,960,48):d.line((x,0,x,315),fill='#66574e',width=2)
  d.polygon([(0,315),(960,315),(960,540),(0,540)],fill='#75675a')
  d.rectangle((425,150,770,230),fill='#734f43');d.rectangle((420,223,780,302),fill='#4c3029');d.line((420,225,780,225),fill='#bb9970',width=4)
  d.ellipse((580,63,625,108),fill='#b6a46e');d.text((570,116),'법정',font=small,fill='#d6c6a3')
 return im

def draw(cue,t,setting):
 im=base(setting);d=ImageDraw.Draw(im);a=cue['action'];q=t/max(.01,cue['end']-cue['start']);g=ease(q);phase=t*6
 if setting=='garage':
  car(d,520,335,.95,False)
  if a=='block':car(d,-325+680*ease(q/.65),400,1.1)
  elif a=='bank_bags':
   for i in range(3):human(d,390+i*92,421,.87,phase=phase+i,mode='walk' if q<.65 else 'stand',color='#73918b')
   bag(d,424,350+40*g);bag(d,510,350+40*g)
  elif a=='gun':
   human(d,245,425,1.1,color='#3a4052',mask=True,gesture=ease(q/.4),tag='A')
   human(d,410,427,.96,color='#646578',mask=True,tag='B')
   human(d,695,420,1.05,color='#73918b')
   # weapon remains attached to right hand through arm extension
   h=lerp((261.5,324),(316.5,293),ease(q/.4));d.polygon([(h[0],h[1]-4),(h[0]+28,h[1]-4),(h[0]+28,h[1]+1),(h[0]+7,h[1]+1),(h[0]+7,h[1]+13),(h[0],h[1]+13)],fill='#171e25')
  else:
   human(d,380+200*ease(max(0,q-.45)/.55),424,1,phase=phase,mode='walk' if q>.45 else 'stand',mask=True,color='#606274',tag='B')
   bag(d,395+200*ease(max(0,q-.45)/.55),408-67*ease(q/.35));bag(d,480,410)
   human(d,700,423,1,color='#73918b');car(d,70,330,.9)
 elif setting=='ground':
  if a=='pack':
   human(d,415,415,1.35,color='#626f51',gesture=.5+.3*math.sin(t*2))
   d.rectangle((460,310,540,422),fill='#3e4c35',outline='#21281f',width=3)
   for i in range(5):d.rectangle((620,390-i*7,670,396-i*7),fill=['#8c6351','#a2906f','#616c74'][i%3],outline='#d6c19e')
   xx,yy=lerp((625,350),(478,320),ease((q-.1)/.6));d.polygon([(xx,yy),(xx+38,yy-4),(xx+39,yy+7),(xx,yy+12)],fill='#b6aa8a',outline='#413e32')
  elif a=='pushup':
   # Anatomical prone figure, elbow flexion and rigid backpack move with torso.
   u=(1-math.cos(t*3.4))/2;sy=335+36*u
   shoulder=(430,sy);hip=(315,sy+30);toe=(195,420)
   d.polygon([(hip[0],hip[1]-10),(430,sy-14),(435,sy+13),(318,sy+44)],fill='#626f51',outline='#283322',width=2)
   d.polygon([(335,sy+5),(395,sy-10),(399,sy+3),(332,sy+19)],fill='#414a37',outline='#20281c')
   d.polygon([(431,sy-7),(454,sy-8),(467,sy+3),(456,sy+15),(435,sy+15)],fill='#c7a282',outline='#2a3029')
   for off in [0,8]:
    hand=(455+off,420);el=ik((430+off,sy+5),hand,49,-1)
    limb(d,(430+off,sy+5),el,12,'#626f51');limb(d,el,hand,10,'#626f51')
    d.ellipse((hand[0]-5,417,hand[0]+12,425),fill='#c7a282')
    knee=lerp(hip,toe,.5)
    limb(d,(hip[0]+off,hip[1]+14),knee,15,'#626f51');limb(d,knee,toe,12,'#626f51')
   d.line((180,427,485,427),fill='#7d6e54',width=3)
  else:
   mode='walk' if a=='walk' else 'run'
   for i in range(6):
    x=140+i*120+30*g;y=350+(i%2)*85;s=.73 if i%2==0 else 1.05
    fall=ease((q-.48)/.34) if a=='collapse' and i==3 else 0
    human(d,x,y,s,phase=phase+i*.7,mode=mode if not fall else 'stand',pack=True,color='#626f51',collapse=fall)
    if not fall: # sling rifle travels with person, not detached floating prop
     d.line((x-4*s,y-137*s,x+23*s,y-73*s),fill='#b5ab89',width=2)
     d.line((x+18*s,y-119*s,x+29*s,y-61*s),fill='#272b28',width=max(3,round(5*s)))
 else:
  # roles and spatial geography persist across cuts; prosecution and sentencing are separate dates
  prosecuting=a in ['prosecutor','prosecutor_reverse']
  human(d,596,270,.65,color='#27232c',gesture=(.15 if prosecuting else .35+.25*ease(q/.6)))
  d.rectangle((420,221,780,302),fill='#4c3029');d.line((420,224,780,224),fill='#bb9970',width=4)
  d.text((444,249),'재판부',font=label,fill='#d6c6a3')
  human(d,250,422 if prosecuting else 470,1.1,color='#303342',gesture=.15+.7*ease(q/.5) if prosecuting else 0)
  d.text((166,260 if prosecuting else 319),'검사',font=small,fill='#dfd6c0')
  py=285 if prosecuting else 357
  d.polygon([(238,py+5),(285,py),(290,py+35),(248,py+41)],fill='#dbd3bd',outline='#81755f')
  d.polygon([(212,336),(302,326),(316,347),(220,360)],fill='#947258');d.rectangle((231,357,301,428),fill='#644636')
  for x,name in [(660,'A' if cue['id'].startswith('L') else '중대장'),(790,'B' if cue['id'].startswith('L') else '부중대장')]:human(d,x,455,.94,color='#69717a',face=-1,tag=name)
  d.polygon([(610,395),(850,395),(872,421),(600,421)],fill='#a48366');d.rectangle((613,422,860,477),fill='#634a3b')
  if not prosecuting:
   # visible paper and judge's reading hand
   yy=201+9*ease(q/.6)
   d.polygon([(589,yy),(621,yy),(623,yy+24),(588,yy+24)],fill='#e0d7bd');d.line((591,yy+4,619,yy+4),fill='#746c5c',width=1)
  stage='검찰 구형 · 법원에 대한 요청' if prosecuting else ('항소심 선고' if a=='appeal' else '1심 선고 · 법원의 판단')
  d.text((30,55),stage,font=label,fill='#ece0bd')
 d.rectangle((0,0,W,32),fill='#17212b');d.text((20,5),'보도 내용을 바탕으로 한 재구성 · 실제 현장 영상 아님',font=small,fill='#c4c7bc')
 d.text((760,5),cue.get('date',''),font=small,fill='#ded3b7')
 return im

def wrap(text,n=39):
 words=text.split();lines=[];line=''
 for word in words:
  if len(line+' '+word)>n:lines.append(line);line=word
  else:line+=((' ' if line else '')+word)
 if line:lines.append(line)
 return lines

def main(ep,name,preview=False):
 out=ROOT/'episodes'/ep/'astra_12min';clip=json.loads((out/f'{name}_cues.json').read_text());cues=clip['cues'];duration=clip['duration'];n=math.ceil(duration*FPS)
 target=out/f'{name}_new_animation_r2.mp4'
 if preview:
  sheet=Image.new('RGB',(W*2,H*len(cues)))
  for i,c in enumerate(cues):
   for j,f in enumerate([.2,.8]):sheet.paste(draw(c,(c['end']-c['start'])*f,clip['setting']),(j*W,i*H))
  sheet.thumbnail((1440,2500));sheet.save(out/f'{name}_poses.jpg');return
 proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(out/f'{name}.wav'),'-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',str(duration),'-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
 for f in range(n):
  sec=f/FPS;c=next((c for c in cues if c['start']<=sec<c['end']),min(cues,key=lambda c:abs(c['start']-sec)))
  im=draw(c,max(0,sec-c['start']),clip['setting']);d=ImageDraw.Draw(im)
  lines=wrap(c.get('display',c['text']));hh=36*len(lines)+12;d.rectangle((0,H-hh,W,H),fill='#17212b')
  for i,line in enumerate(lines):d.text(((W-d.textlength(line,font=font))/2,H-hh+8+32*i),line,font=font,fill='#f3eee2')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();rc=proc.wait();assert rc==0,rc
 print(target,duration,flush=True)
if __name__=='__main__':
 for name,clip in json.loads((ROOT/'production/astra_12min/representatives.json').read_text()).items():main(clip['episode'],name,'--preview' in sys.argv)
