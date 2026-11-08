import sys,bpy,json,time
from pathlib import Path
p=Path('research/hook_stills');sys.path.insert(0,str(p));from cloud_world import apply
assert not (p/'q013_clouds_raw.png').exists();bpy.ops.wm.open_mainfile(filepath=str(p/'q013.blend'));s=bpy.context.scene;apply(s);s.render.filepath=str(p/'q013_clouds_raw.png');start=time.monotonic();bpy.ops.render.render(write_still=True)
with (p/'q013_clouds_render.json').open('x') as f:json.dump(dict(episode='q013',engine='BLENDER_EEVEE',samples=64,screen_space_raytracing=True,volumetric_samples=64,resolution=[1080,1920],render_seconds=time.monotonic()-start,revision='same bounded procedural sky as final v51 q015',network=False,people=False),f,indent=1)
