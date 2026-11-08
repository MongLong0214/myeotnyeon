# per action: root/hips travel, in-place treadmill speed from planted foot, min/max hips height.
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = argv[0], argv[1], argv[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
pb = arm.pose.bones
hips = next(n for n in ('DEF-hips', 'pelvis') if n in pb)
feet = next(p for p in (('DEF-foot.L', 'DEF-foot.R'), ('foot_l', 'foot_r')) if p[0] in pb)
ad = arm.animation_data
res = {}
scn = bpy.context.scene
for a in acts:
    act = bpy.data.actions[a]
    for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
    ad.action = act
    if act.slots and ad.action_slot is None: ad.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    H = []; FL = []; FR = []
    for f in range(f0, f1 + 1):
        scn.frame_set(f)
        H.append(tuple(arm.matrix_world @ pb[hips].head))
        FL.append(tuple(arm.matrix_world @ pb[feet[0]].head)); FR.append(tuple(arm.matrix_world @ pb[feet[1]].head))
    fps = scn.render.fps
    # planted foot = lower one; horizontal speed
    sp = []
    for i in range(1, len(H)):
        lo = FL if FL[i][2] < FR[i][2] else FR
        dx = lo[i][0] - lo[i - 1][0]; dy = lo[i][1] - lo[i - 1][1]
        sp.append(((dx * dx + dy * dy) ** 0.5) * fps)
    sp.sort()
    res[a] = dict(frames=f1 - f0 + 1, fps=fps, seconds=round((f1 - f0) / fps, 2),
                  hips_travel_m=[round(H[-1][k] - H[0][k], 3) for k in range(3)],
                  hips_z_min=round(min(h[2] for h in H), 3), hips_z_max=round(max(h[2] for h in H), 3),
                  planted_foot_speed_median_mps=round(sp[len(sp) // 2], 3) if sp else None)
json.dump(res, open(out, 'w'), indent=1)
