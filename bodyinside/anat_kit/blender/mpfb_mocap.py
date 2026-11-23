"""Offline (run once, ~1-2 min): MPFB human + Mixamo mocap retarget -> baked 'Timeline' action on HumanRig, saved to assets/mpfb/human_mpfb_mocap.blend.
usage: Blender -b assets/mpfb/human_mpfb.blend -P mpfb_mocap.py
Timeline (30 fps, episode frames): 0-100 'Texting While Standing' (phone comes up, f0 upright) + growing slump; 100-118 back to neutral (person already dissolved);
118-819 neutral hold (the skeleton's chain root follows the hips/spine, so it stays put); 819-846 into the payoff start; 846-968 forward-head payoff = texting hold + exaggerated
(but anatomical) forward-head extras (lower-neck flexion, head level, chin poked forward, rounded upper back); 968-1000 straightens in place into 'Standing Idle'; 1000- idle."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(bpy.data.filepath)) + '/../../blender') if False else None
KITB = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KITB)
import mocap_retarget as R
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(KITB))
from asset_paths import asset
sc = bpy.context.scene
body = bpy.data.objects['HumanBody']; rig = bpy.data.objects['HumanRig']
# 1. keep only the body surface (drop MPFB helper geometry)
vg = body.vertex_groups
if 'body' in vg:
    import bmesh
    bm = bmesh.new(); bm.from_mesh(body.data); di = vg['body'].index; dl = bm.verts.layers.deform.verify()
    kill = [v for v in bm.verts if di not in v[dl]]; bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(body.data); bm.free()
print('body verts', len(body.data.vertices))
for m in list(body.modifiers):
    if m.type == 'MASK': body.modifiers.remove(m)
# 2. sources
srcs = {}
for key, fn in (('tx', 'Texting While Standing'), ('ld', 'Looking Down'), ('id', 'Standing Idle')):
    before = set(bpy.data.objects.keys()); bpy.ops.import_scene.fbx(filepath=asset('assets/mocap/' + fn + '.fbx'))
    new = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]; srcs[key] = [o for o in new if o.type == 'ARMATURE'][0]
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: pass
tgt = R.Rig(rig)
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
th = (rig.matrix_world @ rig.data.bones['pelvis'].matrix_local).translation.z
def srcrig(k): return R.Rig(srcs[k])
S = {k: srcrig(k) for k in srcs}
def at(k, fr):
    sc.frame_set(int(fr)); bpy.context.view_layer.update()
    return S[k]
HIP0 = {}
for k in S: at(k, 1); HIP0[k] = S[k].pose_world(R.P + 'Hips').translation.copy()
SC = {k: th / S[k].pose_world(R.P + 'Hips').translation.z for k in S}
def sm(a, b, x): t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
# exaggerated forward-head extras at full strength (degrees about world X, + = forward) and head protraction (m, -y = forward); tuned on proof frames
PAY_EX = dict(Spine=6, Spine1=12, Spine2=20, Neck=-4, Head=-22); PAY_SH = {'Neck': Vector((0, -0.06, -0.015)), 'Head': Vector((0, -0.06, -0.02)), 'LeftShoulder': Vector((0, -0.04, 0.0)), 'RightShoulder': Vector((0, -0.04, 0.0))}   # owner round 4: grotesque but possible forward head (ear 12-15 cm in front of the shoulder), hump, rolled shoulders
OPEN_EX = dict(Spine=3, Spine1=5, Spine2=8, Neck=10, Head=8); OPEN_SH = {'Neck': Vector((0, -0.012, -0.004)), 'Head': Vector((0, -0.016, -0.006))}
def scl(d, w): return {k: v * w for k, v in d.items()}
def pose(f):
    """-> (clip, src frame, extra, shift) pieces for frame f; blended in bake()."""
    if f <= 100:
        w = sm(0, 90, f); return [(1.0, 'tx', 1 + f * 1.0, scl(OPEN_EX, w), {k: v * w for k, v in OPEN_SH.items()})]
    if f <= 118:
        t = sm(100, 118, f); return [(1 - t, 'tx', 101, OPEN_EX, OPEN_SH), (t, 'id', 1, {}, {})]
    if f < 819: return [(1.0, 'id', 1, {}, {})]
    if f <= 846:
        t = sm(819, 846, f); return [(1 - t, 'id', 1, {}, {}), (t, 'tx', 100, scl(PAY_EX, 0.6), {k: v * 0.6 for k, v in PAY_SH.items()})]
    if f <= 968:
        w = 0.6 + 0.4 * sm(846, 900, f); return [(1.0, 'tx', 100 + (f - 846) * 1.0, scl(PAY_EX, w), {k: v * w for k, v in PAY_SH.items()})]
    if f <= 1000:
        t = sm(968, 1000, f); w = 1.0 - t
        return [(1 - t, 'tx', 100 + (968 - 846), scl(PAY_EX, 1.0), PAY_SH), (t, 'id', 1 + (f - 968) * 0.0, {}, {})]
    return [(1.0, 'id', 1 + (f - 1000) * 1.0, {}, {})]
def basis_of(clip, sf, ex, sh):
    s = at(clip, sf); return R.retarget_frame(s, tgt, SC[clip], HIP0[clip], extra=ex, shift=sh)
def blend(parts):
    out = {}
    for n in parts[0][1]:
        if len(parts) == 1: M = parts[0][1][n]; out[n] = (M.to_quaternion(), M.to_translation()); continue
        (w0, A), (w1, B) = parts; qa, qb = A[n].to_quaternion(), B[n].to_quaternion(); out[n] = (qa.slerp(qb, w1), A[n].to_translation().lerp(B[n].to_translation(), w1))
    return out
rig.animation_data_create()
import time; t0 = time.time(); NF = 1080
frames = list(range(0, 119, 2)) + [118, 819] + list(range(820, 1000, 2)) + list(range(1000, NF, 3)) + [NF - 1]
for f in sorted(set(frames)):
    parts = [(w, basis_of(c, sf, ex, sh)) for (w, c, sf, ex, sh) in pose(f)]
    bl = blend(parts)
    for n, (q, l) in bl.items():
        pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
print('baked in', round(time.time() - t0), 's')
act = rig.animation_data.action; act.name = 'Timeline'
for k in S:   # sources are no longer needed
    o = srcs[k]; bpy.data.objects.remove(o)
# own-built clothes: a plain T-shirt and trousers cut from the body surface by dominant bone, pushed out along the normals (same weights, same armature)
import bmesh
def garment(name, groups, off, zmin=-9, zmax=9, wmin=0.5):
    """cut from the body surface by SMOOTH bone weight (sum over `groups` >= wmin) and a height band, so the edges are clean; pushed out along the normals"""
    ob = body.copy(); ob.data = body.data.copy(); ob.name = name; bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(ob.data); dl = bm.verts.layers.deform.verify(); names = {g.index: g.name for g in ob.vertex_groups}
    def wsum(v): return sum(w for gi, w in v[dl].items() if names[gi] in groups)
    keep = {v.index for v in bm.verts if wsum(v) >= wmin and zmin <= v.co.z <= zmax}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.normal_update()
    for v in bm.verts: v.co += v.normal * off
    bm.to_mesh(ob.data); bm.free(); return ob
garment('HumanShirt', {'spine_01', 'spine_02', 'spine_03', 'clavicle_l', 'clavicle_r', 'upperarm_l', 'upperarm_r', 'pelvis'}, 0.013, zmin=0.86, zmax=1.43)
garment('HumanPants', {'pelvis', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r'}, 0.008, zmax=0.93)
hh = bpy.data.objects['HumanHair']; hb = bmesh.new(); hb.from_mesh(hh.data); hb.normal_update()
for v in hb.verts: v.co += v.normal * 0.007   # lift the hair off the scalp: the head surface showed through at the hairline
hb.to_mesh(hh.data); hb.free()
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in ('HumanBody', 'HumanHair', 'HumanShirt', 'HumanPants')]: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=KITB + '/../assets/mpfb/human_mpfb_mocap.blend')
