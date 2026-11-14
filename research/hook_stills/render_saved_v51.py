import bpy,sys,time,json
from pathlib import Path
p=Path('/Users/isaac/projects/verdict-kr/work/research/hook_stills');q=sys.argv[sys.argv.index('--')+1];st=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(p/f'{q}.blend'));s=bpy.context.scene
for im in bpy.data.images:
 if im.source=='FILE' and max(im.size)>1536:
  k=1536/max(im.size);im.scale(max(1,int(im.size[0]*k)),max(1,int(im.size[1]*k)))
s.eevee.taa_render_samples=64;s.eevee.volumetric_tile_size='4';s.eevee.volumetric_samples=96;s.eevee.shadow_ray_count=1;s.eevee.shadow_pool_size='512'
for ob in bpy.data.objects:
 if ob.type=='LIGHT':
  ob.data.use_shadow=False
if q=='q017':
 for ob in bpy.data.objects:
  if ob.name.startswith('cctv'):
   ob.hide_render=True
   for ch in ob.children_recursive:ch.hide_render=True
 s.camera.data.dof.focus_distance=12;s.camera.data.dof.aperture_fstop=2.8
 for ext in ['_raw.png','_render.json','.png','.jpg']:
  f=p/f'{q}{ext}'
  if f.exists():f.rename(p/f'{q}_rejected_r1{ext}')
s.render.filepath=str(p/f'{q}_raw.png');rs=time.monotonic();bpy.ops.render.render(write_still=True)
(p/f'{q}_render.json').write_text(json.dumps(dict(episode=q,engine='BLENDER_EEVEE',samples=s.eevee.taa_render_samples,screen_space_raytracing=s.eevee.use_raytracing,volumetric_samples=s.eevee.volumetric_samples,render_seconds=time.monotonic()-rs,total_seconds=time.monotonic()-st,resolution=[1080,1920],texture_cap=1536),indent=2))
