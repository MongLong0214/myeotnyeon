import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parent))
from split_screen import PAYOFF_DRIFT_START, PAYOFF_DRIFT_END, key_payoff_drift, payoff_drift_pixels

scene = bpy.context.scene
camera = scene.camera
labels = json.loads((stage / 'label_pos.json').read_text())
old = {}
for frame in range(PAYOFF_DRIFT_START, PAYOFF_DRIFT_END + 1):
    scene.frame_set(frame)
    old[frame] = {name: world_to_camera_view(scene, camera, bpy.data.objects[name].matrix_world.translation)
                  for name in labels[str(frame)]}

key_payoff_drift(scene)
for frame in old:
    scene.frame_set(frame)
    dx, dy = payoff_drift_pixels(frame)
    for name, baseline in old[frame].items():
        new = world_to_camera_view(scene, camera, bpy.data.objects[name].matrix_world.translation)
        assert abs((new.x - baseline.x) * scene.render.resolution_x - dx) < 0.002
        assert abs((baseline.y - new.y) * scene.render.resolution_y - dy) < 0.002
        if PAYOFF_DRIFT_START < frame < PAYOFF_DRIFT_END:
            loc = labels[str(frame)][name]
            assert max(abs(loc[0] - baseline.x), abs(loc[1] - (1 - baseline.y))) < 0.0001
            labels[str(frame)][name] = [round(new.x, 4), round(1 - new.y, 4)]
(stage / 'payoff_label_pos.json').write_text(json.dumps(labels))
scene.frame_set(PAYOFF_DRIFT_START + 1)
bpy.ops.wm.save_as_mainfile(filepath=str(stage/'neck_payoff_v3b.blend'))
