"""Reframe the v1 disc asset on a neutral cervical model for the v4 anatomy chapter."""
import json
import math
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / 'anat_kit' / 'blender'))
from kit import CameraPath

scene = bpy.context.scene
objects = bpy.data.objects
scene.frame_set(630)
bulge = objects['Herniation']
full_scale = bulge.scale.copy()
shape_peaks = {
    key.name: key.value
    for key in objects['Disc_C5C6'].data.shape_keys.key_blocks
    if key.value > 0
}
objects['SkelRoot'].animation_data_clear()
objects['SkelRoot'].location = (0, 0, 0)
objects['SkelRoot'].rotation_quaternion = (1, 0, 0, 0)
neutral = (-4, -5, -6, -5, -4, -3, 10, 17)
for i, angle in enumerate(neutral):
    joint = objects[f'J{i}']
    joint.animation_data_clear()
    joint.rotation_euler = (math.radians(angle), 0, 0)

# The new model shows the cervical column and root anatomy in isolation.
visible_prefixes = (
    'Vertebra ', 'Atlas (C1)', 'Axis (C2)', 'Rim_Vertebra_', 'Rim_Atlas_',
    'Rim_Axis_', 'Disc_', 'SpinalRoots', 'SpinalGanglia', 'Herniation',
)
for obj in scene.objects:
    if obj.type in {'MESH', 'CURVE', 'CURVES'}:
        obj.animation_data_clear()
        obj.hide_render = not obj.name.startswith(visible_prefixes)
        if obj.type == 'MESH' and obj.data.shape_keys:
            obj.data.shape_keys.animation_data_clear()
            for key in obj.data.shape_keys.key_blocks:
                key.value = 0

# Keep the protrusion contiguous with the annulus as it moves toward the root.
for f, amount in ((0, 0.001), (119, 0.001), (160, 0.83), (194, 1.0), (336, 1.0)):
    bulge.scale = full_scale * amount
    bulge.keyframe_insert('scale', frame=f)
    for name, peak in shape_peaks.items():
        key = objects['Disc_C5C6'].data.shape_keys.key_blocks[name]
        key.value = peak * amount
        key.keyframe_insert('value', frame=f)

for obj in scene.objects:
    if obj.type == 'MESH' and not obj.hide_render:
        for material in obj.data.materials:
            if material and material.node_tree:
                material.node_tree.animation_data_clear()

root_shader = bpy.data.materials['RootMat'].node_tree
for node in root_shader.nodes:
    if node.type == 'VALUE':
        node.outputs[0].default_value = 0.0
root_shader.animation_data_clear()
scene.animation_data_clear()
scene.timeline_markers.clear()
scene.view_settings.exposure = -0.86
scene.frame_start, scene.frame_end = 0, 336
scene.render.use_motion_blur = False
scene.render.resolution_percentage = 100
scene.cycles.samples = 64
scene.render.use_persistent_data = True
if 'spp_boost' in scene:
    del scene['spp_boost']

bpy.context.view_layer.update()
contact = objects['A_Contact'].matrix_world.translation.copy()
disc = objects['A_C56'].matrix_world.translation.copy()
cam = CameraPath(name='V4 neutral anatomy', lens=68, fstop=24)
cam.cam.data.dof.use_dof = False
# Wide neutral section, identify the disc, contact close-up, then wider anatomy context.
for f, direction, distance, z, y in (
    (0, 0.38, 0.326, 0.010, -0.002),
    (45, 0.19, 0.291, 0.009, -0.003),
    (93, 0.09, 0.24, 0.004, -0.003),
    (139, 0.15, 0.20, 0.001, -0.004),
    (185, 0.27, 0.165, 0.000, 0.002),
    (230, 0.39, 0.185, 0.003, 0.004),
    (276, 0.23, 0.235, 0.005, -0.001),
    (320, 0.08, 0.292, 0.008, -0.005),
    (336, 0.05, 0.318, 0.010, -0.005),
):
    cam.key(f, disc + Vector((0, y, z)), (-1, direction, 0.07), distance)

anchors, amount_by_frame = {}, {}
for f in range(scene.frame_end + 1):
    scene.frame_set(f)
    anchors[f] = {}
    for name in ('A_C56', 'A_Root', 'A_Contact'):
        projected = world_to_camera_view(scene, cam.cam, objects[name].matrix_world.translation)
        anchors[f][name] = [projected.x, 1 - projected.y]
    amount_by_frame[f] = bulge.scale.y / full_scale.y
(ROOT / 'disc_projection.json').write_text(json.dumps(anchors))
(ROOT / 'disc_scale.json').write_text(json.dumps(amount_by_frame))
assert (objects['A_Contact'].matrix_world.translation - contact).length < 0.00001
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'disc.blend'), relative_remap=True)
