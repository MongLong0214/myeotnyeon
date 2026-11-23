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
SH = dict(S1=0, S1b=66, S2=138, S3=249, S4=360, S5=474, S5b=540, S6=600, S7=804, S8=939, S9=1101, S10=1262, END=1305)
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
T3.rotation_euler = (math.radians(84), 0, math.radians(-8)); T3.scale = (0.88, 0.88, 0.88)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
lo, hi = world_bbox(T3)
m2lo, m2hi = world_bbox(M2)
# crown (now pointing -y) touches the distal of the 2nd molar a little below its crown
T3.location += Vector((0.0335 - (lo.x + hi.x) / 2, (m2hi.y - 0.0004) - lo.y, 1.5315 - (lo.z + hi.z) / 2))
bpy.context.view_layer.update()
sel_only(T3); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
lo, hi = world_bbox(T3)
C3 = (lo + hi) / 2
print("T3 bbox", tuple(round(x, 4) for x in lo), tuple(round(x, 4) for x in hi))

# ---------------- nerve: keep the canal ~1.4 mm under the roots ----------------
mwN = NERVE.matrix_world; mwi = mwN.inverted()
nb = [mwN @ v.co for v in NERVE.data.vertices]
target = lo.z - 0.0014
def top_at(y):
    s = [v.z for v in nb if abs(v.y - y) < 0.0008 and abs(v.x - C3.x) < 0.012]
    return max(s) if s else None
need = {}
for i in range(-60, 1):
    y = i * 0.001
    t = top_at(y)
    if t is None: continue
    need[i] = max(0.0, t - target) if lo.y - 0.001 <= y <= hi.y + 0.001 else None
# taper outside the tooth span
def dz(y):
    if lo.y - 0.001 <= y <= hi.y + 0.001:
        i = round(y / 0.001); vals = [need.get(j) for j in (i - 1, i, i + 1) if need.get(j) is not None]
        return max(vals) if vals else 0.0
    if y < lo.y - 0.001:
        k = max(0.0, 1 - (lo.y - 0.001 - y) / 0.010); k = k * k * (3 - 2 * k)
        return dz(lo.y - 0.001) * k
    k = max(0.0, 1 - (y - hi.y - 0.001) / 0.012); k = k * k * (3 - 2 * k)
    return dz(hi.y + 0.001) * k
for v in NERVE.data.vertices:
    w = mwN @ v.co
    w.z -= dz(w.y)
    v.co = mwi @ w
print("nerve shift max", round(max([x for x in need.values() if x is not None] or [0]), 4))

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
    colvar(nt, p, (0.80, 0.72, 0.58, 1), (0.70, 0.60, 0.46, 1), 900)
    p.inputs['Subsurface Weight'].default_value = 0.12; p.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.4)
    p.inputs['Subsurface Scale'].default_value = 0.0015; p.inputs['Roughness'].default_value = 0.55
    noise_bump(nt, p, 2600, 0.25, 0.00012, voronoi=True)
    p.inputs['Emission Color'].default_value = (1.0, 0.22, 0.05, 1)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; em.outputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], p.inputs['Emission Strength'])
    g = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.5)
    return m, g, em
mBone, BONE_G, _ = bone_material('Bone')
mMand, MAND_G, _ = bone_material('MandBone')

# cut (cancellous) bone: socket walls and drilled window
mCut, nt, out, p = newmat('CutBone')
colvar(nt, p, (0.78, 0.50, 0.40, 1), (0.62, 0.30, 0.24, 1), 1400)
p.inputs['Subsurface Weight'].default_value = 0.2; p.inputs['Subsurface Radius'].default_value = (1.0, 0.4, 0.3)
p.inputs['Subsurface Scale'].default_value = 0.001; p.inputs['Roughness'].default_value = 0.35
noise_bump(nt, p, 4200, 0.6, 0.00015, voronoi=True)
p.inputs['Emission Color'].default_value = (1.0, 0.18, 0.04, 1)
CUT_EM = nt.nodes.new('ShaderNodeValue'); CUT_EM.name = 'Emit'; CUT_EM.outputs[0].default_value = 0.0
nt.links.new(CUT_EM.outputs[0], p.inputs['Emission Strength'])
CUT_G = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.5)

# enamel
def enamel(name, glow=False):
    m, nt, out, p = newmat(name)
    p.inputs['Base Color'].default_value = (0.92, 0.90, 0.84, 1)
    p.inputs['Subsurface Weight'].default_value = 0.25; p.inputs['Subsurface Radius'].default_value = (1.0, 0.8, 0.6)
    p.inputs['Subsurface Scale'].default_value = 0.0012
    p.inputs['Roughness'].default_value = 0.16; p.inputs['Coat Weight'].default_value = 0.8; p.inputs['Coat Roughness'].default_value = 0.05
    noise_bump(nt, p, 1800, 0.05, 0.00005)
    p.inputs['Emission Color'].default_value = (1.0, 0.55, 0.08, 1)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; em.outputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], p.inputs['Emission Strength'])
    tint = nt.nodes.new('ShaderNodeValue'); tint.name = 'Tint'; tint.outputs[0].default_value = 0.0
    if glow:
        # base colour shifts toward amber while highlighted
        mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
        mixc.inputs['A'].default_value = (0.92, 0.90, 0.84, 1); mixc.inputs['B'].default_value = (1.0, 0.62, 0.18, 1)
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
mSteel = metal('Steel', 0.14, 0.5)
mSteelDark = metal('SteelBrushed', 0.32, 0.8, (0.7, 0.7, 0.72, 1))
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

# ---------------- retromolar gum pad + flap ----------------
mand_bvh = BVHTree.FromObject(MAND, bpy.context.evaluated_depsgraph_get())
pad = MAND.copy(); pad.data = MAND.data.copy(); pad.name = 'GumPad'; link(pad)
bm = bmesh.new(); bm.from_mesh(pad.data)
mw = pad.matrix_world
y0, y1 = m2hi.y - 0.0035, hi.y + 0.004
kill = []
for f in bm.faces:
    c = mw @ f.calc_center_median(); nrm = (mw.to_3x3() @ f.normal).normalized()
    keep = (y0 < c.y < y1) and (C3.x - 0.0075 < c.x < C3.x + 0.0105) and (c.z > C3.z - 0.0005) and nrm.z > -0.15 and c.z < hi.z + 0.006
    if not keep: kill.append(f)
bmesh.ops.delete(bm, geom=kill, context='FACES')
bm.to_mesh(pad.data); bm.free()
sel_only(pad)
sol = pad.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.0016; sol.offset = 1.0; sol.use_rim = True
sm = pad.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.6; sm.iterations = 6
pad.modifiers.new('sub', 'SUBSURF').levels = 2
setmat(pad, mGum)
pad.data.materials.append(mFlapInner)
bpy.ops.object.modifier_apply(modifier='sol'); bpy.ops.object.modifier_apply(modifier='sm')
# split buccal half -> flap
pad_lo, pad_hi = world_bbox(pad)
FX = C3.x + 0.0005
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
for v in pad.data.vertices:
    v.select = (pad.matrix_world @ v.co).x > FX
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
FLAP = [o for o in O if o.name.startswith('GumPad.')][0]; FLAP.name = 'Flap'
# hinge: buccal lower edge of flap, axis along y
flo, fhi = world_bbox(FLAP)
hinge = Vector((fhi.x - 0.0005, (flo.y + fhi.y) / 2, flo.z + 0.0005))
sel_only(FLAP); sc.cursor.location = hinge; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
print("pad", tuple(round(x, 4) for x in pad_lo), tuple(round(x, 4) for x in pad_hi))

# incision curve along the crest (FX) from 2nd molar distal to retromolar + small releasing cut
def top_z(x, y):
    hit = mand_bvh.ray_cast(Vector((x, y, 1.62)), Vector((0, 0, -1)))
    return (hit[0].z if hit[0] else C3.z) + 0.0017
pts = [Vector((FX, y0 + (y1 - y0) * t, 0)) for t in [i / 14 for i in range(15)]]
for pt in pts: pt.z = top_z(pt.x, pt.y)
rel = [Vector((FX + 0.0018 * i, y0 - 0.0002, top_z(FX, y0) - 0.0016 * i)) for i in range(1, 5)]
path_pts = list(reversed(rel)) + pts
cu = D.curves.new('IncisionC', 'CURVE'); cu.dimensions = '3D'
sp = cu.splines.new('POLY'); sp.points.add(len(path_pts) - 1)
for i, pt in enumerate(path_pts): sp.points[i].co = (pt.x, pt.y, pt.z, 1)
cu.bevel_depth = 0.00028; cu.bevel_resolution = 3; cu.use_fill_caps = True
INC = link(D.objects.new('Incision', cu)); setmat(INC, mCutLine)
cu.bevel_factor_mapping_end = 'SPLINE'
INC_PTS = path_pts

# ---------------- bone cavity + window (boolean) ----------------
cutters = D.collections.new('Cutters'); sc.collection.children.link(cutters)
cav = T3.copy(); cav.data = T3.data.copy(); cav.name = 'CavityCutter'; cutters.objects.link(cav)
cav.scale = (1.06, 1.06, 1.06); setmat(cav, mCut)
win = D.objects.new('WindowCutter', D.meshes.new('win')); cutters.objects.link(win)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(win.data); bm.free()
bv = win.modifiers.new('bev', 'BEVEL'); bv.width = 0.25; bv.segments = 4
win.location = Vector((C3.x + 0.0045, C3.y + 0.001, hi.z + 0.0005))
win.rotation_euler = (0, math.radians(-28), 0)
setmat(win, mCut)
cutters.hide_render = True
for o in cutters.objects: o.hide_render = True; o.display_type = 'WIRE'
bo = MAND.modifiers.new('carve', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.operand_type = 'COLLECTION'; bo.collection = cutters
bo.solver = 'EXACT'; bo.use_hole_tolerant = True; bo.material_mode = 'TRANSFER'
# window grows during S3
for f, s in [(SH['S3'] + 6, (0.0001, 0.0001, 0.0001)), (SH['S3'] + 30, (0.0075, 0.010, 0.006)), (SH['S3'] + 80, (0.0125, 0.0175, 0.0095))]:
    win.scale = s; win.keyframe_insert('scale', frame=f)

# ---------------- crown / root split ----------------
split_y = lo.y + (hi.y - lo.y) * 0.47
def halfbox(name, ymin, ymax):
    o = D.objects.new(name, D.meshes.new(name)); cutters.objects.link(o) if False else None
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(o.data); bm.free()
    o.location = Vector((C3.x, (ymin + ymax) / 2, C3.z)); o.scale = (0.05, ymax - ymin, 0.05)
    o.hide_render = True; o.display_type = 'WIRE'; link(o); return o
boxC = halfbox('CrownBox', split_y - 0.05, split_y)
slot = D.objects.new('Slot', D.meshes.new('slot')); link(slot)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(slot.data); bm.free()
slot.hide_render = True; slot.display_type = 'WIRE'; setmat(slot, mCut)
slot.scale = (0.016, 0.0011, 0.016)
CROWN = T3.copy(); CROWN.data = T3.data.copy(); CROWN.name = 'Crown'; link(CROWN)
ROOT = T3.copy(); ROOT.data = T3.data.copy(); ROOT.name = 'Root'; link(ROOT)
for o, op in [(CROWN, 'INTERSECT'), (ROOT, 'DIFFERENCE')]:
    b = o.modifiers.new('half', 'BOOLEAN'); b.object = boxC; b.operation = op; b.solver = 'EXACT'; b.use_hole_tolerant = True; b.material_mode = 'TRANSFER'
    b2 = o.modifiers.new('slot', 'BOOLEAN'); b2.object = slot; b2.operation = 'DIFFERENCE'; b2.solver = 'EXACT'; b2.use_hole_tolerant = True; b2.material_mode = 'TRANSFER'
setmat(boxC, mT3)
# dentin colour on cut faces
mDentin, nt, out, p = newmat('Dentin')
p.inputs['Base Color'].default_value = (0.93, 0.82, 0.62, 1); p.inputs['Roughness'].default_value = 0.4
p.inputs['Subsurface Weight'].default_value = 0.3; p.inputs['Subsurface Radius'].default_value = (1, 0.7, 0.4); p.inputs['Subsurface Scale'].default_value = 0.001
nt.links.new(p.outputs[0], out.inputs['Surface'])
setmat(slot, mDentin); setmat(boxC, mDentin)
for o in (CROWN, ROOT):
    o.data.materials.clear(); o.data.materials.append(mT3)
# slot descends through the tooth during S4 (top -> bottom), along split plane
slot.location = Vector((C3.x + 0.001, split_y, hi.z + 0.008))
for f, z in [(SH['S4'] + 10, hi.z + 0.008), (SH['S4'] + 75, lo.z + 0.0035)]:
    slot.location.z = z; slot.keyframe_insert('location', index=2, frame=f)
T3.hide_render = True  # Crown+Root stand in for the whole tooth everywhere

# crown out (S5), root out (S5b..S6)
for o in (CROWN, ROOT):
    sel_only(o); sc.cursor.location = (Vector(world_bbox(o)[0]) + Vector(world_bbox(o)[1])) / 2
crown_c = (world_bbox(T3)[0] + Vector((0, 0, 0)))
def set_origin(o, p):
    sel_only(o); sc.cursor.location = p; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
set_origin(CROWN, Vector((C3.x, (lo.y + split_y) / 2, C3.z)))
set_origin(ROOT, Vector((C3.x, (split_y + hi.y) / 2, C3.z)))
cl0, cr0 = CROWN.location.copy(), ROOT.location.copy()
def kloc(o, f, p):
    o.location = p; o.keyframe_insert('location', frame=f)
def krot(o, f, r):
    o.rotation_euler = r; o.keyframe_insert('rotation_euler', frame=f)
kloc(CROWN, SH['S5'] + 4, cl0); krot(CROWN, SH['S5'] + 4, (0, 0, 0))
kloc(CROWN, SH['S5'] + 16, cl0 + Vector((0.0004, 0.0012, 0.0012))); krot(CROWN, SH['S5'] + 16, (math.radians(-8), 0, 0))
kloc(CROWN, SH['S5'] + 50, cl0 + Vector((0.004, 0.004, 0.016))); krot(CROWN, SH['S5'] + 50, (math.radians(-35), math.radians(10), 0))
kloc(CROWN, SH['S5'] + 66, cl0 + Vector((0.008, 0.006, 0.05))); krot(CROWN, SH['S5'] + 66, (math.radians(-50), math.radians(14), 0))
vis(CROWN, [(0, SH['S5'] + 66)])
# root: mesial into the crown space, then up
kloc(ROOT, SH['S5b'] + 10, cr0); krot(ROOT, SH['S5b'] + 10, (0, 0, 0))
kloc(ROOT, SH['S6'] + 30, cr0 + Vector((0.0, -0.0035, 0.0008))); krot(ROOT, SH['S6'] + 30, (math.radians(4), 0, 0))
kloc(ROOT, SH['S6'] + 110, cr0 + Vector((0.0, -0.0050, 0.0080))); krot(ROOT, SH['S6'] + 110, (math.radians(28), 0, 0))
kloc(ROOT, SH['S6'] + 170, cr0 + Vector((0.002, -0.004, 0.040))); krot(ROOT, SH['S6'] + 170, (math.radians(40), math.radians(8), 0))
vis(ROOT, [(0, SH['S6'] + 170)])

# ---------------- clot ----------------
CLOT = cav.copy(); CLOT.data = T3.data.copy(); CLOT.name = 'Clot'; link(CLOT)
CLOT.modifiers.clear()
sel_only(CLOT); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
CLOT.scale = (1.0, 1.0, 1.0)
rm = CLOT.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.00035
dp = CLOT.modifiers.new('disp', 'DISPLACE'); tx = D.textures.new('clotn', 'CLOUDS'); tx.noise_scale = 0.0012; dp.texture = tx; dp.strength = 0.0005; dp.mid_level = 0.5
CLOT.modifiers.new('sm', 'SMOOTH').iterations = 4
setmat(CLOT, mClot)
CLOT.hide_render = False
c0 = CLOT.location.copy()
# fill from the bottom: scale z up from the socket floor
for f, s, dz in [(SH['S7'] + 2, 0.15, -0.004), (SH['S7'] + 45, 1.04, 0.0)]:
    CLOT.scale = (1.04, 1.04, s); CLOT.location = c0 + Vector((0, 0, dz))
    CLOT.keyframe_insert('scale', frame=f); CLOT.keyframe_insert('location', frame=f)
# dry socket: clot pulled out (S9)
for f, dz, r in [(SH['S9'] + 20, 0.0, 0), (SH['S9'] + 40, 0.003, 6), (SH['S9'] + 95, 0.03, 25)]:
    CLOT.location = c0 + Vector((0, 0, dz)); CLOT.rotation_euler = (math.radians(r), 0, 0)
    CLOT.keyframe_insert('location', frame=f); CLOT.keyframe_insert('rotation_euler', frame=f)
vis(CLOT, [(SH['S7'] + 2, SH['S9'] + 95)])

# ---------------- flap animation ----------------
krot(FLAP, SH['S2'] + 50, (0, 0, 0))
krot(FLAP, SH['S2'] + 95, (0, math.radians(-62), 0))
krot(FLAP, SH['S7'] + 48, (0, math.radians(-62), 0))
krot(FLAP, SH['S7'] + 78, (0, 0, 0))
# incision draws S2 (scalpel follows)
cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=SH['S2'] + 8)
cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=SH['S2'] + 46)
vis(INC, [(SH['S2'] + 8, SH['S7'] + 78)])

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

# scalpel follows the incision points during S2
n_pts = len(INC_PTS)
f0, f1 = SH['S2'] + 8, SH['S2'] + 46
srot = (math.radians(-35), math.radians(25), math.radians(15))
place_tool(SCAL, f0 - 10, INC_PTS[0] + Vector((0.004, -0.004, 0.012)), srot)
for i, ptt in enumerate(INC_PTS):
    place_tool(SCAL, int(f0 + (f1 - f0) * i / (n_pts - 1)), ptt + Vector((0, 0, -0.0006)), srot)
place_tool(SCAL, f1 + 14, INC_PTS[-1] + Vector((0.004, 0.006, 0.02)), srot)
tool_vis(SCAL, [(SH['S2'], SH['S2'] + 62)])
# bur: S3 sweeps around the window, S4 down the slot
hrot = (math.radians(-10), math.radians(28), math.radians(-20))
wc = win.location
path3 = [wc + Vector((0.000, -0.004, 0.002)), wc + Vector((-0.001, 0.0, 0.0)), wc + Vector((0.0, 0.004, -0.001)), wc + Vector((0.001, 0.006, 0.0)), wc + Vector((0.0, 0.002, 0.001))]
place_tool(HP, SH['S3'] - 2, path3[0] + Vector((0.006, 0, 0.01)), hrot)
for i, ptt in enumerate(path3):
    place_tool(HP, SH['S3'] + 8 + i * 18, ptt, hrot)
place_tool(HP, SH['S3'] + 100, path3[-1] + Vector((0.004, 0, 0.012)), hrot)
vrot = (math.radians(0), math.radians(12), 0)
place_tool(HP, SH['S4'] + 2, Vector((C3.x + 0.001, split_y, hi.z + 0.01)), vrot)
place_tool(HP, SH['S4'] + 10, Vector((C3.x + 0.001, split_y, hi.z + 0.0005)), vrot)
place_tool(HP, SH['S4'] + 75, Vector((C3.x + 0.001, split_y, lo.z + 0.0040)), vrot)
place_tool(HP, SH['S4'] + 100, Vector((C3.x + 0.001, split_y, hi.z + 0.012)), vrot)
tool_vis(HP, [(SH['S3'], SH['S4'] + 110)])
# elevator: wedges into the slot and lifts crown (S5), then root (S5b)
erot = (math.radians(15), math.radians(20), 0)
place_tool(EL, SH['S5'] - 4, Vector((C3.x + 0.003, split_y, hi.z + 0.012)), erot)
place_tool(EL, SH['S5'] + 4, Vector((C3.x + 0.0015, split_y, hi.z - 0.002)), erot)
place_tool(EL, SH['S5'] + 16, Vector((C3.x + 0.0015, split_y, hi.z - 0.0015)), (math.radians(35), math.radians(20), 0))
place_tool(EL, SH['S5'] + 40, Vector((C3.x + 0.006, split_y + 0.004, hi.z + 0.02)), erot)
place_tool(EL, SH['S5b'] + 2, Vector((C3.x + 0.002, split_y - 0.002, hi.z + 0.0)), (math.radians(-10), math.radians(15), 0))
place_tool(EL, SH['S5b'] + 30, Vector((C3.x + 0.002, split_y - 0.0025, hi.z - 0.001)), (math.radians(-25), math.radians(15), 0))
tool_vis(EL, [(SH['S5'] - 4, SH['S6'])])
# needle: three passes along the incision (S7)
nrot0 = (math.radians(90), 0, math.radians(90))
stitch_y = [y0 + (y1 - y0) * t for t in (0.22, 0.5, 0.78)]
for i, sy in enumerate(stitch_y):
    base = Vector((FX, sy, top_z(FX, sy) + 0.0005))
    fa = SH['S7'] + 80 + i * 18
    place_tool(NEED, fa, base + Vector((0.003, 0, 0.004)), nrot0)
    place_tool(NEED, fa + 9, base + Vector((0.0, 0, 0.0005)), (math.radians(90), 0, math.radians(90 + 90)))
tool_vis(NEED, [(SH['S7'] + 78, SH['S7'] + 135)])
# sutures: small thread loops appearing after each pass
for i, sy in enumerate(stitch_y):
    base = Vector((FX, sy, top_z(FX, sy) + 0.0003))
    tc = D.curves.new(f'st{i}', 'CURVE'); tc.dimensions = '3D'
    s = tc.splines.new('BEZIER'); s.bezier_points.add(3)
    pts4 = [base + Vector((-0.0024, 0, -0.0009)), base + Vector((-0.0008, 0.0003, 0.0007)), base + Vector((0.0008, -0.0003, 0.0007)), base + Vector((0.0024, 0, -0.0009))]
    for bp, pp in zip(s.bezier_points, pts4):
        bp.co = pp; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    tc.bevel_depth = 0.00018; tc.bevel_resolution = 2
    so = link(D.objects.new(f'Suture{i}', tc)); setmat(so, mThread)
    fa = SH['S7'] + 80 + i * 18 + 10
    tc.bevel_factor_end = 0.0; tc.keyframe_insert('bevel_factor_end', frame=fa)
    tc.bevel_factor_end = 1.0; tc.keyframe_insert('bevel_factor_end', frame=fa + 8)
    vis(so, [(fa, SH['S9'] + 20), (SH['S10'], SH['END'])])
# straw (S8-S9): descends toward the mouth from above-front
stl = Vector((C3.x + 0.002, C3.y - 0.004, hi.z + 0.012))
place_tool(STRAW, SH['S8'] + 60, stl + Vector((0.0, -0.01, 0.06)), (math.radians(-18), 0, 0))
place_tool(STRAW, SH['S8'] + 95, stl, (math.radians(-18), 0, 0))
tool_vis(STRAW, [(SH['S8'] + 60, SH['S9'] + 110)])

# ---------------- visibility per shot ----------------
head_shots = [(SH['S1'], SH['S2']), (SH['S10'], SH['END'])]
for o in [SKIN] + upper_skull + GUM_UP:
    vis(o, head_shots)
# lower gingiva / pad / flap always on; flap closed in loop-end
# nerve visible in hook (faint), S6 and S8/S9 cut views
vis(NERVE, [(SH['S1'], SH['S2']), (SH['S6'], SH['S7'])])
for n in ('Mental nerve.l', 'Lingual nerve.l'):
    if n in O: vis(O[n], [(SH['S6'], SH['S7'])])

# ---------------- ghost / glow animation ----------------
# hook: skin ghost already at 0.85 on frame 0 (hook needs the reveal now), full by 20
vkey(SKIN_G, 0, 0.75); vkey(SKIN_G, 22, 1.0)
vkey(BONE_G, 0, 0.6); vkey(BONE_G, 22, 0.85)
vkey(MAND_G, 0, 0.0); vkey(MAND_G, 1, 0.55); vkey(MAND_G, 22, 0.9); vkey(MAND_G, SH['S2'] - 1, 0.9); vkey(MAND_G, SH['S2'], 0.0)
vkey(MAND_G, SH['S6'] - 1, 0.0); vkey(MAND_G, SH['S6'], 0.85); vkey(MAND_G, SH['S7'] - 1, 0.85); vkey(MAND_G, SH['S7'], 0.0)
vkey(MAND_G, SH['S10'] - 1, 0.0); vkey(MAND_G, SH['S10'], 0.9)
for g in (CUT_G,):
    vkey(g, SH['S6'] - 1, 0.0); vkey(g, SH['S6'], 0.6); vkey(g, SH['S7'] - 1, 0.6); vkey(g, SH['S7'], 0.0)
    vkey(g, SH['S10'] - 1, 0.0); vkey(g, SH['S10'], 0.9)
vkey(GUM_G, 0, 0.6); vkey(GUM_G, SH['S2'] - 1, 0.6); vkey(GUM_G, SH['S2'], 0.0)
vkey(GUM_G, SH['S6'] - 1, 0.0); vkey(GUM_G, SH['S6'], 0.8); vkey(GUM_G, SH['S7'] - 1, 0.8); vkey(GUM_G, SH['S7'], 0.0)
vkey(GUM_G, SH['S8'] - 1, 0.0); vkey(GUM_G, SH['S8'], 0.75)
vkey(GUM_G, SH['S10'] - 1, 0.75); vkey(GUM_G, SH['S10'], 0.6)
vkey(TOOTH_G, 0, 0.0); vkey(TOOTH_G, SH['S6'] - 1, 0.0); vkey(TOOTH_G, SH['S6'], 0.6); vkey(TOOTH_G, SH['S7'] - 1, 0.6); vkey(TOOTH_G, SH['S7'], 0.0)
# third molar amber in the hook, pulses on contact; neutral during surgery
for f, t, e in [(0, 1.0, 1.2), (14, 1.0, 2.4), (30, 1.0, 1.0), (46, 1.0, 2.4), (62, 1.0, 1.0), (82, 1.0, 2.4), (100, 1.0, 1.0), (SH['S2'] - 1, 1.0, 1.0), (SH['S2'], 0.0, 0.0)]:
    vkey(T3_TINT, f, t); vkey(T3_EM, f, e)
for f, t, e in [(0, 0.0, 0.0), (14, 0.8, 1.5), (30, 0.3, 0.3), (46, 0.8, 1.5), (62, 0.3, 0.3), (82, 0.8, 1.5), (100, 0.3, 0.3), (SH['S2'] - 1, 0.3, 0.3), (SH['S2'], 0.0, 0.0)]:
    vkey(M2_TINT, f, t); vkey(M2_EM, f, e)
# nerve tension pulses in S6
vkey(NERVE_EM, SH['S6'], 0.3)
for i in range(6):
    vkey(NERVE_EM, SH['S6'] + 20 + i * 30, 2.5); vkey(NERVE_EM, SH['S6'] + 35 + i * 30, 0.6)
vkey(NERVE_EM, SH['S7'] - 1, 0.6); vkey(NERVE_EM, SH['S7'], 0.0)
# dry socket pain glow on cut bone (S9)
vkey(CUT_EM, SH['S9'] + 60, 0.0)
for i in range(4):
    vkey(CUT_EM, SH['S9'] + 85 + i * 20, 1.8); vkey(CUT_EM, SH['S9'] + 95 + i * 20, 0.5)
vkey(CUT_EM, SH['S10'] - 1, 0.5); vkey(CUT_EM, SH['S10'], 0.0)
# loop end: tooth gone, clot visible (healed state), so hide crown/root already handled

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
cams['S1'] = camera('C_S1', jaw + Vector((0, 0, 0.01)), [(SH['S1'], dirv(0.85, -0.55, 0.12, 0.34)), (SH['S1b'], dirv(0.85, -0.5, 0.10, 0.27))], lens=50, fstop=5.6)
cams['S1b'] = camera('C_S1b', C3 + Vector((0, -0.006, 0)), [(SH['S1b'], dirv(1, -0.12, 0.08, 0.15)), (SH['S2'], dirv(1, -0.08, 0.06, 0.125))], lens=55, fstop=4.0)
padc = Vector((FX, (y0 + y1) / 2, top_z(FX, (y0 + y1) / 2)))
cams['S2'] = camera('C_S2', padc, [(SH['S2'], dirv(0.55, -0.75, 0.75, 0.115)), (SH['S3'], dirv(0.65, -0.6, 0.65, 0.095))], lens=60, fstop=3.2)
cams['S3'] = camera('C_S3', wc + Vector((0, 0.001, -0.002)), [(SH['S3'], dirv(0.85, -0.35, 0.6, 0.10)), (SH['S4'], dirv(0.8, -0.2, 0.62, 0.085))], lens=60, fstop=3.2)
cams['S4'] = camera('C_S4', Vector((C3.x, split_y, C3.z + 0.002)), [(SH['S4'], dirv(0.6, -0.45, 0.85, 0.085)), (SH['S5'], dirv(0.55, -0.35, 0.9, 0.072))], lens=60, fstop=2.8)
cams['S5'] = camera('C_S5', C3 + Vector((0, 0, 0.004)), [(SH['S5'], dirv(0.8, -0.55, 0.5, 0.11)), (SH['S5b'], dirv(0.85, -0.45, 0.55, 0.10))], lens=55, fstop=3.2)
cams['S5b'] = camera('C_S5b', C3 + Vector((0, 0.002, 0.003)), [(SH['S5b'], dirv(0.9, 0.25, 0.55, 0.09)), (SH['S6'], dirv(0.9, 0.2, 0.5, 0.082))], lens=60, fstop=3.2)
cams['S6'] = camera('C_S6', C3 + Vector((0, 0.002, -0.004)), [(SH['S6'], dirv(1, -0.05, 0.12, 0.13)), (SH['S7'], dirv(1, -0.02, 0.10, 0.10))], lens=60, fstop=4.5)
cams['S7'] = camera('C_S7', padc + Vector((0, 0, -0.001)), [(SH['S7'], dirv(0.6, -0.6, 0.8, 0.10)), (SH['S8'], dirv(0.55, -0.5, 0.85, 0.085))], lens=60, fstop=3.2)
cams['S8'] = camera('C_S8', C3 + Vector((0, 0, 0.004)), [(SH['S8'], dirv(0.95, -0.4, 0.35, 0.14)), (SH['S9'], dirv(0.95, -0.3, 0.30, 0.115))], lens=55, fstop=4.0)
cams['S9'] = camera('C_S9', C3 + Vector((0, 0, 0.006)), [(SH['S9'], dirv(0.9, -0.3, 0.45, 0.10)), (SH['S10'], dirv(0.9, -0.25, 0.4, 0.085))], lens=60, fstop=3.5)
cams['S10'] = camera('C_S10', jaw + Vector((0, 0, 0.01)), [(SH['S10'], dirv(0.85, -0.5, 0.10, 0.25)), (SH['END'], dirv(0.85, -0.55, 0.12, 0.33))], lens=50, fstop=5.6)
for k, (c, t) in cams.items():
    m = sc.timeline_markers.new(k, frame=SH[k]); m.camera = c
sc.camera = cams['S1'][0]

# ---------------- lights & world ----------------
rig_t = link(D.objects.new('LightTarget', None)); rig_t.location = C3
def area(name, off, energy, size, color):
    d = D.lights.new(name, 'AREA'); d.energy = energy; d.size = size; d.color = color
    o = link(D.objects.new(name, d)); o.location = C3 + Vector(off)
    t = o.constraints.new('TRACK_TO'); t.target = rig_t; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
    return o
area('Key', (0.25, -0.30, 0.35), 7, 0.25, (1.0, 0.94, 0.86))
area('Fill', (0.35, 0.05, -0.05), 1.2, 0.4, (0.8, 0.88, 1.0))
area('Rim', (-0.15, 0.35, 0.20), 9, 0.15, (0.75, 0.88, 1.0))
area('Rim2', (0.10, 0.30, 0.25), 4, 0.12, (1.0, 0.85, 0.7))
area('Top', (0.02, -0.02, 0.30), 3, 0.2, (1.0, 0.97, 0.94))
w = D.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.010, 0.012, 0.016, 1)

# ---------------- render settings ----------------
r = sc.render; r.engine = 'CYCLES'; r.resolution_x = 1080; r.resolution_y = 660; r.film_transparent = True
cy = sc.cycles; cy.device = 'GPU'; cy.samples = 64; cy.use_denoising = True; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.transparent_max_bounces = 32; cy.max_bounces = 10; cy.transmission_bounces = 8
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.2
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
bpy.ops.wm.save_as_mainfile(filepath=HERE + 'wisdom.blend')
print('SAVED')
