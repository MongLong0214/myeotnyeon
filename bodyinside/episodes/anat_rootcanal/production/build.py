"""Build and key the 930-frame native Blender sequence. One local scene unit is a millimetre."""
import bpy, math, json, random, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
EP=HERE.parent; WORK=EP.parents[1]; CACHE=HERE/'.cache';ASSETS=WORK/'episodes/anat_wisdom/astra_surgery/assets'
D=bpy.data; S=bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.render.fps=30;S.frame_start=0;S.frame_end=929;S.unit_settings.system='METRIC';S.unit_settings.scale_length=.001
S.render.engine='CYCLES';S.cycles.samples=24;S.cycles.use_denoising=True;S.cycles.denoiser='OPENIMAGEDENOISE'
S.cycles.max_bounces=5;S.cycles.diffuse_bounces=2;S.cycles.glossy_bounces=3;S.cycles.transmission_bounces=3
S.render.resolution_x=1080;S.render.resolution_y=1920;S.render.resolution_percentage=100
S.render.image_settings.file_format='JPEG';S.render.image_settings.quality=98;S.render.use_persistent_data=True
S.view_settings.view_transform='AgX'
rng=random.Random(396); tau=2*math.pi
materials={}
def shade(name,cols,rough,scale,relief=.025,metal=0,coat=0,sss=0,imagefile=None,usage='bump'):
    mat=D.materials.new(name);mat.use_nodes=True;materials[name]=mat
    nt=mat.node_tree;nodes=nt.nodes;link=nt.links.new
    bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Coat Weight'].default_value=coat;bs.inputs['Coat Roughness'].default_value=min(.24,rough)
    bs.inputs['Subsurface Weight'].default_value=sss;bs.inputs['Subsurface Scale'].default_value=.15
    tc=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');link(tc.outputs['Object'],noise.inputs['Vector']);noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3.8;noise.inputs['Roughness'].default_value=.65
    ramp=nodes.new('ShaderNodeValToRGB');c=ramp.color_ramp;c.elements[0].position=.23;c.elements[0].color=(*cols[0],1);c.elements[1].position=.76;c.elements[1].color=(*cols[-1],1)
    if len(cols)==3:c.elements.new(.49).color=(*cols[1],1)
    link(noise.outputs['Fac'],ramp.inputs[0]);link(ramp.outputs[0],bs.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.29;bump.inputs['Distance'].default_value=relief
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=scale*5.2;fine.inputs['Detail'].default_value=2
    link(tc.outputs['Object'],fine.inputs[0]);link(fine.outputs[0],bump.inputs['Height']);link(bump.outputs[0],bs.inputs['Normal'])
    if imagefile:
        tex=nodes.new('ShaderNodeTexImage');tex.image=D.images.load(str(ASSETS/imagefile),check_existing=True)
        tex.projection='BOX';tex.projection_blend=.22;link(tc.outputs['Generated'],tex.inputs['Vector'])
        if usage=='rough':
            tex.image.colorspace_settings.name='Non-Color'
            mapper=nodes.new('ShaderNodeMapRange');link(tex.outputs[0],mapper.inputs[0]);mapper.inputs['To Min'].default_value=rough*.6;mapper.inputs['To Max'].default_value=rough*1.4;link(mapper.outputs[0],bs.inputs['Roughness'])
        elif usage=='color':
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.32;link(ramp.outputs[0],mix.inputs[1]);link(tex.outputs[0],mix.inputs[2]);link(mix.outputs[0],bs.inputs['Base Color'])
        else:
            tex.image.colorspace_settings.name='Non-Color';extra=nodes.new('ShaderNodeBump');extra.inputs['Distance'].default_value=relief*1.15;extra.inputs['Strength'].default_value=.28;link(tex.outputs[0],extra.inputs['Height']);link(bump.outputs[0],extra.inputs['Normal']);link(extra.outputs[0],bs.inputs['Normal'])
    return mat
def M(n,a,b,r=.32,s=1,d=.025,**kw):return shade(n,[a,b],r,s,d,**kw)
ivory=M('Hydrated enamel',(.49,.45,.35),(.93,.86,.71),.24,.83,.012,coat=.28,sss=.12)
dentin=M('Tubular dentin',(.37,.213,.095),(.78,.56,.30),.34,1.4,.045,sss=.11,imagefile='coral_gravel_disp_1k.jpg')
with D.libraries.load(str(WORK/'episodes/anat_wisdom/wisdom_draft34.blend')) as (a,b):b.materials=['Enamel3','Dentin']
# Carry the earlier enamel and cut-face closures into the new materials at a calibrated strength.
for target,old in [(ivory,D.materials['Enamel3']),(dentin,D.materials['Dentin'])]:
    nt=target.node_tree;bs=nt.nodes.get('Principled BSDF');grp=D.node_groups.new('Wisdom look • '+old.name,'ShaderNodeTree');grp.interface.new_socket(name='Surface',in_out='OUTPUT',socket_type='NodeSocketShader')
    # Preserve the production base BSDF parameters; shared mapped textures are authored above at mm scale.
    legacy=grp.nodes.new('ShaderNodeBsdfPrincipled');legacy_bs=next(n for n in old.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for i in legacy_bs.inputs:
        other=legacy.inputs.get(i.name)
        if other and hasattr(i,'default_value') and not i.is_linked:
            try: other.default_value=i.default_value
            except (TypeError,ValueError):pass
    gout=grp.nodes.new('NodeGroupOutput');grp.links.new(legacy.outputs[0],gout.inputs[0]);node=nt.nodes.new('ShaderNodeGroup');node.node_tree=grp
    mix=nt.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.09;nt.links.new(bs.outputs[0],mix.inputs[1]);nt.links.new(node.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes.get('Material Output').inputs[0])
pdl=M('Periodontal ligament',(.19,.069,.054),(.49,.26,.20),.31,3,.045,sss=.16)
caries=shade('Cavitated dentin',[(.009,.004,.003),(.039,.016,.006),(.17,.068,.020)],.39,2.1,.17,coat=.13)
pulp=M('Necrotic pulp',(.048,.009,.012),(.24,.047,.038),.23,2,.06,coat=.34,sss=.14)
bone=shade('Exposed cancellous bone',[(.23,.117,.061),(.44,.265,.15),(.67,.48,.30)],.46,.76,.16,imagefile='coral_gravel_disp_1k.jpg')
gum=M('Moist attached gingiva',(.32,.080,.081),(.70,.26,.23),.29,.65,.085,coat=.32,sss=.30,imagefile='clinical_attached.png',usage='color')
lining=M('Inflamed periodontal tissue',(.19,.027,.023),(.58,.115,.07),.25,1.5,.083,coat=.32,sss=.26,imagefile='leather_red_02_disp_1k.jpg')
pus=M('Apical exudate',(.54,.36,.13),(.95,.78,.42),.265,2.3,.075,coat=.40,sss=.26)
metal=M('Satin instrument steel',(.40,.45,.48),(.78,.80,.79),.235,3,.009,metal=.94,imagefile='Metal032_1K-JPG_Roughness.jpg',usage='rough')
bright=M('Polished flute edge',(.61,.67,.7),(.84,.9,.94),.15,3,.006,metal=.98)
dark=M('Instrument recess',(.025,.036,.04),(.12,.16,.18),.3,2,metal=.82)
rubber=M('Tensioned dental dam',(.024,.17,.145),(.046,.255,.201),.40,1.5,.027)
grip=M('Cobalt file handle',(.019,.074,.24),(.077,.23,.52),.29,3,.018,coat=.2)
stop=M('Silicone working stop',(.62,.32,.046),(.98,.69,.16),.38,3)
cone=M('Gutta-percha',(.61,.163,.095),(.87,.36,.21),.35,2.7,.03)
sealer=M('Thin sealer',(.73,.52,.35),(.92,.73,.53),.26,2)
paper=M('Absorbent paper',(.72,.64,.47),(.94,.89,.75),.58,8,.055)
comp=M('Access composite',(.46,.36,.22),(.74,.62,.43),.30,2.4,.026)
ceramic=M('Glazed ceramic',(.72,.64,.49),(.91,.85,.71),.20,.86,.012,coat=.48,sss=.11)
water=M('Irrigant meniscus',(.35,.58,.60),(.81,.94,.97),.105,3,.01,coat=.5)
water.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.78
water.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.333
vessel=M('Small venule',(.16,.038,.038),(.35,.095,.084),.28,2,.022,coat=.2)
def mesh(name,v,f,mat=None,smooth=True):
    me=D.meshes.new(name);me.from_pydata(v.tolist() if isinstance(v,np.ndarray) else v,[],f.tolist() if isinstance(f,np.ndarray) else f);me.update()
    ob=D.objects.new(name,me);S.collection.objects.link(ob)
    if mat:me.materials.append(mat)
    if smooth:me.polygons.foreach_set('use_smooth',np.ones(len(me.polygons),bool))
    return ob
def stored(key,name,mat):
    d=np.load(CACHE/(key+'.npz'));return mesh(name,d['v'],d['f'],mat)
def empty(name):
    o=D.objects.new(name,None);S.collection.objects.link(o);return o
def key(o,prop,frame,val):
    setattr(o,prop,val);o.keyframe_insert(data_path=prop,frame=frame)
def visible(o,ranges):
    keys={0:False}
    for a,b in ranges:keys[a]=True;keys[b+1]=False
    for f,show in sorted(keys.items()):
        for k in ['hide_render','hide_viewport']:key(o,k,f,not show)
def ball(name,loc,scale,mat,organic=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc);o=bpy.context.object;o.name=name
    if organic:
        seed=rng.uniform(0,6)
        for v in o.data.vertices:
            x,y,z=v.co;v.co*=1+organic*(.55*math.sin(x*6+2*z+seed)*math.sin(y*4-z*3)+.30*math.sin(z*7-3*x+seed)+.15*math.cos(x*13+y*7))
    o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
def tube(name,pts,radii,mat,sides=12):
    p=np.array(pts,float);tan=np.gradient(p,axis=0);tan/=np.linalg.norm(tan,axis=1)[:,None]
    ref=np.tile([0.,1.,0.],(len(p),1));ref[np.abs(tan[:,1])>.94]=[1.,0,0]
    n=np.cross(tan,ref);n/=np.linalg.norm(n,axis=1)[:,None];b=np.cross(tan,n)
    ang=np.arange(sides)*tau/sides;v=p[:,None,:]+np.broadcast_to(radii,(len(p),))[:,None,None]*(n[:,None,:]*np.cos(ang)[None,:,None]+b[:,None,:]*np.sin(ang)[None,:,None])
    f=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for j in range(len(p)-1) for i in range(sides)]
    f += [tuple(range(sides-1,-1,-1)),tuple(range((len(p)-1)*sides,len(p)*sides))]
    return mesh(name,v.reshape(-1,3),f,mat)
def parent(o,p):o.parent=p;return o
hard=[];tools=[];other=[]
body=stored('m1','M1 • patent canal section',dentin);en=stored('enamel','M1 • enamel mantle',ivory)
root=stored('ligament','M1 • periodontal ligament',pdl)
for o in [body,en]:visible(o,[(0,749),(915,929)]);hard.append(o)
jaw=stored('jaw','FJ3289 • mandibular section',bone);ging=stored('gingiva','FJ1253 • attached gingiva',gum)
hard.append(jaw);other.append(ging)
for k in ['p2','m2']:
    o=stored(k,k.upper()+' • registered neighbor',ivory);hard.append(o)
# Real marrow cavities in a thin trabecular layer over the cut.
if (CACHE/'trabecula.npz').exists():
    marrow=M('Cut marrow',(.145,.049,.031),(.39,.155,.089),.35,.93,.065,sss=.17)
    jaw.data.materials[0]=marrow;hard.append(stored('trabecula','Alveolar trabeculae',bone))
pit=stored('caries','Cavitated occlusal roof',caries);visible(pit,[(0,242),(915,929)]);hard.append(pit)
dead=stored('pulp','Infected chamber and residual canal contents',pulp);visible(dead,[(0,310),(915,929)])
core=stored('core','Bonded access core',comp);visible(core,[(700,749)])
for f,sz in [(700,.008),(710,.25),(723,.77),(739,1.)]:
    key(core,'scale',f,(1,1,sz));key(core,'location',f,(0,0,.67*(1-sz)))
stump=stored('stump','Prepared M1 section',dentin);visible(stump,[(750,867)]);hard.append(stump)
cer=stored('ceramic','Ceramic crown in section',ceramic);visible(cer,[(751,867)])
for f,h in [(751,7.8),(762,5.8),(784,2.1),(805,.17),(809,0),(867,0)]:key(cer,'location',f,(0,0,h))
for k,m in [('stump_full',ivory),('crown_full',ceramic)]:
    o=stored(k,'Restored exterior • '+k,m);visible(o,[(868,914)]);hard.append(o)
    # Unsectioned root and crown share the original DBCLS outer shell.
# Lobulated, wet apical collection with a narrow inflammatory rim.
apex=(-1.98,-.34,-11.78)
halo=ball('Inflamed tissue at mesial foramen',apex,(1.83,1.22,1.46),lining,.14)
pocket=ball('Periapical abscess • cut face',(-2.04,-1.20,-11.87),(1.39,.60,1.00),pus,.16)
for j in range(21):
    a=rng.uniform(0,tau);rr=rng.uniform(.15,.92);x=1.24*rr*math.cos(a);z=.85*rr*math.sin(a)
    w=rng.uniform(.11,.28);ball('Exudate lobule',(-2.04+x,-1.20-.53*math.sqrt(1-rr**2),-11.87+z),(w,w*.46,w*.74),pus,.20)
for j in range(8):
    a=j*tau/8+.15;pts=[]
    for k in range(6):
        u=k/5;pts.append((apex[0]+(1.32+.59*u)*math.cos(a+.12*math.sin(3*u)), -1.04+.34*u,apex[2]+(1.0+.48*u)*math.sin(a+.13*u)))
    tube('Small inflamed vessel',pts,np.linspace(.043,.012,6),vessel,7)
sys.path.insert(0,str(HERE))
from motion import bur_position
visible(pit,[(0,164),(915,929)])
for f in range(165,242):
    o=stored('cut%03d'%f,'Advancing access floor %03d'%f,caries);visible(o,[(f,f)]);hard.append(o)
damrig=empty('Dental dam assembly')
def isolated(o):visible(o,[(150,749)]);parent(o,damrig);return o
v=[];fa=[];na=109;nr=18
for j in range(nr):
    u=j/(nr-1)
    for i in range(na):
        a=-.155+(math.pi+.31)*i/(na-1)
        R=1+u*1.76
        x=-.13+R*5.97*math.cos(a);y=-.04+R*5.51*math.sin(a)
        z=1.85+1.6*u+(.18+.61*u)*math.sin(5*a+3*u)*u+.31*math.sin(12*a+2*u)*math.sin(math.pi*u)+.61*math.exp(-u*16)
        v.append((x,y,z))
        if i and j:ix=j*na+i;fa.append((ix-na-1,ix-na,ix,ix-1))
dam=isolated(mesh('Fenestrated green rubber dam • section',v,fa,rubber));solid=dam.modifiers.new('Sheet thickness','SOLIDIFY');solid.thickness=.13
lip=[v[i] for i in range(na)]
isolated(tube('Rolled dam margin',lip,.15,rubber))
isolated(tube('Dental dam wire frame',[v[(nr-1)*na+i] for i in range(na)],.21,metal))
for sign in [-1,1]:
    a=np.linspace(-.04,1.1,26);pts=[(-.13+sign*5.88*math.cos(t),5.68*math.sin(t),2.10+.22*math.cos(2*t)) for t in a]
    clamp=isolated(tube('Clamp jaw',pts,np.linspace(.19,.33,26),metal,18));tools.append(clamp)
    wing=isolated(ball('Perforated clamp wing',(-.13+sign*6.30,.94,2.10),(.88,.61,.18),metal));tools.append(wing)
    isolated(ball('Clamp forceps perforation',(-.13+sign*6.56,.93,2.26),(.24,.23,.039),dark))
a=np.linspace(.20,math.pi-.2,54)
cl=isolated(tube('Spring clamp bow',[(-.13+6.35*math.cos(q),2.22+4.7*math.sin(q),2.21+1.11*math.sin(q)) for q in a],.25,metal));tools.append(cl)
# Deflection of a seated spring under the brief forceps check.
for f,dz in [(150,0),(152,-.075),(156,0)]:key(damrig,'location',f,(0,0,dz))
probe=tube('Clamp check forceps beak',[(-.18,0,0),(-.36,-.18,1.05),(-1.45,-.46,3.21),(-3.16,-1.05,6.12)], [.10,.17,.28,.36],metal)
visible(probe,[(150,164)]);tools.append(probe)
for f,h in [(150,.60),(152,.08),(155,.10),(164,6.4)]:key(probe,'location',f,(-6.53,.93,2.23+h))
dr=empty('Contra-angle handpiece');rot=parent(empty('Carbide rotor'),dr)
for i in range(10):
    o=stored('bur_'+str(i),['Round cutting bur','Contra-angle head','Power handle','Head retainer'][i] if i<4 else 'Machined flute',bright if i==0 else dark if i>=3 else metal)
    parent(o,rot if i==0 or i>=4 else dr);visible(o,[(157,253)]);tools.append(o)
dr.scale=(.82,)*3
for f in range(157,254):
    key(dr,'location',f,bur_position(f));key(rot,'rotation_euler',f,(0,0,(f-157)*1.13))
# Damp cuttings travel only during engagement.
for i in range(42):
    f=int(rng.uniform(169,233));x,y,z=bur_position(f);x+=rng.uniform(-.52,.52);y-=.5
    r=rng.uniform(.033,.100);o=ball('Wet carious grit',(x,y,z),(r,r*.77,r*.68),dentin if i%3 else caries,.12)
    dur=rng.randint(4,10);visible(o,[(f,f+dur)])
    for ff,dx,dy,dz,sc in [(f,0,0,.6,.17),(f+dur//2,rng.uniform(-.75,.75),-.34,1.16,1),(f+dur,rng.uniform(-1.75,1.75),-.65,.82,.025)]:
        key(o,'location',ff,(x+dx,y+dy,z+dz));key(o,'scale',ff,(r*sc,r*.77*sc,r*.68*sc))
canals=np.load(CACHE/'canals.npz')
def track(i,z):
    z=np.asarray(z);return np.stack([np.interp(z,canals['z'],canals['x'][i]),np.interp(z,canals['z'],canals['y'][i]),z],axis=-1)
def guided(name,i,section,keys,mat,mode='plain',end=None):
    # z-rings follow the original canal at every insertion depth through absolute shape keys.
    # Twisted radial cross-sections model the cutting lands without a separate wire coil.
    side=12 if mode=='file' else 16
    ss,rr=map(np.array,zip(*section));theta=np.arange(side)*tau/side
    ang=theta[None,:]+ss[:,None]*(6.15 if mode=='file' else 0.)
    radii=rr[:,None]*(.78+.22*np.cos(3*theta) if mode=='file' else 1.)
    rx,ry=radii*np.cos(ang),radii*np.sin(ang)
    def verts(tip):
        z=tip+ss;cen=track(i,z)
        return np.stack([cen[:,0,None]+rx,cen[:,1,None]+ry,np.broadcast_to(z[:,None],rx.shape)],axis=-1).reshape(-1,3)
    faces=[(j*side+k,j*side+(k+1)%side,(j+1)*side+(k+1)%side,(j+1)*side+k) for j in range(len(ss)-1) for k in range(side)]
    faces+=[tuple(range(side-1,-1,-1)),tuple(range((len(ss)-1)*side,len(ss)*side))]
    lo=min(v for f,v in keys);hi=max(v for f,v in keys)
    ob=mesh(name,verts(lo),faces,mat)
    if mode=='file':
        ob.data.materials.append(bright)
        for j,p in enumerate(ob.data.polygons):
            if j%side in [0,4,8]:p.material_index=1
    if hi>lo:
        basis=ob.shape_key_add(name='Basis');ks=ob.data.shape_keys;ks.use_relative=False
        stops=np.linspace(lo,hi,1+math.ceil((hi-lo)/.55))
        for step in stops[1:]:
            k=ob.shape_key_add(name='Tip %+.2f mm'%step);k.interpolation='KEY_LINEAR';k.data.foreach_set('co',verts(step).astype('f').ravel())
        basis.interpolation='KEY_LINEAR'
        for f,vv in keys:key(ks,'eval_time',f,(vv-lo)/(hi-lo)*10*(len(stops)-1))
    visible(ob,[(keys[0][0],end if end is not None else keys[-1][0])]);return ob
def taper(length,r0,r1,res=48):
    return [(0.,.035),(.075,r0)]+[(x,r0+(r1-r0)*x/length) for x in np.linspace(.15,length,res)]
def handle(i,keys,zoff,style):
    if style=='hand':
        profile=[(zoff,.44),(zoff+.2,.99),(zoff+.65,1.13),(zoff+1.0,.96)]
        for n in range(5):profile.extend([(zoff+1.1+n*.72,.96),(zoff+1.4+n*.72,1.1)])
        profile.extend([(zoff+5.05,1.12),(zoff+5.3,.82)])
        h=guided('Ribbed hand-file grip',i,profile,keys,grip);tools.append(h)
    else:
        h=guided('Rotary latch and contra-angle',i,[(zoff,.37),(zoff+.55,.41),(zoff+.69,1.25),(zoff+1.1,1.51),(zoff+3.42,1.5),(zoff+3.75,1.03)],keys,metal);tools.append(h)
        # Angled neck tracks the accessible straight shank.
        p=tube('Rotary handpiece neck',[(0,.2,1.7),(1.5,.5,2.1),(4,1.4,3.25),(8,2.7,5.8),(15,3.7,8.0)],[.79,1.0,1.0,1.2,1.4],metal,20)
        visible(p,[(keys[0][0],keys[-1][0])]);tools.append(p)
        for f,z in keys:key(p,'location',f,track(i,z+zoff))
    marker=guided('Working-length stop',i,[(zoff-3,.72),(zoff-2.9,1.02),(zoff-2.60,1.01),(zoff-2.52,.71)],keys,stop);tools.append(marker)
keys=[(255,11.45),(266,4.6),(276,2.3),(289,1.5),(303,1.82),(311,2.03),(324,5.07),(336,9.9),(344,15.)]
broach=guided('Fine pulp broach',0,taper(15,.091,.23,62),keys,metal,'file');tools.append(broach)
handle(0,keys,15,'hand')
rem=ball('Short attached pulp remnant',(-1.74,-.96,2.38),(.44,.34,1.1),pulp,.26);visible(rem,[(303,341)])
for f,z in [(303,2.38),(311,2.5),(324,5.3),(336,10.0),(341,12.)]:
    pt=track(0,z);key(rem,'location',f,pt);key(rem,'rotation_euler',f,(0,.18*math.sin(f*.17),.13))
# Residual canal contents recede as each lumen is shaped.
endpoints=[-10.86,-10.10,-10.36]
for i,(a,b) in enumerate([(311,390),(311,445),(311,495)]):
    zz=np.linspace(endpoints[i]+.06,1.45,62)
    strand=tube('Residual canal tissue '+str(i),track(i,zz),np.linspace(.093,.24,len(zz)),pulp)
    visible(strand,[(a,b)])
for i,keys in enumerate([
 [(345,11.6),(356,2.2),(369,-5.7),(380,-9.2),(385,-8.37),(391,-10.86),(399,-5.8),(405,6.3),(409,12.0)],
 [(410,10.3),(419,.8),(429,-7.5),(435,-6.42),(447,-10.10),(454,-6.17),(462,10.5)],
 [(463,11),(469,1.9),(479,-6.88),(485,-5.96),(496,-10.36),(503,-5.4),(509,10.75)]]):
    tool=guided(['Hand K-file • mesial buccal','Rotary file • mesial lingual','Rotary file • distal'][i],i,taper(19,.118,.51,136),keys,metal,'file');tools.append(tool);handle(i,keys,19,'hand' if i==0 else 'rotary')
# Irrigation is a side-ported closed working end and an ascending film.
keys=[(510,10.4),(518,1.25),(524,-3.00),(542,-3.12),(556,-2.74),(562,.23),(568,9.6)]
needle=guided('Side-vented irrigation cannula',0,[(0,.055),(.10,.14),(.26,.17)]+[(z,.17) for z in np.linspace(.34,14,58)],keys,bright);tools.append(needle)
port=ball('Lateral outlet',(-2,-1,-2),(.069,.041,.18),dark);visible(port,[(510,568)])
hub=stored('rinse_0','Irrigation cannula hub',metal);tools.append(hub);visible(hub,[(510,568)])
neck=tube('Bent irrigation connection',[(0,0,0),(0,0,1.7),(1.3,0,3.3),(4.66,0,6.72)],[.17,.19,.24,.36],metal);tools.append(neck);visible(neck,[(510,568)])
for f,z in keys:
    v=track(0,z+.55);key(port,'location',f,(v[0],v[1]-.145,v[2]))
    top=track(0,z+14);key(neck,'location',f,top)
    hub.scale=(.55,)*3;key(hub,'location',f,(top[0]+.48,top[1],top[2]+.64))
def reflux(name,start,end,zlo,zhi):
    zz=np.linspace(zlo,zhi,28);p=track(0,zz);p[:,0]+=.22;p[:,1]-=.10
    o=tube(name,p,np.linspace(.065,.13,len(p)),water,14);visible(o,[(start,end)])
    for f,sc in [(start,.02),(min(start+10,end-4),1),(end-3,1),(end,.04)]:
        key(o,'scale',f,(1,1,sc));key(o,'location',f,(0,0,zlo*(1-sc)))
reflux('Brief wetting between passes',398,409,-1.0,2.1);reflux('Returning film beside the cannula',522,562,-2.7,2.54)
for j in range(15):
    f=525+j*2;rr=rng.uniform(.045,.12);o=ball('Reflux suspended chip',(-2,-1,0),(rr,rr,rr*1.32),dentin if j%4==0 else water)
    visible(o,[(f,f+12)])
    for step,z in [(0,-2.32),(4,-.9),(9,1.6),(12,3.12)]:v=track(0,z);key(o,'location',f+step,(v[0]+.22+.06*math.sin(j+step),v[1]-.17,z))
suct=empty('Chamber aspiration')
for i in range(2):
    o=stored('suction_'+str(i),'Surgery aspirator '+str(i),metal);parent(o,suct);visible(o,[(540,569)]);tools.append(o)
o=tube('Aspiration taper',[(0,0,0),(.08,0,.6),(.09,.13,3.7),(0,.29,7.95)],[.28,.35,.53,.71],metal);parent(o,suct);visible(o,[(540,569)]);tools.append(o)
o=ball('Aspirator opening',(0,-.18,.08),(.22,.15,.07),dark);parent(o,suct);visible(o,[(540,569)])
suct.scale=(.70,)*3
for f,h in [(540,8.8),(547,4.3),(554,3.88),(563,4.0),(569,11.)]:key(suct,'location',f,(.90,-.58,h))
drykeys=[(568,9.48),(574,-7.5),(578,-8.65),(584,10.2)]
tools.append(guided('Paper point',0,taper(17,.105,.30),drykeys,paper))
for i,(seat,zlo) in enumerate(zip([603,627,651],endpoints)):
    keys=[(seat-16,8.98),(seat-10,1.26),(seat-4,zlo+1.26),(seat,zlo),(seat+4,zlo)]
    guided('Gutta-percha point '+str(i+1),i,taper(17,.115,.36,63),keys,cone)
    zz=np.linspace(zlo,2.64,70);radius=np.interp(zz,canals['z'],canals['r'][i])
    # Sealer lies behind the fitted point and leaves a fine pale interface across the section.
    pp=track(i,zz);pp[:,1]+=.045
    film=tube('Sealer interface '+str(i),pp,radius*.92,sealer,16);visible(film,[(seat+5,867)])
    pp[:,1]-=.083
    fill=tube('Trimmed gutta-percha '+str(i),pp,radius*.82,cone,16);visible(fill,[(seat+5,867)])
# Intraoral background with soft folds well behind the focal plane.
oral=M('Defocused oral lining',(.056,.017,.022),(.23,.062,.060),.34,.23,.11,coat=.28,sss=.17,imagefile='leather_red_02_rough_1k.jpg',usage='rough')
back=ball('Buccal background fold',(0,24,-2),(73,10,20),oral,.08)
back2=ball('Posterior fold',(15,30,17),(48,7,5.6),oral,.12)
world=D.worlds.new('Operating studio');S.world=world;world.use_nodes=True;nt=world.node_tree
bg=nt.nodes['Background'];env=nt.nodes.new('ShaderNodeTexEnvironment');env.image=D.images.load(str(WORK/'anat_kit/assets/studio_small_09_2k.exr'));nt.links.new(env.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.36
def area(name,xyz,energy,size,color,target,size_y=None):
    light=D.lights.new(name,'AREA');light.energy=energy;light.shape='DISK' if size_y is None else 'RECTANGLE';light.size=size
    if size_y:light.size_y=size_y
    light.color=color;o=D.objects.new(name,light);S.collection.objects.link(o);o.location=xyz;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
keylight=area('Operatory softbox',(-12,-23,26),10000,13,(1,.925,.81),(0,0,0))
area('Cool lingual rim',(11,4,18),7200,7,(.73,.84,1),(0,0,2),15)
area('Narrow steel reflection',(-13,-7,3),1500,2.5,(.78,.92,1),(0,0,1),13)
area('Apical fill',(8,-15,-9),1850,12,(1,.78,.65),(-1,0,-8))
# Height, target, oblique angle and elevation. The last nine frames are a pre-roll of the hook.
cam=D.objects.new('Clinical macro camera',D.cameras.new('Macro optics'));S.collection.objects.link(cam);S.camera=cam
cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32;cam.data.clip_start=.1;cam.data.clip_end=450
cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=.19;cam.data.dof.aperture_blades=8
shots=[
 (0,37.8,0,1.82,-.085,.115),(44,35.8,-.10,1.40,-.058,.145),
 (45,29.5,-.20,3.6,-.052,.18),(70,27.0,-.45,3.4,-.015,.20),(98,26.2,-.68,2.4,.018,.17),
 (99,27.5,-.60,-3.8,.02,.125),(125,24.3,-1.12,-5.5,-.025,.105),(149,24.8,-1.24,-4.85,-.061,.12),
 (150,27.4,-.25,5.12,-.076,.31),(169,25.1,-.15,5.29,-.06,.285),(205,23.1,-.04,4.58,-.033,.24),(254,24.3,.03,4.1,.027,.18),
 (255,26.8,-.25,3.05,.033,.17),(300,24.2,-.43,2.5,.012,.16),(344,26.3,-.22,3.55,-.025,.18),
 (345,32.9,-.5,1.01,-.075,.14),(391,30.5,-.76,-.01,-.088,.12),(409,31.7,-.63,.36,-.062,.125),
 (410,31,-.35,.17,.05,.14),(447,29.1,-.4,-.45,.091,.13),(462,31.1,-.12,.42,.055,.13),
 (463,31.1,.40,.50,-.022,.14),(496,29.4,.8,-.17,-.053,.12),(509,30,.61,.37,-.05,.145),
 (510,25.1,-.35,2.22,-.035,.185),(545,23.2,-.43,1.49,.022,.223),(568,23.8,-.38,1.50,.043,.21),(584,26.5,-.4,1.87,.02,.18),
 (585,31.6,-.54,.83,-.048,.14),(614,30.5,-.59,.31,-.061,.12),(650,29.6,.37,.30,.035,.13),(692,31.4,.3,.75,.058,.15),
 (693,27.0,.1,2.60,.038,.19),(749,23.4,.05,4.36,.015,.23),
 (750,24.3,.03,6.08,-.046,.21),(786,22,.12,5.99,-.072,.19),(812,20.9,.06,5.58,-.055,.19),(863,21.9,.08,5.18,.005,.21),
 (864,22,.15,5.25,.035,.23),(884,23.7,.18,5.06,.11,.32),(914,25,.10,5.6,.21,.32),
 (915,38.8,.04,2.02,-.098,.110),(929,37.84,.002,1.831,-.0856,.1147)]
def pose(f):
    pos=np.array(shots,float);return [float(np.interp(f,pos[:,0],pos[:,i])) for i in range(1,6)]
def cam_pose(f):
    height,x,z,ang,el=pose(f);aim=Vector((x,-.32,z));dist=63;direction=Vector((math.sin(ang)*math.cos(el),-math.cos(ang)*math.cos(el),math.sin(el)))
    cam.location=aim+dist*direction;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    key(cam,'location',f,cam.location.copy());key(cam,'rotation_euler',f,cam.rotation_euler.copy());key(cam.data,'lens',f,32*dist/height)
    key(cam.data.dof,'focus_distance',f,dist-.35)
for f,*_ in shots:cam_pose(f)
for f,xoff in [(0,0),(120,1.0),(440,-1.2),(700,1.4),(915,.12),(929,.004)]:key(keylight,'location',f,(-12+xoff,-23,26))
# Exact per-pose track at the caption design size.
def interpolations():
    for action in D.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        if fc.data_path.endswith(('hide_render','hide_viewport')):continue
                        for kp in fc.keyframe_points:kp.interpolation='LINEAR'
interpolations()
anchors={}
for f in range(930):
    if 11<=f<=40:label,point,side='치근단 농양',(-2.03,-1.64,-11.73),'right'
    elif 58<=f<=90:label,point,side='치수강',(-.23,-.91,2.27),'left'
    elif 108<=f<=141:label,point,side='뿌리 끝',(-2.05,-1.29,-10.94),'right'
    elif 153<=f<=169:label,point,side='러버댐',(-5.91,1.2,2.42),'right'
    elif 372<=f<=396:label,point,side='근관 파일',tuple(track(0,-4.4)),'right'
    elif 532<=f<=553:label,point,side='세척액',tuple(track(0,-1.05)),'right'
    elif 665<=f<=686:label,point,side='충전된 근관',tuple(track(2,-2.9)),'left'
    elif 759<=f<810:label,point,side='다음 내원',(4.65,-.25,1.86),'left'
    else:continue
    S.frame_set(f);v=world_to_camera_view(S,cam,Vector(point));anchors[str(f)]=dict(label=label,side=side,x=round(540*v.x,2),y=round(960*(1-v.y),2))
(CACHE/'anchors.json').write_text(json.dumps(anchors,ensure_ascii=False))
for o in set(tools):o['instrument']=True
for o in set(hard):o['mineralized']=True
for f,name in [(0,'치료 전'),(45,'치수 감염'),(99,'치근단 농양'),(150,'치수 접근'),(255,'치수 제거'),(345,'근관 성형'),(510,'세척과 건조'),(585,'근관 충전'),(693,'수복'),(864,'외형과 루프')]:S.timeline_markers.new(name,frame=f)
S.frame_set(0)
# Pack the licensed material maps into the reusable Blender file.
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'rootcanal.blend'),compress=True)

# Apply the registered dental-dam fit and carry the sealed core into the later visit.
import runpy
for stage in ("fit_dam.py", "finish_section.py", "tracks.py"):
    runpy.run_path(str(HERE/stage))
