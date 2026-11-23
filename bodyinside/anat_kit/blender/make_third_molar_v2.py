"""Builds a clean lower-left third molar from scratch (no copy of a Z-Anatomy tooth, no sculpt): metaball composition with smooth union
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
# crown: four unequal lobes on a rounded body (mesiobuccal largest, distolingual smallest), ridges running from each cusp to the centre, small distal fifth cusp
for x, y, a in ((2.7, -2.4, 2.8), (2.6, 2.3, 2.5), (-2.7, -2.4, 2.6), (-2.5, 2.3, 2.2)): ball(x, y, 3.3, a)
ball(0, 0, 3.2, 3.0)
cusps = ((2.6, -2.3, 2.45, 3.9), (2.7, 2.0, 2.05, 3.7), (-2.6, -2.3, 2.2, 3.8), (-2.4, 2.1, 1.75, 3.5))
for x, y, a, z in cusps: ball(x, y, z, a, 2.5)
ball(0.2, 3.8, 3.3, 1.3, 2.5)
for x, y, a, z in cusps:
    for u in (0.35, 0.62): ball(x * (1 - u), y * (1 - u), z - 0.15 - 0.5 * u, 1.05, 2.5)   # ridge from cusp tip toward the central groove
# cervical constriction
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
# fissures: smooth subtracts
for i in range(-3, 4): ball(0, i * 0.95, 6.45, 0.95, 2.5, True)
for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):   # radial grooves between the cusps
    for k in (1, 2): ball(sx * 0.9 * k, sy * 0.9 * k, 6.1 - 0.15 * k, 0.55, 2.5, True)
for i in range(-2, 3): ball(i * 1.2 + 1.5, 0.1, 6.1, 0.8, 2.5, True)
ob = bpy.data.objects.new('T3mb', mb); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.convert(target='MESH'); t = bpy.context.active_object
zs_ = [v.co.z for v in t.data.vertices]; xs_ = [v.co.x for v in t.data.vertices]; ys_ = [v.co.y for v in t.data.vertices]
print('RAW bbox mm', round(min(xs_), 2), round(max(xs_), 2), round(min(ys_), 2), round(max(ys_), 2), round(min(zs_), 2), round(max(zs_), 2), len(t.data.vertices))
# scale to metres, voxel remesh, smooth
t.scale = (0.001, 0.001, 0.001); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rm = t.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.00012; rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='rm')
sm = t.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 30; bpy.ops.object.modifier_apply(modifier='sm')
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
