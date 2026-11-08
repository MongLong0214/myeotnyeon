import sys, bpy, math
sys.path.insert(0, 'production/blender')
import importlib, world2 as W, people as P
from mathutils import Vector
arm_pole, leg_pole = float(sys.argv[-2]), float(sys.argv[-1])
W.reset(samples=8); W.world(haze=0.0, strength=0.6)
W.plane('floor', (30, 30), (0, 0, 0), W.mat('fl', (0.3, 0.3, 0.3), rough=0.8))
s = bpy.context.scene; s.render.resolution_x, s.render.resolution_y = 1600, 600; s.eevee.use_raytracing = False
W.light('AREA', 'key', (3, -4, 5), 1500, size=(3, 3), rot=(math.radians(45), 0, math.radians(35)))
names = ['stand', 'stop', 'step_back', 'ground', 'drive']
for i, pn in enumerate(names):
    r = P.load('B' if pn != 'drive' else 'A', f'fig_{pn}')
    T = P.add_ik(r, arm_pole, leg_pole)
    P.place(r, (i * 1.1 - 2.2, 0, 0), 0)
    P.ik_pose(r, T, pn)
cd = bpy.data.cameras.new('c'); cd.lens = 28; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
for tag, loc in (('front', (0, -6.0, 1.0)), ('side', (-6.5, -2.2, 0.9))):
    co.location = loc; co.rotation_euler = (Vector((0 if tag == 'front' else -0.5, 0, 0.75)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'//test2/ik_{tag}.png'; bpy.ops.render.render(write_still=True)
