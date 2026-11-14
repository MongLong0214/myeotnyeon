import sys, time, bpy, math
sys.path.insert(0, '/Users/isaac/projects/verdict-kr/work/production/blender')
import world2 as W
from mathutils import Vector
t0 = time.time()
W.reset(samples=32); W.build_lot()
W.parked_cars()
hero = W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=True, tag='car_A')
print('BUILD', round(time.time() - t0, 1), 's', len(bpy.data.objects), 'objects', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)//1000, 'k faces')
def cam(loc, tgt, lens, fn):
    cd = bpy.data.cameras.new('c'); cd.lens = lens; co = bpy.data.objects.new('c', cd); bpy.context.scene.collection.objects.link(co)
    co.location = loc; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = co; bpy.context.scene.render.filepath = fn
    t = time.time(); bpy.ops.render.render(write_still=True); print('RENDER', fn, round(time.time() - t, 1), 's')
cam((6.5, -5.5, 1.5), (-3, 0.3, 0.9), 35, '//test2/cars_34.png')
cam((1.2, -5.4, 1.7), (-0.5, 1.0, 1.0), 28, '//test2/cars_side.png')
cam((14, -16, 9), (-2, 2, 0), 30, '//test2/cars_high.png')
