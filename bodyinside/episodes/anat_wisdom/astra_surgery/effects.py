"""Additional motion and contact geometry. Executed by refine.py in its Blender scene."""


def shape_curve(name, paths, radii, width, mat, windows, parent=None):
    times=sorted(paths)
    o=tube(name,paths[times[0]],width,mat,parent,radii=radii)
    for i,p in enumerate(o.data.splines[0].bezier_points):
        for t in times:
            p.co=V(paths[t][i])/1000
            p.keyframe_insert(data_path='co',frame=frame(t))
    visible(o,windows)
    return o


def hollow_tip(name,rig,radius,wall,length):
    n=40; pts=[]; faces=[]
    for r,z in [(radius*.96,0),(radius,.15),(radius,length),(radius-wall,length),(radius-wall,.05)]:
        for j in range(n):
            a=j*2*pi/n
            pts.append((r*cos(a),r*sin(a),z+(.25*cos(a) if z<1 else 0)))
    for i in range(5):
        for j in range(n):
            lo=i*n+j; hi=i*n+(j+1)%n; k=(i+1)%5*n
            faces.append((lo,hi,k+(j+1)%n,k+j))
    return mesh(name,pts,faces,steel,rig)


def procedural_spray():
    drill=O['Surgical handpiece']
    rotor=O['Rotating carbide']
    # A broken specular on an asymmetric land makes the rotor readable even at 20 fps.
    for ang in (0,2.55):
        pts=[(.43*cos(ang),.43*sin(ang),1.55),(.63*cos(ang-.30),.63*sin(ang-.30),1.28),
             (.86*cos(ang-.67),.86*sin(ang-.67),.80),(.66*cos(ang-.94),.66*sin(ang-.94),.35)]
        glint=tube('Polished cutting land',pts,.068,steel,rotor,radii=(.58,1,1,.45))
        visible(glint,[(0,3),(13,23.08),(27,28.06)])
    for o in S.objects:
        if o.name.startswith('Handpiece saline jet'):
            o.data.bevel_depth*=1.72
    windows=[(0,2.99),(13.6,17.96),(19.3,22.79),(27.25,27.87)]
    # A thin turbulent stream, finer airborne mist and short heavy chip paths.
    for i in range(36):
        is_chip=i>=26
        a=2*pi*i/36+rng.uniform(-.35,.35)
        chipmat=(bone if i%2 else dentin) if is_chip else water
        if is_chip:
            pts=[(-.78,-.42,-.30),(.49,-.66,-.35),(.81,.22,-.28),(.12,.74,-.13),(-.54,.37,.48),(.25,-.12,.76)]
            ob=mesh('Angular milling debris',pts,[(0,3,2,1),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],chipmat,drill,smooth=False)
        else:
            ob=organic('Atomised saline',(.1,0,.8),(.1,.1,.15),water,parent=drill,seed=i)
        intervals=[]
        for start,end in windows:
            step=.37+rng.random()*.21
            t=start+(i%9)*step/9
            while t<end-.07:
                life=min(end-t,rng.uniform(.15,.31))
                spread=rng.uniform(2.0,6.0) if is_chip else rng.uniform(2.8,9.8)
                size=rng.uniform(.12,.25) if is_chip else rng.uniform(.035,.105)
                for f in [0,.45,1]:
                    d=spread*f
                    key(ob,'location',t+life*f,V((cos(a)*d,sin(a)*d,.57+(4.9 if is_chip else 6.6)*f-4.8*f*f))/1000,'LINEAR')
                    shrink=1-.54*f
                    key(ob,'scale',t+life*f,(size*shrink,size*.78*shrink,size*(.82 if is_chip else 1.8)*shrink),'LINEAR')
                intervals.append((t,t+life))
                t+=step
        visible(ob,intervals)

    aspirator=link('Assistant suction • fenestrated Frazier tip')
    tip=hollow_tip('Suction bevel and annular steel wall',aspirator,.82,.16,8.1)
    shaft=tube('Angled suction shaft',[(0,0,7.85),(0,0,9.5),(-.62,.08,11.3),(-3.4,.24,17),(-6.3,.55,24)],.82,steel,aspirator)
    hub=lathe('Aspirator ferrule',[(0,.86),(1,1.14),(7.8,1.20)],satin,aspirator)
    hub.location=V((-6.3,.55,24))/1000; hub.rotation_euler.y=-.40
    for part in (tip,shaft,hub):
        visible(part,[(13.65,18.9)])
    axis=(-.12,-.84,.53)
    trajectory=[(13.65,(39,-53,44)),(14.10,(35.2,-44.7,35.1)),(14.70,(35.1,-42.6,34.65)),
                (15.60,(35.7,-41.1,33.75)),(16.65,(35.35,-39.4,32.8)),(17.65,(35.2,-37.8,32.5)),
                (18.15,(35.7,-37.5,34.8)),(18.9,(42,-49,49))]
    tool_pose(aspirator,[(t,p,axis,0) for t,p in trajectory])
    # The pink rivulet terminates at the moving suction lumen.
    eff={}
    for t,p in trajectory[1:-1]:
        end=V(p)
        eff[t]=[end+V((-.70,2.20,.24)),end+V((-.47,1.56,-.05)),end+V((-.24,.91,-.23)),
                end+V((-.11,.38,-.13)),end+V((0,.06,0))]
    for off in (0,.15,-.13):
        path={t:[v+V((off*sin(pi*i/4),0,.04*cos(i+off))) for i,v in enumerate(vs)] for t,vs in eff.items()}
        shape_curve('Pink irrigation drawn into suction',path,(.27,1,.88,.75,.50),.15,dilute,[(14.15,18.07)])
    # Slurry is a low, interrupted film on wet cortex at contact, with foam beads.
    film=shade('Bone slurry • suspended mineral grains',[(.21,.092,.045),(.53,.31,.20),(.72,.53,.37)],2.4,.20,.14,.12,.60,pitting=True)
    for i in range(12):
        p=V((rng.uniform(-.8,.8),rng.uniform(-1.0,1.0),rng.uniform(.02,.30)))
        ob=organic('Slurry gathered around cutting head',p,(1,1,1),film if i%3 else dilute,parent=drill,seed=i)
        size=rng.uniform(.20,.42)
        ob.scale=(size,size*.8,size*.39)
        visible(ob,[(0,3),(13.7,17.85),(19.45,22.7)])
    for i in range(12):
        s=i/11
        x=29.77+.16*sin(9*s)
        y=-34.94+3.2*s
        z=25.85+.46*s+.10*sin(12*s)
        o=organic('Saline meniscus on opening bone', (x,y,z),(.20+.14*sin(pi*s),.38,.11),water,seed=i)
        visible(o,[(0,3)])


def fx_fracture():
    # Attach the fracture trace to the actual surface, around the incomplete bur
    # kerf. The two pieces pause during propagation and separate under the blade.
    crown=O['Crown']; root=O['Root']; elevator=O['Straight elevator']
    S.frame_set(frame(23.5))
    obj=crown.evaluated_get(bpy.context.evaluated_depsgraph_get())
    pts=[]
    for i in range(22):
        z=35.92-i*.345
        # Intersect the buccal surface at progressively more mesial offsets.
        y=-35.77-.30*i/21-.19*abs(sin(i*1.25))-.07*sin(i*4.8)
        start=obj.matrix_world.inverted() @ world((43,y,z))
        hit,co,normal,_=obj.ray_cast(start,V((-1,0,0)))
        if hit:
            pts.append(co*1000+normal*.026)
    if len(pts)<4:
        raise RuntimeError('Fracture trace failed to intersect crown')
    crack=tube('Fracture trace • buccal extent of the groove',pts,.094,liner,crown,
               radii=[.16+.85*sin(pi*(i+.05)/(len(pts)-.90))**.55 for i in range(len(pts))])
    visible(crack,[(23.57,26.60)])
    for t,amount in [(23.57,0),(23.77,.14),(23.91,.40),(24.07,.79),(24.28,1)]:
        key(crack.data,'bevel_factor_end',t,amount,'LINEAR')
    # Slow the first millimetre of crown separation without retiming narration.
    home=world((30,-39.4,31.8))
    for t,delta,rot in [(23.76,(0,0,0),(0,0,0)),(23.86,(.15,-.09,.08),(-.2,.3,-.6)),
                       (24.05,(.52,-.29,.32),(-1.1,2,-2.7)),(24.37,(1.36,-.67,.91),(-4.5,6,-7.5))]:
        key(crown,'location',t,home+V(delta)/1000)
        key(crown,'rotation_euler',t,tuple(map(math.radians,rot)))
    S.frame_set(frame(23.72))
    for i in range(11):
        start=V((33.7+rng.uniform(-.2,.2),-35.79+rng.uniform(-.11,.11),31.75+rng.uniform(-1.15,1.3)))
        end=start+V((rng.uniform(.7,2.9),rng.uniform(-2.2,2.4),rng.uniform(.8,2.0)))
        t=23.82+i*.029; size=rng.uniform(.11,.26)
        pts=[(-.7,-.3,0),(.55,-.47,-.22),(.7,.2,.1),(-.19,.68,-.29),(.13,.07,.78)]
        ob=mesh('Dentin splinter at fracture',pts,[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],dentin if i%3 else enamel,smooth=False)
        ob.scale=(size,size*.6,size*.75); visible(ob,[(t,t+.52)])
        for f in (0,.42,1):
            key(ob,'location',t+.54*f,world(start.lerp(end,f)+V((0,0,.76*sin(pi*f)-.81*f*f))),'LINEAR')
            key(ob,'rotation_euler',t+.54*f,(f*.8,f*(1+i*.2),f*.6),'LINEAR')

    # Preserve an actual purchase point on each piece while it rotates. The
    # lateral blade neck bears against a small irregularity of the bony rim.
    paths=[]
    for t,p,shaft,r in [(23.1,(36,-32,47),(.12,.28,.94),-18),(23.65,(33.7,-35.55,32.55),(.28,.46,.83),-26),
        (23.80,(33.62,-35.55,32.4),(.31,.37,.87),-21),(24.03,(33.58,-35.53,32.41),(.42,.14,.87),17),
        (24.34,(33.71,-35.56,32.55),(.47,.04,.86),39),(24.85,(33.1,-36.46,32.8),(.46,-.07,.88),40)]:
        paths.append((t,V(p),shaft,r))
    for name,local,states in [
        ('Crown',(2.18,2.61,-1.50),[(25.09,32),(25.33,47),(25.63,53),(26.09,60),(26.50,64),(26.89,69)]),
        ('Superior root segment',(2.23,-.54,.45),[(28.37,-21),(28.55,-14),(28.76,14),(29.04,27),(29.4,43),(29.9,49)]),
        ('Inferior root segment',(2.03,-.29,-1.40),[(30.38,-20),(30.57,-16),(30.79,5),(31.04,28),(31.31,44),(31.80,56),(32.24,61)])]:
        piece=O[name]
        for t,roll in states:
            S.frame_set(frame(t))
            co=piece.matrix_world @ (V(local)/1000)
            point=(co-base.ZERO)*1000
            # Shaft arcs toward the viewing-side bony lip under load.
            shaft=(.70, -.22+roll*.006, .71)
            paths.append((t,point,shaft,roll))
    paths += [(27.10,(50,-41,58),(.47,.42,.81),77),(28.0,(37,-34,45),(.48,.12,.87),-4),
              (30.14,(40,-34,46),(.46,.25,.85),27),(32.95,(50,-28,57),(.44,.29,.85),68)]
    elevator.animation_data_clear()
    tool_pose(elevator,sorted(paths,key=lambda row:row[0]))
    for p,sc in [((34.91,-37.42,32.98),(.71,1.20,.50)),((33.64,-31.92,32.38),(.75,1.05,.53))]:
        ledge=organic('Rough buccal bone at elevator fulcrum',p,sc,bone)
        visible(ledge,[(18.71,33.0)])


def root_films():
    for name,local,anchor,t0,t1 in [
        ('Crown',(1.0,1.0,-3.0),(31.15,-38.35,28.2),25.43,26.19),
        ('Superior root segment',(1.5,2.9,-.25),(30.5,-29.30,28.8),28.55,29.52),
        ('Inferior root segment',(1.3,2.8,-1.6),(30.25,-29.6,27.7),30.65,31.57)]:
        piece=O[name]
        for i in range(2):
            a=V(anchor)+V((i*.25,-i*.50,0)); paths={}
            for f in (0,.25,.55,.78,1):
                t=t0+(t1-t0)*f; S.frame_set(frame(t))
                e=((piece.matrix_world @ (V(local)/1000))-base.ZERO)*1000+V((.15*i,-.45*i,0))
                paths[t]=[a,a.lerp(e,.27)+V((-.14,0,-.36*f)),a.lerp(e,.69)+V((.10,0,-.20*f)),e]
            strand=shape_curve('Blood film stretching from periodontal attachment',paths,(1.26,.71,.60,1.08),.15-i*.045,blood,[(t0,t1)])
            for t,r in ((t0,.00015-i*.00004),(t1-.1,.000065-i*.000015),(t1,.000025)):
                key(strand.data,'bevel_depth',t,r)
        for i in range(3):
            rngpos=V(local)+V((rng.uniform(-.40,.30),rng.uniform(-.4,.45),rng.uniform(-.23,.18)))
            blood_drop=organic('Blood adhering to delivered segment',rngpos,(.24,.23,.31),blood,piece,seed=i)
            visible(blood_drop,[(t0-.15,t1+.3)])
        S.frame_set(frame(t1))
        e=((piece.matrix_world @ (V(local)/1000))-base.ZERO)*1000
        dr=organic('Capillary drop returning to socket',e,(.19,.18,.33),blood)
        visible(dr,[(t1,t1+.32)])
        for f in (0,.45,1):
            key(dr,'location',t1+f*.32,world(e+V((0,-.14*f,-5.2*f*f))),'LINEAR')


def change_aim(rig, rows):
    if rig.rotation_mode!='QUATERNION': rig.rotation_mode='QUATERNION'
    for t,axis,roll in rows:
        q=V((0,0,1)).rotation_difference(V(axis).normalized()) @ Quaternion((0,0,1),math.radians(roll))
        key(rig,'rotation_quaternion',t,q)


def instruments_in_profile():
    drill=O['Surgical handpiece']
    # Update every original rotation key so interpolated keys cannot steer the
    # tool back across the camera while the tip stays seated.
    action=drill.animation_data.action
    fc=next(fc for fc in action.layers[0].strips[0].channelbag(drill.animation_data.action_slot).fcurves if fc.data_path=='rotation_quaternion')
    times=[(round(p.co.x)-1)/20 for p in fc.keyframe_points]
    change_aim(drill,[(t,(.19,.84,.52) if t<3 else (.32,-.72,.65),-58 if t<3 else 166+5*sin(t*.75)) for t in times])
    # Keep the point of purchase visible while the hand instruments enter from
    # the anterior side. For needle driving, sample the pivot's actual motion.
    for name,base_roll,axis in [('Periosteal elevator',3,(-.13,-.80,.59)),
                                ('Straight elevator',0,(.21,-.71,.67))]:
        rig=O[name]; action=rig.animation_data.action
        fc=next(fc for fc in action.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves if fc.data_path=='rotation_quaternion')
        times=[(round(p.co.x)-1)/20 for p in fc.keyframe_points]
        rows=[]
        for t in times:
            roll=base_roll+18*sin(t*2) if name.startswith('Periosteal') else (-29+75*min(1,max(0,(t-23.73)/.56)) if t<25 else -22+50*sin((t-25)*2.1))
            rows.append((t,axis,roll))
        change_aim(rig,rows)
    needle=O['Suture needle pivot']; holder=O['Needle holder']
    curve=O['3/8-circle stainless suture needle']
    attach=curve.data.splines[0].bezier_points[9].co.copy()
    holder.animation_data_clear()
    motion=[]
    for f in range(frame(37.82),frame(39.37)+1,2):
        S.frame_set(f)
        t=(f-1)/20
        p=(needle.matrix_world @ attach -base.ZERO)*1000
        motion.append((t,p,(-.16,-.84,.53),-18))
    tool_pose(holder,motion)
    # A progressively closing strip covers the uncut seam ahead of the blade.
    ys=[-49+i*.25 for i in range(109)]
    pts=[]
    nx=8
    for y in ys:
        p=margin(min(1,max(0,(y+44)/17)));p.y=y
        for i in range(nx+1):
            u=(i/nx-.5)*2
            pts.append(p+V((u*.74,0,.09+.03*cos(u*pi/2)-.06*abs(u))))
    faces=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(len(ys)-1) for i in range(nx)]
    bridge=mesh('Continuous epithelium ahead of scalpel',pts,faces,gum)
    visible(bridge,[(3,9.90)])
    for k,cy in enumerate(range(-49,-20,2)):
        t=7.35+max(0,(cy+43)*.143)
        deform(bridge,'Incision releases strip '+str(k),[p+V((0,0,-1.6*exp(-((p.y-cy)/1.65)**4))) for p in pts],
               [(3,0),(t,0),(t+.16,1),(10,1)])
    # Oblique puncture, one pinpoint bead, no pre-incision line at the block site.
    # Keep the needle tip above fluid for its first frames of withdrawal.
    bead=O['Puncture bead after withdrawal']
    bead.location=world((30.65,-25.5,39.29))


def pooling():
    # Move one continuous meniscus through the bowl. Saline concentration also
    # travels across it, leaving a darker far margin until the wash reaches it.
    liquid=blood.copy(); liquid.name='Socket liquid • spatially advancing saline dilution'
    nt=liquid.node_tree; bs=nt.nodes.get('Principled BSDF')
    original=bs.inputs['Base Color'].links[0].from_socket
    tex=nt.nodes.new('ShaderNodeTexCoord')
    sep=node(nt,'ShaderNodeSeparateXYZ',Vector=tex.outputs['Generated'])
    turbulence=node(nt,'ShaderNodeTexNoise',Vector=tex.outputs['Generated'],Scale=6.0,Detail=3.0,Distortion=1.4)
    mul=nt.nodes.new('ShaderNodeMath'); mul.operation='MULTIPLY'
    nt.links.new(turbulence.outputs['Fac'],mul.inputs[0]); mul.inputs[1].default_value=.38
    advance=nt.nodes.new('ShaderNodeMath'); advance.operation='ADD'
    nt.links.new(sep.outputs['Y'],advance.inputs[0]);nt.links.new(mul.outputs[0],advance.inputs[1])
    bias=nt.nodes.new('ShaderNodeMath'); bias.operation='SUBTRACT'
    nt.links.new(advance.outputs[0],bias.inputs[1])
    for t,w in [(25,-.1),(33.8,-.1),(34.25,.42),(34.85,.93),(35.4,1.60),(35.83,1.50),(36.3,.64),(36.85,-.12),(44,-.12)]:
        bias.inputs[0].default_value=w; bias.inputs[0].keyframe_insert(data_path='default_value',frame=frame(t))
    mask=ramp(nt,bias.outputs[0],[(.0,(0,0,0)),(.30,(1,1,1))])
    mix=nt.nodes.new('ShaderNodeMixRGB')
    nt.links.new(mask,mix.inputs[0]);nt.links.new(original,mix.inputs[1])
    mix.inputs[2].default_value=(.47,.125,.116,1)
    nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
    n=106; levels=17; pts=[]; faces=[]
    for j in range(levels):
        r=.004+.996*j/(levels-1)
        for i in range(n):
            a=2*pi*i/n
            k=1+.026*sin(5*a+.3)+.016*cos(9*a)
            z=.06*sin(3*a+r*5.1)*r+.06*cos(5*a-7*r)*r+.32*r**7
            pts.append((4.75*r*k*cos(a),7.58*r*k*sin(a),z))
    for j in range(levels-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;faces.append((a,a+n,b+n,b))
    pool=mesh('Continuous socket meniscus • refill and saline wash',pts,faces,liquid)
    # Lower side wall and the capillary margin close the fluid against the socket.
    sd=pool.modifiers.new('Liquid depth','SOLIDIFY');sd.thickness=.0018;sd.offset=-1
    visible(pool,[(25.35,44.05)])
    for t,z,sz in [(25.35,26.66,.27),(26.4,28.45,.65),(29.26,28.66,.74),(32.7,29.25,.82),
                  (33.84,31.15,1.02),(34.48,31.43,1.02),(35.24,30.36,.93),(35.85,29.68,.88),
                  (36.71,31.42,1.04),(40.74,32.22,1.04),(42.55,34.20,.95)]:
        key(pool,'location',t,world((30.05,-35.65,z)))
        key(pool,'scale',t,(sz,sz,1))
    for k in range(3):
        more=[]
        for x,y,z in pts:
            d=math.hypot((x-1.1)*1.1,y+2-k*1.5)
            more.append((x,y,z+.20*sin(3.2*d-k)*exp(-d/3.1)))
        deform(pool,'Saline impact ripple '+str(k),more,[(33.72,0),(34+k*.35,0),(34.35+k*.35,1),(35.41+k*.32,0)])
    # Aim the visible rinse into the cavity; the source follows the cannula tip.
    noz=O['Blunt irrigation cannula'];noz.animation_data_clear()
    axis=V((.18,.47,.86)).normalized()
    states=[(33,(37,-26,51)),(33.83,(33.0,-35.6,39.0)),(34.35,(32.0,-36.9,37.9)),
            (35.04,(31.8,-35.3,37.3)),(35.78,(32.3,-32.1,37.6)),(36.20,(33.2,-30.7,40.0)),(36.72,(38,-26,51))]
    tool_pose(noz,[(t,p,axis,0) for t,p in states])
    for o in S.objects:
        if o.name.startswith('Saline entering the socket'): o.data.bevel_depth*=1.6
    # A coherent, viscous clot develops within the opening left posterior to
    # the stitch. Its margins recede into the bed as the top consolidates.
    clotpts=[]
    for j in range(19):
        la=-pi/2+pi*(j+.01)/18.02
        for i in range(72):
            a=i*2*pi/72; x=cos(la)*cos(a); y=cos(la)*sin(a); z=sin(la)
            nn=noise.noise_vector(V((x*4.7+.3,y*6.1,z*4.9)))[0]
            r=1+.093*nn+.048*sin(a*5+.7)*cos(la)**2
            clotpts.append((2.97*x*r,5.4*y*r,1.25*z*r+.20*nn))
    clotfaces=[(j*72+i,j*72+(i+1)%72,(j+1)*72+(i+1)%72,(j+1)*72+i) for j in range(18) for i in range(72)]
    clot=mesh('Consolidating clot below posterior suture gap',clotpts,clotfaces,coag)
    visible(clot,[(40.72,44.05)])
    for t,z,sz in [(40.72,32.62,.64),(41.50,34.70,.83),(42.48,36.26,1),(43.95,36.76,1.01)]:
        key(clot,'location',t,world((30.2,-32.6,z)));key(clot,'scale',t,(sz,sz,sz))
    fibrin=shade('Fine fibrin in clot',[(.14,.022,.022),(.22,.049,.038),(.34,.096,.062)],2,.29,.12,.18,.4)
    for i in range(14):
        x=rng.uniform(-1.7,1.7); y=rng.uniform(-1.8,3.6)
        pts=[]
        for j in range(6):
            xx=x+.13*j; yy=y+.13*j+.09*sin(1.25*j+i)
            zz=1.25*math.sqrt(max(.01,1-(xx/2.97)**2-(yy/5.4)**2))+.04*sin(i+j)
            pts.append((xx,yy,zz))
        f=tube('Fine strands at clot meniscus',pts,.027,fibrin,clot,radii=(.15,.75,1,.86,.54,.08))
        visible(f,[(41.65+i*.034,44.05)])


def build_effects():
    procedural_spray()
    fx_fracture()
    root_films()
    instruments_in_profile()
    pooling()
