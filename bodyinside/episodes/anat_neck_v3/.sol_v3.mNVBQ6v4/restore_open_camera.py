from pathlib import Path
import bpy
import sys

stage = Path(sys.argv[-1])
episode = stage.parent
previous = episode.parent / 'anat_neck/neck.blend'
s = bpy.context.scene
poses = {}
for f in range(211, 300):
    s.frame_set(f)
    camera = s.camera
    poses[f] = camera.location.copy(), camera.rotation_quaternion.copy(), camera.data.dof.focus_object.location.copy(), camera.data.lens
assert Path(bpy.data.filepath) == previous
bpy.ops.wm.open_mainfile(filepath=str(episode / 'neck.blend1'))
s = bpy.context.scene
camera = s.camera
focus = camera.data.dof.focus_object
for f, (pos, rot, target, lens) in poses.items():
    camera.location, camera.rotation_quaternion, focus.location, camera.data.lens = pos, rot, target, lens
    camera.keyframe_insert(data_path='location', frame=f)
    camera.keyframe_insert(data_path='rotation_quaternion', frame=f)
    focus.keyframe_insert(data_path='location', frame=f)
    camera.data.keyframe_insert(data_path='lens', frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'opening_approved.blend'), relative_remap=False)
