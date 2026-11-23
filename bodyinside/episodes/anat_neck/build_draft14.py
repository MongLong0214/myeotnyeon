# Stage C (fast, every draft): rig + materials + animation + camera + light. usage: Blender -b neck_solids.blend -P build.py  -> neck.blend
import sys, os, json, math
sys.path.insert(0, (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/blender'))
import bpy
from kit import *; from kit_spine import *
HERE = os.path.dirname(bpy.data.filepath); EP = json.load(open(HERE + '/episode.json')); INFO = json.load(open(HERE + '/disc_info.json'))
sc = bpy.context.scene; FPS = EP['fps']; NF = int(FPS * EP['duration']); sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = NF - 1
X_CUT = 0.001
BODIES = ['Vertebra T1', 'Vertebra C7', 'Vertebra C6', 'Vertebra C5', 'Vertebra C4', 'Vertebra C3', 'Axis (C2)', 'Atlas (C1)', 'Skull']
B = [D.objects[n] for n in BODIES]
# landmarks (computed first: the ending pose aligns the ear over the shoulder)
_mz0 = max(v.co.z for v in D.objects['Mandible'].data.vertices); _cd0 = [v.co for v in D.objects['Mandible'].data.vertices if v.co.z > _mz0 - 0.006 and v.co.x > 0.02]
TMJ_P = sum(_cd0, Vector()) / len(_cd0)   # centre of the mandibular condyle = the jaw joint
EAR_P = Vector((0.050, TMJ_P.y + 0.010, TMJ_P.z + 0.014))   # ear canal on the skull's lateral wall (x = 5 cm, so the oblique view keeps it above the jaw joint rather than shifted a hand's width behind it): 1 cm behind and 1.4 cm above the jaw joint (review 7: the ear belongs above the jaw joint)
ACRO_P = max([v.co for v in D.objects['Clavicle.l'].data.vertices], key=lambda c: c.x).copy()   # shoulder point = lateral end of the clavicle (acromial end)
SL_END = max(-0.03, min(0.03, ACRO_P.y - EAR_P.y))
# ---------------- materials
for o in D.objects:
    if o.type == 'MESH':
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith('BoneBase'): pass
# cord / roots / muscles
def tissue(name, col, rough=0.45, sss=0.25, ghost=False):
    m, nt, out, p = newmat(name); p.inputs['Base Color'].default_value = col; p.inputs['Roughness'].default_value = rough
    p.inputs['Subsurface Weight'].default_value = sss; p.inputs['Subsurface Scale'].default_value = 0.002; p.inputs['Subsurface Radius'].default_value = (1.0, 0.5, 0.3)
    p.inputs['Coat Weight'].default_value = 0.25; p.inputs['Coat Roughness'].default_value = 0.2
    noise_bump(nt, p, 1200, 0.1, 0.0001)
    em = nt.nodes.new('ShaderNodeValue'); em.name = 'Emit'; nt.links.new(em.outputs[0], p.inputs['Emission Strength']); p.inputs['Emission Color'].default_value = HIGHLIGHT
    g = ghostable(nt, out, p.outputs[0], 'Ghost', 0.0, 1.0) if ghost else None
    if not ghost: nt.links.new(p.outputs[0], out.inputs['Surface'])
    return m, em
mCord, _ = tissue('Cord', (0.82, 0.74, 0.54, 1), 0.5, 0.65, ghost=True)
_nt = mCord.node_tree; _p = [n for n in _nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _mp = _nt.nodes.new('ShaderNodeMapping'); _mp.inputs['Scale'].default_value = (900, 900, 60)   # fibres run along z
_nz = _nt.nodes.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 1.0; _nz.inputs['Detail'].default_value = 6
_nt.links.new(_tc.outputs['Object'], _mp.inputs['Vector']); _nt.links.new(_mp.outputs['Vector'], _nz.inputs['Vector'])
_bp = _nt.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.6; _bp.inputs['Distance'].default_value = 0.00012; _nt.links.new(_nz.outputs['Fac'], _bp.inputs['Height']); _nt.links.new(_bp.outputs['Normal'], _p.inputs['Normal'])
_cr = _nt.nodes.new('ShaderNodeValToRGB'); _cr.color_ramp.elements[0].color = (0.78, 0.66, 0.40, 1); _cr.color_ramp.elements[1].color = (0.98, 0.93, 0.76, 1); _nt.links.new(_nz.outputs['Fac'], _cr.inputs['Fac']); _nt.links.new(_cr.outputs['Color'], _p.inputs['Base Color'])
fadeC = add_fade(mCord)
mRoot, eRoot = tissue('RootMat', (0.95, 0.62, 0.02, 1), 0.4, 0.0)
_rt = mRoot.node_tree; _rp = [n for n in _rt.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _rl = _rt.nodes.new('ShaderNodeLayerWeight'); _rl.inputs['Blend'].default_value = 0.35
_rm = _rt.nodes.new('ShaderNodeMix'); _rm.data_type = 'RGBA'; _rm.inputs['A'].default_value = (0.95, 0.62, 0.02, 1); _rm.inputs['B'].default_value = (0.98, 0.93, 0.78, 1); _rt.links.new(_rl.outputs['Fresnel'], _rm.inputs['Factor']); _rt.links.new(_rm.outputs['Result'], _rp.inputs['Base Color'])   # pale sheath at grazing angles
_rtc = _rt.nodes.new('ShaderNodeTexCoord'); _rmp = _rt.nodes.new('ShaderNodeMapping'); _rmp.inputs['Scale'].default_value = (1400, 1400, 120); _rn = _rt.nodes.new('ShaderNodeTexNoise'); _rt.links.new(_rtc.outputs['Object'], _rmp.inputs['Vector']); _rt.links.new(_rmp.outputs['Vector'], _rn.inputs['Vector'])
_rb = _rt.nodes.new('ShaderNodeBump'); _rb.inputs['Strength'].default_value = 0.5; _rb.inputs['Distance'].default_value = 0.0001; _rt.links.new(_rn.outputs['Fac'], _rb.inputs['Height']); _rt.links.new(_rb.outputs['Normal'], _rp.inputs['Normal'])
mMus, eMus = tissue('Muscle', (0.52, 0.12, 0.10, 1), 0.38, 0.35, ghost=True)
mLine, nt, out, p = newmat('CurveLineMat'); p.inputs['Base Color'].default_value = (1.0, 0.42, 0.02, 1); p.inputs['Emission Color'].default_value = (1.0, 0.42, 0.02, 1)
eLine = nt.nodes.new('ShaderNodeValue'); eLine.outputs[0].default_value = 3.0; nt.links.new(eLine.outputs[0], p.inputs['Emission Strength'])
ghostable(nt, out, p.outputs[0], 'Ghost', 0.0, 1.0); fadeL = add_fade(mLine)
fLine = add_fade_simple = None
for n in ('SpinalCord',): setmat(D.objects[n], mCord)
for n in ('SpinalRoots', 'SpinalGanglia'): setmat(D.objects[n], mRoot)
# review 6 item 3: the pale disc on the touch point (f630, 480-520 x 360-400) is a 14-triangle flat cap at the x = 0.001 section plane (found by ray cast: SpinalRoots island 28, centre y 1.32 cm).
# Delete the tiny cap islands: the open tube end then shows as a thin ring and the lobe meeting the root is visible.
import bmesh as _bmr
for _n in ('SpinalRoots',):
    _bm = _bmr.new(); _bm.from_mesh(D.objects[_n].data); _bm.faces.ensure_lookup_table(); _seen = set(); _kill = []
    for _f in _bm.faces:
        if _f.index in _seen: continue
        _st = [_f]; _comp = []; _seen.add(_f.index)
        while _st:
            _c = _st.pop(); _comp.append(_c)
            for _e in _c.edges:
                for _g in _e.link_faces:
                    if _g.index not in _seen: _seen.add(_g.index); _st.append(_g)
        if len(_comp) <= 20: _kill += _comp
    _bmr.ops.delete(_bm, geom=_kill, context='FACES'); _bm.to_mesh(D.objects[_n].data); _bm.free(); print('root cap islands removed', len(_kill), 'faces')
for _o in [o for o in D.objects if o.name.startswith(('Sternocleido', 'Longus colli', 'Semispinalis capitis'))]: D.objects.remove(_o)   # anterior strap muscles end as torn strips: removed (review 1 P1-10)
MUS = [o for o in D.objects if o.type == 'MESH' and any(k in o.name for k in ('Splenius', 'Semispinalis', 'Levator', 'trapezius'))]
_mt = mMus.node_tree; _mp = [n for n in _mt.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _mc = _mt.nodes.new('ShaderNodeTexCoord'); _mm = _mt.nodes.new('ShaderNodeMapping'); _mm.inputs['Scale'].default_value = (900, 28, 1)
_mn = _mt.nodes.new('ShaderNodeTexNoise'); _mn.inputs['Detail'].default_value = 8; _mt.links.new(_mc.outputs['UV'], _mm.inputs['Vector']); _mt.links.new(_mm.outputs['Vector'], _mn.inputs['Vector'])
_mr = _mt.nodes.new('ShaderNodeValToRGB'); _mr.color_ramp.elements[0].color = (0.16, 0.015, 0.02, 1); _mr.color_ramp.elements[1].color = (0.40, 0.055, 0.05, 1); _mt.links.new(_mn.outputs['Fac'], _mr.inputs['Fac'])
_ma = _mt.nodes.new('ShaderNodeAttribute'); _ma.attribute_name = 'tend'; _mx = _mt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs['B'].default_value = (0.82, 0.70, 0.52, 1)
_mt.links.new(_ma.outputs['Fac'], _mx.inputs['Factor']); _mt.links.new(_mr.outputs['Color'], _mx.inputs['A']); _mt.links.new(_mx.outputs['Result'], _mp.inputs['Base Color'])   # pale tendon at both ends
_mb = _mt.nodes.new('ShaderNodeBump'); _mb.inputs['Strength'].default_value = 0.8; _mb.inputs['Distance'].default_value = 0.0002; _mt.links.new(_mn.outputs['Fac'], _mb.inputs['Height']); _mt.links.new(_mb.outputs['Normal'], _mp.inputs['Normal'])
fadeM = add_fade(mMus)
for o in MUS: setmat(o, mMus); o.hide_render = False
# muscle bellies (review 6): the BodyParts3D muscles are thin sheets with spiky nuchal fingers that zig-zag into red "wires" when skinned. Each muscle becomes one solid belly (voxel remesh + smooth),
# gets a fibre UV (V runs along the belly's principal axis) and a per-vertex tendon attribute (1 at both ends) that the shader turns into fibre striation and pale tendon ends.
import numpy as np
def muscle_belly(o, voxel, ztop=None):
    bpy.context.view_layer.objects.active = o
    for ob in D.objects: ob.select_set(ob is o)
    md = o.modifiers.new('belly', 'REMESH'); md.mode = 'VOXEL'; md.voxel_size = voxel; md.use_smooth_shade = True; bpy.ops.object.modifier_apply(modifier='belly')
    if ztop is not None:   # the nuchal fingers above ztop are the red wires: cut the belly there and close it (the cut end reads as a tendon via the 'tend' attribute)
        import bmesh as _bmm
        bm = _bmm.new(); bm.from_mesh(o.data); _bmm.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, ztop), plane_no=(0, 0, 1), clear_outer=True)
        be = [e for e in bm.edges if e.is_boundary]; _bmm.ops.holes_fill(bm, edges=be, sides=max(4, len(be))); _bmm.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
    md = o.modifiers.new('sm', 'SMOOTH'); md.factor = 0.7; md.iterations = 6; bpy.ops.object.modifier_apply(modifier='sm')
    me = o.data; n = len(me.vertices); a = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', a); a = a.reshape(-1, 3); c = a.mean(0)
    u_, s_, vt = np.linalg.svd(a - c, full_matrices=False); ax = vt[0]; bx = vt[1]
    if ax[2] < 0: ax = -ax
    t = (a - c) @ ax; t0, t1 = np.percentile(t, 1), np.percentile(t, 99); tn = np.clip((t - t0) / (t1 - t0), 0, 1); uu = (a - c) @ bx
    e = np.minimum(tn, 1 - tn); tend = 1 - np.clip(e / 0.16, 0, 1) ** 2 * (3 - 2 * np.clip(e / 0.16, 0, 1))   # 1 at the ends, 0 in the belly
    at = me.attributes.new('tend', 'FLOAT', 'POINT'); at.data.foreach_set('value', tend.astype(np.float32))
    uvl = me.uv_layers.new(name='fibre'); li = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', li)
    uv = np.c_[uu[li], t[li]].astype(np.float32); uvl.data.foreach_set('uv', uv.ravel())
    return len(me.vertices)
for o in MUS: print('belly', o.name, muscle_belly(o, 0.0018, 1.49 if 'trapezius' in o.name else None))
_mt = mMus.node_tree
# hook: the cervical cut faces glow amber at the start (the C-curve is the subject), fading out by f110
mTC, vTC = tint_material(D.materials['Trabecular'], name='TrabC')
for n in ('Axis (C2)', 'Vertebra C3', 'Vertebra C4', 'Vertebra C5', 'Vertebra C6', 'Vertebra C7'):
    o = D.objects[n]; i = [m.name if m else '' for m in o.data.materials].index('Trabecular'); o.data.materials[i] = mTC
for f, v in ((0, 0.0), (6, 1.0), (45, 0.9), (110, 0.0)): vkey(vTC, f, v)
# CC0 skin shell: translucent, dissolves in at the start and at the ending
mSkin, nt_, out_, p_ = newmat('SkinGhost'); p_.inputs['Base Color'].default_value = (0.86, 0.60, 0.50, 1); p_.inputs['Roughness'].default_value = 0.5; p_.inputs['Subsurface Weight'].default_value = 0.3
fadeS = nt_.nodes.new('ShaderNodeValue'); fadeS.name = 'Fade'; lw_ = nt_.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.5
mr_ = nt_.nodes.new('ShaderNodeMapRange'); mr_.inputs['To Min'].default_value = 0.16; mr_.inputs['To Max'].default_value = 0.62; nt_.links.new(lw_.outputs['Facing'], mr_.inputs['Value'])
mu_ = nt_.nodes.new('ShaderNodeMath'); mu_.operation = 'MULTIPLY'; nt_.links.new(mr_.outputs['Result'], mu_.inputs[0]); nt_.links.new(fadeS.outputs[0], mu_.inputs[1])   # same opacity on back faces: the far half of the shell is what we look at
geo_ = nt_.nodes.new('ShaderNodeNewGeometry'); sz_ = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], sz_.inputs[0])
mz_ = nt_.nodes.new('ShaderNodeMapRange'); mz_.interpolation_type = 'SMOOTHSTEP'; nt_.links.new(sz_.outputs['Z'], mz_.inputs['Value'])
_zmin = nt_.nodes.new('ShaderNodeValue'); _zmax = nt_.nodes.new('ShaderNodeValue'); nt_.links.new(_zmin.outputs[0], mz_.inputs['From Min']); nt_.links.new(_zmax.outputs[0], mz_.inputs['From Max'])
for f, a, b in ((0, 0.95, 1.38), (20, 0.95, 1.38), (850, 1.33, 1.43), (NF, 1.33, 1.43)): vkey(_zmin, f, a); vkey(_zmax, f, b)   # opening: whole figure; ending: the torso is gone by the frame bottom, no grey slab behind the cord
mu2_ = nt_.nodes.new('ShaderNodeMath'); mu2_.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], mu2_.inputs[0]); nt_.links.new(mz_.outputs['Result'], mu2_.inputs[1]); mu_ = mu2_   # fade out toward the bottom
_gx = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], _gx.inputs[0]); _mx2 = nt_.nodes.new('ShaderNodeMapRange'); _mx2.interpolation_type = 'SMOOTHSTEP'; _mx2.inputs['From Min'].default_value = 0.001; _mx2.inputs['From Max'].default_value = 0.020
nt_.links.new(_gx.outputs['X'], _mx2.inputs['Value']); _mu3 = nt_.nodes.new('ShaderNodeMath'); _mu3.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], _mu3.inputs[0]); nt_.links.new(_mx2.outputs['Result'], _mu3.inputs[1]); mu_ = _mu3   # soft edge where the shell is cut (no jagged rim)
_fy = nt_.nodes.new('ShaderNodeMapRange'); _fy.interpolation_type = 'SMOOTHSTEP'; _fy.inputs['From Min'].default_value = -0.085; _fy.inputs['From Max'].default_value = -0.045; _sy = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], _sy.inputs[0]); nt_.links.new(_sy.outputs['Y'], _fy.inputs['Value'])
_fz = nt_.nodes.new('ShaderNodeMapRange'); _fz.interpolation_type = 'SMOOTHSTEP'; _fz.inputs['From Min'].default_value = 1.49; _fz.inputs['From Max'].default_value = 1.52; nt_.links.new(_sy.outputs['Z'], _fz.inputs['Value'])
_fi = nt_.nodes.new('ShaderNodeMath'); _fi.operation = 'SUBTRACT'; _fi.inputs[0].default_value = 1.0; nt_.links.new(_fz.outputs['Result'], _fi.inputs[1]); _fm = nt_.nodes.new('ShaderNodeMath'); _fm.operation = 'MAXIMUM'; nt_.links.new(_fy.outputs['Result'], _fm.inputs[0]); nt_.links.new(_fi.outputs[0], _fm.inputs[1])
_fmu = nt_.nodes.new('ShaderNodeMath'); _fmu.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], _fmu.inputs[0]); nt_.links.new(_fm.outputs[0], _fmu.inputs[1]); mu_ = _fmu   # the soft orange-brown smear in front of the ghost's lips (f890-f989) is gone: the face front fades out
tr_ = nt_.nodes.new('ShaderNodeBsdfTransparent'); ms_ = nt_.nodes.new('ShaderNodeMixShader'); nt_.links.new(mu_.outputs[0], ms_.inputs['Fac']); nt_.links.new(tr_.outputs[0], ms_.inputs[1]); nt_.links.new(p_.outputs[0], ms_.inputs[2]); nt_.links.new(ms_.outputs[0], out_.inputs['Surface'])
setmat(D.objects['Skin'], mSkin)
_mx = nt_.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs['A'].default_value = (0.86, 0.60, 0.50, 1); _mx.inputs['B'].default_value = (1.0, 0.45, 0.04, 1); tintS = nt_.nodes.new('ShaderNodeValue')
nt_.links.new(tintS.outputs[0], _mx.inputs['Factor']); nt_.links.new(_mx.outputs['Result'], p_.inputs['Base Color']); nt_.links.new(_mx.outputs['Result'], p_.inputs['Emission Color']); _ts = nt_.nodes.new('ShaderNodeMath'); _ts.operation = 'MULTIPLY'; _ts.inputs[1].default_value = 2.2; nt_.links.new(tintS.outputs[0], _ts.inputs[0]); nt_.links.new(_ts.outputs[0], p_.inputs['Emission Strength'])
for f, v in ((0, 1.0), (30, 1.0), (75, 0.0)): vkey(tintS, f, v)   # the establishing figure glows amber (hook subject), then settles to skin tone
for f, v in ((0, 1.0), (3, 1.0), (9, 0.0), (850, 0.0), (900, 1.0), (NF, 1.0)): vkey(fadeS, f, v)   # the ghost dissolves by f9: its throat sheet shears into fans once the head tilts (f9-12 in draft10)
vis(D.objects['Skin'], [(0, 10), (848, NF + 1)])   # faded-out skin still rendered dark scratch marks: hide_render as well
mShoulder = D.materials['BoneBase'].copy(); mShoulder.name = 'BoneShoulder'; fadeSh = add_fade(mShoulder)
SHD = (0.78, 0.70, 0.58)   # measured against the spine in the f950 render (verify)
# shoulder girdle: the vertebrae's bone material, darkened toward their tan (review 6/7: it still read brighter and whiter than the spine)
for _n in mShoulder.node_tree.nodes:
    if _n.type == 'VALTORGB':
        for _e in _n.color_ramp.elements: _e.color = (_e.color[0] * SHD[0], _e.color[1] * SHD[1], _e.color[2] * SHD[2], 1)
    if _n.type == 'BSDF_PRINCIPLED': _n.inputs['Subsurface Weight'].default_value = 0.04
for _n in ('Clavicle.l', 'Scapula.l'): D.objects[_n].data.materials.clear(); setmat(D.objects[_n], mShoulder)
for f, v in ((0, 0.0), (858, 0.0), (890, 1.0), (NF, 1.0)): vkey(fadeSh, f, v)
# review 6 item 5: the lower thoracic vertebrae (T2-T4) end at the frame bottom with white facet bits between their spinous processes that read as floating fragments (f490). A 33-vertex speck
# is deleted from T2 and T3/T4 (+ their cortical rims) fade out with height, like the torso, instead of ending in cut-off bone.
for _n in ('Vertebra T1', 'Vertebra T2', 'Vertebra T3', 'Vertebra T4'): drop_small_parts(D.objects[_n], 100)
for _o in [o for o in D.objects if o.name.startswith('Rim_') and o.type == 'MESH']: drop_small_parts(_o, 100)   # stray rim specks (Rim_Vertebra_T2 left a white dot at f490)
def zfade_mat(_c, z0, z1):
    _nt = _c.node_tree; _out = [n for n in _nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]; _src = _out.inputs['Surface'].links[0].from_socket
    _g = _nt.nodes.new('ShaderNodeNewGeometry'); _sp = _nt.nodes.new('ShaderNodeSeparateXYZ'); _mr = _nt.nodes.new('ShaderNodeMapRange'); _mr.interpolation_type = 'SMOOTHSTEP'; _mr.inputs['From Min'].default_value = z1; _mr.inputs['From Max'].default_value = z0
    _tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader')
    _nt.links.new(_g.outputs['Position'], _sp.inputs[0]); _nt.links.new(_sp.outputs['Z'], _mr.inputs['Value']); _nt.links.new(_mr.outputs['Result'], _mx.inputs['Fac']); _nt.links.new(_tr.outputs[0], _mx.inputs[1]); _nt.links.new(_src, _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _out.inputs['Surface'])
def zfade(o, z0, z1):
    for _k, _m in enumerate(o.data.materials):
        if _m: _c = _m.copy(); zfade_mat(_c, z0, z1); o.data.materials[_k] = _c
for _n, _z in (('Vertebra T1', (1.438, 1.402)), ('Vertebra T2', (1.405, 1.36)), ('Vertebra T3', (1.40, 1.35)), ('Vertebra T4', (1.40, 1.35)), ('Rim_Vertebra_T1', (1.438, 1.402)), ('Rim_Vertebra_T2', (1.405, 1.36)), ('Rim_Vertebra_T3', (1.40, 1.35)), ('Rim_Vertebra_T4', (1.40, 1.35))):
    if _n in D.objects: zfade(D.objects[_n], *_z)
zfade_mat(mCord, 1.40, 1.335)   # review 7: the cord hung out as a bare stick below the last vertebra at 27 kg (f270-f330): it fades with the vertebrae it runs through
zfade_mat(mMus, 1.445, 1.41)   # ... and an orange muscle tip poked through the bottom fade at f820
import bmesh as _bmd
_bd = _bmd.new(); _bd.from_mesh(D.objects['Axis (C2)'].data); _bmd.ops.bisect_plane(_bd, geom=_bd.verts[:] + _bd.edges[:] + _bd.faces[:], plane_co=(0, 0.036, 0), plane_no=(0, 1, 0), clear_outer=True)
_be = [e for e in _bd.edges if e.is_boundary]; _bmd.ops.holes_fill(_bd, edges=_be, sides=max(4, len(_be))); _bmd.ops.triangulate(_bd, faces=_bd.faces[:]); _bd.to_mesh(D.objects['Axis (C2)'].data); _bd.free()   # ray cast at f30 (740-810,350-420): the oval is the cut tip of C2's spinous process (rest y 4.3 cm, z 1.514), which overlaps the cerebellum in the reversed pose and read as an ear outline; its tip is trimmed. Before: the beside the cerebellum (f15-f60, f490, f820; review 8)
for _rn in ('Rim_Axis_(C2)', 'Rim_Atlas_(C1)'):
    for _sp in list(D.objects[_rn].data.splines):   # rim loops across C1-C2 looked like wire
        _ps = [p.co.y for p in (_sp.points if _sp.type in ('POLY', 'NURBS') else _sp.bezier_points)]
        if _ps and sum(_ps) / len(_ps) > 0.034: D.objects[_rn].data.splines.remove(_sp)
for _n in ('Brain',): drop_small_parts(D.objects[_n], 5000)   # two stray brain islands (cut face + cortical ring) read as a second "ear" beside the cerebellum at f18-f60 and f765-f800 (review 7)
# review 7 item 5: cortical rim on every cut vertebra twice as thick and a brighter, denser cortex colour; disc annulus lighter with a visible ring, nucleus translucent
for _o in [o for o in D.objects if o.name.startswith('Rim_') and o.type == 'CURVE']:
    _o.data.bevel_depth *= 2.2
    for _sp in list(_o.data.splines):   # tiny loops left by the deleted islands (Rim_Vertebra_T2's loop was the white speck beside the spine)
        _pp = [p.co.xyz if hasattr(p, 'co') else p.co for p in (_sp.points if _sp.type == 'POLY' or _sp.type == 'NURBS' else _sp.bezier_points)]
        _xs = [Vector(p) for p in _pp]; _d = (Vector((max(v.x for v in _xs), max(v.y for v in _xs), max(v.z for v in _xs))) - Vector((min(v.x for v in _xs), min(v.y for v in _xs), min(v.z for v in _xs)))).length if _xs else 0
        if _d < 0.006: _o.data.splines.remove(_sp)
for _n in D.materials['Cortex'].node_tree.nodes:
    if _n.type == 'BSDF_PRINCIPLED': _n.inputs['Base Color'].default_value = (0.96, 0.90, 0.76, 1); _n.inputs['Roughness'].default_value = 0.35
# ---------------- rig
jp = [Vector((0, INFO[t]['yc'], INFO[t]['zm'])) for t in ('C7T1', 'C6C7', 'C5C6', 'C4C5', 'C3C4', 'C2C3')] + [Vector((0, 0.012, 1.5335)), Vector((0, 0.015, 1.5535))]
chain = FKChain(B, jp)
for o in D.objects:
    if o.name.startswith('Rim_'):
        nm = o.name[4:].replace('_', ' '); tgt = [b for b in B if b.name.replace(' ', '_') == o.name[4:]]
        if tgt: FKChain._parent(o, tgt[0])
        elif nm == 'Mandible': FKChain._parent(o, D.objects['Skull'])
FKChain._parent(D.objects['Mandible'], D.objects['Skull']); FKChain._parent(D.objects['TeethUpper'], D.objects['Skull']); FKChain._parent(D.objects['TeethLower'], D.objects['Skull']); FKChain._parent(D.objects['Brain'], D.objects['Skull'])
mEn = enamel('Enamel')[0]
for _n in ('TeethUpper', 'TeethLower'): D.objects[_n].data.materials.clear(); setmat(D.objects[_n], mEn)
for _n in ('Clavicle.l', 'Scapula.l'): pass
for o in D.objects:
    if o.name.startswith('Rim_Mandible'): FKChain._parent(o, D.objects['Skull'])
# discs: hooks to the vertebra above / below, weights from the ray-measured height inside the gap
up_lo = {'C2C3': ('Axis (C2)', 'Vertebra C3'), 'C3C4': ('Vertebra C3', 'Vertebra C4'), 'C4C5': ('Vertebra C4', 'Vertebra C5'), 'C5C6': ('Vertebra C5', 'Vertebra C6'), 'C6C7': ('Vertebra C6', 'Vertebra C7'), 'C7T1': ('Vertebra C7', 'Vertebra T1')}
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
BULGE = {}
for tag, (un, ln) in up_lo.items():
    U, L = D.objects[un], D.objects[ln]; bu, bl = world_bvh(U), world_bvh(L); zm = INFO[tag]['zm']; yc = INFO[tag]['yc']
    for pre in ('Disc_', 'Nuc_'):
        o = D.objects[pre + tag]; gt = o.vertex_groups.new(name='wt'); gb = o.vertex_groups.new(name='wb')
        o.shape_key_add(name='Basis'); sk = o.shape_key_add(name='Bulge')
        for v in o.data.vertices:
            p = v.co
            hu = bu.ray_cast(p, Vector((0, 0, 1)), 0.01); hl = bl.ray_cast(p, Vector((0, 0, -1)), 0.01)
            if hu[0] is not None and hl[0] is not None: t = (p.z - hl[0].z) / max(hu[0].z - hl[0].z, 1e-5)
            else: t = 1.0 if p.z > zm else 0.0
            t = max(0.0, min(1.0, t)); gt.add([v.index], t, 'REPLACE'); gb.add([v.index], 1 - t, 'REPLACE')
            mid = math.sin(math.pi * t); u = (p.y - yc) / 0.008; lat = 1 + 0.9 * max(0.0, min(1.0, (p.x - 0.003) / 0.007))
            post = max(0.0, min(1.0, (u - 0.1) / 0.8)); ant = max(0.0, min(1.0, (-u - 0.1) / 0.8))
            amp = 1.9 if tag == 'C5C6' else 0.5
            if pre == 'Disc_': d = Vector((0.0004 * post * lat * mid * amp * 0.0 + 0.0003 * post * mid * amp * max(0, lat - 1), (0.0032 * post * lat * mid - 0.0008 * ant * mid) * amp, 0))
            else: d = Vector((0, 0.0013 * amp * (0.4 + 0.6 * (1 - abs(t - 0.5) * 2)), 0))
            sk.data[v.index].co = p + d
        for nm, grp, bd in (('hu', 'wt', U), ('hl', 'wb', L)):
            h = o.modifiers.new(nm, 'HOOK'); h.object = bd; h.vertex_group = grp; h.strength = 1.0; h.falloff_type = 'NONE'; h.matrix_inverse = bd.matrix_world.inverted()
        BULGE.setdefault(tag, []).append(sk)
for _t, _i in INFO.items():
    for _pre in ('Disc_',):
        _o = D.objects[_pre + _t]; _ma = D.materials['Annulus'].copy(); _ma.name = 'Annulus_' + _t; _nt = _ma.node_tree
        for _n in list(_nt.nodes):
            if _n.type in ('TEX_WAVE', 'BUMP', 'VALTORGB'): _nt.nodes.remove(_n)
        _p = [n for n in _nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _tc = _nt.nodes.new('ShaderNodeTexCoord'); _vd = _nt.nodes.new('ShaderNodeVectorMath'); _vd.operation = 'DISTANCE'; _vd.inputs[1].default_value = (0.0, _i['yc'], _i['zm'])
        _nt.links.new(_tc.outputs['Object'], _vd.inputs[0]); _sn = _nt.nodes.new('ShaderNodeMath'); _sn.operation = 'SINE'; _mu = _nt.nodes.new('ShaderNodeMath'); _mu.operation = 'MULTIPLY'; _mu.inputs[1].default_value = 2600.0
        _nt.links.new(_vd.outputs['Value'], _mu.inputs[0]); _nt.links.new(_mu.outputs[0], _sn.inputs[0]); _no = _nt.nodes.new('ShaderNodeTexNoise'); _no.inputs['Scale'].default_value = 700; _nt.links.new(_tc.outputs['Object'], _no.inputs['Vector'])
        _ad = _nt.nodes.new('ShaderNodeMath'); _ad.operation = 'ADD'; _nt.links.new(_sn.outputs[0], _ad.inputs[0]); _nt.links.new(_no.outputs['Fac'], _ad.inputs[1])
        _cr = _nt.nodes.new('ShaderNodeValToRGB'); _cr.color_ramp.elements[0].position = 0.15; _cr.color_ramp.elements[1].position = 1.2; _cr.color_ramp.elements[0].color = (0.28, 0.34, 0.50, 1); _cr.color_ramp.elements[1].color = (0.92, 0.93, 0.97, 1)
        _nt.links.new(_ad.outputs[0], _cr.inputs['Fac']); _nt.links.new(_cr.outputs['Color'], _p.inputs['Base Color']); _bp = _nt.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.7; _bp.inputs['Distance'].default_value = 0.00012
        _nt.links.new(_ad.outputs[0], _bp.inputs['Height']); _nt.links.new(_bp.outputs['Normal'], _p.inputs['Normal']); _p.inputs['Subsurface Weight'].default_value = 0.85; _p.inputs['Subsurface Radius'].default_value = (1.0, 0.8, 0.6); _p.inputs['Transmission Weight'].default_value = 0.55
        for _k, _m in enumerate(_o.data.materials):
            if _m and _m.name.startswith('Annulus'): _o.data.materials[_k] = _ma
for _t in INFO:
    _o = D.objects['Nuc_' + _t]
    for _k, _m in enumerate(_o.data.materials):
        if _m:
            _c = _m.copy(); _pp = [n for n in _c.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _pp.inputs['Base Color'].default_value = (0.88, 0.70, 0.46, 1); _pp.inputs['Subsurface Weight'].default_value = 0.6
            _pp.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.15); _pp.inputs['Roughness'].default_value = 0.04; _pp.inputs['Transmission Weight'].default_value = 0.7; _pp.inputs['IOR'].default_value = 1.35; _o.data.materials[_k] = _c
# soft tissue skinned to the chain by height
zc = [(lambda bb: (bb[0].z + bb[1].z) / 2)(world_bbox(b)) for b in B]
zc[-1] = 1.56
for n in ('SpinalCord', 'SpinalRoots', 'SpinalGanglia'): skin_to_bodies(D.objects[n], B, zc, spread=0.75)
_Bs = [x for x in B if x.name != 'Atlas (C1)']; _zs = [z for x, z in zip(B, zc) if x.name != 'Atlas (C1)']; _zs[-1] = 1.57; skin_to_bodies(D.objects['Skin'], _Bs, _zs)   # wider head/neck blend (7 cm instead of 3): the head slide no longer shears the ghost into comb-like strips
for o in MUS: skin_to_bodies(o, B, zc, spread=0.55)   # gaussian blend over neighbouring bodies: no folds where thin muscle sheets cross the head/neck joint
# ---------------- posture: states = joint angles (deg, bottom->top [C7/T1 .. C0/1]) + head slide (m, -y = forward)
fa = [.07, .12, .15, .15, .14, .11, .08, .18]; S = lambda d: [x * d for x in fa]
P_C = [-4, -5, -6, -5, -4, -3, 10, 17]; P_STR = [0] * 8; P_REV = [x * 1.25 for x in (15, 16, 16, 14, 10, 4, -33, -42)]   # review 6: 25 % more reversed-C bend   # lordosis (exaggerated) / straight / reversed, head level
add = lambda a, b: [x + y for x, y in zip(a, b)]; sc_ = lambda a, k: [x * k for x in a]
ST = lambda v, s: v + [s]
def _cm(degs):
    from mathutils import Matrix as Mx
    M = Mx.Identity(4)
    for pv, a in zip(jp, degs): M = M @ (Mx.Translation(pv) @ Mx.Rotation(math.radians(a), 4, 'X') @ Mx.Translation(-pv))
    return M
SL_END = 0.03   # half of the ear-over-shoulder alignment is a 3 cm head slide (as in draft11 it sat on C1 without a visible gap); the shoulder girdle takes the rest (end of this file)
P = Posture([(0, ST(add(P_C, [0, 0, 0, 0, 0, 0, 9, 12]), 0.014)), (7, ST(add(P_C, [0, 0, 0, 0, 0, 0, -3, -4]), -0.004)), (22, ST(P_REV, -0.025)),   # hook event (review 8): the head starts lifted, drops onto the spine by f7 as the arc lights (pulse sound 0.45 s), then slumps
             (44, ST(P_REV, -0.025)), (100, ST(P_C, 0)), (132, ST(add(P_C, S(15)), -0.004)), (170, ST(add(P_C, S(15)), -0.004)), (208, ST(add(P_C, S(30)), -0.009)), (238, ST(add(P_C, S(30)), -0.009)),
             (275, ST(add(P_C, S(60)), -0.020)), (300, ST(add(P_C, S(60)), -0.020)), (345, ST(P_C, 0)), (380, ST(P_C, 0)), (410, ST(P_STR, -0.010)), (440, ST(P_STR, -0.010)),
             (470, ST(P_REV, -0.025)), (510, ST(P_REV, -0.025)), (750, ST(sc_(P_REV, 1.06), -0.028)), (846, ST(sc_(P_REV, 1.06), -0.028)), (884, ST(sc_(P_C, 0.3), SL_END)), (NF, ST(sc_(P_C, 0.3), SL_END))])
_at = P.at
def pose(f):
    v = _at(f); tr = 0.0
    if 786 <= f <= 884: _e = min((f - 786) / 14.0, (884 - f) / 14.0, 1.0); tr = 1.4 * max(0.0, _e) * math.sin(2 * math.pi * f / 5.6)   # muscle beat (review 8): a visible tremor of the head-neck chain while the posterior muscles hold
    br = [1.8 * math.sin(2 * math.pi * f / 70) if i == 7 else 1.2 * math.sin(2 * math.pi * f / 96 + 1.0) if i == 1 else 0.0 for i in range(8)]; br = [b_ + (tr * (0.4 + 0.1 * i) if i >= 2 else 0.0) for i, b_ in enumerate(br)]   # breathing
    return [a + d for a, d in zip(v[:8], br)], v[8]
def chain_mats(degs, slide):
    """analytic FK: world matrix of every body (same maths as the Blender joint hierarchy)"""
    from mathutils import Matrix as Mx
    Ms = [Mx.Identity(4)]
    for i, (pv, a) in enumerate(zip(jp, degs)):
        Rp = Mx.Translation(pv) @ Mx.Rotation(math.radians(a), 4, 'X') @ Mx.Translation(-pv)
        Ms.append(Ms[-1] @ (Mx.Translation((0, slide, 0)) if i == 7 else Mx.Identity(4)) @ Rp)
    return Ms
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
J7 = chain.joints[7]; J7_loc = Vector(J7.location)
for f in range(NF):
    degs, sl = pose(f); chain.set_angles(f, degs); J7.location = J7_loc + Vector((0, sl, 0)); J7.keyframe_insert('location', frame=f)
# ---------------- the C-curve arc: a thick tube through the anterior vertebral bodies, baked from the analytic chain (one smooth curve at every frame)
def catmull(P_, n=6):
    out = []; Pp = [P_[0]] + list(P_) + [P_[-1]]
    for i in range(1, len(Pp) - 2):
        p0, p1, p2, p3 = Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2]
        for k in range(n): t = k / n; out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P_[-1]); return out
ARC = []
for n, bi in (('Axis (C2)', 6), ('Vertebra C3', 5), ('Vertebra C4', 4), ('Vertebra C5', 3), ('Vertebra C6', 2), ('Vertebra C7', 1)):
    o = D.objects[n]; vs = [v.co for v in o.data.vertices if abs(v.co.x - X_CUT) < 0.0015]; ymn = min(v.y for v in vs); zs = [v.z for v in vs if v.y < ymn + 0.003]
    ARC.append((bi, Vector((X_CUT - 0.0005, ymn - 0.0035, sum(zs) / len(zs)))))
cu = D.curves.new('CurveLine', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0036; cu.bevel_resolution = 5; cu.use_fill_caps = True; cu.materials.append(mLine)
cu.bevel_factor_start = 0.0
for _f, _v in ((0, 0.0), (12, 1.0)): cu.bevel_factor_end = _v; cu.keyframe_insert('bevel_factor_end', frame=_f)   # the arc draws on by f12 (hook event)
NP = 5 * 6 + 1; sp = cu.splines.new('POLY'); sp.points.add(NP - 1); LINE = link(D.objects.new('CurveLine', cu)); LINE['src'] = 'own'
for f in range(NF):
    degs, sl = pose(f); Ms = chain_mats(degs, sl); pp = catmull([Ms[bi] @ p for bi, p in reversed(ARC)], 6)
    for i, q in enumerate(pp[:NP]):
        sp.points[i].co = (q.x, q.y, q.z, 1.0); sp.points[i].keyframe_insert('co', frame=f)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
json.dump({str(f): pose(f)[0] for f in range(NF)}, open(HERE + '/pose_dump.json', 'w'))   # per-frame joint angles for caption_truth / rigid_bend checks
for tag, sks in BULGE.items():
    for sk in sks:
        for f, v in ((0, 0), (520, 0), (620, 1), (855, 1), (930, 0)): sk.value = v; sk.keyframe_insert('value', frame=f)
# disc beat: the cord turns translucent so the root and the bulging disc can be seen behind it; root + contact pulse
for f, v in ((0, 0.0), (40, 0.0), (70, 1.0), (490, 1.0), (525, 0.18), (565, 0.0), (745, 0.0), (785, 1.0)): vkey(fadeC, f, v)   # review 7: the translucent cord veiled the lobe (pale pink patch); it is fully gone while lobe and root touch
vis(D.objects['SpinalCord'], [(0, 568), (742, NF + 1)])   # hide_render too: a faded-out object still renders dark marks
pulse(eRoot, [606, 650, 694], base=0.0, peak=5.0, width=10)   # contact flash only
for f, v in ((0, 1.0), (96, 1.0), (110, 0.0), (290, 0.0), (305, 1.0), (510, 1.0), (540, 0.0), (NF, 0.0)): vkey(fadeL, f, v)   # arc only in beats 1 and 3; gone before the load arrow
# muscles: fade in, tension pulses on the posterior group, fade out
for f, v in ((0, 0.0), (752, 0.0), (790, 1.0), (860, 1.0), (888, 0.0)): vkey(fadeM, f, v)
for o in MUS: vis(o, [(752, 890)])
[setattr(n.inputs['Emission Color'], 'default_value', (0.9, 0.04, 0.03, 1)) for n in mMus.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
for f, v in ((0, 0.0), (790, 0.0), (800, 0.05), (850, 0.12), (870, 0.12), (888, 0.0)): vkey(eMus, f, v)   # one slow swell: tightening, stays red
for f, v in ((0, 3.0), (9, 3.0), (12, 10.0), (19, 3.0)): vkey(eLine, f, v)   # review 7 item 4: the arc finishes drawing at f12 with a flash, in time with the pulse sound (0.45 s)
# disc close-up: less bloom
sc.view_settings.exposure = -0.6; sc.view_settings.keyframe_insert('exposure', frame=0); sc.view_settings.keyframe_insert('exposure', frame=500)
sc.view_settings.exposure = -1.0; sc.view_settings.keyframe_insert('exposure', frame=550); sc.view_settings.keyframe_insert('exposure', frame=750)
sc.view_settings.exposure = -0.6; sc.view_settings.keyframe_insert('exposure', frame=790)
# herniation lobe (own, illustrative): gel pushed out of the C5/C6 annulus toward the C6 root, scaled in with the bulge
import bmesh as _bm
_b = _bm.new(); _bm.ops.create_uvsphere(_b, u_segments=32, v_segments=20, radius=0.0055); _me = D.meshes.new('Herniation'); _b.to_mesh(_me); _b.free()
for _pg in _me.polygons: _pg.use_smooth = True
HER = link(D.objects.new('Herniation', _me)); HER['src'] = 'own'
mHer, eHer = tissue('HerniationMat', (0.95, 0.14, 0.02, 1), 0.42, 0.0); setmat(HER, mHer)
[(setattr(n.inputs['Coat Weight'], 'default_value', 0.0), setattr(n.inputs['Specular IOR Level'], 'default_value', 0.1)) for n in mHer.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
[setattr(n.inputs['Emission Color'], 'default_value', (1.0, 0.16, 0.02, 1)) for n in mHer.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
_i = INFO['C5C6']; HER.location = (0.0055, _i['yc'] + _i['rb'][12] - 0.0030, _i['zm'] - 0.0006); HER.scale = (1, 1, 1)   # centred inside the annulus edge; stretched toward the root below
HER.parent = D.objects['Vertebra C6']   # rest-pose parenting: bodies are identity at rest, location = rest world position (FKChain._parent would bake the pose of the frame the file was saved on)
_dm = HER.modifiers.new('irr', 'DISPLACE'); _tx = D.textures.new('irr', 'CLOUDS'); _tx.noise_scale = 0.5; _dm.texture = _tx; _dm.strength = 0.0026; _dm.mid_level = 0.5   # irregular, not a bead
for f, v in ((0, 0.001), (580, 0.001), (600, 1.0), (750, 1.0), (766, 0.001), (NF, 0.001)):
    HER.scale = (v * 0.95, v * 1.55, v * 0.8); HER.keyframe_insert('scale', frame=f)   # stretched along +y: continuous with the disc, reaching the root
vkey(eHer, 0, 0.8)   # saturated lobe (review 7: it read as a pale orange patch)
# contact: the root turns red only where the lobe touches it (point-masked emission), pulsing with the lobe
_rv = D.objects['SpinalRoots'].data.vertices; _hp = Vector(HER.location); _near = min(_rv, key=lambda v: (v.co - _hp).length).co.copy()
nt_r = mRoot.node_tree; [setattr(n.inputs['Emission Color'], 'default_value', (1.0, 0.08, 0.02, 1)) for n in nt_r.nodes if n.type == 'BSDF_PRINCIPLED']
_cp = chain_mats(*pose(640))[2] @ _near   # contact ring (thin), not a halo
_nt2 = mRoot.node_tree; _pp2 = [n for n in _nt2.nodes if n.type == 'BSDF_PRINCIPLED'][0]
for _l in list(_pp2.inputs['Emission Strength'].links): _nt2.links.remove(_l)
_g2 = _nt2.nodes.new('ShaderNodeNewGeometry'); _d2 = _nt2.nodes.new('ShaderNodeVectorMath'); _d2.operation = 'DISTANCE'; _d2.inputs[1].default_value = _cp; _nt2.links.new(_g2.outputs['Position'], _d2.inputs[0])
_s2 = _nt2.nodes.new('ShaderNodeMath'); _s2.operation = 'SUBTRACT'; _s2.inputs[1].default_value = 0.0030; _nt2.links.new(_d2.outputs['Value'], _s2.inputs[0]); _a2 = _nt2.nodes.new('ShaderNodeMath'); _a2.operation = 'ABSOLUTE'; _nt2.links.new(_s2.outputs[0], _a2.inputs[0])
_m2 = _nt2.nodes.new('ShaderNodeMapRange'); _m2.interpolation_type = 'SMOOTHSTEP'; _m2.inputs['From Min'].default_value = 0.0; _m2.inputs['From Max'].default_value = 0.00035; _m2.inputs['To Min'].default_value = 1.0; _m2.inputs['To Max'].default_value = 0.0; _nt2.links.new(_a2.outputs[0], _m2.inputs['Value'])
_x2 = _nt2.nodes.new('ShaderNodeMath'); _x2.operation = 'MULTIPLY'; _nt2.links.new(_m2.outputs['Result'], _x2.inputs[0]); _nt2.links.new(eRoot.outputs[0], _x2.inputs[1]); _nt2.links.new(_x2.outputs[0], _pp2.inputs['Emission Strength'])
anchor_pt = _near
# thin ring on the touch point (review 7): a torus of 2.4 mm radius and 0.18 mm tube, facing the disc-beat camera, parented to C6; it scales in with the lobe
_rg = _bm.new(); _N, _R, _r = 48, 0.0024, 0.00018
_rv = [[_rg.verts.new(((_R + _r * math.cos(2 * math.pi * j / 8)) * math.cos(2 * math.pi * i / _N), (_R + _r * math.cos(2 * math.pi * j / 8)) * math.sin(2 * math.pi * i / _N), _r * math.sin(2 * math.pi * j / 8))) for j in range(8)] for i in range(_N)]
for i in range(_N):
    for j in range(8): _rg.faces.new((_rv[i][j], _rv[i][(j + 1) % 8], _rv[(i + 1) % _N][(j + 1) % 8], _rv[(i + 1) % _N][j]))
_rme = D.meshes.new('ContactRing'); _rg.to_mesh(_rme); _rg.free(); RING = link(D.objects.new('ContactRing', _rme)); RING['src'] = 'own'
mRing, eRing = tissue('RingMat', (1.0, 0.85, 0.45, 1), 0.3, 0.0); setmat(RING, mRing); vkey(eRing, 0, 2.5); RING.parent = D.objects['Vertebra C6']; RING.location = _near
RING.rotation_mode = 'QUATERNION'; RING.rotation_quaternion = Vector((-1.0, 0.27, 0.11)).normalized().to_track_quat('Z', 'Y')
for f, v in ((0, 0.001), (606, 0.001), (626, 1.0), (735, 1.0), (755, 0.001), (NF, 0.001)): RING.scale = (v, v, v); RING.keyframe_insert('scale', frame=f)
HER.location = Vector((_near.x - 0.0004, _near.y - 0.0036, _near.z)); HER.location.x = max(0.003, HER.location.x)   # the stretched lobe ends on the root contact point

_kk = {0: 0.001, 580: 0.001, 600: 1.0, 750: 1.0, 766: 0.001, NF: 0.001}
def _lin(f, kk):
    ks = sorted(kk)
    for a, c in zip(ks, ks[1:]):
        if a <= f <= c: return kk[a] + (kk[c] - kk[a]) * (f - a) / (c - a)
    return kk[ks[-1]]
_kl = {0: 1.0, 96: 1.0, 110: 0.0, 290: 0.0, 305: 1.0, 510: 1.0, 540: 0.0, NF: 0.0}; _ks = {0: 0.0, 858: 0.0, 890: 1.0, NF: 1.0}; _km = {0: 0.0, 790: 0.0, 800: 0.08, 850: 0.25, 870: 0.25, 888: 0.0, NF: 0.0}
_ke = {0: 0.001, 870: 0.001, 895: 1.0, NF: 1.0}
_kv = {0: 0.0, 6: 1.0, 45: 0.9, 110: 0.0, NF: 0.0}
_ksk = {0: 1.0, 10: 1.0, 11: 0.0, 847: 0.0, 848: 1.0, NF: 1.0}
json.dump({'SkinRender': {str(f): _lin(f, _ksk) for f in range(NF)}, 'VertebraTint': {str(f): _lin(f, _kv) for f in range(NF)}, 'Herniation': {str(f): _lin(f, _kk) for f in range(NF)}, 'CurveLine': {str(f): _lin(f, _kl) for f in range(NF)}, 'Shoulder': {str(f): _lin(f, _ks) for f in range(NF)}, 'MuscleGlow': {str(f): _lin(f, _km) for f in range(NF)}}, open(HERE + '/scene_dump.json', 'w'))
# ---------------- anchors for the 2D label layer
def anchor(name, parent, p):
    e = D.objects.new(name, None); link(e); e.location = p; e.parent = parent if parent else None; return e   # rest-pose parent (identity inverse): the anchor follows the body exactly like the hooked skin does; FKChain._parent baked the saved frame's pose (A_Ear was 1 cm off the ghost's ear)
anchor('A_Head', D.objects['Skull'], Vector((0, 0.002, 1.615))); anchor('A_C7', D.objects['Vertebra C7'], Vector((0, INFO['C6C7']['yc'], 1.446)))
_ep = EAR_P
A_EAR = anchor('A_Ear', D.objects['Skull'], Vector((_ep.x, _ep.y, _ep.z)))   # ear canal opening above/behind the jaw joint; the 2D layer draws the ear outline from the shape below
def _ear_shape():
    """left ear seen from the side, (y, z) in metres relative to the canal opening; y > 0 is posterior. Outer rim (helix + lobe), inner antihelix arc, tragus tick."""
    a, b, tilt = 0.0315, 0.0185, math.radians(14); cy, cz = 0.0050, 0.0040
    def rot(yy, zz): return (yy * math.cos(tilt) + zz * math.sin(tilt) + cy, -yy * math.sin(tilt) + zz * math.cos(tilt) + cz)
    outer = []
    for k in range(48):
        t = 2 * math.pi * k / 48; yy = b * math.sin(t) * (1 + 0.16 * math.cos(t)); zz = a * math.cos(t)
        if math.cos(t) < -0.35: yy *= 0.80                       # the lobe is narrower
        if math.sin(t) < 0 and -0.5 < math.cos(t) < -0.1: yy *= 0.82   # intertragic notch on the front edge
        outer.append(rot(yy, zz))
    inner = [rot(0.62 * b * math.sin(t) + 0.002, 0.66 * a * math.cos(t) + 0.002) for t in [math.pi * (0.08 + 0.84 * k / 20) for k in range(21)]]   # antihelix: arc along the posterior side
    tragus = [rot(-0.55 * b, 0.10 * a), rot(-0.30 * b, 0.0), rot(-0.55 * b, -0.18 * a)]
    return outer, inner, tragus
_eo, _ei, _et = _ear_shape(); A_EAR['ear_outer'] = json.dumps(_eo); A_EAR['ear_inner'] = json.dumps(_ei); A_EAR['ear_tragus'] = json.dumps(_et)
anchor('A_TMJ', D.objects['Skull'], TMJ_P)   # jaw joint, for the ear-position gate
_ac = ACRO_P; anchor('A_Acro', None, _ac)   # shoulder tip = acromial end of the clavicle (the clavicle ends exactly here)
anchor('A_Contact', D.objects['Vertebra C6'], anchor_pt)
anchor('A_C56', D.objects['Vertebra C5'], Vector((0.0055, INFO['C5C6']['yc'] + INFO['C5C6']['rb'][12], INFO['C5C6']['zm'])))
_g = [v.co for v in D.objects['SpinalGanglia'].data.vertices if abs(v.co.z - INFO['C5C6']['zm'] + 0.0012) < 0.0025]
anchor('A_Root', D.objects['Vertebra C6'], sum(_g, Vector()) / len(_g))
# ---------------- camera: skull base -> T2 fills the band height
cam = CameraPath(lens=70, fstop=11)
for _f, _v in ((0, 35), (10, 62), (20, 70)): cam.cam.data.lens = _v; cam.cam.data.keyframe_insert('lens', frame=_f)   # establishing shot: wide full body, zoom into the neck over ~1.5 s
for _f, _v in ((0, 8), (500, 8), (540, 22), (790, 22), (830, 8)): cam.cam.data.dof.aperture_fstop = _v   # shallow DOF on the subject in the wide beats, deeper in the disc close-up; cam.cam.data.dof.keyframe_insert('aperture_fstop', frame=_f)
ENDAZ = -32; ENDEL = -0.12   # ending view: turned 32 deg behind the patient so the shoulder tip (14 cm lateral) separates from the spine on screen
def dirn(az, el=0.03): return Vector((-math.cos(math.radians(az)), math.sin(math.radians(az)), el))
DC0 = Vector((0.004, INFO['C5C6']['yc'], INFO['C5C6']['zm'])); DCa = chain_mats(*pose(570))[2] @ DC0; DCb = chain_mats(*pose(750))[2] @ DC0
for f, tg, d, dist in ((0, Vector((0, 0.0, 1.22)), dirn(0, 0.0), 1.15), (10, Vector((0, 0.006, 1.40)), dirn(-2, 0.01), 0.66), (20, Vector((0, 0.012, 1.495)), dirn(-4), 0.58), (60, Vector((0, 0.012, 1.50)), dirn(0), 0.66), (110, Vector((0, 0.008, 1.50)), dirn(2), 0.76), (210, Vector((-0.004, 0.0, 1.49)), dirn(4), 0.84),
                       (300, Vector((-0.012, -0.002, 1.49)), dirn(-3), 0.92), (360, Vector((-0.006, 0.005, 1.495)), dirn(4), 0.70), (440, Vector((-0.01, 0.004, 1.49)), dirn(-2), 0.72), (510, Vector((-0.014, 0.004, 1.49)), dirn(3), 0.74),
                       (570, DCa + Vector((0.0, 0.004, 0.0)), Vector((-1, 0.22, 0.10)), 0.20), (660, DCa + Vector((0.003, 0.007, -0.002)), Vector((-1, 0.27, 0.11)), 0.175), (750, DCb + Vector((0.004, 0.006, 0.0)), Vector((-1, 0.30, 0.12)), 0.15),
                       (800, Vector((0, 0.01, 1.49)), dirn(0), 0.66), (870, Vector((0.0, 0.02, 1.51)), dirn(-ENDAZ, ENDEL), 0.86), (960, Vector((0.0, 0.02, 1.51)), dirn(-ENDAZ, ENDEL), 0.76), (NF - 1, Vector((0.0, 0.02, 1.51)), dirn(-ENDAZ, ENDEL), 0.68)):
    cam.key(f, tg, d, dist)
N0 = Vector((0, 0.012, 1.52))
# ---------------- light + render
t = link(D.objects.new('LightTarget', None)); t.location = N0
def area(name, off, energy, size, color):
    d = D.lights.new(name, 'AREA'); d.energy = energy; d.size = size; d.color = color
    o = link(D.objects.new(name, d)); o.location = Vector(N0) + Vector(off)
    c = o.constraints.new('TRACK_TO'); c.target = t; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
area('Key', (-0.55, -0.35, 0.45), 9, 0.35, (1.0, 0.94, 0.86)); area('Fill', (-0.6, 0.3, -0.1), 1.5, 0.5, (0.8, 0.88, 1.0))
area('Rim', (0.25, 0.45, 0.35), 14, 0.2, (0.75, 0.88, 1.0)); area('Rim2', (0.2, -0.4, 0.3), 8, 0.2, (1.0, 0.85, 0.7))
w = D.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = D.images.load(KIT + '/assets/studio_small_09_2k.exr'); w.node_tree.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.14
render_settings(*EP['render']['res'], spp=EP['render']['spp'], blur=0)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.6
sc.render.use_persistent_data = True; sc.cycles.sample_clamp_direct = 8; sc.cycles.sample_clamp_indirect = 3
from bpy_extras.object_utils import world_to_camera_view as _w2c
def _sx(f):
    sc.frame_set(f); bpy.context.view_layer.update(); cm = sc.camera
    return _w2c(sc, cm, D.objects['A_Ear'].matrix_world.translation).x - _w2c(sc, cm, D.objects['A_Acro'].matrix_world.translation).x
# ear over shoulder, aligned by moving the SHOULDER GIRDLE (clavicle, scapula, acromion anchor), not the head: the ear now sits above the jaw joint (review 7), and sliding the head
# to meet the old shoulder pulled the skull off C1. The girdle is not skinned, so one translation along y (anterior-posterior) is exact; the head keeps its neutral posture.
_f0 = 950; _d0 = _sx(_f0); _GIRDLE = [D.objects['Clavicle.l'], D.objects['Scapula.l'], D.objects['A_Acro']]
for _o in _GIRDLE: _o.location.y += 0.01
_d1 = _sx(_f0); _tsh = -_d0 / ((_d1 - _d0) / 0.01) if abs(_d1 - _d0) > 1e-6 else 0.0; _tsh = max(-0.08, min(0.08, _tsh))
for _o in _GIRDLE: _o.location.y += _tsh - 0.01
bpy.context.view_layer.update(); print('shoulder girdle shifted by', round(_tsh, 4), 'm (screen dx before', round(_d0, 4), 'after', round(_sx(_f0), 5), ')')
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=HERE + '/neck.blend'); print('SAVED')
