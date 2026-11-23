from pathlib import Path
import bpy
import json
import math
from mathutils import Quaternion, Vector
import sys

stage = Path(sys.argv[-1])
scene = bpy.context.scene
camera = scene.camera
focus = camera.data.dof.focus_object
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'

def angles_through_opening():
    angles = {}
    for f in range(300):
        scene.frame_set(f)
        angles[f] = tuple(camera.location) + tuple(camera.rotation_quaternion) + tuple(focus.location)
    return angles

before = angles_through_opening()
for f in (320, 543, 713):
    for obj, prop in ((camera, 'location'), (camera, 'rotation_quaternion'), (focus, 'location')):
        obj.keyframe_delete(prop, frame=f)

# Camera keys used by the 10:19 draft4 render, recovered from its build command.
keys = (
    (320, (-0.006, 0.0, 1.52), 0, 1.12),
    (420, (-0.006, 0.004, 1.51), 4, 0.97),
    (543, (-0.008, 0.0, 1.515), 1, 1.00),
    (640, (-0.006, -0.004, 1.52), -4, 1.05),
    (713, (-0.006, 0.0, 1.52), -1, 1.10),
)
for f, target, azimuth, distance in keys:
    az = math.radians(azimuth)
    direction = Vector((-math.cos(az), math.sin(az), 0.0))
    target = Vector(target)
    location = target + direction.normalized() * distance
    rotation = (target - location).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), 0.0)
    camera.location = location
    camera.rotation_quaternion = rotation
    focus.location = target
    camera.keyframe_insert('location', frame=f)
    camera.keyframe_insert('rotation_quaternion', frame=f)
    focus.keyframe_insert('location', frame=f)

after = angles_through_opening()
deltas = {f: max(abs(x - y) for x, y in zip(before[f], after[f])) for f in after}
with (stage / 'restored_camera_deltas.json').open('w') as f:
    json.dump(deltas, f)
print('Largest difference up to f210:', max(deltas[f] for f in range(211)))
print('First changed frame:', min(f for f, x in deltas.items() if x > 1e-6))
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'opening_draft4.blend'), relative_remap=False)
