# Blender 5.2 headless LF2 full low-resolution review render.
# Owns only terra_toon_recovery outputs. Uses the existing LF2 60-take timing.
import bpy, os, math, json
from mathutils import Vector
ROOT='episodes/lf2_daejeon_bank/terra_toon_recovery'
OUT=os.path.join(ROOT,'full_frames'); os.makedirs(OUT,exist_ok=True)
W,H=426,240

def m(n,c):
    # Node base colors are required for high-contrast EEVEE delivery, not viewport-only colors.
    x=bpy.data.materials.get(n) or bpy.data.materials.new(n)
    x.diffuse_color=(*c,1); x.use_nodes=True
    bs=x.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*c,1); bs.inputs['Roughness'].default_value=.78
    return x
DARK=m('ink',(0.015,.025,.045)); FLOOR=m('floor',(.20,.25,.29)); WALL=m('wall',(.12,.17,.22)); WHITE=m('transporter',(.76,.78,.72)); BLACK=m('black sedan',(.015,.025,.04)); BLUE=m('glass',(.05,.34,.49)); GOLD=m('lamp',(.95,.55,.08)); RED=m('alert',(.65,.05,.04)); NAVY=m('uniform',(.04,.16,.28)); MASK=m('mask',(.02,.025,.035)); SKIN=m('skin',(.58,.31,.18)); BAG=m('bag',(.28,.13,.045)); OLIVE=m('evidence',(.22,.34,.25)); PAPER=m('paper',(.86,.81,.66)); PURPLE=m('court',(.26,.11,.35)); GREEN=m('DNA',(.08,.55,.37)); ORANGE=m('fire',(.9,.18,.02))
def clear(): bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def cube(n,l,s,ma,bev=.04):
 bpy.ops.mesh.primitive_cube_add(location=l); o=bpy.context.object;o.name=n;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 if bev: q=o.modifiers.new('rounded','BEVEL');q.width=bev;q.segments=2
 return o
def sph(n,l,s,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=l);o=bpy.context.object;o.name=n;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);return o
def line(n,a,b,r,ma):
 d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2;bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=d.length,location=mid);o=bpy.context.object;o.name=n;o.data.materials.append(ma);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def cam(l,t,lens=48):
 bpy.ops.object.camera_add(location=l);o=bpy.context.object;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;bpy.context.scene.camera=o
def setup():
 s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=W;s.render.resolution_y=H;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.use_freestyle=True;s.render.line_thickness=1.25;s.world.color=(.018,.025,.04)
 bpy.ops.object.light_add(type='AREA',location=(-4,-5,7));bpy.context.object.data.energy=900;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
 bpy.ops.object.light_add(type='AREA',location=(5,2,5));bpy.context.object.data.energy=700;bpy.context.object.data.color=(1,.55,.25);bpy.context.object.data.size=4
def room(kind='garage'):
 cube('ground',(0,0,-.2),(14,14,.2),FLOOR,.01);cube('back wall',(0,5.5,3.3),(14,.2,3.3),WALL,.01)
 if kind=='garage':
  for x in (-6,0,6): cube('parking pillar',(x,4.8,2.2),(.32,.32,2.2),WHITE);cube('stripe',(x,4.45,1),(.35,.02,.22),GOLD,.01)
 else:
  cube('room desk',(0,3.6,1.05),(4,.55,.12),PAPER);cube('notice board',(0,5.1,3),(5,.1,1.7),WALL)
def car(n,l,ma,ang=0,van=False):
 body=cube(n+' body',(l[0],l[1],.72),(2.0,.85,.48),ma,.14);body.rotation_euler[2]=ang
 cab=cube(n+' cabin',(l[0]-.28*math.cos(ang),l[1]-.28*math.sin(ang),1.33),(1.05,.70,.38),ma,.16);cab.rotation_euler[2]=ang
 for q in (-1,1):
  x=l[0]-.28*math.cos(ang)-q*.72*math.sin(ang);y=l[1]-.28*math.sin(ang)+q*.72*math.cos(ang);w=cube(n+' window',(x,y,1.35),(.65,.025,.20),BLUE,.01);w.rotation_euler[2]=ang
 for dx in (-1.3,1.3):
  for q in (-.85,.85): sph(n+' wheel',(l[0]+dx*math.cos(ang)-q*math.sin(ang),l[1]+dx*math.sin(ang)+q*math.cos(ang),.35),(.28,.16,.28),DARK)
 if van: cube(n+' armored rear',(l[0]+.9*math.cos(ang),l[1]+.9*math.sin(ang),1.38),(.65,.72,.48),WHITE,.08)
def human(n,x,y,ma=NAVY,masked=False,pose='stand'):
 # explicit head, torso, legs and arms; facing camera-side for low-res legibility
 sph(n+' head',(x,y,2.55),(.32,.25,.35),MASK if masked else SKIN);cube(n+' torso',(x,y,1.85),(.38,.23,.55),ma,.12)
 for q in (-1,1):
  line(n+' leg',(x+q*.18,y,1.40),(x+q*.22,y-.03,.35),.13,ma);cube(n+' boot',(x+q*.22,y-.12,.22),(.18,.25,.10),DARK,.03)
  if pose=='hold' and q==-1:
   line(n+' arm',(x+q*.34,y,2.08),(x-.52,y-.48,1.72),.11,ma);sph(n+' hand',(x-.56,y-.52,1.68),(.13,.11,.12),MASK if masked else SKIN)
  else: line(n+' arm',(x+q*.34,y,2.08),(x+q*.48,y-.22,1.48),.11,ma);sph(n+' hand',(x+q*.49,y-.27,1.43),(.12,.10,.11),MASK if masked else SKIN)
def bag(x,y,z):
 cube('cash bag',(x,y,z),(.42,.18,.28),BAG,.08);line('bag handle',(x-.25,y,z+.28),(x,y,z+.52),.04,BAG);line('bag handle',(x,y,z+.52),(x+.25,y,z+.28),.04,BAG)
def gun_hand(x,y,z):
 # hand visibly joins pistol grip, pistol safely points toward empty wall
 sph('gripping hand',(x,y,z),(.16,.13,.14),MASK);cube('pistol grip',(x+.10,y,z+.08),(.08,.07,.22),DARK,.01);cube('pistol barrel',(x+.40,y,z+.23),(.38,.08,.08),DARK,.01);line('forearm to hand',(x-.48,y+.05,z-.12),(x,y,z),.12,NAVY)
def evidence(kind):
 room('office'); cube('evidence tray',(0,.4,.45),(2.7,1.4,.12),DARK);cube('sample card',(-.6,.35,.62),(1.0,.62,.04),PAPER,.01)
 if kind=='dna':
  for x in (-.7,0,.7): sph('DNA sample',(x,.2,.78),(.18,.18,.18),GREEN)
  line('comparison link',(-.7,.2,.8),(.7,.2,.8),.04,GREEN)
 elif kind=='mask': cube('mask cloth',(0,.2,.76),(1.0,.38,.06),OLIVE,.04);cube('handkerchief',(1.25,.2,.75),(.45,.35,.05),PAPER,.03)
 else:
  cube('record file',(0,.2,.72),(1.9,1.1,.10),PAPER,.03);cube('file tab',(1.65,.2,.9),(.22,.16,.15),RED,.02)
def court(stage):
 room('office');cube('judge bench',(0,3.7,1.65),(4,.45,.95),PURPLE,.05);human('judge',0,3.25,PURPLE);human('A',-1.15,.8,NAVY,True);human('B',1.15,.8,OLIVE,True)
 # physical cards are supplemental labels, positions/roles make stage distinguishable
 if stage==1: cube('prosecutor lectern',(-3,1.5,1.05),(.45,.45,.9),RED);human('prosecutor',-3,1.2,PURPLE)
 if stage==2: cube('appeal papers',(0,2.2,.7),(1.7,.8,.07),PAPER)
 if stage==3: cube('supreme seal',(0,4.18,2.75),(.6,.10,.6),GOLD)
def scene(i):
 clear();setup()
 # 60 actual audio takes: broad distinct factual environments, not a panel swap.
 if i<=5:
  room();car('cash transporter',(1.8,2.5),WHITE,0,True);car('black sedan',(-1.35,.35),BLACK,math.radians(72));
  if i in (2,3,4): human('carrier',-.8,.25,NAVY,False,'hold');bag(-1.12,-.55,1.70)
  if i in (3,4,5): human('masked A',1.0,2.0,NAVY,True);human('masked B',2.45,2.65,OLIVE,True)
  if i==1: human('armed figure',-.7,.6,NAVY,True);gun_hand(-1.2,-.25,2.05)
  cam((-7,-10,4.2),(0,1.1,1.3),48)
 elif i<=10:
  room();car('black sedan',(-1.6,1.1),BLACK,.25);car('switch car',(2.0,3.0),WHITE,0)
  if i<=7: human('masked carrier',-.65,.45,NAVY,True,'hold');bag(-1.0,-.35,1.7)
  elif i==8: gun_hand(-.5,.5,1.8)
  else: human('patrol officer',1.1,1.2,BLUE);car('approaching car',(-2,.5),BLACK,.08)
  cam((-7,-10,4),(0,1.5,1.2),48)
 elif i<=16:
  evidence('mask' if i in (11,12,15) else 'file');
  if i==13: cube('CCTV absent mount',(0,4.6,3.2),(.4,.18,.3),DARK);cube('empty bracket',(0,4.35,3.2),(.15,.12,.5),RED)
  if i==14: car('abandoned sedan',(-1.2,2.0),BLACK,.2);car('second car',(2.4,2.8),WHITE,0)
  if i==16: sph('contained flame',(0,.8,1.4),(.65,.35,.8),ORANGE);cube('mask survives',(1.45,.4,.7),(.45,.25,.05),OLIVE)
  cam((-6,-8,3.8),(0,1.8,1.2),50)
 elif i<=29:
  evidence('dna' if i in (20,21,22,24,25) else 'file');
  if i in (18,19): human('investigator',-2.3,1.0,PURPLE,False,'hold')
  if i in (23,24): cube('arcade cabinet',(2.1,2.2,1.45),(.75,.45,1.4),GREEN);sph('cigarette butt',(.3,.1,.85),(.13,.13,.08),ORANGE)
  cam((-6,-8,3.8),(0,1.4,1.1),50)
 elif i<=37:
  evidence('file');human('detective',-2.2,.8,PURPLE,False,'hold');
  if i in (30,31): human('B identified',1.8,2.1,OLIVE,True)
  if i in (34,35): human('B arrested',1.8,2.1,OLIVE,True);line('detective arm',(1.2,1.7,2),(1.55,1.95,1.7),.1,PURPLE)
  cam((-6,-8,3.8),(0,1.4,1.1),50)
 elif i<=41:
  room('office');cube('spa lockers',(2.8,3.8,1.8),(1.4,.3,1.8),OLIVE);human('A',.6,1.4,NAVY,True);human('detective',-1.2,1.4,PURPLE);line('arrest contact',(-.7,1.3,1.8),(.25,1.35,1.75),.10,PURPLE);cam((-6,-8,3.8),(0,1.7,1.2),50)
 elif i<=48:
  court(1 if i<=44 else 0);cam((-6,-9,4.2),(0,2.1,1.5),48)
 elif i<=56:
  court(2);cam((-6,-9,4.2),(0,2.1,1.5),48)
 else:
  court(3);cube('empty desk',(-2,.2,.72),(1.2,.65,.08),PAPER);cube('empty chair',(-2,1.1,1.0),(.5,.45,.8),DARK);cam((-6,-9,4.2),(0,2.1,1.5),48)
 bpy.context.scene.render.filepath=os.path.join(OUT,f'N{i:03d}.png');bpy.ops.render.render(write_still=True)
# Corrected key tableaux are incorporated in N001–N005 and saved as independent LF2 blend.
for i in range(1,61): scene(i)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'lf2_toon_full_426x240.blend'))
