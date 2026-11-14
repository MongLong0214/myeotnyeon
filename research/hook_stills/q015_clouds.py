import sys,bpy,time,json
from pathlib import Path
p=Path('/Users/isaac/projects/verdict-kr/work/research/hook_stills');sys.path.insert(0,str(p));from cloud_world import apply
bpy.ops.wm.open_mainfile(filepath=str(p/'q015.blend'));s=bpy.context.scene;apply(s)
for ext in ['_raw.png','_render.json','.png','.jpg']:
 f=p/f'q015{ext}'
 if f.exists():f.rename(p/f'q015_rejected_r3{ext}')
s.render.filepath=str(p/'q015_raw.png');rs=time.monotonic();bpy.ops.render.render(write_still=True)
(p/'q015_render.json').write_text(json.dumps(dict(episode='q015',engine='BLENDER_EEVEE',samples=96,screen_space_raytracing=True,volumetric_samples=128,render_seconds=time.monotonic()-rs,resolution=[1080,1920],revision=4),indent=2))
