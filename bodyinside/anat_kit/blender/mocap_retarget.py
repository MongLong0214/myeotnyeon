"""Mixamo FBX -> MPFB 'game_engine' rig, by bone-name mapping (Mixamo short name -> game-engine bone). Direction (swing) retarget in world space: every mapped bone is aimed
from its head toward its child's head along the source bone's direction; axial bones use the delta from the SOURCE REST direction (the rigs bake different head/neck tilts into
rest), limbs the absolute direction (T-pose vs A-pose rests). Hips carry the translation scaled by body height. Both arms follow the clip's LEFT (phone) arm, mirrored
(the clip's right arm hangs behind the body). Hands, fingers and toes are not driven. Pure FK in python (no depsgraph updates)."""
import bpy, math
from mathutils import Vector, Matrix, Quaternion
P = 'mixamorig:'
# (source bone, source child, target bone, target child or None = bone tail, axial?)
TABLE = [('Hips', 'Spine', 'pelvis', 'spine_01', True), ('Spine', 'Spine1', 'spine_01', 'spine_02', True), ('Spine1', 'Spine2', 'spine_02', 'spine_03', True), ('Spine2', 'Neck', 'spine_03', 'neck_01', True),
         ('Neck', 'Head', 'neck_01', 'head', True), ('Head', 'HeadTop_End', 'head', None, True)]
for s, t in (('Left', 'l'), ('Right', 'r')):
    TABLE += [(s + 'Shoulder', s + 'Arm', 'clavicle_' + t, 'upperarm_' + t, False), (s + 'Arm', s + 'ForeArm', 'upperarm_' + t, 'lowerarm_' + t, False), (s + 'ForeArm', s + 'Hand', 'lowerarm_' + t, 'hand_' + t, False),
              (s + 'UpLeg', s + 'Leg', 'thigh_' + t, 'calf_' + t, False), (s + 'Leg', s + 'Foot', 'calf_' + t, 'foot_' + t, False)]
class Rig:
    def __init__(self, obj): self.o = obj
    def pose_world(self, name): return self.o.matrix_world @ self.o.pose.bones[name].matrix
    def rest_world(self, name): return self.o.matrix_world @ self.o.data.bones[name].matrix_local
def order(arm):
    out = []
    def rec(b): out.append(b); [rec(c) for c in b.children]
    [rec(b) for b in arm.data.bones if b.parent is None]; return out
def retarget_frame(src, tgt, scale, hip_rest_src, extra=None, shift=None):
    """extra = {mixamo short: extra forward pitch deg} (about world X, + = forward = -y); shift = {short: world Vector} moves that bone's head (protraction)."""
    extra = extra or {}; shift = shift or {}; aw = tgt.o.matrix_world; awi = aw.inverted(); T = {t[2]: t for t in TABLE}; M = {}; basis = {}
    for b in order(tgt.o):
        n = b.name; rest = tgt.o.data.bones[n].matrix_local
        if b.parent: Mp = M[b.parent.name]; loc = tgt.o.data.bones[b.parent.name].matrix_local.inverted() @ rest
        else: Mp = Matrix.Identity(4); loc = rest
        Mi = Mp @ loc
        if n in T:
            ss, sc_, _, tc, ax = T[n]; mir = ss.startswith('Right')
            if mir: ss = ss.replace('Right', 'Left'); sc_ = sc_.replace('Right', 'Left')
            d = (src.pose_world(P + sc_).translation - src.pose_world(P + ss).translation).normalized()
            if mir: d = Vector((-d.x, d.y, d.z))
            th = tgt.rest_world(n); r = ((tgt.rest_world(tc).translation if tc else (aw @ tgt.o.data.bones[n].tail_local)) - th.translation).normalized()
            if ax:
                rs = (src.rest_world(P + T[n][1]).translation - src.rest_world(P + T[n][0]).translation).normalized(); d = rs.rotation_difference((src.pose_world(P + T[n][1]).translation - src.pose_world(P + T[n][0]).translation).normalized()) @ r
            short = T[n][0]
            if short in extra: d = Matrix.Rotation(math.radians(extra[short]), 3, 'X') @ d
            Rw = r.rotation_difference(d).to_matrix().to_4x4() @ th.to_3x3().to_4x4()
            R = (awi.to_3x3().to_4x4() @ Rw).to_3x3().to_4x4()
            M_arm = Matrix.Translation(Mi.translation + awi.to_3x3() @ shift.get(short, Vector((0, 0, 0)))) @ R
            if not b.parent:
                dh = (src.pose_world(P + 'Hips').translation - hip_rest_src) * scale; M_arm.translation = rest.translation + awi.to_3x3() @ dh
        else: M_arm = Mi
        M[n] = M_arm; basis[n] = loc.inverted() @ Mp.inverted() @ M_arm
    return basis
