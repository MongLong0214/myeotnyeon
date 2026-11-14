import bpy,sys,math,random,time,json
from pathlib import Path
from mathutils import Vector,noise
p=Path('/Users/isaac/projects/verdict-kr/work/research/hook_stills');sys.path.insert(0,str(p.parents[1]/'production/blender'));import world2 as A
bpy.ops.wm.open_mainfile(filepath=str(p/'q012.blend'));s=bpy.context.scene
for o in list(bpy.data.objects):
 if o.name.startswith('wildfire volume'):bpy.data.objects.remove(o,do_unlink=True)
# The requested distant wildfire glow, not literal geometric flame shapes.
mt=bpy.data.materials['scorched rocky terrain'];nt=mt.node_tree;bs=nt.nodes.get('Principled BSDF');tc=nt.nodes.new('ShaderNodeTexCoord');n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=2;n.inputs['Detail'].default_value=6;nt.links.new(tc.outputs['Object'],n.inputs['Vector']);r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.008,.016,.012,1);r.color_ramp.elements[1].color=(.065,.075,.052,1);nt.links.new(n.outputs['Fac'],r.inputs[0]);nt.links.new(r.outputs[0],bs.inputs['Base Color']);b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.65;b.inputs['Distance'].default_value=.35;nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs[0],bs.inputs['Normal'])
# Several ridges fill the distance, with the strongest light concealed behind their crests.
for k in [1,2]:
 verts=[];faces=[];nx=85;ny=35
 for j in range(ny):
  y=65+j*3+k*35
  for i in range(nx):
   x=-125+i*3;z=10+4*math.sin(x*.06+k*1.4)+6*noise.fractal(Vector((x*.03,y*.04,k)),1,2,4)+k*6;verts.append((x,y,z))
 for j in range(ny-1):
  for i in range(nx-1):a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
 me=bpy.data.meshes.new('distant ridge');me.from_pydata(verts,[],faces);me.materials.append(mt);o=bpy.data.objects.new('distant ridge',me);s.collection.objects.link(o)
 for f in me.polygons:f.use_smooth=True
for o in bpy.data.objects:
 if o.type=='LIGHT' and o.name.startswith('fire light'):
  o.data.energy=24000;o.location.y+=7;o.location.z-=2;o.data.shadow_soft_size=10
 if o.name=='moon rim':o.data.energy=15000
# Turbulent low smoke catches the orange light, the source stays below the ridgeline.
sm=bpy.data.materials['turbulent smoke'];v=next(n for n in sm.node_tree.nodes if n.type=='PRINCIPLED_VOLUME');v.inputs['Color'].default_value=(.22,.24,.26,1)
mult=next(n for n in sm.node_tree.nodes if n.type=='MATH');mult.inputs[1].default_value=.025
for o in bpy.data.objects:
 if o.name.startswith('thin windblown smoke'):o.location.z-=3;o.scale.z=10
s.view_settings.exposure=.1;s.eevee.taa_render_samples=64;s.eevee.volumetric_tile_size='4';s.eevee.volumetric_samples=96
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.use_shadow=False
for im in bpy.data.images:
 if im.source=='FILE' and max(im.size)>1536:
  k=1536/max(im.size);im.scale(int(im.size[0]*k),int(im.size[1]*k))
sys.path.insert(0,str(p));from cloud_world import apply;apply(s)
for ext in ['_raw.png','_render.json','.png','.jpg']:
 f=p/f'q012{ext}'
 if f.exists():f.rename(p/f'q012_rejected_r4{ext}')
s.render.filepath=str(p/'q012_raw.png');st=time.monotonic();bpy.ops.render.render(write_still=True)
(p/'q012_render.json').write_text(json.dumps(dict(episode='q012',engine='BLENDER_EEVEE',samples=64,screen_space_raytracing=True,volumetric_samples=96,render_seconds=time.monotonic()-st,resolution=[1080,1920],revision=5),indent=2))
