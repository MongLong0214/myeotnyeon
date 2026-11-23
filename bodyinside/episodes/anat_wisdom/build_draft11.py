# Builds wisdom.blend: impacted lower-left third molar extraction, 9 shots on one timeline (30 fps).
# Assets: Z-Anatomy (CC BY-SA 4.0, derived from BodyParts3D CC BY-SA 2.1 JP) via base.blend; instruments modelled here.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../../episodes/anat_wisdom/")
bpy.ops.wm.open_mainfile(filepath=HERE + "base.blend")
sc = bpy.context.scene
FPS = 30
sc.render.fps = FPS
D = bpy.data
O = D.objects

# ---------------- timeline (frames) ----------------
SH = dict(S1=0, S1b=40, S2=-400, S3=-300, S4=75, S5=160, S5b=200, S6=230, S7=600, S8=700, S9=800, S10=900, END=300)
sc.frame_start = 0
sc.frame_end = SH['END'] - 1

def key(obj, path, f, val, idx=None):
    if idx is None:
        setattr(obj, path, val) if not isinstance(val, (tuple, list, Vector)) else setattr(obj, path, val)
        obj.keyframe_insert(path, frame=f)
    else:
        getattr(obj, path)[idx] = val
        obj.keyframe_insert(path, index=idx, frame=f)

def vkey(node, f, v):
    node.outputs[0].default_value = v
    node.outputs[0].keyframe_insert('default_value', frame=f)

def vis(o, ranges):
    """visible only inside the given [start,end) frame ranges"""
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
    for a, b in ranges:
        o.hide_render = False; o.keyframe_insert('hide_render', frame=a)
        o.hide_render = True; o.keyframe_insert('hide_render', frame=b)

def link(o):
    sc.collection.objects.link(o); return o

def sel_only(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o

def world_bbox(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])

# ---------------- cleanup / grouping ----------------
O['Tongue'].hide_render = True
skin_parts = [o for o in O if o.type == 'MESH' and o.name not in ('Gingiva', 'Tongue', 'Mandible', 'Hyoid bone')
              and not any(k in o.name for k in ('bone', 'Maxilla', 'molar', 'premolar', 'incisor', 'canine', 'nerve', 'Vomer', 'Atlas', 'Axis', 'Vertebra'))]
bpy.ops.object.select_all(action='DESELECT')
for o in skin_parts: o.select_set(True)
bpy.context.view_layer.objects.active = skin_parts[0]
bpy.ops.object.join()
SKIN = bpy.context.active_object; SKIN.name = 'Skin'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0008); bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
if SKIN.data.has_custom_normals: bpy.ops.mesh.customdata_custom_splitnormals_clear()
SKIN.modifiers.new('sub', 'SUBSURF').levels = 2

# split gingiva into upper / lower
G = O['Gingiva']; sel_only(G)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
gparts = [o for o in O if o.name.startswith('Gingiva')]
gparts.sort(key=lambda o: world_bbox(o)[0].z)
GUM_LO = gparts[0]; GUM_LO.name = 'GumLower'
GUM_UP = [o for o in gparts[1:]]
for o in GUM_UP: o.name = 'GumUpper'

for o in O:
    if o.type == 'MESH':
        sel_only(o); bpy.ops.object.shade_smooth()

MAND = O['Mandible']
M2 = O['Lower second molar tooth.l']
NERVE = O['Inferior alveolar nerve.l']
upper_skull = [o for o in O if o.type == 'MESH' and (o.name.startswith('Upper') or any(k in o.name for k in ('bone', 'Maxilla', 'Vomer', 'Atlas', 'Axis', 'Vertebra')))]

# ---------------- third molar (from first molar mesh) ----------------
T3 = O['Lower first molar tooth.l'].copy(); T3.data = T3.data.copy(); T3.name = 'ThirdMolar'; link(T3)
sel_only(T3); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
# root faces -> material slot 1 (decided in the tooth's own frame: crown = top 38 %)
zs = [v.co.z for v in T3.data.vertices]; zmin, zmax = min(zs), max(zs)
cej = zmin + 0.62 * (zmax - zmin)
for pgn in T3.data.polygons:
    pgn.material_index = 1 if pgn.center.z < cej else 0
T3.rotation_euler = (math.radians(96), 0, math.radians(-6)); T3.scale = (0.75, 0.75, 0.75)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
lo, hi = world_bbox(T3)
m2lo, m2hi = world_bbox(M2)
# seat: below the occlusal plane, crown on the distal cervical third of the 2nd molar, inside the ramus base
T3.location += Vector((0.0300 - (lo.x + hi.x) / 2, (m2hi.y + 0.002) - lo.y, 1.5318 - (lo.z + hi.z) / 2))
bpy.context.view_layer.update()
dg0 = bpy.context.evaluated_depsgraph_get()
def world_bvh(o):
    mw_ = o.matrix_world
    return BVHTree.FromPolygons([mw_ @ v.co for v in o.data.vertices], [list(pg.vertices) for pg in o.data.polygons])
bvh_m2 = world_bvh(M2)
def touching():
    bpy.context.view_layer.update()
    return len(world_bvh(T3).overlap(bvh_m2)) > 0
step = 0.0002
for _ in range(80):
    if touching(): break
    T3.location.y -= step
T3.location.y += step * 0.5   # leave it just kissing the molar
bpy.context.view_layer.update()
sel_only(T3); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
lo, hi = world_bbox(T3)
C3 = (lo + hi) / 2
# contact point (closest T3 vertex to M2)
cp = min((T3.matrix_world @ v.co for v in T3.data.vertices), key=lambda w: (bvh_m2.find_nearest(w)[3] or 1))
CONTACT = cp.copy()
print("T3 bbox", tuple(round(x, 4) for x in lo), tuple(round(x, 4) for x in hi), "contact", tuple(round(x, 4) for x in cp))

# ---------------- materials ----------------
def newmat(name):
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    return m, nt, out, p

def ghostable(nt, out, shader_out, name, lo_op=0.04, hi_op=0.55, blend=0.35):
    """mix shader -> transparent driven by a Value node `name` (0 opaque .. 1 ghost, rim kept)"""
    val = nt.nodes.new('ShaderNodeValue'); val.name = name; val.outputs[0].default_value = 0.0
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = blend
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = lo_op; mr.inputs['To Max'].default_value = hi_op
    nt.links.new(lw.outputs['Facing'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'FLOAT'
    nt.links.new(val.outputs[0], mx.inputs['Factor']); mx.inputs['A'].default_value = 1.0
    nt.links.new(mr.outputs['Result'], mx.inputs['B'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], inv.inputs[1])
    bf = nt.nodes.new('ShaderNodeMath'); bf.operation = 'MAXIMUM'
    nt.links.new(inv.outputs[0], bf.inputs[0])
    # backfaces only fade while ghosted
    one_minus = nt.nodes.new('ShaderNodeMath'); one_minus.operation = 'SUBTRACT'; one_minus.inputs[0].default_value = 1.0
    nt.links.new(val.outputs[0], one_minus.inputs[1]); nt.links.new(one_minus.outputs[0], bf.inputs[1])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(mx.outputs['Result'], mul.inputs[0]); nt.links.new(bf.outputs[0], mul.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mul.outputs[0], ms.inputs['Fac']); nt.links.new(tr.outputs[0], ms.inputs[1]); nt.links.new(shader_out, ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs['Surface'])
    return val

def noise_bump(nt, p, scale, strength, dist=0.0003, voronoi=False):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    if voronoi:
        tx = nt.nodes.new('ShaderNodeTexVoronoi'); tx.feature = 'F1'
        out = tx.outputs['Distance']
    else:
        tx = nt.nodes.new('ShaderNodeTexNoise'); tx.inputs['Detail'].default_value = 8; tx.inputs['Roughness'].default_value = 0.6
        out = tx.outputs['Fac']
    tx.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], tx.inputs['Vector'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = dist
    nt.links.new(out, b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return tx

def colvar(nt, p, c1, c2, scale):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = c1; r.color_ramp.elements[1].color = c2
    r.color_ramp.elements[0].position = 0.35; r.color_ramp.elements[1].position = 0.7
    nt.links.new(n.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], p.inputs['Base Color'])

# skin
mSkin, nt, out, p = newmat('Skin')
p.inputs['Base Color'].default_value = (0.70, 0.42, 0.33, 1)
p.inputs['Subsurface Weight'].default_value = 0.4; p.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
p.inputs['Subsurface Scale'].default_value = 0.004; p.inputs['Roughness'].default_value = 0.42
SKIN_G = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.55)
SKIN.data.materials.clear(); SKIN.data.materials.append(mSkin)

# bone (porous)
def bone_material(name):
    m, nt, out, p = newmat(name)
    colvar(nt, p, (0.84, 0.76, 0.62, 1), (0.74, 0.64, 0.50, 1), 500)
    p.inputs['Subsurface Weight'].default_value = 0.12; p.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.4)
    p.inputs['Subsurface Scale'].default_value = 0.0015; p.inputs['Roughness'].default_value = 0.55
    noise_bump(nt, p, 5200, 0.12, 0.00006, voronoi=True)
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.0015
    bc_link = [l for l in nt.links if l.to_socket == p.inputs['Base Color']][0]; src = bc_link.from_socket
    mulc = nt.nodes.new('ShaderNodeMix'); mulc.data_type = 'RGBA'; mulc.blend_type = 'MULTIPLY'; mulc.inputs['Factor'].default_value = 0.3
    nt.links.new(src, mulc.inputs['A']); nt.links.new(src, ao.inputs['Color']); nt.links.new(ao.outputs['AO'], mulc.inputs['B'])
    nt.links.new(mulc.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Specular IOR Level'].default_value = 0.35; p.inputs['Roughness'].default_value = 0.48
    p.inputs['Emission Color'].default_value = (1.0, 0.22, 0.05, 1)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; em.outputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], p.inputs['Emission Strength'])
    g = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.5)
    return m, g, em
mBone, BONE_G, _ = bone_material('Bone')
mMand, MAND_G, _ = bone_material('MandBone')
_pm = [n for n in mMand.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
_pm.inputs['Subsurface Weight'].default_value = 0.45; _pm.inputs['Subsurface Scale'].default_value = 0.003; _pm.inputs['Coat Weight'].default_value = 0.35; _pm.inputs['Coat Roughness'].default_value = 0.25; _pm.inputs['Roughness'].default_value = 0.42
for _n in mMand.node_tree.nodes:
    if _n.type == 'MAP_RANGE': _n.inputs['To Min'].default_value = 0.07; _n.inputs['To Max'].default_value = 0.78

# cut (cancellous) bone: socket walls and drilled window
mCut, nt, out, p = newmat('CutBone')
colvar(nt, p, (0.30, 0.15, 0.12, 1), (0.18, 0.08, 0.07, 1), 1400)
p.inputs['Subsurface Weight'].default_value = 0.05; p.inputs['Subsurface Radius'].default_value = (1.0, 0.5, 0.4)
p.inputs['Subsurface Scale'].default_value = 0.0004; p.inputs['Roughness'].default_value = 0.35
noise_bump(nt, p, 4200, 0.6, 0.00015, voronoi=True)
p.inputs['Emission Color'].default_value = (1.0, 0.18, 0.04, 1)
CUT_EM = nt.nodes.new('ShaderNodeValue'); CUT_EM.name = 'Emit'; CUT_EM.outputs[0].default_value = 0.0
nt.links.new(CUT_EM.outputs[0], p.inputs['Emission Strength'])
CUT_G = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.5)

# enamel
def enamel(name, glow=False):
    m, nt, out, p = newmat(name)
    p.inputs['Base Color'].default_value = (0.90, 0.87, 0.78, 1)
    p.inputs['Subsurface Weight'].default_value = 0.2; p.inputs['Subsurface Radius'].default_value = (0.9, 0.85, 0.7)
    p.inputs['IOR'].default_value = 1.62
    p.inputs['Subsurface Scale'].default_value = 0.0012
    p.inputs['Roughness'].default_value = 0.12; p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.05
    noise_bump(nt, p, 1800, 0.05, 0.00005)
    p.inputs['Emission Color'].default_value = (1.0, 0.22, 0.06, 1)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; em.outputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], p.inputs['Emission Strength'])
    tint = nt.nodes.new('ShaderNodeValue'); tint.name = 'Tint'; tint.outputs[0].default_value = 0.0
    if glow:
        # base colour shifts toward amber while highlighted
        mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
        mixc.inputs['A'].default_value = (0.90, 0.87, 0.78, 1); mixc.inputs['B'].default_value = (1.0, 0.58, 0.22, 1)
        nt.links.new(tint.outputs[0], mixc.inputs['Factor']); nt.links.new(mixc.outputs['Result'], p.inputs['Base Color'])
    g = ghostable(nt, out, p.outputs[0], 'Ghost', 0.05, 0.6)
    return m, em, tint, g
mTooth, _, _, TOOTH_G = enamel('Enamel')
mT3, T3_EM, T3_TINT, T3_G = enamel('Enamel3', glow=True)
mM2, M2_EM, M2_TINT, _ = enamel('Enamel2', glow=True)
# second molar shows the pressure in red
nt = mM2.node_tree
for n in nt.nodes:
    if n.type == 'MIX' and n.data_type == 'RGBA': n.inputs['B'].default_value = (0.95, 0.35, 0.30, 1)
    if n.type == 'BSDF_PRINCIPLED': n.inputs['Emission Color'].default_value = (1.0, 0.1, 0.05, 1)

# gum: wet, translucent
def gum_material(name):
    m, nt, out, p = newmat(name)
    colvar(nt, p, (0.78, 0.30, 0.30, 1), (0.66, 0.22, 0.24, 1), 700)
    p.inputs['Subsurface Weight'].default_value = 0.65; p.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.18)
    p.inputs['Subsurface Scale'].default_value = 0.0025
    p.inputs['Roughness'].default_value = 0.32; p.inputs['Coat Weight'].default_value = 0.7; p.inputs['Coat Roughness'].default_value = 0.06
    p.inputs['Coat IOR'].default_value = 1.33
    noise_bump(nt, p, 1500, 0.15, 0.0001)
    g = ghostable(nt, out, p.outputs[0], 'Ghost', 0.04, 0.6)
    return m, g
mGum, GUM_G = gum_material('Gum')
mFlapInner, nt, out, p = newmat('FlapInner')  # periosteum side of the flap
p.inputs['Base Color'].default_value = (0.55, 0.12, 0.12, 1); p.inputs['Roughness'].default_value = 0.2
p.inputs['Subsurface Weight'].default_value = 0.5; p.inputs['Subsurface Radius'].default_value = (1, 0.2, 0.15); p.inputs['Subsurface Scale'].default_value = 0.002
p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.04
nt.links.new(p.outputs[0], out.inputs['Surface'])

# nerve
mNerve, nt, out, p = newmat('Nerve')
p.inputs['Base Color'].default_value = (0.95, 0.80, 0.30, 1)
p.inputs['Subsurface Weight'].default_value = 0.5; p.inputs['Subsurface Radius'].default_value = (1, 0.8, 0.3); p.inputs['Subsurface Scale'].default_value = 0.001
p.inputs['Roughness'].default_value = 0.3; p.inputs['Coat Weight'].default_value = 0.4
p.inputs['Emission Color'].default_value = (1.0, 0.85, 0.2, 1)
NERVE_EM = nt.nodes.new('ShaderNodeValue'); NERVE_EM.outputs[0].default_value = 0.0
nt.links.new(NERVE_EM.outputs[0], p.inputs['Emission Strength'])
nt.links.new(p.outputs[0], out.inputs['Surface'])

# clot
mClot, nt, out, p = newmat('Clot')
colvar(nt, p, (0.30, 0.02, 0.03, 1), (0.18, 0.01, 0.02, 1), 900)
p.inputs['Roughness'].default_value = 0.12; p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.03
p.inputs['Subsurface Weight'].default_value = 0.4; p.inputs['Subsurface Radius'].default_value = (1, 0.1, 0.1); p.inputs['Subsurface Scale'].default_value = 0.001
noise_bump(nt, p, 900, 0.3, 0.0002)
nt.links.new(p.outputs[0], out.inputs['Surface'])

# blood line of the incision (restrained)
mCutLine, nt, out, p = newmat('Incision')
p.inputs['Base Color'].default_value = (0.35, 0.02, 0.03, 1); p.inputs['Roughness'].default_value = 0.1; p.inputs['Coat Weight'].default_value = 1
nt.links.new(p.outputs[0], out.inputs['Surface'])

# metals
def metal(name, rough=0.16, aniso=0.0, col=(0.82, 0.82, 0.84, 1)):
    m, nt, out, p = newmat(name)
    p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = rough; p.inputs['Anisotropic'].default_value = aniso
    nt.links.new(p.outputs[0], out.inputs['Surface']); return m
mSteel = metal('Steel', 0.24, 0.5, (0.62, 0.62, 0.64, 1))
mSteelDark = metal('SteelBrushed', 0.38, 0.8, (0.45, 0.45, 0.47, 1))
mBlade = metal('Blade', 0.08, 0.0, (0.88, 0.88, 0.9, 1))
mGold = metal('BurGold', 0.25, 0.0, (0.9, 0.75, 0.45, 1))
mThread, nt, out, p = newmat('Thread')
p.inputs['Base Color'].default_value = (0.08, 0.10, 0.30, 1); p.inputs['Roughness'].default_value = 0.35; p.inputs['Sheen Weight'].default_value = 0.5
nt.links.new(p.outputs[0], out.inputs['Surface'])
mStraw, nt, out, p = newmat('Straw')
p.inputs['Base Color'].default_value = (0.95, 0.95, 0.97, 1); p.inputs['Roughness'].default_value = 0.08
p.inputs['Transmission Weight'].default_value = 0.85; p.inputs['IOR'].default_value = 1.45
nt.links.new(p.outputs[0], out.inputs['Surface'])
mStripe, nt, out, p = newmat('StrawStripe')
p.inputs['Base Color'].default_value = (0.85, 0.12, 0.10, 1); p.inputs['Roughness'].default_value = 0.2
nt.links.new(p.outputs[0], out.inputs['Surface'])

def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)

for o in O:
    if o.type != 'MESH': continue
    n = o.name
    if o is SKIN: continue
    if n == 'Mandible': setmat(o, mMand)
    elif n.startswith('Gum'): setmat(o, mGum)
    elif 'nerve' in n: setmat(o, mNerve)
    elif o is T3: setmat(o, mT3)
    elif o is M2: setmat(o, mM2)
    elif any(k in n for k in ('molar', 'premolar', 'incisor', 'canine')): setmat(o, mTooth)
    elif any(k in n for k in ('bone', 'Maxilla', 'Vomer', 'Atlas', 'Axis', 'Vertebra')): setmat(o, mBone)

# ---------------- buccal gum sheet (mucoperiosteal flap) ----------------
dg = bpy.context.evaluated_depsgraph_get()
mand_bvh = BVHTree.FromObject(MAND, dg)
pad = MAND.copy(); pad.data = MAND.data.copy(); pad.name = 'GumPad'; link(pad)
pad.modifiers.clear()
sel_only(pad)
ss = pad.modifiers.new('ss', 'SUBSURF'); ss.levels = 2; bpy.ops.object.modifier_apply(modifier='ss')
bm = bmesh.new(); bm.from_mesh(pad.data)
mw = pad.matrix_world
y0, y1 = m2lo.y + 0.006, hi.y + 0.004
ztop = hi.z + 0.0075
kill = []
for f in bm.faces:
    c = mw @ f.calc_center_median(); nrm = (mw.to_3x3() @ f.normal).normalized()
    ey = ((c.y - (y0 + y1) / 2) / ((y1 - y0) / 2)) ** 2; ez = ((c.z - (lo.z - 0.007 + ztop) / 2) / ((ztop - lo.z + 0.007) / 2)) ** 2
    keep = (ey + ez < 1.0) and c.x > C3.x + 0.002 and nrm.x > 0.2
    if not keep: kill.append(f)
bmesh.ops.delete(bm, geom=kill, context='FACES')
bm.to_mesh(pad.data); bm.free()
sol = pad.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.0011; sol.offset = 1.0; sol.use_rim = True; sol.material_offset = 1
sm = pad.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.8; sm.iterations = 12
setmat(pad, mGum); pad.data.materials.append(mFlapInner)
bpy.ops.object.modifier_apply(modifier='sol'); bpy.ops.object.modifier_apply(modifier='sm')
pad.modifiers.new('sub', 'SUBSURF').levels = 2; pad.modifiers['sub'].render_levels = 2
bpy.ops.object.shade_smooth()
FLAP = pad; FLAP.name = 'Flap'
flo, fhi = world_bbox(FLAP)
fv = [FLAP.matrix_world @ v.co for v in FLAP.data.vertices]
bottom = [v for v in fv if v.z < flo.z + 0.0015]
hinge = Vector((max(v.x for v in bottom), (flo.y + fhi.y) / 2, flo.z + 0.0008))
sel_only(FLAP); sc.cursor.location = hinge; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
print("flap", tuple(round(x, 4) for x in flo), tuple(round(x, 4) for x in fhi))

# incision: along the top edge of the flap + releasing cut down its mesial edge
def edge_top(y):
    s = [v for v in fv if abs(v.y - y) < 0.0009]
    if not s: return Vector((C3.x + 0.006, y, hi.z + 0.003))
    v = max(s, key=lambda q: q.z); return v + Vector((0.0004, 0, 0.0002))
top_pts = [edge_top(y0 + 0.0006 + (y1 - y0 - 0.0012) * t / 14) for t in range(15)]
mes = sorted([v for v in fv if abs(v.y - (y0 + 0.0006)) < 0.0009], key=lambda q: -q.z) or [Vector((C3.x + 0.006, y0, hi.z))]
rel = []
for zz in [top_pts[0].z - 0.0015 * i for i in range(1, 6)]:
    cand = min(mes, key=lambda q: abs(q.z - zz)); rel.append(cand + Vector((0.0004, 0, 0)))
path_pts = list(reversed(rel)) + top_pts
cu = D.curves.new('IncisionC', 'CURVE'); cu.dimensions = '3D'
sp = cu.splines.new('POLY'); sp.points.add(len(path_pts) - 1)
for i, pt in enumerate(path_pts): sp.points[i].co = (pt.x, pt.y, pt.z, 1)
cu.bevel_depth = 0.00026; cu.bevel_resolution = 3; cu.use_fill_caps = True
INC = link(D.objects.new('Incision', cu)); setmat(INC, mCutLine)
cu.bevel_factor_mapping_end = 'SPLINE'
INC_PTS = path_pts
def top_z(x, y):
    return edge_top(y).z
FX = C3.x

# ---------------- bone cavity + buccal window (boolean) ----------------
cutters = D.collections.new('Cutters'); sc.collection.children.link(cutters)
cav = T3.copy(); cav.data = T3.data.copy(); cav.name = 'CavityCutter'; cutters.objects.link(cav)
cav.scale = (1.03, 1.03, 1.03); setmat(cav, mCut)
win = D.objects.new('WindowCutter', D.meshes.new('win')); cutters.objects.link(win)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.5); bm.to_mesh(win.data); bm.free()
for pp in win.data.polygons: pp.use_smooth = True
setmat(win, mCut)
for o in cutters.objects: o.hide_render = True; o.display_type = 'WIRE'
bo = MAND.modifiers.new('carve', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.operand_type = 'COLLECTION'; bo.collection = cutters
bo.solver = 'EXACT'; bo.use_hole_tolerant = True; bo.material_mode = 'TRANSFER'
WX = C3.x + 0.0085
for f, ly, s in [(SH['S3'] + 6, lo.y + 0.004, (0.0002, 0.0002, 0.0002)),
                 (SH['S3'] + 34, lo.y + 0.006, (0.011, 0.008, 0.009)),
                 (SH['S3'] + 70, C3.y - 0.001, (0.013, (hi.y - lo.y) + 0.002, 0.0150)),
                 (SH['S3'] + 92, C3.y, (0.013, (hi.y - lo.y) + 0.005, 0.0165))]:
    win.location = Vector((WX, ly, C3.z + 0.0015)); win.scale = s
    win.keyframe_insert('location', frame=f); win.keyframe_insert('scale', frame=f)
# 10 s cut: window closed through the hook, open from the first close-up
win.scale = (0.0002, 0.0002, 0.0002); win.keyframe_insert('scale', frame=SH['S4'] - 1)
win.scale = (0.013, (hi.y - lo.y) + 0.005, 0.0165); win.keyframe_insert('scale', frame=SH['S4'])
wc = Vector((C3.x + 0.006, C3.y, C3.z + 0.0015))

# ---------------- crown / root split ----------------
split_y = lo.y + (hi.y - lo.y) * 0.47
boxC = D.objects.new('CrownBox', D.meshes.new('CrownBox')); link(boxC)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(boxC.data); bm.free()
boxC.location = Vector((C3.x, split_y - 0.025, C3.z)); boxC.scale = (0.05, 0.05, 0.05)
boxC.hide_render = True; boxC.display_type = 'WIRE'
slot = D.objects.new('Slot', D.meshes.new('slot')); link(slot)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(slot.data); bm.free()
slot.hide_render = True; slot.display_type = 'WIRE'
slot.scale = (0.012, 0.0011, 0.0)
mDentin, nt, out, p = newmat('Dentin')
p.inputs['Base Color'].default_value = (0.93, 0.80, 0.58, 1); p.inputs['Roughness'].default_value = 0.4
p.inputs['Subsurface Weight'].default_value = 0.3; p.inputs['Subsurface Radius'].default_value = (1, 0.7, 0.4); p.inputs['Subsurface Scale'].default_value = 0.001
nt.links.new(p.outputs[0], out.inputs['Surface'])
setmat(slot, mDentin); setmat(boxC, mDentin)
CROWN = T3.copy(); CROWN.data = T3.data.copy(); CROWN.name = 'Crown'; link(CROWN)
ROOT = T3.copy(); ROOT.data = T3.data.copy(); ROOT.name = 'Root'; link(ROOT)
for o, op in [(CROWN, 'INTERSECT'), (ROOT, 'DIFFERENCE')]:
    o.data.materials.clear(); o.data.materials.append(mT3)
    b = o.modifiers.new('half', 'BOOLEAN'); b.object = boxC; b.operation = op; b.solver = 'EXACT'; b.use_hole_tolerant = True; b.material_mode = 'TRANSFER'
    b2 = o.modifiers.new('slot', 'BOOLEAN'); b2.object = slot; b2.operation = 'DIFFERENCE'; b2.solver = 'EXACT'; b2.use_hole_tolerant = True; b2.material_mode = 'TRANSFER'
# slot: bur sweeps up/down while advancing from buccal to near the lingual wall
SL0, SL1 = C3.x + 0.014, C3.x + 0.002
slot.location = Vector((SL0, split_y, C3.z)); slot.scale = (0.012, 0.0011, 0.0)
slot.keyframe_insert('location', frame=SH['S4'] + 10); slot.keyframe_insert('scale', frame=SH['S4'] + 10)
slot.scale = (0.012, 0.0011, 0.016); slot.keyframe_insert('scale', frame=SH['S4'] + 11)
slot.location.x = SL1; slot.keyframe_insert('location', frame=SH['S4'] + 80)
T3.hide_render = True

def set_origin(o, p):
    sel_only(o); sc.cursor.location = p; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(CROWN, Vector((C3.x, (lo.y + split_y) / 2, C3.z)))
set_origin(ROOT, Vector((C3.x, (split_y + hi.y) / 2, C3.z)))
cl0, cr0 = CROWN.location.copy(), ROOT.location.copy()
# cutters ride with their piece once it moves (static cutters would keep slicing the moving root)
boxR = boxC.copy(); link(boxR); slotR = slot.copy(); link(slotR)
bpy.context.view_layer.update()
for c, par in ((boxC, CROWN), (slot, CROWN), (boxR, ROOT), (slotR, ROOT)):
    c.parent = par; c.matrix_parent_inverse = par.matrix_world.inverted()
ROOT.modifiers['half'].object = boxR; ROOT.modifiers['slot'].object = slotR
def kloc(o, f, p):
    o.location = p; o.keyframe_insert('location', frame=f)
def krot(o, f, r):
    o.rotation_euler = r; o.keyframe_insert('rotation_euler', frame=f)
R = math.radians
kloc(CROWN, SH['S5'] + 10, cl0); krot(CROWN, SH['S5'] + 10, (0, 0, 0))
kloc(CROWN, SH['S5'] + 22, cl0 + Vector((0.0012, -0.0004, 0.0006))); krot(CROWN, SH['S5'] + 22, (0, 0, R(-6)))
kloc(CROWN, SH['S5'] + 44, cl0 + Vector((0.010, -0.001, 0.004))); krot(CROWN, SH['S5'] + 44, (R(-10), 0, R(-22)))
kloc(CROWN, SH['S5'] + 64, cl0 + Vector((0.040, 0.0, 0.016))); krot(CROWN, SH['S5'] + 64, (R(-20), R(10), R(-40)))
vis(CROWN, [(0, SH['S5'] + 64)])
kloc(ROOT, SH['S5b'] + 6, cr0); krot(ROOT, SH['S5b'] + 6, (0, 0, 0))
kloc(ROOT, SH['S5b'] + 40, cr0 + Vector((0.0005, -0.0045, 0.0004))); krot(ROOT, SH['S5b'] + 40, (0, 0, R(3)))
kloc(ROOT, SH['S6'] + 70, cr0 + Vector((0.004, -0.0055, 0.0045))); krot(ROOT, SH['S6'] + 70, (R(10), 0, R(10)))
kloc(ROOT, SH['S6'] + 150, cr0 + Vector((0.012, -0.005, 0.016))); krot(ROOT, SH['S6'] + 150, (R(25), 0, R(25)))
kloc(ROOT, SH['S6'] + 185, cr0 + Vector((0.03, -0.004, 0.045))); krot(ROOT, SH['S6'] + 185, (R(35), 0, R(30)))
vis(ROOT, [(0, SH['S6'] + 185)])

# ---------------- clot ----------------
CLOT = T3.copy(); CLOT.data = T3.data.copy(); CLOT.name = 'Clot'; link(CLOT); CLOT.modifiers.clear()
sel_only(CLOT); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
rm = CLOT.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.0004
dp = CLOT.modifiers.new('disp', 'DISPLACE'); tx = D.textures.new('clotn', 'CLOUDS'); tx.noise_scale = 0.0015; dp.texture = tx; dp.strength = 0.0006; dp.mid_level = 0.5
CLOT.modifiers.new('sm', 'SMOOTH').iterations = 4
CLOT.modifiers.new('sub', 'SUBSURF').levels = 1
setmat(CLOT, mClot)
c0 = CLOT.location.copy()
for f, s, dz in [(SH['S7'] + 2, 0.08, -0.0055), (SH['S7'] + 45, 1.03, 0.0)]:
    CLOT.scale = (1.03, 1.03, s); CLOT.location = c0 + Vector((0, 0, dz))
    CLOT.keyframe_insert('scale', frame=f); CLOT.keyframe_insert('location', frame=f)
for f, d, r in [(SH['S9'] + 20, Vector((0, 0, 0)), 0), (SH['S9'] + 40, Vector((0.0015, 0, 0.0015)), 4), (SH['S9'] + 95, Vector((0.025, 0, 0.03)), 25)]:
    CLOT.location = c0 + d; CLOT.rotation_euler = (0, 0, R(r))
    CLOT.keyframe_insert('location', frame=f); CLOT.keyframe_insert('rotation_euler', frame=f)
vis(CLOT, [(SH['S7'] + 2, SH['S9'] + 95)])

# ---------------- flap animation ----------------
FA = R(150)
krot(FLAP, SH['S2'] + 50, (0, 0, 0)); krot(FLAP, SH['S2'] + 92, (0, FA, 0))
krot(FLAP, SH['S7'] + 46, (0, FA, 0)); krot(FLAP, SH['S7'] + 76, (0, 0, 0))
cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=SH['S2'] + 8)
cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=SH['S2'] + 46)
vis(INC, [(SH['S2'] + 8, SH['S2'] + 52), (SH['S7'] + 76, SH['S9'] + 20)])

# ---------------- instruments ----------------
def mesh_obj(name, verts, faces, mat):
    me = D.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = link(D.objects.new(name, me)); setmat(o, mat); return o

def cyl(name, r, h, mat, seg=32, r2=None, loc=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(D.objects.new(name, me)); setmat(o, mat); o.location = loc
    for p in o.data.polygons: p.use_smooth = True
    o.modifiers.new('ws', 'WEIGHTED_NORMAL') if False else None
    return o

def parent(child, par):
    child.parent = par; child.matrix_parent_inverse = par.matrix_world.inverted()

# scalpel: tip at origin, blade along -z?  build along +x then orient with an empty
SCAL = link(D.objects.new('Scalpel', None))
handle = cyl('ScHandle', 0.0042, 0.13, mSteelDark, 6, 0.0042)
handle.scale = (1.0, 0.45, 1.0); handle.location = (0, 0, 0.012 + 0.065)
bvm = handle.modifiers.new('bev', 'BEVEL'); bvm.width = 0.0009; bvm.segments = 3
# blade #15: 2D outline extruded
outline = [(0, 0), (0.0035, 0.0012), (0.0062, 0.0040), (0.0075, 0.0080), (0.0072, 0.0125), (0.0030, 0.0135), (-0.0004, 0.0135), (-0.0012, 0.0080), (-0.0006, 0.0030)]
bm = bmesh.new()
vs = [bm.verts.new((x, 0, y)) for x, y in outline]
f = bm.faces.new(vs)
ext = bmesh.ops.extrude_face_region(bm, geom=[f])
for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.y += 0.00035
me = D.meshes.new('blade'); bm.to_mesh(me); bm.free()
blade = link(D.objects.new('ScBlade', me)); setmat(blade, mBlade)
blade.location = (-0.003, -0.00017, 0.0)
for c in (handle, blade): parent(c, SCAL)
# handpiece (contra-angle) with bur pointing -z at origin
HP = link(D.objects.new('Handpiece', None))
bur_head = cyl('BurHead', 0.0006, 0.005, mGold, 24, 0.00045, (0, 0, 0.0025))
bur_shank = cyl('BurShank', 0.0008, 0.012, mSteel, 24, None, (0, 0, 0.0095))
hp_head = cyl('HpHead', 0.0050, 0.009, mSteel, 40, None, (0, 0, 0.0195))
neck = cyl('HpNeck', 0.0038, 0.04, mSteel, 40, 0.0046, (0, 0.0, 0.0))
neck.rotation_euler = (math.radians(-90 + 18), 0, 0); neck.location = (0, 0.020 + 0.0, 0.0230 + 0.006)
body = cyl('HpBody', 0.0058, 0.09, mSteelDark, 40, 0.0062, (0, 0, 0))
body.rotation_euler = (math.radians(-90 + 18), 0, 0); body.location = (0, 0.083, 0.0485)
for c in (bur_head, bur_shank, hp_head, neck, body): parent(c, HP)
BURSPIN = (bur_head, bur_shank)
for b in BURSPIN:
    d = b.driver_add('rotation_euler', 2).driver; d.type = 'SCRIPTED'; d.expression = 'frame*2.3'
# elevator: blade tip at origin pointing -z
EL = link(D.objects.new('Elevator', None))
tip = cyl('ElTip', 0.0014, 0.009, mSteel, 32, 0.0022, (0, 0, 0.0045))
tip.scale = (1.0, 0.55, 1.0)
shank = cyl('ElShank', 0.0022, 0.03, mSteel, 32, 0.0026, (0, 0, 0.024))
ehandle = cyl('ElHandle', 0.0065, 0.10, mSteelDark, 48, 0.0072, (0, 0, 0.089))
for c in (tip, shank, ehandle): parent(c, EL)
# curved suture needle + thread
NEED = link(D.objects.new('Needle', None))
bm = bmesh.new()
arc = bpy.data.curves.new('needleC', 'CURVE'); arc.dimensions = '3D'
s = arc.splines.new('POLY'); n = 16; s.points.add(n - 1)
for i in range(n):
    a = math.radians(-10 + 200 * i / (n - 1)); s.points[i].co = (0.0045 * math.cos(a), 0, 0.0045 * math.sin(a), 1)
arc.bevel_depth = 0.00025; arc.bevel_resolution = 2
needle = link(D.objects.new('NeedleArc', arc)); setmat(needle, mSteel); parent(needle, NEED)
STRAW = link(D.objects.new('Straw', None))
st1 = cyl('StrawTube', 0.0032, 0.12, mStraw, 48, None, (0, 0, 0.06))
sol2 = st1.modifiers.new('sol', 'SOLIDIFY'); sol2.thickness = 0.0003
for c in (st1,): parent(c, STRAW)

def place_tool(tool, f, loc, rot):
    tool.location = loc; tool.rotation_euler = rot
    tool.keyframe_insert('location', frame=f); tool.keyframe_insert('rotation_euler', frame=f)

def tool_vis(tool, ranges):
    for c in [tool] + list(tool.children): vis(c, ranges)

# scalpel along the incision (S2)
n_pts = len(INC_PTS)
f0, f1 = SH['S2'] + 8, SH['S2'] + 46
srot = (R(-8), R(62), R(12))
place_tool(SCAL, f0 - 12, INC_PTS[0] + Vector((0.01, -0.004, 0.006)), srot)
for i, ptt in enumerate(INC_PTS):
    place_tool(SCAL, int(f0 + (f1 - f0) * i / (n_pts - 1)), ptt + Vector((-0.0005, 0, 0)), srot)
place_tool(SCAL, f1 + 14, INC_PTS[-1] + Vector((0.014, 0.004, 0.006)), srot)
tool_vis(SCAL, [(SH['S2'], SH['S2'] + 62)])
# bur: S3 guttering around the crown, S4 sectioning slot (up/down sweeps)
hrot = (R(-12), R(78), R(-8))
path3 = [Vector((C3.x + 0.0062, lo.y + 0.004, C3.z + 0.005)), Vector((C3.x + 0.0062, lo.y + 0.007, C3.z - 0.004)),
         Vector((C3.x + 0.0062, C3.y - 0.002, C3.z + 0.006)), Vector((C3.x + 0.0062, C3.y + 0.003, C3.z - 0.003)),
         Vector((C3.x + 0.0062, hi.y - 0.002, C3.z + 0.005)), Vector((C3.x + 0.0062, hi.y - 0.001, C3.z - 0.002))]
place_tool(HP, SH['S3'] - 2, path3[0] + Vector((0.012, 0, 0.004)), hrot)
for i, ptt in enumerate(path3):
    place_tool(HP, SH['S3'] + 8 + i * 16, ptt, hrot)
place_tool(HP, SH['S3'] + 104, path3[-1] + Vector((0.014, 0, 0.004)), hrot)
vrot = (R(0), R(45), R(0))
place_tool(HP, SH['S4'] + 0, Vector((SL0 - 0.006 + 0.008, split_y, C3.z + 0.004)), vrot)
for k in range(9):
    t = k / 8
    x = (SL0 - 0.006) + (SL1 - SL0) * t
    place_tool(HP, SH['S4'] + 10 + k * 9, Vector((x - 0.002, split_y, C3.z + (0.005 if k % 2 == 0 else -0.004))), vrot)
place_tool(HP, SH['S4'] + 100, Vector((SL0 + 0.004, split_y, C3.z + 0.004)), vrot)
tool_vis(HP, [(SH['S3'], SH['S4'] + 112)])
# elevator into the slot: twist cracks the crown off, then levers the root
erot = (R(0), R(80), R(0))
place_tool(EL, SH['S5'] - 2, Vector((C3.x + 0.016, split_y, C3.z + 0.002)), erot)
place_tool(EL, SH['S5'] + 8, Vector((C3.x + 0.0045, split_y, C3.z + 0.001)), erot)
place_tool(EL, SH['S5'] + 20, Vector((C3.x + 0.0045, split_y, C3.z + 0.001)), (R(-30), R(80), R(0)))
place_tool(EL, SH['S5'] + 40, Vector((C3.x + 0.02, split_y + 0.003, C3.z + 0.006)), erot)
place_tool(EL, SH['S5b'] + 0, Vector((C3.x + 0.0055, split_y - 0.0005, C3.z + 0.004)), (R(0), R(70), R(-10)))
place_tool(EL, SH['S5b'] + 36, Vector((C3.x + 0.0055, split_y - 0.0035, C3.z + 0.0045)), (R(-18), R(70), R(-10)))
place_tool(EL, SH['S6'] + 0, Vector((C3.x + 0.0075, split_y - 0.0045, C3.z + 0.006)), (R(-25), R(70), R(-10)))
tool_vis(EL, [(SH['S5'] - 4, SH['S5b'] + 28)])
# needle + sutures across the incision (S7)
nrot0 = (R(0), R(90), R(0))
stitch_y = [y0 + (y1 - y0) * t for t in (0.2, 0.5, 0.8)]
for i, sy in enumerate(stitch_y):
    base = edge_top(sy)
    fa = SH['S7'] + 80 + i * 17
    place_tool(NEED, fa, base + Vector((0.004, 0, -0.002)), nrot0)
    place_tool(NEED, fa + 9, base + Vector((0.0015, 0, 0.0005)), (R(90), R(90), R(0)))
tool_vis(NEED, [(SH['S7'] + 78, SH['S7'] + 132)])
for i, sy in enumerate(stitch_y):
    base = edge_top(sy)
    tc = D.curves.new(f'st{i}', 'CURVE'); tc.dimensions = '3D'
    s = tc.splines.new('BEZIER'); s.bezier_points.add(3)
    pts4 = [base + Vector((-0.0003, 0, -0.0026)), base + Vector((0.0007, 0.0003, -0.0008)), base + Vector((0.0007, -0.0003, 0.0008)), base + Vector((-0.0003, 0, 0.0024))]
    for bp, pp in zip(s.bezier_points, pts4):
        bp.co = pp; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    tc.bevel_depth = 0.00017; tc.bevel_resolution = 2
    so = link(D.objects.new(f'Suture{i}', tc)); setmat(so, mThread)
    fa = SH['S7'] + 80 + i * 17 + 10
    tc.bevel_factor_end = 0.0; tc.keyframe_insert('bevel_factor_end', frame=fa)
    tc.bevel_factor_end = 1.0; tc.keyframe_insert('bevel_factor_end', frame=fa + 8)
    vis(so, [(fa, SH['S9'] + 20), (SH['S10'], SH['END'])])
# straw (S8-S9)
stl = Vector((C3.x + 0.012, C3.y, C3.z + 0.012))
place_tool(STRAW, SH['S8'] + 55, stl + Vector((0.03, 0, 0.04)), (R(0), R(42), R(0)))
place_tool(STRAW, SH['S8'] + 90, stl, (R(0), R(42), R(0)))
tool_vis(STRAW, [(SH['S8'] + 55, SH['S9'] + 110)])

# ---------------- visibility per shot (10 s cut) ----------------
HOOK_END = SH['S4']
for o in [SKIN] + upper_skull + GUM_UP:
    vis(o, [(0, HOOK_END)])
vis(NERVE, [(0, HOOK_END), (SH['S6'], SH['END'] + 1)])
for n in ('Mental nerve.l', 'Lingual nerve.l'):
    if n in O: O[n].hide_render = True
vis(FLAP, [(HOOK_END, SH['END'] + 1)])
INC.hide_render = True
for o in (CLOT, NEED, STRAW, SCAL) + tuple(NEED.children) + tuple(STRAW.children) + tuple(SCAL.children):
    if o.animation_data: o.animation_data_clear()
    o.hide_render = True
for i in range(3):
    so = O[f'Suture{i}']; so.animation_data_clear(); so.hide_render = True
for c in [HP] + list(HP.children):
    c.animation_data_clear() if c.animation_data and c is HP and False else None
    vis(c, [(SH['S4'], SH['S4'] + 96)])

vis(GUM_LO, [(0, SH['S6'])])
FLAP.animation_data_clear(); FLAP.hide_render = True
sm_n = NERVE.modifiers.new('sm', 'SMOOTH'); sm_n.factor = 1.0; sm_n.iterations = 6
dn = NERVE.modifiers.new('fat', 'DISPLACE'); dn.strength = 0.00035; dn.mid_level = 0.0
NERVE.modifiers.new('sub', 'SUBSURF').levels = 1
# ---------------- ghost / glow animation ----------------
vkey(SKIN_G, 0, 0.30); vkey(SKIN_G, 26, 1.0)
vkey(BONE_G, 0, 0.30); vkey(BONE_G, 26, 0.85)
vkey(MAND_G, 0, 0.25); vkey(MAND_G, 26, 0.88); vkey(MAND_G, HOOK_END - 1, 0.88); vkey(MAND_G, HOOK_END, 0.0)
vkey(MAND_G, SH['S6'] - 1, 0.0); vkey(MAND_G, SH['S6'], 0.82)
vkey(CUT_G, 0, 0.6); vkey(CUT_G, HOOK_END - 1, 0.6); vkey(CUT_G, HOOK_END, 0.0); vkey(CUT_G, SH['S6'] - 1, 0.0); vkey(CUT_G, SH['S6'], 0.6)
vkey(GUM_G, 0, 0.3); vkey(GUM_G, 26, 0.85); vkey(GUM_G, HOOK_END - 1, 0.85); vkey(GUM_G, HOOK_END, 0.0)
vkey(GUM_G, SH['S6'] - 1, 0.0); vkey(GUM_G, SH['S6'], 0.85)
vkey(TOOTH_G, 0, 0.0); vkey(TOOTH_G, SH['S6'] - 1, 0.0); vkey(TOOTH_G, SH['S6'], 0.75)
for f, t, e in [(0, 0.0, 0.0), (20, 1.0, 1.4), (34, 1.0, 3.0), (46, 1.0, 1.2), (58, 1.0, 3.0), (70, 1.0, 1.2), (HOOK_END - 1, 1.0, 1.2), (HOOK_END, 0.0, 0.0)]:
    vkey(T3_TINT, f, t); vkey(T3_EM, f, e)
for f, t, e in [(0, 0.0, 0.0), (20, 0.0, 0.0), (34, 0.8, 1.6), (46, 0.3, 0.3), (58, 0.8, 1.6), (70, 0.3, 0.3), (HOOK_END - 1, 0.3, 0.3), (HOOK_END, 0.0, 0.0)]:
    vkey(M2_TINT, f, t); vkey(M2_EM, f, e)
vkey(NERVE_EM, 0, 0.0); vkey(NERVE_EM, SH['S6'] - 1, 0.0); vkey(NERVE_EM, SH['S6'], 0.4)
for i in range(3):
    vkey(NERVE_EM, SH['S6'] + 14 + i * 22, 3.0); vkey(NERVE_EM, SH['S6'] + 25 + i * 22, 0.9)

# ---------------- cameras ----------------
def camera(name, target, path, lens=60, fstop=4.0, f_range=None):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_start = 0.002; cd.clip_end = 5
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    c = link(D.objects.new(name, cd))
    t = link(D.objects.new(name + '_T', None)); t.location = target
    tc = c.constraints.new('TRACK_TO'); tc.target = t; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    cd.dof.use_dof = True; cd.dof.focus_object = t; cd.dof.aperture_fstop = fstop
    for f, off in path:
        c.location = Vector(target) + Vector(off); c.keyframe_insert('location', frame=f)
    return c, t

def dirv(x, y, z, d):
    v = Vector((x, y, z)).normalized() * d; return tuple(v)

cams = {}
jaw = Vector((0.026, -0.045, 1.527))
spl = Vector((C3.x + 0.005, split_y, C3.z))
cams['S1'] = camera('C_S1', jaw + Vector((0, 0, 0.01)), [(SH['S1'], dirv(0.85, -0.55, 0.12, 0.34)), (SH['S1b'], dirv(0.85, -0.5, 0.10, 0.27))], lens=50, fstop=11.2)
cams['S1b'] = camera('C_S1b', C3 + Vector((0, -0.006, 0)), [(SH['S1b'], dirv(1, -0.12, 0.08, 0.15)), (SH['S4'], dirv(1, -0.08, 0.06, 0.115))], lens=55, fstop=8.0)
cams['S2'] = camera('C_S2', C3 + Vector((0.006, -0.001, 0.002)), [(SH['S2'], dirv(0.8, -0.5, 0.45, 0.105)), (SH['S3'], dirv(0.85, -0.42, 0.4, 0.088))], lens=60, fstop=6.4)
cams['S3'] = camera('C_S3', wc, [(SH['S3'], dirv(0.85, -0.3, 0.35, 0.09)), (SH['S4'], dirv(0.88, -0.2, 0.32, 0.076))], lens=60, fstop=6.4)
cams['S4'] = camera('C_S4', spl + Vector((0, 0, -0.001)), [(SH['S4'], dirv(1.0, -0.28, 0.06, 0.08)), (SH['S5'], dirv(1.0, -0.2, 0.08, 0.068))], lens=60, fstop=8.0)
cams['S5'] = camera('C_S5', C3 + Vector((0.006, 0, 0.002)), [(SH['S5'], dirv(0.85, -0.45, 0.3, 0.10)), (SH['S6'], dirv(0.85, -0.38, 0.34, 0.085))], lens=55, fstop=6.4)
cams['S5b'] = camera('C_S5b', C3 + Vector((0.004, 0.002, 0.002)), [(SH['S5b'], dirv(0.8, 0.35, 0.45, 0.09)), (SH['S6'], dirv(0.8, 0.3, 0.42, 0.08))], lens=60, fstop=6.4)
cams['S6'] = camera('C_S6', C3 + Vector((0, 0.003, -0.004)), [(SH['S6'], dirv(1, -0.10, 0.10, 0.085)), (SH['END'], dirv(1, -0.06, 0.08, 0.07))], lens=60, fstop=9.0)
cams['S7'] = camera('C_S7', C3 + Vector((0.005, 0, 0.002)), [(SH['S7'], dirv(0.8, -0.4, 0.45, 0.095)), (SH['S8'], dirv(0.82, -0.35, 0.45, 0.08))], lens=60, fstop=6.4)
cams['S8'] = camera('C_S8', C3 + Vector((0.004, 0, 0.004)), [(SH['S8'], dirv(0.9, -0.35, 0.35, 0.13)), (SH['S9'], dirv(0.9, -0.3, 0.32, 0.11))], lens=55, fstop=8.0)
cams['S9'] = camera('C_S9', C3 + Vector((0.004, 0, 0.004)), [(SH['S9'], dirv(0.85, -0.3, 0.45, 0.10)), (SH['S10'], dirv(0.85, -0.25, 0.42, 0.085))], lens=60, fstop=7.0)
cams['S10'] = camera('C_S10', jaw + Vector((0, 0, 0.01)), [(SH['S10'], dirv(0.85, -0.5, 0.10, 0.25)), (SH['END'], dirv(0.85, -0.55, 0.12, 0.33))], lens=50, fstop=11.2)
for k, (c, t) in cams.items():
    if k in ('S1', 'S1b', 'S4', 'S5', 'S6'):
        m = sc.timeline_markers.new(k, frame=SH[k]); m.camera = c
sc.camera = cams['S1'][0]

# ================= V2 (Fable review 1): one continuous scene, solid bone with cutaway, real section =================
E0 = 300
sc.timeline_markers.clear()
for m in D.materials:
    if m.node_tree and m.node_tree.animation_data: m.node_tree.animation_data_clear()
def clear(o):
    if o.animation_data: o.animation_data_clear()
KEEP_LOWER = lambda n: n.startswith('Lower') and n.endswith('.l')
for o in list(O):
    if o.type not in ('MESH', 'CURVE'): continue
    clear(o)
    keep = o.name in ('Mandible', 'GumLower', 'Crown', 'Root') or KEEP_LOWER(o.name)
    o.hide_render = not keep
for o in [HP] + list(HP.children):
    clear(o)
# far (right) half of the jaw dropped: x < 0.004 is transparent for bone, socket and gum
for mat_ in (mMand, mCut, mGum):
    ntm = mat_.node_tree
    msn = [n for n in ntm.nodes if n.type == 'MIX_SHADER'][0]
    src = msn.inputs['Fac'].links[0].from_socket
    geo2 = ntm.nodes.new('ShaderNodeNewGeometry'); sep = ntm.nodes.new('ShaderNodeSeparateXYZ')
    ntm.links.new(geo2.outputs['Position'], sep.inputs[0])
    stp = ntm.nodes.new('ShaderNodeMath'); stp.operation = 'GREATER_THAN'; stp.inputs[1].default_value = 0.004
    ntm.links.new(sep.outputs['X'], stp.inputs[0])
    m2_ = ntm.nodes.new('ShaderNodeMath'); m2_.operation = 'MULTIPLY'
    ntm.links.new(src, m2_.inputs[0]); ntm.links.new(stp.outputs[0], m2_.inputs[1]); ntm.links.new(m2_.outputs[0], msn.inputs['Fac'])
    if mat_ is mGum:  # gum stops at the 2nd molar's distal (no fin up the ramus)
        stz = ntm.nodes.new('ShaderNodeMapRange'); stz.interpolation_type = 'SMOOTHSTEP'; stz.inputs['From Min'].default_value = 1.5265; stz.inputs['From Max'].default_value = 1.5305; stz.inputs['To Min'].default_value = 1.0; stz.inputs['To Max'].default_value = 0.0
        ntm.links.new(sep.outputs['Z'], stz.inputs['Value']); stz = stz.outputs['Result'] and stz; m4_ = ntm.nodes.new('ShaderNodeMath'); m4_.operation = 'MULTIPLY'
        ntm.links.new(m2_.outputs[0], m4_.inputs[0]); ntm.links.new(stz.outputs['Result'], m4_.inputs[1]); m2_ = m4_
        sty = ntm.nodes.new('ShaderNodeMapRange'); sty.interpolation_type = 'SMOOTHSTEP'; sty.inputs['From Min'].default_value = m2hi.y - 0.0085; sty.inputs['From Max'].default_value = m2hi.y - 0.0035; sty.inputs['To Min'].default_value = 1.0; sty.inputs['To Max'].default_value = 0.0
        ntm.links.new(sep.outputs['Y'], sty.inputs['Value']); m3_ = ntm.nodes.new('ShaderNodeMath'); m3_.operation = 'MULTIPLY'
        ntm.links.new(m2_.outputs[0], m3_.inputs[0]); ntm.links.new(sty.outputs['Result'], m3_.inputs[1]); ntm.links.new(m3_.outputs[0], msn.inputs['Fac'])
# ---- material states (static) ----
def setv(node, v): node.outputs[0].default_value = v
setv(MAND_G, 0.55); setv(CUT_G, 0.0); setv(GUM_G, 0.5); setv(TOOTH_G, 0.0)
setv(T3_TINT, 0.22); setv(T3_EM, 0.0); setv(M2_TINT, 0.0); setv(M2_EM, 0.0)
# root (cementum) as its own material on slot 1
mCem, nt, out, p = newmat('Cementum')
p.inputs['Base Color'].default_value = (0.86, 0.74, 0.52, 1); p.inputs['Roughness'].default_value = 0.5
p.inputs['Subsurface Weight'].default_value = 0.25; p.inputs['Subsurface Radius'].default_value = (1, 0.75, 0.45); p.inputs['Subsurface Scale'].default_value = 0.001
noise_bump(nt, p, 2400, 0.08, 0.00005)
nt.links.new(p.outputs[0], out.inputs['Surface'])
for o in (CROWN, ROOT):
    o.data.materials.clear(); o.data.materials.append(mT3); o.data.materials.append(mCem)
    ss = o.modifiers.new('ss', 'SUBSURF'); ss.levels = 1; ss.render_levels = 2
    while o.modifiers[0].name != 'ss': bpy.ops.object.modifier_move_up({'object': o}, modifier='ss') if False else o.modifiers.move(len(o.modifiers) - 1, 0)
ssm = MAND.modifiers.new('ss', 'SUBSURF'); ssm.levels = 1; ssm.render_levels = 1
MAND.modifiers.move(len(MAND.modifiers) - 1, 0)
for mt in (mSteel,):
    pp_ = [n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    pp_.inputs['Base Color'].default_value = (0.80, 0.80, 0.82, 1); pp_.inputs['Roughness'].default_value = 0.2
# ---- window: buccal-occlusal cutaway around the third molar (static) ----
clear(win)
win.data = D.meshes.new('wincyl')
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.5, radius2=0.5, depth=1.0); bm.to_mesh(win.data); bm.free()
for pg in win.data.polygons: pg.use_smooth = True
win.modifiers.clear(); setmat(win, mCut)
NR, CR = 0.0007, 0.00115
_t3v = [T3.matrix_world @ v.co for v in T3.data.vertices]
RT = min((v for v in _t3v if v.y > hi.y - 0.0065), key=lambda q: q.z); root_bottom = RT.z
mid_bottom = min(v.z for v in _t3v if hi.y - 0.0095 < v.y <= hi.y - 0.0065)
z_under = root_bottom - 0.0016 - NR
print('root_bottom', round(root_bottom, 4), 'mid_bottom', round(mid_bottom, 4))
wz0, wz1 = z_under - 0.0016, hi.z + 0.0022
win.data = D.meshes.new('winell'); _bm = bmesh.new(); bmesh.ops.create_uvsphere(_bm, u_segments=48, v_segments=24, radius=0.5); _bm.to_mesh(win.data); _bm.free()
for _pg in win.data.polygons: _pg.use_smooth = True
mWin, _nt, _o, _p = newmat('CutWall'); colvar(_nt, _p, (0.86, 0.76, 0.62, 1), (0.70, 0.56, 0.44, 1), 1600); noise_bump(_nt, _p, 4200, 0.5, 0.00012, voronoi=True); _p.inputs['Roughness'].default_value = 0.5; _nt.links.new(_p.outputs[0], _o.inputs['Surface'])
setmat(win, mWin); win.rotation_euler = (0, 0, 0)
_wz0, _wz1 = z_under - 0.0018, hi.z + 0.002
# socket backing: closes see-through holes where the crypt meets the thin lingual cortex
_bk = cyl('SocketBack', 0.5, 0.0006, mCut, 48, None, (C3.x - 0.0062, C3.y + 0.0004, C3.z))
_bk.rotation_euler = (0, R(90), 0); _bk.scale = (0.016, (hi.y - lo.y) + 0.006, 1)
win.location = Vector((C3.x + 0.0100, C3.y + 0.0004, (_wz0 + _wz1) / 2)); win.scale = (0.0225, (hi.y - lo.y) + 0.005, (_wz1 - _wz0) * 1.15)
def cutbox(name, x0, x1, y0_, y1_, z0, z1):
    o = D.objects.new(name, D.meshes.new(name)); cutters.objects.link(o)
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0); bm_.to_mesh(o.data); bm_.free()
    o.location = Vector(((x0 + x1) / 2, (y0_ + y1_) / 2, (z0 + z1) / 2)); o.scale = (x1 - x0, y1_ - y0_, z1 - z0)
    o.hide_render = True; o.display_type = 'WIRE'; setmat(o, mCut); return o
# section A: through the middle of the third molar, open to the top so the bur comes from the occlusal side
# (no porthole: the bone is translucent instead)
# ---- procedural nerve + canal (round, continuous, no branches) ----
mw_m = MAND.matrix_world
mand_v = [mw_m @ v.co for v in MAND.data.vertices]
def lower_border(y):
    s_ = [v.z for v in mand_v if abs(v.y - y) < 0.002 and v.x > 0.0]
    return min(s_) if s_ else None
NR, CR = 0.0007, 0.00115
pts = [(0.0300, -0.0715, 1.5120), (0.0245, -0.0665, 1.5100), (0.0240, -0.0580, 1.5100), (0.0265, -0.0500, 1.5125),
       (0.0280, -0.0460, 1.5130), (RT.x, RT.y - 0.0035, min(z_under, mid_bottom - 0.0016 - NR)), (RT.x, RT.y, z_under), (RT.x + 0.0008, RT.y + 0.0035, z_under + 0.0010),
       (0.0360, -0.0200, z_under + 0.0060), (0.0375, -0.0130, 1.5390), (0.0365, -0.0085, 1.5500)]
for (x, y, z) in pts:
    lb = lower_border(y); print('nerve pt y=%.4f z=%.4f lower_border=%s' % (y, z, None if lb is None else round(lb, 4)))
def tube(name, r, mat):
    cu_ = D.curves.new(name, 'CURVE'); cu_.dimensions = '3D'
    sp_ = cu_.splines.new('BEZIER'); sp_.bezier_points.add(len(pts) - 1)
    for bp, pp in zip(sp_.bezier_points, pts):
        bp.co = pp; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu_.bevel_depth = r; cu_.bevel_resolution = 6; cu_.use_fill_caps = True; cu_.resolution_u = 24
    ob = link(D.objects.new(name, cu_)); setmat(ob, mat); return ob
mNerve2, nt, out, p = newmat('Nerve2')
p.inputs['Base Color'].default_value = (0.98, 0.82, 0.30, 1); p.inputs['Roughness'].default_value = 0.3
p.inputs['Subsurface Weight'].default_value = 0.6; p.inputs['Subsurface Radius'].default_value = (1, 0.8, 0.3); p.inputs['Subsurface Scale'].default_value = 0.0008
p.inputs['Coat Weight'].default_value = 0.4; p.inputs['Emission Color'].default_value = (1.0, 0.80, 0.25, 1)
NERVE2_EM = nt.nodes.new('ShaderNodeValue'); nt.links.new(NERVE2_EM.outputs[0], p.inputs['Emission Strength'])
# fibre striation along the tube
tc_ = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 900
nt.links.new(tc_.outputs['Object'], wv.inputs['Vector']); bmp = nt.nodes.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.15
nt.links.new(wv.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
nt.links.new(p.outputs[0], out.inputs['Surface'])
NERVE2 = tube('Nerve2', NR, mNerve2)
mCan2, nt, out, p = newmat('Canal2')
p.inputs['Base Color'].default_value = (0.70, 0.58, 0.44, 1); p.inputs['Roughness'].default_value = 0.4
CAN2_G = ghostable(nt, out, p.outputs[0], 'Ghost', 0.06, 0.7, 0.3); CAN2_G.outputs[0].default_value = 1.0
CANAL2 = tube('Canal2', CR, mCan2); CANAL2.hide_render = True
# ---- contact glow (single highlight colour = the wisdom tooth's) ----
mCG, nt, out, p = newmat('ContactGlow')
emc = nt.nodes.new('ShaderNodeEmission'); emc.inputs['Color'].default_value = (1.0, 0.55, 0.18, 1)
CG_S = nt.nodes.new('ShaderNodeValue'); nt.links.new(CG_S.outputs[0], emc.inputs['Strength'])
lwc = nt.nodes.new('ShaderNodeLayerWeight'); lwc.inputs['Blend'].default_value = 0.6
trc = nt.nodes.new('ShaderNodeBsdfTransparent'); msc = nt.nodes.new('ShaderNodeMixShader')
inv_ = nt.nodes.new('ShaderNodeMath'); inv_.operation = 'POWER'; inv_.inputs[1].default_value = 2.0
nt.links.new(lwc.outputs['Facing'], inv_.inputs[0])
nt.links.new(inv_.outputs[0], msc.inputs['Fac']); nt.links.new(emc.outputs[0], msc.inputs[1]); nt.links.new(trc.outputs[0], msc.inputs[2])
nt.links.new(msc.outputs[0], out.inputs['Surface'])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.0024)
GLW = D.objects.new('ContactGlow', D.meshes.new('cgl')); bm.to_mesh(GLW.data); bm.free(); link(GLW); setmat(GLW, mCG)
for pg in GLW.data.polygons: pg.use_smooth = True
GLW.location = CONTACT
vkey(CG_S, 0, 0.0); vkey(CG_S, 8, 0.0); vkey(CG_S, 16, 7.0); vkey(CG_S, 40, 0.0)
GLW.hide_render = True
M2.rotation_mode = 'XYZ'
for _f, _r in ((2, 0), (8, -1.6), (16, -1.6), (26, 0)):
    M2.rotation_euler = (R(_r), 0, 0); M2.keyframe_insert('rotation_euler', frame=_f)
# tooth tint swells with the pulse (same hue)
vkey(T3_EM, 0, 0.0); vkey(T3_EM, 3, 0.0); vkey(T3_EM, 15, 0.6); vkey(T3_EM, 27, 0.08)
# ---- section: bur from the occlusal side, kerf, dust, halves separate ----
BUR0, BUR1 = 92, 152
zt, zb = hi.z + 0.0085, hi.z + 0.008 - (hi.z - lo.z) * 0.66
for o in (slot, slotR):
    o.scale = (0.012, 0.0016, 0.016)
    for f, z in ((BUR0 + 6, zt), (BUR1, zb)):
        o.location = Vector((C3.x + 0.0005, split_y, z)); o.keyframe_insert('location', frame=f)
vtip = lambda f: Vector((C3.x + 0.0005, split_y, (zt - 0.008) + ((zb - 0.008) - (zt - 0.008)) * max(0, min(1, (f - BUR0 - 6) / (BUR1 - BUR0 - 6)))))
burrot = (R(-10), R(8), 0)
place_tool(HP, 78, vtip(BUR0 + 6) + Vector((0.004, -0.006, 0.03)), burrot)
place_tool(HP, BUR0 + 6, vtip(BUR0 + 6), burrot)
for k in range(1, 7):
    f = BUR0 + 6 + k * (BUR1 - BUR0 - 6) // 6
    place_tool(HP, f, vtip(f) + Vector((0, 0.00025 * (-1) ** k, 0)), burrot)
place_tool(HP, BUR1 + 18, vtip(BUR1) + Vector((0.004, -0.004, 0.03)), burrot)
tool_vis(HP, [(78, BUR1 + 18)])
for nm in ('HpHead', 'HpNeck', 'HpBody'):
    O[nm].animation_data_clear(); O[nm].hide_render = True
shk = O['BurShank']; shk.scale = (1, 1, 3.2); shk.location.z = 0.005 + 0.0192
pg_ = [n for n in mGold.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
pg_.inputs['Base Color'].default_value = (0.78, 0.74, 0.62, 1); pg_.inputs['Roughness'].default_value = 0.35
noise_bump(mGold.node_tree, pg_, 9000, 1.0, 0.00004, voronoi=True)
rnd = random.Random(5)
mDust, nt, out, p = newmat('Dust'); p.inputs['Base Color'].default_value = (0.95, 0.90, 0.80, 1); p.inputs['Roughness'].default_value = 0.6
nt.links.new(p.outputs[0], out.inputs['Surface'])
for i in range(36):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rnd.uniform(0.00008, 0.00018))
    dd = D.objects.new('Dust%d' % i, D.meshes.new('dust%d' % i)); bm.to_mesh(dd.data); bm.free(); link(dd); setmat(dd, mDust)
    fb = rnd.randint(BUR0 + 8, BUR1 - 4); life = rnd.randint(8, 16)
    p0 = vtip(fb) + Vector((0, 0, 0.0002)); vel = Vector((rnd.uniform(0.2, 1.0), rnd.uniform(-0.6, 0.6), rnd.uniform(0.3, 1.0))).normalized() * rnd.uniform(0.004, 0.009)
    dd.location = p0; dd.scale = (1, 1, 1); dd.keyframe_insert('location', frame=fb); dd.keyframe_insert('scale', frame=fb)
    dd.location = p0 + vel + Vector((0, 0, -0.003)); dd.scale = (0.2, 0.2, 0.2)
    dd.keyframe_insert('location', frame=fb + life); dd.keyframe_insert('scale', frame=fb + life)
    vis(dd, [(fb, fb + life)])
# halves: root backs off distally (gap opens), crown lifts out, then root follows
C_OUT = 176
kloc(ROOT, BUR1 + 8, cr0); krot(ROOT, BUR1 + 8, (0, 0, 0))
kloc(ROOT, BUR1 + 20, cr0 + Vector((0, 0.0009, 0))); 
kloc(CROWN, BUR1 + 20, cl0); krot(CROWN, BUR1 + 20, (0, 0, 0))
kloc(CROWN, C_OUT + 6, cl0 + Vector((0.0004, 0.0003, 0.0016))); krot(CROWN, C_OUT + 6, (R(-6), 0, 0))
kloc(CROWN, C_OUT + 40, cl0 + Vector((0.004, 0.0015, 0.011))); krot(CROWN, C_OUT + 40, (R(-25), R(10), R(-8)))
kloc(CROWN, C_OUT + 56, cl0 + Vector((0.012, 0.002, 0.045))); krot(CROWN, C_OUT + 56, (R(-40), R(16), R(-14)))
vis(CROWN, [(0, C_OUT + 56)])
R_OUT = 206
kloc(ROOT, R_OUT, cr0 + Vector((0, 0.0009, 0))); krot(ROOT, R_OUT, (0, 0, 0))
kloc(ROOT, R_OUT + 12, cr0 + Vector((0.0002, -0.0045, 0.0004))); krot(ROOT, R_OUT + 12, (R(4), 0, 0))
kloc(ROOT, R_OUT + 30, cr0 + Vector((0.0015, -0.0050, 0.012))); krot(ROOT, R_OUT + 30, (R(12), 0, 0))
kloc(ROOT, R_OUT + 44, cr0 + Vector((0.004, -0.0050, 0.040))); krot(ROOT, R_OUT + 44, (R(16), 0, 0))
vis(ROOT, [(0, R_OUT + 44)])





# ---- nerve reveal + gap bracket ----
vkey(NERVE2_EM, 0, 0.25); vkey(NERVE2_EM, 238, 0.25)
for i in range(2):
    vkey(NERVE2_EM, 256 + i * 20, 5.0); vkey(NERVE2_EM, 266 + i * 20, 0.8)
vkey(NERVE2_EM, E0, 1.6)
floor_z = root_bottom - 0.0002; ntop2 = z_under + NR
gy2 = RT.y
mGap2, nt, out, p = newmat('GapGlow2')
em3 = nt.nodes.new('ShaderNodeEmission'); em3.inputs['Color'].default_value = (1.0, 0.95, 0.80, 1)
GAP2 = nt.nodes.new('ShaderNodeValue'); nt.links.new(GAP2.outputs[0], em3.inputs['Strength']); nt.links.new(em3.outputs[0], out.inputs['Surface'])
gx = RT.x + 0.0025
gl = cyl('Gap2', 0.00022, floor_z - ntop2, mGap2, 16, None, (gx, gy2, (floor_z + ntop2) / 2))
gc = [cyl('Gap2c%d' % i, 0.0013, 0.00016, mGap2, 24, None, (gx, gy2, z)) for i, z in enumerate((floor_z, ntop2))]
for o in [gl] + gc: setmat(o, mGap2); vis(o, [(248, E0 + 1)])
vkey(GAP2, 248, 0.0); vkey(GAP2, 254, 12.0); vkey(GAP2, E0, 12.0)
print('gap mm', round((floor_z - ntop2) * 1000, 2))
# ---- one camera, one continuous move (roll levels the occlusal plane) ----
from mathutils import Quaternion
cd = D.cameras.new('CamV2'); cd.lens = 55; cd.clip_start = 0.002; cd.clip_end = 5
cd.dof.use_dof = True; cd.dof.aperture_fstop = 8.0
CAMV = link(D.objects.new('CamV2', cd)); CAMV.rotation_mode = 'QUATERNION'
FOC = link(D.objects.new('FocusV2', None)); cd.dof.focus_object = FOC
ROLL = R(float(__import__('os').environ.get('ROLL', '15')))
def ckey(f, tgt, dvec, dist):
    loc = tgt + dvec.normalized() * dist
    q = (tgt - loc).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), ROLL)
    CAMV.location = loc; CAMV.rotation_quaternion = q
    CAMV.keyframe_insert('location', frame=f); CAMV.keyframe_insert('rotation_quaternion', frame=f)
    FOC.location = tgt; FOC.keyframe_insert('location', frame=f)
J = Vector((0.030, -0.042, 1.526))
MID = Vector((((m2lo.x + m2hi.x) / 2 + C3.x) / 2, (m2lo.y + hi.y) / 2, C3.z - 0.001))
ckey(0, MID + Vector((0, -0.004, 0.006)), Vector((1, -0.10, 0.14)), 0.150)
ckey(60, C3 + Vector((0, -0.003, 0.0)), Vector((1, -0.10, 0.16)), 0.085)
ckey(BUR0 + 10, C3 + Vector((0, -0.002, 0.002)), Vector((0.9, -0.22, 0.38)), 0.070)
ckey(BUR1, C3 + Vector((0, -0.002, 0.002)), Vector((0.9, -0.2, 0.42)), 0.064)
ckey(214, C3 + Vector((0, -0.002, 0.004)), Vector((0.95, -0.22, 0.30)), 0.074)
ckey(248, Vector((RT.x, RT.y - 0.002, (floor_z + ntop2) / 2)), Vector((1, -0.06, 0.10)), 0.052)
ckey(E0, Vector((RT.x, RT.y - 0.001, (floor_z + ntop2) / 2)), Vector((1, -0.05, 0.08)), 0.044)
sc.camera = CAMV
# bake the static bone: subsurf + crypt boolean applied once (no per-frame boolean)
sc.frame_set(0); sel_only(MAND)
for mname in [m.name for m in MAND.modifiers]:
    bpy.ops.object.modifier_apply(modifier=mname)
sc.frame_start = 0; sc.frame_end = E0 - 1
sc.render.use_motion_blur = False
sc.render.resolution_y = 800

# ---------------- lights & world ----------------
rig_t = link(D.objects.new('LightTarget', None)); rig_t.location = C3
def area(name, off, energy, size, color):
    d = D.lights.new(name, 'AREA'); d.energy = energy; d.size = size; d.color = color
    o = link(D.objects.new(name, d)); o.location = C3 + Vector(off)
    t = o.constraints.new('TRACK_TO'); t.target = rig_t; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
    return o
area('Key', (0.30, -0.22, 0.42), 4, 0.25, (1.0, 0.94, 0.86))
area('Fill', (0.35, 0.05, -0.05), 0.35, 0.4, (0.8, 0.88, 1.0))
area('Rim', (-0.10, 0.35, 0.22), 28, 0.15, (0.75, 0.88, 1.0))
area('Rim2', (0.10, 0.30, 0.25), 4, 0.12, (1.0, 0.85, 0.7))
area('Top', (0.02, -0.02, 0.30), 0.8, 0.2, (1.0, 0.97, 0.94))
w = D.worlds.new('W'); sc.world = w; w.use_nodes = True
wt = w.node_tree; bgn = wt.nodes['Background']
env = wt.nodes.new('ShaderNodeTexEnvironment')
env.image = D.images.load((__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/anatomy3d/polyhaven/studio_small_09_2k.exr'))
wt.links.new(env.outputs['Color'], bgn.inputs['Color']); bgn.inputs['Strength'].default_value = 0.14  # CC0 Poly Haven studio: reflections on enamel/steel/wet tissue

# ---------------- render settings ----------------
r = sc.render; r.engine = 'CYCLES'; r.resolution_x = 1080; r.resolution_y = 800; r.film_transparent = True
cy = sc.cycles; cy.device = 'GPU'; cy.samples = 64; cy.use_denoising = True; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.transparent_max_bounces = 16; cy.max_bounces = 8; cy.transmission_bounces = 8
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.45
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.use_persistent_data = True
bpy.ops.wm.save_as_mainfile(filepath=HERE + 'wisdom.blend')
print('SAVED')
