"""Draft 3 close-up materials, deforming tissue and operating microscope."""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector, Quaternion, noise

HERE=Path(__file__).resolve().parent
S=bpy.context.scene
O=bpy.data.objects
M=bpy.data.materials
V=Vector
ZERO=V((0,0,1.5))
rng=random.Random(302)
flap=O['Attached buccal flap • deforming wound lip']
bank=O['Lingual gingiva • wound margin']
bed=O['Alveolar bed, cortical rim and contiguous vestibule']


def rgb(r,g,b):
    return r,g,b,1


class Graph:
    def __init__(self,m):
        self.nt=m.node_tree
        self.bs=self.nt.nodes.get('Principled BSDF')
        self.coords=self.make('ShaderNodeTexCoord')

    def plug(self,s,v):
        if isinstance(v,bpy.types.NodeSocket):
            self.nt.links.new(v,s)
        else:
            if s.is_linked:self.nt.links.remove(s.links[0])
            if isinstance(v,(float,int)) and s.type=='RGBA':v=(v,v,v,1)
            s.default_value=v

    def make(self,kind,**kw):
        n=self.nt.nodes.new(kind)
        for k,v in kw.items():self.plug(n.inputs[k],v)
        return n

    def current(self,k):
        s=self.bs.inputs[k]
        return s.links[0].from_socket if s.is_linked else s.default_value

    def set(self,**kw):
        for k,v in kw.items():self.plug(self.bs.inputs[k],v)

    def math(self,op,a,b):
        n=self.make('ShaderNodeMath');n.operation=op
        self.plug(n.inputs[0],a);self.plug(n.inputs[1],b)
        return n.outputs[0]

    def vec(self,op,a,b):
        n=self.make('ShaderNodeVectorMath');n.operation=op
        self.plug(n.inputs[0],a);self.plug(n.inputs[1],b)
        return n.outputs['Vector']

    def noise(self,uv,scale,detail=2,dist=0):
        return self.make('ShaderNodeTexNoise',Vector=uv,Scale=scale,Detail=detail,Distortion=dist).outputs['Fac']

    def ramp(self,src,pts):
        n=self.make('ShaderNodeValToRGB',Fac=src);r=n.color_ramp
        r.interpolation='EASE'
        for i,(p,c) in enumerate(pts):
            e=r.elements[i] if i<2 else r.elements.new(p)
            e.position=p;e.color=(*((c,c,c) if isinstance(c,(float,int)) else c),1)
        return n.outputs[0]

    def mix(self,fac,a,b,blend='MIX'):
        n=self.make('ShaderNodeMixRGB',Fac=fac,Color1=a,Color2=b)
        n.blend_type=blend
        return n.outputs[0]

    def bump(self,height,distance,strength):
        prior=self.current('Normal')
        n=self.make('ShaderNodeBump',Height=height,Distance=distance,Strength=strength)
        if isinstance(prior,bpy.types.NodeSocket):self.plug(n.inputs['Normal'],prior)
        self.set(Normal=n.outputs[0])
        return n.outputs[0]


def mm(fr):
    return round(fr*20)+1


def windows(o,spans):
    for frame,hidden in [(1,True)]+[(f,h) for start,end in spans for f,h in [(mm(start),False),(mm(end),True)]]:
        o.hide_render=hidden;o.keyframe_insert(data_path='hide_render',frame=frame)


def tissue():
    im=bpy.data.images.load(str(HERE/'mucosal_microstructure.png'),check_existing=True)
    im.colorspace_settings.name='Non-Color'
    raw=M['Reflected periosteum • fibrous wet surface']
    skin=M['Attached mucosa • stipple and subepithelial vessels']
    subjects=[flap,bank,bed,O['Continuous epithelium ahead of scalpel'],O['Posterior oral lining']]
    subjects.extend(ob for ob in S.objects if ob.type=='MESH' and skin.name in ob.data.materials)
    for ob in dict.fromkeys(subjects):
        me=ob.data
        if ob.name.startswith('Retromolar mucosal fold'):
            ob.scale.z*=.83
            ob.location.z-=.00022
            for vert in me.vertices:
                local=vert.co*1000
                vert.co.z+=.000042*math.sin(5.8*local.y+1.65*local.x)*max(0,local.z)
        uv=me.uv_layers.get('Clinical field (rest)') or me.uv_layers.new(name='Clinical field (rest)')
        for lp in me.loops:
            p=(ob.matrix_world @ me.vertices[lp.vertex_index].co-ZERO)*1000
            uv.data[lp.index].uv=((p.x-14)/28+.10*p.z/28,(p.y+50)/28)
    materials=[flap.data.materials[0],bank.data.materials[0],raw, M['Attached mucosa • stipple and subepithelial vessels'],
               bed.data.materials[0],O['Posterior oral lining'].data.materials[0]]
    for mat in dict.fromkeys(materials):
        g=Graph(mat); rough=mat==raw; radial=mat==bed.data.materials[0]
        uv=g.make('ShaderNodeUVMap');uv.uv_map='Clinical field (rest)'
        a=g.make('ShaderNodeTexImage',Vector=uv.outputs[0]);a.image=im
        sep=g.make('ShaderNodeSeparateColor',Color=a.outputs[0])
        v,p,wet=list(sep.outputs)[:3]
        tint=rgb(.53,.31,.36) if not rough else rgb(.63,.43,.46)
        base=g.mix(.38,g.current('Base Color'),tint,'MULTIPLY')
        base=g.mix(g.math('MULTIPLY',v,1.25),base,rgb(.14,.015,.039))
        pigment=g.noise(g.coords.outputs['Object'],238,3,.61)
        heme=g.ramp(pigment,[(.21,(.70,.21,.26)),(.52,(.89,.61,.60)),(.79,(1,.89,.83))])
        base=g.mix(.43 if not radial else .22,base,heme,'MULTIPLY')
        mirror=g.ramp(wet,[(.26,.112),(.48,.163),(.60,.214),(.77,.31)])
        n=g.bump(p,.00017 if not rough else .00009,.43)
        g.set(**{'Base Color':base,'Coat Weight':g.ramp(wet,[(.22,.58),(.50,.45),(.79,.25)]),'Coat Roughness':mirror,
                 'Coat IOR':1.335,'Subsurface Weight':.37 if not radial else .22,
                 'Subsurface Scale':.00085,'Subsurface Radius':(1,.41,.23),
                 'Roughness':g.ramp(wet,[(.12,.21),(.60,.33),(.88,.45)])})
        # A thin film partially levels the epithelium's fine depressions.
        old=g.bs.inputs['Coat Normal']
        if old.is_linked:g.nt.links.remove(old.links[0])
        film=g.make('ShaderNodeBump',Height=g.noise(g.coords.outputs['Object'],1420,2.5,.53),Distance=.000084,Strength=.35,Normal=n)
        g.plug(old,film.outputs[0])
    for sign,ob in [(1,flap),(-1,bank)]:
        keys=ob.data.shape_keys.key_blocks
        for i,v in enumerate(keys[0].data):
            u=(i//89)/32
            if u>.21:continue
            p=v.co*1000; y=p.y
            # Disrupt the formerly straight scalpel margin without opening the uncut field.
            edge=(1-u/.21)**3
            dz=edge*(.105*math.sin(y*2.3+.7)+.080*math.sin(y*4.71)+.14*noise.noise(V((1.1,y*.94,.22))))
            dx=edge*(.081*math.sin(y*2.73)+.042*math.cos(y*4.5))
            for k in keys:k.data[i].co+=V((dx,sign*.015*math.sin(y*2),dz))*.001
        sub=ob.modifiers.get('Continuous rounded margins');sub.render_levels=2
    for ob in [bed,O['Posterior oral lining']]:
        mod=ob.modifiers.new('Continuous lining silhouette','SUBSURF');mod.levels=1;mod.render_levels=2


def cage(surface,f):
    keys=surface.data.shape_keys.key_blocks
    S.frame_set(f)
    coords=[p.co.copy() for p in keys[0].data]
    for k in list(keys)[1:]:
        if abs(k.value)>.0001:
            for i,v in enumerate(k.data):coords[i]+=(v.co-keys[0].data[i].co)*k.value
    return coords


def surface_point(c,u,j,sign):
    u=max(0,min(31.99,u));j=max(.01,min(87.99,j))
    i=int(u);k=int(j);jfrac=j-k;ufrac=u-i
    p=c[i*89+k].lerp(c[i*89+k+1],jfrac)
    nextp=c[(i+1)*89+k].lerp(c[(i+1)*89+k+1],jfrac)
    along=c[i*89+k+1]-c[i*89+k]
    normal=(nextp-p).cross(along).normalized()*sign
    return p.lerp(nextp,ufrac),normal


def fibers():
    mat=bpy.data.materials.new('Wet collagen strands under the reflected lip')
    mat.use_nodes=True;g=Graph(mat)
    g.set(**{'Base Color':rgb(.61,.31,.24),'Subsurface Weight':.38,'Subsurface Scale':.00034,
             'Roughness':.31,'Coat Weight':.55,'Coat Roughness':.13})
    times=[9.9,10.35,10.75,11.12,11.62,12.05,12.5,12.87,36.6,36.85,37.2,37.55,37.9]
    tracks=[]
    for i in range(146):
        u=rng.uniform(.02,4.9);j=rng.uniform(14,74)
        du=rng.uniform(.34,2.55);dj=rng.uniform(-3,4)
        radius=rng.uniform(.018,.049)*.001
        tracks.append((u,j,du,dj,radius,rng.uniform(0,6.28)))
    faces=[];poses=[]
    for t in times:
        coords=cage(flap,mm(t));verts=[]
        for i,(u,j,du,dj,r,phase) in enumerate(tracks):
            points=[];normals=[]
            for step in range(6):
                q=step/5
                p,n=surface_point(coords,u+du*q,j+dj*q+.24*math.sin(q*5+phase),1)
                points.append(p-n*(.000885+.000027*math.sin(q*math.pi)));normals.append(n)
            start=len(verts)
            for k,(p,n) in enumerate(zip(points,normals)):
                tangent=(points[min(k+1,5)]-points[max(0,k-1)]).normalized()
                side=tangent.cross(n).normalized()
                rr=r*(.13+.87*math.sin(math.pi*(k+.05)/5.1)**.68)
                for h in range(4):
                    angle=h*math.pi*.5;verts.append(p+(side*math.cos(angle)+n*math.sin(angle)*.70)*rr)
                    if t==times[0] and k<5:
                        x=start+k*4;faces.append((x+h,x+(h+1)%4,x+4+(h+1)%4,x+4+h))
        poses.append(verts)
    mesh=bpy.data.meshes.new('Periosteal fibers');mesh.from_pydata(poses[0],[],faces);mesh.materials.append(mat)
    ob=O.new('Collagen fibers on flap underside',mesh);S.collection.objects.link(ob);ob.location=ZERO
    for p in mesh.polygons:p.use_smooth=True
    ob.shape_key_add(name='Before reflection')
    for i,coords in enumerate(poses[1:],1):
        k=ob.shape_key_add(name=f'Flap at {times[i]:.2f}s')
        for v,p in zip(k.data,coords):v.co=p
        for t,val in [(0,0),(times[i-1],0),(times[i],1)]+([(times[i+1],0)] if i+1<len(times) else []):
            k.value=val;k.keyframe_insert(data_path='value',frame=mm(t))
    windows(ob,[(9.9,37.90)])


def bone_and_enamel():
    for mat in [M['Cut cortex • ivory trabeculae and pores'],M['Socket wall • vascular cancellous bed'],
                M['Milled cortex under a thin saline film'],bed.data.materials[0]]:
        g=Graph(mat)
        uv=g.vec('MULTIPLY',g.coords.outputs['Object'],(1000,1000,1000))
        broad=g.make('ShaderNodeTexNoise',Vector=uv,Scale=.71,Detail=2.7,Distortion=.64)
        warp=g.vec('ADD',uv,g.vec('MULTIPLY',broad.outputs['Color'],(.52,.64,.60)))
        cells=g.make('ShaderNodeTexVoronoi',Vector=warp,Scale=2.05)
        pores=g.ramp(cells.outputs['Distance'],[(.16,1),(.30,.70),(.44,0)])
        if mat==bed.data.materials[0]:
            at=g.make('ShaderNodeAttribute');at.attribute_name='Radial tissue layer'
            pores=g.math('MULTIPLY',pores,g.ramp(at.outputs['Fac'],[(.40,.4),(.65,1),(.86,0)]))
        root=g.current('Base Color')
        g.set(**{'Base Color':g.mix(g.math('MULTIPLY',pores,.48),root,rgb(.20,.088,.054))})
        g.bump(g.math('SUBTRACT',1,pores),.00024,.44)
        if mat!=bed.data.materials[0]:
            wav=g.make('ShaderNodeTexWave',Vector=warp,Scale=2.7,Distortion=2.3,Detail=2.0)
            wav.bands_direction='DIAGONAL'
            mask=g.ramp(broad.outputs['Fac'],[(.46,.0),(.61,.78)])
            g.bump(g.math('MULTIPLY',wav.outputs['Fac'],mask),.000042,.26)
    m=M['Hydrated enamel'];g=Graph(m)
    uv=g.vec('MULTIPLY',g.coords.outputs['Object'],(1000,1000,1000))
    base=g.current('Base Color');p=g.noise(uv,.45,3)
    c=g.make('ShaderNodeTexVoronoi',Vector=g.vec('MULTIPLY',uv,(1.25,.84,.19)),Scale=.83)
    c.feature='DISTANCE_TO_EDGE'
    hair=g.ramp(c.outputs['Distance'],[(.001,.77),(.009,.36),(.021,0)])
    patch=g.ramp(p,[(.44,0),(.68,.80)])
    lines=g.math('MULTIPLY',hair,patch)
    g.set(**{'Base Color':g.mix(lines,base,rgb(.31,.21,.120)),'Transmission Weight':.20,
             'IOR':1.62,'Coat Weight':.61,'Coat Roughness':.10,'Subsurface Scale':.00083,
             'Subsurface Weight':.32,'Subsurface Radius':(1,.82,.57)})
    g.bump(g.math('SUBTRACT',1,lines),.000025,.28)
    g=Graph(M['Dentin • fresh fracture'])
    uv=g.vec('MULTIPLY',g.coords.outputs['Object'],(3600,2600,1050))
    fibers=g.noise(uv,2.3,2,.21)
    g.set(**{'Base Color':g.mix(.30,g.current('Base Color'),rgb(.81,.56,.29),'MULTIPLY'),
             'Subsurface Scale':.00063,'Transmission Weight':.055})
    g.bump(fibers,.000093,.43)


def fracture_and_bur_tracks():
    import numpy as np
    crown=O['Crown'];mesh=crown.data
    faces=[face for face in mesh.polygons if mesh.materials[face.material_index]==M['Dentin • fresh fracture']]
    if faces:
        # Rasterize the measured perimeter of the fracture. The ivory outer
        # enamel narrows into the body of the exposed yellow dentin.
        edges={}
        for face in faces:
            for edge in face.edge_keys:edges[edge]=edges.get(edge,0)+1
        boundary=[pair for pair,count in edges.items() if count==1]
        if boundary:
            xz=np.array([(v.co.x,v.co.z) for v in mesh.vertices])*1000
            limits=xz[np.unique(np.array(boundary))];lo=limits.min(0)-.24;hi=limits.max(0)+.24
            size=256
            yy,xx=np.mgrid[:size,:size]
            gx=lo[0]+(hi[0]-lo[0])*(xx+.5)/size
            gy=lo[1]+(hi[1]-lo[1])*(yy+.5)/size
            distance=np.full((size,size),1e6)
            for a,b in boundary:
                u,v=xz[a],xz[b];h=v-u
                q=np.clip(((gx-u[0])*h[0]+(gy-u[1])*h[1])/max(1e-12,h@h),0,1)
                distance=np.minimum(distance,np.hypot(gx-u[0]-q*h[0],gy-u[1]-q*h[1]))
            values=np.clip((.48-distance)/.26,0,1)
            rgba=np.stack([values,values,values,np.ones_like(values)],axis=-1).astype('float32')
            im=bpy.data.images.new('Enamel rim of the crown section',size,size,alpha=False)
            im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(rgba.ravel());im.pack()
            uv=mesh.uv_layers.new(name='Crown section plane')
            for lp in mesh.loops:uv.data[lp.index].uv=(xz[lp.vertex_index]-lo)/(hi-lo)
            dentin=M['Dentin • fresh fracture'];fresh=dentin.copy();fresh.name='Sectioned crown • enamel and dentin junction'
            for i,mat in enumerate(mesh.materials):
                if mat==dentin:mesh.materials[i]=fresh
            g=Graph(fresh);uvmap=g.make('ShaderNodeUVMap');uvmap.uv_map=uv.name
            sampler=g.make('ShaderNodeTexImage',Vector=uvmap.outputs[0]);sampler.image=im;sampler.extension='CLIP'
            rim=sampler.outputs[0]
            g.set(**{'Base Color':g.mix(rim,g.current('Base Color'),rgb(.84,.76,.61)),
                     'Transmission Weight':g.mix(rim,(.05,.05,.05,1),(.25,.25,.25,1))})
    piece=O['Buccal cortical bone to be removed'];cutter=O['Growing bur trough']
    milled=M['Cut cortex • ivory trabeculae and pores'].copy();milled.name='Arcuate bur marks on the cut cortical trough'
    g=Graph(milled);q=g.coords.outputs['Object']
    arc=g.make('ShaderNodeTexWave',Vector=g.vec('MULTIPLY',q,(1000,1000,1000)),Scale=1.32,Distortion=1.7,Detail=2.5)
    arc.wave_type='RINGS';arc.rings_direction='X'
    g.bump(arc.outputs['Fac'],.000096,.51)
    g.set(**{'Coat Weight':.79,'Coat Roughness':.13})
    cutter.data.materials.clear();cutter.data.materials.append(milled)
    if milled.name not in piece.data.materials:piece.data.materials.append(milled)
    boolean=next((m for m in piece.modifiers if m.type=='BOOLEAN'),None)
    if boolean:boolean.material_mode='TRANSFER'


def longitudinal_dentin():
    import bmesh
    import numpy as np
    for name in ('Superior root segment','Inferior root segment'):
        ob=O[name];me=ob.data
        donor=M['Dentin • fresh fracture'];idx=me.materials.find(donor.name)
        if idx<0:continue
        mat=donor.copy();mat.name='Longitudinal dentin in '+name.lower()
        me.materials.append(mat);slot=len(me.materials)-1
        bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
        target=[f for f in bm.faces if f.material_index==idx and abs(f.normal.z)>.86]
        if not target:bm.free();continue
        for f in target:f.material_index=slot
        cuts={e for f in target for e in f.edges if e.calc_length()>.00040}
        bmesh.ops.subdivide_edges(bm,edges=list(cuts),cuts=2,use_grid_fill=True)
        bm.normal_update()
        for v in bm.verts:
            cap=[f for f in v.link_faces if f.material_index==slot]
            if not cap:continue
            n=cap[0].normal.copy();p=v.co*1000
            h=(.078*noise.noise(p*1.8)+.047*noise.noise(p*3.1))*.001
            v.co+=n*h
        bm.to_mesh(me);bm.free();me.update()
        faces=[f for f in me.polygons if f.material_index==slot]
        xy=np.array([(v.co.x,v.co.y) for v in me.vertices])*1000
        subset=xy[list({i for f in faces for i in f.vertices})]
        lo=subset.min(0)-.18;hi=subset.max(0)+.18;siz=256
        uv=me.uv_layers.new(name='Long axis of split root')
        for lp in me.loops:uv.data[lp.index].uv=(xy[lp.vertex_index]-lo)/(hi-lo)
        # Intersect the actual outline to follow the narrowing root. Only the
        # parts of the pulp canal intercepted by the section plane are exposed.
        outline={}
        for f in faces:
            for e in f.edge_keys:outline[e]=outline.get(e,0)+1
        pairs=[k for k,c in outline.items() if c==1]
        px=lo[0]+(np.arange(siz)+.5)/siz*(hi[0]-lo[0])
        ys=lo[1]+(np.arange(siz)+.5)/siz*(hi[1]-lo[1])
        tex=np.zeros((siz,siz,4),'float32');tex[:,:,3]=1
        for row,y in enumerate(ys):
            hits=[]
            for a,b in pairs:
                v,w=xy[a],xy[b]
                if min(v[1],w[1])<=y<max(v[1],w[1]):
                    hits.append(v[0]+(w[0]-v[0])*(y-v[1])/(w[1]-v[1]))
            if len(hits)<2:continue
            low,high=min(hits),max(hits);t=(y-lo[1])/(hi[1]-lo[1])
            mid=low+(high-low)*(.48+.070*math.sin(t*6.3))+.09*math.sin(y*2.7)
            radius=(.083+.19*(1-t)**1.5)*min(1,(high-low)/1.5)
            d=np.abs(px-mid)/max(radius,.02)
            reveal=min(1,max(0,(.87-t)*6))*max(.18,min(1,1.25-.76*math.sin(t*8+.4)))
            core=np.exp(-1.55*d*d)*reveal
            sleeve=np.exp(-.34*d*d)*reveal
            tex[row,:,0]=core;tex[row,:,1]=sleeve
        im=bpy.data.images.new('Canal exposed in '+name.lower(),siz,siz,alpha=False)
        im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(tex.ravel());im.pack()
        g=Graph(mat);u=g.make('ShaderNodeUVMap');u.uv_map=uv.name
        sample=g.make('ShaderNodeTexImage',Vector=u.outputs[0]);sample.image=im;sample.extension='CLIP'
        ch=g.make('ShaderNodeSeparateColor',Color=sample.outputs[0]);core,halo=ch.outputs[0],ch.outputs[1]
        base=g.mix(g.math('MULTIPLY',halo,.72),g.current('Base Color'),rgb(.37,.16,.066))
        g.set(**{'Base Color':g.mix(core,base,rgb(.114,.023,.017)),'Coat Roughness':.145})
        g.bump(g.math('SUBTRACT',1,halo),.00021,.62)


def instruments():
    steel=M['Polished instrument steel'];satin=M['Turned surgical steel']
    for mat in (steel,satin,M['Machined carbide']):
        g=Graph(mat);uv=g.coords.outputs['Object']
        # Two different abrasion directions keep the steel from reflecting as chrome plastic.
        drag=g.noise(g.vec('MULTIPLY',uv,(46500,40000,1450)),1,2.8,.20)
        thin=g.ramp(drag,[(.39,0),(.55,.11),(.69,.96),(.77,.19)])
        rough=g.mix(.39,g.current('Roughness'),g.ramp(drag,[(.24,.12),(.60,.27),(.80,.42)]))
        g.set(**{'Roughness':rough,'Metallic':.985})
        anisotropy=next(s for s in g.bs.inputs if 'Anisotrop' in s.name and 'Rotation' not in s.name and 'Subsurface' not in s.name and s.type=='VALUE')
        anisotropy.default_value=.43
        g.bump(thin,.000010,.27)
    parents=['No. 15 scalpel','Straight elevator','Periosteal elevator','Surgical handpiece',
             'Assistant suction • fenestrated Frazier tip','Blunt irrigation cannula','Suture needle pivot','Needle holder']
    for name in parents:
        rig=O[name]
        sub={}
        for ob in list(rig.children_recursive):
            if ob.type not in {'MESH','CURVE'}:continue
            for k,src in enumerate(list(ob.data.materials)):
                if src not in (steel,satin,M['Machined carbide']):continue
                if src not in sub:
                    mat=src.copy();mat.name=src.name+' contact film • '+name;sub[src]=mat
                    g=Graph(mat);g.coords.object=rig;v=g.coords.outputs['Object']
                    dist=g.make('ShaderNodeVectorMath',Vector=v);dist.operation='LENGTH'
                    # For the long irrigating bur use a clear wetting layer. The elevator
                    # and scalpel retain haemoglobin on the distal couple of millimetres.
                    wet=g.ramp(dist.outputs['Value'],[(.0008,1),(.0026,.55),(.0049,0)])
                    patches=g.noise(v,1490,3.7,.73)
                    tint=g.math('MULTIPLY',wet,g.ramp(patches,[(.37,.0),(.56,.18),(.69,.84)]))
                    if name in ('Surgical handpiece','Blunt irrigation cannula'):
                        tint=g.math('MULTIPLY',tint,.23)
                    contact={'No. 15 scalpel':7.47,'Straight elevator':23.66,'Periosteal elevator':10.43,'Surgical handpiece':0,
                        'Blunt irrigation cannula':34.04,'Assistant suction • fenestrated Frazier tip':14.13,
                        'Suture needle pivot':38.18,'Needle holder':38.4}[name]
                    amount=g.make('ShaderNodeValue')
                    for t,val in [(0,0),(contact,0),(contact+.30,1)]:
                        amount.outputs[0].default_value=val;amount.outputs[0].keyframe_insert(data_path='default_value',frame=mm(t))
                    pigment=g.math('MULTIPLY',tint,amount.outputs[0])
                    g.set(**{'Base Color':g.mix(pigment,g.current('Base Color'),rgb(.10,.006,.012)),
                        'Metallic':g.math('SUBTRACT',.985,pigment),'Coat Weight':wet,'Coat Roughness':.085,'Coat IOR':1.334})
                ob.data.materials[k]=sub[src]


def closure():
    # Local capillary stains follow the sewn lips via their resting UVs.
    for ob,x,t in [(bank,26.55,38.18),(flap,31.48,38.88)]:
        g=Graph(ob.data.materials[0])
        u=g.make('ShaderNodeUVMap');u.uv_map='Clinical field (rest)'
        p=((x-14+.1*38.68)/28,(-35.25+50)/28,0)
        d=g.make('ShaderNodeVectorMath');d.operation='DISTANCE'
        g.plug(d.inputs[0],u.outputs[0]);g.plug(d.inputs[1],p)
        ink=g.ramp(d.outputs['Value'],[(.002,1),(.008,.73),(.017,0)])
        value=g.make('ShaderNodeValue')
        for tm,v in [(0,0),(t,0),(t+.20,.78),(40.25,.68)]:
            value.outputs[0].default_value=v;value.outputs[0].keyframe_insert(data_path='default_value',frame=mm(tm))
        g.set(**{'Base Color':g.mix(g.math('MULTIPLY',ink,value.outputs[0]),g.current('Base Color'),rgb(.19,.010,.017))})
    g=Graph(M['Clotted blood • irregular wet top'])
    relief=g.noise(g.coords.outputs['Generated'],11,3.6,.63)
    g.set(**{'Base Color':g.mix(.42,g.current('Base Color'),rgb(.65,.29,.38),'MULTIPLY'),
             'Coat Weight':g.ramp(relief,[(.23,.22),(.56,.33),(.74,.64)]),
             'Coat Roughness':g.ramp(relief,[(.27,.28),(.68,.095)]),'Subsurface Scale':.00039})
    g=Graph(M['Violet braided suture'])
    g.set(**{'Base Color':g.mix(.46,g.current('Base Color'),rgb(.56,.41,.54),'MULTIPLY'),
             'Coat Weight':.44,'Coat Roughness':.14})

def camera_and_light():
    light=O['Operatory lamp • reflected key'].data
    light.size=.0055;light.size_y=.0082;light.energy*=1.09;light.color=(1,.942,.88)
    O['Slim saline specular'].data.size=.00185
    O['Slim saline specular'].data.energy*=.84
    O['Handpiece strip reflection'].data.energy*=.76
    O['Broad diffuse fill'].data.energy*=.72
    O['Cavity fill'].data.energy*=.81
    # The two small emitters produce discrete glints on the curved saliva film.
    target=ZERO+V((31,-35,35))*.001
    for i,(xyz,energy,size) in enumerate([((46,-53,74),.010,.0020),((49,-51,75),.012,.0026)]):
        lamp=bpy.data.lights.new('Surgical lamp emitter '+str(i+1),'AREA');lamp.shape='DISK'
        lamp.size=size;lamp.energy=energy;lamp.color=(1,.955,.906)
        ob=O.new(lamp.name,lamp);S.collection.objects.link(ob)
        ob.location=ZERO+V(xyz)*.001;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    for idx,marker in enumerate(sorted(S.timeline_markers,key=lambda m:m.frame)):
        camera=marker.camera
        if not camera:continue
        camera.data.dof.use_dof=True
        camera.data.dof.aperture_fstop=(47,38,43,39)[idx]
        camera.data.dof.aperture_blades=8
        for frame in range(1,883,3):
            t=(frame-1)/20
            camera.delta_location=(.000043*math.sin(3.6*t+idx)+.000017*math.sin(8.65*t+idx),
                .000033*math.sin(3.10*t+1.6*idx)+.000018*math.cos(6.1*t),.000024*math.sin(4.8*t+.8))
            camera.keyframe_insert(data_path='delta_location',frame=frame)
    # Keep the tapered outer root and its lever in view while each section rises.
    cam=sorted(S.timeline_markers,key=lambda m:m.frame)[2].camera
    for t,at,d,dist,lens in [
        (28.48,(31.9,-31.6,32.4),(.55,.17,.82),33.6,53),
        (29.32,(34.1,-30.8,36.25),(.44,.34,.83),34.5,52),
        (29.65,(34.8,-30.7,37.75),(.44,.36,.83),35.2,51),
        (30.62,(32.5,-31.2,32.9),(.51,.21,.83),32.9,53),
        (31.30,(34.2,-30.55,35.3),(.47,.36,.82),33.6,53),
        (31.90,(35.4,-30.2,37.5),(.43,.37,.82),34.5,52),
        (32.45,(35.3,-30.5,36.1),(.51,.21,.82),34.2,51)]:
        axis=V(d).normalized();cam.location=ZERO+V(at)*.001+axis*dist*.001
        cam.rotation_quaternion=(-axis).to_track_quat('-Z','Y') @ Quaternion((0,0,1),-.038)
        cam.keyframe_insert(data_path='location',frame=mm(t));cam.keyframe_insert(data_path='rotation_quaternion',frame=mm(t))
        cam.data.lens=lens;cam.data.keyframe_insert(data_path='lens',frame=mm(t))
        cam.data.dof.focus_distance=dist*.001;cam.data.keyframe_insert(data_path='dof.focus_distance',frame=mm(t))
    S.render.use_motion_blur=True;S.render.motion_blur_shutter=.34
    for ob in S.objects:
        if ob.type in {'MESH','CURVE'}:
            rotary=ob.parent==O['Rotating carbide']
            ob.cycles.use_motion_blur=rotary
            if rotary:ob.cycles.motion_steps=4
    S.view_settings.exposure+=.05
