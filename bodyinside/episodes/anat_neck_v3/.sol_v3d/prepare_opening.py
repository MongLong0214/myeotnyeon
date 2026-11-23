from pathlib import Path
import bpy

scene = bpy.context.scene
human = set(bpy.data.collections['Human | character'].all_objects)
anatomy = [obj for obj in scene.objects if obj not in human and obj.type in {'MESH', 'CURVE', 'CURVES'}]
last_opaque = 60
scene.frame_set(last_opaque + 1)
resume = {obj: obj.hide_render for obj in anatomy}
for frame in range(last_opaque + 1):
    for obj in anatomy:
        obj.hide_render = True
        obj.keyframe_insert(data_path='hide_render', frame=frame)
for obj, hidden in resume.items():
    obj.hide_render = hidden
    obj.keyframe_insert(data_path='hide_render', frame=last_opaque + 1)
for frame in range(last_opaque + 1):
    scene.frame_set(frame)
    assert all(obj.hide_render for obj in anatomy), frame
scene.frame_set(last_opaque + 1)
assert all(obj.hide_render == hidden for obj, hidden in resume.items())
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).resolve().parent / 'neck.blend'), relative_remap=False)
