# Cycles preview of the current scene from the -X side. usage: Blender -b X.blend -P prev.py -- out.png cx cy cz dist [azimuth_deg elev_deg lens spp]
import sys; sys.path.insert(0, (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/blender'))
import bpy, math
from kit import *
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; c = Vector(tuple(float(v) for v in a[1:4])); dist = float(a[4])
az = math.radians(float(a[5])) if len(a) > 5 else 0; el = math.radians(float(a[6])) if len(a) > 6 else 0; lens = float(a[7]) if len(a) > 7 else 85; spp = int(a[8]) if len(a) > 8 else 32
mB, gB, eB = bone_material('BoneP')
for o in D.objects:
    if o.type == 'MESH' and not any(m for m in o.data.materials if m): o.data.materials.append(mB)
d = Vector((-math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
cam = CameraPath(lens=lens, fstop=16); cam.key(0, c, -d * -1, dist)
cam.cam.location = c + d * dist; cam.cam.rotation_quaternion = (c - cam.cam.location).to_track_quat('-Z', 'Y')
light_rig(c, hdri=True, hdri_strength=0.3); render_settings(1080, 800, spp=spp, blur=0)
sc = bpy.context.scene; sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.6; sc.render.film_transparent = False
sc.render.resolution_percentage = 50; sc.render.filepath = out; sc.render.use_motion_blur = False
cy = sc.cycles; cy.use_adaptive_sampling = True
p = bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type = 'METAL'; p.get_devices()
for dv in p.devices: dv.use = (dv.type == 'METAL')
sc.frame_set(1); bpy.ops.render.render(write_still=True)
