"""third_molar_v3: v2 body (roots, neck, walls, bbox) with a carved occlusal table.  v2's pits are plugged, then everything above a height field
is cut away with a boolean (so the table is exactly the field, rim included), voxel remesh + smooth.  The height field is
built from five low pyramidal cusps (MB, DB, D, ML, DL), each a ridge segment from the tip down into the central groove (triangular ridge,
V-shaped sides), plus mesial/distal marginal ridges, joined with a log-sum-exp smooth max so valleys are rounded and nothing creases.
The walls, cervical neck and roots are the v2 ones.
Frame as v2: crown +z, root -z, buccal +x, distal +y, metres.  usage: Blender -b --factory-startup -P make_third_molar_v3.py
-> anat_kit/assets/third_molar_v3.blend (object ThirdMolarAsset)"""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(os.path.dirname(HERE), 'assets')
with bpy.data.libraries.load(os.path.join(ASSETS, 'third_molar_v2.blend')) as (src, dst): dst.objects = ['ThirdMolarAsset']
ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob); me = ob.data
import bmesh
v2 = np.array([v.co[:] for v in me.vertices]) * 1000.0; bb0 = (v2.min(0), v2.max(0))
def field(x, y):
    # ridge segments: (x0,y0,h0) tip -> (x1,y1,h1) groove end, side slope (mm of drop per mm sideways)
    G = 3.7
    R = [  # cusp tip ridges, buccal row x>0, lingual row x<0
     ((2.9, -3.0, 6.9), (0.3, -3.0, G + .2), 1.05),   # mesiobuccal (largest)
     ((2.9,  0.9, 6.6), (0.3,  0.7, G), 1.05),        # distobuccal
     ((1.9,  3.9, 5.9), (0.2,  2.9, G + .5), 1.05),   # distal (fifth)
     ((-2.9, -2.6, 6.8), (-0.3, -2.7, G + .2), 1.05), # mesiolingual
     ((-2.6,  1.7, 6.4), (-0.3, 1.3, G), 1.05),       # distolingual
     ((2.2, -4.4, 6.2), (-2.2, -4.4, 6.1), 1.0),     # mesial marginal ridge
     ((-1.8, 4.4, 5.7), (1.0, 4.7, 5.5), 1.0),       # distal marginal ridge
    ]
    H = []
    for (a, b, s) in R:
        A = np.array(a); B = np.array(b); d = B[:2] - A[:2]; L2 = d @ d
        t = np.clip(((x - A[0]) * d[0] + (y - A[1]) * d[1]) / L2, 0, 1)
        px = A[0] + t * d[0]; py = A[1] + t * d[1]; ph = A[2] + t * (B[2] - A[2])
        dist = np.hypot(x - px, y - py)
        dist = np.sqrt(dist ** 2 + 0.35 ** 2) - 0.35                                         # blunt, not needle, tip
        H.append(ph - s * dist)
    H = np.array(H); k = 0.2
    Hs = k * np.log(np.exp((H - H.max(0)) / k).sum(0)) + H.max(0)
    Hs -= k * 0.5                                                                           # undo most of the smooth-max lift in valleys

    Hs += 0.05 * np.sin(x * 2.3 + y * 1.1) * np.sin(y * 2.7 - x * 0.9)
    return Hs
# plug the v2 pits with an inner block, then cut away everything above the field
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = ((v.co.x * 7.2) / 1000, (v.co.y * 6.8 - 0.3) / 1000, (3.0 + (v.co.z + 0.5) * 3.2) / 1000)
fm = bpy.data.meshes.new('plug'); bm.to_mesh(fm); bm.free(); fo = bpy.data.objects.new('plug', fm); bpy.context.scene.collection.objects.link(fo)
g = np.arange(-7.0, 7.0001, 0.1); N = len(g); X, Y = np.meshgrid(g, g, indexing='ij')
Hc = np.maximum(field(X, Y), 3.0 + 2.2 * (lambda t: t * t * (3 - 2 * t))(np.clip((np.hypot(X / 5.2, Y / 5.0) - 0.62) / 0.33, 0, 1)))   # rim floor only near the outline
vb = np.stack([X, Y, Hc], -1).reshape(-1, 3); vt = np.stack([X, Y, np.full_like(X, 9.0)], -1).reshape(-1, 3)
idx = lambda i, j: i * N + j
F = []
for i in range(N - 1):
    for j in range(N - 1):
        q = (idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)); F.append(q); F.append(tuple(N * N + t for t in q[::-1]))
for i in range(N - 1):
    for (j, flip) in ((0, 0), (N - 1, 1)):
        a_, b_ = idx(i, j), idx(i + 1, j); q = (a_, b_, N * N + b_, N * N + a_); F.append(q[::-1] if flip else q)
        a_, b_ = idx(j, i), idx(j, i + 1); q = (a_, b_, N * N + b_, N * N + a_); F.append(q if flip else q[::-1])
cm = bpy.data.meshes.new('cut'); cm.from_pydata((np.vstack([vb, vt]) / 1000).tolist(), [], F); cm.update()
bm = bmesh.new(); bm.from_mesh(cm); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-9); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(cm); bm.free()
co_ = bpy.data.objects.new('cut', cm); bpy.context.scene.collection.objects.link(co_)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
for name, other, op in (('u', fo, 'UNION'), ('d', co_, 'DIFFERENCE')):
    m = ob.modifiers.new(name, 'BOOLEAN'); m.operation = op; m.object = other; m.solver = 'EXACT'; bpy.ops.object.modifier_apply(modifier=name)
bpy.data.objects.remove(fo); bpy.data.objects.remove(co_)
rm = ob.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.0001; rm.use_smooth_shade = True; bpy.ops.object.modifier_apply(modifier='rm')
sm = ob.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 14; bpy.ops.object.modifier_apply(modifier='sm')
bm = bmesh.new(); bm.from_mesh(me); seen = set(); parts = []
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; seen.add(f.index); comp = []
    while st:
        g_ = st.pop(); comp.append(g_)
        for e in g_.edges:
            for h in e.link_faces:
                if h.index not in seen: seen.add(h.index); st.append(h)
    parts.append(comp)
parts.sort(key=len, reverse=True); bmesh.ops.delete(bm, geom=[f for c in parts[1:] for f in c], context='FACES'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
ob.name = 'ThirdMolarAsset'; me.name = 'ThirdMolarAsset'
a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); a = a.reshape(-1, 3) * 1000
print('v2 bbox', bb0[0].round(2), bb0[1].round(2)); print('v3 bbox', a.min(0).round(2), a.max(0).round(2))
print('ext ratio', ((a.max(0) - a.min(0)) / (bb0[1] - bb0[0])).round(4), 'verts', len(a))
out = os.path.join(ASSETS, 'third_molar_v3.blend'); bpy.data.libraries.write(out, {ob}, fake_user=True); print('ASSET', out)
