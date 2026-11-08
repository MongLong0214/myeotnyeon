"""Faceless clothed CC0 figures (MPFB2 + MakeHuman CC0 clothes) and a small pose library.

Rig: MPFB 'cmu_mb'. Figure faces -Y in its own space. Measured axis conventions
(probe_axes.py): arm Z- lowers the left arm (Z+ for right), arm X+ raises forward,
forearm X+ bends the elbow, up-leg X- flexes the hip forward, leg X+ bends the knee,
spine X+ leans forward.
"""
import bpy, math, pathlib

CHARS = pathlib.Path('production/assets/humans/ep001')

POSES = {
    'stand': {'LeftArm': (0, 0, -62), 'RightArm': (0, 0, 62), 'LeftForeArm': (8, 0, 0), 'RightForeArm': (8, 0, 0),
              'LeftUpLeg': (0, 0, 0), 'RightUpLeg': (0, 0, 0), 'LeftLeg': (0, 0, 0), 'RightLeg': (0, 0, 0),
              'Spine': (0, 0, 0), 'Spine1': (0, 0, 0), 'Neck': (0, 0, 0), 'Head': (0, 0, 0),
              'LeftHand': (0, 0, 0), 'RightHand': (0, 0, 0)},
    # one hand pushed out palm-forward at chest height ("stop")
    'stop': {'RightArm': (72, 0, 22), 'RightForeArm': (28, 0, 0), 'RightHand': (-55, 0, 0),
             'LeftArm': (0, 0, -60), 'LeftForeArm': (10, 0, 0), 'Spine': (-3, 0, 0)},
    'stop_both': {'RightArm': (70, 0, 24), 'RightForeArm': (26, 0, 0), 'RightHand': (-55, 0, 0),
                  'LeftArm': (70, 0, -24), 'LeftForeArm': (26, 0, 0), 'LeftHand': (-55, 0, 0), 'Spine': (-4, 0, 0)},
    'lean_back': {'Spine': (-12, 0, 0), 'Spine1': (-6, 0, 0), 'RightArm': (55, 0, 30), 'RightForeArm': (20, 0, 0),
                  'LeftArm': (40, 0, -35), 'LeftForeArm': (20, 0, 0), 'LeftUpLeg': (12, 0, 0), 'LeftLeg': (8, 0, 0)},
    # seated on the ground, leaning back on both hands (non-graphic end state)
    'ground': {'LeftUpLeg': (-82, 0, -6), 'RightUpLeg': (-78, 0, 6), 'LeftLeg': (22, 0, 0), 'RightLeg': (35, 0, 0),
               'Spine': (-18, 0, 0), 'Spine1': (-6, 0, 0), 'LeftArm': (-35, 0, -55), 'RightArm': (-35, 0, 55),
               'LeftForeArm': (0, 0, 0), 'RightForeArm': (0, 0, 0), 'Head': (8, 0, 0)},
    # driver: thighs forward, knees down, hands toward a wheel
    'drive': {'LeftUpLeg': (-88, 0, -4), 'RightUpLeg': (-88, 0, 4), 'LeftLeg': (80, 0, 0), 'RightLeg': (80, 0, 0),
              'LeftArm': (48, 0, -38), 'RightArm': (48, 0, 38), 'LeftForeArm': (35, 0, 0), 'RightForeArm': (35, 0, 0),
              'Spine': (-6, 0, 0)},
}
HIP_DROP = {'ground': -0.86, 'drive': -0.48}   # Hips bone translation (rest-relative, metres, along rig Z)


def load(kind, name):
    """Append char_A / char_B (rig + meshes). Returns the rig object."""
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


def pose(rig, name, frame=None, blend_from=None, t=1.0):
    """Apply a named pose (merged over 'stand'); keyframe if frame given."""
    target = dict(POSES['stand'])
    target.update(POSES[name])
    for b, (x, y, z) in target.items():
        pb = rig.pose.bones.get(b)
        if pb is None:
            continue
        pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
        if frame is not None:
            pb.keyframe_insert('rotation_euler', frame=frame)
    hips = rig.pose.bones['Hips']
    drop = HIP_DROP.get(name, 0.0)
    hips.location = (0, 0, 0)
    # Hips bone points up its own Y axis in cmu_mb; translate in armature space via matrix
    import mathutils
    rest = hips.bone.matrix_local.to_3x3()
    hips.location = rest.inverted() @ mathutils.Vector((0, 0, drop))
    if frame is not None:
        hips.keyframe_insert('location', frame=frame)


def place(rig, loc, yaw_deg, frame=None):
    """Figure faces -Y locally; yaw rotates around Z."""
    rig.location = loc
    rig.rotation_euler = (0, 0, math.radians(yaw_deg))
    if frame is not None:
        rig.keyframe_insert('location', frame=frame)
        rig.keyframe_insert('rotation_euler', frame=frame)


# ---------------------------------------------------------------- IK rig layer
IK_BONES = {'L': ('LeftForeArm', 'LeftLeg', 'LeftHand', 'LeftFoot'), 'R': ('RightForeArm', 'RightLeg', 'RightHand', 'RightFoot')}


def _empty(name, parent, loc):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.05
    e.parent = parent
    e.location = loc
    return e


def add_ik(rig, arm_pole=-90.0, leg_pole=-90.0):
    """Two-bone IK on arms and legs, targets/poles parented to the rig object (rig space, front = -Y)."""
    T = {}
    pb = rig.pose.bones
    for s, (fore, leg, hand, foot) in IK_BONES.items():
        sx = 1 if s == 'L' else -1
        T[f'hand{s}'] = _empty(f'{rig.name}_ikhand{s}', rig, (0.22 * sx, -0.02, 0.86))
        T[f'elbow{s}'] = _empty(f'{rig.name}_pelbow{s}', rig, (0.3 * sx, 0.45, 1.05))
        T[f'foot{s}'] = _empty(f'{rig.name}_ikfoot{s}', rig, (0.11 * sx, -0.03, 0.09))
        T[f'knee{s}'] = _empty(f'{rig.name}_pknee{s}', rig, (0.12 * sx, -0.7, 0.5))
        c = pb[fore].constraints.new('IK'); c.target = T[f'hand{s}']; c.pole_target = T[f'elbow{s}']; c.pole_angle = math.radians(arm_pole); c.chain_count = 2
        c = pb[leg].constraints.new('IK'); c.target = T[f'foot{s}']; c.pole_target = T[f'knee{s}']; c.pole_angle = math.radians(leg_pole); c.chain_count = 2
    rig['ik'] = True
    return T


# target layouts in rig space (metres; front = -Y). hips = Hips bone drop along Z.
IKP = {
    'stand': dict(handL=(0.21, 0.0, 0.84), handR=(-0.21, 0.0, 0.84), footL=(0.1, -0.02, 0.09), footR=(-0.1, -0.02, 0.09),
                  elbowL=(0.3, 0.5, 1.0), elbowR=(-0.3, 0.5, 1.0), kneeL=(0.12, -0.7, 0.5), kneeR=(-0.12, -0.7, 0.5), hips=0.0, spine=0),
    'stop': dict(handL=(0.21, 0.0, 0.84), handR=(-0.06, -0.46, 1.36), elbowR=(-0.6, 0.05, 1.05),
                 footL=(0.1, -0.05, 0.09), footR=(-0.1, 0.06, 0.09), hips=0.0, spine=-3, palm='R'),
    'stop_both': dict(handL=(0.14, -0.5, 1.3), handR=(-0.14, -0.5, 1.3), elbowL=(0.55, 0.0, 1.1), elbowR=(-0.55, 0.0, 1.1), hips=0.0, spine=-4, palm='LR'),
    'step_back': dict(handL=(0.16, -0.2, 1.18), handR=(-0.14, -0.24, 1.22), elbowL=(0.45, 0.1, 0.95), elbowR=(-0.45, 0.1, 0.95),
                      footL=(0.12, 0.32, 0.09), footR=(-0.1, -0.08, 0.09), hips=-0.03, spine=-10),
    'ground': dict(handL=(0.3, 0.42, 0.06 + 0.0), handR=(-0.3, 0.42, 0.06), elbowL=(0.45, 0.6, 0.4), elbowR=(-0.45, 0.6, 0.4),
                   footL=(0.16, -0.85, 0.08), footR=(-0.14, -0.7, 0.14), kneeL=(0.2, -0.6, 1.0), kneeR=(-0.2, -0.5, 1.1), hips=-0.83, spine=-22),
    'drive': dict(handL=(0.2, -0.48, 1.05 - 0.42), handR=(-0.2, -0.48, 1.05 - 0.42), elbowL=(0.45, 0.1, 0.5), elbowR=(-0.45, 0.1, 0.5),
                  footL=(0.12, -0.78, 0.1 - 0.0), footR=(-0.12, -0.78, 0.1), kneeL=(0.15, -0.8, 1.0), kneeR=(-0.15, -0.8, 1.0), hips=-0.42, spine=-8),
}


def ik_pose(rig, T, name, frame=None):
    p = dict(IKP['stand']); p.update(IKP[name])
    for k, v in p.items():
        if k in T:
            # driver pose is defined relative to a lowered pelvis: shift z targets by nothing (already absolute)
            T[k].location = v
            if frame is not None:
                T[k].keyframe_insert('location', frame=frame)
    pb = rig.pose.bones
    import mathutils
    hips = pb['Hips']
    rest = hips.bone.matrix_local.to_3x3()
    hips.location = rest.inverted() @ mathutils.Vector((0, 0, p['hips']))
    pb['Spine'].rotation_euler = (math.radians(p['spine']), 0, 0)
    for s, hand in (('L', 'LeftHand'), ('R', 'RightHand')):
        pb[hand].rotation_euler = (math.radians(-70), 0, 0) if s in p.get('palm', '') else (0, 0, 0)
    if frame is not None:
        hips.keyframe_insert('location', frame=frame)
        pb['Spine'].keyframe_insert('rotation_euler', frame=frame)
        pb['LeftHand'].keyframe_insert('rotation_euler', frame=frame)
        pb['RightHand'].keyframe_insert('rotation_euler', frame=frame)
