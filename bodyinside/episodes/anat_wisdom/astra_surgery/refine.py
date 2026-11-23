"""Run in Blender on surgery/surgery_draft1.blend. Geometry uses millimetres."""
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion, noise

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parent / 'surgery'))
import build as base
from build import world, frame, link, mesh, tube, lathe, visible, key, tool_pose, pose, margin

S = bpy.context.scene
O = bpy.data.objects
V = Vector
sin, cos, pi, exp = math.sin, math.cos, math.pi, math.exp
rng = random.Random(591)
samples = [1.55, 4.25, 11.75, 15.45, 24.05, 30.95, 35.15, 38.70, 43.1]


def disable(obj):
    if isinstance(obj, str):
        obj = O.get(obj)
    if obj:
        obj.animation_data_clear()
        obj.hide_render = True


def node(tree, kind, **inputs):
    n = tree.nodes.new(kind)
    for k, v in inputs.items():
        socket = n.inputs[k]
        if isinstance(v, bpy.types.NodeSocket):
            tree.links.new(v, socket)
        else:
            socket.default_value = v
    return n


def ramp(nt, value, stops):
    n = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(value, n.inputs[0])
    elements = n.color_ramp.elements
    for i, (at, rgb) in enumerate(stops):
        e = elements[i] if i < 2 else elements.new(at)
        e.position = at
        e.color = (*rgb, 1)
    return n.outputs[0]


def shade(name, colors, freq, rough, relief, sss=0, coat=.3, metal=0, fluid=0,
          veins=0, pitting=False, ior=1.43, stretch=(1,1,1)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexCoord')
    v = nt.nodes.new('ShaderNodeVectorMath')
    v.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Object'], v.inputs[0])
    v.inputs[1].default_value = tuple(k*1000 for k in stretch)
    uv = v.outputs['Vector']
    large = node(nt,'ShaderNodeTexNoise', Vector=uv, Scale=freq, Detail=3.6, Roughness=.54,
                 Distortion=.37)
    micro = node(nt,'ShaderNodeTexNoise', Vector=uv, Scale=freq*10, Detail=2.5, Roughness=.54)
    pigment = ramp(nt,large.outputs['Fac'],[(.22,colors[0]),(.54,colors[1]),(.80,colors[2])])
    tiny = micro.outputs['Fac']
    if veins or pitting:
        # Distort the cell boundaries so the subepithelial vessels vary in width
        # and direction. Dentin and cortical pores use isolated cell centres.
        warp = nt.nodes.new('ShaderNodeVectorMath')
        warp.operation = 'SCALE'
        nt.links.new(large.outputs['Color'],warp.inputs[0])
        warp.inputs['Scale'].default_value = 1.9
        add = nt.nodes.new('ShaderNodeVectorMath')
        add.operation='ADD'
        nt.links.new(uv,add.inputs[0])
        nt.links.new(warp.outputs[0],add.inputs[1])
        vor = nt.nodes.new('ShaderNodeTexVoronoi')
        vor.feature = 'DISTANCE_TO_EDGE' if veins else 'F1'
        vor.inputs['Scale'].default_value = .37 if veins else 2.65
        nt.links.new(add.outputs[0],vor.inputs['Vector'])
        vessel = ramp(nt,vor.outputs['Distance'],[(.008 if veins else .14,(.41,.15,.22) if veins else (.33,.17,.11)),
                                                 (.047 if veins else .38,(1,1,1))])
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=veins or .66
        nt.links.new(pigment,mix.inputs[1]); nt.links.new(vessel,mix.inputs[2])
        pigment = mix.outputs[0]
        if pitting:
            tiny = vessel
    nt.links.new(pigment,bs.inputs['Base Color'])
    nt.links.new(ramp(nt,micro.outputs['Fac'],[(.23,(rough*.65,)*3),(.77,(min(.92,rough*1.4),)*3)]),bs.inputs['Roughness'])
    broad = node(nt,'ShaderNodeBump', Strength=.29, Distance=relief*.0014, Height=large.outputs['Fac'])
    bump = node(nt,'ShaderNodeBump', Strength=.34, Distance=relief*.00038, Height=tiny, Normal=broad.outputs[0])
    nt.links.new(bump.outputs[0],bs.inputs['Normal'])
    for k, val in {'Metallic':metal,'Subsurface Weight':sss,'Subsurface Scale':.00058,
                   'Subsurface Radius':(1,.36,.21),'Coat Weight':coat,'Coat Roughness':max(.07,rough*.58),
                   'Coat IOR':1.333,'Transmission Weight':fluid,'IOR':ior}.items():
        bs.inputs[k].default_value=val
    return m


def remat(obj, *materials):
    obj.data.materials.clear()
    for mat in materials:
        obj.data.materials.append(mat)


def replace_slots(obj, mats):
    for i in range(len(obj.data.materials)):
        obj.data.materials[i] = mats[min(i,len(mats)-1)]


def organic(name, p, scale, mat, parent=None, seed=0):
    # A smooth, non-axisymmetric drop or soft aggregate with its origin at p.
    pts, faces = [], []
    n, h = 18, 12
    for j in range(h+1):
        lat = -pi/2+pi*(j+.001)/(h+.002)
        for i in range(n):
            a=2*pi*i/n
            r=1+.053*sin(3*a+seed)*cos(lat)**2+.035*sin(3*lat+a+seed)
            pts.append((r*cos(lat)*cos(a),r*cos(lat)*sin(a),r*sin(lat)))
    for j in range(h):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
    faces.extend((tuple(reversed(range(n))),tuple(range(h*n,(h+1)*n))))
    o=mesh(name,pts,faces,mat,parent)
    o.location=V(p)/1000 if parent else world(p)
    o.scale=scale
    return o


def deform(o, name, points, keys):
    if not o.data.shape_keys:
        o.shape_key_add(name='Rest')
    sk=o.shape_key_add(name=name)
    for v,p in zip(sk.data,points):
        v.co=V(p)/1000
    for t,w in keys:
        sk.value=w
        sk.keyframe_insert(data_path='value',frame=frame(t))
    return sk


def scaled(o, keys):
    for t, values in keys:
        key(o,'scale',t,values)


def field_materials():
    global gum, raw, bone, liner, blood, dilute, water, coag, enamel, cement, dentin, steel, satin, silk
    gum=shade('Attached mucosa • stipple and subepithelial vessels',[(.16,.024,.033),(.39,.085,.104),(.58,.18,.19)],.40,.29,.17,.34,.48,veins=.32,stretch=(1.45,.83,1))
    raw=shade('Reflected periosteum • fibrous wet surface',[(.125,.01,.02),(.30,.038,.044),(.53,.13,.115)],.65,.31,.24,.30,.52,veins=.39,stretch=(1.9,.63,1.2))
    bone=shade('Cut cortex • ivory trabeculae and pores',[(.25,.122,.067),(.65,.46,.28),(.86,.74,.54)],.54,.32,.32,.12,.39,pitting=True)
    liner=shade('Socket wall • vascular cancellous bed',[(.065,.008,.011),(.26,.057,.039),(.55,.25,.145)],.83,.29,.28,.16,.40,pitting=True)
    blood=shade('Blood film • oxyhaemoglobin',[(.028,.00065,.0015),(.112,.0024,.006),(.19,.0075,.010)],.63,.145,.038,.12,.74,fluid=.10,ior=1.35)
    dilute=shade('Suction effluent • diluted blood',[(.33,.049,.043),(.53,.135,.13),(.66,.27,.24)],1.2,.15,.048,.07,.57,fluid=.36,ior=1.334)
    water=shade('Irrigant • saline',[(.68,.795,.82),(.86,.92,.95),(.96,.98,1)],1.2,.085,.015,0,.46,fluid=.88,ior=1.333)
    coag=shade('Coagulum • erythrocytes and fibrin',[(.018,.00065,.002),(.067,.0022,.008),(.171,.010,.018)],1.6,.235,.30,.16,.60,veins=.35)
    enamel=shade('Hydrated enamel',[(.45,.36,.235),(.74,.65,.48),(.90,.84,.69)],.33,.23,.047,.30,.56,ior=1.62)
    cement=shade('Root surface • cementum',[(.31,.18,.105),(.57,.42,.25),(.78,.64,.445)],.65,.31,.12,.17,.31,stretch=(1.5,.57,1))
    dentin=shade('Dentin • fresh fracture',[(.39,.245,.106),(.69,.51,.28),(.865,.72,.48)],1.4,.35,.17,.16,.30,pitting=True)
    steel=shade('Polished instrument steel',[(.44,.48,.53),(.58,.62,.65),(.69,.72,.75)],2.3,.18,.010,metal=.94,stretch=(6,6,.35))
    satin=shade('Turned surgical steel',[(.32,.34,.37),(.43,.46,.49),(.55,.57,.58)],3.0,.29,.023,metal=.94,stretch=(.7,.7,8))
    silk=shade('Violet braided suture',[(.007,.002,.012),(.039,.010,.059),(.10,.043,.12)],8.0,.34,.08,coat=.19)
    for o in list(S.objects):
        if o.type not in ('MESH','CURVE'): continue
        for i,m in enumerate(list(o.data.materials)):
            if not m: continue
            for stem,new in [('Natural enamel',enamel),('Cementum',cement),('Freshly sectioned dentin',dentin),
                ('Wet gingiva',gum),('Vascular underside',raw),('Wet cut cortical',bone),('Deep red liquid',blood),
                ('Wet surgical stainless',steel),('Satin instrument',satin),('Clear saline',water),
                ('Blood diluted',dilute),('Braided violet',silk),('Socket coagulum',coag)]:
                if m.name.startswith(stem):
                    o.data.materials[i]=new
                    break
    replace_slots(O['Mandible'],[bone,liner,bone,bone,liner])
    replace_slots(O['M2Septum'],[bone])
    nerve=shade('Neural epineurium • soft ochre fascicles',[(.29,.15,.058),(.52,.325,.135),(.69,.49,.235)],1.4,.33,.10,.24,.39,stretch=(3,.37,3))
    remat(O['Nerve2'],nerve)


def socket_field():
    # A buccal cutaway exposes a short length of the canal in the lateral views.
    # The operative cameras look down into the same bowl from a steeper angle.
    global rim
    def ring(a):
        ca,sa=cos(a),sin(a)
        und=1+.032*sin(3*a+.4)+.024*cos(7*a-.2)
        return V((30.05+5.72*und*ca,-35.65+9.42*und*sa,
                  35.5-5.3*max(ca,0)**2+.90*max(-ca,0)+.72*sa+.46*sin(3*a+.2)+.19*sin(9*a)))
    rim=ring
    rows=[(.11,-3.1),(.30,-2.65),(.54,-1.75),(.73,-.9),(.87,-.25),(.97,-.20),(1.0,0),(1.07,.20),(1.17,.24),(1.30,.20),(1.53,.36),(1.82,.39),(2.35,.30),(3.2,.22),(5.5,.14)]
    count=128; pts=[]; faces=[]
    for j,(r,lift) in enumerate(rows):
        for i in range(count):
            a=i*2*pi/count
            edge=ring(a)
            floor=27.1+.35*sin(a*3+.3)
            h=floor+(edge.z-floor)*min(1,r)**2.45+lift
            if r>1:
                h+= max(-cos(a),0)*min(6,(r-1)*7) -max(cos(a),0)*(min(8,(r-1)*9))
                h+=min(1.5,(r-1)*2)*sin(3*a+.38*r)
            uneven=.14*sin(11*a+2.1*r)*sin(3.9*r+.6)+.10*cos(19*a-5*r)
            pts.append((30.05+(edge.x-30.05)*r,-35.65+(edge.y+35.65)*r,h+uneven))
    for j in range(len(rows)-1):
        for i in range(count):
            a=j*count+i; b=j*count+(i+1)%count
            faces.append((a,a+count,b+count,b))
    obj=mesh('Alveolar bed, cortical rim and contiguous vestibule',pts,faces,liner)
    for m in (bone,raw,gum): obj.data.materials.append(m)
    for p in obj.data.polygons:
        j=p.index//count; a=(p.index%count+.5)*2*pi/count
        # Blend exposed cortex into attached mucosa using an irregular edge.
        threshold=7.2+.72*sin(3*a)+.50*sin(7*a+.3)
        p.material_index=0 if j<4 else (1 if j<threshold else (2 if j<threshold+1.3 else 3))
    for n in ('RimOut','RimRam','CanalPlug','GumLayer','M2Septum',
              'Lingual edge of gingival incision','Buccal mucoperiosteal flap',
              'Moist reflection along the flap margin','Shallow blood pool in the empty alveolus',
              'Blood clot beneath the sutures'):
        disable(n)
    for o in list(S.objects):
        if o.name.startswith(('Blood bead at','Blood in the cut socket','Blood welling along')): disable(o)
    # The surface skin surrounds both ends of the reflected flap. Keep the
    # inherited sectional mandible and nerve in the lower, lateral cutaway.
    replace_slots(O['Posterior oral lining'],[raw])
    visible(obj,[(3,44.05)])
    visible(O['Mandible'],[(0,3)])
    # Leave a small teaching window in the socket floor over the intact bundle.
    for v in obj.data.vertices:
        x,y,z=v.co*1000
        if 25<x<36 and -36<y<-25:
            w=exp(-((x-30.15)/2.22)**4-((y+30.35)/4.35)**4)
            v.co.z-=.0063*w
    return obj


def gingival_field():
    global flap, bank, seamline
    nx,ny=32,88
    grid=[(i/nx,j/ny) for i in range(nx+1) for j in range(ny+1)]
    quads=[(i*(ny+1)+j,(i+1)*(ny+1)+j,(i+1)*(ny+1)+j+1,i*(ny+1)+j+1)
           for i in range(nx) for j in range(ny)]
    def edge(s):
        y=-49+27*s
        ss=max(0,min(1,(y+44)/17))
        p=margin(ss)
        p.y=y
        return p
    seamline=edge
    def profile(u,s,kind):
        p=edge(s)
        envelope=sin(pi*s)**.74
        if kind=='bank':
            return p+V((-.045-u*15, .6*u*sin(5*s), -1.45*sin(pi*u)+2.3*u**2+.42*sin(s*14)*u))
        p.x+=.018+u*(8.6+1.4*envelope)
        p.y+=.4*u*sin(s*7)
        p.z+=.42*sin(pi*u)-9.5*u**2.65 + .29*sin(12*s)*u+.11*sin(24*s+6*u)*sin(pi*u)
        return p
    def reflected(u,s,stage):
        p=profile(u,s,'flap')
        w=sin(pi*s)**.76*(1-u)**1.05
        if stage=='lift':
            p+=V((3.5*w,.52*w,4.65*w*(.40+sin(pi*(.22+.67*u))) ))
        else:
            p+=V(((12.55+2.8*sin(pi*u))*w, .8*w*sin(4*s),
                  (-7.25+4.6*sin(pi*u))*w))
        return p
    def ribbon(name,kind):
        pts=[profile(u,s,kind) for u,s in grid]
        faces=quads if kind=='flap' else [tuple(reversed(f)) for f in quads]
        o=mesh(name,pts,faces,gum)
        o.data.materials.append(raw)
        o.shape_key_add(name='Rest')
        if kind=='flap':
            deform(o,'Elevator lifts the margin',[reflected(u,s,'lift') for u,s in grid],[(0,0),(9.65,0),(11.05,1),(12.8,0)])
            deform(o,'Buccal reflection, attached at base',[reflected(u,s,'open') for u,s in grid],[(0,1),(2.95,1),(3,0),(10.75,0),(12.8,1),(36.65,1),(37.85,0)])
        # Each scalpel pressure key parts only the tissue already traversed.
        for y in (-43,-40,-37,-34,-31,-28):
            t=7.40+(y+43)*.144
            pts2=[]
            for (u,s),p in zip(grid,pts):
                w=exp(-((p.y-y)/2.25)**2)*(1-u)**4
                pts2.append(p+V(((.70 if kind=='flap' else -.42)*w,0,-.36*w)))
            deform(o,'Local incision at '+str(y),pts2,[(0,0),(t-.16,0),(t+.15,1),(9.8,1),(11.7,0)])
        tipx,tipy=30.65,-25.5
        deform(o,'Needle compression', [p+V((-.24,0,-1.05))*exp(-((p.x-tipx)/1.33)**2-((p.y-tipy)/1.75)**2) for p in pts],
               [(3,0),(4.05,0),(4.36,1),(4.67,.43),(5.66,.40),(6.14,0)])
        for i,cy in enumerate((-35.10,-35.40)):
            cx=27.35 if i==0 else 30.05
            deform(o,'Suture tent '+str(i+1),[p+V(((.18 if i==0 else -.20),0,.76))*exp(-((p.x-cx)/1.25)**2-((p.y-cy)/1.3)**2) for p in pts],
                   [(37.72,0),(38.14+.40*i,0),(38.44+.40*i,1),(38.79+.40*i,0)])
        # Small posterior opening adjacent to the interrupted stitch reveals the clot.
        sign=1 if kind=='flap' else -1
        deform(o,'Edge apposition at knot',[p+V((sign*2.20*w,0,-.8*w)) for (u,s),p in zip(grid,pts)
               for w in [exp(-((p.y+31.5)/2.75)**2)*(1-u)**2.5]],[(36.5,0),(37.85,1),(40.5,.83),(44,.83)])
        solid=o.modifiers.new('Full mucoperiosteal thickness','SOLIDIFY')
        solid.thickness=.00089 if kind=='flap' else .00105
        solid.offset=-1; solid.material_offset=1; solid.material_offset_rim=1
        sub=o.modifiers.new('Continuous rounded margins','SUBSURF'); sub.levels=1; sub.render_levels=1
        return o
    flap=ribbon('Attached buccal flap • deforming wound lip','flap')
    bank=ribbon('Lingual gingiva • wound margin','bank')
    visible(flap,[(3,44.05)])
    track=[margin(i/32)+V((-.07,0,-.13+.08*sin(i*1.53))) for i in range(33)]
    bleed=tube('Capillary welling in the incision',track,.28,blood,radii=[.25+.73*sin(pi*(i+.12)/32.24)**.42 for i in range(33)])
    visible(bleed,[(7.35,37.46)])
    for t,v in [(7.35,0),(8.5,.50),(9.65,1)]: key(bleed.data,'bevel_factor_end',t,v,'LINEAR')
    for i in range(4):
        pts=[p+V((-.15-.12*i+.10*sin(j*1.1+i),.1*i,-.085-.01*i)) for j,p in enumerate(track)]
        film=tube('Wicking film at raw margin',pts,.10+i*.012,blood,radii=[.10+.60*abs(sin(j*.39+i)) for j in range(33)])
        visible(film,[(7.45,37.40)])
        for t,v in [(7.45+i*.08,0),(9.83+i*.09,1)]:key(film.data,'bevel_factor_end',t,v)
    # A real oblique cut through the cannula leaves an elliptical bore.
    needle=O['Long bevel needle']
    disable(needle)
    rig=O['Aspirating dental syringe']
    pts=[]; faces=[]; n=28
    for radius,z,slant in [(.143,.47,.44),(.151,1.35,0),(.151,15.35,0),(.085,15.35,0),(.085,.47,.26)]:
        for i in range(n):
            a=2*pi*i/n; pts.append((radius*cos(a),radius*sin(a),z+slant*cos(a)))
    for j in range(5):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n; k=(j+1)%5*n
            faces.append((a,b,k+(i+1)%n,k+i))
    bevel=mesh('Hollow needle • oblique bevel and lumen',pts,faces,steel,rig)
    visible(bevel,[(3,6.75)])
    # Align the insertion and withdrawal with the actual posterior surface.
    target=V((30.65,-25.5,38.95)); d=V((.57,.16,.82)).normalized()
    tool_pose(rig,[(t,target+d*h,d,110) for t,h in [(3,12),(3.6,5.1),(4.05,.52),(4.38,-1.13),(4.85,-3.6),(5.66,-3.65),(6.04,-.2),(6.30,3.5),(6.72,14)]])
    drop=organic('Puncture bead after withdrawal',target+V((-.05,-.06,.06)),(1,1,1),blood)
    visible(drop,[(6.07,10)])
    scaled(drop,[(6.07,(.03,.03,.01)),(6.36,(.32,.35,.21)),(6.78,(.36,.40,.23))])
    # Steer the periosteal elevator beneath the reflecting free edge.
    tool_pose(O['Periosteal elevator'],[(9.85,(30,-40,45),(.41,-.5,.76),-15),
        (10.35,(29.6,-38.9,38.5),(.33,-.52,.8),-2),(11.10,(32.6,-38.25,42.2),(.33,-.52,.8),17),
        (11.80,(35.3,-38.1,39.0),(.38,-.49,.84),30),(12.50,(39.3,-37.7,33.35),(.49,-.38,.82),43),
        (13.09,(48,-44,52),(.50,-.43,.77),45)])


def cinematography():
    D=bpy.data
    for o in S.objects:
        if o.type=='LIGHT': o.hide_render=True
    cases=[
        [(0,(31,-32.8,26.05),(.91,-.22,.43),29.0,56,-10),(2.95,(31.1,-34.15,26.5),(.93,-.14,.38),28,58,-5)],
        [(3,(30.75,-25.4,39.4),(.52,-.37,.78),31.7,53,-9),
         (4.45,(30.65,-25.5,39.1),(.42,-.45,.78),27.8,58,-8),
         (6.26,(30.2,-26.55,39.1),(.50,-.34,.80),29.3,56,-6),
         (7.4,(29.0,-42.1,39.0),(.54,-.22,.80),32.4,49,-5),
         (9.58,(29.5,-32.0,38.8),(.55,-.22,.81),30.2,54,-4),
         (11.0,(31.5,-37.8,39),(.48,-.31,.82),32.5,54,-2),
         (12.95,(32.6,-37.6,35.9),(.54,-.29,.82),34.8,52,-1)],
        [(13,(33.65,-40.0,35.75),(.49,.36,.80),34.0,53,-2),
         (15.6,(34.1,-39.1,34.8),(.46,.49,.74),32.0,56,0),
         (18.5,(32.7,-37.5,34.35),(.55,.35,.76),32,54,1),
         (21.2,(33.5,-35.6,32.8),(.71,.32,.65),28.2,56,2),
         (23.95,(33.3,-35.45,32.7),(.74,.32,.60),27.6,57,3),
         (25.75,(33.8,-37.2,35.7),(.66,.30,.70),34.4,51,2),
         (27.55,(32,-31.4,32.6),(.63,-.34,.73),32,54,0),
         (29.65,(33.4,-30.8,35),(.61,-.33,.73),34.9,51,-2),
         (31.30,(32.9,-30.9,32.8),(.54,-.34,.77),33.2,53,-3),
         (32.95,(31.8,-32.8,31.8),(.76,-.27,.62),31.8,53,-3)],
        [(33,(30.5,-35.1,30.1),(.53,-.27,.8),34.6,52,-4),
         (35.0,(30.7,-35.3,30.4),(.47,-.33,.82),31.7,55,-3),
         (36.85,(30.5,-35.1,33),(.52,-.25,.82),34.3,52,-2),
         (38.55,(29.08,-35.12,38.8),(.52,-.27,.81),29.1,55,-2),
         (40.56,(29.05,-34.9,38.8),(.51,-.26,.82),28.9,56,0),
         (43.95,(30.5,-31.45,34.7),(.19,-.15,.97),30,58,3)]
    ]
    markers=sorted(S.timeline_markers,key=lambda m:m.frame)
    for mk,rows in zip(markers,cases):
        camera=mk.camera
        camera.animation_data_clear(); camera.data.animation_data_clear()
        data=camera.data
        data.dof.use_dof=True; data.dof.aperture_fstop=68; data.dof.aperture_blades=7
        data.dof.aperture_ratio=1.02
        for t,at,d,dist,lens,roll in rows:
            loc=world(at)+V(d).normalized()*dist/1000
            rot=(world(at)-loc).to_track_quat('-Z','Y') @ Quaternion((0,0,1),math.radians(roll))
            key(camera,'location',t,loc); key(camera,'rotation_quaternion',t,rot)
            key(data,'lens',t,lens); key(data,'dof.focus_distance',t,dist/1000)
    at=world((31.5,-35.5,35.8))
    for name,pos,power,w,h,col in [
        ('Operatory lamp • reflected key',(52,-55,72),.083,10,17,(1,.88,.78)),
        ('Slim saline specular',(23,-22,58),.039,3,15,(.89,.94,1)),
        ('Handpiece strip reflection',(45,-8,39),.029,4,25,(.98,.75,.66)),
        ('Broad diffuse fill',(51,-35,57),.025,26,26,(.87,.90,1)),
        ('Cavity fill',(49,-38,26),.020,11,11,(1,.84,.77))]:
        light=D.lights.new(name,'AREA')
        light.energy=power
        light.shape='RECTANGLE'; light.size=w/1000; light.size_y=h/1000; light.color=col
        ob=link(name,light); ob.location=world(pos); ob.rotation_euler=(at-ob.location).to_track_quat('-Z','Y').to_euler()
    S.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.105
    S.view_settings.look='AgX - Medium High Contrast'
    S.view_settings.exposure=-2.15
    S.render.engine='CYCLES'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL'; prefs.refresh_devices()
    for device in prefs.devices:
        device.use=device.type=='METAL'
    S.cycles.device='GPU'
    S.cycles.samples=12
    S.cycles.use_denoising=True
    S.cycles.denoiser='OPENIMAGEDENOISE'
    S.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
    S.cycles.max_bounces=5; S.cycles.diffuse_bounces=2; S.cycles.glossy_bounces=2; S.cycles.transmission_bounces=3
    S.cycles.sample_clamp_indirect=2.5
    S.cycles.seed=59; S.cycles.use_animated_seed=False
    S.render.use_persistent_data=True
    S.render.resolution_percentage=100
    S.render.image_settings.compression=15
    S.render.filepath='//frames/f_'
    S.frame_set(1)


def main():
    field_materials()
    socket_field()
    # Replace the two draft paths completely, including keys between our poses.
    O['Aspirating dental syringe'].animation_data_clear()
    O['Periosteal elevator'].animation_data_clear()
    gingival_field()
    effect_script=OUT/'effects.py'
    if effect_script.exists():
        exec(compile(effect_script.read_text(),str(effect_script),'exec'),globals())
        build_effects()
        detail_script=OUT/'detail.py'
        exec(compile(detail_script.read_text(),str(detail_script),'exec'),globals())
        polish()
    cinematography()
    final_script = OUT / 'surface_pass.py'
    exec(compile(final_script.read_text(), str(final_script), 'exec'), globals())
    finish_surfaces()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'surgery_draft2.blend'),compress=True)
    if '--preview' in sys.argv:
        S.render.resolution_percentage=55
        S.cycles.samples=7
        directory=Path(os.environ.get('ASTRA_CHECK','/tmp/astra_surgery_previews'))
        directory.mkdir(parents=True,exist_ok=True)
        for idx,t in enumerate(samples,1):
            S.frame_set(frame(t))
            S.render.filepath=str(directory / f'{idx:02d}.png')
            bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
