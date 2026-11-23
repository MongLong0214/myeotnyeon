"""Build the Body Inside character in a clean Blender 5.2 background process.
Run: Blender -b --factory-startup --python-exit-code 1 -P make_human.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_paths import asset
from pathlib import Path
import math
import json
import os

import bpy
import addon_utils
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
DATA = Path(os.environ.get('MPFB_ASSETS', Path.home() / 'Library/Application Support/Blender/5.2/mpfb/data'))
D = bpy.data
V = Vector
rad = math.radians
UP = V((0, 0, 1))
FRONT = V((0, -1, 0))


def active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)


def update():
    bpy.context.view_layer.update()


def material(name, color, roughness):
    mat = D.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    return mat, p


def texture(mat, path, data=False):
    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = D.images.load(str(path), check_existing=True)
    if data:
        node.image.colorspace_settings.name = 'Non-Color'
    return node


def assign(o, mat):
    o.data.materials.clear()
    o.data.materials.append(mat)
    for face in o.data.polygons:
        face.use_smooth = True


def subdiv(o, n=1):
    mod = o.modifiers.new('Tailoring and surface smoothing', 'SUBSURF')
    mod.levels = mod.render_levels = n


def mesh_coords(mesh):
    coords = np.empty(len(mesh.vertices) * 3, np.float32)
    mesh.vertices.foreach_get('co', coords)
    return coords.reshape(-1, 3)


def clean_shape(o):
    if o.data.shape_keys:
        mix = o.shape_key_add(name='Cast shape', from_mix=True)
        coords = np.empty(len(mix.data)*3, np.float32)
        mix.data.foreach_get('co', coords)
        o.shape_key_clear()
        o.data.vertices.foreach_set('co', coords)
        o.data.update()


def body_material(body):
    m, p = material('Skin | warm ochre, natural lips and stubble', (.44,.24,.16), .48)
    link = m.node_tree.links.new
    tex = texture(m, DATA/'skins/young_asian_male/young_lightskinned_male_diffuse3.png')
    link(tex.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value = .055
    p.inputs['Subsurface Scale'].default_value = .004
    p.inputs['Specular IOR Level'].default_value = .29
    n = m.node_tree.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 1050
    n.inputs['Detail'].default_value = 2
    tc=m.node_tree.nodes.new('ShaderNodeTexCoord')
    link(tc.outputs['Object'], n.inputs[0])
    bump=m.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.12
    bump.inputs['Distance'].default_value=.00016
    link(n.outputs['Fac'],bump.inputs['Height'])
    link(bump.outputs[0],p.inputs['Normal'])
    assign(body,m)


def surface(o, folder, name, tint, roughness, alpha=False, normal=False):
    m,p=material(name,tint,roughness)
    nodes=m.node_tree.nodes
    link=m.node_tree.links.new
    path=next(iter(folder.glob('*diffuse.png')),None) or next(folder.glob('*.png'))
    t=texture(m,path)
    link(t.outputs[0],p.inputs['Base Color'])
    if alpha:
        link(t.outputs['Alpha'],p.inputs['Alpha'])
        p.inputs['Specular IOR Level'].default_value=.16
    if normal and list(folder.glob('*normal.png')):
        n=texture(m,next(folder.glob('*normal.png')),True)
        nm=nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value=.72
        link(n.outputs['Color'],nm.inputs['Color'])
        link(nm.outputs[0],p.inputs['Normal'])
    assign(o,m)
    return m,p,t


def wardrobe(o, folder):
    denim,p,albedo=surface(o,folder,'Denim | indigo, worn cotton',(.06,.11,.17),.83,normal=True)
    shirt=denim.copy()
    shirt.name='T-shirt | washed eucalyptus cotton jersey'
    n=shirt.node_tree.nodes
    link=shirt.node_tree.links.new
    p=n.get('Principled BSDF')
    for l in list(p.inputs['Base Color'].links):
        shirt.node_tree.links.remove(l)
    ao=texture(shirt,next(folder.glob('*_ao.png')),True)
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.009,.023,.022,1)
    ramp.color_ramp.elements[1].color=(.055,.143,.122,1)
    link(ao.outputs['Color'],ramp.inputs[0]);link(ramp.outputs[0],p.inputs['Base Color'])
    tc=n.new('ShaderNodeTexCoord')
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=510;noise.inputs['Detail'].default_value=2.
    link(tc.outputs['UV'],noise.inputs[0])
    heather=n.new('ShaderNodeMixRGB');heather.blend_type='MULTIPLY';heather.inputs[0].default_value=.36
    link(ramp.outputs[0],heather.inputs[1]);link(noise.outputs[0],heather.inputs[2]);link(heather.outputs[0],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.00018
    link(noise.outputs[0],bump.inputs['Height']);link(n.get('Normal Map').outputs[0],bump.inputs['Normal']);link(bump.outputs[0],p.inputs['Normal'])
    p.inputs['Sheen Weight'].default_value=.11
    o.data.materials.append(shirt)
    uv=o.data.uv_layers.active.data
    for f in o.data.polygons:
        if sum(uv[i].uv.y for i in f.loop_indices)/len(f.loop_indices) > .55:
            f.material_index=1


def make_cast():
    mod='bl_ext.user_default.mpfb'
    if mod not in bpy.context.preferences.addons:
        bpy.context.preferences.addons.new().module=mod
    addon_utils.enable(mod,default_set=False)
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    import bl_ext.user_default.mpfb as mpfb
    targets=Path(mpfb.__file__).parent/'data/targets'
    d=TargetService.get_default_macro_info_dict()
    d.update(gender=.99,age=.49,muscle=.41,weight=.52,height=.55,proportions=.52)
    d['race']={'asian':.89,'caucasian':.08,'african':.03}
    body=HumanService.create_human(mask_helpers=True,detailed_helpers=True,extra_vertex_groups=False,
                                   feet_on_ground=False,scale=.1,macro_detail_dict=d)
    details={'nose/nose-hump-incr':.18,'nose/nose-width1-incr':.13,
             'chin/chin-prominent-incr':.22,'chin/chin-width-incr':.16,
             'expression/units/asian/eye-right-closure':.18,'expression/units/asian/eye-left-closure':.19,
             'expression/units/asian/mouth-compression':.09,'asym/asym-brown-1-r':.13,'asym/asym-cheek-1-l':.16,
             'eyes/l-eye-bag-incr':.21,'eyes/r-eye-bag-incr':.24,
             'eyes/l-eye-height2-decr':.12,'eyes/r-eye-height2-decr':.16}
    for target,weight in details.items():
        TargetService.load_target(body,str(targets/(target+'.target.gz')),weight=weight)
    clean_shape(body)
    rig=HumanService.add_builtin_rig(body,'game_engine',import_weights=True)
    objs=[body]
    specs=[('Outfit','clothes','male_casualsuit06','Clothes'),('Sneakers','clothes','shoes05','Clothes'),
           ('Hair underlay','hair','short01','Hair'),
           ('Eyes','eyes','high-poly','Eyes'),('Brows','eyebrows','eyebrow012','Eyebrows'),
           ('Lashes','eyelashes','eyelashes01','Eyelashes')]
    parts={}
    for name,cat,asset,kind in specs:
        folder=DATA/cat/asset
        ob=HumanService.add_mhclo_asset(str(folder/(asset+'.mhclo')),body,asset_type=kind,
                                       subdiv_levels=0,material_type='NONE')
        ob.name=name
        parts[name]=ob
        objs.append(ob)
        if name=='Outfit': wardrobe(ob,folder)
        elif name=='Sneakers': surface(ob,folder,'Canvas sneakers',(.68,.68,.66),.73,normal=True)
        elif name=='Hair underlay':
            surface(ob,folder,'Hair | textured roots',(.022,.013,.010),.52,alpha=True)
        elif name=='Eyes':
            mat,p=material('Eyes | umber iris and moist cornea',(.36,.29,.25),.22)
            tx=texture(mat,DATA/'eyes/materials/brown_eye.png')
            mat.node_tree.links.new(tx.outputs[0],p.inputs['Base Color'])
            mat.node_tree.links.new(tx.outputs['Alpha'],p.inputs['Alpha'])
            p.inputs['Coat Weight'].default_value=.2
            assign(ob,mat)
        else:
            surface(ob,folder,name+' | individual dark hairs',(.04,.025,.02),.59,alpha=True)
    for ob in objs: clean_shape(ob)
    # Keep the fitted rig in the same coordinate system as the skin and clothing.
    foot_ids=[v.index for v in body.data.vertices if any(g.group==body.vertex_groups['body'].index for g in v.groups)]
    lift=-min(body.data.vertices[i].co.z for i in foot_ids)
    floor=Matrix.Translation((0,0,lift))
    rig.data.transform(floor)
    for ob in objs:
        ob.data.transform(floor)
    update()
    body.name='Skin'; rig.name='HumanRig'
    body_material(body)
    # Preserve the original MPFB vertex identity for independent surface measurements.
    idx=body.data.attributes.new('hm08_index','INT','POINT')
    idx.data.foreach_set('value',np.arange(len(body.data.vertices),dtype=np.int32))
    for ob in objs:
        active(ob)
        for modifier in list(ob.modifiers):
            if modifier.type=='MASK':
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            elif modifier.type=='ARMATURE':
                modifier.use_deform_preserve_volume=True
        subdiv(ob)
    return rig,body,parts


def link_obj(name,data):
    o=D.objects.new(name,data)
    bpy.context.scene.collection.objects.link(o)
    return o


def camera_and_light():
    sc=bpy.context.scene
    sc.render.engine='CYCLES'
    sc.cycles.samples=32
    sc.cycles.use_denoising=True
    sc.cycles.denoiser='OPENIMAGEDENOISE'
    sc.cycles.denoising_use_gpu=False
    sc.cycles.use_adaptive_sampling=False
    sc.cycles.max_bounces=6
    sc.cycles.transparent_max_bounces=12
    sc.cycles.sample_clamp_indirect=3
    sc.render.resolution_x,sc.render.resolution_y=1080,880
    sc.render.resolution_percentage=100;sc.render.fps=30
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
    sc.view_settings.view_transform='AgX'
    world=D.worlds.new('Soft surround');sc.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.32,.39,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.13
    target=V((0,-.165,1.335))
    cam=link_obj('Camera | profile',D.cameras.new('Portrait 85 mm'))
    cam.location=target+V((-2.65,-.90,.13))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=94;sc.camera=cam
    def area(name,position,target,power,color,size,size_y):
        d=D.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='RECTANGLE'
        d.size=size;d.size_y=size_y
        o=link_obj(name,d);o.location=position
        o.rotation_euler=(V(target)-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key | warm window',(-.76,-1.63,2.55),(0,-.08,1.42),103,(1,.86,.73),.92,1.4)
    area('Rim | cool strip',(.56,.96,2.20),(0,0,1.42),63,(.66,.81,1),.62,1.35)
    area('Fill | book light',(-.9,.40,1.56),(0,0,1.40),10,(.76,.84,1),1.3,1.5)
    area('Eye light',(.20,-1.65,1.96),(0,-.08,1.54),14,(1,.94,.84),.48,.62)
    # A camera-only, matte studio gradient. Fixed in camera space for both shots.
    bpy.ops.mesh.primitive_plane_add(size=18)
    bg=bpy.context.object;bg.name='Backdrop | midnight slate'
    bg.location=target+(target-cam.location).normalized()*2.9
    bg.rotation_euler=cam.rotation_euler
    bg.visible_shadow=bg.visible_diffuse=bg.visible_glossy=bg.visible_transmission=False
    m,p=material('Backdrop | graded slate',(.02,.02,.02),1)
    nt=m.node_tree;nt.nodes.remove(p)
    uv=nt.nodes.new('ShaderNodeTexCoord')
    dist=nt.nodes.new('ShaderNodeVectorMath');dist.operation='DISTANCE'
    nt.links.new(uv.outputs['Window'],dist.inputs[0]);dist.inputs[1].default_value=(.30,.62,0)
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.035,.054,.062,1)
    ramp.color_ramp.elements[1].position=.87;ramp.color_ramp.elements[1].color=(.006,.011,.017,1)
    em=nt.nodes.new('ShaderNodeEmission')
    nt.links.new(dist.outputs['Value'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],em.inputs[0])
    nt.links.new(em.outputs[0],nt.nodes['Material Output'].inputs[0]);bg.data.materials.append(m)



def screen_image():
    """A compact, unbranded messenger screen drawn in linear RGB."""
    w,h=300,630
    yy,xx=np.mgrid[0:h,0:w]
    image=np.ones((h,w,4),np.float32)
    image[:,:,:3]=np.array([.016,.042,.054])+(yy/h)[:,:,None]*np.array([.014,.022,.019])
    def box(x,y,ww,hh,r,col):
        dx=np.maximum(np.maximum(x+r-xx,xx-(x+ww-r)),0)
        dy=np.maximum(np.maximum(y+r-yy,yy-(y+hh-r)),0)
        mask=(dx*dx+dy*dy<=r*r)&(xx>=x)&(xx<=x+ww)&(yy>=y)&(yy<=y+hh)
        image[mask,:3]=col
    white=(.73,.82,.83);gray=(.27,.41,.43);teal=(.12,.46,.37);paper=(.18,.28,.31)
    digits={'0':['111','101','101','101','111'],'9':['111','101','111','001','111'],
            '4':['101','101','111','001','001'],'1':['010','110','010','010','111'],
            ':':['0','1','0','1','0'],'J':['001','001','001','101','111'],
            'I':['111','010','010','010','111'],'N':['1001','1101','1011','1001','1001']}
    def label(x,y,text,unit,color):
        for c in text:
            pattern=digits[c]
            for row,line in enumerate(pattern):
                for j,z in enumerate(line):
                    if z=='1':box(x+j*unit,y+row*unit,unit,unit,0,color)
            x+=(len(pattern[0])+1)*unit
    label(22,18,'09:41',2,white)
    for i in range(4):box(229+i*5,25-i*2,3,4+i*2,1,white)
    box(259,17,19,9,2,white);box(262,19,12,5,1,gray)
    box(20,50,32,32,16,teal);box(31,57,10,10,5,white);box(26,68,20,9,4,white)
    label(64,53,'JIN',3,white);box(65,76,42,3,1,gray)
    box(15,96,270,1,0,gray)
    for x,y,ww,hh,col,lines in [(19,127,157,57,paper,(102,71)),(81,211,198,65,teal,(133,94)),
                                (113,287,166,45,teal,(112,)),(20,360,150,57,paper,(87,108))]:
        box(x,y,ww,hh,13,col)
        for j,length in enumerate(lines):
            line_y=y+17+j*14
            for offset in range(0,length,14):
                box(x+14+offset,line_y,min(11,length-offset),4,1,white)
    box(18,454,261,34,17,paper);box(37,468,75,3,1,gray);box(249,460,21,21,10,teal)
    for row,count in enumerate((10,9,7)):
        for i in range(count):
            x=(w-(count*25+(count-1)*3))//2+i*28
            box(x,505+row*25,25,20,4,paper);box(x+10,511+row*25,4,5,1,white)
    box(92,583,116,18,4,paper);box(110,615,80,4,2,white)
    out=D.images.new('Handset | original messenger artwork',width=w,height=h,alpha=True)
    out.pixels.foreach_set(image[::-1].copy().ravel());out.pack()
    return out


def complexion(body):
    pts=mesh_coords(body.data);x,y,z=pts.T;ax=np.abs(x)
    def patch(cx,cy,cz,rx,ry,rz):
        return np.exp(-((ax-cx)/rx)**2-((y-cy)/ry)**2-((z-cz)/rz)**2)
    ears=patch(.070,-.047,1.554,.013,.021,.036)
    cheek=patch(.050,-.117,1.536,.027,.027,.026)
    jaw=patch(.039,-.093,1.488,.038,.048,.031)+.65*patch(0,-.127,1.470,.027,.031,.021)
    nose=patch(0,-.148,1.536,.017,.029,.015)
    col=np.ones((len(pts),4),np.float32);col[:,:3]=[.965,.875,.805]
    col[:,0]+=cheek*.060+ears*.12+nose*.05-jaw*.13
    col[:,1]-=cheek*.029+ears*.060+nose*.035+jaw*.075
    col[:,2]-=ears*.027+jaw*.028
    a=body.data.color_attributes.new('Complexion','FLOAT_COLOR','POINT');a.data.foreach_set('color',col.ravel())
    m=body.data.materials[0];nt=m.node_tree;n=nt.nodes;link=nt.links.new
    p=n.get('Principled BSDF');t=p.inputs['Base Color'].links[0].from_node
    tint=n.new('ShaderNodeVertexColor');tint.layer_name='Complexion'
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    link(t.outputs[0],mix.inputs[1]);link(tint.outputs[0],mix.inputs[2]);link(mix.outputs[0],p.inputs['Base Color'])


def eyelids(rig,body,lashes):
    import gzip
    import bl_ext.user_default.mpfb as mpfb
    root=Path(mpfb.__file__).parent/'data/targets/expression/units/asian'
    delta=np.zeros((20000,3),np.float32)
    for side in ('left','right'):
        with gzip.open(root/('eye-'+side+'-closure.target.gz'),'rt') as f:
            for line in f:
                if line[:1].isdigit():
                    i,x,y,z=line.split()
                    delta[int(i)]=np.array([float(x),-float(z),float(y)])*.081
    ids=np.array([e.value for e in body.data.attributes['hm08_index'].data])
    weights=[]
    data=(DATA/'eyelashes/eyelashes01/eyelashes01.mhclo').read_text().split('verts 0\n')[1]
    for line in data.splitlines():
        values=line.split()
        if not values:continue
        if not values[0].isdigit():break
        if len(values)==1:weights.append(delta[int(values[0])])
        elif len(values)==9:weights.append(np.asarray(values[3:6],float)@delta[np.asarray(values[:3],int)])
    rig.pose.bones['head']['blink']=0.
    for ob,offsets in [(body,delta[ids]),(lashes,np.asarray(weights))]:
        if len(offsets)!=len(ob.data.vertices):raise ValueError('Lid correspondence: '+ob.name)
        ob.shape_key_add(name='Basis')
        k=ob.shape_key_add(name='Blink')
        k.data.foreach_set('co',(mesh_coords(ob.data)+offsets).astype(np.float32).ravel())
        dr=k.driver_add('value').driver;dr.type='AVERAGE'
        var=dr.variables.new();var.targets[0].id=rig;var.targets[0].data_path='pose.bones["head"]["blink"]'


def organize(rig,phone):
    scene=bpy.context.scene
    actor=D.collections.new('Human | character');studio=D.collections.new('Studio | profile proofs')
    scene.collection.children.link(actor);scene.collection.children.link(studio)
    root=link_obj('HumanRoot',None);root.empty_display_size=.08;rig.parent=root;phone.parent=root
    for obj in list(scene.objects):
        target=studio if obj.type in ('CAMERA','LIGHT') or obj.name.startswith('Backdrop') else actor
        for c in list(obj.users_collection):c.objects.unlink(obj)
        target.objects.link(obj)
    rig.show_in_front=False
    for ob in scene.objects:ob.select_set(False)
    active(rig)
    for screen in D.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.overlay.show_overlays=False
                area.spaces.active.shading.color_type='MATERIAL'
    for a in list(D.actions):
        if a.name.startswith('mixamo') or a.name.startswith('Armature|'):
            D.actions.remove(a)
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def init():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene.render.fps=30
    bpy.context.scene.unit_settings.system='METRIC'



def attach_to_bone(o, rig, name):
    keep=o.matrix_world.copy()
    o.parent=rig;o.parent_type='BONE';o.parent_bone=name
    b=rig.data.bones[name]
    o.matrix_parent_inverse=(rig.matrix_world@b.matrix_local@Matrix.Translation((0,b.length,0))).inverted()
    o.matrix_basis=keep



def hair_fibers(rig,underlay):
    """Trace small locks along the strand direction painted into the CC0 hair cards."""
    rng=np.random.default_rng(21371)
    ev=underlay.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.data;mesh.calc_loop_triangles()
    co=mesh_coords(mesh);uv=np.asarray([p.uv[:] for p in mesh.uv_layers.active.data])
    tri=np.asarray([t.vertices[:] for t in mesh.loop_triangles])
    tid=np.asarray([t.loops[:] for t in mesh.loop_triangles])
    pt=co[tri];uvt=uv[tid]
    cross=np.cross(pt[:,1]-pt[:,0],pt[:,2]-pt[:,0])
    area=np.linalg.norm(cross,axis=1);norm=cross/np.maximum(area[:,None],1e-10)
    tree=BVHTree.FromPolygons(co,tri,all_triangles=True)
    tex=next(n.image for n in underlay.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
    w,h=tex.size
    pix=np.empty(w*h*4,np.float32);tex.pixels.foreach_get(pix)
    pix=pix.reshape(h,w,4)[::4,::4,:]
    gray=np.sqrt(np.maximum(.00001,pix[:,:,:3].mean(2)))
    gy,gx=np.gradient(gray)
    def blur(a):
        return sum(np.roll(np.roll(a,i,0),j,1) for i in range(-3,4) for j in range(-3,4))/49
    theta=.5*np.arctan2(2*blur(gx*gy),blur(gx*gx)-blur(gy*gy))+math.pi/2
    ab=uvt[:,1]-uvt[:,0];ac=uvt[:,2]-uvt[:,0]
    det=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]
    det[np.abs(det)<1e-10]=1
    du=((pt[:,1]-pt[:,0])*ac[:,1,None]-(pt[:,2]-pt[:,0])*ab[:,1,None])/det[:,None]
    dv=((pt[:,2]-pt[:,0])*ab[:,0,None]-(pt[:,1]-pt[:,0])*ac[:,0,None])/det[:,None]
    groups=rng.choice(len(tri),6300,p=area/area.sum())
    strands=[];radii=[]
    for f in groups:
        u,v=rng.random(2)
        if u+v>1:u,v=1-u,1-v
        bary=np.array([1-u-v,u,v])
        loc=V(bary@pt[f]); tuv=bary@uvt[f]
        x,y=(tuv*np.array([pix.shape[1],pix.shape[0]])).astype(int)%[pix.shape[1],pix.shape[0]]
        normal=V(norm[f])
        radial=(loc-V((0,-.043,1.596))).normalized()
        if normal.dot(radial)<.04 or pix[y,x,3]<.63:continue
        a=theta[y,x]
        direct=V(du[f]*math.cos(a)+dv[f]*math.sin(a)).normalized()
        comb=V((.6 if loc.x>-.028 else -.65,.42+.6*radial.y,-.70))
        if direct.dot(comb)<0:direct.negate()
        direct=(.86*direct+.14*comb).normalized()
        direction=(direct-normal*direct.dot(normal)).normalized()
        transverse=normal.cross(direction).normalized()
        length=rng.uniform(.009,.025)*(1+.26*radial.z)
        height=rng.uniform(.0007,.0031)
        if rng.random()<.028:height*=1.55;length*=1.10
        guide=[]
        for k in range(9):
            t=k/8
            guess=loc+direction*(length*t)+transverse*(math.sin(t*math.pi)*length*.045)-UP*(.0025*t*t)
            hit,hn,_,distance=tree.find_nearest(guess)
            if hit is None or distance>.016: hit=guess;hn=normal
            if hn.dot(normal)<0:hn.negate()
            blend=min(t*2,1)*.77
            guide.append((guess.lerp(hit,blend)+normal.lerp(hn,.32)*(.0003+height*math.sin(math.pi*t)**.7),t))
        for _ in range(5):
            offset=rng.uniform(-.0019,.0019)
            lift=rng.uniform(-.0003,.0004)
            width=rng.uniform(.000038,.000071)
            strands.append([tuple(p+transverse*offset*(1-.64*t)+normal*lift) for p,t in guide])
            radii.extend(width*(1-.9*t**1.4) for _,t in guide)
    hair=D.hair_curves.new('Tapered, combed fibers')
    hair.add_curves([9]*len(strands))
    hair.attributes['position'].data.foreach_set('vector',np.array(strands,np.float32).ravel())
    hair.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.array(radii,np.float32))
    obj=link_obj('Hair | individual locks and flyaways',hair)
    m,p=material('Hair fiber | near black eumelanin',(.015,.009,.007),.44)
    nt=m.node_tree;nt.nodes.remove(p);h=nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    h.parametrization='MELANIN';h.inputs['Melanin'].default_value=.87
    h.inputs['Melanin Redness'].default_value=.18;h.inputs['Roughness'].default_value=.40
    nt.links.new(h.outputs[0],nt.nodes['Material Output'].inputs[0]);hair.materials.append(m)
    attach_to_bone(obj,rig,'head')
    return obj


def edge_bands(rig,outfit):
    import bmesh
    bm=bmesh.new();bm.from_mesh(outfit.data);bm.normal_update()
    edges={e for e in bm.edges if e.is_boundary}
    collar,p=material('Neckband | pigment-dyed rib knit',(.035,.095,.086),.83)
    seam,p=material('Hems | double needle cotton',(.040,.108,.095),.86)
    def make_band(loop,name,width,mat):
        verts=[];weights=[];faces=[]
        for j,v in enumerate(loop):
            inward=[e.other_vert(v) for e in v.link_edges if not e.is_boundary]
            if not inward:continue
            inside=min(inward,key=lambda w:(w.co-v.co).length)
            tangent=(loop[(j+1)%len(loop)].co-loop[j-1].co).normalized()
            normal=v.normal.normalized()
            toward=normal.cross(tangent).normalized()
            if toward.dot(inside.co-v.co)<0:toward.negate()
            for t,h in [(-.09,.00025),(.01,.00145),(.14,.0018),(.85,.0018),(.97,.0013),(1.05,.00025)]:
                pos=v.co+toward*(t*width)+normal*h
                verts.append(tuple(pos));weights.append((v.index,inside.index,min(1,max(0,t)*width/max(.001,(inside.co-v.co).length))))
        if len(verts)!=len(loop)*6:return
        for j in range(len(loop)):
            for k in range(5):
                a=j*6+k;b=((j+1)%len(loop))*6+k;faces.append((a,b,b+1,a+1))
        mesh=D.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
        ob=link_obj(name,mesh);ob.parent=rig;assign(ob,mat)
        for g in outfit.vertex_groups:ob.vertex_groups.new(name=g.name)
        for i,(a,b,t) in enumerate(weights):
            w={}
            for vi,factor in [(a,1-t),(b,t)]:
                for g in outfit.data.vertices[vi].groups:w[g.group]=w.get(g.group,0)+factor*g.weight
            for group,val in w.items():
                if val>.00001:ob.vertex_groups[group].add([i],val,'REPLACE')
        arm=ob.modifiers.new('Body motion','ARMATURE');arm.object=rig;arm.use_deform_preserve_volume=True
        subdiv(ob,2)
        wrap=ob.modifiers.new('Stay on the jersey surface','SHRINKWRAP');wrap.target=outfit
        wrap.wrap_method='NEAREST_SURFACEPOINT';wrap.offset=.00065
    while edges:
        e=min(edges,key=lambda edge:edge.index);edges.remove(e);first,cur=e.verts;loop=[first]
        while cur!=first:
            loop.append(cur);next_edge=next((ne for ne in cur.link_edges if ne in edges),None)
            if not next_edge:break
            edges.remove(next_edge);cur=next_edge.other_vert(cur)
        z=sum(v.co.z for v in loop)/len(loop)
        if z>1.40:make_band(loop,'Crew neck | bound rib',.014,collar)
        elif 1.18<z<1.27:make_band(loop,'Sleeve | turned hem',.009,seam)
        elif .84<z<.89:make_band(loop,'Waist | turned hem',.010,seam)
    bm.free()


def ocular_material(rig,eyes):
    coords=mesh_coords(eyes.data)
    radial=np.zeros(coords.shape,np.float32)
    centers={}
    for idx,(key,sign) in enumerate([('r',-1),('l',1)]):
        subset=coords[:,0]*sign>0
        pts=coords[subset]
        center=(pts.min(0)+pts.max(0))*.5
        center[1]=-.1245
        centers[key]=V(center)
        directions=pts-center
        radial[subset]=directions/np.linalg.norm(directions,axis=1)[:,None]
        m,p=material('Eye '+key+' | textured limbus, iris and sclera',(.5,.38,.31),.19)
        if idx==0:eyes.data.materials.clear()
        eyes.data.materials.append(m)
        nt=m.node_tree;n=nt.nodes;link=nt.links.new
        attr=n.new('ShaderNodeAttribute');attr.attribute_name='globe_direction'
        xrot=n.new('ShaderNodeVectorRotate');xrot.rotation_type='X_AXIS'
        zrot=n.new('ShaderNodeVectorRotate');zrot.rotation_type='Z_AXIS'
        link(attr.outputs['Vector'],zrot.inputs['Vector']);link(zrot.outputs[0],xrot.inputs['Vector'])
        for axis,node in [('pitch',xrot),('yaw',zrot)]:
            prop='gaze_'+axis+'_'+key
            rig.pose.bones['head'][prop]=0.
            driver=node.inputs['Angle'].driver_add('default_value').driver
            driver.type='AVERAGE';var=driver.variables.new();var.name='angle'
            var.targets[0].id=rig;var.targets[0].data_path='pose.bones["head"]["'+prop+'"]'
        split=n.new('ShaderNodeSeparateXYZ');link(xrot.outputs[0],split.inputs[0])
        comb=n.new('ShaderNodeCombineXYZ');link(split.outputs['X'],comb.inputs[0]);link(split.outputs['Z'],comb.inputs[1])
        scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=.295
        shift=n.new('ShaderNodeVectorMath');shift.operation='ADD';shift.inputs[1].default_value=(.706,.705,0)
        link(comb.outputs[0],scale.inputs[0]);link(scale.outputs[0],shift.inputs[0])
        t=texture(m,DATA/'eyes/materials/brown_eye.png');link(shift.outputs[0],t.inputs['Vector']);link(t.outputs[0],p.inputs['Base Color'])
        p.inputs['Coat Weight'].default_value=.33;p.inputs['Coat Roughness'].default_value=.14
    a=eyes.data.attributes.new('globe_direction','FLOAT_VECTOR','POINT')
    a.data.foreach_set('vector',radial.ravel())
    for poly in eyes.data.polygons:poly.material_index=int(poly.center.x>0)
    return centers



def spectacles(rig):
    metal,p=material('Spectacles | brushed pewter',(.052,.061,.060),.26)
    p.inputs['Metallic'].default_value=.81
    tip,p=material('Spectacles | brown acetate',(.041,.023,.016),.33)
    lens,p=material('Spectacles | clear antireflective lenses',(.79,.86,.85),.07)
    # An optically thin glass surface; reflections are subdued by the lens coating.
    nt=lens.node_tree;nt.nodes.remove(p)
    transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
    glossy=nt.nodes.new('ShaderNodeBsdfGlossy');glossy.inputs['Roughness'].default_value=.055
    mix=nt.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.025
    nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(glossy.outputs[0],mix.inputs[2])
    nt.links.new(mix.outputs[0],nt.nodes['Material Output'].inputs[0])
    def wire(name,pts,r,mat,loop=False):
        c=D.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=3
        spl=c.splines.new('BEZIER');spl.bezier_points.add(len(pts)-1)
        for b,pt in zip(spl.bezier_points,pts):
            b.co=pt;b.handle_left_type=b.handle_right_type='AUTO'
        spl.use_cyclic_u=loop;o=link_obj(name,c);c.materials.append(mat);attach_to_bone(o,rig,'head')
    for sign in [-1,1]:
        outline=[]
        for a in np.linspace(0,2*math.pi,40,endpoint=False):
            x=math.copysign(abs(math.cos(a))**.86,math.cos(a));z=math.copysign(abs(math.sin(a))**.91,math.sin(a))
            width=.0243*(1+.065*z)
            xx=.0325+width*x; zz=1.5727+.0184*z+.0017*x
            yy=-.1577+.010*(xx/.060)**2-.14*(zz-1.573)
            outline.append((sign*xx,yy,zz))
        wire('Spectacles | lens rim',outline,.00082,metal,True)
        mesh=D.meshes.new('Clear lens');mesh.from_pydata(outline,[],[tuple(range(len(outline)))]);mesh.update()
        o=link_obj('Spectacles | lens',mesh);mesh.materials.append(lens);attach_to_bone(o,rig,'head')
        wire('Spectacles | temple',[(sign*.057,-.149,1.577),(sign*.062,-.141,1.577),
             (sign*.0695,-.091,1.576),(sign*.074,-.053,1.576),(sign*.078,-.042,1.575)],.00092,metal)
        wire('Spectacles | temple tip',[(sign*.074,-.059,1.576),(sign*.078,-.044,1.576),
             (sign*.080,-.035,1.574),(sign*.078,-.030,1.565)],.00158,tip)
    wire('Spectacles | bridge',[(-.010,-.157,1.579),(-.006,-.159,1.582),(0,-.161,1.583),
                                (.006,-.159,1.582),(.010,-.157,1.579)],.00090,metal)


def cotton_drape(outfit):
    """A few millimetres of ease and compression folds in the continuous tee surface."""
    active(outfit)
    sm=outfit.modifiers.new('Cloth fold resolution','SUBSURF');sm.levels=2
    bpy.ops.object.modifier_move_to_index(modifier=sm.name,index=0)
    bpy.ops.object.modifier_apply(modifier=sm.name)
    coords=mesh_coords(outfit.data)
    normals=np.empty(coords.size,np.float32);outfit.data.vertices.foreach_get('normal',normals)
    x,y,z=coords.T
    ax=np.abs(x);side=np.clip((ax-.045)/.115,0,1)
    def fold(line,width):
        return np.exp(-((z-line)/width)**2)-.46*np.exp(-((z-line-width*1.5)/(width*1.2))**2)
    phase=np.where(x<0,.008,-.008)
    amp=.0030*fold(.921+.29*ax+y+phase,.012)
    amp+=.0041*fold(.994+.47*ax+.56*y-phase,.017)
    amp+=.0035*fold(1.08+.35*ax-.80*y+phase,.021)
    amp+=side*.0041*fold(1.165+.62*ax+.78*y,.015)
    amp+=np.clip((ax-.195)/.060,0,1)*.0032*fold(1.41-.72*ax-.65*y,.009)
    amp*=np.clip((z-.876)/.025,0,1)*np.clip((1.41-z)/.045,0,1)
    coords+=normals.reshape(-1,3)*amp[:,None]
    outfit.data.vertices.foreach_set('co',coords.ravel())
    outfit.data.update()


def smooth(x):
    x=max(0.,min(1.,x))
    return x*x*(3-2*x)


def frame3(axis, secondary):
    y=V(axis).normalized()
    x=(V(secondary)-y*y.dot(V(secondary))).normalized()
    return Matrix((x,y,x.cross(y))).transposed().to_quaternion()


def contact_phone():
    root=link_obj('Phone | animated contact frame',None)
    root.empty_display_size=.015
    def rounded(name,w,h,d,r,z,mat,x=0,y=0):
        # Extruded roundrect with a separately bevelled rim.
        verts=[]
        for height in (z-d/2,z+d/2):
            for k in range(4):
                a0=k*math.pi/2
                cx=(w/2-r)*(1 if k in (0,3) else -1)
                cy=(h/2-r)*(1 if k in (0,1) else -1)
                for j in range(8):
                    a=a0+j*math.pi/14
                    verts.append((x+cx+r*math.cos(a),y+cy+r*math.sin(a),height))
        N=len(verts)//2
        faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
        mesh=D.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=link_obj(name,mesh);o.parent=root
        mesh.materials.append(mat)
        if d>.001:
            bevel=o.modifiers.new('Edge catchlight','BEVEL');bevel.width=min(.0016,d*.25);bevel.segments=3
            o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
        return o
    case,p=material('Phone | midnight graphite satin',(.034,.039,.043),.31)
    p.inputs['Metallic'].default_value=.67
    rounded('Phone | enclosure',.073,.150,.0089,.010,0,case)
    glass,p=material('Phone | edge glass',(.004,.007,.009),.18)
    rounded('Phone | glass',.0707,.147,.0007,.009,.0047,glass)
    def emissive(name,col,power):
        m,p=material(name,col,.31);p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=power
        return m
    display=emissive('Display | night mode',(.027,.104,.145),.75)
    nt=display.node_tree;tx=nt.nodes.new('ShaderNodeTexImage');tx.image=screen_image()
    coords=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coords.outputs['Generated'],tx.inputs['Vector'])
    shader=nt.nodes.get('Principled BSDF')
    nt.links.new(tx.outputs['Color'],shader.inputs['Emission Color']);nt.links.new(tx.outputs['Color'],shader.inputs['Base Color'])
    shader.inputs['Emission Strength'].default_value=.96
    rounded('Phone | illuminated display',.067,.142,.00012,.008,.00514,display)
    rounded('Camera | rear island',.026,.034,.0026,.006,-.0054,case,.018,.048)
    for y in (.042,.055):
        rounded('Camera | lens',.010,.010,.001,.0049,-.0070,glass,.018,y)
    return root


def motion_samples():
    sc=bpy.context.scene
    samples={}
    for name,clip,frames in [('text','Texting While Standing',range(95,271)),('look','Looking Down',range(1,177))]:
        before=set(D.objects)
        bpy.ops.import_scene.fbx(filepath=asset('assets/mocap/'+clip+'.fbx'))
        imported=set(D.objects)-before
        src=next(o for o in imported if o.type=='ARMATURE')
        names=('Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','RightShoulder','LeftArm','RightArm',
               'LeftForeArm','RightForeArm','LeftHand','RightHand','LeftUpLeg','RightUpLeg','LeftLeg','RightLeg',
               'LeftFoot','RightFoot','LeftToeBase','RightToeBase','RightHandThumb3','LeftHandThumb3')
        rows=[]
        for f in frames:
            sc.frame_set(f)
            row={}
            for n in names:
                bone=src.pose.bones['mixamorig:'+n]
                mat=src.matrix_world@bone.matrix
                rest=src.matrix_world@bone.bone.matrix_local
                row[n]=(mat.translation.copy(),mat.to_quaternion()@rest.to_quaternion().inverted())
            rows.append(row)
        samples[name]=rows
        for o in imported:D.objects.remove(o,do_unlink=True)
    return samples


def nearest_vertex(ob, target):
    target=V(target)
    return min(ob.data.vertices,key=lambda v:(v.co-target).length_squared).index


def bake(rig,body,parts,phone,eyes):
    sources=motion_samples()
    rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    bones=rig.data.bones
    ear_i=nearest_vertex(body,(-.067,-.052,1.555))
    shoulder_i=nearest_vertex(parts['Outfit'],(-.179,-.010,1.381))
    ear=body.data.vertices[ear_i].co.copy()
    shoulder=parts['Outfit'].data.vertices[shoulder_i].co.copy()
    def bonepoint(n):return rest[n].translation
    armatures=[rig,phone]
    for ob in armatures:ob.animation_data_create()
    N=174;sc=bpy.context.scene
    action_names=('Opening | screen drift','Payoff | return to neutral')
    starts=(1,109);ends=(108,N)
    actions=[[],[]]
    oldq={}
    for i in range(N):
        f=i+1
        action_frame=f if f<=108 else f-48
        if f in starts:
            for j,ob in enumerate(armatures):
                act=D.actions.new(action_names[int(f==109)]+('' if j==0 else ' | handset'))
                ob.animation_data.action=act;act.use_fake_user=True
                actions[j].append(act)
        tx=sources['text'][i];ld=sources['look'][i]
        def P(n):return tx[n][0]
        def Q(n):return tx[n][1]
        initial=sources['text'][0]
        s=smooth((f-2)/56) if f<=108 else 1-smooth((f-133)/30)
        # A little more extension at the skull on the severe shot, with the gaze held down.
        severity=s*.76 if f<=108 else s
        target_lead=(.014+.084*s) if f<=108 else .123*s+.0035*(1-s)
        pose={}
        def predicted(n):
            par=bones[n].parent
            return pose[par.name]@rest[par.name].inverted()@rest[n] if par else rest[n].copy()
        def put(n,rot=None,pos=None):
            m=predicted(n)
            if rot is not None:m=Matrix.Translation(m.translation)@rot.to_matrix().to_4x4()
            if pos is not None:m.translation=pos
            pose[n]=m
        def global_delta(n,q):
            put(n,q@rest[n].to_quaternion())
        def pitch(d):return Quaternion((1,0,0),rad(d))
        def rig_aim(n,d):
            initial_dir=bones[n].tail_local-bonepoint(n)
            global_delta(n,initial_dir.rotation_difference(d))
        put('Root')
        sway=(P('Hips')-initial['Hips'][0])*.25
        put('pelvis',Quaternion().slerp(Q('Hips'),.16)@rest['pelvis'].to_quaternion(),bonepoint('pelvis')+sway)
        for n,src,bend in [('spine_01','Spine',4),('spine_02','Spine1',12),('spine_03','Spine2',22)]:
            global_delta(n,pitch(bend*severity)@Quaternion().slerp(Q(src),.19))
        for suffix,side in [('r',1),('l',-1)]:
            n='clavicle_'+suffix
            inherit=pose['spine_03'].to_quaternion()@rest['spine_03'].to_quaternion().inverted()
            roll=Quaternion(UP,rad(side*6.2*severity))
            global_delta(n,roll@inherit)
        global_delta('neck_01',pitch(-10+51*severity)@Quaternion().slerp(ld['Neck'][1],.11))
        global_delta('head',pitch(11+14*severity if f<=108 else 1+14*severity)@Quaternion().slerp(ld['Head'][1],.22))
        def moved(n,p):return pose[n]@rest[n].inverted()@p
        # The acromial fabric vertex has mixed weights. Match its actual skinned rest point.
        shoulder_now=moved('clavicle_r',shoulder)
        delta_y=(shoulder_now.y-target_lead)-moved('head',ear).y
        pose['neck_01'].translation+=V((0,delta_y*.57,-max(0,-delta_y)*.11))
        pose['head'].translation+=V((0,delta_y,-max(0,-delta_y)*.18))
        # Phone path retains both captured wrist trajectories. Place hands using a solved contact pose.
        wrist_delta=((P('LeftHand')+P('RightHand'))-(initial['LeftHand'][0]+initial['RightHand'][0]))*.23
        phone_center=V((.022,-.368-.095*severity,1.20+.037*severity))+wrist_delta
        phone_center+=V((0,0,.026*(1-s))) if f>108 else V((0,0,0))
        yaw=rad(29+2.5*math.sin(i*.034))
        across=V((-math.cos(yaw),-math.sin(yaw),0))
        toward=V((-math.sin(yaw),math.cos(yaw),0))
        tilt=rad(43+3*severity)
        up=UP*math.cos(tilt)-toward*math.sin(tilt)
        face=across.cross(up)
        rot=Matrix((across,up,face)).transposed().to_quaternion()
        phone.location=phone_center;phone.rotation_mode='QUATERNION';phone.rotation_quaternion=rot
        phone.keyframe_insert('location',frame=action_frame);phone.keyframe_insert('rotation_quaternion',frame=action_frame)
        def world(p):return phone_center+rot@V(p)
        for side,sfx,src in [(1,'r','Right'),(-1,'l','Left')]:
            def n(b):return b+'_'+sfx
            upper,lower,hand=n('upperarm'),n('lowerarm'),n('hand')
            knuckle=bonepoint(n('middle_01'))
            bind=frame3(knuckle-bonepoint(hand),bonepoint(n('index_01'))-bonepoint(n('pinky_01')))
            target=frame3(rot@V((-.69*side,.64,-.34)),rot@V((.28*side,.82,.42)))
            hand_delta=target@bind.inverted()
            offset=-.031 if side==1 else -.003
            anchor=world((side*.040,offset,-.004))
            if side==1:
                # Free right index reads the screen; the left palm carries the handset.
                target=frame3(rot@V((-.48,.72,-.50)),rot@V((-.40,.18,.90)))
                hand_delta=target@bind.inverted()
                finger_dir=V((-.27,.67,-.69)).normalized()
                tap=(1-math.cos((f-57)*math.pi/18))*.0014 if f<108 else .0009
                fingertip=V((.008,.017+.006*math.sin(i*.049),.0105+tap))
                finger_length=sum(bones[n('index_%02d'%j)].length for j in (1,2,3))
                knuckle=bonepoint(n('index_01'))
                anchor=world(fingertip-finger_dir*(finger_length-.00065))
            wrist=anchor-hand_delta@(knuckle-bonepoint(hand))
            sh=predicted(upper).translation
            length1=bones[upper].length;length2=bones[lower].length
            line=wrist-sh;dist=line.length;axis=line.normalized()
            capture_pole=(P(src+'ForeArm')-P(src+'Arm')).normalized()+V((-.3*side,.40,-.35))
            forearm_bind=bonepoint(hand)-bonepoint(lower)
            elbow_for_wrist=wrist-hand_delta@forearm_bind
            pole=.64*(elbow_for_wrist-sh).normalized()+.36*capture_pole
            perpendicular=(pole-axis*axis.dot(pole)).normalized()
            reach=min(dist,length1+length2-.00001)
            proj=(length1**2-length2**2+reach**2)/(2*reach)
            elbow=sh+axis*proj+perpendicular*math.sqrt(max(0.,length1**2-proj**2))
            upper_dir=elbow-sh;lower_dir=wrist-elbow
            old_u=bonepoint(lower)-bonepoint(upper);old_l=bonepoint(hand)-bonepoint(lower)
            upper_q=frame3(upper_dir,lower_dir)@frame3(old_u,old_l).inverted()
            global_delta(upper,upper_q)
            # Distribute pronation into the forearm so wrist skin stays smooth.
            lower_q=(hand_delta@old_l).rotation_difference(lower_dir)@hand_delta
            global_delta(lower,lower_q)
            global_delta(hand,hand_delta)
            for digit in ('index','middle','ring','pinky','thumb'):
                for segment in range(1,4):
                    bn=n('%s_%02d'%(digit,segment))
                    joint=rot.inverted()@(predicted(bn).translation-phone_center)
                    length=bones[bn].length
                    if side==1:
                        forward=(bonepoint(n('middle_01'))-bonepoint(hand)).normalized()
                        index=bonepoint(n('index_01'))-bonepoint(hand)
                        little=bonepoint(n('pinky_01'))-bonepoint(hand)
                        inward=index.cross(little).normalized()
                        if digit=='index':
                            dest=fingertip.copy()
                            if segment==1:dest.z+=.009
                            elif segment==2:dest.z+=.002
                        elif digit=='thumb':
                            home=moved(hand,knuckle+forward*.024+inward*.022)
                            dest=rot.inverted()@(home-phone_center)
                        else:
                            angles={'middle':(35,73,116),'ring':(50,91,134),'pinky':(59,101,144)}
                            bend=rad(angles[digit][segment-1])
                            d=hand_delta@(forward*math.cos(bend)+inward*math.sin(bend))
                            dest=joint+rot.inverted()@d*length
                    elif digit=='thumb':
                        # CMC opposes the fingers; the last pad comes down onto the display.
                        tap=tx[src+'HandThumb3'][0]-initial[src+'HandThumb3'][0]
                        targets=[(.032,-.009,.010),(.022,.012,.009),(.013,.020,.007)]
                        x,y,z=targets[segment-1]
                        dest=V((side*x,y+(offset+.038)+.10*tap.z,z+.035*tap.y))
                    else:
                        inset=(-.017 if side==-1 else -.011)
                        dest=joint+V((-side*length,.14*length,0))
                        dest.z=inset if segment<3 else inset+.002
                        if segment==1 and joint.z>-.004:
                            dest.x=side*.041;dest.z=-.015
                        if digit=='pinky':dest.y-=.12*length
                    local_dir=rot@(dest-joint).normalized()
                    natural=predicted(bn).to_quaternion()
                    old_dir=natural@V((0,1,0))
                    put(bn,old_dir.rotation_difference(local_dir)@natural)
            hip=predicted(n('thigh')).translation
            ankle=bonepoint(n('foot')).copy();ankle.x=side*-.133
            ankle.y+=.014*side;ankle.z+=.0192
            axis=(ankle-hip).normalized();dist=(ankle-hip).length
            thigh=bones[n('thigh')].length;calf=bones[n('calf')].length
            pole=(P(src+'Leg')-P(src+'UpLeg')).normalized()+FRONT*1.7
            bend=(pole-axis*pole.dot(axis)).normalized()
            proj=(thigh**2-calf**2+dist**2)/(2*dist)
            knee=hip+axis*proj+bend*math.sqrt(max(0,thigh**2-proj**2))
            rig_aim(n('thigh'),knee-hip);rig_aim(n('calf'),ankle-knee)
            global_delta(n('foot'),Quaternion(UP,rad(-side*5)))
            put(n('ball'))
        hb=rig.pose.bones['head']
        blink=0.
        for at in (43,145):
            if at-3<=f<=at+5:blink=smooth((f-at+3)/3) if f<=at else 1-smooth((f-at)/5)
        hb['blink']=blink;hb.keyframe_insert('["blink"]',frame=action_frame,group='Blink')
        head_delta=pose['head']@rest['head'].inverted()
        for side,center in eyes.items():
            line=head_delta.inverted()@phone_center-center
            gaze=line.normalized()
            release=smooth((f-140)/20) if f>108 else 0.
            pitch_angle=math.asin(-gaze.z)*(1-release)+rad(4)*release
            yaw_angle=math.atan2(gaze.x,-gaze.y)*(1-release)
            hb=rig.pose.bones['head']
            for kind,angle in [('pitch',pitch_angle),('yaw',yaw_angle)]:
                prop='gaze_'+kind+'_'+side
                hb[prop]=-angle
                hb.keyframe_insert('["'+prop+'"]',frame=action_frame,group='Eye direction')
        for name,m in pose.items():
            pb=rig.pose.bones[name]
            basis=predicted(name).inverted()@m
            q=basis.to_quaternion()
            if name in oldq:q.make_compatible(oldq[name])
            oldq[name]=q.copy()
            pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q
            pb.keyframe_insert('rotation_quaternion',frame=action_frame,group=name)
            if name in ('pelvis','head','neck_01'):
                pb.location=basis.translation;pb.keyframe_insert('location',frame=action_frame,group=name)
    # NLA strips use scene-frame coordinates. Both actions are playable on one timeline.
    for j,ob in enumerate(armatures):
        ob.animation_data.action=None
        t=ob.animation_data.nla_tracks.new();t.name='Character shots'
        for start,act in zip(starts,actions[j]):
            strip=t.strips.new(act.name,start,act)
            strip.action_slot=act.slots[0]
            strip.extrapolation='NOTHING'
    sc.frame_start=1;sc.frame_end=N
    sc.frame_set(1)
    return ear_i,shoulder_i


def bp3d_reference():
    """Measure existing episode anatomy in its neutral world frame; import no anatomical meshes."""
    root=Path(os.environ.get('BP3D_REFERENCE',KIT.parent/'research/anatomy3d/bodyparts3d_4.0'))
    elements={}
    for line in (root/'isa_element_parts.txt').read_text().splitlines():
        fields=line.split('\t')
        if len(fields)>=3:elements.setdefault(fields[0],[]).append(fields[2])
    def part(*fmas):
        pts=[]
        for fma in fmas:
            for stem in elements['FMA'+str(fma)]:
                path=root/'obj/isa_BP3D_4.0_obj_99'/(stem+'.obj')
                pts.extend([float(c) for c in line.split()[1:4]] for line in path.read_text().splitlines() if line.startswith('v '))
        return np.unique(np.array(pts)*.001+[0,.089,.072],axis=0)
    skull=part(52734,52735,9613,52737,52736,52747,9711)
    jaw=part(52748)
    def mid(a):return (a.max(0)+a.min(0))*.5
    def extreme(a,axis,sign,tol=.002):
        v=a[:,axis]*sign
        return a[v>=v.max()-tol].mean(0)
    # Cranial landmarks and the analogous skin/eye landmarks are evaluated independently.
    midline=np.abs(skull[:,0])<.012
    refs={'crown':extreme(skull[midline],2,1),
          'occiput':extreme(skull[midline],1,1),
          'menton':extreme(jaw[np.abs(jaw[:,0])<.012],2,-1)}
    for key,sgn,sclera in [('r',-1,58271),('l',1,58272)]:
        points=part(sclera);refs['eye_'+key]=mid(points[points[:,0]*sgn>0])
        # Same ear proxy used by the episode: posterosuperior to the mandibular condyle.
        condyle=extreme(jaw[jaw[:,0]*sgn>.024],2,1,.004)
        refs['ear_'+key]=condyle+np.array([sgn*.007,.010,.014])
    vertebrae=[]
    for i in range(7):
        a=part(12519+i)
        if i==0: # center of atlas ring in the median plane
            center=mid(a);center[0]=0.
        else:
            med=a[np.abs(a[:,0])<.013]
            front=med[med[:,1]<med[:,1].min()+.018]
            lo,hi=front[:,2].min(),front[:,2].max()
            if i==1:hi=min(hi,lo+.018) # exclude the dens from the axis body center
            center=np.array([0.,(front[:,1].min()+front[:,1].max())/2,(lo+hi)/2])
        vertebrae.append(center)
    return refs,mid(skull),vertebrae,skull


def registration(src,dst,weights):
    """Weighted similarity registration, with reflection explicitly excluded."""
    w=np.asarray(weights,dtype=float);w/=w.sum()
    a=np.asarray(src);b=np.asarray(dst)
    ca=w@a;cb=w@b
    u,s,vt=np.linalg.svd(((a-ca)*w[:,None]).T@(b-cb))
    fix=np.eye(3);fix[2,2]=np.sign(np.linalg.det(vt.T@u.T))
    rot=vt.T@fix@u.T
    scale=(s*fix.diagonal()).sum()/np.sum(w[:,None]*(a-ca)**2)
    mat=np.eye(4);mat[:3,:3]=scale*rot;mat[:3,3]=cb-scale*rot@ca
    return Matrix(mat)


def serial(a):
    return np.asarray(a,dtype=np.float64).round(7).tolist()


def export_anchors(rig,body,parts,eyes,ear_i,shoulder_i):
    scene=bpy.context.scene
    refs,skull_center,cervical,skull=bp3d_reference()
    key_order=list(refs)
    skin=mesh_coords(body.data)
    picks={'crown':nearest_vertex(body,(0,-.052,1.685)),'occiput':nearest_vertex(body,(0,.060,1.597)),
           'menton':nearest_vertex(body,(0,-.125,1.458)),'ear_r':ear_i,
           'ear_l':nearest_vertex(body,(.0695,-.0508,1.5534))}
    inset={'crown':(0,0,-.006),'occiput':(0,-.007,0),'menton':(0,.002,.0055),
           'ear_r':(.010,0,0),'ear_l':(-.010,0,0)}
    rest_targets={n:skin[i]+inset[n] for n,i in picks.items()}
    for side,pt in eyes.items():rest_targets['eye_'+side]=np.array(pt)
    fit=registration([refs[n] for n in key_order],[rest_targets[n] for n in key_order],
                     [2 if n.startswith('eye') else 1 for n in key_order])
    # Preserve depth and height while allowing for the narrower temporal vault of this cast.
    cranial_pivot=fit@V(skull_center)
    fit=Matrix.Translation(cranial_pivot+V((0,.0035,0)))@Matrix.Diagonal((.852,.92344,.955,1.0))@Matrix.Translation(-cranial_pivot)@fit
    # A held-out measure of the bony vault against the actual skin surface, independent of
    # the registered landmarks. Restrict to the vault to avoid the openings in the face.
    tree=BVHTree.FromPolygons(skin,[p.vertices[:] for p in body.data.polygons])
    exterior=0.;vault_count=0
    for point in skull[(skull[:,2]>1.61)&(skull[:,1]>-.044)][::3]:
        target=fit@V(point);hit,normal,_,distance=tree.find_nearest(target)
        if hit is not None:
            vault_count+=1
            exterior=max(exterior,(target-hit).dot(normal))
    rest={n:rig.matrix_world@rig.data.bones[n].matrix_local for n in ('head','neck_01','spine_03')}
    result={'schema_version':1,'fps':30,'units':'metres','axes':'Blender world, +Z up, -Y anterior, +X character left',
            'matrix_convention':'row-major arrays; M @ homogeneous column vector',
            'skull_quaternion_convention':'[w,x,y,z], from BodyParts3D episode axes into Blender world',
            'shots':{'opening':[1,60],'payoff':[61,126],'straighten':[85,115]},
            'opening_source_action':[1,108],
            'source_frame':'BodyParts3D 4.0 OBJ millimetres * 0.001 + (0,0.089,0.072), as in base_bp3d.py',
            'calibration':{'source_to_character_rest':serial(fit),'source_skull_bbox_center':serial(skull_center),
            'source_cervical_centers':{f'C{i+1}':serial(p) for i,p in enumerate(cervical)},
            'source_landmarks':{n:serial(refs[n]) for n in refs},'target_rest_landmarks':{n:serial(rest_targets[n]) for n in refs},
            'skin_to_bone_offsets_metres':{n:list(v) for n,v in inset.items()},'vault_sample_vertices':vault_count,
            'rest_vault_max_exterior_mm':round(exterior*1000,2)},'frames':[]}
    # Subdivision preserves the cage vertices but reorders attributes in some Blender versions.
    # Evaluate the deformed, indexed cage directly so landmark identity stays exact.
    mods=[o.modifiers[-1] for o in [body,parts['Outfit']]]
    old=[m.show_viewport for m in mods]
    for m in mods:m.show_viewport=False
    all_errors=[]
    for f in range(scene.frame_start,scene.frame_end+1):
        scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
        bones={n:rig.matrix_world@rig.pose.bones[n].matrix for n in rest}
        h,n,t=(bones[k]@rest[k].inverted() for k in ('head','neck_01','spine_03'))
        H=h@fit
        sv=body.evaluated_get(dg).data.vertices
        shoulder=parts['Outfit'].evaluated_get(dg).data.vertices[shoulder_i].co
        headrot=h.to_quaternion()
        targets={key:sv[i].co+headrot@V(inset[key]) for key,i in picks.items()}
        # Measure the eye globes on the separately skinned ocular mesh.
        eye_obj=parts['Eyes'].evaluated_get(dg)
        ocular=mesh_coords(eye_obj.data)
        # The skinned globe is rigid in the head. Transform back to bind coordinates
        # before taking left/right bounds, so roll/yaw cannot distort the measured centers.
        inv=np.asarray(h.inverted());ocular=ocular@inv[:3,:3].T+inv[:3,3]
        for side,sgn in [('r',-1),('l',1)]:
            pts=ocular[ocular[:,0]*sgn>0];c=(pts.min(0)+pts.max(0))*.5
            c[1]+=.00245
            targets['eye_'+side]=h@V(c)
        err={key:round((H@V(refs[key])-pt).length*1000,3) for key,pt in targets.items()}
        all_errors.extend(err.values())
        centers={};vertebra_maps={}
        chain=[fit@V(c) for c in reversed(cervical)]
        start=t@chain[0];end=h@chain[-1]
        distance=(end-start).length
        bind_axis=(chain[-1]-chain[0]).normalized()
        base_tangent=n.to_quaternion()@bind_axis
        top_tangent=h.to_quaternion()@bind_axis
        chain_positions=[]
        for j,bind in enumerate(chain):
            u=(bind.z-chain[0].z)/(chain[-1].z-chain[0].z)
            u2=u*u;u3=u2*u
            center=(start*(2*u3-3*u2+1)+end*(-2*u3+3*u2)
                    +base_tangent*(u3-2*u2+u)*distance+top_tangent*(u3-u2)*distance)
            residue=bind-chain[0].lerp(chain[-1],u)
            q=t.to_quaternion().slerp(h.to_quaternion(),u)
            chain_positions.append(center+q@residue)
        for j,center in enumerate(chain_positions):
            key='C'+str(7-j);i=6-j
            lo=max(0,j-1);hi=min(6,j+1)
            q=t.to_quaternion().slerp(h.to_quaternion(),j/6)
            before=q@(chain[hi]-chain[lo])
            after=chain_positions[hi]-chain_positions[lo]
            bend=before.rotation_difference(after)@q
            orient=bend.to_matrix()@fit.to_3x3()
            vm=Matrix.Translation(center)@orient.to_4x4()@Matrix.Translation(-V(cervical[i]))
            centers[key]=serial(center);vertebra_maps[key]=serial(vm)
        result['frames'].append({'frame':f,'shot':'opening' if f<=108 else 'payoff',
                'head_world':serial(bones['head']),'neck_world':serial(bones['neck_01']),
                'head_center':serial(H@V(skull_center)),'skull_orientation_wxyz':serial(H.to_quaternion()),
                'bp3d_skull_to_world':serial(H),'cervical_centers':centers,'bp3d_vertebra_to_world':vertebra_maps,
                'ear_world':serial(sv[ear_i].co),'shoulder_world':serial(shoulder),
                'ear_ahead_of_shoulder_m':round(shoulder.y-sv[ear_i].co.y,6),
                'skull_landmark_errors_mm':err})
    for m,enabled in zip(mods,old):m.show_viewport=enabled
    result['calibration']['max_landmark_residual_mm']=round(max(all_errors),3)
    result['calibration']['rms_landmark_residual_mm']=round(float(np.sqrt(np.mean(np.square(all_errors)))),3)
    long_take=result['frames']
    result['opening_tail_frames']=long_take[60:108]
    result['frames']=long_take[:60]+long_take[108:]
    for row in result['frames'][60:]:row['frame']-=48
    with (HERE/'anchors.json').open('w') as out:json.dump(result,out,ensure_ascii=False,separators=(',',':'))
    print('Cranial fit:',result['calibration']['max_landmark_residual_mm'],'mm; vault exterior:',exterior*1000,'mm')


def editorial_cut(rig,phone):
    # Both source takes retain their complete bake. The first strip has a 48-frame tail handle.
    for ob in (rig,phone):
        track=ob.animation_data.nla_tracks[0]
        actions=[s.action for s in track.strips]
        for strip in list(track.strips):track.strips.remove(strip)
        opening=track.strips.new(actions[0].name,1,actions[0]);opening.action_slot=actions[0].slots[0]
        opening.action_frame_end=60;opening.frame_end=60;opening.extrapolation='NOTHING'
        payoff=track.strips.new(actions[1].name,61,actions[1]);payoff.action_slot=actions[1].slots[0]
        payoff.extrapolation='NOTHING'
        assert (opening.frame_end,payoff.frame_start,payoff.frame_end)==(60,61,126)
    scene=bpy.context.scene;scene.frame_end=126
    for f,name in [(1,'OPENING'),(31,'Mid-slump'),(60,'Opening out'),(61,'PAYOFF'),(85,'Peak / straighten'),(115,'Neutral')]:
        scene.timeline_markers.new(name,frame=f)


if __name__=='__main__':
    init()
    rig,body,parts=make_cast()
    camera_and_light()
    phone=contact_phone()
    hair_fibers(rig,parts['Hair underlay'])
    edge_bands(rig,parts['Outfit'])
    cotton_drape(parts['Outfit'])
    spectacles(rig)
    complexion(body)
    eyelids(rig,body,parts['Lashes'])
    eyes=ocular_material(rig,parts['Eyes'])
    ear,shoulder=bake(rig,body,parts,phone,eyes)
    bpy.context.scene['ear_index']=ear
    bpy.context.scene['shoulder_index']=shoulder
    export_anchors(rig,body,parts,eyes,ear,shoulder)
    editorial_cut(rig,phone)
    bpy.context.scene.frame_set(31)
    organize(rig,phone)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'human_final.blend'),compress=True)
