import sys, time, bpy, math
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(samples=32); W.build_lot(); W.parked_cars()
hero = W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=True, tag='car_A')
s = bpy.context.scene
cd = bpy.data.cameras.new('c'); cd.lens = 35; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (6.5, -5.5, 1.5); co.rotation_euler = (Vector((-3, 0.3, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
hero.keyframe_insert('location', frame=1); hero.location.x = -2.6; hero.keyframe_insert('location', frame=10)
s.frame_start, s.frame_end = 1, 10; s.render.filepath = '//test2/anim5_'
t = time.time(); bpy.ops.render.render(animation=True); print('ANIM10', round(time.time() - t, 1), 's')
