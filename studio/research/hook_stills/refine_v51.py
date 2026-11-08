import bpy,sys,math,json,time
from pathlib import Path
from mathutils import Vector
W=Path('.');sys.path.insert(0,str(W/'production/blender'));import world2 as A
q=sys.argv[sys.argv.index('--')+1];p=W/'research/hook_stills';bpy.ops.wm.open_mainfile(filepath=str(p/f'{q}.blend'));s=bpy.context.scene;start=time.monotonic()
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
if q=='q015':
 for n in s.world.node_tree.nodes:
  if n.type=='PRINCIPLED_VOLUME':n.inputs['Density'].default_value=.00045
 for o in bpy.data.objects:
  if 'floodlight' in o.name and o.type=='LIGHT':o.data.energy=13000;o.data.color=(.67,.83,1)
  if o.name=='cold dusk fill':o.data.energy=6000
 l=A.light('AREA','barrack facade wash',(0,5,10),13000,(.22,.43,.62),size=(28,14));aim(l,(0,31,3));l.data.volume_factor=.05
 l=A.light('AREA','wire rim',(-15,16,6),3000,(.35,.6,.75),size=(18,4));aim(l,(2,24,1))
 s.camera.data.lens=23;s.camera.location=(-3,-10,1.4);aim(s.camera,(0,26,4.4))
if q=='q012':
 for o in list(bpy.data.objects):
  if o.name.startswith('distant fire tongue') or o.name.startswith('drifting smoke'):bpy.data.objects.remove(o,do_unlink=True)
 # Noise-masked emissive volume fire. Density falls toward the top and every domain boundary.
 m=bpy.data.materials.new('volumetric wildfire tongues');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');v=nt.nodes.new('ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(.09,.035,.012,1);v.inputs['Emission Color'].default_value=(1,.12,.005,1)
 tc=nt.nodes.new('ShaderNodeTexCoord');mp=nt.nodes.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(16,3,2);nt.links.new(tc.outputs['Generated'],mp.inputs[0]);nz=nt.nodes.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=3;nz.inputs['Detail'].default_value=5;nt.links.new(mp.outputs['Vector'],nz.inputs['Vector'])
 sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Generated'],sep.inputs[0]);z=nt.nodes.new('ShaderNodeMath');z.operation='MULTIPLY';z.inputs[1].default_value=.72;nt.links.new(sep.outputs['Z'],z.inputs[0]);sub=nt.nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';nt.links.new(nz.outputs['Fac'],sub.inputs[0]);nt.links.new(z.outputs[0],sub.inputs[1]);r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.28;r.color_ramp.elements[0].color=(0,0,0,1);r.color_ramp.elements[1].position=.55;r.color_ramp.elements[1].color=(1,1,1,1);nt.links.new(sub.outputs[0],r.inputs[0]);den=nt.nodes.new('ShaderNodeMath');den.operation='MULTIPLY';den.inputs[1].default_value=.6;nt.links.new(r.outputs[0],den.inputs[0]);nt.links.new(den.outputs[0],v.inputs['Density']);em=nt.nodes.new('ShaderNodeMath');em.operation='MULTIPLY';em.inputs[1].default_value=6;nt.links.new(r.outputs[0],em.inputs[0]);nt.links.new(em.outputs[0],v.inputs['Emission Strength']);nt.links.new(v.outputs['Volume'],out.inputs['Volume'])
 # Place domains following the actual existing ridgeline's old firelight positions.
 for o in [x for x in bpy.data.objects if x.name.startswith('fire light')]:
  A.box('wildfire volume',(24,6,8),(o.location.x,o.location.y,o.location.z+1),m)
 # Larger, much thinner non-emissive smoke drifting sideways; no opaque columns.
 sm=bpy.data.materials['turbulent smoke'];vol=next(n for n in sm.node_tree.nodes if n.type=='PRINCIPLED_VOLUME');vol.inputs['Color'].default_value=(.32,.38,.41,1)
 mult=next(n for n in sm.node_tree.nodes if n.type=='MATH');mult.inputs[1].default_value=.012
 for x,z in [(-20,22),(4,26),(28,29)]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=1,location=(x+5,47,z));o=bpy.context.object;o.name='thin windblown smoke';o.scale=(25,8,8);o.data.materials.append(sm)
 s.camera.data.lens=26;s.camera.location=(-12,-23,12);aim(s.camera,(0,50,18))
 # Increase moonlight terrain texture without washing out the fire glow.
 bpy.data.objects['moon rim'].data.energy=50000
for ext in ['_raw.png','_render.json','.blend']:
 src=p/f'{q}{ext}'
 if src.exists():src.rename(p/f'{q}_rejected_r1{ext}')
s.render.filepath=str(p/f'{q}_raw.png');bpy.ops.wm.save_as_mainfile(filepath=str(p/f'{q}.blend'));rs=time.monotonic();bpy.ops.render.render(write_still=True)
(p/f'{q}_render.json').write_text(json.dumps(dict(episode=q,engine='BLENDER_EEVEE',samples=s.eevee.taa_render_samples,screen_space_raytracing=True,volumetric_samples=s.eevee.volumetric_samples,render_seconds=time.monotonic()-rs,total_seconds=time.monotonic()-start,resolution=[1080,1920],revision=2),indent=2))
