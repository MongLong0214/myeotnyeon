"""Faceless clothed CC0 figures (MPFB2 + MakeHuman CC0 clothes) posed with IK v2.

Rig: MPFB 'cmu_mb', figure faces -Y in rig space. Rest data (char_B): hip joint z 0.918,
knee 0.504, ankle 0.071 → leg 0.851 m, straight at rest. Measured with probe_axes.py /
probe_hand.py; palm orientation chosen by rendering four candidates (probe_palm.py):
right-hand palm normal = bone −X.

Controls
- arms: 2-bone IK to hand targets (rig space) with elbow poles; optional hand orientation lock
- legs: 2-bone IK to ankle targets (rig space, or world space for planted steps) with knee poles;
  feet kept level by a Copy Rotation lock (influence 0 when the leg is extended on the ground)
- hips: vertical drop (armature space), spine/neck lean
- idle: slow breathing + weight shift so a standing figure never freezes like a statue
"""
import bpy, math, pathlib
from mathutils import Vector, Matrix

CHARS = pathlib.Path('production/assets/humans/ep001')


def load(kind, name):
    blend = CHARS / f'char_{kind}.blend'
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.objects = list(src.objects)
    rig = None
    for o in dst.objects:
        if o is None:
            continue
        bpy.context.scene.collection.objects.link(o)
        if o.type == 'ARMATURE':
            rig = o
    rig.name = name
    for o in dst.objects:
        if o is not None and o.type == 'MESH':
            o.name = f'{name}_{o.name}'
    for b in rig.pose.bones:
        b.rotation_mode = 'XYZ'
    return rig


def _empty(name, parent, loc, rot=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.05
    if parent is not None:
        e.parent = parent
        e.matrix_parent_inverse.identity()
    e.location = loc
    e.rotation_mode = 'QUATERNION'
    if rot is not None:
        e.rotation_quaternion = rot
    return e


def _palm_quat(side, palm_dir, finger_dir):
    """Rig-space orientation for a hand bone: bone +Y → finger_dir, palm normal → palm_dir.
    Right hand palm normal is bone −X; left hand mirrored (bone +X)."""
    y = Vector(finger_dir).normalized(); n = Vector(palm_dir).normalized()
    xa = (-n) if side == 'R' else n
    xa = (xa - y * xa.dot(y)).normalized()
    za = xa.cross(y)
    return Matrix((xa, y, za)).transposed().to_quaternion()


def add_ik(rig, world_feet=False):
    """Returns dict of control empties. Feet targets sit at the ankle; foot rotation locked level."""
    T = {}
    pb = rig.pose.bones
    ank_z = rig.data.bones['LeftFoot'].head_local.z
    for s, side in (('L', 'Left'), ('R', 'Right')):
        sx = 1 if s == 'L' else -1
        T[f'hand{s}'] = _empty(f'{rig.name}_ikhand{s}', rig, (0.2 * sx, 0.0, 0.86))
        T[f'elbow{s}'] = _empty(f'{rig.name}_pelbow{s}', rig, (0.32 * sx, 0.5, 1.0))
        T[f'handori{s}'] = _empty(f'{rig.name}_handori{s}', rig, (0, 0, 0))
        foot_rest_q = rig.data.bones[f'{side}Foot'].matrix_local.to_3x3().to_quaternion()
        if world_feet:
            T[f'foot{s}'] = _empty(f'{rig.name}_ikfoot{s}', None, rig.matrix_world @ Vector((0.12 * sx, -0.01, ank_z)),
                                   rig.matrix_world.to_quaternion() @ foot_rest_q)
        else:
            T[f'foot{s}'] = _empty(f'{rig.name}_ikfoot{s}', rig, (0.12 * sx, -0.01, ank_z), foot_rest_q)
        T[f'knee{s}'] = _empty(f'{rig.name}_pknee{s}', rig, (0.14 * sx, -0.8, 0.5))
        c = pb[f'{side}ForeArm'].constraints.new('IK'); c.target = T[f'hand{s}']; c.pole_target = T[f'elbow{s}']
        c.pole_angle = math.radians(-90); c.chain_count = 2
        c = pb[f'{side}Leg'].constraints.new('IK'); c.target = T[f'foot{s}']; c.pole_target = T[f'knee{s}']
        c.pole_angle = math.radians(-90); c.chain_count = 2
        c = pb[f'{side}Foot'].constraints.new('COPY_ROTATION'); c.name = 'foot_level'; c.target = T[f'foot{s}']
        c = pb[f'{side}Hand'].constraints.new('COPY_ROTATION'); c.name = 'hand_ori'; c.target = T[f'handori{s}']; c.influence = 0.0
    T['ankle_z'] = ank_z
    T['scale'] = rig.data.bones['LeftUpLeg'].head_local.z / 0.918
    return T


# Rig-space layouts (front = −Y). z=None → on the ground (ankle height for feet, palm height for hands).
# hips: Hips drop (m). spine/neck/head: lean deg (+ forward). palm: side → (palm_dir, finger_dir).
IKP = {
    'stand': dict(handL=(0.2, 0.01, 0.86), handR=(-0.2, 0.01, 0.86), elbowL=(0.32, 0.5, 1.0), elbowR=(-0.32, 0.5, 1.0),
                  footL=(0.12, -0.01, None), footR=(-0.12, 0.0, None), kneeL=(0.14, -0.8, 0.5), kneeR=(-0.14, -0.8, 0.5),
                  hips=0.0, spine=1, neck=0, head=-2, palm={}, footlock=(1, 1)),
    'stop': dict(handL=(0.19, -0.02, 0.86), handR=(-0.15, -0.5, 1.2), elbowR=(-0.55, 0.15, 1.0),
                 footL=(0.12, 0.06, None), footR=(-0.12, -0.12, None), hips=-0.004, spine=4, neck=2, head=0,
                 palm={'R': ((0, -1, 0.25), (0.08, -0.1, 1))}, footlock=(1, 1)),
    'stop_both': dict(handL=(0.15, -0.48, 1.26), handR=(-0.15, -0.48, 1.26), elbowL=(0.55, 0.15, 1.0), elbowR=(-0.55, 0.15, 1.0),
                      footL=(0.12, 0.06, None), footR=(-0.12, -0.12, None), hips=-0.02, spine=4, neck=2, head=0,
                      palm={'L': ((0, -1, 0.25), (-0.08, -0.1, 1)), 'R': ((0, -1, 0.25), (0.08, -0.1, 1))}, footlock=(1, 1)),
    'guard': dict(handL=(0.17, -0.34, 1.16), handR=(-0.16, -0.36, 1.18), elbowL=(0.5, 0.1, 0.85), elbowR=(-0.5, 0.1, 0.85),
                  footL=(0.13, 0.12, None), footR=(-0.12, -0.1, None), hips=-0.008, spine=-6, neck=-3, head=4,
                  palm={'L': ((0, -1, 0.1), (-0.15, -0.2, 1)), 'R': ((0, -1, 0.1), (0.15, -0.2, 1))}, footlock=(1, 1)),
    'ground': dict(handL=('thighL',), handR=('kneeR',), elbowL=(0.5, 0.3, 0.6), elbowR=(-0.5, 0.2, 0.7),
                   footL=(0.16, -0.86, 0.1), footR=(-0.1, -0.46, None), kneeL=(0.2, -0.6, 1.2), kneeR=(-0.14, -0.4, 1.3),
                   hips=-0.79, spine=-6, neck=6, head=4, palm={}, footlock=(0, 1)),
    'drive': dict(handL=(0.19, -0.42, 0.93), handR=(-0.19, -0.42, 0.93), elbowL=(0.4, 0.0, 0.5), elbowR=(-0.4, 0.0, 0.5),
                  footL=(0.15, -0.66, 0.13), footR=(-0.15, -0.66, 0.13), kneeL=(0.16, -0.7, 1.2), kneeR=(-0.16, -0.7, 1.2),
                  hips=-0.43, spine=-8, neck=6, head=4, palm={}, footlock=(0.5, 0.5)),
}


def ik_pose(rig, T, name, frame=None):
    p = dict(IKP['stand']); p.update(IKP[name])
    sc = T['scale']
    pb = rig.pose.bones
    hips = pb['Hips']
    hips.location = hips.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, p['hips'] * sc))
    deferred = []
    for k in ('elbowL', 'elbowR', 'footL', 'footR', 'kneeL', 'kneeR', 'handL', 'handR'):
        v = list(p[k])
        if isinstance(v[0], str):          # attach to a body landmark after the legs are solved
            deferred.append((k, v[0])); continue
        v = [v[0] * sc, v[1] * sc, (T['ankle_z'] if k.startswith('foot') else 0.035) if v[2] is None else v[2] * sc]
        e = T[k]
        e.location = (rig.matrix_world @ Vector(v)) if e.parent is None else Vector(v)
        if frame is not None:
            e.keyframe_insert('location', frame=frame)
    if deferred:
        bpy.context.view_layer.update()
        def rs(bone, tail=False):
            b_ = pb[bone]; return (b_.tail if tail else b_.head).copy()
        marks = {'kneeR': rs('RightLeg') + Vector((0.0, -0.02, 0.07)), 'kneeL': rs('LeftLeg') + Vector((0.0, -0.02, 0.07)),
                 'thighL': rs('LeftUpLeg').lerp(rs('LeftLeg'), 0.62) + Vector((0.02, 0.0, 0.08)),
                 'thighR': rs('RightUpLeg').lerp(rs('RightLeg'), 0.62) + Vector((-0.02, 0.0, 0.08))}
        for k, m in deferred:
            e = T[k]; e.location = marks[m]
            if frame is not None:
                e.keyframe_insert('location', frame=frame)
    pb['Spine'].rotation_euler = (math.radians(p['spine'] * 0.6), 0, 0)
    pb['Spine1'].rotation_euler = (math.radians(p['spine'] * 0.4), 0, 0)
    pb['Neck'].rotation_euler = (math.radians(p['neck']), 0, 0)
    pb['Head'].rotation_euler = (math.radians(p['head']), 0, 0)
    for s, side in (('L', 'Left'), ('R', 'Right')):
        con = pb[f'{side}Hand'].constraints['hand_ori']
        if s in p['palm']:
            pd, fd = p['palm'][s]
            T[f'handori{s}'].rotation_quaternion = _palm_quat(s, pd, fd)
            con.influence = 1.0
        else:
            con.influence = 0.0
        fl = pb[f'{side}Foot'].constraints['foot_level']
        fl.influence = p['footlock'][0 if s == 'L' else 1]
        if frame is not None:
            T[f'handori{s}'].keyframe_insert('rotation_quaternion', frame=frame)
            con.keyframe_insert('influence', frame=frame)
            fl.keyframe_insert('influence', frame=frame)
    if frame is not None:
        hips.keyframe_insert('location', frame=frame)
        for b in ('Spine', 'Spine1', 'Neck', 'Head'):
            pb[b].keyframe_insert('rotation_euler', frame=frame)


def idle(rig, f0, f1, amp=1.0, seed=0.0):
    """Breathing + slow weight shift + small head drift layered on the current pose."""
    pb = rig.pose.bones
    base = {b: tuple(pb[b].rotation_euler) for b in ('Spine1', 'Neck', 'Head')}
    hb = pb['Hips'].location.copy()
    for f in range(f0, f1 + 1, 6):
        t = f / 30.0
        br = math.sin(2 * math.pi * 0.23 * t + seed) * 0.9 * amp
        sway = math.sin(2 * math.pi * 0.07 * t + seed * 1.7) * amp
        pb['Spine1'].rotation_euler = (base['Spine1'][0] + math.radians(br), base['Spine1'][1], base['Spine1'][2] + math.radians(sway * 0.8))
        pb['Neck'].rotation_euler = (base['Neck'][0] - math.radians(br * 0.6), base['Neck'][1], base['Neck'][2])
        pb['Head'].rotation_euler = (base['Head'][0], base['Head'][1] + math.radians(math.sin(2 * math.pi * 0.05 * t + seed * 2.3) * 2.0 * amp), base['Head'][2])
        pb['Hips'].location = hb + Vector((0.006 * sway, 0, 0))
        for b in ('Spine1', 'Neck', 'Head'):
            pb[b].keyframe_insert('rotation_euler', frame=f)
        pb['Hips'].keyframe_insert('location', frame=f)


GROUND_OFFSET = 0.02     # MPFB shoe soles sit 2 cm below the rig origin at rest


def place(rig, loc, yaw_deg, frame=None):
    rig.location = (loc[0], loc[1], loc[2] + GROUND_OFFSET)
    rig.rotation_euler = (0, 0, math.radians(yaw_deg))
    if frame is not None:
        rig.keyframe_insert('location', frame=frame)
        rig.keyframe_insert('rotation_euler', frame=frame)
