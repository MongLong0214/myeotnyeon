from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parent))
from split_screen import LOWER_SPINE_HIDE, SPLIT_END, drift_pixels, key_camera_drift

side = sys.argv[-1]
scene = bpy.context.scene
bones = [
    obj for obj in bpy.data.objects
    if obj.type in ('MESH', 'CURVE') and obj.name.startswith(('Vertebra T', 'Rim_Vertebra_T'))
]
assert bones and len(bones) % 2 == 0
old_hide_frame = 710
for frame in (709, old_hide_frame, SPLIT_END, LOWER_SPINE_HIDE):
    scene.frame_set(frame)
    assert all(obj.hide_render == (frame >= old_hide_frame) for obj in bones)

landmark = bpy.data.objects['A_Ear']
def projected(frame):
    scene.frame_set(frame)
    return world_to_camera_view(scene, scene.camera, landmark.matrix_world.translation)
frames = (299, 300, 301, 335, 367, 542, 660, 700, 713, 714)
original = {frame: projected(frame) for frame in frames}

key_camera_drift(scene)
for frame in range(old_hide_frame, LOWER_SPINE_HIDE):
    scene.frame_set(frame)
    for obj in bones:
        obj.hide_render = False
        obj.keyframe_insert('hide_render', frame=frame)

for frame in (709, 710, 711, 712, 713, 714, 720, 878, 879):
    scene.frame_set(frame)
    assert all(obj.hide_render == (714 <= frame < 879) for obj in bones), frame
for frame in frames:
    new = projected(frame)
    baseline = original[frame]
    offset = ((new.x - baseline.x) * scene.render.resolution_x,
              (baseline.y - new.y) * scene.render.resolution_y)
    assert max(abs(a - b) for a, b in zip(offset, drift_pixels(frame))) < 0.002, (frame, offset, drift_pixels(frame))

# Each variant supplies just one half; keep a denoising margin across the seam.
scene.render.use_border = True
scene.render.use_crop_to_border = False
scene.render.border_min_x = 0.0 if side == 'A' else 0.45
scene.render.border_max_x = 0.55 if side == 'A' else 1.0
scene.render.border_min_y = 0.0
scene.render.border_max_y = 1.0
scene.frame_set(700)
bpy.ops.wm.save_as_mainfile(filepath=str(stage / f'neck_{side}_v3b.blend'))
print(f'Verified {len(bones)} thoracic meshes/rims, matched camera projection, saved variant {side}')
