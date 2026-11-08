import sys, bpy, math
sys.path.insert(0, 'production/blender')
import world2 as W, people as P
from mathutils import Vector
W.reset(samples=8); W.world(haze=0.0, strength=0.6)
W.plane('floor', (30, 30), (0, 0, 0), W.mat('fl', (0.3, 0.3, 0.3), rough=0.8))
s = bpy.context.scene; s.render.resolution_x, s.render.resolution_y = 1600, 600; s.eevee.use_raytracing = False
W.light('AREA', 'key', (3, -4, 5), 1500, size=(3, 3), rot=(math.radians(45), 0, math.radians(35)))
for i, (k, pn) in enumerate((('B', 'stand'), ('B', 'stop'), ('B', 'step_back'), ('A', 'stand'))):
    r = P.load(k, f'f{i}'); T = P.add_ik(r); P.place(r, (i * 0.8 - 1.2, 0, 0), 0); P.ik_pose(r, T, pn)
cd = bpy.data.cameras.new('c'); cd.lens = 50; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (0, -4.2, 1.5); co.rotation_euler = (Vector((0, 0, 1.2)) - co.location).to_track_quat('-Z', 'Y').to_euler()
s.render.filepath = '//test2/face.png'; bpy.ops.render.render(write_still=True)
