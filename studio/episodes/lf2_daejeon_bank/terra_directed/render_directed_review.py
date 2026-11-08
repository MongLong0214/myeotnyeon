# LF2 v6fix2 directed review. Renders one actual animated block per invocation.
# Only writes inside terra_directed; output is intentionally a low-resolution parent-review sample.
import bpy, os, sys, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 426, 240, 12
STAGE = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'event'

# --- materials and basic geometry ---
def mat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .7
    return m
INK=mat('ink',(0.012,.018,.03)); FLOOR=mat('garage floor',(.17,.21,.24)); WALL=mat('wall',(.075,.10,.14)); WHITE=mat('transport white',(.78,.79,.73)); BLACK=mat('black sedan',(.012,.018,.028)); GLASS=mat('glass',(.04,.23,.36)); GOLD=mat('sodium gold',(.92,.52,.07)); NAVY=mat('bank navy',(.04,.14,.25)); OLIVE=mat('robber olive',(.16,.28,.19)); MASK=mat('mask',(.015,.018,.022)); SKIN=mat('skin',(.55,.28,.16)); RED=mat('prosecutor red',(.52,.035,.03)); PURPLE=mat('appeal purple',(.24,.08,.32)); PAPER=mat('record cream',(.75,.70,.55)); GREEN=mat('sentence green',(.06,.36,.20)); BLUE=mat('clerk blue',(.08,.28,.42)); BAGMAT=mat('cash-bag brown',(.34,.12,.035)); MASKPLATE=mat('mask plate',(.78,.78,.70))

def cube(n, loc, scale, material, bevel=.03):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=n; o.scale=scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.materials.append(material)
    if bevel:
        q=o.modifiers.new('soft edges','BEVEL'); q.width=bevel; q.segments=2
    return o

def sphere(n, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=loc)
    o=bpy.context.object; o.name=n; o.scale=scale; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.materials.append(material); return o

def rod(n, a, b, radius, material):
    d=Vector(b)-Vector(a); mid=(Vector(a)+Vector(b))/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=d.length, location=mid)
    o=bpy.context.object; o.name=n; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); o.data.materials.append(material); return o

def key(o, frame, loc=None, rot=None, hide=None):
    if loc is not None: o.location=loc; o.keyframe_insert('location',frame=frame)
    if rot is not None: o.rotation_euler=rot; o.keyframe_insert('rotation_euler',frame=frame)
    if hide is not None:
        o.hide_render=hide; o.keyframe_insert('hide_render',frame=frame)

def linear_all(o):
    # Blender 5 action layers no longer expose Action.fcurves directly. Default interpolation is sufficient for this review render.
    return

def parent(parts, n):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0)); root=bpy.context.object; root.name=n
    for x in parts: x.parent=root
    return root

def human(n, x, y, clothes, masked=False):
    # Low-poly body with readable face, eyes/brows, and articulated shoulder-elbow-wrist arms.
    parts=[]
    parts += [sphere(n+' head',(x,y,2.55),(.29,.23,.33), MASK if masked else SKIN), cube(n+' torso',(x,y,1.84),(.34,.22,.54),clothes,.09)]
    for q in (-1,1):
        parts += [rod(n+f' leg{q}',(x+q*.16,y,1.37),(x+q*.20,y-.03,.34),.12,clothes), cube(n+f' boot{q}',(x+q*.20,y-.10,.20),(.16,.22,.09),INK,.02)]
        shoulder=(x+q*.34,y,2.08); elbow=(x+q*.47,y-.08,1.72); wrist=(x+q*.48,y-.20,1.43)
        parts += [rod(n+f' upper{q}',shoulder,elbow,.10,clothes),rod(n+f' lower{q}',elbow,wrist,.09,clothes),sphere(n+f' hand{q}',wrist,(.105,.09,.10),MASK if masked else SKIN)]
    if masked:
        # A pale face plate and two dark eye slots make the anonymity readable rather than a featureless hair silhouette.
        parts += [cube(n+' mask plate',(x,y-.225,2.55),(.23,.025,.16),MASKPLATE,.025), sphere(n+' mask eyeL',(x-.085,y-.255,2.58),(.042,.015,.035),INK), sphere(n+' mask eyeR',(x+.085,y-.255,2.58),(.042,.015,.035),INK)]
    else:
        for q in (-1,1):
            parts += [sphere(n+f' eye{q}',(x+q*.105,y-.225,2.61),(.055,.025,.055),INK), rod(n+f' brow{q}',(x+q*.16,y-.235,2.74),(x+q*.055,y-.24,2.77),.018,INK)]
    return parent(parts,n+' root')

def car(n, x, y, material, armored=False):
    ps=[cube(n+' body',(x,y,.68),(1.72,.74,.42),material,.13), cube(n+' cabin',(x-.22,y,1.22),( .88,.60,.34),material,.12)]
    for q in (-1,1): ps.append(cube(n+' glass'+str(q),(x-.22,y+q*.61,1.26),(.55,.025,.17),GLASS,.01))
    # Readable vehicle cues survive the dark garage: roof, wheels, two lamps, and a wide rear door on the transporter.
    ps += [cube(n+' roof',(x-.25,y,1.56),(.62,.48,.08),material,.03), cube(n+' lampL',(x-1.73,y-.45,.72),(.07,.05,.07),GOLD,.01),cube(n+' lampR',(x-1.73,y+.45,.72),(.07,.05,.07),GOLD,.01)]
    if armored: ps.append(cube(n+' rear',(x+.82,y,1.23),(.56,.63,.40),WHITE,.06))
    for dx in (-1.16,1.16):
        for q in (-.72,.72): ps.append(sphere(n+' wheel',(x+dx,y+q*.72,.30),(.24,.13,.24),INK))
    return parent(ps,n+' root')

def bag(n,x,y,z):
    ps=[cube(n+' case',(x,y,z),(.38,.16,.25),BAGMAT,.06),rod(n+' handleL',(x-.22,y,z+.24),(x,y,z+.48),.035,BAGMAT),rod(n+' handleR',(x,y,z+.48),(x+.22,y,z+.24),.035,BAGMAT)]
    return parent(ps,n+' root')

def camera(loc,target,lens=46):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; c.data.lens=lens; c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=c; return c

def configure(end):
    s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.fps=FPS; s.frame_start=(162 if STAGE=='courtpatch' else 1); s.frame_end=(396 if STAGE=='courtpatch' else end); s.render.threads=1; s.render.film_transparent=False
    s.world.color=(.010,.015,.025)
    bpy.ops.object.light_add(type='AREA',location=(-4,-5,7)); bpy.context.object.data.energy=700; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=5
    bpy.ops.object.light_add(type='AREA',location=(5,1,5)); bpy.context.object.data.energy=500; bpy.context.object.data.color=(1,.48,.18); bpy.context.object.data.size=4

def garage():
    cube('ground',(0,0,-.2),(13,13,.2),FLOOR,.01); cube('back wall',(0,5.6,3.2),(13,.15,3.2),WALL,.01)
    for x in (-5.6,0,5.6):
        cube('pillar',(x,5.25,2.1),(.26,.26,2.1),WHITE,.01); cube('stripe',(x,4.98,1.05),(.27,.015,.23),GOLD,.01)
    for y in (-1,2.3): cube('parking marker',(0,y,.02),(5.7,.025,.015),WHITE,0)

def court(appeal=False):
    cube('court floor',(0,0,-.2),(11,10,.2),FLOOR,.01); cube('court back',(0,5.6,3.4),(11,.15,3.4),WALL,.01)
    benchmat=PURPLE if appeal else BLUE
    cube('bench',(0,4.15,1.7),(4.3,.48,.92),benchmat,.05); cube('bench top',(0,3.64,2.35),(4.55,.12,.14),PAPER,.02)
    if appeal: sphere('appeal seal',(0,3.55,3.0),(.45,.08,.45),GOLD)
    cube('A dock',(-1.45,1.45,.73),(.68,.42,.68),NAVY,.04); cube('B dock',(1.45,1.45,.73),(.68,.42,.68),OLIVE,.04)
    cube('lectern',(-3.25,1.55,.82),(.43,.43,.82),RED,.04); cube('record cart',(3.0,2.35,.58),(.52,.38,.56),PAPER,.04)

def render_event():
    end=338; configure(end); garage()
    van=car('cash transporter',2.3,2.5,WHITE,True); sedan=car('black sedan',-6.5,-.4,BLACK)
    workers=[human('carrier1',.4,1.0,NAVY),human('carrier2',1.05,1.55,NAVY),human('carrier3',1.62,2.0,NAVY)]
    robberA=human('masked A',-2.4,.1,NAVY,True); robberB=human('masked B',-2.7,.65,OLIVE,True)
    b1=bag('bag one',.25,.72,1.08); b2=bag('bag two',.82,.72,1.08); trolley=cube('cash trolley',(.55,.76,.62),(.85,.35,.11),WHITE,.03)
    # approach / block at cue 12-13
    key(van,1,(5.7,2.5,0)); key(van,57,(2.3,2.5,0)); key(van,338,(2.3,2.5,0))
    for i,w in enumerate(workers): key(w,1,(0,0,0)); key(w,57,(-i*.22,0,0)); key(w,338,(-i*.22,0,0))
    key(sedan,1,(-6.5,-.4,0)); key(sedan,57,(-6.5,-.4,0)); key(sedan,124,(-.9,.35,0)); key(sedan,260,(-.9,.35,0)); key(sedan,338,(-6.0,-1.6,0))
    key(robberA,1,(0,0,0)); key(robberA,124,(0,0,0)); key(robberA,178,(1.35,.8,0)); key(robberA,338,(1.35,.8,0))
    key(robberB,1,(0,0,0)); key(robberB,124,(0,0,0)); key(robberB,178,(1.62,.12,0)); key(robberB,220,(2.25,.72,0)); key(robberB,338,(2.25,.72,0))
    # physical contact: robber B grasps bag two and carries it to the sedan's rear.
    key(b2,1,(0,0,0)); key(b2,178,(0,0,0)); key(b2,220,(1.55,.30,.36)); key(b2,260,(-1.35,-.10,.20)); key(b2,338,(-6.4,-1.6,.20))
    # carrier1 retreats/falls as an anonymous gun is raised; no wound or identity claim.
    key(workers[0],124,(0,0,0)); key(workers[0],178,(-.40,-.28,0)); key(workers[0],200,(-.72,-.52,-.72),(.75,0,.2)); key(workers[0],338,(-.72,-.52,-.72),(.75,0,.2))
    gun=parent([cube('pistol grip',(-1.98,.18,1.92),(.07,.06,.18),INK,.01),cube('pistol barrel',(-1.72,.18,2.10),(.32,.07,.065),INK,.01)],'anonymous pistol')
    key(gun,1,(0,0,0)); key(gun,124,(0,0,0)); key(gun,178,(.35,.05,.25),(-.18,0,0)); key(gun,338,(.35,.05,.25),(-.18,0,0))
    flash=sphere('muzzle flash',(-1.28,.23,2.14),(.16,.08,.16),GOLD); key(flash,1,hide=True); key(flash,185,hide=True); key(flash,186,hide=False); key(flash,188,hide=True); key(flash,338,hide=True)
    cam=camera((-7.4,-9.4,5.0),(0,1.15,1.25),42); key(cam,1,cam.location,cam.rotation_euler); key(cam,124,(-7.4,-9.4,5.0),(Vector((0,1.15,1.25))-Vector((-7.4,-9.4,5.0))).to_track_quat('-Z','Y').to_euler()); key(cam,178,(-6.5,-7.1,3.3),(Vector((-.2,.8,1.25))-Vector((-6.5,-7.1,3.3))).to_track_quat('-Z','Y').to_euler()); key(cam,220,(-5.9,-7.7,3.6),(Vector((-.5,.55,1.0))-Vector((-5.9,-7.7,3.6))).to_track_quat('-Z','Y').to_euler()); key(cam,338,(-6.8,-9,4.2),(Vector((-.2,.7,1.0))-Vector((-6.8,-9,4.2))).to_track_quat('-Z','Y').to_euler())
    for o in bpy.context.scene.objects: linear_all(o)
    out=os.path.join(ROOT,'event_frames'); os.makedirs(out,exist_ok=True); bpy.context.scene.render.filepath=os.path.join(out,'frame_'); bpy.ops.render.render(animation=True)

def render_court():
    end=480; configure(end); court(False)
    judge=human('trial judge',0,3.35,BLUE); prosecutor=human('prosecutor',-3.25,.95,RED); clerk=human('clerk',3.0,1.75,BLUE); A=human('A defendant',-1.45,1.05,NAVY,True); B=human('B defendant',1.45,1.05,OLIVE,True)
    # prosecutor moves to lectern; judge remains seated as distinct authority.
    key(prosecutor,1,(0,-1.5,0)); key(prosecutor,42,(0,0,0)); key(prosecutor,82,(0,0,0)); key(clerk,1,(0,0,0)); key(clerk,82,(0,0,0)); key(clerk,140,(-.65,.15,0)); key(clerk,240,(-.65,.15,0))
    # Rebuild second court within same timeline as a purposeful court-domain change.
    appeal_parts=[]
    for o in list(bpy.context.scene.objects):
        if o.name.startswith(('bench','court','appeal','A dock','B dock','lectern','record cart')): appeal_parts.append(o)
    # stage color transformation marks appeal court rather than paper-card repetition.
    bench=bpy.data.objects.get('bench'); seal=sphere('appeal seal',(0,3.54,3.02),(.46,.08,.46),GOLD); key(seal,1,hide=True); key(seal,240,hide=True); key(seal,246,hide=False); key(seal,480,hide=False)
    key(bench,1,hide=False); key(bench,240,hide=False)
    # Change bench material to purple at appeal via duplicate hidden purple face.
    appeal_front=cube('appeal bench face',(0,3.62,1.7),(4.32,.03,.90),PURPLE,.02); key(appeal_front,1,hide=True); key(appeal_front,240,hide=True); key(appeal_front,246,hide=False); key(appeal_front,480,hide=False)
    appeal_judge=human('appeal judge',0,3.35,PURPLE); key(appeal_judge,1,hide=True); key(appeal_judge,240,hide=True); key(appeal_judge,246,hide=False); key(appeal_judge,480,hide=False)
    key(judge,1,hide=False); key(judge,240,hide=False); key(judge,246,hide=True); key(judge,480,hide=True)
    # Appeal clerk physically changes the two separated docket markers to equal final-state markers.
    mA=cube('A sentence marker',(-1.45,.86,.22),(.30,.06,.12),PAPER,.01); mB=cube('B sentence marker',(1.45,.86,.22),(.30,.06,.12),PAPER,.01); finalA=cube('A final marker',(-1.45,.86,.22),(.30,.06,.12),GREEN,.01); finalB=cube('B final marker',(1.45,.86,.22),(.30,.06,.12),GREEN,.01)
    for o in (mA,mB): key(o,1,hide=False); key(o,365,hide=False); key(o,366,hide=True); key(o,480,hide=True)
    for o in (finalA,finalB): key(o,1,hide=True); key(o,365,hide=True); key(o,366,hide=False); key(o,480,hide=False)
    key(clerk,240,(-.65,.15,0)); key(clerk,300,(-.15,.25,0)); key(clerk,365,(-.15,.25,0)); key(clerk,420,(-.65,.15,0)); key(clerk,480,(-.65,.15,0))
    cam=camera((-7.2,-9.2,4.1),(0,2.05,1.35),45); key(cam,1,cam.location,cam.rotation_euler); key(cam,82,(-6.1,-6.8,3.1),(Vector((0,2.35,1.28))-Vector((-6.1,-6.8,3.1))).to_track_quat('-Z','Y').to_euler()); key(cam,140,(-4.9,-5.8,2.7),(Vector((0,2.2,1.1))-Vector((-4.9,-5.8,2.7))).to_track_quat('-Z','Y').to_euler()); key(cam,246,(-6.9,-8.6,4.6),(Vector((0,2.25,1.55))-Vector((-6.9,-8.6,4.6))).to_track_quat('-Z','Y').to_euler()); key(cam,480,(-6.9,-8.6,4.6),(Vector((0,2.25,1.55))-Vector((-6.9,-8.6,4.6))).to_track_quat('-Z','Y').to_euler())
    for o in bpy.context.scene.objects: linear_all(o)
    out=os.path.join(ROOT,'court_frames'); os.makedirs(out,exist_ok=True); bpy.context.scene.render.filepath=os.path.join(out,'frame_'); bpy.ops.render.render(animation=True)

if STAGE=='event': render_event()
elif STAGE in ('court','courtpatch'): render_court()
else: raise SystemExit('stage must be event, court, or courtpatch')
