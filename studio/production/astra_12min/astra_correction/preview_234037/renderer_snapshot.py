"""Native 426x240 polygon animation; silhouette vocabulary adapted from draw_scene.py.
Authored articulated keyframes, explicit prop identity and contact. No action_revision imports.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math, json, subprocess, hashlib, wave, sys, datetime
ROOT=Path('.')
OUT=Path(__file__).parent
W,H=426,240; SX=W/960; SY=H/540; FPS=24
C={'ink':'#18252b','paper':'#e8dfc9','skin':'#cf9b72','skinshade':'#9c6b52','hair':'#243038','olive':'#5c6a49','oliveLight':'#889273','oliveShade':'#394a3a','pack':'#927449','packShade':'#625638','navy':'#364d64','blue':'#607d8b','teal':'#4e7e79','wood':'#755442','gold':'#b79960','red':'#883d35','grey':'#89918b','white':'#f4ecda','floor':'#a7aaa0','suspectB':'#365c8d'}
FONT=ROOT/'episodes/quiz/v52_support/bundle_v52_final/public/fonts/Pretendard-Regular.otf'
def sm(v):
 v=max(0,min(1,v));return v*v*(3-2*v)
def lerp(a,b,u): return a+(b-a)*u
def mix(a,b,u):return tuple(lerp(x,y,u) for x,y in zip(a,b))
def rot(p,a):return (p[0]*math.cos(a)-p[1]*math.sin(a),p[0]*math.sin(a)+p[1]*math.cos(a))
def add(a,b):return a[0]+b[0],a[1]+b[1]
def key(u,pts):
 if u<=pts[0][0]:return pts[0][1]
 for (t0,a),(t1,b) in zip(pts,pts[1:]):
  if u<=t1:return mix(a,b,sm((u-t0)/(t1-t0))) if isinstance(a,tuple) else lerp(a,b,sm((u-t0)/(t1-t0)))
 return pts[-1][1]
class Canvas:
 def __init__(self):self.im=Image.new('RGB',(W,H),C['paper']);self.d=ImageDraw.Draw(self.im)
 def poly(self,p,c='ink',edge=True):self.d.polygon([(x*SX,y*SY) for x,y in p],fill=C.get(c,c)); self.line(p+[p[0]],'ink',2) if edge and c!='ink' else None
 def line(self,p,c='ink',w=2):self.d.line([(x*SX,y*SY) for x,y in p],fill=C.get(c,c),width=max(1,round(w*SX)),joint='curve')
 def rect(self,x,y,w,h,c):self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],c)
 def text(self,t,x,y,size=22,c='ink',center=False):
  f=ImageFont.truetype(str(FONT),round(size*SX));self.d.text((round(x*SX),round(y*SY)),t,font=f,fill=C[c],anchor='mt' if center else 'lt')
 def limb(self,a,b,width,c):
  dx=b[0]-a[0];dy=b[1]-a[1];l=max(.01,math.hypot(dx,dy));nx=-dy/l;ny=dx/l
  self.poly([(a[0]+nx*width,a[1]+ny*width),(a[0]-nx*width,a[1]-ny*width),(b[0]-nx*width*.76,b[1]-ny*width*.76),(b[0]+nx*width*.76,b[1]+ny*width*.76)],c)
 def hand(self,p,s=1):
  x,y=p;self.poly([(x-6*s,y-6*s),(x+4*s,y-8*s),(x+10*s,y-3*s),(x+9*s,y+6*s),(x+1*s,y+9*s),(x-6*s,y+4*s)],'skin');self.line([(x+1*s,y),(x+8*s,y+2*s)],'skinshade',2*s)

def ik(a,b,l1,l2,side=1):
 dx=b[0]-a[0];dy=b[1]-a[1];d=max(.001,math.hypot(dx,dy));q=min(d,l1+l2-.001);v=(l1*l1-l2*l2+q*q)/(2*q);h=math.sqrt(max(0,l1*l1-v*v));return a[0]+dx/d*v-dy/d*h*side,a[1]+dy/d*v+dx/d*h*side

def actor(cv,x,y,s=1,c='navy',flip=False,hip=None,angle=0,head=0,face=None,feet=None,hands=None,seated=False,robe=False,mask=False,pack=False,mouth=False,rifle=False,elbows=None,knees=None):
 # Complete figure: articulated legs and shoes, pelvis, torso, continuous neck, jaw and head.
 f=-1 if flip else 1
 def world(p):return x+p[0]*s*f,y+p[1]*s
 hp=hip or (0,-57 if seated else -106)
 def upper(p):return world(add(hp,rot(p,angle)))
 def pg(p,col):cv.poly([upper(z) for z in p],col)
 def ln(p,col='ink',w=2):cv.line([upper(z) for z in p],col,w*s)
 feet=feet or ((-15,0),(18,0))
 for j,(foot,hx) in enumerate(zip(feet,(-10,10))):
  h=world((hp[0]+hx,hp[1]+3));a=world((foot[0],foot[1]-8))
  k=world(knees[j]) if knees else world((33+9*j,-38)) if seated else ik(h,a,51*s,49*s,-f)
  cv.limb(h,k,12*s,'ink' if j==0 else c);cv.limb(k,a,8*s,'ink' if j==0 else c)
  ax,ay=a;cv.poly([(ax-9*s,ay-5*s),(ax+7*s,ay-5*s),(ax+22*s*f,ay+5*s),(ax+22*s*f,ay+8*s),(ax-10*s,ay+8*s)],'ink');cv.line([(ax-7*s,ay+7*s),(ax+20*s*f,ay+7*s)],'grey',2*s)
 if pack:
  pg([(-24,-78),(-56,-70),(-59,-23),(-43,-10),(-23,-20)],'pack');pg([(-57,-68),(-53,-82),(-25,-87),(-22,-71),(-48,-63)],'packShade');ln([(-48,-68),(-43,-18)],'gold',3)
 pg([(-26,-74),(-12,-88),(10,-88),(25,-75),(27,-48),(19,-23),(24,1),(5,10),(-22,1),(-26,-30)],'ink' if robe else c)
 pg([(-24,-70),(-13,-75),(-15,-32),(-8,5),(-23,0),(-27,-42)],'oliveShade' if c=='olive' else 'ink')
 pg([(-9,-89),(1,-75),(12,-88),(17,-76),(4,-61),(-13,-75)],'white')
 if robe:pg([(-24,-75),(-14,-82),(-12,-25),(-30,16),(27,16),(15,-26),(15,-83),(25,-73),(28,-29),(36,20),(-35,20)],'ink');pg([(-8,-83),(0,-63),(7,-37),(13,-81),(3,-71)],'red')
 else:ln([(2,-61),(8,-29)],'oliveLight' if c=='olive' else 'blue',3);ln([(-20,0),(21,0)],'ink',4)
 # Neck overlaps both shoulder collar and jaw through every head rotation.
 pg([(-9,-101),(7,-101),(10,-83),(1,-75),(-9,-86)],'skin')
 neck=upper((0,-96));ha=angle+head
 fd=f if face is None else face
 def hd(p):
  v=rot((p[0]*fd,p[1]),ha);return neck[0]+v[0]*s,neck[1]+v[1]*s
 cv.poly([hd(p) for p in [(-13,-4),(-21,-16),(-19,-35),(-9,-46),(8,-47),(20,-39),(21,-27),(29,-20),(22,-16),(22,-6),(13,1),(4,0),(-2,8)]],'skin')
 cv.poly([hd(p) for p in [(-18,-27),(-20,-39),(-12,-51),(8,-52),(22,-43),(21,-34),(8,-37),(-3,-32),(-4,-18),(-12,-20),(-14,-2),(-19,-11)]],'hair')
 cv.poly([hd(p) for p in [(-12,-20),(-7,-24),(-3,-19),(-5,-12),(-10,-12)]],'skinshade')
 cv.line([hd((9,-28)),hd((18,-28))],'ink',2*s);cv.line([hd((13,-24)),hd((17,-24))],'ink',2*s)
 cv.line([hd((17,-9)),hd((23,-9+(3 if mouth else 0)))],'ink',2*s)
 if mask:
  cv.poly([hd(p) for p in [(-18,-35),(-9,-48),(9,-48),(21,-39),(22,-27),(29,-20),(23,-15),(23,-5),(13,4),(-3,3),(-16,-8)]],'ink')
  cv.poly([hd(p) for p in [(5,-29),(20,-29),(21,-23),(6,-23)]],'skin')
  cv.line([hd((13,-26)),hd((18,-26))],'ink',2*s)
 if hands is None:
  hands=[upper((-25,-12)),upper((26,-9))]
  elbows=[upper((-28,-43)),upper((28,-42))]
 shoulders=[upper((-19,-73)),upper((18,-74))]
 for j,(sh,hand) in enumerate(zip(shoulders,hands)):
  el=elbows[j] if elbows else ik(sh,hand,43*s,43*s,(1 if j==0 else -1)*f);cv.limb(sh,el,9*s,'ink' if robe else c);cv.limb(el,hand,7*s,'ink' if robe else c);cv.line([el,(el[0]+4*s,el[1]+3*s)],'ink',2*s);cv.hand(hand,s)
 if pack:ln([(-14,-83),(-5,-50),(-5,-7)],'pack',4)
 if rifle:
  # One slung rifle rigidly attached to trunk; both hands share its grip anchors.
  pg([(14,-28),(24,-34),(64,-79),(69,-76),(45,-42),(36,-30),(34,-17),(26,-17),(27,-29),(17,-19),(10,-20)],'ink');ln([(-12,-80),(29,-64),(18,-25)],'packShade',3)
  for hand in hands:cv.hand(hand,s)
 return {'upper':upper,'hands':hands,'neck':neck}

def document(cv,anchor,s=1,flat=0):
 x,y=anchor
 p=[(x-5*s,y-4*s),(x+41*s,y-33*s*(1-flat)-3*s),(x+60*s,y-17*s*(1-flat)+7*s),(x+12*s,y+13*s)]
 cv.poly(p,'white');cv.line([mix(p[0],p[3],.35),mix(p[1],p[2],.35)],'grey',1.6*s);cv.line([mix(p[0],p[3],.65),mix(p[1],p[2],.65)],'grey',1.6*s);cv.hand(anchor,s)

def bag(cv,grip,s=1):
 # This is the ONLY bag geometry. Ground and carried states use the same grip transform.
 x,y=grip;cv.poly([(x-28*s,y+16*s),(x+26*s,y+16*s),(x+31*s,y+49*s),(x-31*s,y+49*s)],'wood');cv.line([(x-11*s,y+17*s),(x-9*s,y),(x+9*s,y),(x+11*s,y+17*s)],'gold',4*s);cv.line([(x-23*s,y+25*s),(x+23*s,y+25*s)],'gold',2*s)

def vehicle(cv,x,y,s=1,van=False):
 def p(pts,c):cv.poly([(x+a*s,y+b*s) for a,b in pts],c)
 p([(-140,-30),(-130,-72),(-86,-81),(-54,-118),(58,-118),(94,-78),(134,-65),(145,-26)],'teal' if van else 'ink');p([(-47,-110),(49,-110),(76,-80),(-72,-80)],'blue');p([(-135,-29),(140,-29),(140,-16),(-139,-16)],'grey')
 for a in (-90,90):p([(a-23,-35),(a+13,-35),(a+24,-15),(a+13,5),(a-17,5),(a-27,-13)],'ink');p([(a-12,-25),(a+9,-25),(a+12,-8),(a-10,-5)],'grey')
 p([(107,-61),(136,-57),(139,-46),(108,-47)],'paper')

def chair(cv,x,y,s=1):
 cv.rect(x-30*s,y-110*s,52*s,81*s,'wood');cv.rect(x-32*s,y-46*s,67*s,10*s,'wood');cv.line([(x-25*s,y-36*s),(x-25*s,y)],'ink',5*s);cv.line([(x+26*s,y-36*s),(x+26*s,y)],'ink',5*s)

def court(cv,clip,cue,u,t):
 cv.rect(0,0,960,540,'paper');cv.rect(0,330,960,210,'wood')
 for x in range(20,960,84):cv.line([(x,42),(x,330)],'gold',2)
 cv.rect(340,79,400,45,'red');cv.text('재 판 부',540,88,26,'white',True)
 speak=cue['action'] in ('prosecutor','prosecutor_reverse');second=cue['action']=='prosecutor_reverse'
 # Raised dais and seats are behind bodies. Solid bench is drawn after complete bodies.
 cv.poly([(300,319),(754,319),(780,345),(278,345)],'packShade')
 for x in (405,540,680):chair(cv,x,316,.72)
 for x in (405,680):actor(cv,x,315,.70,'ink',seated=True,robe=True,face=-1 if speak else 1,head=.10 if speak else .24,hands=[(x-15,250),(x+19,250)],elbows=[(x-18,239),(x+20,239)])
 jx,jy,js=540,325,.88
 jread=1 if speak else 1-key(u,[(0,0),(.24,0),(.42,1),(.75,1),(.95,0)])
 jhead=.38*jread; jface=-1 if speak else 1
 jbody=0 if speak else key(u,[(0,-.04),(.25,-.04),(.44,.09),(.78,.09),(1,0)])
 jhand=(jx+25,251) if speak else key(u,[(0,(jx+28,jy-103)),(.20,(jx+30,jy-114)),(.42,(jx+30,jy-111)),(.78,(jx+30,jy-111)),(.94,(jx+39,252)),(1,(jx+39,252))])
 actor(cv,jx,jy,js,'ink',seated=True,robe=True,head=jhead,face=jface,angle=jbody,hands=[(jx-26,251),jhand],elbows=[(jx-25,236),(jx+28,238)],mouth=(not speak and .42<u<.78 and int(t*5)%3==0))
 cv.rect(312,258,424,78,'wood');cv.line([(318,263),(731,263)],'gold',5);cv.text('재판부',526,284,24,'paper',True)
 if not speak:document(cv,jhand,.9,key(u,[(0,0),(.8,0),(.94,1)]))
 else:cv.rect(564,249,44,6,'white')
 # Prosecutor rises only for the request; sentencing keeps seated pelvis and bent legs.
 px,py,ps=171,470,1.08;chair(cv,px,py,ps)
 rise=key(u,[(0,0),(.12,1),(.88,1),(1,.30)]) if speak and not second else (1 if speak else 0)
 hp=(0,-57-49*rise)
 ph=key(u,[(0,(211,367)),(.16,(223,307)),(.34,(226,304)),(.73,(226,304)),(.92,(220,370)),(1,(219,375))]) if speak else (216,382)
 gh=key(u,[(0,(192,364)),(.20,(201,345)),(.36,(246,332)),(.50,(258,325)),(.66,(238,337)),(.83,(206,365)),(1,(201,380))]) if speak else (196,381)
 head=key(u,[(0,.42),(.22,.42),(.36,-.09),(.77,-.09),(.93,.33)]) if speak else -.07
 actor(cv,px,py,ps,'navy',hip=hp,seated=not speak,head=head,angle=key(u,[(0,0),(.34,.04),(.78,.04),(1,0)]) if speak else 0,hands=[ph,gh],elbows=None if speak else [(181,369),(198,365)],mouth=speak and .35<u<.78 and int(t*5)%3==0)
 # Small desk does not erase legs or float torso; front legs visible below its edge.
 cv.poly([(86,388),(250,388),(263,400),(94,400)],'pack');cv.rect(95,400,151,34,'wood');cv.line([(104,433),(104,481)],'wood',8);cv.line([(238,433),(238,481)],'wood',8);cv.text('검사',171,404,24,'white',True)
 document(cv,ph,1.04,key(u,[(0,1),(.16,0),(.8,0),(.96,1)]) if speak else 1)
 # Stable defendant seats and identities; neither figure receives a speaking gesture.
 names=['A','B'] if clip['episode']=='lf2_daejeon_bank' else ['중대장','부중대장']
 for x,c,n in [(776,'grey',names[0]),(884,'blue',names[1])]:
  chair(cv,x,476,.83);actor(cv,x,474,.83,c,flip=True,seated=False,head=-.07,hands=[(x-16,384),(x+3,389)],elbows=[(x-20,365),(x+11,367)])
 cv.poly([(704,404),(947,404),(947,420),(710,420)],'pack');cv.rect(712,420,234,32,'wood');cv.line([(723,450),(723,485)],'wood',7);cv.line([(934,450),(934,485)],'wood',7)
 cv.text(names[0],776,425,23,'white',True);cv.text(names[1],884,425,23,'white',True)
 status='검찰 구형' if speak else ('항소심 선고' if cue['action']=='appeal' else '1심 선고')
 cv.text(status,930,19,24,'ink',True)

def garage(cv,clip,cue,u,t):
 cv.rect(0,0,960,540,'blue');cv.poly([(0,235),(960,180),(960,540),(0,540)],'floor')
 for x in (54,455,896):cv.poly([(x,46),(x+34,46),(x+34,245),(x,248)],'paper');cv.rect(x,186,34,17,'gold')
 for x in (80,410,740):cv.line([(x,283),(x-125,505)],'paper',3)
 act=cue['action'];vehicle(cv,165,298,1.02,True);vehicle(cv,800-365*sm(u/.62) if act=='block' else 435,329,.92)
 if act in ('block','bank_bags'):
  move=sm(u/.7) if act=='bank_bags' else 0
  bend=sm((u-.5)/.36) if act=='bank_bags' else 0
  grips=[(274,lerp(346,408,bend)),(443,lerp(346,408,bend))]
  for (x,y),grip in zip([(210,446),(379,447)],grips):
   actor(cv,x+move*28,y,.76,'teal',hip=(0,-106+58*bend),angle=.25*bend,hands=[(x+move*28-18,366+bend*25),grip],elbows=[(x+move*28-20,347+bend*30),(x+move*28+31,335+bend*53)])
  actor(cv,116,402,.76,'teal')
  for grip in grips:bag(cv,grip,.9);cv.hand(grip,.76)
 elif act=='gun':
  for x,y in [(155,441),(246,413),(90,385)]:actor(cv,x,y,.72,'teal')
  z=sm((u-.18)/.32);gx,gy=lerp(598,542,z),lerp(345,298,z)
  actor(cv,651,457,1.04,'navy',flip=True,mask=True,hands=[(625,350),(gx,gy)])
  cv.poly([(gx-3,gy-6),(gx-9,gy-15),(gx-40,gy-15),(gx-41,gy-8),(gx-18,gy-7),(gx-14,gy+7),(gx-5,gy+7)],'ink');cv.hand((gx,gy),1.04)
  actor(cv,796,430,.85,'suspectB',mask=True,flip=True)
  bag(cv,(333,408),.9);bag(cv,(434,408),.9)
 else:
  # One named moving bag, one named stationary bag: no duplicated ground state.
  bag_stationary=(300,408);contact=(434,408)
  approach=sm(u/.27);bend=key(u,[(0,0),(.27,0),(.43,1),(.51,1),(.65,0),(1,0)])
  carry=sm((u-.68)/.27);x=lerp(345,399,approach)+carry*280
  hip=(bend*15,-106+bend*50);angle=bend*.45
  hand=key(u,[(0,(378,344)),(.27,(432,345)),(.43,contact),(.51,contact),(.65,(438,360)),(.68,(438,360)),(.95,(718,360)),(1,(718,360))])
  # Before contact bag remains on floor; after contact same geometry follows the hand.
  moving=contact if u<.43 else hand
  walkphase=t*1.25;feet=((-15,0),(18,0))
  if u<.25 or .70<u<.95:feet=((-14+18*math.sin(walkphase*math.tau),-max(0,math.cos(walkphase*math.tau))*9),(18-18*math.sin(walkphase*math.tau),-max(0,-math.cos(walkphase*math.tau))*9))
  actor(cv,796,421,.8,'navy',mask=True,flip=True)
  actor(cv,x,452,1.04,'suspectB',mask=True,hip=hip,angle=angle,head=.25*bend,feet=feet,hands=[(x-22,350+bend*20),hand])
  bag(cv,bag_stationary,.9);bag(cv,moving,.9)
  if u>=.43:cv.hand(hand,1.04)

def pack_scene(cv,u):
 cv.rect(0,0,960,540,'paper');cv.rect(0,375,960,165,'floor');cv.rect(130,77,680,35,'blue')
 cv.rect(383,359,361,17,'wood');cv.rect(405,375,15,105,'wood');cv.rect(706,375,15,105,'wood')
 # The sole book enters from above, behind the front wall; no three-book pile teleports.
 hx,hy=key(u,[(0,(480,261)),(.18,(512,251)),(.37,(590,251)),(.61,(590,318)),(.70,(590,318)),(.80,(620,235)),(.82,(620,235)),(.97,(620,329)),(1,(620,329))])
 actor(cv,390,475,1.14,'olive',angle=.05,head=.20,hands=[(466,326),(hx,hy)])
 cv.poly([(548,281),(650,281),(658,361),(540,361)],'packShade')
 close=sm((u-.82)/.15)
 cv.poly([(548,281),(542,235+close*94),(646,235+close*94),(650,281)],'packShade')
 if u<.72:
  cv.poly([(hx-10,hy-3),(hx+42,hy-3),(hx+42,hy+22),(hx-10,hy+22)],'blue');cv.rect(hx-6,hy+3,43,13,'paper');cv.hand((hx,hy),1.14)
 cv.poly([(541,307),(654,307),(658,361),(540,361)],'pack');cv.line([(547,312),(650,312)],'gold',3)
 if close>0:cv.poly([(548,281),(542,235+close*94),(646,235+close*94),(650,281)],'packShade')
 if u>=.72:cv.hand((hx,hy),1.14)

def ground(cv,clip,cue,u,t):
 if cue['action']=='pack':pack_scene(cv,u);return
 cv.rect(0,0,960,540,'blue');cv.poly([(0,159),(960,129),(960,540),(0,540)],'floor')
 for x in range(40,950,140):cv.rect(x,58,75,58,'paper')
 for y in (280,470):cv.line([(0,y),(960,y-25)],'paper',3)
 act=cue['action'];run=act in ('race','collapse');x=360+u*(190 if run else 85);y=457;s=1.12
 if act=='pushup':
  z=key(u,[(0,0),(.38,1),(.70,0),(1,0)])
  # Shared full-body silhouette; both palms and both toe contacts remain fixed.
  ax,ay,ss=390,457,1.20
  hp=(8,-49+z*24);ang=1.33+z*.13
  ob=actor(cv,ax,ay,ss,'olive',hip=hp,angle=ang,head=-.20,pack=True,feet=[(-60,-2),(-55,0)],knees=[(-29,-18+z*10),(-26,-14+z*9)],hands=[(535,452),(555,457)],elbows=[(510,410+z*20),(532,415+z*20)])
  tr=ob['upper'];cv.line([tr((12,-70)),tr((12,-8))],'ink',7);cv.line([tr((-12,-77)),tr((16,-45)),tr((12,-8))],'packShade',3)
  cv.hand((535,452),ss);cv.hand((555,457),ss)
 elif act=='collapse' and u>.35:
  z=sm((u-.35)/.48);ax=360+.35*190;ay=457;ss=1.12
  hp=key(z,[(0,(0,-96)),(.35,(5,-55)),(.65,(0,-24)),(1,(-12,-15))])
  ang=key(z,[(0,.18),(.35,.40),(.65,.90),(1,1.43)])
  foot1=key(z,[(0,(-20,0)),(.35,(-48,0)),(1,(-73,0))]);foot2=key(z,[(0,(21,-7)),(.35,(-17,0)),(1,(-60,-4))])
  knee1=key(z,[(0,(-8,-49)),(.35,(17,-4)),(.65,(-14,-3)),(1,(-38,-4))]);knee2=key(z,[(0,(29,-44)),(.35,(28,-16)),(1,(-31,-9))])
  hand=key(z,[(0,(ax+64,337)),(.52,(ax+118,455)),(1,(ax+118,455))]);far=key(z,[(0,(ax+30,354)),(.55,(ax+97,450)),(1,(ax+97,450))])
  ob=actor(cv,ax,ay,ss,'olive',hip=hp,angle=ang,head=-.12,pack=True,feet=[foot2,foot1],knees=[knee2,knee1],hands=[far,hand])
  tr=ob['upper'];cv.line([tr((12,-72)),tr((12,-8))],'ink',7);cv.line([tr((-12,-77)),tr((16,-45)),tr((12,-8))],'packShade',3);cv.hand(hand,ss)
 else:
  cyc=t*(1.35 if run else .78);p=cyc%1
  def foot(phase):
   q=phase%1
   if run:
    return (lerp(25,-24,q/.35),0) if q<.35 else (lerp(-24,25,(q-.35)/.65),-32*math.sin(math.pi*(q-.35)/.65))
   return (lerp(21,-21,q/.65),0) if q<.65 else (lerp(-21,21,(q-.65)/.35),-16*math.sin(math.pi*(q-.65)/.35))
  feet=[foot(p),foot(p+.5)];fly=run and all(a[1]<-1 for a in feet);hip=(0,(-96 if run else -103)-(6 if fly else 0));ang=.18 if run else .03
  def upper(p):return (x+s*(hip[0]+rot(p,ang)[0]),y+s*(hip[1]+rot(p,ang)[1]))
  actor(cv,x,y,s,'olive',hip=hip,angle=ang,feet=feet,head=-.06,pack=True,rifle=True,hands=[upper((24,-33)),upper((52,-64))])

def frame(clip,t):
 cv=Canvas();cue=clip['cues'][0]
 for cc in clip['cues']:
  if t>=cc['start']:cue=cc
 u=max(0,min(1,(t-cue['start'])/(cue['end']-cue['start'])))
 if clip['setting']=='court':court(cv,clip,cue,u,t)
 elif clip['setting']=='garage':garage(cv,clip,cue,u,t)
 else:ground(cv,clip,cue,u,t)
 cv.rect(0,0,960,44,'paper');cv.text(cue.get('date',clip['date']),23,13,24,'ink');cv.text(('검찰 구형' if cue['action'] in ('prosecutor','prosecutor_reverse') else '항소심 선고' if cue['action']=='appeal' else '1심 선고') if clip['setting']=='court' else '보도에 근거한 재구성',778,13,22,'ink',True)
 cv.rect(0,505,960,35,'ink');cv.text('보도에 근거한 재구성 · 실제 현장 영상 아님',23,514,18,'paper')
 return cv.im

def run(cmd):return subprocess.run(cmd,check=True,capture_output=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 names=sys.argv[1:] or ['lf2_court','lf2_event','n18_court','n18_event'];preview='--preview' in names
 names=[n for n in names if not n.startswith('--')]
 dest=OUT/('preview_'+datetime.datetime.now().strftime('%H%M%S') if preview else 'delivery_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));dest.mkdir()
 (dest/'renderer_snapshot.py').write_bytes(Path(__file__).read_bytes())
 print('OUTPUT',dest,flush=True)
 reps=json.loads((OUT.parent/'representatives.json').read_text());records=[]
 for name in names:
  base=ROOT/'episodes'/reps[name]['episode']/'astra_12min';cp=base/f'{name}_cues.json';clip=json.loads(cp.read_text());audio=base/f'{name}.wav'
  audio_checks=[]
  with wave.open(str(audio)) as w:whole=w.readframes(w.getnframes());rate=w.getframerate();width=w.getsampwidth()
  for cue in clip['cues']:
   with wave.open(cue['audio']) as w:pcm=w.readframes(w.getnframes())
   start=round(cue['start']*rate)*width
   audio_checks.append({'cue':cue['id'],'source_sha256':sha(cue['audio']),'sha_matches_cue':sha(cue['audio'])==cue['sha256'],'full_wav_pcm_exact_at_cue_start':whole[start:start+len(pcm)]==pcm})
  assert all(c['sha_matches_cue'] and c['full_wav_pcm_exact_at_cue_start'] for c in audio_checks)
  if preview:
   ims=[]
   for cue in clip['cues']:
    for phase,u in [('start',0),('contact',.43),('middle',.60),('end',.99)]:
     t=cue['start']+(cue['end']-cue['start'])*u;im=frame(clip,t);p=dest/f"{cue['id']}_{phase}.png";im.save(p);ims.append((p,f"{cue['id']} {phase} {t:.2f}s"))
   sheet(ims,dest/f'{name}_preview.png');continue
  mp4=dest/f'{name}_CORRECTED_426x240.mp4';n=math.ceil(clip['duration']*FPS)
  command=['ffmpeg','-n','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(audio),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','192k','-t',str(clip['duration']),'-movflags','+faststart',str(mp4)]
  proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
  for f in range(n):proc.stdin.write(frame(clip,f/FPS).tobytes())
  proc.stdin.close();err=proc.stderr.read();assert proc.wait()==0,err
  probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(mp4)]).stdout)
  decode=run(['ffmpeg','-v','error','-threads','2','-i',str(mp4),'-f','null','-']);(dest/f'{name}_decode.log').write_bytes(decode.stderr)
  ev=dest/f'{name}_frames';ev.mkdir();extracts=[];ims=[]
  for cue in clip['cues']:
   ratios=[('start',0),('read_or_approach',.20),('contact_or_orientation',.43),('middle',.60),('settle',.84),('end',.985)]
   if cue['action']=='take_bag':ratios=[('start',0),('empty_approach',.25),('grip_contact',.45),('lift',.64),('carry',.82),('end',.985)]
   if cue['action']=='pack':ratios=[('start',0),('above_opening',.37),('insert_occlusion',.61),('release',.74),('flap_closing',.86),('end',.985)]
   for phase,u in ratios:
    exact=cue['start']+(cue['end']-cue['start'])*u;fi=min(n-1,math.ceil(exact*FPS));ts=fi/FPS;png=ev/f"{cue['id']}_{phase}_f{fi:04d}.png"
    run(['ffmpeg','-n','-v','error','-i',str(mp4),'-vf',f'select=eq(n\\,{fi})','-vsync','0','-frames:v','1',str(png)])
    extracts.append({'cue':cue['id'],'phase':phase,'frame':fi,'time':ts,'path':str(png),'sha256':sha(png)});ims.append((png,f"{cue['id']} {phase} {ts:.2f}s"))
  review=dest/f'{name}_review_sheet.png';sheet(ims,review)
  record={'name':name,'path':str(mp4),'sha256':sha(mp4),'source_cue_file':str(cp),'source_cue_sha256':sha(cp),'source_audio':str(audio),'source_audio_sha256':sha(audio),'audio_checks':audio_checks,'audio':'Existing composite WAV; original PCM and cue start times verified exactly; AAC encoded without resynthesis. No SFX added.','probe':probe,'full_decode':decode.returncode==0,'cues':clip['cues'],'extracts':extracts,'review_sheet':str(review),'visual_review':'pending actual extracted image inspection','continuous_watch':'not performed','full_episode':False,'renderer':str(dest/'renderer_snapshot.py'),'renderer_sha256':sha(dest/'renderer_snapshot.py')}
  (dest/f'{name}_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));records.append(record);(dest/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('DONE',name,mp4,record['sha256'],flush=True)

def sheet(ims,path):
 cols=3;rows=math.ceil(len(ims)/cols);out=Image.new('RGB',(W*cols,(H+27)*rows),'#18252b');d=ImageDraw.Draw(out)
 for i,(p,label) in enumerate(ims):
  x=i%cols*W;y=i//cols*(H+27);out.paste(Image.open(p),(x,y));d.text((x+6,y+H+6),label,fill='white',font=ImageFont.truetype(str(FONT),11))
 out.save(path)
if __name__=='__main__':main()
