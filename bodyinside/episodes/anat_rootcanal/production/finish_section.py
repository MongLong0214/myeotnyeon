"""Continue the existing core through preparation and feather the cut caries into surrounding dentin."""
import bpy
from pathlib import Path
sc=bpy.context.scene
sc.frame_set(749)
core=sc.objects['Bonded access core']
stump=sc.objects['Restored exterior • stump_full']
if 'Prepared access core' not in sc.objects:
    prepared=core.copy()
    prepared.data=core.data.copy()
    sc.collection.objects.link(prepared)
    prepared.name='Prepared access core'
    prepared.animation_data_clear()
    prepared.location=(0,0,0)
    prepared.scale=(1,1,1)
    trim=prepared.modifiers.new('Match crown preparation','BOOLEAN')
    trim.operation='INTERSECT';trim.solver='EXACT';trim.object=stump
    bpy.context.view_layer.objects.active=prepared
    bpy.ops.object.modifier_apply(modifier=trim.name)
    if not prepared.data.polygons:raise ValueError('Empty prepared core')
    for f,on in [(0,False),(750,True),(868,False)]:
        for name in ('hide_viewport','hide_render'):
            setattr(prepared,name,not on);prepared.keyframe_insert(name,frame=f)
    print('PREPARED',len(prepared.data.polygons))

m=bpy.data.materials['Cavitated dentin']
nt=m.node_tree
if 'Caries mineral gradient' not in nt.nodes:
    def node(kind):return nt.nodes.new(kind)
    def wire(a,b):nt.links.new(a,b)
    def math(operation,a,b=0):
        n=node('ShaderNodeMath');n.operation=operation
        for i,k in enumerate((a,b)):
            if isinstance(k,(int,float)):n.inputs[i].default_value=k
            else:wire(k,n.inputs[i])
        return n.outputs[0]
    pos=node('ShaderNodeNewGeometry').outputs['Position']
    xyz=node('ShaderNodeSeparateXYZ');wire(pos,xyz.inputs[0])
    noise=node('ShaderNodeTexNoise');wire(pos,noise.inputs['Vector'])
    noise.inputs['Scale'].default_value=2.3;noise.inputs['Detail'].default_value=4.0
    x=math('ADD',xyz.outputs['X'],.20)
    x=math('ADD',x,math('MULTIPLY',math('SINE',math('MULTIPLY',xyz.outputs['Z'],1.3)),.23))
    distance=math('ADD',math('ABSOLUTE',x),math('MULTIPLY',math('SUBTRACT',noise.outputs[0],.5),1.05))
    mask=node('ShaderNodeMapRange');mask.interpolation_type='SMOOTHERSTEP';wire(distance,mask.inputs[0])
    mask.inputs['From Min'].default_value=.48;mask.inputs['From Max'].default_value=1.77
    source=nt.nodes.get('Color Ramp').outputs[0]
    darken=node('ShaderNodeMixRGB');darken.blend_type='MULTIPLY';darken.inputs[0].default_value=.7
    wire(source,darken.inputs[1]);darken.inputs[2].default_value=(.16,.12,.10,1)
    dent=node('ShaderNodeTexNoise');wire(pos,dent.inputs['Vector']);dent.inputs['Scale'].default_value=1.4;dent.inputs['Detail'].default_value=3.8
    colour=node('ShaderNodeValToRGB')
    for el,p,c in zip(colour.color_ramp.elements,(.23,.76),((.37,.213,.095,1),(.78,.56,.30,1))):
        el.position=p;el.color=c
    wire(dent.outputs['Fac'],colour.inputs[0])
    mix=node('ShaderNodeMixRGB');mix.name='Caries mineral gradient';wire(mask.outputs[0],mix.inputs[0]);wire(darken.outputs[0],mix.inputs[1]);wire(colour.outputs[0],mix.inputs[2])
    wire(mix.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color'])
sc.frame_set(0)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
