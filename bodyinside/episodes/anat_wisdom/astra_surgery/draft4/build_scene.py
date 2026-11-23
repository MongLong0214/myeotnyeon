"""Layer the draft 4 surgical field and cameras onto the registered draft 3 blend."""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector
from math import cos, exp, pi, sin

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1]/'surgery'), str(HERE.parent/'draft3')]
from look import S, O, M, V, ZERO, Graph, rgb, mm, windows, surface_point, flap, bank, bed
from build import key, tube, mesh, world, link, margin
from edit import SHOTS

rng = random.Random(411)
BLOOD = rgb(.128,.0018,.0065)
THIN = rgb(.285,.010,.017)

def newmat(name):
    m=M.new(name)
    m.use_nodes=True
    return m,Graph(m)

def param(g, name, keys):
    n=g.make('ShaderNodeValue')
    n.label=name
    for t,v in keys:
        n.outputs[0].default_value=v
        n.outputs[0].keyframe_insert(data_path='default_value',frame=mm(t))
    return n.outputs[0]

def layers(g, mask, base, wet, rough=.142):
    g.set(**{'Base Color':g.mix(mask,base,wet),
             'Roughness':g.mix(mask,g.current('Roughness'),rough),
             'Coat Weight':g.mix(mask,g.current('Coat Weight'),.58),
             'Coat Roughness':g.mix(mask,g.current('Coat Roughness'),.085)})

def tissue():
    for side, polarity in ((flap,1),(bank,-1)):
        data=side.data
        uv=data.uv_layers.new(name='Depth and distance along incision')
        for lp in data.loops:
            i,j=divmod(lp.vertex_index,89)
            uv.data[lp.index].uv=(i/32,j/88)
        g=Graph(data.materials[0])
        node=g.make('ShaderNodeUVMap');node.uv_map=uv.name
        q=node.outputs[0]
        depth,length=g.make('ShaderNodeSeparateXYZ',Vector=q).outputs[:2]
        large=g.noise(g.vec('MULTIPLY',q,(5,8,1)),1,3.6,.68)
        micro=g.noise(g.vec('MULTIPLY',q,(19,9,1)),3.6,3.5,.85)
        base=g.mix(.52,g.current('Base Color'),g.ramp(large,[(.22,(.62,.25,.24)),(.5,(.88,.60,.56)),(.77,(1,.84,.77))]),'MULTIPLY')
        base=g.mix(g.ramp(depth,[(0,.27),(.23,.07),(.54,.0)]),base,rgb(.49,.13,.14))
        # An irregular front travels with the knife. Side branches spread away from the incision.
        front=param(g,'Knife position',[(7.31,.185),(7.52,.23),(8.35,.435),(9,.598),(9.60,.79),(10,.83)])
        passed=g.ramp(g.math('ADD',.05,g.math('SUBTRACT',front,length)),[(.04,0),(.073,1)])
        ends=g.ramp(length,[(.13,0),(.185,1),(.79,1),(.864,0)])
        width=param(g,'Blood film reach',[(7.25,.08),(9.57,.115),(11.72,.172),(14.2,.23),(16.92,.105),(19.08,.186),(32.74,.202),(35.63,.105),(37.21,.158),(38.48,.075),(42,.069)])
        # Subtract a spatially varying boundary from the transverse coordinate.
        spread=g.math('MULTIPLY',width,g.math('ADD',.34,g.math('MULTIPLY',large,1.10)))
        grain=g.math('MULTIPLY',g.math('SUBTRACT',micro,.5),.15)
        signed=g.math('ADD',.19,g.math('SUBTRACT',spread,g.math('ADD',depth,grain)))
        fresh=g.ramp(signed,[(.125,0),(.174,.25),(.198,.78),(.258,.96)])
        mask=g.math('MULTIPLY',g.math('MULTIPLY',fresh,ends),passed)
        dye=g.ramp(micro,[(.20,(.081,.0015,.004)),(.52,(.17,.004,.011)),(.78,(.31,.019,.029))])
        layers(g,mask,base,dye)
        # A feathered wet highlight crosses the photographed connective tissue.
        g.set(**{'Subsurface Weight':.26,'Subsurface Scale':.00072})
    for name in ['Reflected periosteum • fibrous wet surface','Deep posterior mucosal fold']:
        g=Graph(M[name]);v=g.noise(g.coords.outputs['Object'],380,3.8,.7)
        g.set(**{'Base Color':g.mix(.52,g.current('Base Color'),g.ramp(v,[(.23,(.56,.26,.24)),(.74,(.92,.68,.63))]),'MULTIPLY'),
                 'Coat Weight':.36,'Coat Roughness':.17})
    # Pressure holds briefly as the needle is seated.
    for o in (flap,bank):
        sk=o.data.shape_keys.key_blocks.get('Needle compression')
        if sk:
            base=o.data.shape_keys.key_blocks[0]
            for a,b in zip(base.data,sk.data):
                b.co=a.co+(b.co-a.co)*1.40

def flood_edges():
    material,g=newmat('Fresh mobile film on the cut lips')
    wet=g.noise(g.coords.outputs['Generated'],3.6,3.3,.78)
    g.set(**{'Base Color':g.ramp(wet,[(.2,(.074,.0008,.003)),(.57,(.144,.002,.009)),(.82,(.245,.009,.018))]),
             'Roughness':.115,'Coat Weight':.62,'Coat Roughness':.077,'Transmission Weight':.08,'IOR':1.35})
    # Conform each meniscus to the moving cage. The flow develops after the blade has passed.
    times=[7.25,7.42,7.67,7.94,8.22,8.51,8.80,9.08,9.36,9.61,9.99,10.40,10.78,11.10,11.50,11.95,12.38,12.82,
           14.3,15.1,16.85,18.5,24.1,32.7,35.59,36.61,37.03,37.47,37.85,38.5,42.1]
    js=[13+k*.47 for k in range(130)]
    for side,sign in ((flap,1),(bank,-1)):
        keys=side.data.shape_keys.key_blocks
        basis=keys[0]
        poses=[]
        for t in times:
            S.frame_set(mm(t))
            # Only the first few transverse rows are under the film.
            cage=[p.co.copy() for p in basis.data[:89*13]]
            for k in list(keys)[1:]:
                if k.value>.0001:
                    for i,p in enumerate(cage):p+=(k.data[i].co-basis.data[i].co)*k.value
            verts=[]
            for j in js:
                y=-49+27*j/88
                age=t-(7.36+(y+43.8)/6.95)
                advance=min(1,max(0,age/.28))
                breath=min(1,max(0,age/1.7))
                tip=min(1,max(.0,(j-13)/5),max(.0,(73.6-j)/4))
                lobes=sum(amp*exp(-((j-mid-.9*sin(t*.9+j*.08))/s)**2) for mid,s,amp in [(24,3.6,1.8),(37.5,2.1,2.3),(52,3.1,2.9),(65.6,2.6,1.8)])
                irrigation=1-.57*exp(-((t-16.75)/1.22)**2)-.52*exp(-((t-35.55)/1.0)**2)
                closure=1-.68*min(1,max(0,(t-37.15)/1.1))
                reach=(1+.48*sin(j*.36+sign)+.28*sin(j*.93)+breath*lobes)*tip*advance*irrigation*closure*(1 if sign==1 else .76)
                for u in (0,.18,.44,.72,1):
                    p,n=surface_point(cage,.055+max(.001,reach)*u,j,sign)
                    z=(.048+.148*sin(pi*u)**.74+.064*(1-u))*advance*tip-.19*(1-advance*tip)
                    verts.append((p+n*(z*.001))*1000)
            poses.append(verts)
        faces=[(5*j+i,5*j+i+1,5*j+i+6,5*j+i+5) for j in range(len(js)-1) for i in range(4)]
        o=mesh('Moving blood meniscus on '+side.name,poses[0],faces if sign==1 else [f[::-1] for f in faces],material)
        o.shape_key_add(name='Base')
        for j,pose in enumerate(poses[1:],1):
            k=o.shape_key_add(name='Flow %.2f'%times[j])
            for v,p in zip(k.data,pose):v.co=p*.001
            for ti,val in [(times[0],0),(times[j-1],0),(times[j],1)]+([(times[j+1],0)] if j+1<len(times) else []):
                k.value=val;k.keyframe_insert(data_path='value',frame=mm(ti))
        windows(o,[(7.27,42.12)])
    # The narrow cache remains the source of tiny broken droplets at the lip.
    bead=O['FLIP puncture • 1'].parent
    bead.scale=(1.85,1.65,1.46)
    bead.location.z+=.00005
    droplet=O['FLIP puncture • 1']
    g=Graph(droplet.data.materials[0]);g.set(**{'Base Color':rgb(.167,.002,.009),'Roughness':.115})

def hard_tissues():
    for name in ['Cut cortex • ivory trabeculae and pores','Milled cortex under a thin saline film','Arcuate bur marks on the cut cortical trough']:
        g=Graph(M[name]);q=g.coords.outputs['Object']
        v=g.noise(q,375,3,.76); fine=g.noise(q,1600,2,.45)
        broad=g.ramp(v,[(.21,(.51,.355,.217)),(.51,(.77,.63,.43)),(.79,(.87,.77,.59))])
        g.set(**{'Base Color':broad,'Normal':(0,0,0),'Coat Normal':(0,0,0),'Roughness':.30,
                 'Subsurface Weight':.23,'Subsurface Scale':.00064,'Coat Weight':.43,'Coat Roughness':.16})
        # Replace coarse pores with shallow tool striae on the cut cortex.
        wave=g.make('ShaderNodeTexWave',Vector=g.vec('MULTIPLY',q,(900,900,900)),Scale=1.45,Distortion=2.4,Detail=2)
        wave.wave_type='RINGS';wave.rings_direction='X'
        g.bump(g.mix(.44,fine,wave.outputs['Fac']),.000052,.32)
        # Flushed cancellous points only occur in the trough and on the margin of the bone cap.
        n=g.noise(q,1400,3.2,.5)
        patches=g.ramp(g.math('ADD',v,g.math('MULTIPLY',n,.28)),[(.61,0),(.71,.17),(.78,.85)])
        if name.startswith('Cut cortex'):
            patches=g.math('MULTIPLY',patches,g.ramp(v,[(.42,.12),(.55,.53),(.69,1)]))
        layers(g,patches,broad,THIN,.19)
    g=Graph(bed.data.materials[0])
    r=g.make('ShaderNodeAttribute');r.attribute_name='Radial tissue layer'
    radial=r.outputs['Fac'];n=g.noise(g.coords.outputs['Object'],568,3.6,.91)
    bone=g.ramp(radial,[(.51,.0),(.66,.62),(.75,.75),(.87,.05),(.93,0)])
    base=g.mix(bone,g.current('Base Color'),g.ramp(n,[(.23,(.40,.206,.105)),(.68,(.71,.54,.36))]))
    stain=g.ramp(g.math('ADD',n,g.math('MULTIPLY',radial,.16)),[(.40,.12),(.54,.48),(.62,.85),(.77,.98)])
    zone=g.ramp(radial,[(.18,.92),(.74,.93),(.84,.77),(.97,.30),(1,.06)])
    layers(g,g.math('MULTIPLY',stain,zone),base,g.ramp(n,[(.27,(.29,.022,.020)),(.71,(.122,.002,.007))]))
    g=Graph(M['Hydrated enamel']);q=g.coords.outputs['Generated']
    v=g.noise(q,3.7,3,.81)
    ivory=g.ramp(v,[(.22,(.55,.37,.17)),(.50,(.76,.605,.369)),(.80,(.88,.78,.55))])
    g.set(**{'Base Color':g.mix(.58,g.current('Base Color'),ivory),'Subsurface Scale':.00096,'Subsurface Weight':.39,
             'Roughness':.205,'Transmission Weight':.23,'Coat Weight':.50,'Coat Roughness':.14})
    # The stain along the cervical margin follows the tooth into the gauze shot.
    for obname in ('Crown','Root','Superior root segment','Inferior root segment'):
        ob=O[obname]
        for i,mat in enumerate(list(ob.data.materials)):
            m=mat.copy();m.name=mat.name+' | '+obname+' wet'
            ob.data.materials[i]=m;g=Graph(m)
            uv=g.coords.outputs['Object']
            n=g.noise(g.vec('MULTIPLY',uv,(800,230,610)),.86,3.4,.41)
            broad=g.noise(uv,235,3,.54)
            co=g.make('ShaderNodeSeparateXYZ',Vector=uv)
            if i==0 and obname=='Crown':
                toward=g.math('MULTIPLY',co.outputs['Y'],69)
                v=g.math('ADD',g.math('ADD',n,g.math('MULTIPLY',.50,broad)),toward)
                mask=g.ramp(v,[(.78,0),(.89,.15),(.99,.84)])
            else:
                v=g.math('ADD',n,g.math('MULTIPLY',broad,.48))
                v=g.math('ADD',v,g.math('MULTIPLY',co.outputs['Z'],21))
                pts=[(.55,.04),(.69,.20),(.78,.67),(.89,.92)] if i<2 else [(.66,0),(.79,.14),(.89,.76)]
                mask=g.ramp(v,pts)
            base=g.current('Base Color')
            if obname!='Crown' and i<2:base=g.mix(.54,base,rgb(.56,.37,.23),'MULTIPLY')
            layers(g,mask,base,g.ramp(broad,[(.24,(.092,.002,.005)),(.71,(.248,.011,.015))]),.155)
    # Slender ivory and red ligament remnants drape along the outer cementum only.
    ligament,g=newmat('Periodontal ligament remnants')
    g.set(**{'Base Color':rgb(.51,.228,.144),'Roughness':.31,'Subsurface Weight':.24,'Subsurface Scale':.00026,'Coat Weight':.48})
    for obname,start,end in [('Superior root segment',28,30.1),('Inferior root segment',30.12,32.73)]:
        ob=O[obname]
        faces=[p for p in ob.data.polygons if p.material_index in (0,1) and abs(p.normal.z)<.85]
        for j in range(26):
            f=rng.choice(faces);p=f.center*1000;n=f.normal.normalized()
            t=V((rng.uniform(-.3,.3),rng.uniform(.4,1),rng.uniform(-1,-.2)));t=(t-n*t.dot(n)).normalized()
            length=rng.uniform(.42,1.18)
            pts=[p+n*.022,p+t*length*.32+n*.12,p+t*length*.72+n*.16,p+t*length+n*.05+V((0,0,-.12))]
            strand=tube('Periodontal tuft '+obname,pts,rng.uniform(.031,.059),ligament if j%3 else M['Oozing capillary blood'],ob,radii=(.67,1,.62,.07))
            windows(strand,[(start,end)])

def tooth_relief():
    # Keep matching points on both sides of the section coincident until the lever separates them.
    S.frame_set(mm(23.48))
    for name in ('Crown','Root','Superior root segment','Inferior root segment'):
        ob=O[name];me=ob.data
        home=V((30,-39.4 if name=='Crown' else -31.23,31.8))
        for v in me.vertices:
            x,y,z=v.co*1000+home
            fall=exp(-((y+35.70)/.87)**2)
            low=.25+.75*min(1,max(0,(35.55-z)/3.3))
            v.co.y+=.001*fall*low*(.22*sin(x*2.8+z*1.61)+.135*sin(z*4.02-x*1.16)+.065*cos(x*5.2+z*3.6))
        me.update()
    ob=O['Crown'];me=ob.data
    neighbours=[[] for _ in me.vertices]
    for e in me.edges:
        a,b=e.vertices;neighbours[a].append(b);neighbours[b].append(a)
    grooves=me.attributes.new('Occlusal fissure pigment','FLOAT','POINT')
    for i,v in enumerate(me.vertices):
        if not neighbours[i]:continue
        vecs=[me.vertices[j].co-v.co for j in neighbours[i]]
        local=sum(vecs,V())/len(vecs)
        curve=max(0,local.dot(v.normal))/max(1e-9,sum(d.length for d in vecs)/len(vecs))
        front=max(0,min(1,(-v.co.y*1000-.65)/1.8))
        grooves.data[i].value=min(.91,max(0,(curve-.010)*7.5))*front
    g=Graph(ob.data.materials[0]);a=g.make('ShaderNodeAttribute');a.attribute_name=grooves.name
    n=g.noise(g.vec('MULTIPLY',g.coords.outputs['Object'],(1,.67,1.23)),670,3.4,.40)
    base=g.mix(.20,g.current('Base Color'),g.ramp(n,[(.23,(.69,.49,.28)),(.77,(.99,.91,.75))]),'MULTIPLY')
    g.set(**{'Base Color':g.mix(a.outputs['Fac'],base,rgb(.32,.169,.065)),
             'Coat Roughness':.158,'Roughness':.225})
    g.bump(n,.000028,.18)


def fluids_and_steel():
    for m in list(M):
        if 'contact film •' not in m.name:continue
        tool=m.name.split('contact film • ')[-1];rig=O.get(tool)
        if not rig:continue
        g=Graph(m);g.coords.object=rig;v=g.coords.outputs['Object']
        length=g.make('ShaderNodeVectorMath',Vector=v);length.operation='LENGTH'
        mm_dist=g.math('MULTIPLY',length.outputs['Value'],160)
        splash=g.noise(g.vec('MULTIPLY',v,(1450,1150,620)),1.24,3.3,.63)
        reach=g.ramp(g.math('SUBTRACT',mm_dist,g.math('MULTIPLY',splash,.57)),[(.09,.98),(.36,.88),(.58,.28),(.75,0)])
        val={'No. 15 scalpel':7.37,'Straight elevator':23.49,'Periosteal elevator':10.38,'Surgical handpiece':13.62,
             'Blunt irrigation cannula':34.22,'Assistant suction • fenestrated Frazier tip':14.1,'Suture needle pivot':38.20,'Needle holder':38.35}[tool]
        amount=param(g,'First contact',[(val-.04,0),(val+.33,.98)])
        mask=g.math('MULTIPLY',g.math('MULTIPLY',amount,reach),g.ramp(splash,[(.32,.29),(.50,.76),(.63,.97)]))
        layers(g,mask,g.current('Base Color'),g.ramp(splash,[(.25,(.29,.012,.022)),(.66,(.107,.0017,.0055))]))
        g.set(**{'Metallic':g.mix(mask,g.current('Metallic'),.035)})
    # Real low-profile menisci catch the light along the two sharpened working edges.
    m,g=newmat('Blood still clinging to the working edge')
    g.set(**{'Base Color':rgb(.141,.002,.007),'Roughness':.143,'IOR':1.36,
             'Coat Weight':.55,'Coat Roughness':.11,'Transmission Weight':.07})
    for name,thick,start,end in [('No. 15 blade',.19,7.38,10.14),('Straight elevator spatula',.22,23.52,32.96)]:
        tool=O[name]
        for face in (-1,1):
            verts=[]
            # The footprint straddles the face and wraps around the tip. The
            # serrated upper edge thins to nothing just above the contact area.
            for k in range(25):
                q=k/24
                z=.28+2.23*q
                left=(-.42-.47*sin(min(q*2.3,1)*pi/2)) if name.startswith('Straight') else (-.32-.99*sin(min(q*1.8,1)*pi/2))
                span=(.49+.18*sin(12*q)+.15*sin(31*q))*(sin(pi*(.03+.94*q))**.54)
                for u in (0,.21,.60,1):
                    verts.append((left+u*span,face*(thick+.011+.037*sin(pi*u)),z+.065*sin(q*23+u)))
            fs=[(4*k+h,4*k+h+1,4*k+h+5,4*k+h+4) for k in range(24) for h in range(3)]
            slick=mesh('Wetted cutting edge '+name,verts,fs,m,tool)
            windows(slick,[(start,end)] if name.startswith('No.') else [(start,27.12),(28.08,32.90)])
            for t,fraction in [(start,.025),(start+.42,1)]:key(slick,'scale',t,(fraction,1,fraction))
    # Rotary contact releases a pink, mineral-bearing film. The moving suction clears a tapered corridor.
    for m in (M['Cut cortex • ivory trabeculae and pores'],M['Arcuate bur marks on the cut cortical trough'],bed.data.materials[0]):
        g=Graph(m);g.coords.object=O['Surgical handpiece'];v=g.coords.outputs['Object']
        d=g.make('ShaderNodeVectorMath',Vector=g.vec('MULTIPLY',v,(.78,.62,.93)));d.operation='LENGTH'
        n=g.noise(g.coords.outputs['Generated'],6,3.2,1.1)
        skin=g.ramp(g.math('SUBTRACT',g.math('MULTIPLY',d.outputs['Value'],136),g.math('MULTIPLY',n,.49)),[(0,.94),(.26,.88),(.45,.53),(.64,.04),(.7,0)])
        u=g.make('ShaderNodeTexCoord');u.object=O['Assistant suction • fenestrated Frazier tip']
        dst=g.make('ShaderNodeVectorMath',Vector=u.outputs['Object']);dst.operation='LENGTH'
        cut=g.ramp(g.math('MULTIPLY',dst.outputs['Value'],240),[(.05,.09),(.31,.30),(.75,1)])
        wet=g.math('MULTIPLY',skin,cut)
        slurry=g.ramp(n,[(.24,(.33,.035,.045)),(.48,(.49,.11,.12)),(.68,(.71,.27,.25)),(.81,(.81,.50,.34))])
        layers(g,wet,g.current('Base Color'),slurry,.13)
    g=Graph(M['Saline carrying wet mineral dust']);g.coords.object=O['Surgical handpiece']
    z=g.make('ShaderNodeSeparateXYZ',Vector=g.coords.outputs['Object']).outputs['Z']
    impact=g.ramp(g.math('ADD',.36,g.math('MULTIPLY',z,120)),[(.30,.88),(.54,.69),(.83,0)])
    layers(g,impact,g.current('Base Color'),rgb(.54,.145,.158),.115)
    g.set(**{'Transmission Weight':g.mix(impact,g.current('Transmission Weight'),.27)})
    g=Graph(M['Rose effluent at the aspirator']);g.set(**{'Base Color':rgb(.42,.066,.083),'Transmission Weight':.26})
    # The cache includes the fine drops and the entering saline jet. Extend the meniscus up the actual socket wall.
    mat,g=newmat('Raised socket meniscus | saline fronts and returning blood')
    pos=g.coords.outputs['Object']
    ng=g.make('ShaderNodeTexNoise',Vector=g.vec('MULTIPLY',pos,(550,320,270)),Scale=1,Detail=3.6,Distortion=1.45)
    ng.noise_dimensions='4D';travel=param(g,'Swirl advection',[(25,.1),(33.84,.24),(34.63,.60),(35.68,1.32),(36.48,1.67),(37.31,1.73)])
    g.plug(ng.inputs['W'],travel);dye=ng.outputs['Fac']
    strength=param(g,'Irrigant influx and washout',[(25,0),(33.88,0),(34.48,.6),(35.10,.93),(35.72,1.15),(36.02,.96),(36.26,.79),(36.71,.37),(37.12,0)])
    phase=g.math('ADD',g.math('SUBTRACT',strength,g.math('MULTIPLY',dye,.70)),.10)
    clear=g.ramp(phase,[(.12,0),(.46,.50),(.71,.91)])
    c=g.ramp(dye,[(.22,(.069,.0007,.0033)),(.56,(.133,.0026,.008)),(.80,(.211,.0055,.014))])
    g.set(**{'Base Color':g.mix(clear,c,g.ramp(dye,[(.2,(.59,.19,.20)),(.78,(.82,.46,.45))])),
             'Transmission Weight':g.mix(clear,.075,.55),'Roughness':.166,'IOR':1.346,'Coat Weight':.41,'Coat Roughness':.136})
    wet=g.noise(pos,980,2,.36);g.bump(wet,.000043,.26)
    heights=[(25.36,25.7),(26.45,27.44),(29.12,28.17),(31.10,28.26),(31.80,28.57),(32.68,29.03),(33.21,30.18),
             (33.87,32.12),(34.52,32.34),(35.27,30.47),(35.83,29.18),(36.18,29.25),(36.60,30.57),(37.17,32.46),(38.02,32.54),(42.16,32.57)]
    cols=128;rings=19
    spokes=[[bed.data.vertices[j*cols+i].co*1000 for j in range(9)] for i in range(cols)]
    def level(t,h):
        ps=[]
        for k in range(rings):
            r=.0002+.9998*k/(rings-1)
            for i,spoke in enumerate(spokes):
                for lo,hi in zip(spoke,spoke[1:]):
                    if hi.z>h:break
                v=lo.lerp(hi,max(0,min(1,(h-lo.z)/max(.001,hi.z-lo.z))))
                a=2*pi*i/cols
                x=30.05+(v.x-30.05)*r*1.029;y=-35.65+(v.y+35.65)*r*1.029
                rr=math.hypot(x-31.25,y+34.4)
                wash=exp(-((t-35.12)/.96)**2)
                z=h+.13*r**7-min(.98,max(0,h-spoke[6].z))*(r**5)+.046*(sin(3*a+7*r+2.7*t)+.47*cos(5*a-3.5*r-2*t))*r+.13*wash*cos(3.5*rr-9*t)*exp(-rr/4.2)
                ps.append((x,y,z))
        return ps
    faces=[(k*cols+i,(k+1)*cols+i,(k+1)*cols+(i+1)%cols,k*cols+(i+1)%cols) for k in range(rings-1) for i in range(cols)]
    pool=mesh('Rising blood conforming to the socket wall',level(*heights[0]),faces,mat)
    pool.shape_key_add(name='Floor')
    for j,(t,h) in enumerate(heights[1:],1):
        sk=pool.shape_key_add(name='Fill at %.2f'%t)
        for v,co in zip(sk.data,level(t,h)):v.co=V(co)*.001
        for tm,val in [(25.35,0),(heights[j-1][0],0),(t,1)]+([(heights[j+1][0],0)] if j+1<len(heights) else []):
            sk.value=val;sk.keyframe_insert(data_path='value',frame=mm(tm))
    windows(pool,[(25.35,42.16)])
    crack=O['Fracture trace • buccal extent of the groove']
    crack.data.bevel_depth*=1.18
    crack.data.materials[0]=M['Oozing capillary blood']

def trim():
    for ob in list(S.objects):
        if ob.type=='CURVE' and M['Violet braided suture'].name in ob.data.materials:
            ob.data.bevel_depth*=1.22
    g=Graph(M['Violet braided suture']);g.set(**{'Base Color':rgb(.028,.008,.041),'Coat Weight':.34,'Coat Roughness':.18})
    tails=sorted((o for o in S.objects if o.name.startswith('Free suture end tightening')),key=lambda o:o.name)
    S.frame_set(mm(40.50))
    org=margin(.515)
    # Fold both free ends into the scissor bite. Short material stays on the knot;
    # the two offcuts recoil with the blades after they close.
    origin=org+V((.83,1.51,1.06))
    for side,ob in zip((-1,1),tails):
        pts=ob.data.splines[0].bezier_points
        old=[p.co.copy()*1000 for p in pts]
        target=origin+V((.36*side,.04*side,.07*side))
        updated=old[:3]+[org+V((.18*side,.39,.62)),org+V((.46+.26*side,.69,.69)),target.lerp(org+V((.46+.26*side,.69,.69)),.36),target]
        for i,p in enumerate(pts):
            if i<3:continue
            attr=f'splines[0].bezier_points[{i}].co'
            key(ob.data,attr,40.50,old[i]*.001);key(ob.data,attr,40.88,updated[i]*.001)
        coords=[V((0,0,0)),V((.23,.52,.32)),V((.49,1.05,.55)),V((.88,1.82,.81))]
        scrap=tube('Trimmed violet free end',coords,.104,M['Violet braided suture'],origin=world(target))
        windows(scrap,[(40.47,41.75)])
        for t,v in [(40.47,old[-1]),(40.88,target),(41.31,target),(41.45,target+V((.53*side,.66,.51))),
                    (41.74,target+V((3.8*side,2.5,-2.9)))]:
            key(scrap,'location',t,world(v))
        for t,scale in [(40.47,.02),(40.78,1)]:key(scrap,'scale',t,(scale,)*3)
    # Working blades are hinged at their broad ends, with a shallow curved profile and polished bevel.
    pivot=origin+V((6.15,1.7,3.24))
    rig=link('Iris scissors · trim pivot')
    for t,offset in [(40.5,(10,5,9)),(40.78,(3.2,1,2.2)),(41.06,(0,0,0)),(41.36,(0,0,0)),(41.75,(9,4,8))]:
        key(rig,'location',t,world(pivot+V(offset)))
    vec=origin-pivot;d=vec.normalized()
    side=V((-.31,.94,.04)).normalized();n=d.cross(side).normalized();side=n.cross(d).normalized()
    steel=M['Polished instrument steel']
    for sign in (-1,1):
        verts=[];sections=[(-8,.65),(-3,.60),(0,.73),(1.7,.66),(4.5,.41),(6.6,.23),(vec.length+.85,.024)]
        for along,w in sections:
            centre=d*along+side*sign*(w*.64)+n*(.13*sign+max(0,along/8)**2*.10)
            verts.extend([centre+side*w+n*.13,centre-side*w+n*.04,centre-side*w-n*.04,centre+side*w-n*.13])
        faces=[(4*i+j,4*i+(j+1)%4,4*i+4+(j+1)%4,4*i+4+j) for i in range(len(sections)-1) for j in range(4)]
        blade=mesh('Curved trimming blade',verts,faces,steel,rig,smooth=False)
        blade.rotation_mode='QUATERNION'
        for t,angle in [(40.5,.18),(41.08,.145),(41.20,.083),(41.32,0),(41.43,.012),(41.74,.105)]:
            key(blade,'rotation_quaternion',t,Quaternion(n,sign*angle))
        bev=blade.modifiers.new('Honed edge','BEVEL');bev.width=.000048;bev.segments=2
        windows(blade,[(40.50,41.76)])

def specimen():
    from mathutils import Euler
    center=V((147,-35,38))
    chart=link('Specimen gauze coordinates')
    chart.location=world(center)
    cotton,g=newmat('Cotton gauze | interlaced fibres and capillary wick')
    g.coords.object=chart
    q=g.vec('MULTIPLY',g.coords.outputs['Object'],(1000,1000,1000))
    fuzz=g.noise(q,11.2,2.5,.49)
    broken=g.noise(q,1.15,3.7,.76)
    tissue=g.ramp(fuzz,[(.18,(.59,.59,.53)),(.53,(.79,.80,.73)),(.85,(.93,.92,.85))])
    cover=0
    positions=[(-3.55,5.85),(4.3,-.85),(-3.15,-6.50)]
    for i,((x,y),(sx,sy)) in enumerate(zip(positions,[(.16,.175),(.22,.189),(.23,.245)])):
        v=g.vec('MULTIPLY',g.vec('SUBTRACT',q,(x,y,0)),(sx,sy,0))
        d=g.make('ShaderNodeVectorMath',Vector=v);d.operation='LENGTH'
        dist=g.math('SUBTRACT',g.math('MULTIPLY',d.outputs['Value'],.70),g.math('MULTIPLY',broken,.62))
        if i==2:
            wick=param(g,'Last fragment wicks into cotton',[(44.1,0),(45.57,0),(45.86,.36),(46.60,.79),(48.1,1)])
            dist=g.math('ADD',dist,g.math('SUBTRACT',1,wick))
        cover=g.math('MAXIMUM',cover,g.ramp(dist,[(.02,.95),(.34,.83),(.60,.56),(.80,.19),(.97,0)]))
    tint=g.ramp(broken,[(.20,(.095,.002,.006)),(.55,(.30,.020,.035)),(.76,(.55,.102,.11))])
    g.set(**{'Base Color':g.mix(cover,tissue,tint),'Roughness':.77,'Sheen Weight':.28,'Sheen Roughness':.73})
    g.bump(fuzz,.000044,.47)
    def cloth(x,y):
        return .15*sin(x*.29+y*.08)+.27*cos(y*.22+x*.11)+.11*sin(x*.72-y*.26)+1.07*exp(-((y-10+.48*x)/2.4)**2)+.63*sin(y*.15-x*.17)
    backing,g=newmat('Surgical drape beneath gauze')
    n=g.noise(g.coords.outputs['Object'],4550,3)
    g.set(**{'Base Color':g.ramp(n,[(.27,(.036,.10,.096)),(.73,(.108,.235,.217))]),'Roughness':.82});g.bump(n,.000085,.30)
    plane=mesh('Operatory drape',[(x,y,-1.08) for x,y in [(-43,-49),(43,-49),(43,49),(-43,49)]],[(0,1,2,3)],backing,chart)
    # Two offset plies keep actual gaps and occlusion between cotton yarns.
    for ply,(step,depth) in enumerate(((.53,-.36),(.52,0))):
        verts=[];faces=[]
        for axis in (0,1):
            half,run=(24.2,16.7) if axis==0 else (16.7,24.2)
            for line in range(-int(half/step),int(half/step)+1):
                base=line*step+ply*.17;start=len(verts)
                ct=int(2*run/(step/3))
                for j in range(ct+1):
                    a=-run+j*step/3
                    b=base+.069*sin(a*.80+line*.54)+.069*sin(a*.30+line*.66)+.24*sin(a*.19+base*.22)+ply*.13
                    x,y=(a,b) if axis==0 else (b,a)
                    if not ply:
                        x,y=x*.996-y*.082,y*.996+x*.082
                    z=cloth(x,y)+depth+.095*cos(a*pi/step+line*pi+ply*.33)*(1 if axis==0 else -1)
                    rr=.158+.024*sin(a*2.35+line)+.013*cos(a*.33+line*1.4)
                    for k in range(5):
                        phase=2*pi*k/5
                        off=rr*cos(phase)
                        verts.append((x+(off if axis else 0),y+(0 if axis else off),z+rr*.76*sin(phase)))
                        if j:
                            ix=start+j*5
                            faces.append((ix-5+k,ix-5+(k+1)%5,ix+(k+1)%5,ix+k))
        mesh('Plain weave cotton ply '+str(ply+1),verts,faces,cotton,chart)
    for i,(name,(x,y),angles) in enumerate(zip(('Crown','Superior root segment','Inferior root segment'),positions,
                                                 [(-52,21,-29),(39,23,32),(-44,12,-36)])):
        src=O[name];o=O.new('Retrieved '+name.lower(),src.data);S.collection.objects.link(o)
        rot=Euler(tuple(math.radians(a) for a in angles)).to_quaternion()
        pts=[rot@v.co*1000 for v in o.data.vertices]
        midx=(min(p.x for p in pts)+max(p.x for p in pts))/2;midy=(min(p.y for p in pts)+max(p.y for p in pts))/2
        centre=V((x-midx,y-midy,cloth(x,y)+.06-min(p.z for p in pts)))
        holder=link('Specimen placement '+name);holder.parent=chart;holder.location=centre*.001
        o.parent=holder;o.rotation_mode='QUATERNION';o.rotation_quaternion=rot
        for strand in src.children:
            if not strand.name.startswith('Periodontal tuft'):continue
            dup=O.new('Adhering ligament on gauze',strand.data);S.collection.objects.link(dup);dup.parent=o
        if i!=2:continue
        for t,offset,tilt in [(44.10,(3.0,-.8,5.4),-.25),(44.88,(1.55,-.48,2.85),-.14),
                              (45.50,(.17,-.05,.42),-.035),(45.70,(0,0,0),0),(45.85,(-.13,.06,-.035),.026)]:
            key(holder,'location',t,(centre+V(offset))*.001)
            key(holder,'rotation_euler',t,(0,tilt,.32*tilt))
        # Locate two opposing purchase points on this fragment in its laid-down pose.
        z=sorted(p.z for p in pts)[int(len(pts)*.66)]
        near=[p for p in pts if abs(p.z-z)<.9 and abs(p.y-midy)<1.2] or pts
        for sign in (-1,1):
            contact=(min if sign<0 else max)(near,key=lambda p:p.x)
            tip=link('Specimen forceps articulating arm');tip.parent=holder
            for t,offset in [(44.1,(0,0,0)),(45.69,(0,0,0)),(46,(sign*.68,.11,.34)),(46.45,(sign*1.22,2.7,3.7)),(47.30,(sign*1.75,21,27))]:
                key(tip,'location',t,(contact+V(offset))*.001)
            vs=[];fs=[]
            for j,(h,wx,wy) in enumerate([(0,.12,.31),(.9,.22,.39),(3.7,.31,.48),(10,.44,.69),(21,.56,.85)]):
                axis=V((sign*h*.16+.22*h,.52*h,h))
                for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append(axis+V((wx*dx,wy*dy,0)))
                if j:fs.extend((4*j-4+k,4*j-4+(k+1)%4,4*j+(k+1)%4,4*j+k) for k in range(4))
            fs.extend([(3,2,1,0),(16,17,18,19)])
            jaw=mesh('Specimen forceps jaw',vs,fs,M['Turned surgical steel'],tip,smooth=False)
            bevel=jaw.modifiers.new('Rounded forceps edges','BEVEL');bevel.width=.00009;bevel.segments=2
    for i,(p,w,h,power,col) in enumerate([((-16,-18,31),17,21,.105,(1,.947,.86)),((13,11,21),5,14,.049,(.83,.91,1)),((17,-16,12),12,15,.035,(1,.89,.79))]):
        lt=bpy.data.lights.new('Specimen lamp '+str(i),'AREA');lt.shape='RECTANGLE';lt.size=w*.001;lt.size_y=h*.001;lt.energy=power*.68;lt.color=col
        ob=link(lt.name,lt);ob.location=world(center+V(p));ob.rotation_euler=(-V(p)).to_track_quat('-Z','Y').to_euler()

def cameras():
    # Every lens points at a measured contact or at the centre of the extracted specimen.
    specs={
    'fracture':[(23.52,(33.5,-35.58,32.56),(.80,.30,.52),24,66,-10,32),(24.58,(33.62,-35.96,33.14),(.76,.24,.60),24.8,66,-8,32)],
    'anaesthesia':[(3.78,(30.70,-25.48,39.10),(.57,-.59,.58),20.8,67,-13,29),(4.53,(30.65,-25.5,38.96),(.56,-.58,.60),20.2,68,-12,29),(6.59,(30.65,-25.5,39.18),(.53,-.54,.66),20.3,70,-10,30)],
    'access':[(7.22,(29.41,-43.66,38.78),(.57,-.30,.76),23,61,-12,30),(7.57,(29.15,-42.77,38.63),(.56,-.32,.76),22,65,-10,30),(8.35,(28.54,-38.34,38.47),(.56,-.30,.78),22.2,67,-8,31),(9.58,(29.5,-30.6,38.83),(.56,-.21,.80),23.0,61,-7,32),(10.49,(30.15,-37.7,39.05),(.55,-.34,.79),26.8,59,-6,36),(11.22,(32.4,-37.65,40.30),(.56,-.34,.79),28.4,57,-5,35),(12.8,(32.9,-37.72,35.56),(.56,-.32,.81),28.8,57,-5,36)],
    'osteotomy':[(13.47,(34.25,-40.82,35.5),(.42,.44,.80),29.3,59,-4,36),(15.5,(34.50,-39.11,35.4),(.49,.42,.76),27.1,60,-3,35),(16.46,(34.40,-37.93,34.8),(.49,.44,.75),28.4,59,-3,36)],
    'aspiration':[(16.46,(35.27,-39.05,33.36),(.66,.44,.68),23.95,65,9,32),(18.06,(35.14,-37.68,33.48),(.61,.45,.71),25.55,63,6,34)],
    'section':[(19.2,(33.5,-35.72,33.5),(.66,.29,.69),28.2,58,-2,36),(22.6,(33.5,-35.5,32.9),(.71,.30,.64),27.3,60,-2,36),(24.89,(33.25,-35.9,33.12),(.67,.35,.66),28.0,59,-1,36)],
    'delivery':[(24.89,(33.02,-36.9,33.8),(.60,.30,.73),30.1,60,-3,36),(25.94,(35.48,-39.72,40.04),(.56,.38,.74),30.6,55,-4,42),(26.22,(36.54,-39.70,42.28),(.54,.39,.75),31.5,54,-4,42),(26.62,(34.0,-35.4,36.2),(.51,.40,.77),31.5,52,-4,38),(27.65,(32.5,-30.9,32.7),(.54,.17,.82),29.5,55,-4,36),(28.57,(32.9,-31.3,33.0),(.55,.17,.82),28.1,57,-4,35),(29.21,(35.3,-30.9,38.8),(.47,.36,.81),30.5,55,-6,41),(29.52,(38.4,-29.7,43.0),(.46,.34,.83),31.3,54,-5,43),(29.77,(38.9,-29.69,43.1),(.47,.32,.82),31.3,53,-5,43),(30.52,(32.6,-31.3,33.3),(.52,.19,.84),29.1,57,-4,36),(31.42,(35.2,-30.4,36.15),(.44,.36,.83),29.9,56,-5,39),(32.02,(37.75,-29.6,40.1),(.45,.34,.83),31.2,56,-5,41),(32.84,(32.14,-33.0,32.44),(.53,.19,.83),30.4,56,-4,35)],
    'socket':[(32.84,(30.42,-35.1,29.1),(.48,-.29,.84),27.8,61,-5,36),(33.91,(30.5,-35.15,31.61),(.44,-.3,.86),26.6,62,-4,37),(35.63,(30.5,-35.2,30.36),(.44,-.30,.86),27.4,60,-3,38),(37.28,(30.53,-35.12,32.62),(.43,-.27,.86),27.9,60,-4,37)],
    'closure':[(37.59,(28.93,-35.29,38.69),(.46,-.34,.82),25,61,-4,35),(39.33,(28.83,-35.33,38.94),(.46,-.29,.84),24.7,64,-5,35),(40.55,(28.92,-35.12,39.0),(.45,-.28,.85),22.2,66,-6,34),(41.38,(29.25,-34.59,39.15),(.44,-.29,.85),21.7,67,-6,34),(42.04,(29.15,-34.71,38.96),(.43,-.30,.85),22.6,65,-5,34)],
    'specimen':[(44.1,(147.0,-36.25,40.04),(.14,-.41,.90),40.5,55,9,49),(45.72,(146.45,-36.09,40.54),(.13,-.38,.92),39.3,55,8,49),(48.10,(146.92,-34.78,40.33),(.12,-.31,.94),38.8,54,6,51)]}
    for shot,rows in specs.items():
        cam=bpy.data.cameras.new('Macro '+shot);ob=link(cam.name,cam)
        cam.sensor_fit='HORIZONTAL';cam.sensor_width=36;cam.clip_start=.0006;cam.clip_end=10
        ob.rotation_mode='QUATERNION';cam.dof.use_dof=True;cam.dof.aperture_blades=9
        for t,p,d,dist,lens,roll,fstop in rows:
            axis=V(d).normalized()
            key(ob,'location',t,world(p)+axis*dist*.001)
            key(ob,'rotation_quaternion',t,(-axis).to_track_quat('-Z','Y')@Quaternion((0,0,1),math.radians(roll)))
            key(cam,'lens',t,lens);key(cam,'dof.focus_distance',t,dist*.001);key(cam,'dof.aperture_fstop',t,fstop)
        cam.shift_y=-.045
    # Keep the native source timeline convenient to inspect. The edit also uses a separate hook lens.
    S.timeline_markers.clear()
    for shot,marks in SHOTS[1:]:
        mk=S.timeline_markers.new(shot,frame=mm(marks[0][1]));mk.camera=O['Macro '+shot]

def main():
    tissue();flood_edges();hard_tissues();tooth_relief();fluids_and_steel();trim();specimen();cameras()
    S.frame_end=mm(48.10)
    S.view_settings.exposure-=.14
    O['Operatory lamp • reflected key'].data.color=(1,.967,.925)
    O['Cavity fill'].data.energy*=.86
    S.render.resolution_x,S.render.resolution_y=540,960;S.render.resolution_percentage=100
    S.render.fps=20;S.cycles.samples=10;S.cycles.use_denoising=True
    S.cycles.denoiser='OPENIMAGEDENOISE';S.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
    S.render.filepath='//renders/f_';S.frame_set(mm(23.88));S.camera=O['Macro fracture']
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'surgery_draft4.blend'),compress=True,relative_remap=True)
    print('DRAFT 4 SAVED',flush=True)
if __name__=='__main__':main()
