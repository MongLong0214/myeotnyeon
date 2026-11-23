"""Render continuous subframe motion from the source-scene clock onto the edited clock."""
import bpy
import math
import os
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from edit import FPS,FRAMES,at

s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.refresh_devices()
if not any(d.type=='METAL' for d in prefs.devices):raise RuntimeError('Metal device missing')
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.render.engine='CYCLES'
s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.cycles.adaptive_min_samples=4;s.cycles.adaptive_threshold=.085
s.render.use_persistent_data=True
s.render.image_settings.file_format='PNG';s.render.image_settings.compression=9
s.render.image_settings.color_depth='8';s.render.image_settings.color_mode='RGB'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
proof=args and args[0]=='proof'
out=Path(os.environ.get('ASTRA4_FRAMES',str(HERE/'renders')))
if proof:out=out/'proof'
out.mkdir(parents=True,exist_ok=True)
frames=[round(float(t)*FPS)+1 for t in args[1:]] if proof else range(1,FRAMES+1)
# Camera-bound source markers would otherwise override the editorial angle inside render().
for marker in list(s.timeline_markers):s.timeline_markers.remove(marker)
for f in frames:
    target=out/f'f_{f:04d}.png'
    if not proof and target.exists():continue
    shot,src=at((f-1)/FPS)
    source=1+src*FPS;whole=math.floor(source)
    s.frame_set(whole,subframe=source-whole);s.camera=bpy.data.objects['Macro '+shot]
    s.cycles.samples=12 if shot in ('fracture','socket','closure','specimen') else 9
    s.render.filepath=str(target.with_name('working.png'))
    started=time.monotonic()
    bpy.ops.render.render(write_still=True)
    Path(s.render.filepath).replace(target)
    print(f'FRAME {f:04d} {shot} {src:.3f} {time.monotonic()-started:.2f}s',flush=True)
