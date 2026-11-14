# Blender 5.2 headless construction and low-resolution proof renderer.
# Creates original 3D cartoon tableaux: custom posed figures, environments and props.
import bpy, math, os, sys
from mathutils import Vector

ROOT = '/Users/isaac/projects/verdict-kr/work/episodes/v4/n18/terra_toon_recovery'
OUT = os.path.join(ROOT, 'full_renders')
os.makedirs(OUT, exist_ok=True)
W,H=426,240

# Materials: broad flat planes with real 3D lighting; outlines are Freestyle geometry edges.
def mat(name, color, rough=0.75):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
    return m
NAVY=mat('uniform navy',(0.045,0.12,0.20)); OLIVE=mat('field olive',(0.18,0.28,0.17)); SKIN=mat('warm stylized skin',(0.72,0.38,0.22)); DARK=mat('outline dark',(0.015,0.02,0.035)); BLACK=mat('mask black',(0.025,0.03,0.04)); WHITE=mat('eye white',(0.82,0.88,0.87)); IRIS=mat('iris teal',(0.05,0.34,0.36)); GOLD=mat('bank gold',(0.95,0.58,0.10)); RED=mat('warning red',(0.62,0.06,0.05)); GREY=mat('concrete',(0.24,0.29,0.33)); LIGHTGREY=mat('vehicle white',(0.67,0.72,0.72)); BLACKCAR=mat('black sedan',(0.025,0.04,0.06),.25); BAG=mat('cash bag',(0.22,0.12,0.06)); KHAKI=mat('pack khaki',(0.20,0.29,0.16)); BOOT=mat('boots',(0.055,0.065,0.055)); BLUE=mat('light blue',(0.08,0.25,0.40));

def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for d in (bpy.data.materials,): pass

def assign(o, m): o.data.materials.append(m); return o

def cube(name, loc, scale, m, bevel=.12):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('soft cartoon edges','BEVEL'); mod.width=bevel; mod.segments=3
    assign(o,m); return o

def uv(name, loc, scale, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); bpy.ops.object.shade_smooth(); assign(o,m); return o

def curve(name, pts, radius, m, taper=.72):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=2; c.bevel_depth=radius; c.bevel_resolution=2
    s=c.splines.new('BEZIER'); s.bezier_points.add(len(pts)-1)
    for b,p in zip(s.bezier_points,pts): b.co=p; b.handle_left_type='AUTO'; b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); assign(o,m); return o

def look(o, target): o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def camera(loc, target, lens=42):
    bpy.ops.object.camera_add(location=loc); c=bpy.context.object; look(c,target); bpy.context.scene.camera=c; c.data.lens=lens; return c

def light(loc, energy, color, size=5):
    bpy.ops.object.light_add(type='AREA', location=loc); l=bpy.context.object; l.data.energy=energy; l.data.color=color; l.data.shape='DISK'; l.data.size=size; look(l,(0,0,1)); return l

def floor_room(kind='garage'):
    cube('ground',(0,0,-.18),(15,15,.18),GREY,.02)
    cube('back wall',(0,5.7,4),(15,.2,4),GREY,.02)
    if kind=='garage':
        for x in (-5,0,5):
            p=cube('structural pillar',(x,4.9,2.5),(.42,.42,2.5),LIGHTGREY,.08)
            cube('yellow safety stripe',(x,4.42,1.2),(.45,.03,.28),GOLD,.01)
        for x in (-9,-3,3,9): cube('ceiling light',(x,2.3,6), (1.5,.25,.08),WHITE,.05)
    else:
        cube('training wall',(0,5.4,2.6),(14,.25,2.6),OLIVE,.02)
        for x in (-7,0,7): cube('training-frame',(x,5.05,2.7),(.05,.1,2.2),DARK,.01)
        cube('training stripe',(0,5.05,1.2),(14,.03,.18),GOLD,.01)

def vehicle(name, loc, m, facing=0, armored=False):
    body=cube(name+' body',(loc[0],loc[1],.78),(2.1,.88,.55),m,.18); body.rotation_euler[2]=facing
    cabin=cube(name+' cabin',(loc[0]-.28*math.cos(facing),loc[1]-.28*math.sin(facing),1.45),(1.15,.75,.43),m,.22); cabin.rotation_euler[2]=facing
    # High-contrast glazed planes and lamps make the vehicle type legible at 426px.
    for side in (-1,1):
        wx=loc[0]-.25*math.cos(facing)-side*.77*math.sin(facing); wy=loc[1]-.25*math.sin(facing)+side*.77*math.cos(facing)
        win=cube(name+' side glass',(wx,wy,1.48),(.72,.025,.25),BLUE,.025); win.rotation_euler[2]=facing
    front=(loc[0]-2.12*math.cos(facing),loc[1]-2.12*math.sin(facing),.83)
    for side in (-.38,.38):
        lx=front[0]-side*math.sin(facing); ly=front[1]+side*math.cos(facing); lamp=cube(name+' headlamp',(lx,ly,.88),(.15,.035,.10),GOLD,.02); lamp.rotation_euler[2]=facing
    for dx in (-1.35,1.35):
        for side in (-.9,.9):
            x=loc[0]+dx*math.cos(facing)-side*math.sin(facing); y=loc[1]+dx*math.sin(facing)+side*math.cos(facing)
            w=uv(name+' wheel',(x,y,.43),(.36,.20,.36),DARK); w.rotation_euler[0]=math.pi/2
    if armored:
        cube(name+' armored rear',(loc[0]+.9*math.cos(facing),loc[1]+.9*math.sin(facing),1.48),(.7,.78,.55),LIGHTGREY,.1).rotation_euler[2]=facing

def hand(name, wrist, fingers_to, m=SKIN):
    uv(name+' palm',wrist,(.22,.16,.15),m)
    for i,off in enumerate((-.13,-.065,0,.065,.13)):
        a=Vector(wrist); end=Vector(fingers_to)+Vector((off,0,0))
        curve(name+' finger '+str(i),[a+Vector((off*.3,0,0)), (a+end)/2+Vector((0,0,.04)), end],.035,m)

def person(name, hip, facing=0, uniform=NAVY, pose='stand', pack=False, masked=False, grounded=False):
    # Segment hierarchy deliberately visible: pelvis, taper-like torso, neck, shoulder, articulated limbs.
    x,y,z=hip
    pelvis=uv(name+' pelvis',(x,y,z),(.38,.25,.28),uniform)
    torso=uv(name+' ribcage',(x,y,z+.72),(.50,.30,.64),uniform)
    neck=uv(name+' neck',(x,y,z+1.38),(.15,.14,.18),SKIN if not masked else BLACK)
    head=uv(name+' expressive head',(x,y,z+1.72),(.42,.34,.46),SKIN if not masked else BLACK)
    if not masked:
        # eyeballs, eyelids/brows and mouth: enough readable expression at proof resolution
        for side in (-1,1):
            ex=x+side*.16; ey=y-.30; ez=z+1.78
            uv(name+' eye', (ex,ey,ez),(.12,.045,.14),WHITE)
            uv(name+' iris',(ex,ey-.04,ez),(.055,.02,.068),IRIS)
            curve(name+' brow',[(ex-side*.10,ey-.06,ez+.17),(ex+side*.10,ey-.06,ez+.20)],.027,DARK)
        curve(name+' mouth',[(x-.12,y-.345,z+1.53),(x,y-.37,z+1.48),(x+.12,y-.345,z+1.53)],.025,DARK)
    else:
        cube(name+' mask cloth',(x,y-.31,z+1.63),(.38,.055,.22),BLACK,.04)
        for side in (-1,1): uv(name+' masked eye',(x+side*.14,y-.37,z+1.77),(.055,.018,.055),WHITE)
    # shoulders and limbs use kinked curves, not sticks; palm and fingers meet props.
    for side in (-1,1):
        sh=(x+side*.43,y,z+1.1)
        if grounded:
            elbow=(x+side*.55,y-.12,z+.48); wrist=(x+side*.30,y-.35,z+.10); finger=(x+side*.15,y-.55,z+.06)
            hipj=(x+side*.22,y,z-.14); knee=(x+side*.42,y-.18,z-.43); ankle=(x+side*.20,y-.38,z-.70)
        elif pose=='carry' and side==-1:
            elbow=(x+side*.62,y-.45,z+.82); wrist=(x+side*.46,y-.85,z+.62); finger=(x+side*.32,y-.92,z+.60)
            hipj=(x+side*.20,y,z-.18); knee=(x+side*.35,y-.10,z-.70); ankle=(x+side*.48,y-.25,z-1.18)
        else:
            # Bow the resting arms away from the ribcage: at proof size the negative space
            # must survive, rather than letting hands merge into the torso silhouette.
            elbow=(x+side*.82,y-.08,z+.67); wrist=(x+side*.78,y-.34,z+.34); finger=(x+side*.74,y-.50,z+.27)
            hipj=(x+side*.20,y,z-.18); knee=(x+side*.33,y-.06,z-.72); ankle=(x+side*.25,y-.16,z-1.22)
        curve(name+' upper arm',[sh,elbow],.14,uniform); curve(name+' forearm',[elbow,wrist],.11,uniform); hand(name+str(side),wrist,finger,SKIN if not masked else BLACK)
        curve(name+' thigh',[hipj,knee],.18,uniform); curve(name+' calf',[knee,ankle],.14,uniform); cube(name+' boot',(ankle[0],ankle[1]-.10,ankle[2]-.09),(.20,.32,.12),BOOT,.06)
    if pack:
        cube(name+' backpack',(x,y+.32,z+.78),(.43,.18,.58),KHAKI,.12)
        curve(name+' left shoulder strap',[(x-.37,y+.08,z+1.15),(x-.30,y-.12,z+.65),(x-.16,y-.18,z+.25)],.04,KHAKI)
        curve(name+' right shoulder strap',[(x+.37,y+.08,z+1.15),(x+.30,y-.12,z+.65),(x+.16,y-.18,z+.25)],.04,KHAKI)
        # A dark waist belt and side buckle make the pack-to-body attachment readable.
        cube(name+' waist belt',(x,y-.27,z+.30),(.48,.045,.075),DARK,.02)
        cube(name+' belt buckle',(x+.30,y-.33,z+.30),(.08,.03,.10),KHAKI,.01)
    return head

def grounded_trainee_tableau():
    # A deliberate side-lying settled pose: the support route is visually explicit,
    # unlike a vertical rig merely bent down toward the floor.
    uv('grounded torso',(0.10,.95,.46),(.78,.34,.31),OLIVE)
    uv('grounded pelvis',(.66,.96,.39),(.42,.30,.25),OLIVE)
    uv('turned-away head',(-.73,.83,.46),(.34,.29,.34),SKIN)
    cube('closed eye shade',(-.76,.55,.49),(.20,.035,.06),DARK,.02)
    # Back-mounted pack visibly rests against the upper back; paired straps emerge at shoulders.
    cube('grounded backpack',(-.06,1.27,.65),(.47,.18,.36),KHAKI,.10)
    curve('grounded left strap',[(-.35,1.15,.63),(-.32,.83,.66),(-.15,.63,.52)],.045,KHAKI)
    curve('grounded right strap',[(.12,1.15,.63),(.18,.83,.61),(.30,.63,.48)],.045,KHAKI)
    # Supporting forearm laid on the ground, then a second bent arm over the torso.
    curve('grounded supporting arm',[(-.38,.76,.42),(-.46,.35,.18),(-.18,.14,.13)],.115,OLIVE); hand('grounded support hand',(-.18,.14,.13),(-.03,.02,.09))
    curve('grounded upper arm',[(.02,.73,.56),(.20,.42,.47),(.04,.27,.34)],.12,OLIVE); hand('grounded resting hand',(.04,.27,.34),(.14,.12,.30))
    # Rear leg lies nearly long, front leg is distinctly flexed: hip -> knee -> ankle -> boot.
    curve('grounded rear thigh',[(.78,.98,.34),(1.30,1.06,.25),(1.72,.95,.18)],.19,OLIVE); curve('grounded rear calf',[(1.72,.95,.18),(2.07,.74,.14),(2.28,.63,.13)],.15,OLIVE); cube('grounded rear boot',(2.42,.56,.13),(.32,.20,.13),BOOT,.06)
    curve('grounded front thigh',[(.75,.74,.34),(1.13,.38,.24),(1.30,.20,.17)],.20,OLIVE); curve('grounded front calf',[(1.30,.20,.17),(1.00,-.10,.13),(.78,-.18,.13)],.15,OLIVE); cube('grounded front boot',(.61,-.23,.13),(.33,.20,.13),BOOT,.06)
    # tight contact shadows define physical support without injury or intervention.
    for n,p,s in [('torso contact',(.0,.94,.015),(.85,.34,.018)),('arm contact',(-.30,.20,.014),(.45,.16,.016)),('pack contact',(-.06,1.31,.018),(.52,.22,.018)),('knee contact',(1.28,.20,.015),(.28,.20,.016)),('rear boot contact',(2.40,.55,.014),(.46,.24,.016)),('front boot contact',(.60,-.23,.014),(.46,.24,.016))]: uv(n,p,s,DARK)

def configure(scene_name):
    s=bpy.context.scene; s.name=scene_name; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'; s.render.film_transparent=False
    s.world.color=(0.035,0.045,0.065); s.render.use_freestyle=True; s.render.line_thickness=1.2
    s.view_settings.look='AgX - Medium High Contrast'; s.render.resolution_percentage=100
    light((-4,-5,7),1000,(0.72,0.82,1.0),5); light((5,1,4),700,(1.0,.55,.25),4)

def render_lf():
    # Shot 1: black sedan blocks armored cash van nose-to-side in a garage; clear spatial relation.
    clear(); configure('LF2_S01_blocked_vehicles'); floor_room('garage'); vehicle('cash transporter',(1.7,2.6),LIGHTGREY,0,True); vehicle('black sedan',(-1.25,.20),BLACKCAR,math.radians(72),False)
    # painted lane gives direction: sedan is diagonal across the van's forward route, not parked parallel.
    cube('travel lane',(1.7,0.0,.015),(.32,5,.02),GOLD,.01)
    camera((-8,-11,5.0),(0,1.3,1.0),46); bpy.context.scene.render.filepath=os.path.join(OUT,'lf2_01_block.png'); bpy.ops.render.render(write_still=True)
    # Shot 2: carrier and actual bag foreground, two masked people enter deeper route.
    clear(); configure('LF2_S02_bag_and_approach'); floor_room('garage'); vehicle('cash transporter',(2.5,2.8),LIGHTGREY,0,True)
    carrier=person('bag carrier',(-.8,.45,1.25),pose='carry'); cube('cash bag',(-1.12,-.55,1.78),(.45,.20,.32),BAG,.10); curve('bag handle',[(-1.34,-.55,2.04),(-1.12,-.55,2.28),(-.90,-.55,2.04)],.055,BAG)
    person('masked approach A',(1.2,2.25,1.25),masked=True); person('masked approach B',(2.45,2.9,1.25),masked=True)
    camera((-6,-9,4.3),(0.25,.7,1.45),48); bpy.context.scene.render.filepath=os.path.join(OUT,'lf2_02_approach.png'); bpy.ops.render.render(write_still=True)
    # Shot 3: anonymous masked silhouette holds pistol safely away from any person; no target/gore inferred.
    clear(); configure('LF2_S03_anonymous_gunfire'); floor_room('garage'); vehicle('cash transporter',(2.5,3.4),LIGHTGREY,0,True); person('masked foreground',(-.7,.6,1.25),masked=True)
    cube('compact handgun',(-1.42,-.18,2.18),(.35,.08,.09),DARK,.025); uv('muzzle flash',(-1.8,-.18,2.18),(.20,.20,.20),GOLD)
    # foreground concrete post produces actual occlusion and avoids assigning a target.
    cube('foreground pillar',(-3.1,-1.4,2.6),(.38,.38,2.6),LIGHTGREY,.07); camera((-6,-8,4.2),(-.1,.9,1.55),50); bpy.context.scene.render.filepath=os.path.join(OUT,'lf2_03_gunfire.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'lf2_toon_proof.blend'))

def render_n18():
    # Shot 1: full kit has visible straps and boot ground contact; no enacted drill.
    clear(); configure('N18_S01_training_kit'); floor_room('training'); person('anonymous trainee',(-.8,.7,1.3),uniform=OLIVE,pack=True,pose='stand'); uv('left boot contact',(-1.02,.54,.02),(.32,.42,.025),DARK); uv('right boot contact',(-.58,.54,.02),(.32,.42,.025),DARK); camera((-7,-10,4.8),(-.3,1.2,1.35),48); bpy.context.scene.render.filepath=os.path.join(OUT,'n18_01_kit.png'); bpy.ops.render.render(write_still=True)
    # Shot 2: different still composition and stance, without inventing command/violence.
    clear(); configure('N18_S02_training_context'); floor_room('training'); person('anonymous trainee',(0,1.0,1.3),uniform=OLIVE,pack=True,pose='carry'); cube('foreground frame',(-3,-.5,2.0),(.18,.18,2.0),DARK,.03); camera((-6,-8,3.8),(0,1.3,1.35),52); bpy.context.scene.render.filepath=os.path.join(OUT,'n18_02_context.png'); bpy.ops.render.render(write_still=True)
    # Shot 3: grounded, non-gory, single anonymous body; backpack/forearm/knee/boots visibly support pose.
    clear(); configure('N18_S03_grounded_non_gory'); floor_room('training'); grounded_trainee_tableau()
    camera((-7,-10,3.9),(.55,.65,.35),50); bpy.context.scene.render.filepath=os.path.join(OUT,'n18_03_grounded.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'n18_toon_proof.blend'))

def caption_card(title, line, accent=GOLD):
    # Physical title placard is used only for factual institutional context, not as a substitute for scenes.
    cube('placard',(0,3.9,2.1),(4.8,.10,1.05),DARK,.06)
    for i in range(7): cube('placard rule '+str(i),(-3.7+i*1.15,3.76,2.65),(.38,.02,.035),accent,.01)

def court_scene(kind):
    clear(); configure('court_'+kind); cube('court floor',(0,0,-.18),(15,15,.18),GREY,.02); cube('court back',(0,5.5,3.5),(15,.2,3.5),DARK,.02)
    cube('judge bench',(0,3.8,1.25),(3.2,.55,1.1),BAG,.12); person('judge',(0,4.05,1.35),uniform=NAVY)
    if kind=='prosecutor':
        person('prosecutor',(-2.5,1.0,1.25),uniform=NAVY); cube('case file',(-2.5,.42,1.7),(.46,.07,.28),RED,.02)
    elif kind=='defendants':
        person('defendant A',(-1.3,.9,1.25),uniform=BLUE); person('defendant B',(1.3,.9,1.25),uniform=BLUE)
        cube('separate rail',(0,.1,.65),(4.1,.12,.55),DARK,.04)
    elif kind=='witness':
        cube('witness stand',(0,1.4,1.0),(1.0,.55,.85),BAG,.08); person('witness',(0,1.65,1.25),uniform=BLUE)
        cube('judge side bench',(-3.1,3.7,1.1),(1.25,.45,.9),BAG,.08); person('judge',(-3.1,3.95,1.3),uniform=NAVY)
    elif kind=='records':
        cube('records desk',(0,1.7,.85),(4.2,1.35,.35),BAG,.10)
        for i in range(6): cube('case folder '+str(i),(-1.8+(i%3)*1.8,1.15+(i//3)*.82,1.28),(.55,.34,.06),RED if i%2 else BLUE,.02)
        person('clerk',(3.1,2.2,1.25),uniform=NAVY)
    elif kind=='judgeclose':
        cube('open decision',(0,2.88,2.28),(1.0,.06,.52),WHITE,.02); person('judge',(0,4.05,1.35),uniform=NAVY)
    else:
        person('court clerk',(-2.3,1.2,1.25),uniform=NAVY); person('court attendee',(2.5,1.4,1.25),uniform=BLUE)
    if kind=='judgeclose': camera((-4.8,-7.5,3.8),(0,3.2,1.9),58)
    elif kind=='records': camera((-6.5,-8,4.8),(0,1.9,1.15),52)
    elif kind=='witness': camera((-7,-9,4.4),(-.5,2.2,1.35),48)
    else: camera((-7,-10,4.8),(0,2.4,1.45),47)

def training_scene(kind):
    clear(); configure('training_'+kind); floor_room('training')
    if kind=='kit':
        person('trainee',(-.8,.7,1.3),uniform=OLIVE,pack=True); uv('left boot contact',(-1.02,.54,.02),(.42,.48,.025),DARK); uv('right boot contact',(-.58,.54,.02),(.42,.48,.025),DARK)
    elif kind=='six':
        for i in range(6): person('trainee '+str(i),(-3+i*1.15,1.1+(i%2)*.28,1.25),uniform=OLIVE,pack=True)
    elif kind=='grounded':
        grounded_trainee_tableau()
    elif kind=='pack':
        person('packing trainee',(-1.0,1.1,1.25),uniform=OLIVE,pack=True); cube('supply shelf',(2.8,3.5,1.5),(1.2,.35,1.5),BAG,.05)
        for i in range(7): cube('book '+str(i),(2.0+(i%3)*.4,2.9+(i//3)*.16,.55+(i//3)*.24),(.16,.11,.10),GOLD,.01)
    else:
        person('trainee A',(-1.1,.8,1.3),uniform=OLIVE,pack=True); person('trainee B',(1.1,1.5,1.3),uniform=OLIVE,pack=True)
    camera((-7,-10,4.4),(0,1.35,1.1),48)

def hospital_scene():
    clear(); configure('hospital'); cube('hospital floor',(0,0,-.18),(15,15,.18),LIGHTGREY,.02); cube('hospital wall',(0,5.4,3.4),(15,.2,3.4),WHITE,.02)
    cube('bed',(0,1.3,.72),(2.5,1.0,.24),WHITE,.10); cube('blanket',(0,1.1,1.03),(1.5,.76,.20),BLUE,.10); cube('privacy screen',(3.3,3.1,1.9),(.08,1.4,1.9),LIGHTGREY,.04)
    person('clinician',(-2.6,1.5,1.25),uniform=WHITE); cube('record',(-2.3,.72,1.8),(.38,.05,.27),BLUE,.02)
    camera((-7,-10,4.6),(0,1.7,1.05),48)

def family_scene():
    clear(); configure('family_letter'); cube('table',(0,1.5,.75),(3.4,1.2,.18),BAG,.08); person('reader',(0,2.1,1.15),uniform=BLUE)
    cube('letter',(0,.65,1.05),(1.05,.72,.025),WHITE,.01); curve('letter line',[(-.65,.58,1.09),(0,.58,1.09),(.65,.58,1.09)],.025,DARK)
    cube('warm wall',(0,5.2,3.2),(15,.2,3.2),GOLD,.02); camera((-6,-9,4),(0,1.8,1.1),50)

def memorial_scene():
    clear(); configure('memorial'); cube('memorial wall',(0,5.3,3.4),(15,.2,3.4),DARK,.02); cube('memorial table',(0,1.7,.72),(4,1.1,.2),BAG,.06); cube('portrait frame',(0,2.15,2.0),(1.05,.08,1.25),WHITE,.04)
    for i in range(5): uv('white flower '+str(i),(-1.8+i*.9,1.15,1.08),(.19,.12,.10),WHITE)
    person('visitor',(-2.8,1.2,1.22),uniform=BLUE); camera((-7,-10,4.6),(0,2,1.3),48)

def policy_scene():
    clear(); configure('policy'); floor_room('training'); cube('procedure board',(1.9,4.7,2.3),(2.7,.08,1.65),WHITE,.04)
    for i in range(3): cube('check '+str(i),(1.0,4.57,3.05-i*.55),(1.3,.02,.045),OLIVE,.01)
    person('trainee',(-2.0,1.0,1.25),uniform=OLIVE,pack=True); cube('calendar',(1.9,4.55,1.55),(1.1,.02,.35),GOLD,.02); camera((-7,-10,4.5),(0,2.1,1.4),48)

def render_library():
    jobs=[('training_kit',lambda:training_scene('kit')),('training_six',lambda:training_scene('six')),('training_pack',lambda:training_scene('pack')),('training_grounded',lambda:training_scene('grounded')),('court_wide',lambda:court_scene('wide')),('court_prosecutor',lambda:court_scene('prosecutor')),('court_defendants',lambda:court_scene('defendants')),('court_witness',lambda:court_scene('witness')),('court_records',lambda:court_scene('records')),('court_judgeclose',lambda:court_scene('judgeclose')),('hospital',hospital_scene),('family',family_scene),('memorial',memorial_scene),('policy',policy_scene)]
    for name,fn in jobs:
        fn(); bpy.context.scene.render.filepath=os.path.join(OUT,name+'.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'n18_full_preview_toon.blend'))

render_library()
