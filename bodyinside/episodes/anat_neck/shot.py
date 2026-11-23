# one still with a free camera. usage: Blender -b neck.blend -P shot.py -- out.png frame cx cy cz dx dy dz dist [spp] [pct]
import sys; sys.path.insert(0, (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/blender'))
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; sc = bpy.context.scene
out, f = a[0], int(a[1]); c = Vector(tuple(float(v) for v in a[2:5])); d = Vector(tuple(float(v) for v in a[5:8])).normalized(); dist = float(a[8])
spp = int(a[9]) if len(a) > 9 else 24; pct = int(a[10]) if len(a) > 10 else 50
cam = sc.camera; cam.animation_data_clear(); cam.location = c + d * dist; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (c - cam.location).to_track_quat('-Z', 'Y')
fo = bpy.data.objects[cam.name + '_focus']; fo.animation_data_clear(); fo.location = c
sc.cycles.samples = spp; sc.render.resolution_percentage = pct; sc.render.use_motion_blur = False; sc.render.filepath = out
p = bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type = 'METAL'; p.get_devices()
for dv in p.devices: dv.use = (dv.type == 'METAL')
sc.frame_set(f); bpy.ops.render.render(write_still=True)
