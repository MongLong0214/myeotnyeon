"""Interpenetration gate (BVH overlap between named meshes on sampled frames). usage: Blender -b X.blend -P penetration_gate.py -- OUT.json [PAIRS.json]
Pairs default to episode.json "no_overlap": [["Mandible","Vertebra C3"], ...]; fails if the evaluated meshes' triangles overlap by more than `tol` triangle pairs (jaw through neck)."""
import bpy, sys, json, os
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; sc = bpy.context.scene
pairs = json.load(open(a[1])) if len(a) > 1 else json.load(open(os.path.dirname(bpy.data.filepath) + '/episode.json')).get('no_overlap', [])
step = 30; frames = list(range(sc.frame_start, sc.frame_end + 1, step)); res = {'pairs': pairs, 'violations': []}
def tree(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); vs = [e.matrix_world @ v.co for v in m.vertices]; ps = [tuple(p.vertices) for p in m.polygons]; t = BVHTree.FromPolygons(vs, ps); e.to_mesh_clear(); return t
for f in frames:
    sc.frame_set(f)
    for x, y in pairs:
        n = len(tree(bpy.data.objects[x]).overlap(tree(bpy.data.objects[y])))
        if n > 40: res['violations'].append({'frame': f, 'pair': [x, y], 'overlapping_triangle_pairs': n})
res['ok'] = not res['violations']; json.dump(res, open(OUT, 'w'), indent=1); print('PENETRATION', json.dumps(res)[:300])
