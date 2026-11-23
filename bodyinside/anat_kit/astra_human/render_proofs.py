"""Render the three delivery frames in Blender. Pass -- --draft for a 4 spp quarter-size check."""
from pathlib import Path
import sys
import bpy

folder=Path(__file__).resolve().parent
if Path(bpy.data.filepath)!=folder/'human_final.blend':
    bpy.ops.wm.open_mainfile(filepath=str(folder/'human_final.blend'))
scene=bpy.context.scene
draft='--draft' in sys.argv
scene.render.engine='CYCLES'
scene.cycles.samples=4 if draft else 32
scene.cycles.use_adaptive_sampling=False
scene.cycles.use_denoising=True
scene.cycles.denoiser='OPENIMAGEDENOISE'
scene.cycles.denoising_use_gpu=False
scene.render.resolution_x,scene.render.resolution_y=1080,880
scene.render.resolution_percentage=25 if draft else 100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
output=folder/'.build' if draft else folder
output.mkdir(exist_ok=True)
for name,frame in [('open',31),('payoff',85),('neutral',115)]:
    scene.frame_set(frame)
    scene.render.filepath=str(output/(('draft_' if draft else 'proof_')+name+'.png'))
    bpy.ops.render.render(write_still=True)
