"""Person-reads-as-human measurements. usage: Blender -b EPISODE.blend -P human_gate.py -- OUT.json   (then checks.human_reads_as_human on the JSON)
For the payoff frames (f872-f968 every 8) and the neutral ending frame (f1040): projected HumanBody silhouette height / band height, head top above the shoulder dot on screen,
lowest skull/jaw point vs the shoulder (A_Acro) height, and the ear distance in front of the shoulder along the facing axis (-y), measured on the person's own head and shoulder joints (the skeleton anchors, whose ending alignment is a screen-space one, are listed as anchor_gap)."""
import bpy, sys, json, os, numpy as np
from bpy_extras.object_utils import world_to_camera_view as w2c
out = sys.argv[sys.argv.index('--') + 1]; sc = bpy.context.scene; cam = sc.camera; D = bpy.data
def measure(f):
    sc.frame_set(f); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); ps = []
    for nm in ('Skin.001', 'Outfit', 'Hair underlay'):
        e = D.objects[nm].evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world; ps += [w2c(sc, cam, mw @ v.co) for v in list(me.vertices)[::3]]; e.to_mesh_clear()
    ys = np.array([1 - p.y for p in ps if -0.2 < p.x < 1.2]); top = float(max(0.0, ys.min())); bot = float(min(1.0, ys.max()))
    acro = D.objects['A_Acro'].matrix_world.translation; ear = D.objects['A_Ear'].matrix_world.translation
    sh_y = 1 - w2c(sc, cam, acro).y
    zs = [(D.objects[n].matrix_world @ v.co).z for n in ('Skull', 'Mandible') for v in list(D.objects[n].data.vertices)[::7]]
    gap = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), 'scene_dump.json')))['EarShoulderGapCm'][str(f)] / 100.0   # anchors.json ear-ahead-of-shoulder x scale, written by build.py
    return {'f': f, 'anchor_gap': round(acro.y - ear.y, 4), 'band_h': round(bot - top, 3), 'head_above_shoulder': bool(top < sh_y - 0.02), 'skull_min_z': round(min(zs), 4), 'shoulder_z': round(acro.z, 4), 'ear_fwd': round(gap, 4)}
ep = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath),'episode.json')))
gap_label = next((label for label in ep.get('labels', []) if label['kind'] == 'gap'), None)
payoff = ep.get('payoff_frames') or range(gap_label['f0'], gap_label['f1'] + 1, 8)
neutral = ep.get('neutral_frame')
if neutral is None:
    fade = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), 'scene_dump.json')))['HumanFade']
    neutral = max(int(f) for f, value in fade.items() if int(f) > max(payoff) and value >= .99)
res = {'payoff': [measure(f) for f in payoff], 'neutral': measure(neutral)}
json.dump(res, open(out, 'w'), indent=1)
