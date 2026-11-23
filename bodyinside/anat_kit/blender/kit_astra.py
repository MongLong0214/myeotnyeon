"""The person for the neck episode: Astra's human (anat_kit/astra_human/human_final.blend, MakeHuman/MPFB CC0 assets + Mixamo mocap, see astra_human/SOURCES.md) and the skeleton slave.
Retimed with NLA strips: opening action 1-84 at f0-83 (60-frame opening + 24-frame dissolve), payoff action 61-85 at f846-870, hold on the peak to f968, straighten 85-126 at f968-1009.
anchors.json (per editorial frame skull/vertebra maps into the posed human) drives the skeleton: the chain root follows C7's rigid part, the cervical angles + head slide are solved so the skull follows
the skull map. The human is never moved or scaled (anchors are in the same world frame)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_paths import asset
import bpy, math, os, json, hashlib
from mathutils import Vector, Matrix, Quaternion
D = bpy.data
AH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'astra_human')
BLEND = asset('astra_human/human_final.blend'); ANCH = AH + '/anchors.json'
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def E_OF(f):
    """episode frame -> editorial (action) frame"""
    if f <= 114: return min(1 + f, 108)
    if f < 816: return 126
    if f <= 840: return 61 + (f - 816)
    if f <= 968: return int(round(76 + 10 * (f - 841) / 127.0))
    if f <= 1009: return 85 + (f - 968)
    return 126
K = 1.05   # the person is scaled 5 % about the origin: the BodyParts3D skeleton is ~5-12 % larger than the character's fitted skull (anchors.json maps carry that scale), this keeps it inside the skin
SC = Matrix.Diagonal((K, K, K, 1.0))
class Astra:
    def __init__(self, scene, link): self.sc = scene; self.link = link
    def load(self):
        with D.libraries.load(BLEND, link=False) as (src, dst):
            dst.collections = ['Human | character']
        col = D.collections['Human | character']; self.sc.collection.children.link(col)
        self.objs = list(col.all_objects); self.rig = D.objects['HumanRig']; self.root = D.objects['HumanRoot']; self.root.scale = (K, K, K)
        provenance = 'astra:%s|mocap:%s:%s' % (sha(BLEND), sha(asset('assets/mocap/Texting While Standing.fbx')), sha(asset('assets/mocap/Looking Down.fbx')))
        for o in self.objs:
            if o.type in ('MESH', 'CURVES', 'CURVE'): o['src'] = provenance
        self.anch = json.load(open(ANCH)); self.A = {}
        for r in self.anch['frames'] + self.anch['opening_tail_frames']:
            if r['frame'] not in self.A or r['frame'] > 60 and r in self.anch['opening_tail_frames']: pass
        self.A_open = {r['frame']: r for r in self.anch['frames'] if r['frame'] <= 60}; self.A_open.update({r['frame']: r for r in self.anch['opening_tail_frames']})
        self.A_pay = {r['frame']: r for r in self.anch['frames'] if r['frame'] >= 61}
        return self
    def rec(self, f):
        e = E_OF(f); return (self.A_open if f <= 114 else self.A_pay)[e]
    def retime(self):
        """NLA: rebuild the tracks of the rig and the phone empty with the episode timing"""
        for ob in (self.rig, D.objects['Phone | animated contact frame']):
            ad = ob.animation_data; sfx = ' | handset' if ob is not self.rig else ''
            op = D.actions['Opening | screen drift' + sfx]; pa = D.actions['Payoff | return to neutral' + sfx]
            for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
            ad.action = None; tr = ad.nla_tracks.new(); tr.name = 'Episode shots'
            def strip(name, act, a0, a1, f0, f1):
                s = tr.strips.new(name, int(f0), act); s.action_frame_start = a0; s.action_frame_end = a1; s.frame_start = f0; s.scale = (f1 - f0) / float(a1 - a0); s.extrapolation = 'NOTHING'; s.blend_type = 'REPLACE'; return s
            s0 = strip('opening', op, 1, 84, 0, 83); s0.extrapolation = 'HOLD'
            strip('payoff-in', pa, 61, 85, 816, 840); strip('peak-hold', pa, 76, 86, 841, 968); strip('straighten', pa, 85, 126, 969, 1010).extrapolation = 'HOLD_FORWARD'
    def vis(self, vis, ranges):
        for o in self.objs:
            if o.type in ('MESH', 'CURVES', 'CURVE'): vis(o, ranges)
    def fades(self, vkey, keys):
        """alpha fade on every material: Mix(Transparent, shader) in front of each material output, driven by one Value node per material, keyed like `keys`"""
        done = []
        mats = {m for o in self.objs if o.type in ('MESH', 'CURVES', 'CURVE') for m in o.data.materials if m}
        for m in mats:
            nt = m.node_tree
            for out in [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']:
                lk = out.inputs['Surface'].links
                if not lk: continue
                src = lk[0].from_socket; mix = nt.nodes.new('ShaderNodeMixShader'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); fd = nt.nodes.new('ShaderNodeValue'); fd.name = 'Fade'
                nt.links.new(fd.outputs[0], mix.inputs['Fac']); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(src, mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs['Surface']); done.append(fd)
        for fd in done:
            for f, v in keys: vkey(fd, f, v)
        return done
    # ---------------------------------------------------------------- skeleton slave
    @staticmethod
    def rigid(M, c):
        q = M.to_3x3().to_quaternion(); Rr = q.to_matrix().to_4x4(); t = (M @ c) - (Rr @ c); Rr.translation = t; return Rr
    def root_matrix(self, f, c7_rest):
        r = self.rec(f); return self.rigid(SC @ Matrix(r['bp3d_vertebra_to_world']['C7']), c7_rest)
    def derive(self, frames, chain_mats, P_C, shape, fa, c_pt, c7_rest):
        c_pt = Vector(c_pt); fa = list(fa); sP = sum(P_C); out = {}; err = []; raw = {}
        def angles(lam, theta):
            base = [p + lam * s for p, s in zip(P_C, shape)]; tot = sP + theta - sum(base); return [b + a * tot for b, a in zip(base, fa)]
        for f in frames:
            r = self.rec(f); Sm = SC @ Matrix(r['bp3d_skull_to_world']); R = self.root_matrix(f, c7_rest); Ri = R.inverted()
            tgt = Ri @ (Sm @ (c_pt + Vector((0, 0.012, 0.014))));  # (nudged up/back inside the head: the jaw stood out under the chin)
            Rs = Sm.to_3x3().to_quaternion().to_matrix().to_4x4(); Rrel = Ri.to_3x3().to_4x4() @ Rs; theta = math.degrees(math.atan2(Rrel[2][1], Rrel[1][1]))
            def res(lam, sl): return chain_mats(angles(lam, theta), sl)[8] @ c_pt - tgt
            best = None
            for lam in [x * 0.1 for x in range(-3, 18)]:
                sl = max(-0.25, min(0.25, -res(lam, 0.0).y)); rr = res(lam, sl); e = abs(rr.z) + 0.3 * abs(rr.y)
                if best is None or e < best[0]: best = (e, lam)
            raw[f] = (best[1], theta, tgt)
        fl = sorted(raw)
        for i, f in enumerate(fl):
            nb = [raw[g][0] for g in fl[max(0, i - 3):i + 4]]; lam = sum(nb) / len(nb); theta = raw[f][1]; tgt = raw[f][2]
            r0 = chain_mats(angles(lam, theta), 0.0)[8] @ c_pt - tgt; sl = max(-0.25, min(0.25, -r0.y)); r = chain_mats(angles(lam, theta), sl)[8] @ c_pt - tgt
            err.append(math.hypot(r.y, r.z)); out[f] = (angles(lam, theta), sl)
        print('ASTRA derive: %d frames, skull-point error cm: mean %.2f max %.2f' % (len(frames), 100 * sum(err) / len(err), 100 * max(err)))
        return out
