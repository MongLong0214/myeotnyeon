"""MPFB2 human (CC0) + retargeted Mixamo mocap in the neck scene (see mpfb_make.py, mpfb_mocap.py, assets/mpfb/human_mpfb_mocap.blend).
The human is the visible PERSON; the BodyParts3D skeleton is the slave: its chain root follows the human's upper-back bone and the angles of the cervical chain +
a head slide are SOLVED so the skull sits on the human's head bone at every frame (so the dissolve person -> x-ray lines up).
usage in build.py:  H = Human(KIT); H.load(); H.fit(skull_obj, c7_z); ...  then H.derive(chain_mats, ...) ."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_paths import asset
import bpy, math, os, hashlib
from mathutils import Vector, Matrix
D = bpy.data
ASSET = asset('assets/mpfb/human_mpfb_mocap.blend')
REF = 400   # neutral standing frame of the Timeline (idle hold): the reference pose the skeleton was modelled in
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
class Human:
    def __init__(self, scene, link):
        self.sc = scene; self.link = link
    def load(self):
        with D.libraries.load(ASSET, link=False) as (src, dst):
            dst.objects = ['HumanRig', 'HumanBody', 'HumanHair', 'HumanShirt', 'HumanPants']; dst.actions = ['Timeline']
        self.rig = D.objects['HumanRig']; self.body = D.objects['HumanBody']
        for o in (self.rig, self.body): self.link(o) if o.name not in self.sc.collection.objects else None
        self.rig.animation_data_create(); self.rig.animation_data.action = D.actions['Timeline']
        self.root = D.objects.new('HumanRoot', None); self.link(self.root)
        self.rig.parent = self.root; self.extra = [D.objects[n] for n in ('HumanHair', 'HumanShirt', 'HumanPants')]
        for o in [self.body] + self.extra:
            self.link(o) if o.name not in self.sc.collection.objects else None; o.parent = self.rig; o.matrix_parent_inverse = self.rig.matrix_basis.inverted()   # the rig is lifted to the mesh (mpfb_make.py): cancel it for the body; the root carries the fit
        self.body['src'] = 'mpfb:%s|mocap:%s' % (sha(ASSET.replace('human_mpfb_mocap', 'human_mpfb')), '|'.join(sha(os.path.join(os.path.dirname(os.path.dirname(ASSET)), 'mocap', n + '.fbx')) for n in ('Texting While Standing', 'Looking Down', 'Standing Idle')))
        return self
    def at(self, f):
        self.sc.frame_set(int(f)); bpy.context.view_layer.update()
    def bone(self, name): return self.rig.matrix_world @ self.rig.pose.bones[name].matrix
    def fit(self, skull_top, c7_z, skull_cy, s=None):
        """uniform scale about the neck base so the crown sits 1.2 cm above the skull and the neck base on C7; y so the head joint centre sits on the skull centre."""
        self.at(REF); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); e = self.body.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        top = max((mw @ v.co).z for v in me.vertices if (mw @ v.co).z < 1.95); e.to_mesh_clear()
        N = self.bone('neck_01').translation.copy(); hb = self.rig.pose.bones['head']; hc = self.rig.matrix_world @ (hb.head + hb.tail) / 2
        s = s or (skull_top + 0.012 - c7_z) / (top - N.z)
        self.s = s; target = Vector((0.0, N.y + (skull_cy - hc.y) * s, c7_z))
        self.root.scale = (s, s, s); self.root.location = target - s * N; bpy.context.view_layer.update()
        print('HUMAN fit: scale', round(s, 3), 'crown z', round(top, 3), 'neck z', round(N.z, 3), 'target', tuple(round(x, 3) for x in target))
        return s
    def follow(self, objs, bone='spine_03'):
        """parent rigid objects to a bone of the human so they travel with the upper back; world position is unchanged at the REF pose."""
        self.at(REF); pb = self.rig.pose.bones[bone]; inv = (self.rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))).inverted()
        for o in objs:
            mw = o.matrix_world.copy(); o.parent = self.rig; o.parent_type = 'BONE'; o.parent_bone = bone; o.matrix_parent_inverse = inv
        bpy.context.view_layer.update()
    def material(self, vkey, fade_name='Fade'):
        """opaque-by-default skin (principled, no transmission, no volume, no subsurface); alpha = Fade value (1 = opaque). Optional amber hook tint node 'Tint'."""
        m = D.materials.new('HumanSkin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        p.inputs['Base Color'].default_value = (0.78, 0.54, 0.43, 1); p.inputs['Roughness'].default_value = 0.55; p.inputs['Subsurface Weight'].default_value = 0.0
        p.inputs['Specular IOR Level'].default_value = 0.35
        fade = nt.nodes.new('ShaderNodeValue'); fade.name = fade_name; fade.outputs[0].default_value = 1.0; nt.links.new(fade.outputs[0], p.inputs['Alpha'])
        tint = nt.nodes.new('ShaderNodeValue'); tint.name = 'Tint'; tint.outputs[0].default_value = 0.0
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.78, 0.54, 0.43, 1); mx.inputs['B'].default_value = (1.0, 0.45, 0.04, 1)
        nt.links.new(tint.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], p.inputs['Base Color']); nt.links.new(mx.outputs['Result'], p.inputs['Emission Color'])
        ts = nt.nodes.new('ShaderNodeMath'); ts.operation = 'MULTIPLY'; ts.inputs[1].default_value = 1.6; nt.links.new(tint.outputs[0], ts.inputs[0]); nt.links.new(ts.outputs[0], p.inputs['Emission Strength'])
        nt.links.new(p.outputs[0], out.inputs['Surface'])
        self.body.data.materials.clear(); self.body.data.materials.append(m); self.fades = [fade]
        for o, col, rough in ((self.extra[0], (0.05, 0.035, 0.03, 1), 0.6), (self.extra[1], (0.22, 0.30, 0.42, 1), 0.85), (self.extra[2], (0.10, 0.11, 0.14, 1), 0.8)):   # hair, T-shirt, trousers: same fade, opaque principled
            mm = m.copy(); mm.name = 'Human_' + o.name; pp = [n for n in mm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
            for n in list(mm.node_tree.nodes):
                if n.type in ('MIX', 'MATH'): mm.node_tree.nodes.remove(n)
            pp.inputs['Base Color'].default_value = col; pp.inputs['Roughness'].default_value = rough; pp.inputs['Emission Strength'].default_value = 0.0
            o.data.materials.clear(); o.data.materials.append(mm); self.fades.append(mm.node_tree.nodes['Fade'])
        for mod in self.body.modifiers:
            if mod.type == 'SUBSURF': mod.levels = 0; mod.render_levels = 0
        return fade, tint
    # ------------------------------------------------------------------ skeleton slave: solve chain angles + head slide from the human
    def derive(self, frames, chain_mats, P_C, shape, fa, c_pt, lam_fixed=0.0):
        c_pt = Vector(c_pt)
        """-> {f: (angles[8], slide)} so that the chain's skull follows the human's head bone. shape = (P_REV - P_C): direction along which the lower neck flexes while the
        head stays level (forward-head posture). Unknowns per frame: lam (how much of `shape`) and the slide (m, -y = forward); the total head pitch is fixed by the human."""
        self.at(REF); H0 = self.bone('head'); S0 = self.bone('spine_03'); H0i = H0.inverted(); S0i = S0.inverted(); out = {}; err = []
        fa = list(fa); sP = sum(P_C)
        def angles(lam, theta):
            base = [p + lam * s for p, s in zip(P_C, shape)]; tot = sP + theta - sum(base); return [b + a * tot for b, a in zip(base, fa)]
        c0 = chain_mats(list(P_C), 0.0)[8] @ c_pt   # where the skeleton's neutral (P_C) puts the skull point: the human's neutral head must sit there
        raw = {}
        for f in frames:
            self.at(f); Q = (self.bone('spine_03') @ S0i).inverted() @ self.bone('head') @ H0i
            theta = math.degrees(math.atan2(Q[2][1], Q[1][1])); tgt = Q @ c0
            def res(lam, sl): return (chain_mats(angles(lam, theta), sl)[8] @ c_pt - tgt)
            best = None
            for lam in [x * 0.1 for x in range(-3, 18)]:   # scan how much of the reversed-curve shape (lower neck flexed, head level) fits; the slide then makes y exact
                r0 = res(lam, 0.0); sl = max(-0.25, min(0.25, -r0.y)); e = abs(res(lam, sl).z) + 0.3 * abs(res(lam, sl).y)
                if best is None or e < best[0]: best = (e, lam)
            raw[f] = (best[1], theta, tgt)
        # smooth lambda over time (jitter from the scan would shake the neck), then solve the slide exactly
        fl = sorted(raw)
        for i, f in enumerate(fl):
            nb = [raw[g][0] for g in fl[max(0, i - 3):i + 4]]; lam = sum(nb) / len(nb); theta = raw[f][1]; tgt = raw[f][2]
            def res(lam, sl): return (chain_mats(angles(lam, theta), sl)[8] @ c_pt - tgt)
            r0 = res(lam, 0.0); sl = max(-0.25, min(0.25, -r0.y))
            r = res(lam, sl); err.append(math.hypot(r.y, r.z)); self.log = getattr(self, 'log', {}); self.log[f] = (round(theta, 1), round(lam, 2), round(sl, 3), round(err[-1] * 100, 1)); out[f] = (angles(lam, theta), sl)
        print('HUMAN derive: %d frames, skull-point error cm: mean %.2f max %.2f' % (len(frames), 100 * sum(err) / len(err), 100 * max(err)))
        return out
    def phone(self, f_ref=920):
        """a plain dark slab with a lit screen, held between the hands: placed at the payoff hold pose, parented to the left hand bone (rigid). Opaque principled; Fade node like the person."""
        self.at(f_ref); rg = self.rig; pb = rg.pose.bones; hl = rg.matrix_world @ pb['hand_l'].head; hr = rg.matrix_world @ pb['hand_r'].head; ctr = (hl + hr) / 2
        eye = rg.matrix_world @ pb['head'].head; n = (eye + Vector((0, 0, 0.06)) - ctr).normalized() + Vector((-0.75, 0, 0)); n.normalize(); ctr = ctr + Vector((-0.03, -0.01, 0.0)); up = (Vector((0, 0, 1)) - n * n.z).normalized(); x = up.cross(n).normalized()   # screen faces the eyes
        M = Matrix(((x.x, up.x, n.x, ctr.x), (x.y, up.y, n.y, ctr.y), (x.z, up.z, n.z, ctr.z), (0, 0, 0, 1)))
        out = []
        for name, size, off, emit in (('HumanPhone', (0.045, 0.09, 0.006), 0.0, 0.0), ('HumanPhoneScreen', (0.040, 0.082, 0.0005), 0.0065, 1.2)):
            me = D.meshes.new(name); import bmesh; bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts: v.co = Vector((v.co.x * size[0] * 2, v.co.y * size[1] * 2, v.co.z * size[2] * 2 + off))
            bm.to_mesh(me); bm.free(); o = D.objects.new(name, me); self.link(o); o['src'] = 'own'
            m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out_n = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
            p.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1) if not emit else (0.55, 0.75, 1.0, 1); p.inputs['Roughness'].default_value = 0.3
            if emit: p.inputs['Emission Color'].default_value = (0.55, 0.75, 1.0, 1); p.inputs['Emission Strength'].default_value = emit
            fd = nt.nodes.new('ShaderNodeValue'); fd.name = 'Fade'; fd.outputs[0].default_value = 1.0; nt.links.new(fd.outputs[0], p.inputs['Alpha']); nt.links.new(p.outputs[0], out_n.inputs['Surface'])
            me.materials.append(m); self.fades.append(fd)
            o.parent = rg; o.parent_type = 'BONE'; o.parent_bone = 'hand_l'; hb = pb['hand_l']
            o.matrix_parent_inverse = (rg.matrix_world @ hb.matrix @ Matrix.Translation((0, hb.bone.length, 0))).inverted() @ M
            out.append(o)
        self.extra += out; return out
