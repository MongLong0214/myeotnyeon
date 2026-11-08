import sys, time, bpy, math
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
t0 = time.time()
W.reset(samples=32); W.build_lot()
print('BUILD', round(time.time() - t0, 1), 's', len(bpy.data.objects), 'objects')
def cam(loc, tgt, lens, fn):
    cd = bpy.data.cameras.new('c'); cd.lens = lens; co = bpy.data.objects.new('c', cd); bpy.context.scene.collection.objects.link(co)
    co.location = loc; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = co; bpy.context.scene.render.filepath = fn
    t = time.time(); bpy.ops.render.render(write_still=True); print('RENDER', fn, round(time.time() - t, 1), 's')
cam((12, -13, 2.2), (-2, 6, 3.5), 28, '//test2/wide.png')
cam((-1, -6, 1.6), (0, 12, 1.8), 35, '//test2/ground.png')
cam((20, -30, 22), (0, 8, 4), 32, '//test2/aerial.png')
