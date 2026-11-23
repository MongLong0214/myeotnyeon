"""(v2b: crown built from pyramids + ridges + grooves, roots from metaballs)
Builds a clean lower-left third molar from scratch (no copy of a Z-Anatomy tooth, no sculpt): metaball composition with smooth union
(4 cusp lobes + a small distal fifth, rounded crown, cervical constriction, two curved roots converging at the apex), a central and a buccal
fissure as smooth subtracts, then voxel remesh + smooth so there is no crease.  Frame matches third_molar_l.blend: crown +z, root -z,
buccal +x, distal +y, metres.  usage: Blender -b --factory-startup -P make_third_molar_v2.py -> anat_kit/assets/third_molar_v2.blend (object ThirdMolarAsset)"""
import bpy, math, os
from mathutils import Vector
THR = 0.6
def rad(a, s): return a / math.sqrt(1 - (THR / s) ** (1 / 3))   # element radius for a wanted visible radius a (single ball)
mb = bpy.data.metaballs.new('T3mb'); mb.threshold = THR; mb.resolution = 0.12; mb.render_resolution = 0.12
def ball(x, y, z, a, s=2.5, neg=False):
    e = mb.elements.new(type='BALL'); e.co = (x, y, z); e.radius = rad(a, s); e.stiffness = s; e.use_negative = neg
# neck only (the crown is built from primitives below)
ball(0, 0, -0.3, 3.7, 3.0); ball(0, 0, 0.5, 3.9, 3.0)
# two tapered roots, both curving distally (+y) by about 22 degrees, close together near the neck, converging toward the apex
zk = (-1.2, -3.2, -5.0, -6.7, -8.1, -9.0); ak = (2.5, 2.2, 1.8, 1.35, 0.85, 0.45)
def lerp_k(vals, t):
    f = t * (len(vals) - 1); i = min(int(f), len(vals) - 2); u = f - i; u = u * u * (3 - 2 * u); return vals[i] * (1 - u) + vals[i + 1] * u
NR = 26
for i in range(NR + 1):
    t = i / NR; sh = t ** 1.5
    ball(-0.6 * t * t, -1.7 + 3.6 * sh, lerp_k(zk, t), lerp_k(ak, t), 3.0)   # mesial root
    ball(-0.6 * t * t, 1.7 + 2.7 * sh, lerp_k(zk, t), lerp_k(ak, t), 3.0)    # distal root
ob = bpy.data.objects.new('T3mb', mb); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.convert(target='MESH'); t = bpy.context.active_object

import bmesh, random
from mathutils import Vector, Matrix
def prim(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o
def bool_op(target, cutter, op):
    m = target.modifiers.new('b', 'BOOLEAN'); m.operation = op; m.object = cutter; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier=m.name); bpy.data.objects.remove(cutter)
rnd = random.Random(4)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 5.5, v.co.y * 5.1, v.co.z * 2.5 + 2.4))   # crown body: a low dome, widest at the cervical bulge
crown = prim('crown', bm)
# cusps: low four-sided pyramids of unequal size on the shoulders
cusps = ((2.5, -2.3, 2.5, 2.3), (2.7, 2.1, 2.1, 2.0), (-2.6, -2.3, 2.3, 2.2), (-2.4, 2.1, 1.8, 1.8))   # x, y, base radius, height above the shoulder
tops = []
for x, y, r, h in cusps:
    b = bmesh.new(); bmesh.ops.create_cone(b, cap_ends=True, segments=4, radius1=r, radius2=0.12, depth=h)
    for v in b.verts: v.co = Vector((v.co.x, v.co.y, v.co.z + h / 2))
    rot = Matrix.Rotation(math.radians(45 + rnd.uniform(-12, 12)), 4, 'Z'); b.transform(rot) if hasattr(b, 'transform') else None
    for v in b.verts: v.co += Vector((x, y, 3.6))
    tops.append(Vector((x, y, 3.6 + h))); bool_op(crown, prim('cusp', b), 'UNION')
b = bmesh.new(); bmesh.ops.create_cone(b, cap_ends=True, segments=4, radius1=1.5, radius2=0.1, depth=1.3)   # small distal fifth cusp
for v in b.verts: v.co += Vector((0.2, 3.7, 3.6 + 0.65))
bool_op(crown, prim('cusp5', b), 'UNION')
# ridges from each cusp apex down into the central groove
for tp in tops:
    c = Vector((0.0, 0.0, 4.35)); d = c - tp; L = d.length
    b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts: v.co = Vector((v.co.x * 1.1, v.co.y * L, v.co.z * 0.9))
    q = Vector((0, 1, 0)).rotation_difference(d.normalized()); b.transform(q.to_matrix().to_4x4()); b.transform(Matrix.Translation((tp + c) / 2))
    bool_op(crown, prim('ridge', b), 'UNION')
# central groove (mesiodistal) and a buccal groove, cut as thin wedges
b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
for v in b.verts: v.co = Vector((v.co.x * 0.9, v.co.y * 9.0, v.co.z * 1.4 + 4.6))
bool_op(crown, prim('groove', b), 'DIFFERENCE')
b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
for v in b.verts: v.co = Vector((v.co.x * 7.0, v.co.y * 0.7, v.co.z * 1.0 + 4.3))
bool_op(crown, prim('groove2', b), 'DIFFERENCE')
# union with the roots (the metaball mesh), voxel remesh makes it one closed solid
bpy.ops.object.select_all(action='DESELECT'); t.select_set(True); crown.select_set(True); bpy.context.view_layer.objects.active = t
bpy.ops.object.join(); t = bpy.context.active_object
zs_ = [v.co.z for v in t.data.vertices]; xs_ = [v.co.x for v in t.data.vertices]; ys_ = [v.co.y for v in t.data.vertices]
print('RAW bbox mm', round(min(xs_), 2), round(max(xs_), 2), round(min(ys_), 2), round(max(ys_), 2), round(min(zs_), 2), round(max(zs_), 2), len(t.data.vertices))
# scale to metres, voxel remesh, smooth
t.scale = (0.001, 0.001, 0.001); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rm = t.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.00010; rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='rm')
sm = t.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 12; bpy.ops.object.modifier_apply(modifier='sm')
# drop any stray islands
import bmesh
bm = bmesh.new(); bm.from_mesh(t.data); seen = set(); parts = []
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; seen.add(f.index); comp = []
    while st:
        g = st.pop(); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: seen.add(h.index); st.append(h)
    parts.append(comp)
parts.sort(key=len, reverse=True)
bmesh.ops.delete(bm, geom=[f for c in parts[1:] for f in c], context='FACES'); bm.to_mesh(t.data); bm.free()
for p in t.data.polygons: p.use_smooth = True
t.name = 'ThirdMolarAsset'; t.data.name = 'ThirdMolarAsset'
vs = [v.co for v in t.data.vertices]
print('ASSET bbox mm', [round(1000 * min(v[i] for v in vs), 2) for i in range(3)], [round(1000 * max(v[i] for v in vs), 2) for i in range(3)], 'verts', len(vs), 'parts', len(parts))
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'third_molar_v2.blend')
bpy.data.libraries.write(out, {t}, fake_user=True); print('ASSET', out)
