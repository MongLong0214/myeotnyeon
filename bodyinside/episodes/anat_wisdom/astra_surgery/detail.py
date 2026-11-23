"""Close-range anatomical surface and fluid refinements."""


def bed_and_mucosa():
    bed=O['Alveolar bed, cortical rim and contiguous vestibule']
    m=gum.copy();m.name='Continuous transition from socket wall through cortex to periosteum'
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    attr=bed.data.attributes.new('Radial tissue layer','FLOAT','POINT')
    rr=[.11,.30,.54,.73,.87,.97,1,1.07,1.17,1.30,1.53,1.82,2.35,3.2,5.5]
    for i,v in enumerate(bed.data.vertices):
        a=(i%128)*2*pi/128; r=rr[i//128]
        attr.data[i].value=min(1,r/1.45+.028*cos(3*a)+.012*sin(7*a))
    at=nt.nodes.new('ShaderNodeAttribute');at.attribute_name='Radial tissue layer'
    uv=nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    grit=node(nt,'ShaderNodeTexNoise',Vector=uv,Scale=1920,Detail=2.4,Roughness=.63)
    mult=nt.nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';nt.links.new(grit.outputs[0],mult.inputs[0]);mult.inputs[1].default_value=.115
    layers=nt.nodes.new('ShaderNodeMath');layers.operation='ADD';nt.links.new(mult.outputs[0],layers.inputs[0]);nt.links.new(at.outputs['Fac'],layers.inputs[1])
    r=ramp(nt,layers.outputs[0],[(.0,(.079,.008,.013)),(.49,(.19,.026,.029)),(.62,(.31,.082,.050)),
        (.68,(.48,.27,.15)),(.74,(.70,.51,.32)),(.79,(.62,.39,.23)),(.84,(.285,.071,.050)),
        (.90,(.31,.064,.074)),(1,(.40,.105,.119))])
    tissue=bs.inputs['Base Color'].links[0].from_socket
    pig=nt.nodes.new('ShaderNodeMixRGB');pig.blend_type='MULTIPLY';pig.inputs[0].default_value=.45
    nt.links.new(r,pig.inputs[1]);nt.links.new(tissue,pig.inputs[2]);nt.links.new(pig.outputs[0],bs.inputs['Base Color'])
    micro=node(nt,'ShaderNodeBump',Strength=.23,Distance=.00012,Height=grit.outputs['Fac'],Normal=bs.inputs['Normal'].links[0].from_socket)
    nt.links.new(micro.outputs[0],bs.inputs['Normal'])
    remat(bed,m)
    # Rolled edges and constrained, asymmetric rugae continue through every
    # shape key so the detail stays embedded in the tissue through retraction.
    for o in (flap,bank):
        keys=o.data.shape_keys.key_blocks
        for i,v in enumerate(o.data.vertices):
            p=keys[0].data[i].co*1000; u=(i//89)/32; s=(i%89)/88
            ridge=.19*sin(2.12*p.x+.37*p.y+.62*sin(.63*p.y))*exp(-((u-.16)/.23)**2)
            ridge+=.085*sin(.92*p.y+.36*p.x+.40*cos(p.x))+.14*noise.noise(V((p.x*.54,p.y*.54,.51)))
            ridge*=min(1,u*30)+.12
            for sk in keys:
                sk.data[i].co.z+=ridge/1000
    bg=shade('Deep posterior mucosal fold',[(.038,.005,.011),(.11,.021,.033),(.21,.062,.068)],.23,.41,.26,.28,.20,veins=.25)
    replace_slots(O['Posterior oral lining'],[bg])
    # Anatomical retromolar fold encloses the distal end of the incision.
    # It slopes down into the two wound lips without an exposed square mesh end.
    for pos,scale in [((28.9,-18.9,36.45),(10.3,5.6,4.0)),((22.6,-23.1,36.0),(6.5,6.4,3.25))]:
        pad=organic('Retromolar mucosal fold',pos,scale,gum,seed=7)
        visible(pad,[(3,44.05)])
    # Keep the injection field anatomically continuous against the closed lips.
    bridge=O['Continuous epithelium ahead of scalpel']
    for i,v in enumerate(bridge.data.vertices):
        for sk in bridge.data.shape_keys.key_blocks:
            u=i%9/8
            sk.data[i].co.z-=.00014*abs(2*u-1)**2


def finer_fluid_surface():
    pool=O['Continuous socket meniscus • refill and saline wash']
    bed=O['Alveolar bed, cortical rim and contiguous vestibule']
    # The meniscus follows the true cross-section of the cavity at each height.
    # Sample the polygonal wall along its own radial spokes.
    contours=[]
    heights=[26.66,28.45,28.66,29.25,30.42,30.52,29.86,29.38,30.50,30.62,30.72]
    times=[25.35,26.4,29.26,32.7,33.84,34.48,35.24,35.85,36.71,40.74,42.55]
    for ht in heights:
        ring=[]
        for i in range(128):
            column=[bed.data.vertices[j*128+i].co*1000 for j in range(11)]
            for j in range(1,len(column)):
                left,right=column[j-1:j+1]
                if right.z>=ht and right.z>left.z:
                    break
            t=max(0,min(1,(ht-left.z)/max(.015,right.z-left.z)))
            rimpoint=left.lerp(right,t)
            # Slightly submerge the liquid perimeter in the porous wall.
            ring.append(((rimpoint.x-30.05)*1.045,(rimpoint.y+35.65)*1.045))
        contours.append(ring)
    # Initial form is replaced with a sequence of mutually exclusive fill shapes.
    pool.shape_key_clear();pool.animation_data_clear()
    pool.location=world((30.05,-35.65,0))
    def surface(level):
        height=heights[level];edge=contours[level];pts=[]
        for j in range(17):
            r=.004+.996*j/16
            for i in range(106):
                phase=i*128/106;ii=int(phase);f=phase-ii
                xx=edge[ii][0]*(1-f)+edge[(ii+1)%128][0]*f
                yy=edge[ii][1]*(1-f)+edge[(ii+1)%128][1]*f
                a=2*pi*i/106
                z=height+.037*sin(3*a+r*5)*r+.022*cos(8*a-r*9)*r+.16*r**7
                pts.append((xx*r,yy*r,z))
        return pts
    for v,p in zip(pool.data.vertices,surface(0)):v.co=V(p)/1000
    pool.shape_key_add(name='Initial blood film')
    for i in range(1,len(times)):
        keys=[(times[i-1],0),(times[i],1)]
        if i+1<len(times):keys.append((times[i+1],0))
        if i>1: keys.insert(0,(times[0],0))
        deform(pool,'Meniscus at '+str(times[i])+'s',surface(i),keys)
    visible(pool,[(25.35,44.05)])
    m=pool.data.materials[0];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    mix=bs.inputs['Base Color'].links[0].from_node
    uv=nt.nodes.new('ShaderNodeTexCoord').outputs['Generated']
    swirl=node(nt,'ShaderNodeTexNoise',Vector=uv,Scale=3.65,Detail=4.0,Roughness=.56,Distortion=1.7)
    near=ramp(nt,swirl.outputs['Fac'],[(.19,(.098,.009,.017)),(.49,(.40,.072,.080)),(.76,(.65,.22,.19))])
    nt.links.new(near,mix.inputs[2])
    gloss=nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(mix.inputs[0].links[0].from_socket,gloss.inputs[0])
    gloss.inputs['To Min'].default_value=.08;gloss.inputs['To Max'].default_value=.59
    nt.links.new(gloss.outputs[0],bs.inputs['Transmission Weight'])
    for k,t in enumerate((34.15,34.70,35.18,35.60)):
        pts=surface(4 if k<2 else 6)
        for i,p in enumerate(pts):
            x,y,z=p;d=math.hypot(x-1.0,y+2-k)
            pts[i]=(x,y,heights[0]+.13*sin(3.4*d)*exp(-d/3.1))
        # Keep ripple offsets relative to the initial surface.
        basis=pool.data.shape_keys.key_blocks[0]
        offsets=[(v.co.x*1000,v.co.y*1000,v.co.z*1000+pts[i][2]-heights[0]) for i,v in enumerate(basis.data)]
        deform(pool,'Wave from irrigation '+str(k),offsets,[(33.7,0),(t,0),(t+.24,1),(t+.66,0)])
    for i in range(10):
        t=34.16+i*.125; x=rng.uniform(-2,2); y=rng.uniform(-3.8,3.1); radius=rng.uniform(.06,.18)
        bead=organic('Small air bubble in irrigant',(30.05+x,-35.65+y,30.4),(radius,radius,radius*.63),water)
        visible(bead,[(t,t+.55)])
        for f in (0,.56,1):
            z=30.52-.7*max(0,min(1,(t+.52*f-34.5)/.8))
            key(bead,'location',t+.52*f,world((30.05+x+.35*f,-35.65+y+.42*f,z)))


def steel_and_canal():
    # The two small longitudinal vessels remain outside the neural sheath and
    # follow exactly the same curved canal as the inherited nerve centreline.
    nerve=O['Nerve2']; points=nerve.data.splines[0].bezier_points
    centre=[(p.co-base.ZERO)*1000 for p in points]
    shear=shade('Epineurial longitudinal fibre',[(.26,.15,.053),(.55,.37,.153),(.71,.53,.25)],1,.29,.06,.19,.36)
    vess=shade('Vasa nervorum',[(.07,.012,.015),(.23,.037,.034),(.32,.077,.057)],1,.3,.05,.18,.36)
    for j in range(5):
        pts=[]
        for i in range(len(centre)-1):
            if centre[i].y>-20 or centre[i+1].y<-49:continue
            p0,p1=points[i],points[i+1]
            from mathutils.geometry import interpolate_bezier
            for k,v in enumerate(interpolate_bezier(p0.co,p0.handle_right,p1.handle_left,p1.co,9)[:-1]):
                p=(v-base.ZERO)*1000
                a=-1.08+.46*j+.16*sin(p.y*.41+j)
                pts.append(p+V((.685*cos(a),-.26*sin(a),.62*sin(a))))
        o=tube('Longitudinal fibres on canal contents',pts,.045 if j!=1 else .065,vess if j==1 else shear)
    # Irrigation port running separately from the shank; a tapering liquid sheet
    # and a beaded edge make the free jet visible against the darker cavity.
    dr=O['Surgical handpiece']
    feed=tube('External saline spray port',[(.73,.6,7.4),(1.6,.88,6.5),(2.25,.86,5.72),(2.15,.76,4.75)],.242,satin,dr)
    visible(feed,[(0,3),(13,23.1),(27,28.1)])
    for k in (-1,0,1):
        pts=[(2.15,.76,4.78),(1.94+k*.06,.66,3.97),(1.48+k*.09,.53,3.09),
             (1.03+k*.09,.29,2.07),(.65+k*.07,.18,1.41),(.40+k*.12,.08,.58)]
        jet=tube('Free irrigant jet from offset port',pts,.122 if not k else .051,water,dr,radii=(.89,1,.88,.82,.64,.32))
        visible(jet,[(0,3),(13.60,17.95),(19.29,22.78),(27.22,27.88)])
    # A slightly broader cuff of blanching around the penetration helps convey
    # the bevel breaking the surface. The dimple itself is in the deforming gum.
    # Keep the elevator blade under the actual flap, through both shape keys.
    rig=O['Periosteal elevator']
    for f in range(frame(10.39),frame(12.64)+1,3):
        S.frame_set(f)
        eval_flap=flap.evaluated_get(bpy.context.evaluated_depsgraph_get())
        # Subdivision changes evaluated topology. Interpolate the unmodified
        # animated control cage at the anterior third of the free lip instead.
        idx=1*89+35
        base_point=flap.data.shape_keys.key_blocks[0].data[idx].co.copy()
        pp=base_point.copy()
        for sk in list(flap.data.shape_keys.key_blocks)[1:]:
            pp+=(sk.data[idx].co-base_point)*sk.value
        key(rig,'location',(f-1)/20,base.ZERO+pp+V((0,.02,-.34))/1000)


def suture_drive():
    needle=O['Suture needle pivot']; needle.animation_data_clear()
    ctr=margin(.515)+V((.10,0,1.15))
    for t,angle,z,x in [(37.82,178,3.1,-.7),(38.00,159,.50,-.15),(38.21,146,0,0),
                        (38.44,113,0,0),(38.66,78,0,0),(38.88,42,0,0),
                        (39.02,13,.22,.1),(39.17,-9,1.40,.75),(39.36,-33,5.5,2.25)]:
        key(needle,'location',t,world(ctr+V((x,0,z))))
        key(needle,'rotation_euler',t,(0,math.radians(angle),0))
    # Follow the tapering swage, whichever way the curved needle turns.
    curve=O['3/8-circle stainless suture needle']
    swage=curve.data.splines[0].bezier_points[0].co
    grip=curve.data.splines[0].bezier_points[9].co
    holder=O['Needle holder'];holder.animation_data_clear();motion=[]; paths={}
    for f in range(frame(37.82),frame(39.36)+1):
        S.frame_set(f);t=(f-1)/20
        m=needle.matrix_world
        p=(m@grip-base.ZERO)*1000;e=(m@swage-base.ZERO)*1000
        motion.append((t,p,(-.16,-.84,.53),-20))
        d=max(0,min(1,(t-38.18)/1.12))
        paths[t]=[e,e+V((-.38,-.28,.17)),e+V((-.83,-1.3,.35)),
                  e+V((-1.3,-2.6,.21+d*.51)),e+V((-1.75,-4.7,.66+d*1.1)),e+V((-2.61,-8.73,2.20+d*1.38))]
    tool_pose(holder,motion)
    shape_curve('Braided thread trailing the curved needle',paths,(.68,.88,.98,1,.98,.85),.078,silk,[(37.82,39.36)])
    # Reposition the tenting over the two actual penetration sites.
    for o in (flap,bank):
        ref=o.data.shape_keys.key_blocks[0]
        for i,(x,t) in enumerate(((ctr.x-2.43,38.18),(ctr.x+2.43,38.92))):
            sk=o.data.shape_keys.key_blocks['Suture tent '+str(i+1)]
            for a,b in zip(ref.data,sk.data):
                p=a.co*1000
                w=exp(-((p.x-x)/1.30)**2-((p.y-ctr.y)/1.15)**2)
                b.co=a.co+V(((.20 if not i else -.20),0,.76))*w/1000
            for tm,value in [(37.82,0),(t-.17,0),(t,1),(t+.26,0),(39.5,0)]:
                sk.value=value;sk.keyframe_insert(data_path='value',frame=frame(tm))


def polish():
    bed_and_mucosa()
    finer_fluid_surface()
    steel_and_canal()
    suture_drive()
