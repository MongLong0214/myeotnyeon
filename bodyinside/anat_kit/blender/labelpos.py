"""Projects every anchor empty named in episode.json labels to band-normalised screen coordinates, per frame.
usage: Blender -b X.blend -P labelpos.py -- EPISODE_DIR   -> EPISODE_DIR/label_pos.json  {frame: {anchor: [x, y]}}  (x,y in 0..1, y from the top)
Labels are drawn in 2D (labels2d.py) above the finished 3D frames, so nothing in the scene can occlude them."""
import bpy, json, sys
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
E = sys.argv[sys.argv.index('--') + 1]; ep = json.load(open(E + '/episode.json')); sc = bpy.context.scene; cam = sc.camera
names = sorted({l[k] for l in ep.get('labels', []) for k in ('anchor', 'anchor2') if l.get(k)}); out = {}
frames = sorted({f for l in ep.get('labels', []) for f in range(l['f0'], l['f1'] + 1)})
evidence = [ev for b in ep['beats'] for ev in b.get('evidence',[]) if ev['type'].startswith('anchors_')]
names = sorted(set(names) | {n for ev in evidence for n in (ev.get('anchors') or [ev.get('a'),ev.get('b')]) if n})
frames = sorted(set(frames) | {f for ev in evidence for f in ev.get('frames',[])})
args = sys.argv[sys.argv.index('--')+1:]
selection = set(json.load(open(args[1]))) if len(args)>1 else None
if selection is not None:
    evidence_frames = {f for ev in evidence for f in ev.get('frames', [])}
    frames = sorted((set(frames) & selection) | evidence_frames)
for f in frames:
    sc.frame_set(f); row = {}
    for n in names:
        c = world_to_camera_view(sc, cam, bpy.data.objects[n].matrix_world.translation); row[n] = [round(c.x, 4), round(1 - c.y, 4)]
    out[f] = row
# plumb landmarks, measured in projected pixels: the ear dot lies inside the outline of the ghost's own ear (hull of the skin's ear vertices, evaluated per frame),
# the shoulder dot inside the ghost body's silhouette (camera ray hits the skin) and outside the projected bbox of the cervical vertebrae.
pl = [l for l in ep.get('labels', []) if l['kind'] == 'plumb']
if pl:
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    sk = bpy.data.objects.get('Skin.001') or bpy.data.objects.get('HumanBody') or bpy.data.objects['Skin']; CERV = ['Atlas (C1)', 'Axis (C2)', 'Vertebra C3', 'Vertebra C4', 'Vertebra C5', 'Vertebra C6', 'Vertebra C7']; out['_plumb'] = {}
    def inside(poly, x, y):
        c = False; n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
        return c
    for f in frames:
        if not pl[0]['f0'] <= f <= pl[0]['f1']: continue
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); tree = BVHTree.FromObject(sk, dg); co = cam.matrix_world.translation
        dot = bpy.data.objects[pl[0]['anchor2']].matrix_world.translation; ear = bpy.data.objects[pl[0]['anchor']].matrix_world.translation
        mwi = sk.matrix_world.inverted(); co_l = mwi @ co; hit = tree.ray_cast(co_l, (mwi @ dot - co_l).normalized()); hit_e = tree.ray_cast(co_l, (mwi @ ear - co_l).normalized())   # BVH is in object space (the rigged person carries a root scale/offset)
        W_, H_ = sc.render.resolution_x, sc.render.resolution_y; Mp = np.array(cam.calc_matrix_camera(dg, x=W_, y=H_)) @ np.array(cam.matrix_world.inverted()); pts = []
        for n in CERV:   # exact projected extent of the cervical vertebrae (all vertices, not their loose bound boxes)
            o = bpy.data.objects[n]; k = len(o.data.vertices); a = np.empty(k * 3, dtype=np.float32); o.data.vertices.foreach_get('co', a); a = a.reshape(-1, 3)
            c = (np.c_[a, np.ones(k)] @ np.array(o.matrix_world).T) @ Mp.T; pts.append(np.c_[c[:, 0] / c[:, 3] * 0.5 + 0.5, 0.5 - c[:, 1] / c[:, 3] * 0.5])
        pts = np.vstack(pts); xs = [float(pts[:, 0].min()), float(pts[:, 0].max())]; ys = [float(pts[:, 1].min()), float(pts[:, 1].max())]
        q_ = Mp @ np.r_[np.array(dot), 1.0]; q2 = world_to_camera_view(sc, cam, dot); assert abs(q_[0] / q_[3] * 0.5 + 0.5 - q2.x) < 2e-3 and abs(0.5 - q_[1] / q_[3] * 0.5 - (1 - q2.y)) < 2e-3, 'vector projection disagrees with world_to_camera_view'
        d2 = world_to_camera_view(sc, cam, dot); e2 = world_to_camera_view(sc, cam, ear); dx, dy = d2.x, 1 - d2.y; ex, ey = e2.x, 1 - e2.y
        ae = bpy.data.objects[pl[0]['anchor']]; shp = {k: json.loads(ae['ear_' + k]) for k in ('outer', 'inner', 'tragus')}; tm = bpy.data.objects['A_TMJ'].matrix_world.translation
        def pj(pts): return [[round(q.x, 4), round(1 - q.y, 4)] for q in (world_to_camera_view(sc, cam, ae.matrix_world @ Vector((0.0, y_, z_))) for y_, z_ in pts)]
        poly = pj(shp['outer']); tq = world_to_camera_view(sc, cam, tm)
        outside = not (min(xs) <= dx <= max(xs) and min(ys) <= dy <= max(ys))
        out['_plumb'][str(f)] = {'in_skin': hit[0] is not None, 'ear_in_skin': hit_e[0] is not None, 'outside_spine_bbox': bool(outside), 'ear_above': ey < dy, 'ear_in_outline': inside([tuple(p) for p in poly], ex, ey), 'ear_inner': pj(shp['inner']), 'ear_tragus': pj(shp['tragus']), 'tmj': [round(tq.x, 4), round(1 - tq.y, 4)],
                                 'spine_bbox': [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)], 'shoulder': [round(dx, 4), round(dy, 4)], 'ear': [round(ex, 4), round(ey, 4)], 'ear_poly': poly}
json.dump(out, open(E + '/label_pos.json', 'w')); print('LABELPOS', len(out), 'frames', names)
