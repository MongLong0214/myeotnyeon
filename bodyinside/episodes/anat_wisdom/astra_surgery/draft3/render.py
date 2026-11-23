"""Render the local draft or representative macro proofs, on one Metal device."""
import bpy
import os
import sys
import time
from pathlib import Path
s=bpy.context.scene
root=Path(os.environ.get('ASTRA_RENDER_WORK','/tmp/astra3check'))
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.refresh_devices()
devices=[d for d in prefs.devices if d.type=='METAL']
if not devices:raise RuntimeError('No Metal device available')
for dev in prefs.devices:dev.use=dev.type=='METAL'
s.cycles.device='GPU'
s.render.engine='CYCLES'
s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
s.cycles.adaptive_threshold=.074
s.cycles.adaptive_min_samples=4
s.render.use_persistent_data=True
s.render.image_settings.file_format='PNG'
s.render.image_settings.compression=12
s.render.image_settings.color_depth='8';s.render.image_settings.color_mode='RGB'
s.render.resolution_percentage=100
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'movie'
picks=(32,126,236,310,482,620,704,775,863)
if mode=='proof':
    s.render.resolution_x,s.render.resolution_y=1080,1920
    s.cycles.samples=22
    picks=(310,704)
if mode=='range':
    first,last=map(int,args[1:])
    frames=range(first,last+1)
else:
    frames=[int(n) for n in args[1:]] or (list(range(1,881)) if mode=='movie' else picks)
out=Path(__file__).resolve().parent/'renders' if mode=='movie' else root/mode
out.mkdir(parents=True,exist_ok=True)
for f in frames:
    dest=out/f'f_{f:04d}.png'
    if mode=='movie' and dest.exists():continue
    s.frame_set(f)
    if mode!='proof':
        hero=(379<=f<=505 or 670<=f<=728 or 749<=f<=790)
        s.cycles.samples=int(os.environ.get('ASTRA_HERO' if hero else 'ASTRA_BASE',16 if hero else 12))
    s.render.filepath=str(dest)
    start=time.monotonic()
    bpy.ops.render.render(write_still=True)
    print('RENDERED',f,s.cycles.samples,round(time.monotonic()-start,2),flush=True)
