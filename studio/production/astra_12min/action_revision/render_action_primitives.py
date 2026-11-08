"""Independent low-res corrective representative renderer.
Uses planar authored silhouettes: contact-led props, gait phases, and role-specific court blocking.
"""
import bpy, math, sys
from pathlib import Path

mode=sys.argv[sys.argv.index('--')+1]
out=Path(sys.argv[sys.argv.index('--')+2]); out.mkdir(parents=True,exist_ok=True)
FPS=12; N=96; W,H=426,240
C={'paper':'e9e1cf','ink':'17262d','floor':'89918b','wall':'607d8b','wood':'755442','red':'883d35','skin':'cf9b72','navy':'364d64','olive':'5c6a49','shade':'394a3a','pack':'927449','gold':'b79960','white':'f4ecda','teal':'4e7e79'}
mats={}
for n,h in C.items():
 m=bpy.data.materials.new(n);m.diffuse_color=tuple(int(h[i:i+2],16)/255 for i in (0,2,4))+(1,);mats[n]=m
objs=[]; z=0
def poly(pts,c):
 global z
 z+=.2; me=bpy.data.meshes.new('contour');me.from_pydata([(x,H-y,z) for x,y in pts],[],[tuple(range(len(pts)))]);o=bpy.data.objects.new('drawn_'+c,me);bpy.context.collection.objects.link(o);o.data.materials.append(mats[c]);objs.append(o)
def ln(a,b,c='ink',w=2):
 global z
 z+=.2; cv=bpy.data.curves.new('stroke','CURVE');cv.dimensions='3D';cv.bevel_depth=w/2;sp=cv.splines.new('POLY');sp.points.add(1);sp.points[0].co=(a[0],H-a[1],z,1);sp.points[1].co=(b[0],H-b[1],z,1);o=bpy.data.objects.new('stroke',cv);bpy.context.collection.objects.link(o);o.data.materials.append(mats[c]);objs.append(o)
def rect(x,y,w,h,c): poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],c)
def clear():
 global z
 for o in objs:
  d=o.data;bpy.data.objects.remove(o,do_unlink=True)
  if d.users==0:
   try: bpy.data.meshes.remove(d)
   except: 
    try:bpy.data.curves.remove(d)
    except:pass
 objs.clear();z=0
def head(x,y,face=1):
 poly([(x-8,y-18),(x-10,y-29),(x-4,y-38),(7+x,y-37),(12+x,y-31),(11+x,y-22),(5+x,y-17)],'skin');poly([(x-10,y-30),(x-4,y-42),(8+x,y-40),(12+x,y-32),(1+x,y-31)],'ink');ln((x+4*face,y-28),(x+8*face,y-28),'ink',1)
def body(x,y,lean=0,col='olive',scale=1):
 # angular adult torso, not circle/cylinder.
 p=[(-13,-70),(8,-73),(18,-46),(12,-15),(-9,-13),(-18,-43)]
 def T(q): return (x+scale*(q[0]+lean*(-q[1]/70)),y+scale*q[1])
 poly([T(q) for q in p],col);head(x+lean*0.5,y-70*scale)
def limb(a,b,c='olive',w=7):
 dx=b[0]-a[0];dy=b[1]-a[1];L=max(1,math.hypot(dx,dy));nx=-dy/L*w;ny=dx/L*w;poly([(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),(b[0]-nx*.75,b[1]-ny*.75),(b[0]+nx*.75,b[1]+ny*.75)],c)
def bag(x,y,open=False):
 rect(x,y,38,22,'pack');ln((x+7,y),(x+11,y-8),'gold',2);ln((x+11,y-8),(x+27,y-8),'gold',2);ln((x+27,y-8),(x+31,y),'gold',2)
 if open: poly([(x+2,y),(x+36,y),(x+31,y-11),(x+5,y-11)],'shade')
def rifle(x,y,angle=0):
 ex=x+math.cos(angle)*28;ey=y+math.sin(angle)*28;ln((x,y),(ex,ey),'ink',3);ln((x+8*math.cos(angle),y+8*math.sin(angle)),(x+5*math.cos(angle)-7*math.sin(angle),y+5*math.sin(angle)+7*math.cos(angle)),'gold',2)
def soldier(x,ground,phase,run=False,fall=0):
 # phases make heel/toe contact readable; fall progresses through knee/hand/torso contact.
 if fall:
  # centroid descends/rightward; first knee at fall .33, hand .58, torso .9
  cx=x+35*fall; cy=ground-65+48*fall; lean=55*fall
  body(cx,cy,lean,'olive'); hip=(cx+4,cy-15); knee=(cx+15+18*fall,ground-9); hand=(cx+18+35*fall,ground-5)
  limb((cx+9,cy-51),hand,'olive',5); limb(hip,knee,'olive',7)
  if fall>.55: ln(hand,(hand[0]+7,ground-4),'ink',2)
  if fall>.88: ln((cx-12,ground-3),(cx+35,ground-3),'shade',3)
  # pack remains attached to torso, moves with centroid
  poly([(cx-22,cy-64),(cx-42,cy-55),(cx-38,cy-27),(cx-15,cy-30)],'pack')
  return
 cyc=math.sin(phase*2*math.pi); stride=(20 if run else 11)*cyc; lift=(abs(cyc)*7 if run else 0); cy=ground-70-lift
 body(x,cy,8 if run else 2,'olive'); hip=(x+2,cy-14)
 # alternating legs with explicit soles at ground
 for sg in (1,-1):
  sx=stride*sg; knee=(x+sx*.25,ground-37+max(0,-sx)*.25); foot=(x+sx,ground-4-max(0,sx)*.25)
  limb(hip,knee,'olive' if sg==1 else 'shade',7);limb(knee,foot,'olive' if sg==1 else 'shade',5);ln((foot[0]-6,foot[1]),(foot[0]+11,foot[1]),'ink',2)
 # pack and rifle fixed by hands/shoulder connection
 poly([(x-20,cy-63),(x-39,cy-57),(x-37,cy-29),(x-16,cy-30)],'pack');
 hand=(x+23,cy-47);limb((x+10,cy-55),hand,'olive',5);rifle(hand[0],hand[1],.25)
def court_person(x,y,role,phase):
 # different body, gaze and document sequence per role
 if role=='prosecutor':
  lean=8+6*math.sin(phase*math.pi); body(x,y,lean,'navy'); docx=x+18+14*min(1,phase*1.8);docy=y-54-9*min(1,phase*1.8)
  limb((x+9,y-53),(docx,docy),'navy',5);rect(docx,docy-12,14,19,'white');ln((docx+2,docy-7),(docx+11,docy-7),'ink',1)
 elif role=='judge':
  # read down at start, raise gaze toward defendants, lower document at close.
  lean=-4+10*math.sin(phase*math.pi);body(x,y,lean,'ink');docy=y-46+18*max(0,(phase-.68)/.32);rect(x+12,docy-14,16,22,'white');limb((x+8,y-56),(x+16,docy),'ink',5);ln((x+18,y-69),(x+26,y-69),'ink',1)
 else: body(x,y,-5,'shade')
def bg(kind):
 rect(0,0,W,H,'paper')
 if kind=='court':
  rect(0,143,W,97,'wood');rect(100,32,230,19,'red');rect(90,75,246,45,'wood');ln((94,77),(331,77),'gold',2)
 else:
  rect(0,0,W,92,'wall');poly([(0,92),(W,75),(W,H),(0,H)],'floor');ln((0,92),(W,75),'ink',2)
def draw(t):
 clear();
 if mode=='lf2_event':
  bg('event');rect(252,105,115,46,'teal');rect(265,115,74,26,'wall')
  # canonical bag transfer: hand → handle → lift, other bag stays on floor.
  # Exactly two bags throughout: left remains grounded; right is the one lifted.
  bag(82,181)
  zt=min(1,max(0,(t-.08)/.36)); bx=159+70*zt;by=181-37*zt;bag(bx,by)
  body(110+55*zt,205,5,'navy');hand=(151+72*zt,166-37*zt);limb((133+55*zt,155),hand,'navy',5);ln((hand[0],hand[1]),(bx+20,by-8),'skin',3)
  # masked observer only: no firing-count visual claim.
  body(315,194,-5,'ink');ln((320,154),(286,156),'ink',4);rect(279,153,11,5,'ink')
 elif mode=='n18_event':
  bg('event');
  # books visibly enter open pack, then closed pack is worn.
  if t<.25:
   bag(154,153,True);z0=t/.25;bookx=107+54*z0;booky=139+20*z0;rect(bookx,booky,22,5,'white');body(90,205,0,'olive');limb((99,151),(bookx,booky),'olive',5)
  else:
   ph=(t-.25)*1.5;run=t>.48;fall=max(0,(t-.73)/.27)
   for xx,off in ((65,0),(135,.3),(205,.6)):soldier(xx+min(1,t)*75,218,ph+off,run=run,fall=fall if xx==135 else 0)
 elif mode.endswith('court'):
  bg('court'); rect(30,141,88,45,'wood');rect(288,141,112,45,'wood')
  prosecutor=mode=='lf2_court' # distinct emitter governed by clip semantics
  # prosecutor has document-linked address; judges listen. Court begins judge has document -> gaze -> announce.
  court_person(205,123,'judge',t); court_person(156,123,'other',t);court_person(255,123,'other',t)
  court_person(62,207,'prosecutor' if prosecutor else 'other',t)
  court_person(318,207,'other',t);court_person(372,207,'other',t)
  # for N18 court switch authority at mid-time: prosecutor seated, judge raises document/gaze.
  if mode=='n18_court':
   rect(50,184,18,9,'wood')
 # universal ground line
 if mode!='lf2_event': ln((0,216),(W,216),'shade',1)

scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='FLAT';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=False;scene.view_settings.view_transform='Standard';scene.render.resolution_x=W;scene.render.resolution_y=H;scene.render.resolution_percentage=100;scene.render.fps=FPS;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
bpy.ops.object.camera_add(location=(W/2,H/2,1000));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=W;scene.camera=cam
for f in range(1,N+1):
 draw((f-1)/(N-1));scene.render.filepath=str(out/f'frame_{f:04}.png');bpy.ops.render.render(write_still=True)
print('rendered',mode,N)
