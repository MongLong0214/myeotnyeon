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

import sys; sys.path.insert(0, (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/blender'))
from kit import clip_box, section_cap, boolean_apply, half_shell, upright_mesh, sculpt_molar, split_by_plane, add_fade, point_mask_emission, drape_sheet, inset_cut_faces, drop_small_parts, seat_against
# second molar: Z-Anatomy pose leans back ~32 deg; upright 12 deg in its socket, then back into contact with the first molar
upright_mesh(M2, -12, 'X')
_mz = [v.co.z for v in M2.data.vertices]; _mz0 = min(_mz); _mzc = _mz0 + 0.004
for _v in M2.data.vertices:   # shorter second-molar roots: apex clear of the canal
    if _v.co.z < _mzc: _v.co.z = _mzc - (_mzc - _v.co.z) * 0.65
M2.data.update()
seat_against(M2, O['Lower first molar tooth.l'], (0, -1, 0), step=0.0001)
# ---------------- third molar (from first molar mesh, sculpted: cusps, fissures, converging roots) ----------------
# anat_kit asset (anat_kit/blender/make_third_molar.py): level-3 sculpt, 5 cusps, fissures, cervical line, converging roots
with bpy.data.libraries.load((__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/assets/third_molar_v2.blend')) as (_src, _dst): _dst.objects = ['ThirdMolarAsset']
T3 = _dst.objects[0]; T3.name = 'ThirdMolar'; link(T3)
sel_only(T3); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
T3.data.materials.append(None); T3.data.materials.append(None)   # slots must exist or index 1 is clamped to 0
# root faces -> material slot 1 (decided in the tooth's own frame: crown = top 38 %)
zs = [v.co.z for v in T3.data.vertices]; zmin, zmax = min(zs), max(zs)
cej = zmin + 0.60 * (zmax - zmin)
for pgn in T3.data.polygons:
    pgn.material_index = 1 if pgn.center.z < cej else 0
T3.rotation_euler = (math.radians(80), 0, math.radians(-6)); T3.scale = (0.95, 0.95, 0.95)   # third molars are smaller than the second molar; 0.75 read as a bullet, 1.0 dwarfed the jaw
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
    colvar(nt, p, (0.58, 0.54, 0.47, 1), (0.44, 0.39, 0.33, 1), 500)   # darker, cooler than the ivory teeth
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
noise_bump(nt, p, 4200, 0.15, 0.00008, voronoi=True)
p.inputs['Emission Color'].default_value = (1.0, 0.18, 0.04, 1)
CUT_EM = nt.nodes.new('ShaderNodeValue'); CUT_EM.name = 'Emit'; CUT_EM.outputs[0].default_value = 0.0
nt.links.new(CUT_EM.outputs[0], p.inputs['Emission Strength'])
CUT_G = ghostable(nt, out, p.outputs[0], 'Ghost', 0.03, 0.5)

# enamel
def enamel(name, glow=False):
    m, nt, out, p = newmat(name)
    p.inputs['Base Color'].default_value = (0.80, 0.76, 0.68, 1)
    p.inputs['Subsurface Weight'].default_value = 0.45; p.inputs['Subsurface Radius'].default_value = (0.9, 0.85, 0.7)
    p.inputs['IOR'].default_value = 1.62
    p.inputs['Subsurface Scale'].default_value = 0.0012
    p.inputs['Roughness'].default_value = 0.30; p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.12; p.inputs['Specular IOR Level'].default_value = 0.35   # clamp highlights
    noise_bump(nt, p, 1800, 0.05, 0.00005)
    p.inputs['Emission Color'].default_value = (1.0, 0.22, 0.06, 1)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; em.outputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], p.inputs['Emission Strength'])
    tint = nt.nodes.new('ShaderNodeValue'); tint.name = 'Tint'; tint.outputs[0].default_value = 0.0
    if glow:
        # base colour shifts toward amber while highlighted
        mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
        mixc.inputs['A'].default_value = (0.80, 0.76, 0.68, 1); mixc.inputs['B'].default_value = (1.0, 0.58, 0.22, 1)
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
p.inputs['Base Color'].default_value = (0.24, 0.045, 0.045, 1); p.inputs['Roughness'].default_value = 0.2
p.inputs['Subsurface Weight'].default_value = 0.0
p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.35; p.inputs['Roughness'].default_value = 0.5; p.inputs['Specular IOR Level'].default_value = 0.2   # moist, but no clipped hot spots
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
cav.scale = (1.03, 1.03, 1.03)
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
bur_head = link(D.objects.new('BurHead', D.meshes.new('burhead'))); _hb = bmesh.new(); bmesh.ops.create_uvsphere(_hb, u_segments=24, v_segments=12, radius=0.0007); _hb.to_mesh(bur_head.data); _hb.free(); setmat(bur_head, mGold); bur_head.location = (0, 0, 0.0007)   # small round bur
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
setv(MAND_G, 0.30); setv(CUT_G, 0.0); setv(GUM_G, 0.0);   # opaque gum: no glass pane over the second molar
setv(TOOTH_G, 0.0)
setv(T3_TINT, 0.22); setv(T3_EM, 0.0); setv(M2_TINT, 0.0); setv(M2_EM, 0.0)
# root (cementum) as its own material on slot 1
mCem, nt, out, p = newmat('Cementum')
p.inputs['Base Color'].default_value = (0.76, 0.62, 0.40, 1); p.inputs['Roughness'].default_value = 0.55   # root: yellower than enamel
p.inputs['Subsurface Weight'].default_value = 0.25; p.inputs['Subsurface Radius'].default_value = (1, 0.75, 0.45); p.inputs['Subsurface Scale'].default_value = 0.001
noise_bump(nt, p, 2400, 0.08, 0.00005)
nt.links.new(p.outputs[0], out.inputs['Surface'])
for o in (CROWN, ROOT):
    o.data.materials.clear(); o.data.materials.append(mT3); o.data.materials.append(mCem)
    ss = o.modifiers.new('ss', 'SUBSURF'); ss.levels = 1; ss.render_levels = 2
    while o.modifiers[0].name != 'ss': bpy.ops.object.modifier_move_up({'object': o}, modifier='ss') if False else o.modifiers.move(len(o.modifiers) - 1, 0)
for mt in (mSteel,):
    pp_ = [n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    pp_.inputs['Base Color'].default_value = (0.80, 0.80, 0.82, 1); pp_.inputs['Roughness'].default_value = 0.2
# ================= draft12 (Fable review 3): flat section cut, static split, nerve beat before extraction =================
D.objects.remove(win)
NR, CR = 0.0007, 0.00115
_t3v = [T3.matrix_world @ v.co for v in T3.data.vertices]
RT = min((v for v in _t3v if v.y > split_y + 0.5 * (hi.y - split_y)), key=lambda q: q.z); root_bottom = RT.z   # nerve route anchor (distal half); root_bottom = RT.z
mid_bottom = min(v.z for v in _t3v if hi.y - 0.0095 < v.y <= hi.y - 0.0065)
z_under = root_bottom - 0.0016 - NR
print('root_bottom', round(root_bottom, 4), 'mid_bottom', round(mid_bottom, 4), 'C3', tuple(round(x, 4) for x in C3), 'lo', tuple(round(x, 4) for x in lo), 'hi', tuple(round(x, 4) for x in hi))
def cutbox(name, x0, x1, y0_, y1_, z0, z1, mat):
    o = D.objects.new(name, D.meshes.new(name)); cutters.objects.link(o)
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0); bm_.to_mesh(o.data); bm_.free()
    o.location = Vector(((x0 + x1) / 2, (y0_ + y1_) / 2, (z0 + z1) / 2)); o.scale = (x1 - x0, y1_ - y0_, z1 - z0)
    o.hide_render = True; o.display_type = 'WIRE'; setmat(o, mat); return o
X_CUT = C3.x - 0.0005          # section plane through the tooth's middle; everything buccal of it is cut away
Y_S0, Y_S1 = m2hi.y - 0.0045, hi.y + 0.0045
# ---- nerve: one continuous tube, lying in a half-open canal groove on the section face ----
def t3_floor(y): return min(v.z for v in _t3v if abs(v.y - y) < 0.0005)
BRK_Y = RT.y                    # bracket at the root apex (closest point to the canal)
# under the upright second molar the nerve stays >= 1 mm below its apices, then rises toward the ramus under the third molar
pts = [(X_CUT + 0.0003, -0.0830, 1.5072), (X_CUT + 0.0003, -0.0720, 1.5082), (X_CUT + 0.0003, -0.0620, 1.5098), (X_CUT + 0.0003, -0.0520, 1.5120),
       (X_CUT + 0.0003, -0.0455, 1.5146), (X_CUT + 0.0003, -0.0405, 1.5178), (X_CUT + 0.0003, (-0.0405 + RT.y) / 2, (1.5178 + RT.z - 0.0016 - NR) / 2 - 0.0002), (X_CUT + 0.0003, BRK_Y, RT.z - 0.0016 - NR),
       (X_CUT + 0.0006, hi.y - 0.0006, t3_floor(hi.y - 0.0006) - 0.0028 - NR), (0.0345, -0.0200, 1.5330), (0.0372, -0.0130, 1.5390), (0.0365, -0.0085, 1.5500)]
_Z0 = [q[2] for q in pts]
for _ in range(6):   # no kink under the bracket: relax z along the run beneath the tooth, never upward (keeps the clearance to the tooth)
    _zz = [q[2] for q in pts]
    for i_ in range(5, 10): pts[i_] = (pts[i_][0], pts[i_][1], max(min(pts[i_][2], (_zz[i_ - 1] + _zz[i_] * 2 + _zz[i_ + 1]) / 4), _Z0[i_] - 0.0006))
def tube(name, r, mat):
    cu_ = D.curves.new(name, 'CURVE'); cu_.dimensions = '3D'
    sp_ = cu_.splines.new('BEZIER'); sp_.bezier_points.add(len(pts) - 1)
    for bp, pp in zip(sp_.bezier_points, pts):
        bp.co = pp; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu_.bevel_depth = r; cu_.bevel_resolution = 8; cu_.use_fill_caps = True; cu_.resolution_u = 48
    ob = link(D.objects.new(name, cu_)); setmat(ob, mat); return ob
mNerve2, nt, out, p = newmat('Nerve2')
p.inputs['Base Color'].default_value = (1.0, 0.72, 0.10, 1); p.inputs['Roughness'].default_value = 0.3
p.inputs['Subsurface Weight'].default_value = 0.5; p.inputs['Subsurface Radius'].default_value = (1, 0.7, 0.2); p.inputs['Subsurface Scale'].default_value = 0.0006
p.inputs['Coat Weight'].default_value = 0.4; p.inputs['Emission Color'].default_value = (1.0, 0.50, 0.02, 1)
NERVE2_EM = nt.nodes.new('ShaderNodeValue'); nt.links.new(NERVE2_EM.outputs[0], p.inputs['Emission Strength'])
tc_ = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 900
nt.links.new(tc_.outputs['Object'], wv.inputs['Vector']); bmp = nt.nodes.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.15
nt.links.new(wv.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
nt.links.new(p.outputs[0], out.inputs['Surface'])
NERVE2 = tube('Nerve2', NR, mNerve2)
# ---- section materials: trabecular fill, cortical ring, canal wall ----
mTrab, nt, out, p = newmat('Trabecular')
tcv = nt.nodes.new('ShaderNodeTexCoord'); vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 3400
nt.links.new(tcv.outputs['Object'], vor.inputs['Vector'])
rmp = nt.nodes.new('ShaderNodeValToRGB'); rmp.color_ramp.elements[0].color = (0.62, 0.57, 0.50, 1); rmp.color_ramp.elements[0].position = 0.10
rmp.color_ramp.elements[1].color = (0.16, 0.08, 0.07, 1); rmp.color_ramp.elements[1].position = 0.22   # open pores
nt.links.new(vor.outputs['Distance'], rmp.inputs['Fac']); nt.links.new(rmp.outputs['Color'], p.inputs['Base Color'])
bpt = nt.nodes.new('ShaderNodeBump'); bpt.inputs['Strength'].default_value = 0.5; bpt.inputs['Distance'].default_value = 0.0001
nt.links.new(vor.outputs['Distance'], bpt.inputs['Height']); nt.links.new(bpt.outputs['Normal'], p.inputs['Normal'])
p.inputs['Roughness'].default_value = 0.55; nt.links.new(p.outputs[0], out.inputs['Surface'])
mCortex, nt, out, p = newmat('Cortex')
colvar(nt, p, (0.93, 0.90, 0.82, 1), (0.86, 0.82, 0.72, 1), 2000); p.inputs['Roughness'].default_value = 0.35
nt.links.new(p.outputs[0], out.inputs['Surface'])
mCanalW, nt, out, p = newmat('CanalWall')
p.inputs['Base Color'].default_value = (0.36, 0.16, 0.12, 1); p.inputs['Roughness'].default_value = 0.4
nt.links.new(p.outputs[0], out.inputs['Surface'])
# ---- cutters: smooth tooth-shaped socket, section box, canal ----
sel_only(cav); cav.scale = (1.04, 1.04, 1.04)
_rm = cav.modifiers.new('rm', 'REMESH'); _rm.mode = 'VOXEL'; _rm.voxel_size = 0.0003
cav.modifiers.new('sm', 'SMOOTH').iterations = 6
for _m in [m.name for m in cav.modifiers]: bpy.ops.object.modifier_apply(modifier=_m)
for _pg in cav.data.polygons: _pg.use_smooth = True
_zs0 = min(p_[2] for p_ in pts if Y_S0 - 0.003 <= p_[1] <= Y_S1) - NR - 0.0025
# ---- one mandible (review 7): Z-Anatomy jaw voxel-remeshed into ONE closed solid, then cut once ----
MAND.modifiers.clear()
# retromolar / alveolar bone over the impacted tooth, unioned into the jaw before the remesh so it becomes the same solid
_mv = [MAND.matrix_world @ v.co for v in MAND.data.vertices if Y_S0 < (MAND.matrix_world @ v.co).y < Y_S1 and (MAND.matrix_world @ v.co).x > 0.01]
_bx0, _bx1 = min(v.x for v in _mv) + 0.0012, max(v.x for v in _mv) - 0.0012
_cr = D.objects.new('CrestFill', D.meshes.new('CrestFill')); link(_cr)
_bm = bmesh.new(); bmesh.ops.create_cube(_bm, size=1.0)
_zc0 = _zs0 - 0.003   # down into the body: Z-Anatomy leaves a hollow crypt here
for _v in _bm.verts: _v.co = Vector(((_bx0 + _bx1) / 2 + _v.co.x * (_bx1 - _bx0), (m2hi.y - 0.002 + hi.y + 0.008) / 2 + _v.co.y * (hi.y + 0.010 - m2hi.y), (_zc0 + hi.z + 0.0012) / 2 + _v.co.z * (hi.z + 0.0012 - _zc0)))
bmesh.ops.bevel(_bm, geom=list(_bm.edges), offset=0.0025, segments=8, profile=0.5, affect='EDGES')
_bm.to_mesh(_cr.data); _bm.free(); setmat(_cr, mMand)
boolean_apply(MAND, _cr, 'UNION'); D.objects.remove(_cr)
_rm = MAND.modifiers.new('rm', 'REMESH'); _rm.mode = 'VOXEL'; _rm.voxel_size = 0.0003; _rm.use_smooth_shade = True
sel_only(MAND); bpy.ops.object.modifier_apply(modifier='rm'); print('mandible remeshed', len(MAND.data.vertices))
print('interior shells removed (hollow canal/medulla surfaces -> solid bone)', drop_small_parts(MAND, len(MAND.data.vertices) // 3))

_cc = D.curves.new('CanalCut', 'CURVE'); _cc.dimensions = '3D'; _sp = _cc.splines.new('BEZIER'); _sp.bezier_points.add(len(pts) - 1)
for bp, pp in zip(_sp.bezier_points, pts): bp.co = pp; bp.handle_left_type = bp.handle_right_type = 'AUTO'
_cc.bevel_depth = CR; _cc.bevel_resolution = 6; _cc.resolution_u = 48; _cc.use_fill_caps = True
_cco = D.objects.new('CanalCutTmp', _cc); sc.collection.objects.link(_cco); bpy.context.view_layer.update()
_cme = D.meshes.new_from_object(_cco.evaluated_get(bpy.context.evaluated_depsgraph_get())); D.objects.remove(_cco)
CANC = link(D.objects.new('CanalCutter', _cme)); setmat(CANC, mCanalW); CANC.hide_render = True; CANC.display_type = 'WIRE'
Z_CREST = hi.z + 0.0006
# curved cutaway: a box with 3 mm rounded edges following the body, everything buccal of X_CUT
_cut = D.objects.new('JawCut', D.meshes.new('JawCut')); link(_cut)
_bm = bmesh.new(); bmesh.ops.create_cube(_bm, size=1.0)
Y_CF = Y_S0 - 0.07   # section runs forward past the second molar: no end wall (slit) and no buccal plate in front of the teeth (glass pane)
for _v in _bm.verts: _v.co = Vector((X_CUT + 0.025 + _v.co.x * 0.05, (Y_CF + Y_S1) / 2 + _v.co.y * (Y_S1 - Y_CF), (_zs0 + hi.z + 0.03) / 2 + _v.co.z * (hi.z + 0.03 - _zs0)))
bmesh.ops.bevel(_bm, geom=list(_bm.edges), offset=0.003, segments=10, profile=0.5, affect='EDGES')
_bm.to_mesh(_cut.data); _bm.free(); setmat(_cut, mTrab); _cut.hide_render = True
mSock, _n, _o, _p = newmat('SocketWall'); colvar(_n, _p, (0.55, 0.20, 0.13, 1), (0.30, 0.08, 0.05, 1), 1500); _p.inputs['Roughness'].default_value = 0.4; _n.links.new(_p.outputs[0], _o.inputs['Surface'])
setmat(cav, mSock)
# socket stops 1.5 mm short of the lingual cortex: a back wall, never a hole to the background
_cavt = cav.copy(); _cavt.data = cav.data.copy(); _cavt.name = 'CavTrim'; link(_cavt); setmat(_cavt, mSock)
_lb = D.objects.new('LingualGuard', D.meshes.new('lg')); link(_lb); _gb_ = bmesh.new(); bmesh.ops.create_cube(_gb_, size=1.0)
for _v in _gb_.verts: _v.co = Vector((_bx0 + 0.0003 + 0.05 + _v.co.x * 0.1, C3.y + _v.co.y * 0.1, C3.z + _v.co.z * 0.1))
_gb_.to_mesh(_lb.data); _gb_.free(); boolean_apply(_cavt, _lb, 'INTERSECT'); D.objects.remove(_lb)   # manifold-safe trim (bisect+fill left a broken cutter)
print('socket cutter verts', len(_cavt.data.vertices))
for _pg in _cavt.data.polygons: _pg.material_index = 0
_cavt.hide_render = True
for _c in (_cavt, CANC, _cut): boolean_apply(MAND, _c)   # socket and canal first, the section box last (box-first left a black coplanar patch)
_cb2 = bmesh.new(); _cb2.from_mesh(MAND.data)
_z0 = sum(1 for f in _cb2.faces if f.calc_area() < 1e-12)
bmesh.ops.remove_doubles(_cb2, verts=_cb2.verts, dist=0.00001)
bmesh.ops.dissolve_degenerate(_cb2, edges=_cb2.edges, dist=0.00001)
_cb2.to_mesh(MAND.data); _cb2.free(); print('zero-area faces before cleanup', _z0)
print('loose boolean slivers removed', drop_small_parts(MAND, len(MAND.data.vertices) // 3))
import collections; print('mandible faces per material', {MAND.data.materials[k].name: v for k, v in collections.Counter(p.material_index for p in MAND.data.polygons).items()})
# explicit opaque socket and canal walls behind the section: the boolean's own walls rendered as see-through (rays ran out of transparent bounces -> black)
_ms = [m.name for m in MAND.data.materials]
if 'SocketWall' not in _ms: MAND.data.materials.append(mSock); _ms.append('SocketWall')
_it, _is = _ms.index('Trabecular'), _ms.index('SocketWall')
_cb = __import__('kit').world_bvh(_cavt); _n = 0
for _pg in MAND.data.polygons:   # boolean TRANSFER gave the socket walls the cut-face material; they are socket walls
    if _pg.material_index == _it and abs((MAND.matrix_world @ _pg.center).x - X_CUT) > 0.0002:
        _h = _cb.find_nearest(MAND.matrix_world @ _pg.center)
        if _h[3] is not None and _h[3] < 0.0004: _pg.material_index = _is; _n += 1
print('socket wall faces reassigned', _n)
mSockD, _n, _o, _p = newmat('SocketDark'); _p.inputs['Base Color'].default_value = (0.06, 0.03, 0.025, 1); _p.inputs['Roughness'].default_value = 0.8; _n.links.new(_p.outputs[0], _o.inputs['Surface'])
MAND.data.materials.append(mSockD); _isd = len(MAND.data.materials) - 1
_mb = __import__('kit').world_bvh(M2); _n2 = 0
for _pg in MAND.data.polygons:
    _h = _mb.find_nearest(MAND.matrix_world @ _pg.center)
    if _h[3] is not None and _h[3] < 0.0011: _pg.material_index = _isd; _n2 += 1
print('second-molar socket faces -> SocketWall', _n2)
_nb = bmesh.new(); _nb.from_mesh(MAND.data); bmesh.ops.recalc_face_normals(_nb, faces=_nb.faces); _nb.to_mesh(MAND.data); _nb.free()
_fl = sum(1 for _pg in MAND.data.polygons if _pg.material_index == _it and _pg.normal.x < -0.5); print('cut faces facing away after recalc', _fl)
D.objects.remove(_cut)
_tb_ = bmesh.new(); _tb_.from_mesh(MAND.data); bmesh.ops.triangulate(_tb_, faces=[f for f in _tb_.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY'); _tb_.to_mesh(MAND.data); _tb_.free()   # big concave cut n-gons filled the socket opening (black patch)
# cortical rim = one continuous round tube along every boundary edge of the section face (inset_region left dashes and black ticks on thin triangles)
_bmr = bmesh.new(); _bmr.from_mesh(MAND.data); _bmr.edges.ensure_lookup_table()
_be = [e for e in _bmr.edges if len(e.link_faces) >= 1 and any(f.material_index == _it for f in e.link_faces) and not all(f.material_index == _it for f in e.link_faces)]
_vi = {}; _vl = []; _el = []
for e in _be:
    ids = []
    for v in e.verts:
        if v.index not in _vi: _vi[v.index] = len(_vl); _vl.append(MAND.matrix_world @ v.co)
        ids.append(_vi[v.index])
    _el.append(tuple(ids))
_bmr.free()
_rme = D.meshes.new('RimEdges'); _rme.from_pydata([tuple(v) for v in _vl], _el, []); _rme.update()
RIM = link(D.objects.new('Rim', _rme)); sel_only(RIM); bpy.ops.object.convert(target='CURVE')
RIM = bpy.context.active_object; RIM.name = 'Rim'; RIM.data.dimensions = '3D'; RIM.data.bevel_depth = 0.00017; RIM.data.bevel_resolution = 2; RIM.data.use_fill_caps = True
RIM.data.materials.clear(); RIM.data.materials.append(mCortex)
for _i, _sp in enumerate(RIM.data.splines):
    _pp = [p.co.xyz for p in _sp.points]; print('rim spline', _i, 'pts', len(_pp), 'cyclic', _sp.use_cyclic_u, 'len_mm', round(sum((a - b).length for a, b in zip(_pp, _pp[1:])) * 1000, 1), 'at', tuple(round(c, 4) for c in _pp[0]))
_short = [i for i, sp in enumerate(RIM.data.splines) if sum((a.co.xyz - b.co.xyz).length for a, b in zip(sp.points, list(sp.points)[1:])) < 0.012]
_short = [i for i, sp in enumerate(RIM.data.splines) if sum((a.co.xyz - b.co.xyz).length for a, b in zip(sp.points, list(sp.points)[1:])) < 0.025]   # beads, stubs and the wire triangle at the second molar / socket contact
for _i in reversed(_short): RIM.data.splines.remove(RIM.data.splines[_i])
print('rim boundary edges', len(_el), 'splines left', len(RIM.data.splines), 'removed', _short)
# nerve window clip: the section's front bone edge (rim points on the plane near the canal height)
_pp0 = sorted(pts, key=lambda q: q[1])
def _nz0(y):
    for a_, b_ in zip(_pp0, _pp0[1:]):
        if a_[1] <= y <= b_[1]: return a_[2] + (b_[2] - a_[2]) * (y - a_[1]) / (b_[1] - a_[1])
    return _pp0[0][2] if y < _pp0[0][1] else _pp0[-1][2]
_rp = [p.co.xyz for sp in RIM.data.splines for p in sp.points if abs(p.co.x - X_CUT) < 0.0007 and abs(p.co.z - _nz0(p.co.y)) < 0.0016 and p.co.y < -0.045]   # rim crossing the nerve path
YB = min(p.y for p in _rp) if _rp else -0.075; print('bone front edge y', round(YB, 4))
_nn = mNerve2.node_tree; _np = [n for n in _nn.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _no = [n for n in _nn.nodes if n.type == 'OUTPUT_MATERIAL'][0]
_g = _nn.nodes.new('ShaderNodeNewGeometry'); _sx = _nn.nodes.new('ShaderNodeSeparateXYZ'); _gt = _nn.nodes.new('ShaderNodeMath'); _gt.operation = 'GREATER_THAN'; _gt.inputs[1].default_value = YB + 0.0002
_tn = _nn.nodes.new('ShaderNodeBsdfTransparent'); _mm = _nn.nodes.new('ShaderNodeMixShader')
_nn.links.new(_g.outputs['Position'], _sx.inputs[0]); _nn.links.new(_sx.outputs['Y'], _gt.inputs[0]); _nn.links.new(_gt.outputs[0], _mm.inputs['Fac']); _nn.links.new(_tn.outputs[0], _mm.inputs[1]); _nn.links.new(_np.outputs[0], _mm.inputs[2]); _nn.links.new(_mm.outputs[0], _no.inputs['Surface'])   # nerve ends at the bone rim
# rim: stop at the tooth outline (no wire drawn across the front of the crown); the clipped-away stretches come back once the tooth is out
_tb = __import__('kit').world_bvh(T3)
def _inside(p_):
    if _tb.find_nearest(p_)[3] is not None and _tb.find_nearest(p_)[3] < 0.00045: return True
    n_ = 0; o_ = p_.copy()
    for _ in range(40):
        h_ = _tb.ray_cast(o_, Vector((1, 0, 0)))
        if h_[0] is None: break
        n_ += 1; o_ = h_[0] + Vector((1e-6, 0, 0))
    return n_ % 2 == 1
_spl = [([p.co.xyz.copy() for p in sp.points], sp.use_cyclic_u) for sp in RIM.data.splines]
def _curve(name):
    c_ = D.curves.new(name, 'CURVE'); c_.dimensions = '3D'; c_.bevel_depth = 0.00017; c_.bevel_resolution = 2; c_.use_fill_caps = True; c_.materials.append(mCortex)
    return c_, link(D.objects.new(name, c_))
_cout, RIMOUT = _curve('RimOut'); _cin, RIMIN = _curve('RimIn')
def _add(c_, pl):
    if len(pl) < 2: return
    sp_ = c_.splines.new('POLY'); sp_.points.add(len(pl) - 1)
    for k_, p_ in enumerate(pl): sp_.points[k_].co = (p_.x, p_.y, p_.z, 1)
for pl, cyc in _spl:
    ins = [_inside(p_) for p_ in pl]; n_ = len(pl)
    if not any(ins): _add(_cout, pl + ([pl[0]] if cyc else [])); continue
    start = next((i_ for i_ in range(n_) if ins[i_]), 0) if cyc else 0   # for loops begin at an inside point so no run is split
    order = [(start + k_) % n_ for k_ in range(n_)] if cyc else list(range(n_)); runs = []; cur = []; cur_in = ins[order[0]]
    for i_ in order:
        if ins[i_] != cur_in: runs.append((cur_in, cur)); cur = []; cur_in = ins[i_]
        cur.append(pl[i_])
    runs.append((cur_in, cur))
    for k_, (isin, run) in enumerate(runs):
        nxt = runs[(k_ + 1) % len(runs)][1][0] if (k_ + 1 < len(runs) or cyc) else None
        _add(_cin if isin else _cout, run + ([nxt] if nxt is not None else []))
D.objects.remove(RIM)
RIM = RIMOUT; vis(RIMIN, [(272, 301)])
print('rim clipped: outside splines', len(_cout.splines), 'inside runs', len(_cin.splines))
for _m in (mSock, mCanalW):   # thin cortical rim also around the socket and canal openings
    pass

# ---- static split (animated EXACT booleans collapsed the root to 6 verts on f135/138/145/149-159 = the flash frames) ----
mDentin.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.80, 0.68, 0.50, 1)
mDentin.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.65
import numpy as _np
def _taubin_region(o, wfun, iters, lam=0.5, mu=-0.53):
    me = o.data; n_ = len(me.vertices); mw_ = o.matrix_world
    P_ = _np.empty(n_ * 3); me.vertices.foreach_get('co', P_); P_ = P_.reshape(-1, 3)
    W_ = _np.array([wfun(mw_ @ v_.co) for v_ in me.vertices]); act = _np.where(W_ > 0)[0]
    E_ = _np.empty(len(me.edges) * 2, dtype=_np.int64); me.edges.foreach_get('vertices', E_); E_ = E_.reshape(-1, 2)
    deg = _np.zeros(n_); _np.add.at(deg, E_[:, 0], 1); _np.add.at(deg, E_[:, 1], 1); deg[deg == 0] = 1
    for i_ in range(iters):
        S_ = _np.zeros_like(P_); _np.add.at(S_, E_[:, 0], P_[E_[:, 1]]); _np.add.at(S_, E_[:, 1], P_[E_[:, 0]])
        f_ = lam if i_ % 2 == 0 else mu
        P_[act] += (f_ * W_[act])[:, None] * (S_[act] / deg[act][:, None] - P_[act])
    me.vertices.foreach_set('co', P_.ravel()); me.update()
_NUB = Vector((0.03450, -0.03630, 1.53000))
def _w_nub(w):
    d_ = (w - _NUB).length; t_ = max(0.0, min(1.0, (0.0026 - d_) / 0.0013)); return t_ * t_ * (3 - 2 * t_)
_GCY = lo.y + 0.40 * (hi.y - lo.y)
def _w_groove(w):
    t_ = max(0.0, min(1.0, (0.0014 - abs(w.y - _GCY)) / 0.0006)); return t_ * t_ * (3 - 2 * t_)
# (v2 tooth is built clean: no nub, no cervical crease to smooth)
for o in (CROWN, ROOT): D.objects.remove(o)
KERF = 0.0001   # 0.36 mm kerf = ~12 px in close-up
CROWN = split_by_plane(T3, 'Crown', (0, split_y - KERF, 0), (0, -1, 0))
ROOT = split_by_plane(T3, 'Root', (0, split_y + KERF, 0), (0, 1, 0))
_tmp = split_by_plane(T3, 'FillTmp', (0, split_y - KERF, 0), (0, 1, 0))
FILL = split_by_plane(_tmp, 'Filler', (0, split_y + KERF, 0), (0, -1, 0)); D.objects.remove(_tmp)
for o in (CROWN, ROOT, FILL):
    o.data.materials.clear()
    for m_ in (mT3, mCem, mDentin): o.data.materials.append(m_)
    for _pg in o.data.polygons:
        if _pg.material_index != 2: _pg.use_smooth = True
    print('split', o.name, len(o.data.vertices))
_ycej = lo.y + 0.42 * (hi.y - lo.y)
for o_ in (CROWN, ROOT, FILL, T3):   # materials.clear() had reset every index to 0 (all enamel): re-derive enamel / root / cut face
    o_.data.materials.clear()
    for m_ in (mT3, mCem, mDentin): o_.data.materials.append(m_)
    mw_ = o_.matrix_world; n3 = mw_.to_3x3()
    for p_ in o_.data.polygons:
        c_ = mw_ @ p_.center; nn = (n3 @ p_.normal).normalized()
        if abs(nn.y) > 0.98 and min(abs(c_.y - (split_y - KERF)), abs(c_.y - (split_y + KERF))) < 0.00003: p_.material_index = 2; p_.use_smooth = False
        else: p_.material_index = 1 if c_.y > _ycej else 0
    print('mats', o_.name, __import__('collections').Counter(p_.material_index for p_ in o_.data.polygons))
# ---- cervical groove: the sculpt's groove is not edited (tooth-mesh edits break the jaw boolean). Both materials read one 'cem' vertex ramp
# across +-1.2 mm of the groove, so colour, roughness, coat and subsurface are the same on both sides of it (no seam ring)
_GW = 0.0018; _GC = lo.y + 0.40 * (hi.y - lo.y); _GH = 0.0011   # colour ramp +-1.8 mm; shine mask +-1.1 mm around the sculpt groove
for o_ in (CROWN, ROOT, FILL, T3):
    mw_ = o_.matrix_world; at_ = o_.data.attributes.new('cem', 'FLOAT', 'POINT')
    for v_ in o_.data.vertices:
        t_ = max(0.0, min(1.0, ((mw_ @ v_.co).y - (_ycej - _GW)) / (2 * _GW))); at_.data[v_.index].value = t_ * t_ * (3 - 2 * t_)
    ag_ = o_.data.attributes.new('grv', 'FLOAT', 'POINT')
    for v_ in o_.data.vertices:
        u_ = max(0.0, min(1.0, 1.0 - abs((mw_ @ v_.co).y - _GC) / _GH)); ag_.data[v_.index].value = u_ * u_ * (3 - 2 * u_)
def _cem_blend(m_, glow_node=None):
    nt_ = m_.node_tree; p_ = [n for n in nt_.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    at = nt_.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'cem'
    def mixf(a_, b_, col=False):
        n_ = nt_.nodes.new('ShaderNodeMix'); n_.data_type = 'RGBA' if col else 'FLOAT'
        n_.inputs['A'].default_value = a_; n_.inputs['B'].default_value = b_; nt_.links.new(at.outputs['Fac'], n_.inputs['Factor']); return n_.outputs['Result']
    col_ = mixf((0.80, 0.76, 0.68, 1), (0.76, 0.62, 0.40, 1), True)
    if glow_node is not None: nt_.links.new(col_, glow_node.inputs['A'])
    else: nt_.links.new(col_, p_.inputs['Base Color'])
    ag = nt_.nodes.new('ShaderNodeAttribute'); ag.attribute_type = 'GEOMETRY'; ag.attribute_name = 'grv'
    def gmix(n_out, a_, b_):   # n_out blended toward b_ by the groove mask
        n_ = nt_.nodes.new('ShaderNodeMix'); n_.data_type = 'FLOAT'; nt_.links.new(ag.outputs['Fac'], n_.inputs['Factor']); nt_.links.new(n_out, n_.inputs['A']); n_.inputs['B'].default_value = b_; return n_.outputs['Result']
    nt_.links.new(gmix(mixf(0.30, 0.55), 0, 0.85), p_.inputs['Roughness']); nt_.links.new(gmix(mixf(0.25, 0.0), 0, 0.0), p_.inputs['Coat Weight'])
    nt_.links.new(mixf(0.45, 0.25), p_.inputs['Subsurface Weight']); p_.inputs['Specular IOR Level'].default_value = 0.35
    sp_ = nt_.nodes.new('ShaderNodeMix'); sp_.data_type = 'FLOAT'; nt_.links.new(ag.outputs['Fac'], sp_.inputs['Factor']); sp_.inputs['A'].default_value = 0.35; sp_.inputs['B'].default_value = 0.0; nt_.links.new(sp_.outputs['Result'], p_.inputs['Specular IOR Level'])
_gl = [n for n in mT3.node_tree.nodes if n.type == 'MIX' and n.data_type == 'RGBA'][0]
_cem_blend(mT3, _gl); _cem_blend(mCem)
set_origin(CROWN, Vector((C3.x, (lo.y + split_y) / 2, C3.z))); set_origin(ROOT, Vector((C3.x, (split_y + hi.y) / 2, C3.z)))
cl0, cr0 = CROWN.location.copy(), ROOT.location.copy()
_fz = [FILL.matrix_world @ v.co for v in FILL.data.vertices]; fz0, fz1 = min(v.z for v in _fz), max(v.z for v in _fz)
set_origin(FILL, Vector((C3.x, split_y, fz0)))
# ---- contact glow on the second molar only (masked to the contact point) + 2 degree nudge ----
GLW_OFF = True
M2.rotation_mode = 'XYZ'
_m2v = [M2.matrix_world @ v.co for v in M2.data.vertices]; set_origin(M2, min(_m2v, key=lambda q: q.z))   # pivot at the apex: the crown visibly tips
_zf = min(v.z for v in _m2v) + 0.0105; _xc = sum(v.x for v in _m2v if v.z < _zf) / max(1, sum(1 for v in _m2v if v.z < _zf))
_bmh = bmesh.new()
for v in _m2v:
    if v.z < _zf and v.x < _xc: _bmh.verts.new(v)
bmesh.ops.convex_hull(_bmh, input=list(_bmh.verts)); _hm = D.meshes.new('M2Septum'); _bmh.to_mesh(_hm); _bmh.free()
M2SEP = link(D.objects.new('M2Septum', _hm)); setmat(M2SEP, mTrab); bpy.context.view_layer.update(); parent(M2SEP, M2)   # interradicular bone: fills the slot between the second molar's roots
for o_ in (CROWN, ROOT, T3):
    kloc(o_, 2, o_.location.copy()); kloc(o_, 7, o_.location + Vector((0, -0.00025, 0))); kloc(o_, 20, o_.location + Vector((0, 0.00025, 0)))
for _f, _r in ((0, -1.0), (3, -1.0), (10, -5.0), (20, -5.0), (32, -1.0)):   # owner: the push must be seen
    M2.rotation_euler = (R(_r), 0, 0); M2.keyframe_insert('rotation_euler', frame=_f)
setv(T3_EM, 0.0)
_pM2 = [n for n in mM2.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _pM2.inputs['Emission Color'].default_value = (1.0, 0.45, 0.10, 1)
point_mask_emission(mM2, M2_EM, CONTACT, 0.004)
vkey(M2_EM, 0, 3.0); vkey(M2_EM, 3, 3.0); vkey(M2_EM, 9, 40.0); vkey(M2_EM, 14, 14.0); vkey(M2_EM, 32, 0.0)   # squash flash on impact
for _f, _sz in ((7, 1.0), (10, 0.94), (13, 1.0)): M2.scale = (1.02 if _sz < 1 else 1.0, 1.0, _sz); M2.keyframe_insert('scale', frame=_f)
# ---- section: bur from the occlusal side; the kerf slab (filler) is eaten top-down with the tip; dust ----
BUR0, BUR1 = 92, 152
_sl = [(T3.matrix_world @ v.co).z for v in T3.data.vertices if abs((T3.matrix_world @ v.co).y - split_y) < 0.0003]
SL_TOP, SL_BOT = max(_sl), min(_sl)   # tooth depth at the cut plane
burrot = (R(-10), R(8), 0)
BE = BUR0 + 6   # first contact
BUR_OFF = Vector((0.0012, -0.0015, 0.0175))   # just above the frame top: 8 frames of visible travel in and out
CK0 = BUR1 + 6   # crack starts as the head clears the cut
mMC, _mn, _mo, _mp = newmat('MistConeM'); _mp.inputs['Base Color'].default_value = (0.9, 0.95, 1.0, 1)
_tr = _mn.nodes.new('ShaderNodeBsdfTransparent'); _em = _mn.nodes.new('ShaderNodeEmission'); _em.inputs['Color'].default_value = (0.92, 0.96, 1.0, 1); _em.inputs['Strength'].default_value = 1.6
_mx = _mn.nodes.new('ShaderNodeMixShader'); _lw = _mn.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.5; _iv = _mn.nodes.new('ShaderNodeMath'); _iv.operation = 'SUBTRACT'; _iv.inputs[0].default_value = 1.0; _mn.links.new(_lw.outputs['Facing'], _iv.inputs[1]); _tcn = _mn.nodes.new('ShaderNodeTexCoord'); _spz = _mn.nodes.new('ShaderNodeSeparateXYZ'); _mn.links.new(_tcn.outputs['Generated'], _spz.inputs[0])
_fz = _mn.nodes.new('ShaderNodeMath'); _fz.operation = 'SUBTRACT'; _fz.inputs[0].default_value = 1.0; _mn.links.new(_spz.outputs['Z'], _fz.inputs[1])   # dense at the head, gone at the wide end
_fz2 = _mn.nodes.new('ShaderNodeMath'); _fz2.operation = 'POWER'; _fz2.inputs[1].default_value = 1.6; _mn.links.new(_fz.outputs[0], _fz2.inputs[0])
_fm = _mn.nodes.new('ShaderNodeMath'); _fm.operation = 'MULTIPLY'; _mn.links.new(_iv.outputs[0], _fm.inputs[0]); _mn.links.new(_fz2.outputs[0], _fm.inputs[1])
_sc2 = _mn.nodes.new('ShaderNodeMath'); _sc2.operation = 'MULTIPLY'; _sc2.inputs[1].default_value = 0.6; _mn.links.new(_fm.outputs[0], _sc2.inputs[0]); _mn.links.new(_sc2.outputs[0], _mx.inputs['Fac']); _mn.links.new(_tr.outputs[0], _mx.inputs[1]); _mn.links.new(_em.outputs[0], _mx.inputs[2]); _mn.links.new(_mx.outputs[0], _mo.inputs['Surface'])
HP.location = (0, 0, 0); HP.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
_d = Vector((0.25, 0.7, 0.6)).normalized(); MISTC = cyl('MistCone', 0.0004, 0.0052, mMC, 24, 0.0023, (0, 0, 0))
MISTC.rotation_euler = _d.to_track_quat('Z', 'Y').to_euler(); MISTC.location = Vector((0, 0, 0.001)) + _d * 0.0026; parent(MISTC, HP)   # tip at the head, widening up and away: the water mist
def zmask(m, above):
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    cv = nt.nodes.new('ShaderNodeValue'); cv.name = 'CutZ'; cv.outputs[0].default_value = 9.0
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    cmpn = nt.nodes.new('ShaderNodeMath'); cmpn.operation = 'GREATER_THAN' if above else 'LESS_THAN'; nt.links.new(sep.outputs['Z'], cmpn.inputs[0]); nt.links.new(cv.outputs[0], cmpn.inputs[1])
    ms = [n for n in nt.nodes if n.type == 'MIX_SHADER']
    if ms:
        src = ms[0].inputs['Fac'].links[0].from_socket; mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
        nt.links.new(src, mu.inputs[0]); nt.links.new(cmpn.outputs[0], mu.inputs[1]); nt.links.new(mu.outputs[0], ms[0].inputs['Fac'])
    else:
        surf = out.inputs['Surface'].links[0].from_socket; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(cmpn.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(surf, mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return cv
# the whole tooth shows below the bur head, the cut halves above it: the kerf is only visible where the bur has been (no seam line before the cut)
mT3w, mCw, mDw = mT3.copy(), mCem.copy(), mDentin.copy()
T3.data.materials.clear()
for _m in (mT3w, mCw, mDw): T3.data.materials.append(_m)
T3.scale = (0.992, 0.992, 0.992)   # the whole tooth sits 0.05 mm inside the cut halves: coincident surfaces made the transparent T3 swallow the pieces behind it
CUTN = [zmask(m_, False) for m_ in (mT3w, mCw, mDw)] + [zmask(m_, True) for m_ in (mT3, mCem, mDentin)]
def bur_keys(zb):
    vtip = lambda f: Vector((hi.x - 0.0008, split_y, (SL_TOP + 0.0005) + (zb - (SL_TOP + 0.0005)) * max(0, min(1, (f - BE) / (BUR1 - BE)))))
    for c_ in [HP] + list(HP.children): c_.animation_data_clear()
    FILL.animation_data_clear(); FILL.hide_render = True
    for _cn in CUTN: _cn.outputs[0].default_value = 9.0
    _ed = bpy.context.preferences.edit; _ed.keyframe_new_interpolation_type = 'LINEAR'   # entry and exit legs at constant speed (8 visible frames)
    place_tool(HP, BE - 8, vtip(BE) + BUR_OFF, burrot); _ed.keyframe_new_interpolation_type = 'BEZIER'
    place_tool(HP, BE, vtip(BE), burrot)
    for _cn in CUTN: vkey(_cn, BE - 1, 9.0)
    for f in range(BE + 1, BUR1 + 1):   # head keyed every frame to the cut front (filler top)
        if f == BUR1: _ed.keyframe_new_interpolation_type = 'LINEAR'
        place_tool(HP, f, vtip(f), burrot)
        _ed.keyframe_new_interpolation_type = 'BEZIER'
        for _cn in CUTN: vkey(_cn, f, vtip(f).z - 0.0002)
    place_tool(HP, BUR1 + 8, vtip(BUR1) + BUR_OFF, burrot)   # withdraws over 8 frames
    for _cn in CUTN: vkey(_cn, BE, vtip(BE).z); vkey(_cn, CK0, vtip(BUR1).z - 0.0002); vkey(_cn, CK0 + 5, SL_BOT - 0.003); vkey(_cn, CK0 + 6, -9.0)   # crack: the kerf line runs the remaining way to the underside in 5 frames
    tool_vis(HP, [(BE - 8, BUR1 + 9)])
    for nm_ in ('HpHead', 'HpNeck', 'HpBody'): O[nm_].animation_data_clear(); O[nm_].hide_render = True
    MISTC.animation_data_clear(); vis(MISTC, [(BE, BUR1 + 1)])
    return vtip
bur_keys(SL_TOP - 0.50 * (SL_TOP - SL_BOT))
vis(T3, [(0, CK0 + 6)])   # whole tooth stays below the head until the crack has run through
for nm in ('HpHead', 'HpNeck', 'HpBody'):
    O[nm].animation_data_clear(); O[nm].hide_render = True
shk = O['BurShank']; shk.scale = (1, 1, 3.2); shk.location.z = 0.0008 + 0.0192   # shank bottom inside the head (a 3 mm gap left the head as a floating ball)
pg_ = [n for n in mGold.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
mBurS, _bn, _bo, _bp = newmat('BurSteel'); _bp.inputs['Base Color'].default_value = (0.62, 0.63, 0.66, 1); _bp.inputs['Metallic'].default_value = 1.0; _bp.inputs['Roughness'].default_value = 0.25; _bp.inputs['Alpha'].default_value = 1.0; _bp.inputs['Transmission Weight'].default_value = 0.0; _bn.links.new(_bp.outputs[0], _bo.inputs['Surface'])
mBurH, _bn, _bo, _bp = newmat('BurHeadCarbide'); _bp.inputs['Base Color'].default_value = (0.25, 0.25, 0.27, 1); _bp.inputs['Metallic'].default_value = 0.8; _bp.inputs['Roughness'].default_value = 0.35; _bn.links.new(_bp.outputs[0], _bo.inputs['Surface'])
setmat(O['BurShank'], mBurS); setmat(O['BurHead'], mBurH)
_hd = O['BurHead']; _hb = bmesh.new(); bmesh.ops.create_uvsphere(_hb, u_segments=24, v_segments=12, radius=0.001); _hb.to_mesh(_hd.data); _hb.free(); _hd.location.z = 0.001   # visible dark round head
noise_bump(mGold.node_tree, pg_, 9000, 1.0, 0.00004, voronoi=True)
rnd = random.Random(5)
mDust, nt, out, p = newmat('Chip'); p.inputs['Base Color'].default_value = (0.55, 0.42, 0.28, 1); p.inputs['Roughness'].default_value = 0.5   # dentin chips, darker than enamel so they read
mMist, ntm_, outm_, pm_ = newmat('Mist'); pm_.inputs['Base Color'].default_value = (0.85, 0.92, 1.0, 1); pm_.inputs['Transmission Weight'].default_value = 0.7; pm_.inputs['Roughness'].default_value = 0.1; ntm_.links.new(pm_.outputs[0], outm_.inputs['Surface'])
nt.links.new(p.outputs[0], out.inputs['Surface'])
for i in range(400):
    mist = False
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=math.exp(rnd.uniform(math.log(0.0004), math.log(0.0013))))
    if not mist: bmesh.ops.randomize_vertices(bm, verts=bm.verts, ammount=0.00015, seed=i) if hasattr(bmesh.ops, 'randomize_vertices') else None
    dd = D.objects.new(('Mist%d' if mist else 'Chip%d') % i, D.meshes.new('dust%d' % i)); bm.to_mesh(dd.data); bm.free(); link(dd); setmat(dd, mDust if i % 2 else mTooth)   # dentin and enamel flakes
    fb = rnd.randint(BUR0 + 8, BUR1 - 10); life = rnd.randint(8, 12)   # all gone by f150
    p0 = Vector((C3.x + 0.0012, split_y, max(Z_CREST, hi.z) + 0.0004)); vel = Vector((rnd.uniform(0.5, 1.0), rnd.uniform(-0.7, 0.7), rnd.uniform(0.4, 1.0))).normalized() * rnd.uniform(0.007, 0.014)   # spray leaves the cut mouth, outside the tooth
    dd.location = p0; dd.scale = (1.0, rnd.uniform(0.18, 0.4), rnd.uniform(0.5, 1.0)); dd.rotation_euler = (rnd.random() * 6.3, rnd.random() * 6.3, 0); dd.keyframe_insert('location', frame=fb); dd.keyframe_insert('scale', frame=fb)
    dd.location = p0 + vel + Vector((0, 0, -0.003)); dd.scale = (0.6 * dd.scale[0], 0.6 * dd.scale[1], 0.6 * dd.scale[2])
    dd.keyframe_insert('location', frame=fb + life); dd.keyframe_insert('scale', frame=fb + life)
    vis(dd, [(fb, fb + life)])
    if mist: setmat(dd, mMist); dd.scale = (0.5, 0.5, 2.5); dd.keyframe_insert('scale', frame=fb)   # water-mist streak
# ---- timeline after the cut: crack (152-172), nerve beat with the roots in place (160-206), crown out (206-244), roots out (244-284) ----
NB0, NB1 = 160, 206
CRJ = Vector((0, 0.0003, 0)); CLJ = cl0 + Vector((0, -0.00015, 0.0001))   # the halves jump apart when the crack closes (f163-165)
kloc(ROOT, CK0 + 5, cr0); krot(ROOT, CK0 + 5, (0, 0, 0)); kloc(ROOT, CK0 + 7, cr0 + CRJ); krot(ROOT, CK0 + 7, (0, 0, 0))
kloc(CROWN, CK0 + 5, cl0); krot(CROWN, CK0 + 5, (0, 0, 0)); kloc(CROWN, CK0 + 7, CLJ); krot(CROWN, CK0 + 7, (0, 0, 0))
kloc(CROWN, NB1, CLJ); krot(CROWN, NB1, (0, 0, 0))
kloc(CROWN, NB1 + 8, CLJ + Vector((0.0020, 0.0005, 0.0010))); krot(CROWN, NB1 + 8, (R(-6), 0, 0))
kloc(CROWN, NB1 + 24, CLJ + Vector((0.0060, 0.0015, 0.011))); krot(CROWN, NB1 + 24, (R(-25), R(10), R(-8)))
kloc(CROWN, NB1 + 38, CLJ + Vector((0.0140, 0.002, 0.045))); krot(CROWN, NB1 + 38, (R(-40), R(16), R(-14)))
vis(CROWN, [(BUR0 + 6, NB1 + 38)])
R_OUT = NB1 + 38
kloc(ROOT, R_OUT, cr0 + CRJ); krot(ROOT, R_OUT, (0, 0, 0))
kloc(ROOT, R_OUT + 12, cr0 + Vector((0.0002, -0.0045, 0.0004))); krot(ROOT, R_OUT + 12, (R(4), 0, 0))
kloc(ROOT, R_OUT + 26, cr0 + Vector((0.0020, -0.0050, 0.012))); krot(ROOT, R_OUT + 26, (R(12), 0, 0))
kloc(ROOT, R_OUT + 40, cr0 + Vector((0.0050, -0.0050, 0.040))); krot(ROOT, R_OUT + 40, (R(16), 0, 0))
vis(ROOT, [(BUR0 + 6, R_OUT + 40)])
# ---- nerve beat: dark bracket + "1~2 mm" between root tip and nerve, two pulses ----
vkey(NERVE2_EM, 0, 0.3); vkey(NERVE2_EM, NB0, 0.3)
pulse_peaks = (NB0 + 16, NB0 + 34)
for pk in pulse_peaks:
    vkey(NERVE2_EM, pk - 7, 0.4); vkey(NERVE2_EM, pk, 2.4); vkey(NERVE2_EM, pk + 9, 0.6)
vkey(NERVE2_EM, R_OUT + 20, 0.6); vkey(NERVE2_EM, 279, 0.3); vkey(NERVE2_EM, 288, 5.0); vkey(NERVE2_EM, E0 - 1, 0.8)   # last pulse under the empty socket
def _nz(y):   # nerve centre z along the control polyline
    pp = sorted(pts, key=lambda q: q[1])
    for a_, b_ in zip(pp, pp[1:]):
        if a_[1] <= y <= b_[1]: t_ = (y - a_[1]) / (b_[1] - a_[1]); return a_[2] + (b_[2] - a_[2]) * t_
    return pp[-1][2]
_near = min((v for v in _t3v if Y_S0 < v.y < hi.y), key=lambda v: v.z - _nz(v.y))   # tooth point nearest the canal: the bracket goes here (caption: 사랑니 밑)
floor_z = _near.z; ntop2 = _nz(_near.y) + NR
mInk, nt, out, p = newmat('Ink'); p.inputs['Base Color'].default_value = (0.015, 0.012, 0.01, 1); p.inputs['Roughness'].default_value = 0.6
nt.links.new(p.outputs[0], out.inputs['Surface'])
bx = X_CUT + 0.0024; by = BRK_Y
mBr, nt, out, p = newmat('BracketWhite'); _e = nt.nodes.new('ShaderNodeEmission'); _e.inputs['Strength'].default_value = 3.0; nt.links.new(_e.outputs[0], out.inputs['Surface'])
bx = X_CUT + 0.0030; by = _near.y
_brk = [cyl('Gap2', 0.00016, floor_z - ntop2, mBr, 12, None, (bx, by, (floor_z + ntop2) / 2))]
for i, z in enumerate((floor_z, ntop2)):
    t_ = cyl('Gap2c%d' % i, 0.00016, 0.0014, mBr, 12, None, (bx, by, z)); t_.rotation_euler = (R(90), 0, 0); _brk.append(t_)
fc = D.curves.new('GapLabel', 'FONT'); fc.body = '1~2 mm'; fc.size = 0.0021; fc.align_y = 'CENTER'; fc.align_x = 'LEFT'   # right of the bracket: left of it the blurred second molar covers the pill
fc.font = D.fonts.load((__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../branding/_src/public/fonts/Pretendard-Bold.otf'))
fc.size = 0.0024; fc.space_character = 1.12
mWhite, nt, out, p = newmat('LabelWhite'); em_ = nt.nodes.new('ShaderNodeEmission'); em_.inputs['Strength'].default_value = 4.0; nt.links.new(em_.outputs[0], out.inputs['Surface'])
mPill, nt, out, p = newmat('LabelPill'); p.inputs['Base Color'].default_value = (0.005, 0.005, 0.006, 1); p.inputs['Roughness'].default_value = 0.8; nt.links.new(p.outputs[0], out.inputs['Surface'])
LBL = link(D.objects.new('GapLabel', fc)); setmat(LBL, mWhite); LBL.location = (bx + 0.0012, by + 0.0019, (floor_z + ntop2) / 2)   # in front of the tooth
_pw, _ph = fc.size * 3.3, fc.size * 1.05
_pm = D.meshes.new('pill'); _pb = bmesh.new(); bmesh.ops.create_cube(_pb, size=1.0); _pb.to_mesh(_pm); _pb.free()
PILL = link(D.objects.new('LabelPill', _pm)); setmat(PILL, mPill); PILL.parent = LBL; PILL.location = (_pw / 2 - 0.0001, fc.size * 0.08, -0.0002); PILL.scale = (_pw + 0.0008, _ph + 0.0006, 0.0001)
_bv = PILL.modifiers.new('bv', 'BEVEL'); _bv.width = 0.0004; _bv.segments = 6; _bv.affect = 'EDGES'
for o in _brk:
    vis(o, [(NB0 + 6, NB1 + 1)])
    if o is not LBL:
        o.scale = (0, 0, 0); o.keyframe_insert('scale', frame=NB0 + 6); o.scale = (1, 1, 1); o.keyframe_insert('scale', frame=NB0 + 12); o.keyframe_insert('scale', frame=NB1 - 16); o.scale = (0, 0, 0); o.keyframe_insert('scale', frame=NB1 - 6)
LBL.scale = (0, 0, 0); LBL.keyframe_insert('scale', frame=NB0 + 8); LBL.scale = (1, 1, 1); LBL.keyframe_insert('scale', frame=NB0 + 14)
LBL.keyframe_insert('scale', frame=NB1 - 16); LBL.scale = (0, 0, 0); LBL.keyframe_insert('scale', frame=NB1 - 6)   # gone before the camera starts
print('gap mm', round((floor_z - ntop2) * 1000, 2))
# ---- gingiva (review 13): ONE soft-tissue layer made from the bone's own crest faces, offset outward with solidify, scalloped away from each tooth neck
# with a boolean against slightly inflated tooth copies; the part over the wisdom tooth is the flap, cut loose along two incision lines ----
GUMMODE = __import__('os').environ.get('GUMMODE', 'layer')   # 'layer' (draft25) or 'line' (draft25b: a thin gum line on the crest, no flap)
mGumV, nt, out, p = newmat('GumVol')
colvar(nt, p, (0.60, 0.30, 0.29, 1), (0.57, 0.28, 0.27, 1), 900)   # even moist pink: no radial gradient
p.inputs['Subsurface Weight'].default_value = 0.05; p.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.18); p.inputs['Subsurface Scale'].default_value = 0.002
p.inputs['Roughness'].default_value = 0.5; p.inputs['Coat Weight'].default_value = 0.2; p.inputs['Coat Roughness'].default_value = 0.3; p.inputs['Specular IOR Level'].default_value = 0.2
noise_bump(nt, p, 1500, 0.08, 0.00008); nt.links.new(p.outputs[0], out.inputs['Surface'])
mwm = MAND.matrix_world; n3m = mwm.to_3x3()
GX0, GX1, GY0, GY1, GZ0 = X_CUT - 0.0070, X_CUT + 0.0012, -0.0700, hi.y + 0.0045, 1.5230
_bmc = bmesh.new(); _bmc.from_mesh(MAND.data)
_drop = [f for f in _bmc.faces if not (GX0 < (mwm @ f.calc_center_median()).x < GX1 and GY0 < (mwm @ f.calc_center_median()).y < GY1 and (mwm @ f.calc_center_median()).z > GZ0 and (n3m @ f.normal).z > 0.25)]
bmesh.ops.delete(_bmc, geom=_drop, context='FACES')
bmesh.ops.transform(_bmc, matrix=mwm, verts=_bmc.verts)
FY0, FY1 = lo.y + 0.0010, hi.y + 0.0030   # incision lines: the flap is the part of the layer over the wisdom tooth
for _yy in ((FY0, FY1) if GUMMODE == 'layer' else ()):
    bmesh.ops.bisect_plane(_bmc, geom=list(_bmc.verts) + list(_bmc.edges) + list(_bmc.faces), plane_co=(0, _yy, 0), plane_no=(0, 1, 0))
def _gum_obj(name, bmx, keep):
    b_ = bmx.copy(); bmesh.ops.delete(b_, geom=[f for f in b_.faces if not keep(f.calc_center_median().y)], context='FACES')
    me_ = D.meshes.new(name); b_.to_mesh(me_); b_.free(); o_ = link(D.objects.new(name, me_)); setmat(o_, mGumV); o_.data.materials.append(mFlapInner)
    return o_
THK = 0.0018 if GUMMODE == 'layer' else 0.0008
GUMM = _gum_obj('GumLayer', _bmc, (lambda y: y < FY0 or y > FY1) if GUMMODE == 'layer' else (lambda y: True))
_so = GUMM.modifiers.new('sol', 'SOLIDIFY'); _so.thickness = THK; _so.offset = 1.0; _so.material_offset = 0
sel_only(GUMM); bpy.ops.object.modifier_apply(modifier='sol')
# scalloped margins: inflated copies of every lower tooth, the contact point and its surroundings
sc.frame_set(0); bpy.context.view_layer.update()
def _inflated(src, d):
    o_ = src.copy(); o_.data = src.data.copy(); o_.animation_data_clear(); o_.parent = None; link(o_); o_.matrix_world = src.matrix_world.copy(); o_.hide_render = True
    sel_only(o_); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rm_ = o_.modifiers.new('rm', 'REMESH'); rm_.mode = 'VOXEL'; rm_.voxel_size = 0.00035; bpy.ops.object.modifier_apply(modifier='rm')
    dp_ = o_.modifiers.new('dp', 'DISPLACE'); dp_.direction = 'NORMAL'; dp_.strength = d; dp_.mid_level = 0.0; bpy.ops.object.modifier_apply(modifier='dp')
    return o_
_cuts = [_inflated(o_, 0.0010) for o_ in O if o_.type == 'MESH' and o_.name.startswith('Lower') and o_.name.endswith('.l') and o_.name != 'Lower medial incisor.l' and o_.hide_render is not None and (O['Lower second molar tooth.l'].location - o_.location).length < 0.1]
_bs = bmesh.new(); bmesh.ops.create_icosphere(_bs, subdivisions=3, radius=0.0024); bmesh.ops.translate(_bs, vec=CONTACT, verts=_bs.verts)
_cm = D.meshes.new('ContactCut'); _bs.to_mesh(_cm); _bs.free(); _cs_o = link(D.objects.new('ContactCut', _cm)); _cuts.append(_cs_o)
for _c in _cuts:
    try: boolean_apply(GUMM, _c)
    except Exception as e_: print('gum boolean skipped', _c.name, e_)
    _c.hide_render = True
_cb = bmesh.new(); _cb.from_mesh(GUMM.data); bmesh.ops.dissolve_degenerate(_cb, edges=_cb.edges, dist=0.00002); _cb.to_mesh(GUMM.data); _cb.free()
GUMM.modifiers.new('sub', 'SUBSURF').levels = 1
for _pg in GUMM.data.polygons: _pg.use_smooth = True
print('gum layer verts', len(GUMM.data.vertices), 'cutters', len(_cuts))
if GUMMODE == 'layer':
    GUMV = _gum_obj('GumFlap', _bmc, lambda y: FY0 < y < FY1)
    _cy = (FY0 + FY1) / 2
    for _v in GUMV.data.vertices: _v.co.y = _cy + (_v.co.y - _cy) * 0.965   # a hair of gap along the incision
    _so = GUMV.modifiers.new('sol', 'SOLIDIFY'); _so.thickness = THK; _so.offset = 1.0; _so.material_offset = 1; _so.use_rim = True
    GUMV.modifiers.new('sub', 'SUBSURF').levels = 1
    for _pg in GUMV.data.polygons: _pg.use_smooth = True
    _xs = [v.co.x for v in GUMV.data.vertices]; _hx = min(_xs); _hzs = [v.co.z for v in GUMV.data.vertices if v.co.x < _hx + 0.0006]; _hz = sum(_hzs) / len(_hzs)
    set_origin(GUMV, Vector((_hx, _cy, _hz)))   # hinge: the lingual edge of the flap
    GUMV.shape_key_add(name='Basis'); _sk = GUMV.shape_key_add(name='Curl'); _rc = -0.010   # lengthwise curl across the flap's width: the free edge rolls up
    for _v in GUMV.data.vertices:
        u_, z_ = _v.co.x, _v.co.z; a_ = u_ / _rc
        _sk.data[_v.index].co = Vector((_rc * math.sin(a_) - z_ * math.sin(a_), _v.co.y, _rc - _rc * math.cos(a_) + z_ * math.cos(a_)))
    _l0 = GUMV.location.copy()
    for _f, _r, _dz, _kv in ((14, 0, 0.0, 0.0), (18, -45, 0.0030, 0.35), (24, -110, 0.0032, 0.75), (29, -160, 0.0008, 1.0)):   # opens over 15 frames, then rests folded on the crest
        GUMV.rotation_euler = (0, R(_r), 0); GUMV.location = _l0 + Vector((0, 0, _dz)); GUMV.keyframe_insert('rotation_euler', frame=_f); GUMV.keyframe_insert('location', frame=_f)
        _sk.value = _kv; _sk.keyframe_insert('value', frame=_f)
    print('flap verts', len(GUMV.data.vertices), 'hinge z', round(_hz, 4))

LBL.hide_render = True; PILL.hide_render = True   # label is drawn in 2D over the render (label2d.py): the blurred ramus slab clipped the 3D label
GUM_LO.hide_render = True; GUM_LO.animation_data_clear()   # buccal side is cut away in the section; the gum was a blurred pink block in the foreground
# ---- pulp dot on the root cut face ----
_cf = [ROOT.matrix_world @ p.center for p in ROOT.data.polygons if p.material_index == 2]
if _cf:
    _cc_ = sum(_cf, Vector()) / len(_cf)
    mPulp, _pn, _po, _pp = newmat('Pulp'); _pp.inputs['Base Color'].default_value = (0.45, 0.07, 0.06, 1); _pp.inputs['Roughness'].default_value = 0.3; _pn.links.new(_pp.outputs[0], _po.inputs['Surface'])
    PD = cyl('PulpDot', 0.0006, 0.00008, mPulp, 24, None, (_cc_.x, _cc_.y - 0.00005, _cc_.z)); PD.rotation_euler = (R(90), 0, 0); parent(PD, ROOT); vis(PD, [(CK0 + 5, R_OUT + 40)])
print('root cap faces', len(_cf))
# ---- one camera, one continuous move (roll levels the occlusal plane) ----
from mathutils import Quaternion
cd = D.cameras.new('CamV2'); cd.lens = 55; cd.clip_start = 0.002; cd.clip_end = 5
cd.dof.use_dof = True; cd.dof.aperture_fstop = 14.0
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
ckey(0, CONTACT, Vector((1, -0.10, 0.14)), 0.055)   # hook: close on the contact so the push reads
ckey(30, CONTACT + Vector((0, 0.001, 0)), Vector((1, -0.10, 0.14)), 0.062)
ckey(60, C3 + Vector((0, -0.003, 0.0)), Vector((1, -0.10, 0.16)), 0.085)
ckey(BUR0 + 10, C3 + Vector((0, -0.002, 0.002)), Vector((0.9, -0.22, 0.38)), 0.070)
ckey(BUR1, C3 + Vector((0, -0.002, 0.002)), Vector((0.9, -0.2, 0.42)), 0.064)
GAPMID = Vector((X_CUT + 0.0012, _near.y + 0.0008, (floor_z + ntop2) / 2))
ckey(NB0 + 14, GAPMID, Vector((1, -0.19, 0.12)), 0.044)   # turned 7 deg so the ramus clears the label   # bracket >= 40 px
ckey(NB1 - 2, GAPMID + Vector((0, 0.0003, 0)), Vector((1, -0.18, 0.10)), 0.040)
ckey(NB1 + 4, GAPMID + Vector((0, 0.0004, 0.0001)), Vector((1, -0.18, 0.11)), 0.041)   # ease-in over 6 frames
ckey(NB1 + 22, C3 + Vector((0, -0.002, 0.004)), Vector((0.95, -0.22, 0.30)), 0.072)
_fc = Vector((hi.x - 0.0030, lo.y + 0.0035, hi.z - 0.0030))   # focal plane on the wisdom tooth crown / the contact for the opening
for _f in (0, 12): FOC.location = _fc; FOC.keyframe_insert('location', frame=_f)
for _f, _fs in ((0, 22.0), (12, 22.0), (40, 14.0)): cd.dof.aperture_fstop = _fs; cd.dof.keyframe_insert('aperture_fstop', frame=_f)
ckey(R_OUT, C3 + Vector((0, 0.001, 0.002)), Vector((0.95, -0.16, 0.28)), 0.068)
ckey(R_OUT + 26, C3 + Vector((0, 0.002, 0.001)), Vector((1, -0.12, 0.22)), 0.062)
ckey(E0, C3 + Vector((0, 0.001, -0.002)), Vector((1, -0.10, 0.18)), 0.058)
LBL.constraints.new('COPY_ROTATION').target = CAMV
sc.camera = CAMV
from bpy_extras.object_utils import world_to_camera_view
def _scr_y(w, f):
    sc.frame_set(f); return 1.0 - world_to_camera_view(sc, CAMV, w).y
_sl_w = [T3.matrix_world @ v.co for v in T3.data.vertices if abs((T3.matrix_world @ v.co).y - split_y) < 0.0003 and (T3.matrix_world @ v.co).x > X_CUT]   # the visible part of the section (in front of the cut plane)
_sy = [_scr_y(w, BUR1) for w in _sl_w]; _ytop, _ybot = min(_sy), max(_sy); _yt = _ytop + 0.55 * (_ybot - _ytop)   # head stops a little below the tooth's mid-height in camera space
_a, _b = SL_BOT, SL_TOP
for _ in range(40):
    _m = (_a + _b) / 2
    if _scr_y(Vector((hi.x - 0.0008, split_y, _m)), BUR1) > _yt: _a = _m
    else: _b = _m
ZB = (_a + _b) / 2; print('bur stop z', round(ZB, 5), 'depth frac', round((SL_TOP - ZB) / (SL_TOP - SL_BOT), 3), 'tooth screen y', round(_ytop * 800), round(_ybot * 800), 'head', round(_yt * 800))
bur_keys(ZB)
# bake the static bone: subsurf + crypt boolean applied once (no per-frame boolean)
sc.frame_set(0); sel_only(MAND)
for mname in [m.name for m in MAND.modifiers]:
    bpy.ops.object.modifier_apply(modifier=mname)
for _pg in MAND.data.polygons: _pg.use_smooth = True
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
area('Key', (0.30, -0.22, 0.42), 0.5, 0.25, (1.0, 0.94, 0.86))
T3L = area('T3Fill', (0.040, -0.030, 0.035), 0.035, 0.012, (1.0, 0.97, 0.92))   # lights the wisdom tooth like its neighbour while the gum opens
for _f, _e in ((0, 0.035), (28, 0.035), (46, 0.0)): T3L.data.energy = _e; T3L.data.keyframe_insert('energy', frame=_f)
area('Fill', (0.35, 0.05, -0.05), 0.35, 0.4, (0.8, 0.88, 1.0))
area('Rim', (-0.10, 0.35, 0.22), 34, 0.15, (0.75, 0.88, 1.0))
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
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.6
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.use_persistent_data = True
bpy.ops.wm.save_as_mainfile(filepath=HERE + 'wisdom.blend')
print('SAVED')
