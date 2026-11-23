"""Open surgery_draft2.blend in Blender, then run this script to build draft 3."""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Matrix, Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from look import (S,O,M,V,ZERO,Graph,rgb,mm,windows,flap,bank,cage,surface_point,tissue,
                  fibers,bone_and_enamel,fracture_and_bur_tracks,longitudinal_dentin,instruments,closure,camera_and_light)
from fluid_bakes import PRESETS,PULLS,SOCKET_ORIGIN,socket_frame

def linear(id):
    ad=id.animation_data
    if not ad or not ad.action:return
    slot=ad.action.layers[0].strips[0].channelbag(ad.action_slot)
    for fc in slot.fcurves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'


def carrier(name,position=(0,0,0),parent=None):
    o=O.new(name,None);S.collection.objects.link(o)
    o.empty_display_size=.0008;o.parent=parent
    o.location=V(position)*.001+(Vector() if parent else ZERO)
    return o


def remove_proxy_fluids():
    starts=('Saline droplet','Atomised saline','Diluted blood droplet','Impact droplets','Blood in the cut socket edge',
        'Slurry gathered','Saline meniscus','Small air bubble','Blood bead','Blood adhering','Blood film stretching',
        'Peripheral saline','Wicking film','Saline entering','Pink irrigation drawn','Capillary drop','Free irrigant jet',
        'Handpiece saline jet','Blood welling','Shallow blood pool','Capillary welling','Puncture bead',
        'Continuous socket meniscus','Continuous saline core','Surface blood film','Moist reflection along the flap margin')
    for obj in list(S.objects):
        if obj.name.startswith(starts):
            bpy.data.objects.remove(obj,do_unlink=True)


def fluids_materials():
    def body(name,col,rough,trans,ior):
        m=M.new(name);m.use_nodes=True;g=Graph(m)
        g.set(**{'Base Color':col,'Roughness':rough,'Transmission Weight':trans,'IOR':ior,
                 'Coat Weight':.32,'Coat Roughness':.073,'Coat IOR':1.333})
        return m,g
    blood,b=body('Oozing capillary blood',rgb(.092,.0024,.008),.135,.19,1.35)
    clear,g=body('Saline carrying wet mineral dust',rgb(.94,.94,.93),.080,.90,1.333)
    origin=g.make('ShaderNodeTexCoord');origin.object=O['Surgical handpiece']
    coord=origin.outputs['Object']
    z=g.make('ShaderNodeSeparateXYZ',Vector=coord).outputs['Z']
    # Sockets clamp ramp inputs below zero. Offset Z before mapping the impact band.
    low=g.ramp(g.math('ADD',z,.004),[(.0043,.80),(.0055,.42),(.0065,0)])
    n=g.noise(coord,7600,2.2,.30)
    grains=g.ramp(n,[(.57,.0),(.67,.21),(.77,.92)])
    density=g.math('MULTIPLY',low,grains)
    g.set(**{'Base Color':g.mix(low,rgb(.93,.948,.94),rgb(.69,.31,.31)),
             'Transmission Weight':g.math('SUBTRACT',.92,g.math('MULTIPLY',density,.88))})
    g.set(**{'Base Color':g.mix(density,g.current('Base Color'),rgb(.82,.64,.44))})
    # Fade spray at the edge of this local solver volume after it has left the
    # tool. This prevents a straight domain boundary at the edge of a droplet fan.
    planar=g.vec('MULTIPLY',coord,(1,1,0))
    span=g.make('ShaderNodeVectorMath',Vector=planar);span.operation='LENGTH'
    perimeter=g.ramp(span.outputs['Value'],[(.0025,1),(.00372,0)])
    lower=g.ramp(g.math('ADD',z,.003),[(.0015,0),(.0031,1)])
    shader=g.make('ShaderNodeMixShader')
    g.plug(shader.inputs[0],g.math('MULTIPLY',perimeter,lower))
    g.plug(shader.inputs[1],g.make('ShaderNodeBsdfTransparent').outputs[0]);g.plug(shader.inputs[2],g.bs.outputs[0])
    g.plug(g.nt.nodes.get('Material Output').inputs['Surface'],shader.outputs[0])
    dilute,_=body('Rose effluent at the aspirator',rgb(.69,.31,.32),.118,.71,1.334)
    mat,g=body('Alveolar blood with advancing saline dilution',rgb(.082,.0018,.005),.115,.23,1.351)
    world=g.make('ShaderNodeNewGeometry').outputs['Position']
    space=g.vec('SUBTRACT',world,tuple(ZERO+SOCKET_ORIGIN*.001))
    sep=g.make('ShaderNodeSeparateXYZ',Vector=space)
    turb=g.noise(space,420,3.3,1.3)
    # The wash advances from the cannula across the meniscus. Free jet above
    # the cavity remains transmissive as it enters the intra-alveolar blood.
    tint=g.make('ShaderNodeValue')
    for t,val in [(0,0),(33.85,0),(34.2,.29),(34.89,.86),(35.58,1),(36.02,.88),(36.65,.15),(37.02,0),(44,0)]:
        tint.outputs[0].default_value=val;tint.outputs[0].keyframe_insert(data_path='default_value',frame=mm(t))
    yy=g.math('MULTIPLY',sep.outputs['Y'],29)
    way=g.math('SUBTRACT',g.math('MULTIPLY',tint.outputs[0],1.80),g.math('ADD',g.math('MULTIPLY',turb,.74),yy))
    wash=g.ramp(way,[(.062,0),(.80,.96)])
    jet=g.ramp(sep.outputs['Z'],[(.0013,0),(.0034,1)])
    dye_coord=g.vec('MULTIPLY',space,(1.35,.73,1.0))
    dye=g.make('ShaderNodeTexNoise',Vector=dye_coord,Scale=527,Detail=3.1,Distortion=2.4)
    dye.noise_dimensions='4D'
    for t,w in [(25,0),(33.85,0),(34.45,.44),(35.25,.91),(36.25,1.64),(37,1.76),(44,1.76)]:
        dye.inputs['W'].default_value=w;dye.inputs['W'].keyframe_insert(data_path='default_value',frame=mm(t))
    swirl=g.ramp(dye.outputs['Fac'],[(.275,.08),(.405,.27),(.51,.78),(.65,.995)])
    dilution=g.math('MULTIPLY',wash,swirl)
    pink=g.mix(turb,rgb(.63,.17,.21),rgb(.98,.60,.62))
    heme=g.mix(dye.outputs['Fac'],rgb(.056,.001,.004),rgb(.153,.003,.014))
    g.set(**{'Base Color':g.mix(jet,g.mix(dilution,heme,pink),rgb(.97,.98,.98)),
        'Roughness':.098,
        'Transmission Weight':g.mix(jet,g.mix(dilution,(.15,)*3+(1,),(.54,)*3+(1,)),(.97,)*3+(1,))})
    glass=g.make('ShaderNodeBsdfGlass',Color=rgb(.986,.961,.962),Roughness=.052,IOR=1.333)
    surface=g.make('ShaderNodeMixShader')
    g.plug(surface.inputs[0],g.mix(jet,g.math('MULTIPLY',dilution,.48),(.93,.93,.93,1)))
    g.plug(surface.inputs[1],g.bs.outputs[0]);g.plug(surface.inputs[2],glass.outputs[0])
    g.plug(g.nt.nodes.get('Material Output').inputs['Surface'],surface.outputs[0])
    absorption=g.make('ShaderNodeVolumeAbsorption',Color=rgb(.77,.32,.38),Density=62)
    g.plug(g.nt.nodes.get('Material Output').inputs['Volume'],absorption.outputs[0])
    return blood,clear,dilute,mat


def smooth_modifier():
    tree=bpy.data.node_groups.new('Smooth baked liquid interfaces','GeometryNodeTree')
    tree.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp=tree.nodes.new('NodeGroupInput');out=tree.nodes.new('NodeGroupOutput')
    n=tree.nodes.new('GeometryNodeSetShadeSmooth');n.domain='FACE'
    tree.links.new(inp.outputs[0],n.inputs['Geometry']);tree.links.new(n.outputs[0],out.inputs[0])
    return tree


class CacheSurface:
    def __init__(self,name,mat,smooth):
        old=set(O)
        bpy.ops.wm.alembic_import(filepath=str(HERE/(name+'.abc')),set_frame_range=False,
            validate_meshes=False,always_add_cache_reader=True,as_background_job=False)
        meshes=[o for o in set(O)-old if o.type=='MESH']
        if len(meshes)!=1:
            raise RuntimeError(f'{name} cache contains {[m.name for m in meshes]}')
        self.template=meshes[0];self.name=name;self.instances=0
        self.matrix=self.template.matrix_world.copy()
        self.template.constraints.clear()
        self.template.data.materials.clear();self.template.data.materials.append(mat)
        mod=self.template.modifiers.new('Smooth liquid interface','NODES');mod.node_group=smooth
        self.template.cycles.use_motion_blur=False

    def place(self,base,keys,spans):
        if self.instances:
            ob=self.template.copy();S.collection.objects.link(ob)
            ob.animation_data_clear()
            modifier=next(m for m in ob.modifiers if m.type=='MESH_SEQUENCE_CACHE')
            modifier.cache_file=modifier.cache_file.copy()
            modifier.cache_file.animation_data_clear()
        else:
            ob=self.template
        self.instances+=1
        ob.name=f'FLIP {self.name} • {self.instances}'
        mod=next(m for m in ob.modifiers if m.type=='MESH_SEQUENCE_CACHE')
        c=mod.cache_file;c.override_frame=True
        for f,cacheframe in keys:
            c.frame=float(cacheframe);c.keyframe_insert(data_path='frame',frame=f)
        linear(c)
        ob.parent=base;ob.matrix_parent_inverse=Matrix.Identity(4)
        ob.matrix_basis=Matrix.Scale(.01,4) @ self.matrix
        windows(ob,spans)
        return ob


def install_liquids():
    blood,clear,dilute,pool=fluids_materials()
    smoothing=smooth_modifier()
    def surface(name,mat):return CacheSurface(name,mat,smoothing)
    drill=carrier('Saline at contra-angle port',parent=O['Surgical handpiece'])
    # Orient the external irrigation port into the lateral camera profile.
    # The nozzle and its simulated spray move together about the shank.
    O['External saline spray port'].parent=drill
    for t,roll in [(0,50),(2.99,50),(3.1,-18),(44,-18)]:
        drill.rotation_euler.z=math.radians(roll);drill.keyframe_insert(data_path='rotation_euler',frame=mm(t))
    for n in clear.node_tree.nodes:
        if n.type=='TEX_COORD' and n.object==O['Surgical handpiece']:n.object=drill
    jet=surface('bur',clear)
    windows_bur=[(0,2.99),(13.60,17.96),(19.30,22.81),(27.22,27.91)]
    keys=[]
    for (a,b),offset in zip(windows_bur,(23,2,9,36)):
        keys.extend([(mm(a),offset),(mm(b),min(90,offset+mm(b)-mm(a)))])
    jet.place(drill,keys,windows_bur)
    bead=surface('puncture',blood)
    bead.place(carrier('Injection puncture',(30.65,-25.5,39.28)),[(mm(6.03),1),(mm(7.18),24)],[(6.03,7.18)])
    # First points lie immediately behind the scalpel. Each bank carries
    # its baked patches through reflection and closure via the deforming cage.
    margin=surface('margin',blood)
    ts=[7.35,7.62,8,8.4,8.8,9.2,9.6,9.95,10.33,10.70,11.14,11.67,12.1,12.52,12.97,36.61,36.81,37.09,37.41,37.75]
    for side,sign in [(flap,1),(bank,-1)]:
        positions=[21,31,44,55,67] if sign==1 else [24,37,50,64]
        anchors=[carrier(f'Capillaries in {side.name[:7]} {j}') for j in positions]
        for t in ts:
            c=cage(side,mm(t))
            for j,o in zip(positions,anchors):
                p,normal=surface_point(c,.20,j,sign)
                inward=(c[89+j]-c[j]).normalized()
                yaxis=normal.cross(inward).normalized()
                xaxis=yaxis.cross(normal).normalized()
                o.rotation_mode='QUATERNION'
                o.rotation_quaternion=Matrix((xaxis,yaxis,normal)).transposed().to_quaternion()
                o.location=ZERO+p+inward*.00030-normal*.00015
                o.keyframe_insert(data_path='location',frame=mm(t));o.keyframe_insert(data_path='rotation_quaternion',frame=mm(t))
        for i,(j,o) in enumerate(zip(positions,anchors)):
            scale=.57+(j%4)*.045
            for t,h in [(7,.86),(9.9,.86),(12.75,.42),(37.4,.42)]:
                o.scale=(scale,scale,scale*h);o.keyframe_insert(data_path='scale',frame=mm(t))
            y=-49+27*j/88;a=7.37+(y+43.6)/6.96
            margin.place(o,[(mm(a),1),(mm(a+.95),17),(mm(a+2.25),24)],[(a,37.45)])
    root=carrier('Registered FLIP socket',SOCKET_ORIGIN)
    soc=surface('socket',pool)
    soc.place(root,[(socket_frame(f),f) for f in (1,42,129)],[(25.35,44.05)])
    for n,(_,_,anchor,t) in PULLS.items():
        duration=(PRESETS[n][3]-1)/20
        surface(n,blood).place(carrier('Periodontal attachment '+n,anchor),[(mm(t),1),(mm(t+duration),PRESETS[n][3])],[(t,t+duration)])
    suction=carrier('Aspirator wet field')
    constraint=suction.constraints.new('COPY_LOCATION');constraint.target=O['Assistant suction • fenestrated Frazier tip']
    surface('suction',dilute).place(suction,[(mm(14.10),1),(mm(18.12),55)],[(14.10,18.12)])


def main():
    remove_proxy_fluids()
    tissue();fibers();bone_and_enamel();fracture_and_bur_tracks();longitudinal_dentin();instruments();closure();camera_and_light()
    install_liquids()
    S.frame_set(1)
    S.cycles.samples=16;S.cycles.use_denoising=True
    S.render.resolution_x=540;S.render.resolution_y=960;S.render.resolution_percentage=100
    S.render.filepath='//renders/f_'
    bpy.context.preferences.filepaths.save_version=0
    # Relative cache paths refer to this blend's own directory.
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'surgery_draft3.blend'),compress=True,relative_remap=True)
    for cache in bpy.data.cache_files:
        cache.filepath='//'+Path(bpy.path.abspath(cache.filepath)).name
    for img in bpy.data.images:
        if img.source=='FILE' and not img.packed_file:
            img.pack()
    bpy.ops.wm.save_mainfile(compress=True)
    print('Draft 3 scene saved',flush=True)


if __name__=='__main__':main()
