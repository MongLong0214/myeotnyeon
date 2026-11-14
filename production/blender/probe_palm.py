import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, '/Users/isaac/projects/verdict-kr/work/production/blender')
import world2 as W, people as P
W.reset(samples=8); s = bpy.context.scene; s.eevee.use_raytracing = False; s.render.resolution_x = s.render.resolution_y = 600
W.world(haze=0.0, strength=0.6); W.plane('floor', (20, 20), (0, 0, 0), W.mat('fl', (0.35, 0.35, 0.36), rough=0.8))
L = W.light('AREA', 'L', (0, -3, 3), 700, size=(3, 3)); L.rotation_euler = (Vector((0, 0, 1.3)) - L.location).to_track_quat('-Z', 'Y').to_euler()
cands = {'+x': (1, 0, 0), '-x': (-1, 0, 0), '+z': (0, 0, 1), '-z': (0, 0, -1)}
for i, (k, ax) in enumerate(cands.items()):
    r = P.load('B', f'f{i}'); T = P.add_ik(r); P.place(r, (i * 1.6, 0, 0), 0); P.ik_pose(r, T, 'stop')
    # orientation empty in rig space: bone Y → up(+Z), palm candidate axis → forward (-Y)
    y = Vector((0, 0, 1)); n = Vector((0, -1, 0))
    m = {}
    if k in ('+x', '-x'):
        xa = n if k == '+x' else -n; za = xa.cross(y)
        M = Matrix((xa, y, za)).transposed()
    else:
        za = n if k == '+z' else -n; xa = y.cross(za)
        M = Matrix((xa, y, za)).transposed()
    e = bpy.data.objects.new(f'ori{i}', None); s.collection.objects.link(e); e.parent = r; e.matrix_parent_inverse.identity()
    e.matrix_basis = M.to_4x4()
    c = r.pose.bones['RightHand'].constraints.new('COPY_ROTATION'); c.target = e
cd = bpy.data.cameras.new('c'); cd.lens = 60; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
bpy.context.view_layer.update()
for i in range(4):
    hp = r.matrix_world @ r.pose.bones['RightHand'].head if False else None
for i, k in enumerate(cands):
    rig = bpy.data.objects[f'f{i}']
    hp = rig.matrix_world @ rig.pose.bones['RightHand'].tail
    co.location = hp + Vector((0.15, -1.1, 0.1)); co.rotation_euler = (hp - co.location).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'//figqa/palm_{k.replace("+", "p").replace("-", "m")}.png'; bpy.ops.render.render(write_still=True)
