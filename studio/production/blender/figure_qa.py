"""Close-up QA of the faceless figures. Usage:
  Blender --background --factory-startup --python-exit-code 1 --python figure_qa.py -- OUT_DIR POSE[,POSE..] [--who=B]

For each pose: 6 views (front, back, left, right, 3/4 high, 3/4 low) + head/neck close-up + both hands
close-up, plus numeric checks printed as QA lines: lowest foot point vs ground, hand-to-torso clearance,
elbow/knee bend direction.
"""
import sys, os, math, json
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world2 as W
import people as P

a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; poses = a[1].split(','); who = next((x.split('=')[1] for x in a if x.startswith('--who=')), 'B')
os.makedirs(out, exist_ok=True)


def studio():
    W.reset(samples=16)
    s = bpy.context.scene
    s.eevee.use_raytracing = False
    s.render.resolution_x = s.render.resolution_y = 900
    W.world(haze=0.0, strength=0.4)
    W.plane('floor', (20, 20), (0, 0, 0), W.mat('fl', (0.35, 0.35, 0.36), rough=0.8))
    for i, (loc, e) in enumerate((((3, -4, 4), 900), ((-3.5, -2, 3), 450), ((0, 4, 3.5), 600))):
        l = W.light('AREA', f'L{i}', loc, e, size=(2.5, 2.5))
        l.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def bone_world(rig, name, tail=True):
    pb = rig.pose.bones[name]
    return rig.matrix_world @ (pb.tail if tail else pb.head)


def checks(rig, pose):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = 9.0; meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(rig.name) and o.visible_get()]
    for o in meshes:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            if z < zmin:
                zmin = z
        ev.to_mesh_clear()
    spine = [bone_world(rig, b, False) for b in ('Hips', 'Spine', 'Spine1', 'Neck')]
    def seg_dist(p):
        best = 9
        for q0, q1 in zip(spine, spine[1:]):
            d = q1 - q0; t = max(0, min(1, (p - q0).dot(d) / d.length_squared)); best = min(best, (q0 + d * t - p).length)
        return best
    hands = {s: bone_world(rig, f'{s}Hand') for s in ('Left', 'Right')}
    elbow = {}
    for s in ('Left', 'Right'):
        sh, el, wr = bone_world(rig, f'{s}Arm', False), bone_world(rig, f'{s}ForeArm', False), bone_world(rig, f'{s}Hand', False)
        elbow[s] = round(math.degrees((sh - el).angle(wr - el)), 1)
    knee = {}
    for s in ('Left', 'Right'):
        hp, kn, an = bone_world(rig, f'{s}UpLeg', False), bone_world(rig, f'{s}Leg', False), bone_world(rig, f'{s}Foot', False)
        knee[s] = round(math.degrees((hp - kn).angle(an - kn)), 1)
        fwd = (rig.matrix_world.to_3x3() @ Vector((0, -1, 0)))
        bend = (kn - (hp + an) / 2).dot(fwd)
        knee[s + '_bend_forward'] = round(bend, 3)
    r = dict(pose=pose, lowest_z=round(zmin, 3), hand_torso_clearance={s: round(seg_dist(p), 3) for s, p in hands.items()},
             elbow_angle=elbow, knee=knee)
    print('QA ' + json.dumps(r, ensure_ascii=False), flush=True)
    return r


def shoot(rig, pose, center, height):
    s = bpy.context.scene
    cd = bpy.data.cameras.new('qc'); cd.lens = 50; co = bpy.data.objects.new('qc', cd); s.collection.objects.link(co); s.camera = co
    tgt = Vector(center)
    yaw = rig.rotation_euler.z
    def rot(v):
        c, si = math.cos(yaw), math.sin(yaw); return Vector((v[0] * c - v[1] * si, v[0] * si + v[1] * c, v[2]))
    views = {'front': (0, -1, 0.15), 'back': (0, 1, 0.15), 'left': (1, 0, 0.1), 'right': (-1, 0, 0.1), 'q34hi': (0.7, -0.7, 0.55), 'q34lo': (-0.7, -0.7, -0.05)}
    dist = max(2.6, height * 1.7)
    for name, d in views.items():
        dv = rot(Vector(d)).normalized()
        co.location = tgt + dv * dist
        co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out, f'{who}_{pose}_{name}.png'); bpy.ops.render.render(write_still=True)
    neck = bone_world(rig, 'Head', False)
    cd.lens = 85
    for name, d in (('head_front', (0.15, -1, 0.05)), ('head_side', (1, -0.2, 0.0))):
        dv = rot(Vector(d)).normalized(); c0 = neck + Vector((0, 0, 0.02)); co.location = c0 + dv * 1.5
        co.rotation_euler = (c0 - co.location).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out, f'{who}_{pose}_{name}.png'); bpy.ops.render.render(write_still=True)
    for side in ('Left', 'Right'):
        hpos = bone_world(rig, f'{side}Hand', True)
        dv = rot(Vector((0.4 if side == 'Left' else -0.4, -1, 0.3))).normalized(); co.location = hpos + dv * 0.7
        co.rotation_euler = (hpos - co.location).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out, f'{who}_{pose}_hand{side[0]}.png'); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(co)


results = []
for pose in poses:
    studio()
    r = P.load(who, 'fig'); T = P.add_ik(r); P.place(r, (0, 0, 0), 0); P.ik_pose(r, T, pose)
    bpy.context.view_layer.update()
    results.append(checks(r, pose))
    h = 0.6 if pose in ('ground', 'drive') else 1.0
    shoot(r, pose, (0, 0, h), 1.8 if h > 0.8 else 1.2)
json.dump(results, open(os.path.join(out, f'{who}_checks.json'), 'w'), ensure_ascii=False, indent=1)
