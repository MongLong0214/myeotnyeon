import sys, time, bpy, math
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(); W.build_lot(); W.parked_cars()
hero = W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=True, tag='car_A')
s = bpy.context.scene; e = s.eevee
print('FACES', sum(len(o.data.polygons) for o in s.objects if o.type == 'MESH' and not o.hide_render) // 1000, 'k')
cd = bpy.data.cameras.new('c'); cd.lens = 35; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (6.5, -5.5, 1.5); co.rotation_euler = (Vector((-3, 0.3, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
def r(tag):
    s.render.filepath = f'//test2/prof2_{tag}.png'; t = time.time(); bpy.ops.render.render(write_still=True); print('PROF', tag, round(time.time() - t, 1), flush=True)
r('warmup'); r('opt2')
e.taa_render_samples = 16; r('opt2_s16')
