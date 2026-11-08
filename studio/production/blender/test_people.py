import sys, bpy, math
sys.path.insert(0, 'production/blender')
import world2 as W, people as P
from mathutils import Vector
W.reset(); W.world(haze=0.0, strength=1.0)
fl = W.plane('floor', (30, 30), (0, 0, 0), W.mat('fl', (0.3, 0.3, 0.3), rough=0.8))
s = bpy.context.scene
W.light('AREA', 'key', (3, -4, 5), 1500, size=(3, 3), rot=(math.radians(45), 0, math.radians(35)))
W.light('AREA', 'rim', (-3, 3, 4), 600, size=(2, 2), rot=(math.radians(-45), 0, math.radians(-140)))
names = ['stand', 'stop', 'lean_back', 'ground', 'drive']
for i, pn in enumerate(names):
    r = P.load('B' if pn != 'drive' else 'A', f'fig_{pn}')
    P.place(r, (i * 1.3 - 2.6, 0, 0), 0)
    P.pose(r, pn)
cd = bpy.data.cameras.new('c'); cd.lens = 32; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
for tag, loc in (('front', (0, -7.5, 1.3)), ('side', (-7.5, -1.5, 1.2))):
    co.location = loc; co.rotation_euler = (Vector((0, 0, 0.8)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'//test2/people_{tag}.png'; bpy.ops.render.render(write_still=True)
