# LF2 directed v2: two self-contained review blocks, Blender EEVEE + exact PCM trims.
# Invocation: blender -b --factory-startup --python render_directed_v2.py -- event|court
import bpy, os, sys, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.abspath(__file__))
W,H,FPS=640,360,12
STAGE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'event'

def m(n,c):
    x=bpy.data.materials.new(n); x.diffuse_color=(*c,1); return x
INK=m('ink',(.015,.02,.03)); FLOOR=m('floor',(.12,.16,.19)); WALL=m('wall',(.05,.075,.10)); WHITE=m('van',(.72,.76,.73)); BLACK=m('sedan',(.01,.015,.025)); GLASS=m('glass',(.04,.22,.32)); GOLD=m('gold',(.95,.55,.06)); NAVY=m('navy',(.035,.13,.25)); OLIVE=m('olive',(.13,.26,.17)); RED=m('prosecutor',(.55,.035,.035)); BLUE=m('clerk',(.04,.25,.42)); PURPLE=m('appeal',(.28,.06,.35)); SKIN=m('skin',(.55,.30,.18)); MASK=m('mask',(.04,.05,.055)); BAG=m('cash bag',(.34,.12,.025)); PAPER=m('paper',(.78,.72,.55)); GREEN=m('final sentence',(.04,.40,.18))

def cube(n,loc,sc,ma,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=n; o.scale=sc; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma)
    if bevel: mod=o.modifiers.new('edge','BEVEL'); mod.width=bevel; mod.segments=2
    return o
def sph(n,loc,sc,ma):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=loc); o=bpy.context.object; o.name=n; o.scale=sc; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma); return o
def cyl(n,loc,rad,depth,ma,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=rad,depth=depth,location=loc,rotation=rot); o=bpy.context.object; o.name=n; o.data.materials.append(ma); return o
def root(n, parts):
    bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,0)); r=bpy.context.object; r.name=n
    for o in parts: o.parent=r
    return r
def k(o,f,loc=None,rot=None,hide=None):
    if loc is not None: o.location=loc; o.keyframe_insert('location',frame=f)
    if rot is not None: o.rotation_euler=rot; o.keyframe_insert('rotation_euler',frame=f)
    if hide is not None: o.hide_render=hide; o.keyframe_insert('hide_render',frame=f)
def linear(o):
    a=o.animation_data
    if a and a.action:
        for fc in a.action.fcurves:
            for p in fc.keyframe_points:p.interpolation='LINEAR'
def label(n,text,loc,size,ma,rot=(math.pi/2,0,0)):
    bpy.ops.object.text_add(location=loc,rotation=rot); o=bpy.context.object; o.name=n; o.data.body=text; o.data.align_x='CENTER'; o.data.align_y='CENTER'; o.data.size=size; o.data.extrude=.008; o.data.materials.append(ma); return o

def configure(end):
    s=bpy.context.scene
    # Factory-startup removes the startup cube; explicit delete makes this invariant on every run.
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.fps=FPS; s.frame_start=1; s.frame_end=end; s.render.film_transparent=False
    s.world.color=(.008,.012,.02)
    bpy.ops.object.light_add(type='AREA',location=(-4,-5,7)); bpy.context.object.data.energy=850; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=5
    bpy.ops.object.light_add(type='AREA',location=(5,2,5)); bpy.context.object.data.energy=500; bpy.context.object.data.color=(1,.48,.16); bpy.context.object.data.size=4

def camera(loc,target,lens=48):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.data.lens=lens; c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=c; return c

def person(n,loc,clothes,masked=False):
    # All geometry is local to its root: no absolute child transforms or doubled offsets.
    parts=[]; parts += [sph(n+' head',(0,0,2.48),(.27,.23,.31),MASK if masked else SKIN),cube(n+' torso',(0,0,1.76),(.33,.22,.53),clothes,.07)]
    # Articulated visual limbs: upper/lower arm and legs individually keyed below.
    for side in (-1,1):
        parts += [cyl(n+f' thigh{side}',(side*.15,0,.90),.115,.78,clothes,(-.12,0,0)),cyl(n+f' shin{side}',(side*.15,-.05,.39),.10,.55,clothes,(.10,0,0)),cube(n+f' foot{side}',(side*.15,-.18,.12),(.14,.22,.08),INK,.02)]
        parts += [cyl(n+f' upper{side}',(side*.42,-.01,1.96),.095,.55,clothes,(0,side*.65,0)),cyl(n+f' lower{side}',(side*.55,-.13,1.55),.08,.48,clothes,(0,side*.38,0)),sph(n+f' hand{side}',(side*.62,-.20,1.32),(.10,.08,.10),MASK if masked else SKIN)]
    if masked:
        parts += [cube(n+' plate',(0,-.225,2.48),(.22,.025,.15),PAPER,.02), sph(n+' eyeL',(-.08,-.255,2.50),(.04,.01,.03),INK),sph(n+' eyeR',(.08,-.255,2.50),(.04,.01,.03),INK)]
    else:
        parts += [sph(n+' eyeL',(-.09,-.23,2.54),(.04,.015,.04),INK),sph(n+' eyeR',(.09,-.23,2.54),(.04,.015,.04),INK)]
    r=root(n+' root',parts); r.location=loc; return r

def walk(p,frames,positions):
    # Root path plus alternating leg/arm swing makes walking legible in a fixed camera.
    for f,pos in zip(frames,positions):
        k(p,f,loc=pos)
        phase=(f//8)%2
        for side in (-1,1):
            a=.34*(1 if side==(-1 if phase else 1) else -1)
            k(bpy.data.objects[p.name.replace(' root','')+f' thigh{side}'],f,rot=(a,0,0)); k(bpy.data.objects[p.name.replace(' root','')+f' shin{side}'],f,rot=(-a*.7,0,0)); k(bpy.data.objects[p.name.replace(' root','')+f' upper{side}'],f,rot=(-a*.7,side*.65,0))

def car(n,loc,ma,van=False):
    ps=[cube(n+' body',(0,0,.63),(1.55,.70,.38),ma,.12),cube(n+' cabin',(-.20,0,1.13),(.78,.55,.32),ma,.10),cube(n+' roof',(-.2,0,1.47),(.55,.45,.07),ma,.02)]
    for sy in (-1,1):ps += [cube(n+' window'+str(sy),(-.2,sy*.56,1.15),(.49,.02,.16),GLASS,.01)]
    for dx in (-1.05,1.05):
        for sy in (-1,1):ps += [sph(n+' wheel',(dx,sy*.69,.28),(.23,.12,.23),INK)]
    if van: ps += [cube(n+' rear',(1.05,0,1.05),(.42,.62,.36),WHITE,.04)]
    r=root(n+' root',ps);r.location=loc;return r

def bag(n,loc):
    ps=[cube(n+' case',(0,0,0),(.35,.15,.23),BAG,.05),cyl(n+' handleL',(-.19,0,.29),.028,.35,BAG,(0,.55,0)),cyl(n+' handleR',(.19,0,.29),.028,.35,BAG,(0,-.55,0))];r=root(n+' root',ps);r.location=loc;return r

def garage():
    cube('ground',(0,0,-.18),(13,13,.18),FLOOR,.01); cube('wall',(0,5.6,3.1),(13,.12,3.1),WALL,.01)
    for x in (-5.5,0,5.5):cube('pillar',(x,5.25,2.0),(.22,.22,2),WHITE,.01)
    for y in (-.6,2.2):cube('line',(0,y,.01),(6,.025,.01),WHITE,0)
    label('reconstruction','사건 재구성 (CCTV 아님)',(0,5.42,5.4),.34,PAPER,(math.pi/2,0,0))
def event():
    end=338; configure(end); garage()
    van=car('cash transporter',(5.5,2.45,0),WHITE,True); sedan=car('black sedan',(-6,-.4,0),BLACK)
    workers=[person(f'carrier{i}',(.3+i*.52,1.0+i*.32,0),NAVY) for i in range(3)]
    ra=person('masked A',(-2.4,.25,0),NAVY,True); rb=person('masked B',(-2.7,.68,0),OLIVE,True)
    b1=bag('bag one',(.30,.72,1.02)); b2=bag('bag two',(.87,.72,1.02)); trolley=cube('trolley',(.59,.75,.54),(.84,.34,.10),WHITE,.03)
    # transport team walks in and reaches the two bags.
    k(van,1,(5.5,2.45,0));k(van,56,(2.3,2.45,0));k(van,end,(2.3,2.45,0))
    for i,w in enumerate(workers): walk(w,[1,22,44,56],[(.3+i*.52,1+i*.32,0),(.2+i*.25,.9+i*.22,0),(-.05+i*.06,.80+i*.07,0),(-i*.18,0,0)])
    # sedan blocks, robbers leave separate doors and converge.
    k(sedan,1,(-6,-.4,0));k(sedan,100,(-6,-.4,0));k(sedan,124,(-.9,.35,0));k(sedan,270,(-.9,.35,0));k(sedan,end,(-6,-1.6,0))
    walk(ra,[100,124,150,178],[(0,0,0),(0,0,0),(.35,.10,0),(1.20,.72,0)])
    walk(rb,[100,124,150,178,210],[(0,0,0),(0,0,0),(.28,-.05,0),(1.26,.02,0),(1.72,.30,0)])
    # Gun appears beside A's raised hand—not separate from it. Non-graphic retreat/collapse follows.
    gun=root('pistol root',[cube('pistol grip',(0,0,0),(.06,.05,.17),INK,.01),cube('pistol barrel',(.25,0,.14),(.27,.06,.05),INK,.01)])
    for f,pos,hide in [(1,(0,0,0),True),(145,(1.52,.61,1.72),True),(150,(1.52,.61,1.72),False),(205,(1.52,.61,1.72),False)]:k(gun,f,pos,hide=hide)
    # carrier 0 steps toward trolley then falls away; no wound shown.
    k(workers[0],150,(-.05,0,0));k(workers[0],178,(-.45,-.22,0));k(workers[0],202,(-.72,-.46,-.68),rot=(.72,0,.20));k(workers[0],end,(-.72,-.46,-.68),rot=(.72,0,.20))
    # B's hand, handle and bag remain co-located throughout the grasp-to-car path.
    for f,pos in [(1,(.87,.72,1.02)),(178,(.87,.72,1.02)),(210,(1.70,.10,1.30)),(240,(-.55,.10,1.30)),(270,(-1.52,-.05,1.08)),(end,(-6,-1.6,1.02))]: k(b2,f,pos)
    # B follows identical bag/contact journey, hand visibly down at handle then rises to rear seat.
    k(rb,210,(1.72,.30,0));k(rb,240,(-.52,.10,0));k(rb,270,(-1.45,-.05,0));k(rb,end,(-5.85,-1.5,0))
    # fixed readable action coverage; not camera-motion proof.
    cam=camera((-7.3,-9.0,4.6),(0,1.1,1.3),43)
    for f,loc,tgt in [(1,(-7.3,-9,4.6),(0,1.1,1.3)),(124,(-7.3,-9,4.6),(0,1.1,1.3)),(150,(-6.4,-7.2,3.4),(.3,.55,1.25)),(210,(-6.2,-7.2,3.5),(.1,.45,1.0)),(270,(-6.2,-7.8,3.7),(-.8,.25,1.0)),(end,(-7.3,-9,4.6),(-.2,.6,.9))]: k(cam,f,loc,(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler())
    for o in bpy.context.scene.objects:linear(o)
    out=os.path.join(ROOT,'directed_v2_event_frames');os.makedirs(out,exist_ok=True);bpy.context.scene.render.filepath=os.path.join(out,'frame_');bpy.ops.render.render(animation=True)

def courtroom(appeal=False):
    cube('court floor',(0,0,-.2),(11,10,.2),FLOOR,.01);cube('court wall',(0,5.6,3.2),(11,.12,3.2),WALL,.01)
    benchmat=PURPLE if appeal else BLUE;cube('bench',(0,4.1,1.7),(4.3,.48,.9),benchmat,.05);cube('bench top',(0,3.62,2.34),(4.55,.10,.12),PAPER,.02)
    cube('A dock',(-1.5,1.45,.72),(.65,.42,.67),NAVY,.04);cube('B dock',(1.5,1.45,.72),(.65,.42,.67),OLIVE,.04);cube('lectern',(-3.25,1.55,.82),(.42,.42,.82),RED,.04);cube('record cart',(3,2.3,.58),(.5,.35,.54),PAPER,.04)
    if appeal:sph('appeal seal',(0,3.5,3.0),(.44,.06,.44),GOLD)
def court():
    end=481;configure(end);courtroom(False)
    judge=person('trial judge',(0,3.28,0),BLUE);pros=person('prosecutor',(-3.25,.1,0),RED);clerk=person('clerk',(3,1.72,0),BLUE);A=person('A defendant',(-1.5,1.04,0),NAVY);B=person('B defendant',(1.5,1.04,0),OLIVE)
    label('A label','A',(-1.5,.93,.25),.32,PAPER);label('B label','B',(1.5,.93,.25),.32,PAPER)
    # Prosecutor walks to lectern, then makes an open-arm submission gesture (not judge action).
    walk(pros,[1,30,60,82],[(-3.25,-1.2,0),(-3.25,-.7,0),(-3.25,-.2,0),(0,0,0)])
    for side in (-1,1): k(bpy.data.objects[f'prosecutor upper{side}'],70,rot=(-.35,side*.65,0));k(bpy.data.objects[f'prosecutor upper{side}'],112,rot=(-1.05,side*.75,0));k(bpy.data.objects[f'prosecutor upper{side}'],150,rot=(-.35,side*.65,0))
    # First-instance: judge turns to separated docks; clerk transports records toward the cart.
    k(judge,82,(0,0,0),rot=(0,0,0));k(judge,150,(0,0,0),rot=(0,0,.18));k(clerk,82,(0,0,0));k(clerk,145,(-.70,.15,0));k(clerk,230,(-.70,.15,0))
    record=cube('case record',(3,1.35,1.25),(.25,.05,.34),PAPER,.01);k(record,82,(0,0,0));k(record,145,(-.7,.15,0));k(record,230,(-.7,.15,0))
    # Appeal is an actual separate purple bench/court, not an overlapping hidden root.
    appeal=[]
    for o in [cube('appeal bench',(0,4.1,1.7),(4.3,.50,.92),PURPLE,.05),cube('appeal top',(0,3.60,2.36),(4.55,.10,.12),PAPER,.02),sph('appeal seal',(0,3.49,3.02),(.44,.06,.44),GOLD),person('appeal judge',(0,3.28,0),PURPLE)]: appeal.append(o)
    for o in appeal:
        k(o,1,hide=True);k(o,245,hide=True);k(o,246,hide=False);k(o,end,hide=False)
    # Remove whole first stage objects individually (hide_render is not inherited).
    for o in [judge]:
        # root plus every child so trial judge never overlaps appeal judge.
        k(o,1,hide=False);k(o,245,hide=False);k(o,246,hide=True);k(o,end,hide=True)
        for ch in o.children:k(ch,1,hide=False);k(ch,245,hide=False);k(ch,246,hide=True);k(ch,end,hide=True)
    # clerk physically switches separate 20-year marker into shared final markers.
    old=cube('B 20y marker',(1.5,.83,.22),(.32,.05,.11),PAPER,.01);newa=cube('A final marker',(-1.5,.83,.22),(.32,.05,.11),GREEN,.01);newb=cube('B final marker',(1.5,.83,.22),(.32,.05,.11),GREEN,.01)
    for o in (newa,newb):k(o,1,hide=True);k(o,365,hide=True);k(o,366,hide=False);k(o,end,hide=False)
    k(old,1,hide=False);k(old,365,hide=False);k(old,366,hide=True);k(old,end,hide=True)
    k(clerk,245,(0,0,0));k(clerk,310,(-.20,.12,0));k(clerk,365,(-.20,.12,0));k(clerk,425,(0,0,0));k(clerk,end,(0,0,0))
    # distinct court compositions: prosecutor wide, trial rear, appeal high frontal.
    cam=camera((-7.2,-9.1,4.2),(0,2.0,1.3),45)
    for f,loc,tgt in [(1,(-7.2,-9.1,4.2),(0,2,1.3)),(82,(-6.0,-6.6,3.1),(0,2.35,1.2)),(145,(-5.4,-5.7,2.8),(0,2.2,1.2)),(246,(-6.9,-8.5,4.8),(0,2.3,1.5)),(366,(-6.9,-8.5,4.8),(0,2.3,1.5)),(end,(-6.9,-8.5,4.8),(0,2.3,1.5))]:k(cam,f,loc,(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler())
    for o in bpy.context.scene.objects:linear(o)
    out=os.path.join(ROOT,'directed_v2_court_frames');os.makedirs(out,exist_ok=True);bpy.context.scene.render.filepath=os.path.join(out,'frame_');bpy.ops.render.render(animation=True)
if STAGE=='event':event()
elif STAGE=='court':court()
else:raise SystemExit('use event or court')
