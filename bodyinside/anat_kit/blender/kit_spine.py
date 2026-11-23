"""anat_kit spine/cutaway components (episode 2, neck). Import after kit:  from kit import *; from kit_spine import *
Lessons from episode 1 baked in: one continuous closed mesh per structure (voxel remesh), ONE smooth boolean for any cutaway with a
trabecular fill on the cut face and a cortical rim tube around it, rigid FK chain for posture, skinning by hooks (no per-frame booleans)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from kit import *

# ------------------------------------------------------------------ materials
def trabecular_material(name='Trabecular', scale=2200, base=(0.80, 0.66, 0.50, 1)):
    m, nt, out, p = newmat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = base; r.color_ramp.elements[0].position = 0.10
    r.color_ramp.elements[1].color = (0.30, 0.13, 0.09, 1); r.color_ramp.elements[1].position = 0.26
    nt.links.new(vor.outputs['Distance'], r.inputs['Fac']); nt.links.new(r.outputs['Color'], p.inputs['Base Color'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.5; b.inputs['Distance'].default_value = 0.0001
    nt.links.new(vor.outputs['Distance'], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.55; nt.links.new(p.outputs[0], out.inputs['Surface']); return m

def cortex_material(name='Cortex'):
    m, nt, out, p = newmat(name)
    colvar(nt, p, (0.80, 0.72, 0.58, 1), (0.72, 0.64, 0.50, 1), 2000); p.inputs['Roughness'].default_value = 0.5   # rim = bone colour (white rims read as loose fragments)
    nt.links.new(p.outputs[0], out.inputs['Surface']); return m

def disc_materials():
    """annulus (fibrous, bluish white, wet) and nucleus (translucent amber gel). Returns (annulus, nucleus)"""
    a, nt, out, p = newmat('Annulus')
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 900; wv.inputs['Distortion'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    rr = nt.nodes.new('ShaderNodeValToRGB'); rr.color_ramp.elements[0].color = (0.62, 0.66, 0.70, 1); rr.color_ramp.elements[1].color = (0.80, 0.82, 0.82, 1)
    nt.links.new(wv.outputs['Fac'], rr.inputs['Fac']); nt.links.new(rr.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.32; p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.1
    p.inputs['Subsurface Weight'].default_value = 0.35; p.inputs['Subsurface Scale'].default_value = 0.003; p.inputs['Subsurface Radius'].default_value = (0.9, 0.9, 1.0)
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.25; bm.inputs['Distance'].default_value = 0.00008
    nt.links.new(wv.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], p.inputs['Normal']); nt.links.new(p.outputs[0], out.inputs['Surface'])
    n, nt, out, p = newmat('Nucleus')
    p.inputs['Base Color'].default_value = (0.95, 0.78, 0.45, 1); p.inputs['Roughness'].default_value = 0.08; p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Coat Roughness'].default_value = 0.03
    p.inputs['Subsurface Weight'].default_value = 0.6; p.inputs['Subsurface Scale'].default_value = 0.004; p.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.3)
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return a, n

# ------------------------------------------------------------------ one continuous solid, one smooth cut
def smooth_solid(o, voxel=0.0004, subsurf=1, smooth_iter=8, smooth_factor=0.5):
    """Catmull-Clark (rounds the 1000-vertex Z-Anatomy facets) -> voxel remesh (ONE closed manifold solid) -> light smoothing."""
    sel_only(o)
    if subsurf:
        s = o.modifiers.new('ss', 'SUBSURF'); s.levels = subsurf; s.render_levels = subsurf; bpy.ops.object.modifier_apply(modifier='ss')
    r = o.modifiers.new('rm', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = voxel; r.use_smooth_shade = True; bpy.ops.object.modifier_apply(modifier='rm')
    if smooth_iter:
        sm = o.modifiers.new('sm', 'SMOOTH'); sm.iterations = smooth_iter; sm.factor = smooth_factor; bpy.ops.object.modifier_apply(modifier='sm')
    for pg in o.data.polygons: pg.use_smooth = True
    return o

def cut_half(o, x=0.0, keep_positive=True, cut_mat=None, reach=0.4):
    """Single EXACT boolean: remove everything on the camera side of the plane x. Cut faces get cut_mat (material transfer)."""
    cutter_me = D.meshes.new('cutbox'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cutter_me); bm.free()
    c = link(D.objects.new('cutbox_tmp', cutter_me)); c.scale = (reach, reach, reach)
    c.location = (x - reach / 2 if keep_positive else x + reach / 2, 0.0, 1.5)
    if cut_mat is not None: cutter_me.materials.append(cut_mat)
    if cut_mat is not None and cut_mat.name not in [m.name for m in o.data.materials if m]: o.data.materials.append(cut_mat)
    boolean_apply(o, c); D.objects.remove(c)
    for pg in o.data.polygons: pg.use_smooth = True
    return o

def cut_face_index(o, cut_mat_name):
    ms = [m.name if m else '' for m in o.data.materials]; return ms.index(cut_mat_name) if cut_mat_name in ms else None

def flatten_cut(o, cut_mat_name, x):
    """cut faces are planar by construction: snap their vertices to x and mark them flat-shaded (kills the smooth-shading ripple of a voxel mesh on the section)"""
    idx = cut_face_index(o, cut_mat_name)
    if idx is None: return 0
    n = 0
    for pg in o.data.polygons:
        if pg.material_index == idx: pg.use_smooth = False; n += 1
    return n

def cortical_rim(o, cut_mat_name, rim_mat, radius=0.00017, name=None):
    """ONE continuous round tube along every boundary edge of the section face (inset_region left dashes and ticks on thin triangles)."""
    idx = cut_face_index(o, cut_mat_name)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.edges.ensure_lookup_table()
    be = [e for e in bm.edges if any(f.material_index == idx for f in e.link_faces) and not all(f.material_index == idx for f in e.link_faces)]
    vi = {}; vl = []; el = []
    for e in be:
        ids = []
        for v in e.verts:
            if v.index not in vi: vi[v.index] = len(vl); vl.append(o.matrix_world @ v.co)
            ids.append(vi[v.index])
        el.append(tuple(ids))
    bm.free()
    me = D.meshes.new((name or o.name) + '_rimedges'); me.from_pydata([tuple(v) for v in vl], el, []); me.update()
    r = link(D.objects.new(name or ('Rim_' + o.name), me)); sel_only(r); bpy.ops.object.convert(target='CURVE')
    r = bpy.context.active_object; r.name = name or ('Rim_' + o.name)
    r.data.dimensions = '3D'; r.data.bevel_depth = radius; r.data.bevel_resolution = 2; r.data.use_fill_caps = True
    r.data.materials.clear(); r.data.materials.append(rim_mat); return r

# ------------------------------------------------------------------ intervertebral disc that fits the real endplates
def _hit(bvh, p, d, maxd):
    h = bvh.ray_cast(p, d, maxd); return h[0] if h and h[0] is not None else None

def disc_between(name, U_bvh, L_bvh, probe_y, mat, n_r=9, n_t=48, n_h=6, margin=0.00025, bulge=0.0002, embed=0.00015, reach=0.0045):
    """Disc = the space between the inferior endplate of U and the superior endplate of L, found by vertical ray casts on the (uncut, remeshed) solids.
    Footprint = polar star-shaped region (centre on x=0) where both rays hit within `reach`; wall rows bulge outward a little.
    Returns (obj, info). Top ring rows are embedded `embed` into U, bottom rows into L, so no seam shows when the vertebrae rotate."""
    # gap height on the centre line: sample probe_y, walk down from above U to find hits U_top, U_bot, L_top
    # zm: midpoint of the largest gap in the column hit list around the disc (U bottom .. L top)
    def gap_mid(x, y):
        # hits of U and L separately; U's lowest hit above L's highest hit
        zu = []; zl = []
        for bv, store in ((U_bvh, zu), (L_bvh, zl)):
            p = Vector((x, y, 1.7))
            while True:
                h = bv.ray_cast(p, Vector((0, 0, -1)), 2.0)
                if h[0] is None: break
                store.append(h[0].z); p = h[0] + Vector((0, 0, -0.00002))
        return zu, zl
    def gap_at(y):
        zu, zl = gap_mid(0.0, y)
        if not zu or not zl: return None
        zl_top = max(zl); cand = [z for z in zu if z > zl_top]
        if not cand: return None
        u_bot = min(cand); return (u_bot, zl_top) if 0.0015 < u_bot - zl_top < 0.008 else None
    cands = [(y, gap_at(y)) for y in [k * 0.0005 for k in range(-24, 80)]]; cands = [c for c in cands if c[1]]
    if not cands: raise RuntimeError('no disc gap found on the centre line')
    run0 = [cands[0]]   # the anterior-most contiguous run of valid columns = the vertebral body / disc. Later runs are laminae (also gaps) and must not move the centre
    for c in cands[1:]:
        if c[0] - run0[-1][0] < 0.0011: run0.append(c)
        else: break
    mid = run0[len(run0) // 2]; probe_y = mid[0]; u_bot, l_top = mid[1]; zm = (u_bot + l_top) / 2
    def zpair(x, y):
        up = _hit(U_bvh, Vector((x, y, zm)), Vector((0, 0, 1)), reach); dn = _hit(L_bvh, Vector((x, y, zm)), Vector((0, 0, -1)), reach)
        return (up.z, dn.z) if up is not None and dn is not None and up.z - dn.z > 0.0003 else None
    # centre: scan y at x=0 for the extent
    ys = [probe_y + k * 0.0005 for k in range(-30, 31)]; good = [y for y in ys if zpair(0.0, y)]
    # contiguous run containing probe_y
    run = [probe_y]
    y = probe_y
    while zpair(0.0, y - 0.0005): y -= 0.0005; run.append(y)
    y = probe_y
    while zpair(0.0, y + 0.0005): y += 0.0005; run.append(y)
    yc = (min(run) + max(run)) / 2
    rb = []
    for j in range(n_t):
        th = 2 * math.pi * j / n_t; c, s = math.cos(th), math.sin(th); r = 0.0; step = 0.00025
        while r < 0.03 and zpair(c * (r + step), yc + s * (r + step)): r += step
        rb.append(max(r - margin, 0.001))
    rb = [sum(rb[(j + k) % n_t] for k in (-2, -1, 0, 1, 2)) / 5 for j in range(n_t)]   # moving average
    bm = bmesh.new(); top_c = None
    def zz(x, y):
        zp = zpair(x, y)
        if zp is None:
            zp = zpair(0.0, yc)
        return zp
    cz = zz(0.0, yc)
    topv = [[bm.verts.new((0, yc, cz[0] + embed))]]; botv = [[bm.verts.new((0, yc, cz[1] - embed))]]
    for i in range(1, n_r + 1):
        rt, rbm = [], []
        for j in range(n_t):
            th = 2 * math.pi * j / n_t; x = math.cos(th) * rb[j] * i / n_r; y = yc + math.sin(th) * rb[j] * i / n_r; z = zz(x, y)
            rt.append(bm.verts.new((x, y, z[0] + embed))); rbm.append(bm.verts.new((x, y, z[1] - embed)))
        topv.append(rt); botv.append(rbm)
    wall = []
    for h in range(1, n_h):
        t = h / n_h; row = []
        for j in range(n_t):
            xt, yt, zt = topv[-1][j].co; xb, yb, zb = botv[-1][j].co
            th = 2 * math.pi * j / n_t; bl = bulge * math.sin(math.pi * t)
            row.append(bm.verts.new((xt + (xb - xt) * (1 - t) + math.cos(th) * bl, yt + (yb - yt) * (1 - t) + math.sin(th) * bl, zt + (zb - zt) * (1 - t))))
        wall.append(row)
    for j in range(n_t):
        jn = (j + 1) % n_t
        bm.faces.new((topv[0][0], topv[1][jn], topv[1][j]))
        bm.faces.new((botv[0][0], botv[1][j], botv[1][jn]))
        for i in range(1, n_r):
            bm.faces.new((topv[i][j], topv[i][jn], topv[i + 1][jn], topv[i + 1][j]))
            bm.faces.new((botv[i][jn], botv[i][j], botv[i + 1][j], botv[i + 1][jn]))
        rows = [topv[-1]] + wall + [botv[-1]]
        for a, b in zip(rows, rows[1:]): bm.faces.new((a[j], b[j], b[jn], a[jn]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for pg in me.polygons: pg.use_smooth = True
    o = link(D.objects.new(name, me))
    return o, {'yc': yc, 'rb': rb, 'zm': zm, 'gap_mm': round((cz[0] - cz[1]) * 1000, 2)}

def nucleus_from(disc_info, disc_obj, name, mat, scale=(0.6, 0.55), shift_y=0.0006, inset=0.0006, n_t=48, n_r=6):
    """gel core inside a disc: a scaled copy of the disc footprint, heights pulled in by `inset` from the endplates (closed mesh)."""
    yc = disc_info['yc']; src = disc_obj.data
    top = {}; bot = {}
    # sample the disc's top/bottom surface heights from its own verts (nearest in xy)
    pts = [(v.co.x, v.co.y, v.co.z) for v in src.vertices]
    mz = sum(p[2] for p in pts) / len(pts)
    T = [p for p in pts if p[2] >= mz]; B = [p for p in pts if p[2] < mz]
    def nz(arr, x, y):
        best = min(arr, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2); return best[2]
    rb = disc_info['rb']; nt0 = len(rb)
    bm = bmesh.new()
    def r_at(j):
        return rb[int(round(j * nt0 / n_t)) % nt0]
    cy = yc + shift_y
    tv = [[bm.verts.new((0, cy, nz(T, 0, cy) - inset))]]; bv = [[bm.verts.new((0, cy, nz(B, 0, cy) + inset))]]
    for i in range(1, n_r + 1):
        rt, rbm = [], []
        for j in range(n_t):
            th = 2 * math.pi * j / n_t; f = i / n_r
            x = math.cos(th) * r_at(j) * scale[0] * f; y = cy + math.sin(th) * r_at(j) * scale[1] * f * (disc_info['rb'][0] / max(r_at(j), 1e-6) if False else 1.0)
            # round the lip: pull heights in more toward the rim
            lip = inset * (1 + 2.2 * f ** 3)
            rt.append(bm.verts.new((x, y, nz(T, x, y) - lip))); rbm.append(bm.verts.new((x, y, nz(B, x, y) + lip)))
        tv.append(rt); bv.append(rbm)
    for j in range(n_t):
        jn = (j + 1) % n_t
        bm.faces.new((tv[0][0], tv[1][jn], tv[1][j])); bm.faces.new((bv[0][0], bv[1][j], bv[1][jn]))
        for i in range(1, n_r):
            bm.faces.new((tv[i][j], tv[i][jn], tv[i + 1][jn], tv[i + 1][j])); bm.faces.new((bv[i][jn], bv[i][j], bv[i + 1][j], bv[i + 1][jn]))
        bm.faces.new((tv[-1][j], tv[-1][jn], bv[-1][jn], bv[-1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for pg in me.polygons: pg.use_smooth = True
    return link(D.objects.new(name, me))

# ------------------------------------------------------------------ posture rig: rigid FK chain of X-rotations (flexion = +X rotation, head tilts toward -y)
class FKChain:
    """bodies bottom->top; pivots[i] = world point of the joint between bodies[i] and bodies[i+1] (disc centre). Body i+1 is parented to joint i,
    joint i+1 to body i+1, so rotations accumulate exactly like a spine. fixed body = bodies[0]. Key with set_angles(frame, [deg per joint])."""
    def __init__(self, bodies, pivots, extra_children=None):
        self.bodies = bodies; self.joints = []
        prev = None
        for i, pv in enumerate(pivots):
            j = D.objects.new('J%d' % i, None); j.empty_display_type = 'PLAIN_AXES'; j.empty_display_size = 0.004; link(j); j.location = pv
            j.rotation_mode = 'XYZ'; self.joints.append(j)
        bpy.context.view_layer.update()
        for i, j in enumerate(self.joints):
            par = bodies[i]
            if i > 0: self._parent(j, bodies[i])           # joint i sits on body i (lower body of the pair i, i+1)
            self._parent(bodies[i + 1], j)
        bpy.context.view_layer.update()
    @staticmethod
    def _parent(child, par):
        bpy.context.view_layer.update()   # a freshly created object has a stale (identity) matrix_world until updated
        mw = child.matrix_world.copy(); child.parent = par; child.matrix_parent_inverse = par.matrix_world.inverted(); child.matrix_world = mw
    def set_angles(self, f, degs):
        for j, d in zip(self.joints, degs):
            j.rotation_euler = (math.radians(d), 0, 0); j.keyframe_insert('rotation_euler', index=0, frame=f)

def ease(t): t = max(0.0, min(1.0, t)); return t * t * t * (t * (6 * t - 15) + 10)   # smootherstep

class Posture:
    """piecewise posture timeline: states = [(frame, [deg per joint])]; between two states joint angles are eased (hold = same state twice)."""
    def __init__(self, states): self.states = sorted(states, key=lambda s: s[0])
    def at(self, f):
        S = self.states
        if f <= S[0][0]: return list(S[0][1])
        for (f0, a0), (f1, a1) in zip(S, S[1:]):
            if f0 <= f <= f1:
                t = ease((f - f0) / max(1, f1 - f0)); return [x + (y - x) * t for x, y in zip(a0, a1)]
        return list(S[-1][1])
    def bake(self, chain, f0, f1):
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'   # sampled every frame: linear keeps the eased curve exact (Blender 5 actions are layered, no fcurves)
        for f in range(f0, f1 + 1): chain.set_angles(f, self.at(f))
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'

# ------------------------------------------------------------------ skin a mesh to rigid bodies with hooks (weights by height between body anchors)
def skin_to_bodies(obj, bodies, anchors_z, power=1.0, spread=None):
    """Hook-skin `obj` (identity transform, world-space mesh) to rigid `bodies` whose rest heights are `anchors_z` (ascending with body order).
    Weight of body i = smooth tent over neighbouring anchors. Bodies must have identity world matrix at rest (true for world-space meshes parented through FKChain)."""
    n = len(bodies); zs = list(anchors_z)
    ws = [[0.0] * n for _ in obj.data.vertices]
    for vi, v in enumerate(obj.data.vertices):
        z = v.co.z
        if spread:   # gaussian blend over neighbouring bodies: a smooth centreline for tubes (cord, roots, curve line) instead of piecewise-linear kinks
            sg = spread * (zs[-1] - zs[0]) / (n - 1); g = [math.exp(-((z - a) / sg) ** 2) for a in zs]; tot = sum(g) or 1.0
            for i in range(n): ws[vi][i] = g[i] / tot
        elif z <= zs[0]: ws[vi][0] = 1.0
        elif z >= zs[-1]: ws[vi][-1] = 1.0
        else:
            for k in range(n - 1):
                if zs[k] <= z <= zs[k + 1]:
                    t = (z - zs[k]) / (zs[k + 1] - zs[k]); t = t * t * (3 - 2 * t); ws[vi][k] = 1 - t; ws[vi][k + 1] = t; break
    for i, b in enumerate(bodies):
        g = obj.vertex_groups.new(name='sk_%s' % b.name)
        for vi in range(len(ws)):
            if ws[vi][i] > 1e-4: g.add([vi], ws[vi][i], 'REPLACE')
        h = obj.modifiers.new('hook_%s' % b.name, 'HOOK'); h.object = b; h.vertex_group = g.name; h.strength = 1.0; h.falloff_type = 'NONE'
        h.matrix_inverse = b.matrix_world.inverted()

def tint_material(mat, color=(1.0, 0.55, 0.10, 1), glow=0.8, name=None):
    """copy of a Principled-based material with a keyed 'Tint' Value (0 = as is, 1 = amber + glow). Returns (material, tint_value_node)."""
    m = mat.copy(); m.name = name or (mat.name + 'Tint'); nt = m.node_tree; p = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    v = nt.nodes.new('ShaderNodeValue'); v.name = 'Tint'; mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    if src: nt.links.new(src, mx.inputs['A'])
    else: mx.inputs['A'].default_value = p.inputs['Base Color'].default_value
    mx.inputs['B'].default_value = color; nt.links.new(v.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Emission Color'].default_value = color; g = nt.nodes.new('ShaderNodeMath'); g.operation = 'MULTIPLY'; g.inputs[1].default_value = glow
    nt.links.new(v.outputs[0], g.inputs[0]); nt.links.new(g.outputs[0], p.inputs['Emission Strength']); return m, v

# ------------------------------------------------------------------ own-built cord and roots (BodyParts3D has no spinal cord or spinal nerves)
def cord_and_roots(info, order, rb_dir=12, cord_r=0.0031, behind=0.0055, out_x=0.040):
    """Spinal cord = one round tube along the canal (x = 0, y = posterior disc edge + behind); at each disc level a root pair leaves it laterally to a ganglion
    in the intervertebral foramen and a short trunk beyond. Returns (cord, roots, ganglia) meshes. info: {tag: {'yc','zm','rb'}}; order: tags top -> bottom."""
    P = []
    for t in order:
        i = info[t]; P.append(Vector((0.0, i['yc'] + i['rb'][rb_dir] + behind, i['zm'])))
    import numpy as _np
    _c = _np.polyfit([p.z for p in P], [p.y for p in P], 3); P = [Vector((p.x, float(_np.polyval(_c, p.z)), p.z)) for p in P]   # smooth canal axis (disc centres are noisy)
    up = P[0] + (P[0] - P[1]).normalized() * 0.035; dn = P[-1] + (P[-1] - P[-2]).normalized() * 0.30
    mC = newmat('CordTmp')[0]; mR = newmat('RootTmp')[0]
    pts = catmull_rom([up] + P + [dn], 10)
    cord = tube_from_points('SpinalCord', pts, cord_r, mC, res=20); sel_only(cord); bpy.ops.object.convert(target='MESH'); cord = bpy.context.active_object; cord.name = 'SpinalCord'
    roots = []; gang = []
    for t, p in zip(order, P):
        for sgn, dy in ((1, -0.0035), (2, 0.0035)):   # anterior and posterior rootlet
            a = Vector((0.001, p.y + dy * 0.6, p.z + 0.0015 * sgn)); b = Vector((0.010, p.y + dy * 0.8, p.z + 0.0004 * sgn - 0.001)); c = Vector((0.016, p.y + dy * 0.2, p.z - 0.0012))
            r = tube_from_points('Rt_%s_%d' % (t, sgn), catmull_rom([a, b, c], 8), 0.0014, mR, res=8); roots.append(r)
        g = Vector((0.0175, p.y + 0.0006, p.z - 0.0012))
        n = tube_from_points('Tr_%s' % t, catmull_rom([g, g + Vector((0.006, -0.002, -0.002)), Vector((out_x, p.y - 0.004, p.z - 0.005))], 8), 0.0024, mR, res=10); roots.append(n)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.0045); bmesh.ops.scale(bm, vec=(1.3, 0.9, 1.1), verts=bm.verts)
        me = D.meshes.new('Ga_' + t); bm.to_mesh(me); bm.free(); go = link(D.objects.new('Ga_' + t, me)); go.location = g; gang.append(go)
    def merge(objs, name):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            if o.type == 'CURVE': sel_only(o); bpy.ops.object.convert(target='MESH')
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); r = bpy.context.active_object; r.name = name; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for pg in r.data.polygons: pg.use_smooth = True
        return r
    R_ = merge([D.objects[o.name] for o in roots], 'SpinalRoots'); G_ = merge([D.objects[o.name] for o in gang], 'SpinalGanglia')
    for o in (cord, R_, G_): o['src'] = 'own'; o.data.materials.clear()
    return cord, R_, G_

def catmull_rom(P, n=12):
    out = []; Pp = [P[0]] + list(P) + [P[-1]]
    for i in range(1, len(Pp) - 2):
        p0, p1, p2, p3 = Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2]
        for kk in range(n): t = kk / n; out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1]); return out
