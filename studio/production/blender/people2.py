"""people2 — ready-made faceless mannequins (Quaternius UAL1, CC0) with natural motion, baked.

API (frames at 30 fps; every motion keys f0..f1 and crossfades from whatever precedes it):
  load(name, tone=TONE_A|TONE_B)            → rig (armature) + mesh '<name>_body', plaster/joint mats
  place(rig, (x, y, z), yaw_deg, frame=None) put the root on the ground; with frame= it is a cut
  idle(rig, f0, f1)                          natural standing, breathing / weight shifts, relaxed hands
  stop(rig, f0, f1, hands='both'|'right')    palms-out halt toward the front, held
  walk_to(rig, f0, f1, start, end, end_yaw=None)   planted-foot walk (start=None: from where it stands)
  step_back(rig, f0, f1, dist, hands='fend') 2–3 backward steps, hands low toward the bumper
  sit_ground(rig, f0, f1)                    seated on the asphalt after a fall, dazed
  get_up(rig, f0, f1)                        from that seated pose to standing (same take, seamless)
  drive(rig, f0, f1, car=None)               seated driver, fists on the wheel (accord_2019 cabin)
  jog_in(rig, f0, f1, start, end)            a few hurried steps toward the car (ghost)
  driver_seat(car, rig)                      the accord_2019 asset has no seats: adds simple ones
  mocap(rig, f0, f1, take, t0, ...)          any CMU take window (generic)

How: every call appends a segment to the rig's timeline and re-bakes the whole timeline into one
action (per-frame keys) plus object keys for root travel, so one contact solver sees transitions:
  segments → crossfaded pose (local quats, smoothstep) → floor calibration → foot locking with
  heading lock + hinge-correct leg IK → anti-penetration → palm contacts / grips (arm IK) → keys.

Conventions (same as people.py): the figure faces −Y in rig space; yaw_deg is the object's Z
rotation (yaw −90 faces −X, +90 faces +X); the object origin is on the ground plane.

Sources (licence evidence in assets/humans_ready/*/):
  mannequin, Walk/Driving loops, finger axes   Quaternius Universal Animation Library 1 — CC0
  idle                                         100STYLE Neutral_ID (Mason et al.) — CC BY 4.0 (credit)
  step_back                                    CMU mocap 136_25 (walk backwards) — free for all uses
  sit_ground / get_up                          CMU mocap 111_06 (4.0–5.6 s / → 11.0 s)
  stop / fend arm poses                        designed in-module (IK) over the idle
"""
import bpy, math, pathlib
import numpy as np
from mathutils import Vector, Matrix

HR = pathlib.Path('production/assets/humans_ready')
UAL_GLB = HR / 'quaternius_ual1' / 'AnimationLibrary_Godot_Standard.glb'
CMU = HR / 'cmu_selected'
FPS = 30

TONE_A = (0.60, 0.615, 0.63)     # slightly cooler grey (driver A)
TONE_B = (0.65, 0.635, 0.615)    # slightly warmer grey (B)

# ===================================================================== numpy rotation helpers


def q2m(q):
    q = np.asarray(q, float)
    w, x, y, z = np.moveaxis(q, -1, 0)
    n = w * w + x * x + y * y + z * z
    s = np.where(n > 0, 2.0 / np.maximum(n, 1e-12), 0.0)
    m = np.empty(q.shape[:-1] + (3, 3))
    m[..., 0, 0] = 1 - s * (y * y + z * z); m[..., 0, 1] = s * (x * y - w * z); m[..., 0, 2] = s * (x * z + w * y)
    m[..., 1, 0] = s * (x * y + w * z); m[..., 1, 1] = 1 - s * (x * x + z * z); m[..., 1, 2] = s * (y * z - w * x)
    m[..., 2, 0] = s * (x * z - w * y); m[..., 2, 1] = s * (y * z + w * x); m[..., 2, 2] = 1 - s * (x * x + y * y)
    return m


def m2q(m):
    m = np.asarray(m, float)
    sh = m.shape[:-2]
    m = m.reshape(-1, 3, 3)
    q = np.empty((len(m), 4))
    tr = m[:, 0, 0] + m[:, 1, 1] + m[:, 2, 2]
    c0 = tr > 0
    c1 = (~c0) & (m[:, 0, 0] >= m[:, 1, 1]) & (m[:, 0, 0] >= m[:, 2, 2])
    c2 = (~c0) & (~c1) & (m[:, 1, 1] >= m[:, 2, 2])
    c3 = ~(c0 | c1 | c2)
    if c0.any():
        a = m[c0]; s = np.sqrt(tr[c0] + 1.0) * 2
        q[c0] = np.stack([0.25 * s, (a[:, 2, 1] - a[:, 1, 2]) / s, (a[:, 0, 2] - a[:, 2, 0]) / s, (a[:, 1, 0] - a[:, 0, 1]) / s], -1)
    if c1.any():
        a = m[c1]; s = np.sqrt(1.0 + a[:, 0, 0] - a[:, 1, 1] - a[:, 2, 2]) * 2
        q[c1] = np.stack([(a[:, 2, 1] - a[:, 1, 2]) / s, 0.25 * s, (a[:, 0, 1] + a[:, 1, 0]) / s, (a[:, 0, 2] + a[:, 2, 0]) / s], -1)
    if c2.any():
        a = m[c2]; s = np.sqrt(1.0 + a[:, 1, 1] - a[:, 0, 0] - a[:, 2, 2]) * 2
        q[c2] = np.stack([(a[:, 0, 2] - a[:, 2, 0]) / s, (a[:, 0, 1] + a[:, 1, 0]) / s, 0.25 * s, (a[:, 1, 2] + a[:, 2, 1]) / s], -1)
    if c3.any():
        a = m[c3]; s = np.sqrt(1.0 + a[:, 2, 2] - a[:, 0, 0] - a[:, 1, 1]) * 2
        q[c3] = np.stack([(a[:, 1, 0] - a[:, 0, 1]) / s, (a[:, 0, 2] + a[:, 2, 0]) / s, (a[:, 1, 2] + a[:, 2, 1]) / s, 0.25 * s], -1)
    q /= np.linalg.norm(q, axis=-1, keepdims=True)
    return q.reshape(sh + (4,))


def qnorm(q):
    return q / np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-12)


def qslerp(a, b, t):
    """Slerp (...,4) with shortest-path sign fix; t broadcastable to (...)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    t = np.asarray(t, float)
    sh = np.broadcast_shapes(a.shape[:-1], b.shape[:-1], t.shape)
    a = np.broadcast_to(a, sh + (4,)); b = np.broadcast_to(b, sh + (4,)); t = np.broadcast_to(t, sh)
    d = (a * b).sum(-1)
    b = np.where((d < 0)[..., None], -b, b)
    d = np.abs(d)
    t = np.broadcast_to(t, d.shape)
    th = np.arccos(np.clip(d, -1, 1))
    st = np.sin(th)
    small = st < 1e-5
    w0 = np.where(small, 1 - t, np.sin((1 - t) * th) / np.where(small, 1, st))
    w1 = np.where(small, t, np.sin(t * th) / np.where(small, 1, st))
    return qnorm(w0[..., None] * a + w1[..., None] * b)


def qcont(q):
    """Hemisphere continuity along axis 0."""
    q = q.copy()
    for i in range(1, len(q)):
        d = (q[i] * q[i - 1]).sum(-1)
        q[i] = np.where((d < 0)[..., None], -q[i], q[i])
    return q


def rotz(a):
    a = np.asarray(a, float)
    c, s = np.cos(a), np.sin(a)
    m = np.zeros(a.shape + (3, 3))
    m[..., 0, 0] = c; m[..., 0, 1] = -s; m[..., 1, 0] = s; m[..., 1, 1] = c; m[..., 2, 2] = 1
    return m


def rot_between(a, b):
    """Minimal rotation matrices taking unit vectors a → b (...,3)."""
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    v = np.cross(a, b)
    c = (a * b).sum(-1)
    k = 1.0 / np.maximum(1.0 + c, 1e-8)
    vx = np.zeros(a.shape[:-1] + (3, 3))
    vx[..., 0, 1] = -v[..., 2]; vx[..., 0, 2] = v[..., 1]; vx[..., 1, 0] = v[..., 2]
    vx[..., 1, 2] = -v[..., 0]; vx[..., 2, 0] = -v[..., 1]; vx[..., 2, 1] = v[..., 0]
    eye = np.broadcast_to(np.eye(3), vx.shape)
    return eye + vx + (vx @ vx) * k[..., None, None]


def axis_angle(axis, ang):
    axis = axis / np.linalg.norm(axis, axis=-1, keepdims=True)
    h = np.asarray(ang)[..., None] * 0.5
    q = np.concatenate([np.cos(h), axis * np.sin(h)], -1)
    return q2m(q)


def gsmooth(x, sigma, mode='edge'):
    """Gaussian smoothing along axis 0 (sigma in samples)."""
    x = np.asarray(x, float)
    if sigma <= 0 or len(x) < 2:
        return x.copy()
    r = max(1, int(3 * sigma + 0.5))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    pad = np.pad(x, [(r, r)] + [(0, 0)] * (x.ndim - 1), mode=mode)
    out = np.zeros_like(x)
    for i in range(2 * r + 1):
        out += k[i] * pad[i:i + len(x)]
    return out


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def unwrap_yaw(y):
    return np.unwrap(np.asarray(y, float))


# ===================================================================== BVH


class Bvh:
    def __init__(self, path):
        toks = open(path).read().split()
        i = 0
        names, parents, offsets, chans, is_end = [], [], [], [], []
        stack = []
        while toks[i] != 'MOTION':
            t = toks[i]
            if t in ('ROOT', 'JOINT', 'End'):
                nm = toks[i + 1] if t != 'End' else names[stack[-1]] + '_end'
                names.append(nm); parents.append(stack[-1] if stack else -1)
                offsets.append([0, 0, 0]); chans.append([]); is_end.append(t == 'End')
                i += 2
            elif t == '{':
                stack.append(len(names) - 1); i += 1
            elif t == '}':
                stack.pop(); i += 1
            elif t == 'OFFSET':
                offsets[stack[-1]] = [float(v) for v in toks[i + 1:i + 4]]; i += 4
            elif t == 'CHANNELS':
                n = int(toks[i + 1]); chans[stack[-1]] = toks[i + 2:i + 2 + n]; i += 2 + n
            else:
                i += 1
        i += 1
        assert toks[i] == 'Frames:'
        nf = int(toks[i + 1]); self.ft = float(toks[i + 4]); i += 5
        nch = sum(len(c) for c in chans)
        data = np.array(toks[i:i + nf * nch], float).reshape(nf, nch)
        self.names, self.parents, self.offsets, self.chans = names, np.array(parents), np.array(offsets, float), chans
        self.idx = {n: k for k, n in enumerate(names)}
        # unwrap rotation channels so fractional-frame interpolation never crosses ±180
        k = 0
        for c in chans:
            for ch in c:
                if ch.endswith('rotation'):
                    data[:, k] = np.degrees(np.unwrap(np.radians(data[:, k])))
                k += 1
        self.data = data
        self.nf = nf

    def sample(self, frames):
        """Channel values at fractional frame indices (linear)."""
        f = np.clip(np.asarray(frames, float), 0, self.nf - 1)
        i0 = np.floor(f).astype(int); i1 = np.minimum(i0 + 1, self.nf - 1); a = (f - i0)[:, None]
        return self.data[i0] * (1 - a) + self.data[i1] * a

    def fk(self, frames):
        """World rotations (F,J,3,3) and positions (F,J,3) at fractional frames (Y-up units).
        Interpolates in rotation space between neighbouring source frames: interpolating the raw
        Euler channels breaks where a joint passes near gimbal lock (180° flips)."""
        f = np.clip(np.asarray(frames, float), 0, self.nf - 1)
        i0 = np.floor(f); a = f - i0
        if np.all(a < 1e-9):
            return self._fk(i0)
        R0, P0 = self._fk(i0); R1, P1 = self._fk(np.minimum(i0 + 1, self.nf - 1))
        q = qslerp(m2q(R0), m2q(R1), a[:, None])
        return q2m(q), P0 * (1 - a)[:, None, None] + P1 * a[:, None, None]

    def _fk(self, frames):
        d = self.sample(frames)
        F = len(d); J = len(self.names)
        R = np.zeros((F, J, 3, 3)); P = np.zeros((F, J, 3))
        k = 0
        ax = {'X': 0, 'Y': 1, 'Z': 2}
        for j in range(J):
            Rl = np.broadcast_to(np.eye(3), (F, 3, 3)).copy()
            t = np.broadcast_to(self.offsets[j], (F, 3)).copy()
            for ch in self.chans[j]:
                v = d[:, k]; k += 1
                if ch.endswith('position'):
                    t[:, ax[ch[0]]] = v
                else:
                    a = np.radians(v); c, s = np.cos(a), np.sin(a)
                    m = np.zeros((F, 3, 3))
                    if ch[0] == 'X':
                        m[:, 0, 0] = 1; m[:, 1, 1] = c; m[:, 1, 2] = -s; m[:, 2, 1] = s; m[:, 2, 2] = c
                    elif ch[0] == 'Y':
                        m[:, 1, 1] = 1; m[:, 0, 0] = c; m[:, 0, 2] = s; m[:, 2, 0] = -s; m[:, 2, 2] = c
                    else:
                        m[:, 2, 2] = 1; m[:, 0, 0] = c; m[:, 0, 1] = -s; m[:, 1, 0] = s; m[:, 1, 1] = c
                    Rl = Rl @ m
            p = self.parents[j]
            if p < 0:
                R[:, j] = Rl; P[:, j] = t
            else:
                R[:, j] = R[:, p] @ Rl
                P[:, j] = P[:, p] + np.einsum('fij,fj->fi', R[:, p], t)
        return R, P


    def fk_rest(self):
        """Zero-rotation rest pose: identity world rotations, offsets accumulated."""
        J = len(self.names)
        R = np.broadcast_to(np.eye(3), (1, J, 3, 3)).copy(); P = np.zeros((1, J, 3))
        for j in range(J):
            p = self.parents[j]
            P[0, j] = (P[0, p] if p >= 0 else 0) + self.offsets[j]
        return R, P


_bvh_cache = {}


def bvh(path):
    path = str(path)
    if path not in _bvh_cache:
        _bvh_cache[path] = Bvh(path)
    return _bvh_cache[path]


# Y-up → Z-up (Blender importer convention): (x, y, z) → (x, −z, y)
C_YUP = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)

# target bone ← (source joint whose world rotation drives it, direction span from, to).
# CMU puts LowerBack/Neck/Shoulder/FingerBase on their parent's position (zero offsets), so the
# direction span skips to the next joint with length.
CMU_MAP = {
    'DEF-hips': ('Hips', 'Hips', 'Spine'), 'DEF-spine.001': ('LowerBack', 'LowerBack', 'Spine'),
    'DEF-spine.002': ('Spine', 'Spine', 'Spine1'), 'DEF-spine.003': ('Spine1', 'Spine1', 'Neck1'),
    'DEF-neck': ('Neck', 'Neck', 'Head'), 'DEF-head': ('Head', 'Head', 'Head_end'),
    'DEF-shoulder.L': ('LeftShoulder', 'LeftShoulder', 'LeftArm'), 'DEF-upper_arm.L': ('LeftArm', 'LeftArm', 'LeftForeArm'),
    'DEF-forearm.L': ('LeftForeArm', 'LeftForeArm', 'LeftHand'), 'DEF-hand.L': ('LeftHand', 'LeftHand', 'LeftHandIndex1'),
    'DEF-shoulder.R': ('RightShoulder', 'RightShoulder', 'RightArm'), 'DEF-upper_arm.R': ('RightArm', 'RightArm', 'RightForeArm'),
    'DEF-forearm.R': ('RightForeArm', 'RightForeArm', 'RightHand'), 'DEF-hand.R': ('RightHand', 'RightHand', 'RightHandIndex1'),
    'DEF-thigh.L': ('LeftUpLeg', 'LeftUpLeg', 'LeftLeg'), 'DEF-shin.L': ('LeftLeg', 'LeftLeg', 'LeftFoot'),
    'DEF-foot.L': ('LeftFoot', 'LeftFoot', 'LeftToeBase'), 'DEF-toe.L': ('LeftToeBase', 'LeftToeBase', 'LeftToeBase_end'),
    'DEF-thigh.R': ('RightUpLeg', 'RightUpLeg', 'RightLeg'), 'DEF-shin.R': ('RightLeg', 'RightLeg', 'RightFoot'),
    'DEF-foot.R': ('RightFoot', 'RightFoot', 'RightToeBase'), 'DEF-toe.R': ('RightToeBase', 'RightToeBase', 'RightToeBase_end'),
}
S100_MAP = {
    'DEF-hips': ('Hips', 'Hips', 'Chest'), 'DEF-spine.001': ('Chest', 'Chest', 'Chest2'), 'DEF-spine.002': ('Chest2', 'Chest2', 'Chest3'),
    'DEF-spine.003': ('Chest4', 'Chest3', 'Neck'), 'DEF-neck': ('Neck', 'Neck', 'Head'), 'DEF-head': ('Head', 'Head', 'Head_end'),
    'DEF-shoulder.L': ('LeftCollar', 'LeftCollar', 'LeftShoulder'), 'DEF-upper_arm.L': ('LeftShoulder', 'LeftShoulder', 'LeftElbow'),
    'DEF-forearm.L': ('LeftElbow', 'LeftElbow', 'LeftWrist'), 'DEF-hand.L': ('LeftWrist', 'LeftWrist', 'LeftWrist_end'),
    'DEF-shoulder.R': ('RightCollar', 'RightCollar', 'RightShoulder'), 'DEF-upper_arm.R': ('RightShoulder', 'RightShoulder', 'RightElbow'),
    'DEF-forearm.R': ('RightElbow', 'RightElbow', 'RightWrist'), 'DEF-hand.R': ('RightWrist', 'RightWrist', 'RightWrist_end'),
    'DEF-thigh.L': ('LeftHip', 'LeftHip', 'LeftKnee'), 'DEF-shin.L': ('LeftKnee', 'LeftKnee', 'LeftAnkle'),
    'DEF-foot.L': ('LeftAnkle', 'LeftAnkle', 'LeftToe'), 'DEF-toe.L': ('LeftToe', 'LeftToe', 'LeftToe_end'),
    'DEF-thigh.R': ('RightHip', 'RightHip', 'RightKnee'), 'DEF-shin.R': ('RightKnee', 'RightKnee', 'RightAnkle'),
    'DEF-foot.R': ('RightAnkle', 'RightAnkle', 'RightToe'), 'DEF-toe.R': ('RightToe', 'RightToe', 'RightToe_end'),
}
CMU_HIPJ = ('LeftUpLeg', 'RightUpLeg')

# ===================================================================== target skeleton


class Skel:
    def __init__(self, arm, mesh):
        order = []

        def visit(b):
            order.append(b)
            for c in b.children:
                visit(c)
        for b in arm.data.bones:
            if b.parent is None:
                visit(b)
        self.names = [b.name for b in order]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.parent = np.array([self.idx[b.parent.name] if b.parent else -1 for b in order])
        self.restM = np.array([np.array(b.matrix_local) for b in order])
        self.restR = self.restM[:, :3, :3].copy(); self.restT = self.restM[:, :3, 3].copy()
        relM = []
        for i, b in enumerate(order):
            p = self.parent[i]
            relM.append(np.linalg.inv(self.restM[p]) @ self.restM[i] if p >= 0 else self.restM[i])
        relM = np.array(relM)
        self.relR = relM[:, :3, :3].copy(); self.relT = relM[:, :3, 3].copy()
        self.length = np.array([b.length for b in order])
        self.B = len(order)
        self.hips = self.idx['DEF-hips']
        # mesh skinning data (rest positions, per-vertex top-4 weights), for contact geometry
        vg = {g.index: g.name for g in mesh.vertex_groups}
        V = len(mesh.data.vertices)
        self.vrest = np.array([v.co[:] for v in mesh.data.vertices])
        W = np.zeros((V, self.B))
        for v in mesh.data.vertices:
            for g in v.groups:
                n = vg.get(g.group)
                if n in self.idx:
                    W[v.index, self.idx[n]] = g.weight
        W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
        self.W = W
        self.dom = W.argmax(1)
        # hip-joint midpoint offset expressed in the DEF-hips rest frame
        mid = 0.5 * (self.restT[self.idx['DEF-thigh.L']] + self.restT[self.idx['DEF-thigh.R']])
        self.hipmid_local = self.restR[self.hips].T @ (mid - self.restT[self.hips])

    def fk(self, hipsP, Q):
        """hipsP (F,3) armature-space DEF-hips head, Q (F,B,4) local basis quats → R (F,B,3,3), P heads (F,B,3)."""
        F = len(Q)
        L = q2m(Q)
        R = np.empty((F, self.B, 3, 3)); P = np.empty((F, self.B, 3))
        for b in range(self.B):
            p = self.parent[b]
            if p < 0:
                R[:, b] = self.restR[b] @ L[:, b]; P[:, b] = self.restT[b]
            else:
                R[:, b] = R[:, p] @ self.relR[b] @ L[:, b]
                P[:, b] = P[:, p] + np.einsum('fij,j->fi', R[:, p], self.relT[b])
            if b == self.hips:
                P[:, b] = hipsP
        return R, P

    def local(self, R):
        """World (armature-space) rotations (F,B,3,3) → local basis quats (F,B,4)."""
        Q = np.empty(R.shape[:2] + (4,))
        for b in range(self.B):
            p = self.parent[b]
            if p < 0:
                Lm = np.swapaxes(self.restR[b], -1, -2) @ R[:, b]
            else:
                Lm = np.swapaxes(R[:, p] @ self.relR[b], -1, -2) @ R[:, b]
            Q[:, b] = m2q(Lm)
        return qcont(Q)

    def verts(self, R, P, sel):
        """Linear-blend-skinned positions (F,len(sel),3) of rest vertices `sel` given pose R,P."""
        vr = self.vrest[sel]; W = self.W[sel]
        bones = np.nonzero(W.sum(0) > 0)[0]
        out = np.zeros((len(R), len(sel), 3))
        for b in bones:
            w = W[:, b]
            loc = (vr - self.restT[b]) @ self.restR[b]          # rest-local coords
            out += w[None, :, None] * (np.einsum('fij,vj->fvi', R[:, b], loc) + P[:, b][:, None, :])
        return out


# ===================================================================== template / loading
_S = {}          # python-side caches that survive scene resets: skel, ual clips


def _keep_scene_settings():
    s = bpy.context.scene
    return (s.render.fps, s.render.fps_base, s.frame_start, s.frame_end, s.frame_current)


def _restore_scene_settings(v):
    s = bpy.context.scene
    s.render.fps, s.render.fps_base, s.frame_start, s.frame_end = v[:4]
    s.frame_set(v[4])


def _template():
    rig = bpy.data.objects.get('_p2_tpl_rig')
    mesh = bpy.data.objects.get('_p2_tpl_mesh')
    if rig is not None and mesh is not None:
        return rig, mesh
    keep = _keep_scene_settings()
    before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(UAL_GLB))
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == 'ARMATURE')
    mesh = next(o for o in new if o.type == 'MESH' and o.name.startswith('Mannequin'))
    for o in new:
        if o not in (rig, mesh):
            bpy.data.objects.remove(o, do_unlink=True)      # stray 2 m Icosphere
    rig.name = '_p2_tpl_rig'; mesh.name = '_p2_tpl_mesh'
    if 'skel' not in _S:
        _S['skel'] = Skel(rig, mesh)
    if 'ual' not in _S:
        _S['ual'] = _sample_ual(rig, [a for a in bpy.data.actions if a not in acts_before])
    # strip animation and unlink: templates are only copied from, never evaluated
    rig.animation_data_clear()
    for a in [a for a in bpy.data.actions if a not in acts_before]:
        bpy.data.actions.remove(a)
    for o in (rig, mesh):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        o.use_fake_user = True
    _restore_scene_settings(keep)
    return rig, mesh


def skel():
    if 'skel' not in _S:
        _template()
    return _S['skel']


UAL_NEEDED = ('Idle_Loop', 'Walk_Loop', 'Jog_Fwd_Loop', 'Driving_Loop')


def _sample_ual(rig, actions):
    """Sample needed UAL actions at their native keys → dict name → (hipsP (N,3), Q (N,B,4), period frames)."""
    sk = _S['skel']
    out = {}
    for a in actions:
        if a.name not in UAL_NEEDED:
            continue
        cb = a.layers[0].strips[0].channelbag(a.slots[0])
        fr0, fr1 = a.frame_range
        n = int(round(fr1 - fr0)) + 1
        frames = np.arange(n) + fr0
        curves = {}
        for fc in cb.fcurves:
            bn = fc.data_path.split('"')[1]
            prop = fc.data_path.rsplit('.', 1)[1]
            curves[(bn, prop, fc.array_index)] = np.array([fc.evaluate(f) for f in frames])
        # full FK with basis loc/rot/scale (glTF bakes all three for every bone)
        Rw = np.empty((n, sk.B, 3, 3)); Pw = np.empty((n, sk.B, 3))
        for b, nm in enumerate(sk.names):
            loc = np.stack([curves.get((nm, 'location', i), np.zeros(n)) for i in range(3)], -1)
            q = np.stack([curves.get((nm, 'rotation_quaternion', i), np.full(n, 1.0 if i == 0 else 0.0)) for i in range(4)], -1)
            Rb = q2m(qnorm(q))
            p = sk.parent[b]
            if p < 0:
                Rw[:, b] = sk.restR[b] @ Rb
                Pw[:, b] = sk.restT[b] + np.einsum('ij,fj->fi', sk.restR[b], loc)
            else:
                Rw[:, b] = Rw[:, p] @ sk.relR[b] @ Rb
                Pw[:, b] = Pw[:, p] + np.einsum('fij,fj->fi', Rw[:, p], sk.relT[b] + np.einsum('ij,fj->fi', sk.relR[b], loc))
        fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        out[a.name] = dict(hipsP=Pw[:, sk.hips].copy(), Q=sk.local(Rw), n=n, fps=fps)
    return out


def _plaster(name, color, sss=0.06):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color[:3], 1)
    b.inputs['Roughness'].default_value = 0.58
    b.inputs['Specular IOR Level'].default_value = 0.35
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.32, 0.26)
    b.inputs['Subsurface Scale'].default_value = 0.015
    return m


def load(name, tone=None):
    """Instance a mannequin named `name` (armature object) with mesh `<name>_body`; returns the rig."""
    tpl_rig, tpl_mesh = _template()
    tone = tuple(tone) if tone is not None else (0.63, 0.63, 0.63)
    rig = tpl_rig.copy(); rig.data = tpl_rig.data.copy(); rig.use_fake_user = False
    rig.name = name; rig.data.name = f'{name}_arm'
    bpy.context.scene.collection.objects.link(rig)
    me = tpl_mesh.copy(); me.data = tpl_mesh.data.copy(); me.use_fake_user = False
    me.name = f'{name}_body'; me.data.name = f'{name}_body'
    bpy.context.scene.collection.objects.link(me)
    me.parent = rig; me.matrix_parent_inverse.identity()
    for md in me.modifiers:
        if md.type == 'ARMATURE':
            md.object = rig
    main = _plaster(f'{name}_plaster', tone)
    joint = _plaster(f'{name}_joints', tuple(c * 0.78 for c in tone), sss=0.03)
    for i, slot in enumerate(me.material_slots):
        n = slot.material.name if slot.material else ''
        me.data.materials[i] = joint if 'Joint' in n else main
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    rig.rotation_mode = 'XYZ'
    _T[rig.name] = dict(segs=[], root0=None, seed=(sum(map(ord, name)) * 0.37) % 7.0)
    return rig


def body(rig):
    return next(o for o in rig.children if o.type == 'MESH')


_T = {}         # rig name → timeline state


def _state(rig):
    if rig.name not in _T:
        _T[rig.name] = dict(segs=[], root0=None)
    st = _T[rig.name]
    if st['root0'] is None:
        st['root0'] = (rig.location.x, rig.location.y, rig.location.z, rig.rotation_euler.z)
    return st


# ===================================================================== retarget (BVH → canonical)
#
# canonical clip: root (N,3) = ground x, y, yaw relative to the clip's first frame;
#                 hipsP (N,3) DEF-hips head in object space; Q (N,B,4) local basis quats.

RELAX_DEG = {'index': (10, 16, 9), 'middle': (13, 20, 11), 'ring': (16, 24, 13), 'pinky': (20, 28, 15)}
OPEN_DEG = {'index': (3, 4, 2), 'middle': (3, 4, 2), 'ring': (4, 5, 3), 'pinky': (5, 6, 3)}


def _finger_pose(table, thumb_k=0.35, thumb3=14.0):
    """Finger local quats from per-joint curl angles (deg) about each bone's UAL curl axis."""
    sk = skel(); ual = _S['ual']['Idle_Loop']
    out = {}
    for n in sk.names:
        if not n.startswith(('DEF-f_', 'DEF-thumb')):
            continue
        q = ual['Q'][0, sk.idx[n]]
        ax = q[1:] / max(1e-9, np.linalg.norm(q[1:]))
        if n.startswith('DEF-f_'):
            fing = n.split('_')[1].split('.')[0]
            k = int(n.split('.')[1]) - 1
            ang = math.radians(table[fing][k])
            out[n] = np.concatenate([[math.cos(ang / 2)], ax * math.sin(ang / 2)])
        elif n.startswith('DEF-thumb.03'):
            ang = math.radians(thumb3)
            out[n] = np.concatenate([[math.cos(ang / 2)], ax * math.sin(ang / 2)])
        else:
            out[n] = qslerp(np.array([1.0, 0, 0, 0]), q, thumb_k)
    return out


def _relaxed_hand():
    if 'relaxed' not in _S:
        _S['relaxed'] = _finger_pose(RELAX_DEG)
    return _S['relaxed']


def _open_hand():
    if 'open' not in _S:
        _S['open'] = _finger_pose(OPEN_DEG, thumb_k=0.15, thumb3=6.0)
    return _S['open']


def _yaw_from_hips(PL, PR):
    L = PL - PR
    return unwrap_yaw(np.arctan2(L[..., 1], L[..., 0]))


CMU_FEET = {'L': ('LeftFoot', 'LeftToeBase', 'LeftToeBase_end'), 'R': ('RightFoot', 'RightToeBase', 'RightToeBase_end')}
CMU_HANDS = {'L': ('LeftHand', 'LeftHandIndex1'), 'R': ('RightHand', 'RightHandIndex1')}


S100_FEET = {'L': ('LeftAnkle', 'LeftToe', 'LeftToe_end'), 'R': ('RightAnkle', 'RightToe', 'RightToe_end')}
S100_HANDS = {'L': ('LeftWrist', 'LeftWrist_end'), 'R': ('RightWrist', 'RightWrist_end')}
FAMILIES = {
    'cmu': dict(map=CMU_MAP, hipj=CMU_HIPJ, feet=CMU_FEET, hands=CMU_HANDS, calib=0),
    '100style': dict(map=S100_MAP, hipj=('LeftHip', 'RightHip'), feet=S100_FEET, hands=S100_HANDS, calib='rest'),
}


def _family(path):
    return '100style' if '100style' in str(path) else 'cmu'


def _take_stats(path, feet=CMU_FEET):
    """Whole-take floor statistics (Z-up source units): low percentiles of ankle / toe heights."""
    key = ('stats', str(path))
    if key in _S:
        return _S[key]
    bv = bvh(path)
    fr = np.arange(1, bv.nf, 4)
    _, P = bv.fk(fr)
    P = np.einsum('ij,fkj->fki', C_YUP, P)
    z = {}
    for k in range(3):
        allz = np.concatenate([P[:, bv.idx[feet[s][k]], 2] for s in ('L', 'R')])
        z[k] = float(np.percentile(allz, 3))
    st = dict(ank=z[0], toe=z[1], tip=z[2], floor=z[2] - 0.6 * (z[1] - z[2]) if z[1] > z[2] else z[2])
    _S[key] = st
    return st


def _src_contacts(bv, Ps, ratio, stats, frames_dt, feet=CMU_FEET, hands=CMU_HANDS):
    """Per-foot / per-hand contact masks from the source joints (floor + speed tests)."""
    out = {}
    dz = 0.022 / ratio
    vmax = 0.30 / ratio
    for s in ('L', 'R'):
        a, t, e = (bv.idx[n] for n in feet[s])
        za, zt = Ps[:, a, 2], Ps[:, t, 2]
        def spd(j):
            v = np.zeros(len(Ps)); v[1:] = np.linalg.norm(np.diff(Ps[:, j, :2], axis=0), axis=1) / frames_dt[1:]
            return gsmooth(v, 1.0)
        heel = (za < stats['ank'] + dz) & (spd(a) < vmax)
        ball = (zt < stats['toe'] + dz) & (spd(t) < vmax)
        out['c' + s] = _clean_mask(heel | ball, 3, 3).astype(float)
        h, i = (bv.idx[n] for n in hands[s])
        zh = np.minimum(Ps[:, h, 2], Ps[:, i, 2])
        out['ch' + s] = _clean_mask((zh < stats['floor'] + 0.075 / ratio) & (spd(h) < vmax), 3, 3).astype(float)
    return out


def retarget(path, times, root_mode='track', root_sigma=8.0, yaw_sigma=10.0, fam=None, floor='body'):
    """Retarget BVH samples at `times` (s, file time) onto the mannequin. Returns canonical clip
    in clip coordinates (root not yet normalised) plus the source data needed for diagnostics."""
    sk = skel()
    F_ = FAMILIES[fam or _family(path)]
    mapping, hipj = F_['map'], F_['hipj']
    bv = bvh(path)
    frames = np.asarray(times, float) / bv.ft
    Rs, Ps = bv.fk(frames)
    Rs = _repair_flips(Rs, np.asarray(times, float))
    Rc, Pc = bv.fk_rest() if F_['calib'] == 'rest' else bv.fk(np.array([F_['calib']]))
    A = C_YUP
    Rs = A @ Rs; Ps = np.einsum('ij,fkj->fki', A, Ps)
    Rc = A @ Rc[0]; Pc = Pc[0] @ A.T
    jl = bv.idx
    # scale: target leg length / source leg length
    src_leg = np.linalg.norm(bv.offsets[jl[mapping['DEF-shin.L'][0]]]) + np.linalg.norm(bv.offsets[jl[mapping['DEF-foot.L'][0]]])
    tgt_leg = sk.length[sk.idx['DEF-thigh.L']] + sk.length[sk.idx['DEF-shin.L']]
    ratio = tgt_leg / src_leg
    F = len(frames)
    Rw = np.empty((F, sk.B, 3, 3))
    mapped = np.zeros(sk.B, bool)
    for tb, (j, ja, jc) in mapping.items():
        b = sk.idx[tb]
        sdir = Pc[jl[jc]] - Pc[jl[ja]]
        tcal = rot_between(sk.restR[b][:, 1], sdir) @ sk.restR[b]
        O = Rc[jl[j]].T @ tcal
        Rw[:, b] = Rs[:, jl[j]] @ O
        mapped[b] = True
    # hip-joint midpoint → DEF-hips head; vertical refined later by floor calibration
    mid = 0.5 * (Ps[:, jl[hipj[0]]] + Ps[:, jl[hipj[1]]]) * ratio
    yaw_raw = _yaw_from_hips(Ps[:, jl[hipj[0]]], Ps[:, jl[hipj[1]]])
    if root_mode == 'fixed':
        rxy = np.broadcast_to(mid[:, :2].mean(0), (F, 2)).copy()
        ryaw = np.full(F, math.atan2(np.sin(yaw_raw).mean(), np.cos(yaw_raw).mean()))
    else:
        rxy = gsmooth(mid[:, :2], root_sigma)
        ryaw = gsmooth(yaw_raw, yaw_sigma)
    Rinv = rotz(-ryaw)
    Robj = Rinv[:, None] @ Rw
    hips_obj_mid = np.einsum('fij,fj->fi', Rinv, mid - np.concatenate([rxy, np.zeros((F, 1))], 1))
    hipsP = hips_obj_mid - np.einsum('fij,j->fi', Robj[:, sk.hips], sk.hipmid_local)
    # local quats: mapped bones from world; fingers relaxed; root identity
    relax = _relaxed_hand()
    Q = np.empty((F, sk.B, 4))
    Rfull = np.empty_like(Rw)
    for b in range(sk.B):
        p = sk.parent[b]
        Rp = sk.restR[b] @ np.eye(3) if p < 0 else None
        if p < 0:
            Q[:, b] = (1, 0, 0, 0); Rfull[:, b] = sk.restR[b]
            continue
        if mapped[b]:
            Rfull[:, b] = Robj[:, b]
            Q[:, b] = m2q(np.swapaxes(Rfull[:, p] @ sk.relR[b], -1, -2) @ Robj[:, b])
        else:
            q = relax.get(sk.names[b], np.array([1.0, 0, 0, 0]))
            Q[:, b] = q
            Rfull[:, b] = Rfull[:, p] @ sk.relR[b] @ q2m(q)
    Q = qcont(Q)
    clip = dict(root=np.concatenate([rxy, ryaw[:, None]], 1), hipsP=hipsP, Q=Q, ratio=ratio)
    dt = np.gradient(np.asarray(times, float)) if len(times) > 1 else np.ones(1)
    dt = np.where(np.abs(dt) < 1e-6, 1.0 / FPS, np.abs(dt))
    _deglitch(clip)
    stats = _take_stats(path, F_['feet'])
    clip.update(_src_contacts(bv, Ps, ratio, stats, dt, F_['feet'], F_['hands']))
    clip['src_hipz'] = (0.5 * (Ps[:, jl[hipj[0]], 2] + Ps[:, jl[hipj[1]], 2]) - stats['floor']) * ratio
    if floor == 'body':
        _floor_calibrate(clip)
    elif floor == 'ground':
        _floor_calibrate_ground(clip)
    return clip


def _repair_flips(R, times, jump_deg=75.0, max_s=0.5):
    """Mocap twist flips (a joint's rotation jumps >75° and jumps back within 0.5 s – e.g. CMU
    111_06 right leg at 6.38–6.52 s) are replaced by slerp between the bounding good samples."""
    F, J = R.shape[:2]
    if F < 3:
        return R
    q = m2q(R.reshape(-1, 3, 3)).reshape(F, J, 4)
    q = qcont(q)
    dt = np.median(np.abs(np.diff(times))) or 1.0 / FPS
    win = max(2, int(max_s / dt))
    out = q.copy(); bad_any = False
    for j in range(J):
        d = np.degrees(2 * np.arccos(np.abs((q[1:, j] * q[:-1, j]).sum(-1)).clip(0, 1)))
        jumps = np.nonzero(d > jump_deg)[0]
        k = 0
        while k < len(jumps):
            a = jumps[k]
            back = [b for b in jumps[k + 1:] if b - a <= win]
            if not back:
                k += 1; continue
            b = back[0]                       # samples a+1 .. b are the flipped stretch
            g0, g1 = a, min(b + 1, F - 1)
            t = (np.arange(a + 1, b + 1) - g0) / max(g1 - g0, 1)
            out[a + 1:b + 1, j] = qslerp(q[g0, j], q[g1, j], t)
            bad_any = True
            k = list(jumps).index(b) + 1
    return q2m(out) if bad_any else R


def _deglitch(clip, thresh=0.02, sigma=2.5):
    """Mocap marker glitches show up as pelvis acceleration spikes (> 2 cm/frame²); smooth
    pose and root locally around them, leaving clean motion untouched."""
    hw = np.concatenate([clip['root'][:, :2], np.zeros((len(clip['root']), 1))], 1) + clip['hipsP']
    if len(hw) < 5:
        return
    acc = np.zeros(len(hw)); acc[1:-1] = np.linalg.norm(np.diff(hw, 2, axis=0), axis=1)
    bad = _maxfilter((acc > thresh).astype(float), 3)
    if not bad.any():
        return
    m = np.clip(gsmooth(bad, 1.5) * 1.5, 0, 1)[:, None]
    clip['hipsP'] = clip['hipsP'] * (1 - m) + gsmooth(clip['hipsP'], sigma) * m
    clip['root'] = clip['root'] * (1 - m) + gsmooth(clip['root'], sigma) * m
    Qs = qnorm(gsmooth(qcont(clip['Q']), sigma))
    clip['Q'] = qslerp(clip['Q'], Qs, m)
    clip['deglitched'] = int((bad > 0).sum())


def _foot_sets():
    if 'feet' in _S:
        return _S['feet']
    sk = skel()
    out = {}
    for s in ('L', 'R'):
        ids = [sk.idx[f'DEF-foot.{s}'], sk.idx[f'DEF-toe.{s}']]
        sel = np.nonzero(np.isin(sk.dom, ids))[0]
        out[s] = sel
        hid = [sk.idx[n] for n in sk.names if n.endswith(f'.{s}') and (n.startswith('DEF-f_') or n.startswith('DEF-thumb') or n == f'DEF-hand.{s}')]
        out['hand' + s] = np.nonzero(np.isin(sk.dom, hid))[0]
    seat_ids = [sk.idx['DEF-hips'], sk.idx['DEF-thigh.L'], sk.idx['DEF-thigh.R'], sk.idx['DEF-spine.001']]
    out['seat'] = np.nonzero(np.isin(sk.dom, seat_ids) & (sk.vrest[:, 2] < 0.98))[0]
    out['all'] = np.arange(len(sk.vrest))
    _S['feet'] = out
    return out


def _world(root, Pobj):
    """Object-space points (F,...,3) → clip/world space using root (F,3) [x, y, yaw]."""
    Rz = rotz(root[:, 2])
    sh = Pobj.shape
    p = np.einsum('fij,fvj->fvi', Rz, Pobj.reshape(sh[0], -1, 3))
    p[..., 0] += root[:, 0, None]; p[..., 1] += root[:, 1, None]
    return p.reshape(sh)


def _floor_sample():
    """Vertex subset for lowest-point queries: every sole/hand vertex plus a sparse body sample."""
    if 'floor_sel' not in _S:
        sk = skel(); fs = _foot_sets()
        legs = np.nonzero(np.isin(sk.dom, [sk.idx[n] for n in ('DEF-thigh.L', 'DEF-thigh.R', 'DEF-shin.L', 'DEF-shin.R')]))[0]
        sel = np.unique(np.concatenate([fs['L'], fs['R'], fs['handL'], fs['handR'], fs['seat'], legs, np.arange(0, len(sk.vrest), 3)]))
        _S['floor_sel'] = sel
    return _S['floor_sel']


def _body_sample():
    """Floor-query vertices excluding forearms/hands (those are reached by arm IK)."""
    if 'body_sel' not in _S:
        sk = skel(); sel = _floor_sample()
        arm = [sk.idx[n] for n in sk.names if n.startswith(('DEF-f_', 'DEF-thumb', 'DEF-hand', 'DEF-forearm'))]
        _S['body_sel'] = sel[~np.isin(sk.dom[sel], arm)]
    return _S['body_sel']


def _floor_calibrate_feet(clip, contacts, sigma=2.0):
    """Gait loops: the planted foot defines the floor (the authored swing toe may dip below)."""
    sk = skel(); fs = _foot_sets()
    R, P = sk.fk(clip['hipsP'], clip['Q'])
    N = len(R); low = np.full(N, np.inf)
    for s in ('L', 'R'):
        mz = sk.verts(R, P, fs[s])[:, :, 2].min(1)
        low = np.where(contacts[s] > 0.5, np.minimum(low, mz), low)
    ok = np.isfinite(low)
    if ok.sum() >= 2:
        idx = np.arange(N)
        off = gsmooth(np.interp(idx, idx[ok], low[ok]), sigma)
        clip['hipsP'] = clip['hipsP'] - np.stack([np.zeros(N), np.zeros(N), off], 1)


SEAT_HIPZ = 0.33      # source hip-joint height (m, target scale) below which the figure is seated


def _floor_calibrate_ground(clip, sigma=2.0):
    """Ground motions (sitting, crawling, getting up): whatever non-arm part is lowest – seat,
    knee, shin or foot – is what the floor supports. Hands are excluded on purpose: the mannequin's
    arms are proportionally longer than the performers', so a supporting palm would prop the body
    up; the solver bends the elbows to put the palms on the floor instead."""
    sk = skel()
    R, P = sk.fk(clip['hipsP'], clip['Q'])
    N = len(R)
    low = sk.verts(R, P, _body_sample())[:, :, 2].min(1)
    off = -_maxfilter(-low, 2)
    off = np.minimum(gsmooth(off, sigma), low)
    clip['hipsP'] = clip['hipsP'] - np.stack([np.zeros(N), np.zeros(N), off], 1)
    clip['seat'] = np.zeros(N)
    clip['floor_off'] = off


def _floor_calibrate(clip, sigma=2.5):
    """Per frame, shift the hips so the body's lowest vertex rests on z=0 (true for any motion
    without a flight phase: the lowest point is what the floor supports). Erode-then-smooth keeps
    the correction from ever pushing a part below the floor (may float a few mm in a switch)."""
    sk = skel()
    R, P = sk.fk(clip['hipsP'], clip['Q'])
    low = sk.verts(R, P, _floor_sample())[:, :, 2].min(1)
    off = -_maxfilter(-low, 3)            # running min
    off = gsmooth(off, sigma)
    off = np.minimum(off, low)
    clip['hipsP'] = clip['hipsP'] - np.stack([np.zeros(len(off)), np.zeros(len(off)), off], 1)
    clip['floor_off'] = off


def _normalise(clip):
    """Root relative to the first frame: root_rel[0] = (0,0,0); object-space data unchanged."""
    r = clip['root']
    r0 = r[0].copy()
    d = r[:, :2] - r0[:2]
    Rz = rotz(-r0[2])
    rel = np.concatenate([np.einsum('ij,fj->fi', Rz[:2, :2], d), (r[:, 2] - r0[2])[:, None]], 1)
    clip['root'] = rel
    return clip


# ===================================================================== timeline

EXT = 30          # frames each segment is extended past f1 so the next one can crossfade into it


def _add(rig, seg):
    st = _state(rig)
    st['segs'] = [s for s in st['segs'] if not (s['f0'] == seg['f0'] and s['kind'] == seg['kind'])]
    st['segs'].append(seg)
    st['segs'].sort(key=lambda s: s['f0'])
    _bake(rig)
    return rig


def _compose(start, rel):
    """start (x, y, yaw) ∘ rel (N,3) → absolute (N,3)."""
    Rz = rotz(start[2])[:2, :2]
    xy = np.einsum('ij,fj->fi', Rz, rel[:, :2]) + np.array(start[:2])
    return np.concatenate([xy, (rel[:, 2] + start[2])[:, None]], 1)


FLAG_DEFAULTS = {'seat': 0.0, 'hands': 0.0, 'nofeet': 0.0, 'widenL': 0.0, 'widenR': 0.0, 'cL': -1.0, 'cR': -1.0, 'chL': -1.0, 'chR': -1.0, 'clearL': 0.0, 'clearR': 0.0}


def _seg_flag(s, k, j):
    v = s.get(k, FLAG_DEFAULTS[k])
    return float(v[j]) if np.ndim(v) else float(v)


def _assemble(rig):
    st = _state(rig); sk = skel()
    segs = st['segs']
    F0 = min(s['f0'] for s in segs); F1 = max(s['f1'] for s in segs)
    N = F1 - F0 + 1
    root = np.zeros((N, 3)); hipsP = np.zeros((N, 3)); Q = np.zeros((N, sk.B, 4))
    flags = {k: np.full(N, v) for k, v in FLAG_DEFAULTS.items()}
    targets = []
    x0, y0, z0, yaw0 = st['root0']
    cur = (x0, y0, yaw0)
    written = -1
    for i, s in enumerate(segs):
        a = s['f0'] - F0
        n = len(s['Q'])
        if s.get('start') is not None:
            start = s['start']
        elif 0 <= a <= written:
            start = tuple(root[a])
        else:
            start = cur
        cut = False
        for pf, pl in st.get('places', []):
            if pf is not None and pf <= s['f0'] and (i == 0 or pf > segs[i - 1]['f0']):
                start = (pl[0], pl[1], pl[3]); cut = True
        sroot = _compose(start, s['root'])
        bl = s.get('blend', 10) if (i > 0 and a <= written and not cut) else 0
        hi = min(N, a + n)
        for k in range(a, hi):
            j = k - a
            if j < bl and k <= written:
                w = smoothstep((j + 1) / (bl + 1))
                r0 = root[k]; r1 = sroot[j]
                dyaw = math.atan2(math.sin(r1[2] - r0[2]), math.cos(r1[2] - r0[2]))
                root[k] = (r0[0] + (r1[0] - r0[0]) * w, r0[1] + (r1[1] - r0[1]) * w, r0[2] + dyaw * w)
                hipsP[k] = hipsP[k] * (1 - w) + s['hipsP'][j] * w
                Q[k] = qslerp(Q[k], s['Q'][j], w)
                for fk_ in flags:
                    v = _seg_flag(s, fk_, j)
                    if fk_.startswith('c'):
                        old = flags[fk_][k]
                        # a contact persists through the crossfade if either side has it
                        flags[fk_][k] = max(old, v) if (old >= 0 and v >= 0) else (v if w > 0.5 else old)
                    else:
                        flags[fk_][k] = flags[fk_][k] * (1 - w) + v * w
            else:
                root[k] = sroot[j]; hipsP[k] = s['hipsP'][j]; Q[k] = s['Q'][j]
                for fk_ in flags:
                    flags[fk_][k] = _seg_flag(s, fk_, j)
        if hi < N:
            root[hi:] = root[hi - 1]; hipsP[hi:] = hipsP[hi - 1]; Q[hi:] = Q[hi - 1]
            for fk_ in flags:
                flags[fk_][hi:] = flags[fk_][hi - 1]
        written = hi - 1
        cur = tuple(root[min(s['f1'] - F0, N - 1)])
        if s.get('targets'):
            targets.append((a, n, s['targets']))
    root[:, 2] = unwrap_yaw(root[:, 2])
    return F0, F1, root, z0, hipsP, qcont(Q), flags, targets


# ===================================================================== contact solver + IK

def _runs(m):
    """[(a, b)] inclusive index runs where boolean mask m is True."""
    m = np.asarray(m, bool)
    if not m.any():
        return []
    d = np.diff(np.concatenate([[0], m.astype(int), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1))


def _clean_mask(m, min_len=4, max_gap=3):
    m = np.asarray(m, bool).copy()
    for a, b in _runs(~m):
        if a > 0 and b < len(m) - 1 and (b - a + 1) <= max_gap:
            m[a:b + 1] = True
    for a, b in _runs(m):
        if b - a + 1 < min_len:
            m[a:b + 1] = False
    return m


def _maxfilter(x, r):
    out = x.copy()
    for k in range(1, r + 1):
        out[k:] = np.maximum(out[k:], x[:-k]); out[:-k] = np.maximum(out[:-k], x[k:])
    return out


def _contact_fix(Vw, Ew, enable, h_on=0.03, v_on=0.5, eps=0.012, lock=True, forced=None, clear=None):
    """Lock sliding contact and snap to the floor.
    Vw (N,V,3) world contact-surface vertices, Ew (N,3) world chain end (ankle/wrist).
    Returns corrected chain-end targets (N,3) and the planted mask."""
    N = len(Vw)
    minz = Vw[:, :, 2].min(1)
    c = Vw.mean(1)
    sp = np.zeros(N); sp[1:] = np.linalg.norm(np.diff(c[:, :2], axis=0), axis=1) * FPS
    sp = gsmooth(sp, 1.0)
    pl = (minz < h_on) & (sp < v_on)
    if forced is not None:
        pl = np.where(forced >= 0, forced > 0.5, pl)
    pl = _clean_mask(pl & enable, 3, 3)
    w = gsmooth(pl.astype(float), 0.8 if clear is not None and np.any(clear) else 1.5)
    cl = np.zeros(N) if clear is None else np.where(pl, 0.0, clear)
    # a free foot/hand moving along the floor hovers a little instead of skidding on it
    cl = np.maximum(cl, np.where(pl, 0.0, 0.014 * smoothstep((sp - 0.15) / 0.3)))
    dz = w * (-minz) + (1 - w) * np.maximum(0, cl - minz)
    corr = np.zeros((N, 2))
    if lock:
        runs = _runs(pl)
        last_end, last_c = None, np.zeros(2)
        for a, b in runs:
            if last_end is not None:                 # swing: ease the previous lock back to the source path
                g = a - last_end - 1
                for k in range(last_end + 1, a):
                    corr[k] = last_c * (1 - smoothstep((k - last_end) / (g + 1)))
            corr[a] = 0
            for t in range(a + 1, b + 1):
                zt = Vw[t, :, 2] + dz[t]; zp = Vw[t - 1, :, 2] + dz[t - 1]
                m = (zt < eps) & (zp < eps)
                if m.sum() < 3:
                    m = np.argsort(zt)[:6]
                slide = (Vw[t, m, :2] - Vw[t - 1, m, :2]).mean(0)
                corr[t] = corr[t - 1] - slide
            last_end, last_c = b, corr[b].copy()
        if last_end is not None and last_end < N - 1:
            corr[last_end + 1:] = last_c
    T = Ew + np.concatenate([corr, dz[:, None]], 1)
    _S['last_corr'] = corr
    return T, pl


def _ik2(R, P, sk, b1, b2, T, w, bend_local=None):
    """Two-bone IK in place on world rotations R: chain b1 → b2 → end (child of b2) reaches T
    (blend weight w). Anatomical hinge: both bones flex about one shared axis; the bend plane
    follows the current joint offset when the limb is bent and the upper bone's −Z (the side the
    knee/elbow points to in Rigify) when it is straight, so a straight limb never folds sideways.
    The lower bone keeps its original twist; the end bone keeps its world rotation."""
    H = P[:, b1]; K0 = P[:, b2]
    l1 = sk.length[b1]; l2 = sk.length[b2]
    E0 = K0 + R[:, b2][:, :, 1] * l2
    T = E0 + (T - E0) * np.asarray(w)[:, None]
    d = T - H; dl = np.linalg.norm(d, axis=1); u = d / dl[:, None]
    dc = np.clip(dl, abs(l1 - l2) + 1e-4, (l1 + l2) - 1e-5)
    perp = lambda v: v - (v * u).sum(1)[:, None] * u
    off = perp(K0 - H)
    anat = perp(-R[:, b1][:, :, 2])
    anat /= np.maximum(np.linalg.norm(anat, axis=1), 1e-9)[:, None]
    on = np.linalg.norm(off, axis=1)
    wt = np.clip((on - 0.01) / 0.04, 0, 1)[:, None]           # trust the joint offset once bent >~5°
    pole = off / np.maximum(on, 1e-9)[:, None] * wt + anat * (1 - wt)
    # a nearly straight limb must not start bending against the anatomical side (a deeply bent
    # one keeps its own plane – switching there would flip the joint)
    flip = ((pole * anat).sum(1) < -0.2) & (wt[:, 0] < 0.5)
    pole[flip] = anat[flip]
    pole /= np.maximum(np.linalg.norm(pole, axis=1), 1e-9)[:, None]
    a = (l1 * l1 - l2 * l2 + dc * dc) / (2 * dc)
    h = np.sqrt(np.maximum(l1 * l1 - a * a, 0))
    K = H + u * a[:, None] + pole * h[:, None]
    E = H + u * dc[:, None]
    Y1 = (K - H) / l1; Y2 = (E - K) / l2
    hinge = np.cross(Y1, Y2); hn = np.linalg.norm(hinge, axis=1)
    # straight limb: hinge from the upper bone's own X (orthogonalised)
    X1o = R[:, b1][:, :, 0]
    X1f = X1o - (X1o * Y1).sum(1)[:, None] * Y1
    X1f /= np.maximum(np.linalg.norm(X1f, axis=1), 1e-9)[:, None]
    hinge = np.where((hn > 1e-4)[:, None], hinge / np.maximum(hn, 1e-9)[:, None], X1f)
    # original twist of the lower bone about its axis relative to the hinge
    Y2o = R[:, b2][:, :, 1]; X2o = R[:, b2][:, :, 0]
    ref = X1o - (X1o * Y2o).sum(1)[:, None] * Y2o
    ref /= np.maximum(np.linalg.norm(ref, axis=1), 1e-9)[:, None]
    tw = np.arctan2((np.cross(ref, X2o) * Y2o).sum(1), (ref * X2o).sum(1))
    R1n = np.stack([hinge, Y1, np.cross(hinge, Y1)], 2)
    X2 = hinge * np.cos(tw)[:, None] + np.cross(Y2, hinge) * np.sin(tw)[:, None]
    R2n = np.stack([X2, Y2, np.cross(X2, Y2)], 2)
    R[:, b1] = R1n; R[:, b2] = R2n
    return E


def _heading_lock(R, ft, toe, Rz, Rzi, pl):
    """Planted feet keep their world heading (a flat foot must not spin on the ground while the
    body turns); the offset eases out over the next swing so the step lands in the new
    direction. Rotates foot and toe world rotations about the vertical through the ankle."""
    N = len(R)
    fwd = np.einsum('fij,fj->fi', Rz, R[:, ft][:, :, 1])
    head = unwrap_yaw(np.arctan2(fwd[:, 0], -fwd[:, 1]))
    hz = np.linalg.norm(fwd[:, :2], axis=1)
    dpsi = np.zeros(N)
    last_end, last_d = None, 0.0
    for a, b in _runs(pl):
        if hz[a:b + 1].min() < 0.5:          # foot near vertical (kneeling on tucked toes): heading undefined
            continue
        if last_end is not None:
            g = a - last_end - 1
            for k_ in range(last_end + 1, a):
                dpsi[k_] = last_d * (1 - smoothstep((k_ - last_end) / (g + 1)))
        dpsi[a:b + 1] = head[a] - head[a:b + 1]
        last_end, last_d = b, dpsi[b]
    if last_end is not None and last_end < N - 1:
        dpsi[last_end + 1:] = last_d
    if np.abs(dpsi).max() < 1e-4:
        return False
    M = Rzi @ rotz(dpsi) @ Rz
    R[:, ft] = M @ R[:, ft]; R[:, toe] = M @ R[:, toe]
    return True


def _reach_drop(H, T, Lmax):
    d = T - H
    s = np.sqrt(np.maximum(Lmax ** 2 - d[:, 0] ** 2 - d[:, 1] ** 2, 0))
    return np.maximum(0, -s - d[:, 2])


MAX_DROP = 0.04                       # m: never squat more than this to reach a locked foot
KNEE_FWD = np.array([0, -1.0, 0])     # rest-pose (armature) direction the knees bend toward
ELBOW_BACK = np.array([0, 1.0, 0])    # rest-pose direction the elbows point to


def _solve(root, hipsP, Q, flags, targets):
    sk = skel(); fs = _foot_sets(); ix = sk.idx
    N = len(Q)
    hipsP = hipsP.copy()
    # light de-noise (mocap hand/finger jitter, resampling) – sub-frame scale only
    Q = qnorm(gsmooth(qcont(Q), 0.7))
    hipsP = gsmooth(hipsP, 0.6)
    R, P = sk.fk(hipsP, Q)
    # 1. seat on the asphalt where flagged
    if flags['seat'].max() > 0:
        sv = sk.verts(R, P, fs['seat'])
        mz = sv[:, :, 2].min(1)
        hipsP[:, 2] -= flags['seat'] * mz
        R, P = sk.fk(hipsP, Q)
    # 2. foot contacts → ankle targets (world → object)
    Rz = rotz(root[:, 2]); Rzi = np.swapaxes(Rz, -1, -2)
    off = np.concatenate([root[:, :2], np.zeros((N, 1))], 1)
    feet_on = flags['nofeet'] < 0.5
    leg = {}; corrs = {}
    for s in ('L', 'R'):
        th, sh, ft, toe = ix[f'DEF-thigh.{s}'], ix[f'DEF-shin.{s}'], ix[f'DEF-foot.{s}'], ix[f'DEF-toe.{s}']
        Vw = _world(root, sk.verts(R, P, fs[s]))
        Ew = _world(root, P[:, ft][:, None])[:, 0]
        _, pl0 = _contact_fix(Vw, Ew, feet_on, forced=flags['c' + s], clear=flags['clear' + s])
        if _heading_lock(R, ft, toe, Rz, Rzi, pl0):
            Vw = _world(root, sk.verts(R, P, fs[s]))
        Tw, pl = _contact_fix(Vw, Ew, feet_on, forced=flags['c' + s], clear=flags['clear' + s])
        To = np.einsum('fij,fj->fi', Rzi, Tw - off)
        To[:, 0] += flags['widen' + s] * (1.0 if s == 'L' else -1.0)     # step width (object +X = left)
        leg[s] = (th, sh, To, pl)
        corrs[s] = _S['last_corr'].copy()
    # extra explicit targets (object space) e.g. pedals / wheel
    for a, n, tg in targets:
        for key, val in tg.items():
            if key.startswith('foot'):
                pos, wt = val
                s = key[-1]; th, sh, To, pl = leg[s]
                hi = min(N, a + n); L = hi - a
                ww = np.asarray(wt)[:L][:, None]
                To[a:hi] = To[a:hi] * (1 - ww) + pos[:L] * ww
    # 3. pelvis drop where a planted foot is out of reach
    drop = np.zeros(N)
    for s in ('L', 'R'):
        th, sh, To, pl = leg[s]
        Lmax = (sk.length[th] + sk.length[sh]) * 0.996
        drop = np.maximum(drop, _reach_drop(P[:, th], To, Lmax))
    if drop.max() > 1e-4:
        drop = np.minimum(gsmooth(_maxfilter(drop, 6), 2.0), MAX_DROP)
        hipsP[:, 2] -= drop
        P = sk.fk(hipsP, sk.local(R))[1]           # keep R: it carries the heading locks
    for it in range(2):
        if it:      # residual pass: shin-weighted ankle vertices move with the IK'd shin
            P = sk.fk(hipsP, sk.local(R))[1]
            for s in ('L', 'R'):
                th, sh, To, pl = leg[s]
                ft = ix[f'DEF-foot.{s}']
                mz = sk.verts(R, P, fs[s])[:, :, 2].min(1)
                res = np.where(pl, -mz, np.maximum(0, -mz))
                To[:, 2] += res
        for s in ('L', 'R'):
            th, sh, To, pl = leg[s]
            bend = sk.restR[th].T @ KNEE_FWD
            _ik2(R, P, sk, th, sh, To, np.ones(N), bend)
    # 3b. nothing below the floor: raise the pelvis where any vertex is under z=0, then re-reach
    lift = np.zeros(N)
    for _ in range(3):
        P = sk.fk(hipsP, sk.local(R))[1]
        low = sk.verts(R, P, _body_sample())[:, :, 2].min(1)
        if low.min() >= -0.002:
            break
        dl = gsmooth(_maxfilter(np.maximum(0, -low), 5), 2.2) * 1.05
        lift += dl
        hipsP[:, 2] += dl
        P = sk.fk(hipsP, sk.local(R))[1]
        for s in ('L', 'R'):
            th, sh, To, pl = leg[s]
            _ik2(R, P, sk, th, sh, To, np.ones(N), sk.restR[th].T @ KNEE_FWD)
    # 4. hands: ground contact where flagged, explicit targets
    hand_t = {}
    for s in ('L', 'R'):
        ua, fa, hd = ix[f'DEF-upper_arm.{s}'], ix[f'DEF-forearm.{s}'], ix[f'DEF-hand.{s}']
        Pk = None
        To = None; wt = np.zeros(N)
        if flags['hands'].max() > 0:
            R2, P2 = R, sk.fk(hipsP, sk.local(R))[1]
            Vw = _world(root, sk.verts(R2, P2, fs['hand' + s]))
            Ew = _world(root, P2[:, hd][:, None])[:, 0]
            Tw, pl = _contact_fix(Vw, Ew, flags['hands'] > 0.5, h_on=0.035, v_on=0.5, forced=flags['ch' + s])
            To = np.einsum('fij,fj->fi', Rzi, Tw - off)
            wt = np.maximum(wt, np.clip(flags['hands'], 0, 1))
        for a, n, tg in targets:
            k = 'hand' + s
            if k in tg and isinstance(tg[k], tuple):
                pos, w_ = tg[k]
                hi = min(N, a + n); L = hi - a
                if To is None:
                    To = P[:, hd].copy()
                ww = np.asarray(w_)[:L][:, None]
                To[a:hi] = To[a:hi] * (1 - ww) + pos[:L] * ww
                wt[a:hi] = np.maximum(wt[a:hi], np.asarray(w_)[:L])
        if To is not None:
            P2 = sk.fk(hipsP, sk.local(R))[1]
            keep = any(tg.get('hand_local') for _, _, tg in targets)
            rel = np.swapaxes(R[:, fa], -1, -2) @ R[:, hd] if keep else None
            _ik2(R, P2, sk, ua, fa, To, wt)
            if keep:                     # gripping hands follow the forearm (wrist keeps its bend)
                R[:, hd] = R[:, fa] @ rel
    Qn = sk.local(R)
    # fingers / unmapped bones keep their incoming local rotation
    return hipsP, Qn, {'drop': drop, 'lift': lift, 'planted': {s: leg[s][3] for s in leg}, 'corr': corrs}


# ===================================================================== writing

_CUTS = {'frames': [], 'idx': None}       # set by _write for the curves it creates


def _fc_set(cb, path, idx, frames, vals):
    """Per-frame LINEAR keys. At an in-shot cut c the pre-cut pose holds to c-0.5 and switches
    with CONSTANT interpolation, so motion blur (±0.25 frame) never smears across the cut."""
    frames = np.asarray(frames, float); vals = np.asarray(vals, float)
    interp = np.ones(len(frames), int)
    for c in _CUTS['frames']:
        i = int(c - frames[0])
        if 0 < i < len(frames):
            frames = np.insert(frames, i, c - 0.5); vals = np.insert(vals, i, vals[i])
            interp = np.insert(interp, i, 0); interp[i - 1] = 0
    fc = cb.fcurves.new(path, index=idx)
    n = len(frames)
    fc.keyframe_points.add(n)
    co = np.empty(2 * n); co[0::2] = frames; co[1::2] = vals
    fc.keyframe_points.foreach_set('co', co)
    fc.keyframe_points.foreach_set('interpolation', interp.tolist())      # 1 LINEAR, 0 CONSTANT
    fc.update()
    return fc


def _write(rig, F0, root, z0, hipsP, Q):
    from bpy_extras import anim_utils
    sk = skel()
    N = len(Q)
    frames = np.arange(F0, F0 + N, dtype=float)
    ad = rig.animation_data_create()
    old = ad.action
    if old is not None:
        ad.action = None
        if old.users == 0:
            bpy.data.actions.remove(old)
        old = None
    act = bpy.data.actions.new(f'{rig.name}_p2')
    ad.action = act
    slot = ad.action_slot
    if slot is None:
        slot = act.slots.new('OBJECT', rig.name)
        ad.action_slot = slot
    cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
    if old is not None and old.users == 0:
        bpy.data.actions.remove(old)
    hb = rig.pose.bones['DEF-hips'].bone
    rest = np.array(hb.matrix_local)
    loc = (hipsP - rest[:3, 3]) @ rest[:3, :3]          # armature → bone-local translation
    for i in range(3):
        _fc_set(cb, 'pose.bones["DEF-hips"].location', i, frames, loc[:, i])
    for b, nm in enumerate(sk.names):
        if nm == 'root':
            continue
        q = Q[:, b]
        if np.abs(q - q[0]).max() < 1e-7:
            rig.pose.bones[nm].rotation_quaternion = q[0]
            continue
        for i in range(4):
            _fc_set(cb, f'pose.bones["{nm}"].rotation_quaternion', i, frames, q[:, i])
    moving = np.abs(root - root[0]).max() > 1e-6
    if moving:
        _fc_set(cb, 'location', 0, frames, root[:, 0]); _fc_set(cb, 'location', 1, frames, root[:, 1])
        _fc_set(cb, 'location', 2, frames, np.full(N, z0))
        _fc_set(cb, 'rotation_euler', 2, frames, root[:, 2])
    rig.location = (root[0, 0], root[0, 1], z0)
    rig.rotation_euler = (0, 0, root[0, 2])


def _slice_targets(targets, p0, p1):
    out = []
    for a, n, tg in targets:
        lo, hi = max(a, p0), min(a + n, p1)
        if lo >= hi:
            continue
        o = lo - a; L = hi - lo
        tg2 = {}
        for k, v in tg.items():
            tg2[k] = (v[0][o:o + L], np.asarray(v[1])[o:o + L]) if isinstance(v, tuple) else v
        out.append((lo - p0, L, tg2))
    return out


def _bake(rig):
    F0, F1, root, z0, hipsP, Q, flags, targets = _assemble(rig)
    st = _state(rig)
    cuts = sorted(pf for pf, _ in st.get('places', []) if pf is not None and F0 < pf <= F1)
    # an in-shot cut is a hard boundary: solve each continuous piece on its own (no smoothing,
    # contact locks or pelvis filters may reach across it)
    edges = [0] + [c - F0 for c in cuts] + [len(Q)]
    hp_out, q_out, dbg = [], [], {}
    for p0, p1 in zip(edges[:-1], edges[1:]):
        if p1 <= p0:
            continue
        fl = {k: v[p0:p1] for k, v in flags.items()}
        h_, q_, d_ = _solve(root[p0:p1], hipsP[p0:p1], Q[p0:p1], fl, _slice_targets(targets, p0, p1))
        hp_out.append(h_); q_out.append(q_)
        for k, v in d_.items():
            if isinstance(v, dict):
                dbg.setdefault(k, {}); [dbg[k].setdefault(kk, []).append(vv) for kk, vv in v.items()]
            else:
                dbg.setdefault(k, []).append(v)
    hipsP = np.concatenate(hp_out); Q = np.concatenate(q_out)
    dbg = {k: ({kk: np.concatenate(vv) for kk, vv in v.items()} if isinstance(v, dict) else np.concatenate(v)) for k, v in dbg.items()}
    _CUTS['frames'] = cuts
    try:
        _write(rig, F0, root, z0, hipsP, Q)
    finally:
        _CUTS['frames'] = []
    st = _state(rig)
    st['baked'] = dict(F0=F0, F1=F1, root=root, z0=z0, hipsP=hipsP, Q=Q, flags=flags, dbg=dbg)


# ===================================================================== placement

def lowest_z(rig, frame=None):
    """Lowest evaluated (deformed) vertex z of the rig's body mesh at `frame` (world)."""
    sc = bpy.context.scene
    keep = sc.frame_current
    if frame is not None and frame != sc.frame_current:
        sc.frame_set(int(frame))
    dg = bpy.context.evaluated_depsgraph_get()
    ob = body(rig).evaluated_get(dg)
    me = ob.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    z = (co @ mw[:3, :3].T + mw[:3, 3])[:, 2].min()
    ob.to_mesh_clear()
    if sc.frame_current != keep:
        sc.frame_set(keep)
    return float(z)


def place(rig, loc, yaw_deg, frame=None):
    """Put the figure's root at loc (x, y, ground z) facing yaw_deg; feet exactly on the ground.
    With frame=None it sets where the timeline starts; with a frame it re-anchors every motion
    that starts at or after that frame (a cut)."""
    st = _state(rig)
    x, y, z = (tuple(loc) + (0.0,))[:3]
    yaw = math.radians(yaw_deg)
    if frame is None:
        st['root0'] = (x, y, z, yaw)
        st['places'] = [p for p in st.get('places', []) if p[0] is not None]
    else:
        st.setdefault('places', []).append((int(frame), (x, y, z, yaw)))
    if st['segs']:
        _bake(rig)
    else:
        rig.location = (x, y, z); rig.rotation_euler = (0, 0, yaw)
    # measure: lowest evaluated vertex must sit on the ground plane. Without motions the rig is
    # in its T-pose rest, which is no stance; motions put the soles on z=0 by construction.
    if not st['segs']:
        return rig
    f = frame if frame is not None else st['segs'][0]['f0']
    dz = z - lowest_z(rig, f)
    if abs(dz) > 1e-4:
        x0, y0, z0, yw = st['root0']
        st['root0'] = (x0, y0, z0 + dz, yw)
        if st['segs']:
            _bake(rig)
        else:
            rig.location.z += dz
    return rig


# ===================================================================== motions

def _times(f0, f1, t0, rate=1.0, t_end=None, mode='clamp'):
    n = f1 - f0 + 1 + EXT
    t = t0 + np.arange(n) / FPS * rate
    if t_end is not None and mode == 'pingpong':
        L = t_end - t0
        u = np.mod(t - t0, 2 * L)
        t = t0 + np.where(u > L, 2 * L - u, u)
    elif t_end is not None:
        t = np.minimum(t, t_end)
    return t


def mocap(rig, f0, f1, take, t0, t_end=None, rate=1.0, root_mode='track', kind=None, blend=10, mode='clamp',
          floor='body', times=None, **flags):
    """Generic: play CMU take `take` from t0 s (file time) at `rate`, frames f0..f1.
    floor='ground' for sitting/getting up (seat or feet define the floor, hands IK'd to it)."""
    if times is None:
        times = _times(f0, f1, t0, rate, t_end, mode)
    clip = _normalise(retarget(CMU / f'{take}.bvh', times, root_mode=root_mode, floor=floor))
    seg = dict(kind=kind or f'mocap_{take}', f0=f0, f1=f1, root=clip['root'], hipsP=clip['hipsP'], Q=clip['Q'], blend=blend)
    for k in ('cL', 'cR', 'chL', 'chR'):
        seg[k] = clip[k]
    if floor == 'ground':
        seg['hands'] = 1.0
        seg['chL'] = seg['chR'] = -1.0          # palms: detect on the mannequin (arms differ)
    seg.update(flags)
    return _add(rig, seg)


# clean standing windows, file time in s (outside them the performers fold hands / step away)
S100 = HR / '100style_neutral'
IDLE_TAKES = {'neutral': (S100 / 'Neutral_ID.bvh', 10.95, 25.85),        # 100STYLE, CC BY 4.0
              'armsbyside': (S100 / 'ArmsBySide_ID.bvh', 9.5, 21.9),     # 100STYLE, CC BY 4.0
              '111_28': (CMU / '111_28.bvh', 0.3, 3.3), '40_10': (CMU / '40_10.bvh', 0.3, 4.4)}
IDLE_DEFAULT = 'neutral'


def _idle_times(rig, f0, n, take):
    """Idle source time on a per-rig clock (frame-locked, ping-pong over the take window), so
    every idle-based segment of a rig samples the same idle at the same frame and crossfades
    between them never jump."""
    _, a, b = IDLE_TAKES[take]
    seed = _state(rig).get('seed', 0.0)
    return a + _pingpong(seed + (f0 - 1 + np.arange(n)) / FPS, b - a)


def _pingpong(t, L, e=0.6):
    """Back-and-forth over [0, L] with eased turnarounds (velocity → 0 over e s at each end),
    so a reversed mocap pass never snaps direction."""
    v = 1.0
    T = L + e                                   # time per pass (ramps lose e/2 of distance each)
    u = np.mod(np.asarray(t, float), 2 * T)
    fwd = u <= T
    x = np.where(fwd, u, u - T)
    pos = np.where(x < e, 0.5 * x * x / e, np.where(x > T - e, L - 0.5 * (T - x) ** 2 / e, x - 0.5 * e))
    return np.where(fwd, pos, L - pos)


# local pitch corrections (deg, + = forward) so the idle looks ahead instead of at the floor
IDLE_POSTURE = {'neutral': {'DEF-spine.003': -3.0, 'DEF-neck': -8.0, 'DEF-head': -9.0},
                'armsbyside': {'DEF-spine.003': -3.0, 'DEF-neck': -8.0, 'DEF-head': -9.0}}


def _idle_clip(rig, f0, f1, take):
    n = f1 - f0 + 1 + EXT
    clip = retarget(IDLE_TAKES[take][0], _idle_times(rig, f0, n, take), root_mode='fixed')
    sk = skel()
    for nm, deg in IDLE_POSTURE.get(take, {}).items():
        b = sk.idx[nm]
        clip['Q'][:, b] = qnorm(_qmul_np(clip['Q'][:, b], _pitch(deg)))
    if IDLE_POSTURE.get(take):
        _floor_calibrate(clip)
    return _normalise(clip)


def idle(rig, f0, f1, take=None, blend=12):
    """Natural standing (CMU standing-still mocap), feet planted, fingers relaxed."""
    st = _state(rig)
    take = take or st.get('idle_take', IDLE_DEFAULT)
    st['idle_take'] = take
    clip = _idle_clip(rig, f0, f1, take)
    seg = dict(kind='idle', f0=f0, f1=f1, root=clip['root'], hipsP=clip['hipsP'], Q=clip['Q'], blend=blend)
    for k in ('cL', 'cR'):
        seg[k] = clip[k]
    return _add(rig, seg)


# ===================================================================== designed arm poses (stop)

def _twist_y(q):
    tw = np.array([q[0], 0.0, q[2], 0.0])
    n = np.linalg.norm(tw)
    return tw / n if n > 1e-9 else np.array([1.0, 0, 0, 0])


def _arm_design(side, wrist, pole, fdir, pnorm, clav_elev=0.0, clav_fwd=0.0, twist_share=1.0):
    """Local quats for shoulder/upper_arm/forearm/hand reaching `wrist` (rest armature space,
    figure facing −Y) with the elbow toward `pole`, fingers along `fdir`, palm facing `pnorm`.
    The elbow is a pure hinge; wrist twist is moved into the forearm (pronation)."""
    sk = skel(); ix = sk.idx; s = side
    sh, ua, fa, hd = (ix[f'DEF-{n}.{s}'] for n in ('shoulder', 'upper_arm', 'forearm', 'hand'))
    sgn = 1.0 if s == 'L' else -1.0
    nz = lambda v: np.asarray(v, float) / np.linalg.norm(v)
    Rc = axis_angle(np.array([0, 0, 1.0]), -sgn * math.radians(clav_fwd)) @ axis_angle(np.array([0, 1.0, 0]), -sgn * math.radians(clav_elev))
    R_sh = Rc @ sk.restR[sh]
    S = sk.restT[sh] + R_sh @ sk.relT[ua]
    l1, l2 = sk.length[ua], sk.length[fa]
    W = np.asarray(wrist, float); d = W - S; dl = np.linalg.norm(d); u = d / dl
    dc = min(dl, (l1 + l2) * 0.999)
    p = np.asarray(pole, float); p = nz(p - p.dot(u) * u)
    a = (l1 * l1 - l2 * l2 + dc * dc) / (2 * dc); h = math.sqrt(max(l1 * l1 - a * a, 0))
    E = S + u * a + p * h; W2 = S + u * dc
    Y1 = (E - S) / l1; f = (W2 - E) / l2
    Z1 = f - f.dot(Y1) * Y1
    Z1 = nz(Z1) if np.linalg.norm(Z1) > 1e-6 else nz(np.cross(p, Y1))
    X1 = np.cross(Y1, Z1)
    R_ua = np.stack([X1, Y1, Z1], 1)
    X2 = X1; Y2 = f; R_fa = np.stack([X2, Y2, np.cross(X2, Y2)], 1)
    Yh = nz(fdir); n = np.asarray(pnorm, float); n = nz(n - n.dot(Yh) * Yh)
    Xh = sgn * n; R_h = np.stack([Xh, Yh, np.cross(Xh, Yh)], 1)
    q_h = m2q((R_fa @ sk.relR[hd]).T @ R_h)
    tw = _twist_y(q_h); ang = 2 * math.atan2(tw[2], tw[0]) * twist_share
    R_fa = R_fa @ axis_angle(np.array([0, 1.0, 0]), ang)
    out = {sk.names[sh]: m2q(sk.restR[sh].T @ R_sh), sk.names[ua]: m2q((R_sh @ sk.relR[ua]).T @ R_ua),
           sk.names[fa]: m2q((R_ua @ sk.relR[fa]).T @ R_fa), sk.names[hd]: m2q((R_fa @ sk.relR[hd]).T @ R_h)}
    info = dict(elbow_flex=math.degrees(math.acos(np.clip(Y1.dot(f), -1, 1))),
                wrist=math.degrees(math.acos(np.clip(f.dot(Yh), -1, 1))), forearm_twist=math.degrees(ang))
    return out, info


def _pitch(deg):
    """Local rotation about +X (spine/neck/head: + bends forward)."""
    a = math.radians(deg) / 2
    return np.array([math.cos(a), math.sin(a), 0, 0])


STOP_POSES = {
    # wrist (x, y, z) rest-armature space; shoulders are at (±0.19, 0.065, 1.44)
    'both': dict(L=dict(wrist=(0.20, -0.42, 1.33), pole=(0.55, 0.25, -1.0), fdir=(0.12, -0.28, 1.0), pnorm=(0.08, -1.0, -0.12),
                        clav_elev=4, clav_fwd=7),
                 R=dict(wrist=(-0.20, -0.42, 1.33), pole=(-0.55, 0.25, -1.0), fdir=(-0.12, -0.28, 1.0), pnorm=(-0.08, -1.0, -0.12),
                        clav_elev=4, clav_fwd=7),
                 spine=2.5, neck=-2.0, head=-3.0),
    'right': dict(R=dict(wrist=(-0.16, -0.46, 1.42), pole=(-0.6, 0.3, -1.0), fdir=(-0.1, -0.25, 1.0), pnorm=(-0.05, -1.0, -0.1),
                         clav_elev=6, clav_fwd=6),
                  spine=1.5, neck=-1.5, head=-3.0),
}


STOP_POSES['fend'] = dict(
    L=dict(wrist=(0.21, -0.33, 1.10), pole=(0.6, 0.4, -1.0), fdir=(0.2, -0.75, 0.65), pnorm=(0.1, -0.65, -0.75), clav_elev=1, clav_fwd=6),
    R=dict(wrist=(-0.21, -0.33, 1.10), pole=(-0.6, 0.4, -1.0), fdir=(-0.2, -0.75, 0.65), pnorm=(-0.1, -0.65, -0.75), clav_elev=1, clav_fwd=6),
    spine=4.0, neck=-2.0, head=-2.0)


def _overlay_arms(seg, pose, strength=0.85):
    """Blend a designed arm pose over a segment (keeps (1-strength) of the source arm motion)."""
    sk = skel()
    q, cfg, info = stop_pose(pose)
    Q = seg['Q']; n = len(Q)
    for nm, qd in q.items():
        b = sk.idx[nm]
        Q[:, b] = qslerp(Q[:, b], np.broadcast_to(qd, (n, 4)), strength)
    opn = _open_hand()
    for nm, qd in opn.items():
        b = sk.idx[nm]
        Q[:, b] = qslerp(Q[:, b], np.broadcast_to(qd, (n, 4)), strength)
    for nm, deg in (('DEF-spine.002', cfg['spine'] * 0.5), ('DEF-spine.003', cfg['spine'] * 0.5), ('DEF-neck', cfg['neck']), ('DEF-head', cfg['head'])):
        b = sk.idx[nm]
        Q[:, b] = qnorm(_qmul_np(Q[:, b], _pitch(deg * strength)))
    seg['Q'] = qcont(Q)
    return seg


def stop_pose(hands='both'):
    key = ('stop', hands)
    if key not in _S:
        cfg = STOP_POSES[hands]
        q = {}
        info = {}
        for s in ('L', 'R'):
            if s in cfg:
                d, inf = _arm_design(s, **cfg[s]); q.update(d); info[s] = inf
        _S[key] = (q, cfg, info)
    return _S[key]


def stop(rig, f0, f1, hands='both', raise_s=0.5, blend=10):
    """Palms-out halt toward the figure's front, held (idle body underneath keeps breathing and
    shifting weight). hands='both' | 'right'."""
    sk = skel(); st = _state(rig)
    take = st.get('idle_take', IDLE_DEFAULT)
    clip = _idle_clip(rig, f0, f1, take)
    Q = clip['Q'].copy(); n = len(Q)
    q, cfg, info = stop_pose(hands)
    t = np.arange(n) / FPS
    w = smoothstep(t / raise_s)
    # slight anticipation: the arms lead, the hands open and the wrists extend a touch later
    w_hand = smoothstep((t - 0.08) / raise_s)
    opn = _open_hand()
    for nm, qd in q.items():
        b = sk.idx[nm]
        ww = w_hand if nm.startswith('DEF-hand') else w
        Q[:, b] = qslerp(Q[:, b], np.broadcast_to(qd, (n, 4)), ww)
    for s in ('L', 'R'):
        if s not in cfg:
            continue
        for nm, qd in opn.items():
            if nm.endswith('.' + s):
                b = sk.idx[nm]
                Q[:, b] = qslerp(Q[:, b], np.broadcast_to(qd, (n, 4)), w_hand)
        # held, not frozen: slow independent drift of shoulder/elbow/wrist (≈1–2°)
        ph = 1.3 if s == 'L' else 0.0
        for nm, amp, fr in ((f'DEF-upper_arm.{s}', 1.2, 0.21), (f'DEF-forearm.{s}', 1.5, 0.17), (f'DEF-hand.{s}', 2.0, 0.27)):
            b = sk.idx[nm]
            a = np.radians(amp) * np.sin(2 * np.pi * fr * t + ph) * w
            Q[:, b] = qnorm(_qmul_np(Q[:, b], np.stack([np.cos(a / 2), np.sin(a / 2), np.zeros(n), np.zeros(n)], 1)))
    for nm, deg in (('DEF-spine.002', cfg['spine'] * 0.5), ('DEF-spine.003', cfg['spine'] * 0.5), ('DEF-neck', cfg['neck']), ('DEF-head', cfg['head'])):
        b = sk.idx[nm]
        Q[:, b] = qnorm(_qmul_np(Q[:, b], qslerp(np.array([1.0, 0, 0, 0]), _pitch(deg), w)))
    seg = dict(kind='stop', f0=f0, f1=f1, root=clip['root'], hipsP=clip['hipsP'], Q=qcont(Q), blend=blend)
    for k in ('cL', 'cR'):
        seg[k] = clip[k]
    return _add(rig, seg)


def _qmul_np(a, b):
    aw, ax, ay, az = np.moveaxis(np.asarray(a, float), -1, 0)
    bw, bx, by, bz = np.moveaxis(np.asarray(b, float), -1, 0)
    return np.stack([aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw], -1)


# ===================================================================== locomotion (walk / jog / back)

def _root_at(rig, f):
    """Root (x, y, yaw) of the current timeline at frame f (before adding a new segment)."""
    st = _state(rig)
    if not st['segs']:
        x, y, z, yaw = st['root0']
        return np.array([x, y, yaw])
    F0, F1, root, *_ = _assemble(rig)
    return root[int(np.clip(f - F0, 0, len(root) - 1))].copy()


def _gait_table(name, res=8):
    """Sample a UAL in-place loop densely: object-space sole centroids and contact masks."""
    key = ('gait', name)
    if key in _S:
        return _S[key]
    sk = skel(); fs = _foot_sets(); c = _S['ual'][name]
    per = c['n'] - 1; fps = c['fps']
    m = per * res
    tau = np.arange(m + 1) / (fps * res)
    hp, Q = _ual_sample(name, tau)
    R, P = sk.fk(hp, Q)
    tab = dict(tau=tau, T=per / fps)
    for s in ('L', 'R'):
        v = sk.verts(R, P, fs[s])
        mz = v[:, :, 2].min(1); cy = v[:, :, 1].mean(1)
        vy = np.gradient(cy, tau)
        stance = (mz < 0.015) & (vy > 0.1)          # carrying the body: drives root advance
        con = mz < 0.012                             # touching (incl. heel strike / toe pivot): locked
        # cyclic clean: tile three cycles, clean, keep the middle one
        cyc = lambda x: _clean_mask(np.concatenate([x[:-1], x[:-1], x]), res * 2, res)[m:2 * m + 1]
        cl = cyc(stance)
        tab['k' + s] = cyc(con).astype(float)
        tab['c' + s] = cl.astype(float)
        tab['y' + s] = cy
        tab['z' + s] = mz
        d = np.diff(np.concatenate([cl[-2:-1], cl]).astype(int))     # toe-off events: 1 → 0
        tab['off' + s] = tau[d < 0]
    _S[key] = tab
    return tab


def _ual_sample(name, tau, fingers=True):
    c = _S['ual'][name]; per = c['n'] - 1
    fr = np.mod(np.asarray(tau, float) * c['fps'], per)
    i0 = np.floor(fr).astype(int); i1 = i0 + 1; a = fr - i0
    hp = c['hipsP'][i0] * (1 - a[:, None]) + c['hipsP'][i1] * a[:, None]
    Q = qslerp(c['Q'][i0], c['Q'][i1], a[:, None])
    if fingers:
        sk = skel()
        for nm, q in _relaxed_hand().items():
            Q[:, sk.idx[nm]] = q
    return hp, Q


class _Gait:
    """Uniform gait source: UAL in-place loop or a retargeted mocap window.
    sample(tau) → hipsP, Q (object space); con[s](tau) stance mask; z[s](tau) lowest sole z;
    offs = sorted toe-off events (time, foot); direction +1 forward / −1 backward."""

    def __init__(self, spec):
        self.spec = spec
        self.direction = spec.get('direction', 1)
        if 'loop' in spec:
            tab = _gait_table(spec['loop'])
            self.T = tab['T']; self.tau = tab['tau']; self.tab = tab
            self.a, self.b = 0.0, None
            ev = [(t, s) for s in ('L', 'R') for t in tab['off' + s]]
            base = sorted(ev)
            self.offs = [(t + k * self.T, s) for k in range(0, 80) for t, s in base]
            self.offs.sort()
        else:
            self._mocap(spec)

    def _mocap(self, spec, rate=60.0):
        key = ('gaitmc', str(spec['bvh']), spec['win'])
        if key not in _S:
            sk = skel(); fs = _foot_sets()
            a, b = spec['win']
            tau = np.arange(a, b, 1.0 / rate)
            clip = retarget(spec['bvh'], tau, root_mode='track', root_sigma=12, yaw_sigma=20)
            R, P = sk.fk(clip['hipsP'], clip['Q'])
            out = dict(tau=tau, hipsP=clip['hipsP'], Q=clip['Q'])
            zs = {}; spd = {}
            for s in ('L', 'R'):
                v = sk.verts(R, P, fs[s]); zs[s] = v[:, :, 2].min(1)
                vw = _world(clip['root'], v)
                low = np.argsort(v[:, :, 2], axis=1)[:, :12]
                c = np.take_along_axis(vw, low[:, :, None], 1).mean(1)
                sp = np.zeros(len(tau)); sp[1:] = np.linalg.norm(np.diff(c[:, :2], axis=0), axis=1) * rate
                spd[s] = gsmooth(sp, 2.0)
            for s, o in (('L', 'R'), ('R', 'L')):
                con = (spd[s] < 0.22) & (zs[s] - np.minimum(zs[s], zs[o]) < 0.03)
                out['c' + s] = _clean_mask(con, 6, 4).astype(float)
                out['z' + s] = zs[s] - np.minimum(zs['L'], zs['R'])
                d = np.diff(out['c' + s].astype(int))
                out['off' + s] = tau[1:][d < 0]
            _S[key] = out
        m = _S[key]
        self.T = None; self.tau = m['tau']; self.tab = m; self.a, self.b = spec['win']
        self.offs = sorted([(t, s) for s in ('L', 'R') for t in m['off' + s]])

    def sample(self, tau):
        if self.T is not None:
            return _ual_sample(self.spec['loop'], tau)
        m = self.tab
        f = np.clip((np.asarray(tau) - self.tau[0]) / (self.tau[1] - self.tau[0]), 0, len(self.tau) - 1.001)
        i0 = np.floor(f).astype(int); al = f - i0
        hp = m['hipsP'][i0] * (1 - al[:, None]) + m['hipsP'][i0 + 1] * al[:, None]
        Q = qslerp(m['Q'][i0], m['Q'][i0 + 1], al[:, None])
        return hp, Q

    def _lookup(self, key, tau):
        if self.T is not None:
            return np.interp(np.mod(tau - self.tau[0], self.T), self.tau, self.tab[key])
        return np.interp(tau, self.tau, self.tab[key])

    def con(self, s, tau):
        return self._lookup('c' + s, tau) > 0.5

    def z(self, s, tau):
        return np.clip(self._lookup('z' + s, tau), 0, None)


def _bezier(S, E, t0, t1, n=400):
    """Cubic Bézier from S to E with unit tangents t0, t1; returns arc-length table."""
    S = np.asarray(S, float); E = np.asarray(E, float)
    L = np.linalg.norm(E - S)
    h = L / 3.0
    P1 = S + np.asarray(t0) * h; P2 = E - np.asarray(t1) * h
    u = np.linspace(0, 1, n)[:, None]
    pts = (1 - u) ** 3 * S + 3 * (1 - u) ** 2 * u * P1 + 3 * (1 - u) * u ** 2 * P2 + u ** 3 * E
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    sl = np.concatenate([[0], np.cumsum(seg)])
    tan = np.gradient(pts, axis=0)
    yaw = unwrap_yaw(np.arctan2(tan[:, 0], -tan[:, 1]))
    return sl, pts, yaw


def _yaw_dir(yaw):
    return np.array([math.sin(yaw), -math.cos(yaw)])


LOCO_SIGMA = 1.0
LOCO_K_ENDS = True
GAITS = {
    'walk': dict(loop='Walk_Loop', first='R', cad=(0.85, 1.25), sink=0.015),
    'jog': dict(loop='Jog_Fwd_Loop', first='R', cad=(0.7, 1.1), flight=True),   # unused: dirty loop
    # hurried rush: the walk loop at a quick cadence, lower pelvis, leaning into it
    'rush': dict(loop='Walk_Loop', first='R', cad=(1.3, 1.55), sink=0.035, lean=8.0, min_cad=True),
    # CMU 136_25: steady straight backward walk (~0.5 m/s), file time window
    'back': dict(bvh=CMU / '136_25.bvh', win=(1.2, 13.0), first=None, cad=(0.8, 1.35), direction=-1, widen=0.035),
}


def _locomote(rig, f0, f1, start, end, end_yaw, gait='walk', kind='walk', blend=8, k_range=(0.6, 1.3),
              settle=0.5, pre=0.1, max_cad=None, start_after=0.0):
    """Shared locomotion builder. Root follows a cubic Bézier from the current root to `end`;
    arc length advances with the planted foot's object-space motion (no slide by construction);
    the gait source is blended in over the first swing and out over the last, into the rig's
    idle (shared clock). Distance remainder goes into the first/last steps (stride scale k)."""
    sk = skel(); st = _state(rig)
    g = GAITS[gait]; G = _Gait(g); dirn = G.direction
    take = st.setdefault('idle_take', IDLE_DEFAULT)
    cur = _root_at(rig, f0)
    S = np.array(start[:2], float) if start is not None else cur[:2]
    E = np.array(end[:2], float)
    yaw0 = cur[2] if start is None or len(start) < 4 else math.radians(start[3])
    d = E - S; L = float(np.linalg.norm(d))
    ddir = d / max(L, 1e-9)
    t0 = _yaw_dir(yaw0) * dirn                              # travel direction at the start
    if L < 1e-3 or t0.dot(ddir) < math.cos(math.radians(100)):
        t0 = ddir
    yaw_face_end = (math.atan2(ddir[0], -ddir[1]) + (math.pi if dirn < 0 else 0.0)) if end_yaw is None else math.radians(end_yaw)
    t1 = _yaw_dir(yaw_face_end) * dirn
    if t1.dot(ddir) < math.cos(math.radians(100)):
        t1 = ddir
    sl, pts, pyaw = _bezier(S, E, t0, t1)
    if dirn < 0:
        pyaw = pyaw + math.pi
    Lp = sl[-1]
    pyaw = pyaw + 2 * math.pi * round((yaw0 - pyaw[0]) / (2 * math.pi))
    # toe-off events: first swing foot
    evs = G.offs
    i0 = 0
    if G.T is not None and g.get('first'):
        i0 = next(i for i, (t_, s_) in enumerate(evs) if s_ == g['first'])
    else:
        i0 = next(i for i, (t_, s_) in enumerate(evs) if t_ >= G.a + start_after + 0.2)
    ev_t = np.array([t_ for t_, _ in evs[i0:]])
    n_fr = f1 - f0 + 1
    avail = n_fr / FPS - pre - settle
    stand = _idle_clip(rig, f0, f1, take)                   # shared idle clock

    def build(nsteps, cad, k):
        N = n_fr + EXT
        t = np.arange(N) / FPS
        tg = np.clip(t - pre, 0, None)
        dur = (ev_t[nsteps] - ev_t[0]) / cad
        sw0 = (ev_t[1] - ev_t[0]) / cad; sw1 = (ev_t[nsteps] - ev_t[nsteps - 1]) / cad
        tau = ev_t[0] + np.minimum(tg, dur) * cad
        w = smoothstep(tg / sw0) * (1 - smoothstep((tg - (dur - sw1)) / sw1))
        w = np.where(t < pre, 0.0, w)
        walking = (t >= pre) & (tg <= dur)
        ghp, gQ = G.sample(tau)
        ghp = ghp - np.array([0, 0, g.get('sink', 0.0)])
        if g.get('lean'):
            for nm_, k_ in (('DEF-spine.001', 0.4), ('DEF-spine.002', 0.4), ('DEF-neck', -0.5)):
                b_ = sk.idx[nm_]
                gQ[:, b_] = qnorm(_qmul_np(gQ[:, b_], _pitch(g['lean'] * k_)))
        hp = stand['hipsP'][:N] * (1 - w[:, None]) + ghp * w[:, None]
        Q = qslerp(stand['Q'][:N], gQ, w[:, None])
        cont = {}; lift = {}
        first_sw = walking & (tg < sw0)
        last_sw = walking & (tg >= dur - sw1)
        f_first = evs[i0][1]; f_last = evs[i0 + nsteps - 1][1]
        for s_ in ('L', 'R'):
            gc = G.con(s_, tau)
            sc = stand['c' + s_][:N] > 0.5
            c_ = np.where(walking, gc, sc)
            # during the blended first/last swing the other foot carries the body: keep it planted
            if s_ != f_first:
                c_ = c_ | first_sw
            if s_ != f_last:
                c_ = c_ | last_sw
            else:
                c_ = c_ | (last_sw & (w < 0.12))
            cont[s_] = c_.astype(float)
            # swing clearance: at least the source's own swing height (lost when blending toward
            # the planted stand pose) and a quick lift-off/landing ramp
            gz = G.z(s_, tau)
            dist = np.full(N, 99.0)
            idx = np.nonzero(c_)[0]
            if len(idx):
                dist = np.abs(np.arange(N)[:, None] - idx[None, :]).min(1).astype(float)
            ramp = 0.022 * smoothstep((dist + 0.6) / 2.6)
            lift[s_] = np.where(walking & ~c_, np.maximum(ramp, gz * (w < 0.999)), 0.0)
        if not g.get('flight'):
            # walking always has a supporting foot: where detection left none, plant the lower one
            none = (cont['L'] < 0.5) & (cont['R'] < 0.5)
            if none.any():
                zl, zr = G.z('L', tau), G.z('R', tau)
                pickL = none & (zl <= zr); pickR = none & (zr < zl)
                cont['L'] = np.where(pickL, 1.0, cont['L']); cont['R'] = np.where(pickR, 1.0, cont['R'])
                lift['L'] = np.where(pickL, 0.0, lift['L']); lift['R'] = np.where(pickR, 0.0, lift['R'])
        clip_ = dict(hipsP=hp, Q=Q)
        _floor_calibrate_feet(clip_, cont)
        R, P = sk.fk(clip_['hipsP'], Q)
        fs = _foot_sets()
        ds = np.zeros(N); nds = np.zeros(N)
        for s_ in ('L', 'R'):
            v = sk.verts(R, P, fs[s_])
            for i in range(1, N):
                if cont[s_][i] > 0.5 and cont[s_][i - 1] > 0.5:
                    m = (v[i, :, 2] < 0.012) & (v[i - 1, :, 2] < 0.012)
                    if m.sum() >= 3:
                        ds[i] += (v[i, m, 1] - v[i - 1, m, 1]).mean(); nds[i] += 1
        ds = np.where(nds > 0, ds / np.maximum(nds, 1), np.nan) * dirn
        ok = np.isfinite(ds)
        ds = np.interp(np.arange(N), np.nonzero(ok)[0], ds[ok]) if ok.any() else np.zeros(N)
        ds = gsmooth(np.clip(ds, 0, None), LOCO_SIGMA)
        ds = np.where(t < pre, 0.0, ds)
        kk = np.where(w < 0.999, k, 1.0) if LOCO_K_ENDS else np.full(N, k)
        s_arc = np.cumsum(ds * kk)
        cont['liftL'], cont['liftR'] = lift['L'], lift['R']
        return t, tau, w, walking, dur, clip_['hipsP'], Q, cont, s_arc

    max_steps = len(ev_t) - 1
    _, _, _, _, _, _, _, _, s2 = build(2, 1.0, 1.0)
    s_two = s2[-1]
    _, _, _, _, _, _, _, _, s4 = build(min(4, max_steps), 1.0, 1.0)
    step_len = (s4[-1] - s_two) / 2
    cmin, cmax = g['cad']
    if max_cad:
        cmax = max_cad
    best = None
    for nsteps in range(2, max_steps + 1):
        k = (Lp - (nsteps - 2) * step_len) / max(s_two, 1e-6)
        need = (ev_t[nsteps] - ev_t[0])
        cad = max(cmin, need / max(avail, 1e-3)) if (need / max(avail, 1e-3) > 1.0 or g.get('min_cad')) else 1.0
        if cad > cmax or not (k_range[0] <= k <= k_range[1]):
            continue
        cost = abs(math.log(k / 0.9)) * 2 + abs(math.log(cad)) * 1.5
        if best is None or cost < best[0]:
            best = (cost, nsteps, cad, k)
    if best is None:
        nsteps = int(np.clip(round((Lp - s_two) / max(step_len, 1e-3)) + 2, 2, max_steps))
        cad = min(cmax, max(1.0, (ev_t[nsteps] - ev_t[0]) / max(avail, 1e-3)))
        best = (0, nsteps, cad, (Lp - (nsteps - 2) * step_len) / max(s_two, 1e-6))
        print(f'people2: {kind} {rig.name} {f0}-{f1}: {Lp:.2f} m does not fit comfortably '
              f'(steps {nsteps}, end-step stride x{best[3]:.2f}, cadence x{cad:.2f})')
    _, nsteps, cad, k = best
    t, tau, w, walking, dur, hp, Q, cont, s_arc = build(nsteps, cad, k)
    for _ in range(2):                                      # exact arc length (k on end steps)
        kn = k + (Lp - s_arc[-1]) / max(s_two, 1e-6)
        if abs(kn - k) < 1e-4:
            break
        k = kn
        t, tau, w, walking, dur, hp, Q, cont, s_arc = build(nsteps, cad, k)
    s_arc = s_arc * Lp / max(s_arc[-1], 1e-6)
    pos = np.stack([np.interp(s_arc, sl, pts[:, 0]), np.interp(s_arc, sl, pts[:, 1])], 1)
    yaw = np.interp(s_arc, sl, pyaw)
    root = np.concatenate([pos, yaw[:, None]], 1)
    seg = dict(kind=kind, f0=f0, f1=f1, start=(0.0, 0.0, 0.0), root=root, hipsP=hp, Q=qcont(Q),
               blend=blend, cL=cont['L'], cR=cont['R'], clearL=cont['liftL'], clearR=cont['liftR'], w=w,
               widenL=_hold_in_stance(g.get('widen', 0.0) * w, cont['L']), widenR=_hold_in_stance(g.get('widen', 0.0) * w, cont['R']),
               info=dict(steps=nsteps, cadence=round(cad, 3), end_stride=round(float(k), 3), path=round(float(Lp), 3),
                         walk_s=round(float(dur), 2), end_frame=f0 + int(round((pre + dur) * FPS))))
    st['last_loco'] = seg['info']
    return seg


def _hold_in_stance(v, contact):
    """Hold a per-foot offset constant while that foot is planted (changes only in the air)."""
    v = np.asarray(v, float).copy()
    for a, b in _runs(np.asarray(contact) > 0.5):
        v[a:b + 1] = v[a]
    return gsmooth(v, 0.5) if len(v) > 2 else v


def walk_to(rig, f0, f1, start, end, end_yaw=None, blend=8):
    """Walk from `start` (x, y; None = where the figure stands at f0) to `end` (x, y) with planted
    feet, ending settled facing end_yaw (deg; default: the walking direction). Steps/cadence are
    fitted to the distance and frame budget; with a generous budget it arrives early and stands."""
    return _add(rig, _locomote(rig, f0, f1, start, end, end_yaw, gait='walk', kind='walk', blend=blend))


def step_back(rig, f0, f1, dist=0.7, hands='fend', blend=14):
    """Two or three steps straight backwards (CMU 136_25 backward walk, retargeted), as if
    yielding to a slowly advancing bumper, then settle facing the same way. hands='fend' keeps
    the hands low and forward toward the car; 'down' leaves the mocap arm swing."""
    cur = _root_at(rig, f0)
    back = -_yaw_dir(cur[2])
    end = cur[:2] + back * dist
    seg = _locomote(rig, f0, f1, None, end, math.degrees(cur[2]), gait='back', kind='step_back', blend=blend)
    if hands == 'fend':
        _overlay_arms(seg, 'fend')
    return _add(rig, seg)


# ===================================================================== on the ground

SIT_TAKE = '111_06'
SIT_WIN = (4.0, 5.6)       # seated after the (unseen) fall, leaning back on the left hand, dazed
GETUP_END = 11.0           # 111_06: rolls onto hands and knees, squats, stands (6.3–10.5 s)


def sit_ground(rig, f0, f1, rate=0.8, blend=10):
    """Seated on the asphalt after a fall, dazed (CMU 111_06 3.4–6.1 s, played slowly back and
    forth with eased turnarounds). Seat, heels and the supporting palm rest on the ground.
    Place the figure first (place(rig, loc, yaw, frame=f0)) – the fall itself is never shown."""
    st = _state(rig)
    a, b = SIT_WIN
    n = f1 - f0 + 1 + EXT
    times = a + _pingpong(np.arange(n) / FPS * rate, b - a)
    raw = retarget(CMU / f'{SIT_TAKE}.bvh', times, root_mode='fixed', floor='ground')
    raw_root = raw['root'].copy()
    clip = _normalise(raw)
    seg = dict(kind='sit_ground', f0=f0, f1=f1, root=clip['root'], hipsP=clip['hipsP'], Q=clip['Q'], blend=blend,
               cL=-1.0, cR=-1.0, hands=1.0)
    st['sit'] = dict(f0=f0, times=times, raw_root=raw_root)
    return _add(rig, seg)


def get_up(rig, f0, f1, blend=10, settle=0.6):
    """From the seated pose to standing (continues CMU 111_06: turns onto hands and knees,
    squats, stands; the source's marker glitch at 9.6 s is smoothed). Timing is fitted to the
    frame range (0.8–1.25×); any spare time is spent standing (idle)."""
    sk = skel(); st = _state(rig)
    sit = st.get('sit')
    if sit is not None and sit['f0'] <= f0 < sit['f0'] + len(sit['times']):
        t_start = float(sit['times'][f0 - sit['f0']])
    else:
        t_start, sit = 6.0, None
    n_fr = f1 - f0 + 1
    span = GETUP_END - t_start
    rate = float(np.clip(span / max(n_fr / FPS - settle, 0.1), 0.8, 1.25))
    N = n_fr + EXT
    tt = np.arange(N) / FPS
    # ease in from the (slow, possibly reversing) seated playback
    ramp = 0.5
    adv = np.where(tt < ramp, rate * tt * tt / (2 * ramp), rate * (tt - ramp / 2))
    times = np.minimum(t_start + adv, GETUP_END + 0.5)
    raw = retarget(CMU / f'{SIT_TAKE}.bvh', times, root_mode='track', floor='ground')
    # start where the seated segment's root says this source frame is (no slide at the hand-off)
    cur = _root_at(rig, f0)
    if sit is not None:
        rs = sit['raw_root'][f0 - sit['f0']]
        rg = raw['root'][0]
        dxy = rotz(-rs[2])[:2, :2] @ (rg[:2] - rs[:2])
        start = _compose(tuple(cur), np.array([[dxy[0], dxy[1], rg[2] - rs[2]]]))[0]
    else:
        start = cur
    clip = _normalise(raw)
    # settle into the shared-clock idle once standing
    done = times >= GETUP_END - 1e-6
    t_done = tt[np.argmax(done)] if done.any() else tt[-1]
    w = smoothstep((tt - t_done + 0.1) / settle)
    stand = _idle_clip(rig, f0, f1, st.setdefault('idle_take', IDLE_DEFAULT))
    hp = clip['hipsP'] * (1 - w[:, None]) + stand['hipsP'][:N] * w[:, None]
    Q = qslerp(clip['Q'], stand['Q'][:N], w[:, None])
    cont = {}
    for s in ('L', 'R'):            # on the ground the performer's floor is unreliable: detect on the mannequin
        cont[s] = np.where(w > 0.5, stand['c' + s][:N], -1.0)
    seg = dict(kind='get_up', f0=f0, f1=f1, start=tuple(start), root=clip['root'], hipsP=hp, Q=qcont(Q), blend=blend,
               cL=cont['L'], cR=cont['R'], hands=np.clip(1 - w * 2, 0, 1),
               info=dict(t_start=round(t_start, 2), rate=round(rate, 3), standing_frame=f0 + int(round(t_done * FPS))))
    st['last_getup'] = seg['info']
    return _add(rig, seg)


# ===================================================================== driver (accord_2019)
#
# Measured in the accord_2019 asset as placed by world2.car() (car-local, front = +X, left = +Y),
# by ray casts (figtest/probe_car*.py): steering wheel rim centre (0.45, 0.389, 0.821), radius
# ~0.165, plane tilted 16° (normal toward the driver (−0.96, 0, 0.28)); cabin floor z 0.22;
# roof lining ~1.40–1.41 above the driver; door inner face y ≈ 0.90 (0.75 at shoulder height).
# The model has NO seats and no dashboard underside, so driver_seat() can add a simple seat.

ACCORD = dict(wheel_c=(0.45, 0.389, 0.821), wheel_n=(-0.96, 0.0, 0.28), wheel_r=0.165, floor_z=0.22, roof_z=1.40)
# fitted by grid search (figtest/t_drive_grid.py): elbows ~40°, knees ~75°, head 5 cm under the
# roof lining, legs 9 cm clear of wheel/column, no mesh overlap except the fists on the rim
DRIVER_FIT = dict(hip=(0.04, 0.389, 0.47), recline=0.0, neck=-6.0, foot_x=0.68, foot_dy=0.11, grip_deg=58.0,
                  grip_open=0.2)


def _grip_points(fit=DRIVER_FIT, car=ACCORD):
    c = np.array(car['wheel_c']); n = np.array(car['wheel_n']); n /= np.linalg.norm(n)
    up = np.array([0, 0, 1.0]) - n * n[2]; up /= np.linalg.norm(up)
    lat = np.cross(n, up); lat = lat if lat[1] > 0 else -lat           # +Y (driver's left)
    a = math.radians(fit['grip_deg'])
    out = {}
    for s, sg in (('L', 1.0), ('R', -1.0)):
        out[s] = c + car['wheel_r'] * (math.sin(a) * sg * lat + math.cos(a) * up)
    return out


def drive(rig, f0, f1, car=None, fit=None, blend=8):
    """Seated driver gripping the wheel (UAL Driving_Loop, refitted to the accord_2019 cabin:
    hips at the measured H-point, legs to the footwell, hands IK'd to the rim at 10-and-2).
    The rig must be parented to the car (car-local placement e.g. (-0.30, 0.37, 0), yaw 90°,
    as in shots2.lot()); pass car= to parent and place it here."""
    sk = skel(); st = _state(rig); ix = sk.idx
    fit = dict(DRIVER_FIT, **(fit or {}))
    if car is not None:
        rig.parent = car; rig.matrix_parent_inverse.identity()
        rig.location = (-0.30, 0.37, 0.0); rig.rotation_euler = (0, 0, math.radians(90))
        st['root0'] = (-0.30, 0.37, 0.0, math.radians(90))
    x0, y0, z0, yaw0 = st['root0']
    M = np.array(Matrix.Translation((x0, y0, z0)) @ Matrix.Rotation(yaw0, 4, 'Z'))
    Mi = np.linalg.inv(M)
    to_obj = lambda p: (Mi @ np.append(p, 1.0))[:3]
    n = f1 - f0 + 1 + EXT
    tau = (f0 - 1 + np.arange(n)) / FPS
    hp, Q = _ual_sample('Driving_Loop', tau, fingers=False)
    if fit.get('grip_open'):         # the UAL fist is curled tighter than the rim tube
        for nm in sk.names:
            if nm.startswith(('DEF-f_', 'DEF-thumb')):
                Q[:, ix[nm]] = qslerp(Q[:, ix[nm]], np.array([1.0, 0, 0, 0]), fit['grip_open'])
    # recline: pitch the pelvis back (whole body rotates), counter-flex neck/head to keep eyes level
    Q[:, ix['DEF-hips']] = qnorm(_qmul_np(Q[:, ix['DEF-hips']], _pitch(-fit['recline'])))
    for nm, k in (('DEF-neck', 0.5), ('DEF-head', 0.5)):
        Q[:, ix[nm]] = qnorm(_qmul_np(Q[:, ix[nm]], _pitch(fit['recline'] * 0.6 * k + fit['neck'] * k)))
    R, P = sk.fk(hp, Q)
    mid = 0.5 * (P[:, ix['DEF-thigh.L']] + P[:, ix['DEF-thigh.R']])
    hp = hp + (to_obj(np.array(fit['hip'])) - mid)
    grips = _grip_points(fit)
    tg = dict(hand_local=True)
    # wrist targets such that the fist (grip centroid) closes around the rim point: iterate IK
    fs = _foot_sets()
    R0, P0 = sk.fk(hp[:1], Q[:1])
    for s, sg in (('L', 1.0), ('R', -1.0)):
        ua, fa, hd = ix[f'DEF-upper_arm.{s}'], ix[f'DEF-forearm.{s}'], ix[f'DEF-hand.{s}']
        rim = to_obj(grips[s]); T = rim.copy()
        for _ in range(6):
            R1 = R0.copy()
            rel = R1[0, fa].T @ R1[0, hd]
            _ik2(R1, P0, sk, ua, fa, T[None], np.ones(1))
            R1[0, hd] = R1[0, fa] @ rel
            P1 = sk.fk(hp[:1], sk.local(R1))[1]
            cen = sk.verts(R1, P1, fs['hand' + s])[0].mean(0)
            T = T + (rim - cen)
        tg['hand' + s] = (np.broadcast_to(T, (n, 3)).copy(), np.ones(n))
        ank = np.array([fit['foot_x'], fit['hip'][1] + sg * fit['foot_dy'], ACCORD['floor_z'] + 0.105])
        tg['foot' + s] = (np.broadcast_to(to_obj(ank), (n, 3)).copy(), np.ones(n))
    seg = dict(kind='drive', f0=f0, f1=f1, root=np.zeros((n, 3)), hipsP=hp, Q=qcont(Q), blend=blend,
               nofeet=1.0, cL=0.0, cR=0.0, targets=tg, start=None)
    return _add(rig, seg)


def _box(name, size, loc, rot, mat, parent, bevel=0.02):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.parent = parent; o.matrix_parent_inverse.identity()
    o.location = loc; o.rotation_euler = rot
    me.materials.append(mat)
    if bevel:
        md = o.modifiers.new('bevel', 'BEVEL'); md.width = bevel; md.segments = 3
        o.modifiers.new('sub', 'SUBSURF').levels = 1
    for poly in me.polygons:
        poly.use_smooth = True
    return o


def driver_seat(car, rig=None, frame=None, passenger=True):
    """The accord_2019 asset has no seats: add simple charcoal front seats (cushion, reclined
    back, headrest) fitted under/behind the driving mannequin (and a mirrored passenger seat)."""
    fit = DRIVER_FIT
    hx, hy, hz = fit['hip']
    cushion_top = hz - 0.115; back_x = hx - 0.17; tilt = math.radians(14)
    if rig is not None:
        sk = skel(); fs = _foot_sets(); st = _state(rig)
        b = st['baked']; k = 0 if frame is None else int(np.clip(frame - b['F0'], 0, len(b['Q']) - 1))
        R, P = sk.fk(b['hipsP'][k:k + 1], b['Q'][k:k + 1])
        M = np.array(rig.matrix_basis)
        allv = sk.verts(R, P, np.arange(len(sk.vrest)))[0] @ M[:3, :3].T + M[:3, 3]
        seatv = sk.verts(R, P, fs['seat'])[0] @ M[:3, :3].T + M[:3, 3]
        cushion_top = float(seatv[:, 2].min()) + 0.004            # cushion compresses a few mm
        torso = [sk.idx[n] for n in ('DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003')]
        tv = allv[np.isin(sk.dom, torso)]
        # backrest plane: tilted by the torso lean, just behind its rearmost point
        a = P[0, sk.idx['DEF-spine.001']] @ M[:3, :3].T + M[:3, 3]; c = P[0, sk.idx['DEF-neck']] @ M[:3, :3].T + M[:3, 3]
        tilt = math.atan2(-(c[0] - a[0]), c[2] - a[2])
        nrm = np.array([math.cos(tilt), 0, math.sin(tilt)])
        back_x = float(((tv - np.array([0, 0, cushion_top])) @ nrm).min()) / math.cos(tilt)
    fab = bpy.data.materials.get('seat_fabric')
    if fab is None:
        fab = bpy.data.materials.new('seat_fabric'); fab.use_nodes = True
        bb = fab.node_tree.nodes['Principled BSDF']
        bb.inputs['Base Color'].default_value = (0.022, 0.022, 0.024, 1); bb.inputs['Roughness'].default_value = 0.88
    objs = []
    for nm, y in (('drv', hy),) + ((('pas', -hy),) if passenger else ()):
        cl = 0.50                                                      # cushion length
        cx = back_x + 0.02 + cl / 2
        objs.append(_box(f'seat_{nm}_cushion', (cl, 0.50, 0.11), (cx, y, cushion_top - 0.055), (0, math.radians(-6), 0), fab, car))
        objs.append(_box(f'seat_{nm}_base', (0.40, 0.42, cushion_top - 0.11 - ACCORD['floor_z']), (cx, y, (cushion_top - 0.11 + ACCORD['floor_z']) / 2), (0, 0, 0), fab, car, bevel=0.01))
        bh = 0.60
        bc = np.array([back_x, y, cushion_top]) + np.array([-math.sin(tilt), 0, math.cos(tilt)]) * (bh / 2 + 0.03) - np.array([math.cos(tilt), 0, math.sin(tilt)]) * 0.055
        objs.append(_box(f'seat_{nm}_back', (0.10, 0.50, bh), tuple(bc), (0, -tilt, 0), fab, car))
        hc = np.array([back_x, y, cushion_top]) + np.array([-math.sin(tilt), 0, math.cos(tilt)]) * (bh + 0.16) - np.array([math.cos(tilt), 0, math.sin(tilt)]) * 0.07
        objs.append(_box(f'seat_{nm}_headrest', (0.08, 0.26, 0.17), tuple(hc), (0, -tilt, 0), fab, car))
    return objs


def jog_in(rig, f0, f1, start, end, end_yaw=None, blend=6):
    """A few quick, hurried steps from the current root (or `start`) to `end`, leaning in, then
    settle (UAL Walk_Loop at 1.3–1.55× cadence; the UAL jog loop's contacts are unusable)."""
    return _add(rig, _locomote(rig, f0, f1, start, end, end_yaw, gait='rush', kind='jog_in', blend=blend,
                               k_range=(0.6, 1.5), settle=0.4))
