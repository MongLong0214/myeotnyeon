"""anat_kit Blender library: materials, ghosting, animation helpers, rigs, procedural anatomy, gates-friendly placement.
Import from a build script run inside Blender:  import sys; sys.path.insert(0, KIT + '/blender'); from kit import *
Units: metres. Every function is extracted from the wisdom-tooth episode that passed the geometry gates."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_paths import asset
import bpy, bmesh, math, os
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
D = bpy.data; O = D.objects; R = math.radians
sc = bpy.context.scene
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _sc():
    return bpy.context.scene
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

def metal(name, rough=0.16, aniso=0.0, col=(0.82, 0.82, 0.84, 1)):
    m, nt, out, p = newmat(name)
    p.inputs['Base Color'].default_value = col; p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = rough; p.inputs['Anisotropic'].default_value = aniso
    nt.links.new(p.outputs[0], out.inputs['Surface']); return m

def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)

def kloc(o, f, p):
    o.location = p; o.keyframe_insert('location', frame=f)

def krot(o, f, r):
    o.rotation_euler = r; o.keyframe_insert('rotation_euler', frame=f)

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

# ---------------- generic additions ----------------
def world_bvh(o, evaluated=False):
    """BVH in WORLD space (FromObject is local space: that bug once left a 4 mm gap)."""
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
        t = BVHTree.FromPolygons([e.matrix_world @ v.co for v in m.vertices], [list(p.vertices) for p in m.polygons]); e.to_mesh_clear(); return t
    mw = o.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons])

def seat_against(mover, target, direction, step=0.0002, max_steps=200, back_off=0.5):
    """Translate `mover` along `direction` until it touches `target` (world BVH overlap), then back off half a step."""
    d = Vector(direction).normalized(); tb = world_bvh(target)
    for _ in range(max_steps):
        bpy.context.view_layer.update()
        if world_bvh(mover).overlap(tb): break
        mover.location += d * step
    mover.location -= d * step * back_off; bpy.context.view_layer.update()

def tube_from_points(name, pts, radius, mat, res=24):
    """Round continuous tube (nerve, vessel, canal) through points; AUTO handles; capped."""
    cu = D.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = radius; cu.bevel_resolution = 6; cu.use_fill_caps = True; cu.resolution_u = res
    o = link(D.objects.new(name, cu)); setmat(o, mat); return o

def emission_value(mat, color, strength=0.0):
    """Adds emission driven by a Value node to a Principled material; returns the node to key."""
    nt = mat.node_tree; p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    p.inputs['Emission Color'].default_value = color
    v = nt.nodes.new('ShaderNodeValue'); v.outputs[0].default_value = strength; nt.links.new(v.outputs[0], p.inputs['Emission Strength']); return v

def mask_halfspace(mat, axis='X', threshold=0.004, keep_greater=True, soft=0.0):
    """Multiply a ghostable material's opacity by a world-position mask (drop the far half of a bilateral mesh)."""
    nt = mat.node_tree; ms = [n for n in nt.nodes if n.type == 'MIX_SHADER'][0]
    src = ms.inputs['Fac'].links[0].from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    a, b = (threshold - soft / 2, threshold + soft / 2 + 1e-6)
    mr.inputs['From Min'].default_value = a; mr.inputs['From Max'].default_value = b
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = (0.0, 1.0) if keep_greater else (1.0, 0.0)
    nt.links.new(sep.outputs[axis], mr.inputs['Value'])
    m = nt.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'
    nt.links.new(src, m.inputs[0]); nt.links.new(mr.outputs['Result'], m.inputs[1]); nt.links.new(m.outputs[0], ms.inputs['Fac'])

def light_rig(target, scale=1.0, hdri=True, hdri_strength=0.14):
    """Key + fill + cool rim + warm rim + top, tracked on `target` (positions scaled for ~10 cm subjects)."""
    t = link(D.objects.new('LightTarget', None)); t.location = target
    def area(name, off, energy, size, color):
        d = D.lights.new(name, 'AREA'); d.energy = energy * scale * scale; d.size = size * scale; d.color = color
        o = link(D.objects.new(name, d)); o.location = Vector(target) + Vector(off) * scale
        c = o.constraints.new('TRACK_TO'); c.target = t; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    area('Key', (0.30, -0.22, 0.42), 8, 0.25, (1.0, 0.94, 0.86)); area('Fill', (0.35, 0.05, -0.05), 0.35, 0.4, (0.8, 0.88, 1.0))
    area('Rim', (-0.10, 0.35, 0.22), 16, 0.15, (0.75, 0.88, 1.0)); area('Rim2', (0.10, 0.30, 0.25), 4, 0.12, (1.0, 0.85, 0.7))
    area('Top', (0.02, -0.02, 0.30), 0.8, 0.2, (1.0, 0.97, 0.94))
    w = D.worlds.new('W'); _sc().world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    if hdri:
        env = w.node_tree.nodes.new('ShaderNodeTexEnvironment')
        env.image = D.images.load(asset('assets/studio_small_09_2k.exr')); w.node_tree.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = hdri_strength

def render_settings(w=1080, h=800, spp=64, blur=0.35):
    s = _sc(); r = s.render; r.engine = 'CYCLES'; r.resolution_x = w; r.resolution_y = h; r.film_transparent = True
    cy = s.cycles; cy.device = 'GPU'; cy.samples = spp; cy.use_denoising = True; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
    cy.transparent_max_bounces = 32; cy.max_bounces = 10; cy.transmission_bounces = 8
    s.view_settings.view_transform = 'Khronos PBR Neutral'; s.view_settings.look = 'None'; s.view_settings.exposure = -0.45
    r.use_motion_blur = blur > 0; r.motion_blur_shutter = blur
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'

class CameraPath:
    """One camera, one continuous move. key(frame, target, direction, distance). `roll_deg` levels a tilted occlusal/horizon plane."""
    def __init__(self, name='Cam', lens=55, fstop=8.0, roll_deg=0.0):
        cd = D.cameras.new(name); cd.lens = lens; cd.clip_start = 0.002; cd.clip_end = 5
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        self.cam = link(D.objects.new(name, cd)); self.cam.rotation_mode = 'QUATERNION'
        self.focus = link(D.objects.new(name + '_focus', None)); cd.dof.focus_object = self.focus
        self.roll = R(roll_deg); _sc().camera = self.cam
    def key(self, f, target, direction, dist):
        target = Vector(target); loc = target + Vector(direction).normalized() * dist
        q = (target - loc).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), self.roll)
        self.cam.location = loc; self.cam.rotation_quaternion = q
        self.cam.keyframe_insert('location', frame=f); self.cam.keyframe_insert('rotation_quaternion', frame=f)
        self.focus.location = target; self.focus.keyframe_insert('location', frame=f)

def pulse(value_node, frames_peaks, base=0.0, peak=3.0, width=8):
    """One ease-in/out per listed frame (no irregular flicker)."""
    for f in frames_peaks:
        vkey(value_node, f - width, base); vkey(value_node, f, peak); vkey(value_node, f + width * 2, base)

def import_parts(fbx_name, keep):
    """Legacy entry point retained to explain the DBCLS source requirement."""
    raise ValueError("New anatomy must come from DBCLS BodyParts3D Release 4.0. Use the region pack.")


def frosted_bone(name):
    """The look that passed review: translucent frosted cortical shell (SSS + coat), rim kept. Key the returned ghost node (0.8 typical)."""
    m, g, em = bone_material(name)
    p = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    p.inputs['Subsurface Weight'].default_value = 0.45; p.inputs['Subsurface Scale'].default_value = 0.003
    p.inputs['Coat Weight'].default_value = 0.35; p.inputs['Coat Roughness'].default_value = 0.25; p.inputs['Roughness'].default_value = 0.42
    for n in m.node_tree.nodes:
        if n.type == 'MAP_RANGE': n.inputs['To Min'].default_value = 0.07; n.inputs['To Max'].default_value = 0.78
    g.outputs[0].default_value = 0.8
    return m, g, em

HIGHLIGHT = (1.0, 0.58, 0.22, 1)   # the single highlight hue (amber) used for the subject structure
NERVE_YELLOW = (0.98, 0.82, 0.30, 1)

# ---------------- additions from wisdom draft12 (Fable review 3) ----------------
from mathutils import Matrix
def upright_mesh(o, deg, axis='X', pivot=None):
    """Re-pose a tooth in its socket: rotate the mesh vertices (not the object) about `pivot` (default: vertex centroid).
    Object transforms/animation stay untouched, so later keys (nudges) still act about the object origin."""
    mw = o.matrix_world; inv = mw.inverted(); vs = [mw @ v.co for v in o.data.vertices]
    c = Vector(pivot) if pivot is not None else sum(vs, Vector()) / len(vs)
    T = Matrix.Translation(c) @ Matrix.Rotation(R(deg), 4, axis) @ Matrix.Translation(-c)
    for v, w in zip(o.data.vertices, vs): v.co = inv @ (T @ w)
    o.data.update()

def _long_axis(pts):
    c = sum(pts, Vector()) / len(pts); C = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3): C[i][j] += d[i] * d[j]
    a = Vector((0, 0, 1))
    for _ in range(50): a = (C @ a).normalized()   # power iteration -> principal axis
    return c, (a if a.z > 0 else -a)

def sculpt_molar(o, levels=2, cej_frac=0.62, root_converge=0.5, root_curve=0.001, fissure=0.00035, cusp=0.00028, distal=(0, 1, 0), seed=3, root_len=1.0, cervical=0.00012):
    """Z-Anatomy has no third molars and its molars are smooth lumps. This turns a molar copy into a third molar:
    subdivide, converge the roots toward each other (tips nearly meet) with a distal curve, carve the occlusal fissure
    pattern (central, buccal, lingual, distobuccal grooves), raise five cusps, add fine crenulation.
    Works in the tooth's own frame (principal axis = occlusal up), so a tilted source tooth is fine. `distal` = world direction."""
    import mathutils.noise as mn
    sel_only(o); m = o.modifiers.new('ss', 'SUBSURF'); m.levels = levels; bpy.ops.object.modifier_apply(modifier='ss')
    me = o.data; mw = o.matrix_world
    P = [mw @ v.co for v in me.vertices]; c, ax = _long_axis(P)
    q = ax.rotation_difference(Vector((0, 0, 1))); Rq = q.to_matrix()
    dist_l = (Rq @ Vector(distal)); dist_l.z = 0; dist_l.normalize()
    side = Vector((0, 0, 1)).cross(dist_l)        # bucco-lingual axis in the tooth frame
    L = [Rq @ (p - c) for p in P]                 # tooth frame: z = occlusal
    zs = [p.z for p in L]; zmin, zmax = min(zs), max(zs); cej = zmin + cej_frac * (zmax - zmin)
    cr = [p for p in L if p.z > cej]; ctr = sum(cr, Vector()) / len(cr); ctr.z = 0
    U = [(p - ctr).dot(side) for p in L]; W = [(p - ctr).dot(dist_l) for p in L]
    au = max(abs(U[i]) for i in range(len(L)) if L[i].z > cej); aw = max(abs(W[i]) for i in range(len(L)) if L[i].z > cej)
    me.update(); N = [Rq @ (mw.to_3x3() @ v.normal).normalized() for v in me.vertices]
    g = lambda d, s: math.exp(-(d / s) ** 2)
    sm = lambda a, b, x: 0.0 if x <= a else 1.0 if x >= b else (lambda t: t * t * (3 - 2 * t))((x - a) / (b - a))
    cusps = [(0.48, -0.42), (0.50, 0.18), (0.30, 0.62), (-0.48, -0.38), (-0.46, 0.30)]
    occl = zmax - 0.32 * (zmax - cej)
    for i, p in enumerate(L):
        u, w = U[i], W[i]
        if p.z < cej:   # roots: converge and curve distally
            t = (cej - p.z) / (cej - zmin)
            k = 1 - root_converge * t ** 1.3
            p = p - dist_l * w * (1 - k) - side * u * (0.3 * root_converge * t) + dist_l * root_curve * t * t
            p.z = cej - (cej - p.z) * root_len   # third-molar roots are shorter
        elif p.z > occl and N[i].z > 0.15:
            h = sm(occl, zmax - 0.15 * (zmax - occl), p.z) * min(1.0, N[i].z / 0.5)
            un, wn = u / au, w / aw
            box = lambda x, a: 1 - sm(a - 0.12, a + 0.05, abs(x))
            fis = max(g(un, 0.075) * box(wn, 0.66),                       # central groove
                      g(wn + 0.08, 0.065) * sm(0.05, 0.25, un) * box(un, 0.95),   # buccal groove
                      g(wn - 0.02, 0.065) * sm(0.05, 0.25, -un) * box(un, 0.95),  # lingual groove
                      g(wn - 0.42, 0.06) * sm(0.10, 0.30, un) * box(un, 0.95))    # distobuccal groove
            bump = sum(g(((un - cu) ** 2 + (wn - cw) ** 2) ** 0.5, 0.26) for cu, cw in cusps)
            cren = mn.noise(Vector((u, w, p.z)) * 2600, noise_basis='PERLIN_ORIGINAL') * 0.00005
            p = p + N[i] * h * (cusp * min(1.0, bump) - fissure * fis + cren)
        if abs(p.z - cej) < 0.0012:   # cervical line: a fine groove at the CEJ with the enamel bulge just above it
            p = p - Vector((N[i].x, N[i].y, 0)) * (cervical * g(p.z - cej, 0.00025) - cervical * 0.6 * g(p.z - cej - 0.0009, 0.0004))
        L[i] = p
    Ri = Rq.inverted(); inv = mw.inverted()
    for v, p in zip(me.vertices, L): v.co = inv @ (Ri @ p + c)
    me.update(); return cej

def split_by_plane(src, name, co, no, cap_mat_index=2):
    """Static, robust split (bisect + triangle fill), returns a new object keeping the side `no` points to.
    Use this instead of animated EXACT booleans: those failed on single frames (mesh collapsed to 6 verts) and read as flash frames."""
    bm = bmesh.new(); bm.from_mesh(src.data); inv = src.matrix_world.inverted()
    lco = inv @ Vector(co); lno = (inv.to_3x3() @ Vector(no)).normalized()
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=lco, plane_no=lno, clear_inner=True)
    cut_edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
    old = set(bm.faces)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=cut_edges, normal=-lno)
    for fa in bm.faces:   # the cap = faces the fill created (triangle_fill does not report them)
        if fa not in old: fa.material_index = cap_mat_index; fa.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(D.objects.new(name, me)); o.matrix_world = src.matrix_world.copy()
    for m in src.data.materials: me.materials.append(m)
    return o

def add_fade(mat):
    """Extra opacity multiplier on a ghostable material (1 = as is, 0 = gone). Fade out, then hide: never pop."""
    nt = mat.node_tree; ms = [n for n in nt.nodes if n.type == 'MIX_SHADER'][0]
    src = ms.inputs['Fac'].links[0].from_socket if ms.inputs['Fac'].links else None
    v = nt.nodes.new('ShaderNodeValue'); v.name = 'Fade'; v.outputs[0].default_value = 1.0
    m = nt.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'
    if src: nt.links.new(src, m.inputs[0])
    else: m.inputs[0].default_value = ms.inputs['Fac'].default_value
    nt.links.new(v.outputs[0], m.inputs[1]); nt.links.new(m.outputs[0], ms.inputs['Fac']); return v

def point_mask_emission(mat, value_node, point, radius):
    """Emission only near `point` (world): strength = value * smoothstep(radius..0). Keeps a contact glow at the contact."""
    nt = mat.node_tree; p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    for l in list(p.inputs['Emission Strength'].links): nt.links.remove(l)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); d = nt.nodes.new('ShaderNodeVectorMath'); d.operation = 'DISTANCE'
    d.inputs[1].default_value = Vector(point); nt.links.new(geo.outputs['Position'], d.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = radius; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
    nt.links.new(d.outputs['Value'], mr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(mr.outputs['Result'], mul.inputs[0]); nt.links.new(value_node.outputs[0], mul.inputs[1]); nt.links.new(mul.outputs[0], p.inputs['Emission Strength'])

def drape_sheet(name, surface_bvh, x0, x1, y0, y1, z_top, n=40, lift=0.0002, thickness=0.0012, z_cap=None):
    """Sheet (gum, periosteum) draped on a surface by ray-casting down over an x/y rectangle, then solidified outward."""
    bm = bmesh.new(); grid = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * j / n
            hit = surface_bvh.ray_cast(Vector((x, y, z_top)), Vector((0, 0, -1)))
            if hit[0] is not None and (z_cap is None or hit[0].z < z_cap): grid[i, j] = bm.verts.new(hit[0] + Vector((0, 0, lift)))
    for i in range(n):
        for j in range(n):
            q = [grid.get(k) for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if all(q): bm.faces.new(q)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(D.objects.new(name, me))
    s = o.modifiers.new('sol', 'SOLIDIFY'); s.thickness = thickness; s.offset = 1.0
    o.modifiers.new('sm', 'SMOOTH').iterations = 4
    for pg in me.polygons: pg.use_smooth = True
    return o

def inset_cut_faces(o, mat_name, new_mat, width=0.0012):
    """Boolean section faces -> a cortical ring: inset the faces carrying `mat_name` by `width`, ring gets `new_mat`."""
    mats = [m.name if m else '' for m in o.data.materials]
    if mat_name not in mats: return 0
    idx = mats.index(mat_name); o.data.materials.append(new_mat); ridx = len(o.data.materials) - 1
    bm = bmesh.new(); bm.from_mesh(o.data)
    faces = [f for f in bm.faces if f.material_index == idx]
    r = bmesh.ops.inset_region(bm, faces=faces, thickness=width, depth=0.0, use_even_offset=True)
    for f in r['faces']: f.material_index = ridx
    bm.to_mesh(o.data); bm.free(); return len(r['faces'])

def drop_small_parts(o, min_verts=1000):
    """Delete loose mesh islands smaller than min_verts (Z-Anatomy jaws carry stray crypt shells that render as grey ovals)."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); seen = set(); kill = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        if len(comp) < min_verts: kill += comp
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(o.data); bm.free(); return len(kill)

def clip_box(mat, lo, hi, soft=0.0003):
    """Make a ghostable material fully transparent inside a world-space box (a cutaway without booleans).
    Z-Anatomy bones are not manifold: EXACT booleans on them leave cutter walls and slivers in frame."""
    nt = mat.node_tree; ms = [n for n in nt.nodes if n.type == 'MIX_SHADER'][0]
    src = ms.inputs['Fac'].links[0].from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    acc = None
    for ax, a, b in zip('XYZ', lo, hi):
        m1 = nt.nodes.new('ShaderNodeMapRange'); m1.interpolation_type = 'SMOOTHSTEP'
        m1.inputs['From Min'].default_value = a - soft; m1.inputs['From Max'].default_value = a + soft; nt.links.new(sep.outputs[ax], m1.inputs['Value'])
        m2 = nt.nodes.new('ShaderNodeMapRange'); m2.interpolation_type = 'SMOOTHSTEP'
        m2.inputs['From Min'].default_value = b - soft; m2.inputs['From Max'].default_value = b + soft
        m2.inputs['To Min'].default_value = 1.0; m2.inputs['To Max'].default_value = 0.0; nt.links.new(sep.outputs[ax], m2.inputs['Value'])
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(m1.outputs['Result'], mm.inputs[0]); nt.links.new(m2.outputs['Result'], mm.inputs[1])
        if acc is None: acc = mm
        else:
            m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; nt.links.new(acc.outputs[0], m3.inputs[0]); nt.links.new(mm.outputs[0], m3.inputs[1]); acc = m3
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(acc.outputs[0], inv.inputs[1])
    m4 = nt.nodes.new('ShaderNodeMath'); m4.operation = 'MULTIPLY'; nt.links.new(src, m4.inputs[0]); nt.links.new(inv.outputs[0], m4.inputs[1]); nt.links.new(m4.outputs[0], ms.inputs['Fac'])

def section_cap(src, name, x, y0, y1, z0, z1, face_mat, ring_mat, ring=0.0011, depth=0.0005):
    """Flat cut face for a clip_box cutaway: bisect the (evaluated) bone at x, fill the contour, keep y0..y1 / z0..z1,
    inset a cortical ring, extrude `depth` lingually (-x). Returns the cap object (material 0 = trabecular, 1 = cortex)."""
    dg = bpy.context.evaluated_depsgraph_get(); e = src.evaluated_get(dg); me0 = e.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me0); e.to_mesh_clear(); bm.transform(src.matrix_world)
    r = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=Vector((x, 0, 0)), plane_no=Vector((1, 0, 0)), clear_inner=True, clear_outer=True)
    edges = [g for g in r['geom_cut'] if isinstance(g, bmesh.types.BMEdge) and g.is_valid]
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00002)
    edges = [ed for ed in bm.edges]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=Vector((1, 0, 0)))
    for co, no in (((0, y0, 0), (0, 1, 0)), ((0, y1, 0), (0, -1, 0)), ((0, 0, z0), (0, 0, 1)), ((0, 0, z1), (0, 0, -1))):
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=Vector(co), plane_no=Vector(no), clear_inner=True)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for f in bm.faces:
        if f.normal.x < 0: f.normal_flip()
        f.material_index = 0
    ins = bmesh.ops.inset_region(bm, faces=list(bm.faces), thickness=ring, depth=0.0, use_even_offset=True)
    for f in ins['faces']: f.material_index = 1
    ex = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    for v in [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]: v.co.x -= depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(D.objects.new(name, me)); me.materials.append(face_mat); me.materials.append(ring_mat)
    return o

def boolean_apply(o, cutter, op='DIFFERENCE'):
    """One static EXACT boolean on a manifold target (cap slabs, voxel-remeshed cutters), applied immediately."""
    sel_only(o); b = o.modifiers.new('b', 'BOOLEAN'); b.object = cutter; b.operation = op; b.solver = 'EXACT'; b.use_hole_tolerant = True; b.material_mode = 'TRANSFER'
    bpy.ops.object.modifier_apply(modifier='b')

def half_shell(src, name, x, mat, keep_below=True):
    """Inside-out half of a closed cutter (socket bowl, canal groove) behind a section plane at x."""
    bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=Vector((x, 0, 0)),
                           plane_no=Vector((-1 if keep_below else 1, 0, 0)), clear_inner=True)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for pg in me.polygons: pg.use_smooth = True
    o = link(D.objects.new(name, me)); me.materials.append(mat); return o
