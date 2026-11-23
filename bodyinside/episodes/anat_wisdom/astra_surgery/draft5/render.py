"""Render the revised shots, preserving the approved clean plates at unchanged cuts."""
import math
import os
import sys
import time
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'draft4'))
from edit import at,FPS,FRAMES

scene=bpy.context.scene
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.refresh_devices()
if not any(d.type=='METAL' for d in prefs.devices):raise RuntimeError('Metal device missing')
for d in prefs.devices:d.use=d.type=='METAL'
scene.render.engine='CYCLES';scene.cycles.device='GPU'
scene.cycles.samples=6;scene.cycles.adaptive_min_samples=3
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE'
scene.render.use_persistent_data=True;scene.render.image_settings.file_format='PNG'
scene.render.image_settings.compression=8;scene.render.image_settings.color_mode='RGB'
frames=Path(os.getenv('ASTRA5_PLATES',str(HERE/'renders')));frames.mkdir(parents=True,exist_ok=True)
selected=os.getenv('RENDER_FRAMES')
sequence=[int(f) for f in selected.split(',')] if selected else range(1,FRAMES+1)
for f in sequence:
    dst=frames/f'f_{f:04}.png'
    if dst.exists():continue
    shot,src=at((f-1)/FPS)
    if shot in ('anaesthesia','socket','closure') or (shot=='access' and src<9.84):
        dst.symlink_to(Path('../../draft4/renders')/dst.name)
        continue
    frame=1+src*FPS
    scene.frame_set(math.floor(frame),subframe=frame%1)
    scene.camera=bpy.data.objects['Macro '+shot]
    scene.render.filepath=str(frames/'working.png')
    begin=time.monotonic()
    bpy.ops.render.render(write_still=True)
    Path(scene.render.filepath).replace(dst)
    print(f'FRAME {f} {shot} {time.monotonic()-begin:.2f}s',flush=True)
