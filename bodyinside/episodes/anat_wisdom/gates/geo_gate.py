"""Blender geometry gate. usage: blender -b X.blend -P geo_gate.py -- spec.json  -> prints GATE_JSON {...}
spec: {"contacts":[["ThirdMolar","Lower second molar tooth.l",0.0003]], "gaps":[["Root","Nerve2",0.001,0.003,frame]]}
contact = min surface distance <= tol; gap = min distance between meshes within [lo,hi] metres at frame."""
import bpy, sys, json
from mathutils.bvhtree import BVHTree
spec = json.load(open(sys.argv[sys.argv.index('--') + 1]))
sc = bpy.context.scene
def wverts(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in m.vertices]; ps = [list(p.vertices) for p in m.polygons]; e.to_mesh_clear(); return vs, ps
def mindist(a, b):
    va, _ = wverts(a); vb, pb = wverts(b); t = BVHTree.FromPolygons(vb, pb)
    return min(t.find_nearest(v)[3] for v in va[::max(1, len(va) // 4000)])
out = {'contacts': [], 'gaps': [], 'pass': True}
for a, b, tol in spec.get('contacts', []):
    sc.frame_set(0); d = mindist(bpy.data.objects[a], bpy.data.objects[b]); ok = d <= tol
    out['contacts'].append({'a': a, 'b': b, 'dist_mm': round(d * 1000, 3), 'tol_mm': tol * 1000, 'ok': ok}); out['pass'] &= ok
for a, b, lo, hi, f in spec.get('gaps', []):
    sc.frame_set(f); d = mindist(bpy.data.objects[a], bpy.data.objects[b]); ok = lo <= d <= hi
    out['gaps'].append({'a': a, 'b': b, 'frame': f, 'dist_mm': round(d * 1000, 3), 'range_mm': [lo * 1000, hi * 1000], 'ok': ok}); out['pass'] &= ok
print('GATE_JSON ' + json.dumps(out))
