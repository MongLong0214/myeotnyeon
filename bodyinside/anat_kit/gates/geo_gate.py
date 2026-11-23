"""Blender geometry gate. usage: blender -b X.blend -P geo_gate.py -- spec.json  -> prints GATE_JSON {...}
spec: {"contacts":[["ThirdMolar","Lower second molar tooth.l",0.0003]], "gaps":[["Root","Nerve2",0.001,0.003,frame]]}
contact = min surface distance <= tol; gap = min distance between meshes within [lo,hi] metres at frame.
"stable": ["Crown","Root"] -> evaluated vertex count on every frame must stay >= 50 % of its median (catches collapsing booleans)."""
import bpy, sys, json
from mathutils.bvhtree import BVHTree
spec = json.load(open(sys.argv[sys.argv.index('--') + 1]))
sc = bpy.context.scene
def wverts(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in m.vertices]; ps = [list(p.vertices) for p in m.polygons]; e.to_mesh_clear(); return vs, ps
def mindist(a, b):
    va, pa = wverts(a); vb, pb = wverts(b); t = BVHTree.FromPolygons(vb, pb)
    if BVHTree.FromPolygons(va, pa).overlap(t): return 0.0
    return min(t.find_nearest(v)[3] for v in va[::max(1, len(va) // 4000)])
out = {'contacts': [], 'gaps': [], 'pass': True}
for tool, protected, first, last in spec.get('disjoint', []):
    hits = []
    for frame in range(first, last + 1):
        sc.frame_set(frame)
        tool_verts, tool_faces = wverts(bpy.data.objects[tool])
        organ_verts, organ_faces = wverts(bpy.data.objects[protected])
        tool_tree = BVHTree.FromPolygons(tool_verts, tool_faces)
        organ_tree = BVHTree.FromPolygons(organ_verts, organ_faces)
        if tool_tree.overlap(organ_tree):
            hits.append(frame)
    ok = not hits
    out.setdefault('disjoint', []).append({'tool': tool, 'protected': protected,
        'violations': hits, 'frames': [first,last], 'ok': ok})
    out['pass'] &= ok
for a, b, tol in spec.get('contacts', []):
    sc.frame_set(0); d = mindist(bpy.data.objects[a], bpy.data.objects[b]); ok = d <= tol
    out['contacts'].append({'a': a, 'b': b, 'dist_mm': round(d * 1000, 3), 'tol_mm': tol * 1000, 'ok': ok}); out['pass'] &= ok
for a, b, lo, hi, f in spec.get('gaps', []):
    sc.frame_set(f); d = mindist(bpy.data.objects[a], bpy.data.objects[b]); ok = lo <= d <= hi
    out['gaps'].append({'a': a, 'b': b, 'frame': f, 'dist_mm': round(d * 1000, 3), 'range_mm': [lo * 1000, hi * 1000], 'ok': ok}); out['pass'] &= ok
for a, b, lo, f0, f1 in spec.get('clearance', []):   # e.g. ["BurHead","Nerve2",0.001,78,170]: >= lo on every frame
    worst = (9, None)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); d = mindist(bpy.data.objects[a], bpy.data.objects[b])
        if d < worst[0]: worst = (d, f)
    ok = worst[0] >= lo; out.setdefault('clearance', []).append({'a': a, 'b': b, 'min_mm': round(worst[0] * 1000, 3), 'at_frame': worst[1], 'min_req_mm': lo * 1000, 'ok': ok}); out['pass'] &= ok
for n, f0, f1, mindeg in spec.get('rotation_delta', []):   # a key that must move something (nudge): degrees between two frames
    o = bpy.data.objects[n]; sc.frame_set(f0); q0 = o.matrix_world.to_quaternion(); sc.frame_set(f1); q1 = o.matrix_world.to_quaternion()
    import math; deg = math.degrees(q0.rotation_difference(q1).angle); ok = deg >= mindeg
    out.setdefault('rotation_delta', []).append({'obj': n, 'frames': [f0, f1], 'deg': round(deg, 2), 'ok': ok}); out['pass'] &= ok
for tool, tooth, plane, lo, f0, f1 in spec.get('underside', []):   # tool head must stay >= lo above the tooth's underside at the plane of the cut (plane = object whose world y marks it)
    P = bpy.data.objects[plane]; to = bpy.data.objects[tooth]; sc.frame_set(f0)
    y0 = P.matrix_world.translation.y; zs = [(to.matrix_world @ v.co).z for v in to.data.vertices if abs((to.matrix_world @ v.co).y - y0) < 0.0003]
    under = min(zs); worst = (9.0, f0)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); T = bpy.data.objects[tool]; hz = min((T.matrix_world @ v.co).z for v in T.data.vertices)
        if hz - under < worst[0]: worst = (hz - under, f)
    ok = worst[0] >= lo; out.setdefault('underside', []).append({'tool': tool, 'tooth': tooth, 'underside_z': round(under, 5), 'min_margin_mm': round(worst[0] * 1000, 3), 'at_frame': worst[1], 'min_req_mm': lo * 1000, 'ok': ok}); out['pass'] &= ok
for tool, tooth, plane, f0, f1, frac in spec.get('mid_height', []):   # camera space: the tool head's projected y must not pass top + frac*(bottom-top) of the tooth section, per frame
    from bpy_extras.object_utils import world_to_camera_view
    P = bpy.data.objects[plane]; to = bpy.data.objects[tooth]; Tl = bpy.data.objects[tool]; worst = (9.0, f0)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); cam = sc.camera; y0 = P.matrix_world.translation.y; xcut = spec.get('x_cut', -9.0)
        ys = [1 - world_to_camera_view(sc, cam, to.matrix_world @ v.co).y for v in to.data.vertices if abs((to.matrix_world @ v.co).y - y0) < 0.0003 and (to.matrix_world @ v.co).x > xcut]
        top, bot = min(ys), max(ys); limit = top + frac * (bot - top)
        head = max(1 - world_to_camera_view(sc, cam, Tl.matrix_world @ v.co).y for v in Tl.data.vertices)
        if limit - head < worst[0]: worst = (limit - head, f)
    ok = worst[0] >= 0; out.setdefault('mid_height', []).append({'tool': tool, 'tooth': tooth, 'frac': frac, 'worst_margin_px': round(worst[0] * sc.render.resolution_y, 1), 'at_frame': worst[1], 'ok': ok}); out['pass'] &= ok
for n in spec.get('stable', []):
    o = bpy.data.objects[n]; cnt = []
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); cnt.append(len(m.vertices)); e.to_mesh_clear()
    med = sorted(cnt)[len(cnt) // 2]; bad = [sc.frame_start + i for i, c in enumerate(cnt) if c < 0.5 * med]
    ok = not bad; out.setdefault('stable', []).append({'obj': n, 'median_verts': med, 'bad_frames': bad[:20], 'ok': ok}); out['pass'] &= ok
print('GATE_JSON ' + json.dumps(out))

args = sys.argv[sys.argv.index('--') + 1:]
if len(args)>1:
    with open(args[1],'w') as report: json.dump(out,report)
