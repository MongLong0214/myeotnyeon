import sys, time, bpy
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(); W.build_lot(); W.parked_cars()
W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=True, tag='car_A')
for nm in W.CARS: print('BODY', nm, W.CARS[nm][6])
s = bpy.context.scene
cd = bpy.data.cameras.new('c'); cd.lens = 35; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
for tag, loc, tgt in (('q1', (5.2, -2.6, 1.3), (-3, 0.4, 0.8)), ('q2', (-9, -2.8, 1.6), (2, 0.5, 0.9))):
    co.location = loc; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'//test2/quick_{tag}.png'; t = time.time(); bpy.ops.render.render(write_still=True); print('R', tag, round(time.time() - t, 1))
