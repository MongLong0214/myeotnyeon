# Stage C (fast, every draft): rig + materials + animation + camera + light. usage: Blender -b neck_solids.blend -P build.py  -> neck.blend
import sys, os, json, math
sys.path.insert(0, os.path.join(os.environ['ANAT_KIT'],'blender'))
import bpy
from kit import *; from kit_spine import *; from kit_astra import Astra
HERE = os.environ['ANAT_EPISODE']; EP = json.load(open(HERE + '/episode.json')); INFO = json.load(open(HERE + '/disc_info.json'))
sc = bpy.context.scene; FPS = EP['fps']; NF = int(FPS * EP['duration']); sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = NF - 1
X_CUT = 0.001
BODIES = ['Vertebra T1', 'Vertebra C7', 'Vertebra C6', 'Vertebra C5', 'Vertebra C4', 'Vertebra C3', 'Axis (C2)', 'Atlas (C1)', 'Skull']
B = [D.objects[n] for n in BODIES]
# Older prepared solids contain only the far-side girdle. Register the camera-side
# DBCLS originals in the same coordinates as Stage A before fitting the endpoint.
from pathlib import Path
import hashlib
for name, fma, fj in [('Clavicle.r', 'FMA13322', 'FJ3362'), ('Scapula.r', 'FMA13395', 'FJ3384'), ('Temporal.r', 'FMA52738', 'FJ3386')]:
    if D.objects.get(name):
        continue
    root = Path(os.environ.get('BP3D_ROOT', (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../../research/anatomy3d/bodyparts3d_4.0')))
    obj_file = root / 'obj/isa_BP3D_4.0_obj_99' / (fj + '.obj')
    bpy.ops.wm.obj_import(filepath=str(obj_file), forward_axis='Y', up_axis='Z')
    obj = bpy.context.selected_objects[0]
    obj.name = name
    obj.data.transform(Matrix.Translation((0, .089, .072)) @ Matrix.Scale(.001, 4))
    obj['src'] = 'bp3d:%s:%s:%s' % (fma, fj, hashlib.sha256(obj_file.read_bytes()).hexdigest())
    for face in obj.data.polygons:
        face.use_smooth = True
# landmarks (computed first: the ending pose aligns the ear over the shoulder)
_mz0 = max(v.co.z for v in D.objects['Mandible'].data.vertices); _cd0 = [v.co for v in D.objects['Mandible'].data.vertices if v.co.z > _mz0 - 0.006 and v.co.x > 0.02]
TMJ_P = sum(_cd0, Vector()) / len(_cd0)   # centre of the mandibular condyle = the jaw joint
# The lateral depth map of DBCLS FJ3386 places the ear recess behind the
# mandibular fossa. Seat the marker on the displayed temporal bone itself.
bpy.context.view_layer.update()
hit, EAR_P, _, _ = D.objects['Temporal.r'].ray_cast(Vector((-.15, .004, 1.578)), Vector((1, 0, 0)))
if not hit:
    raise ValueError('right temporal surface missing at registered ear site')
clavicle_tip = min((v.co for v in D.objects['Clavicle.r'].data.vertices), key=lambda p: p.x)
scapula_points = [v.co for v in D.objects['Scapula.r'].data.vertices]
joint = min(scapula_points, key=lambda p: (p-clavicle_tip).length_squared)
# The superior surface of the acromion is exposed; the opposing joint face is internal.
ACRO_P = max((p for p in scapula_points if (p-joint).length <= .005), key=lambda p: p.z).copy()
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
_ma = _mt.nodes.new('ShaderNodeAttribute'); _ma.attribute_name = 'tend'; _mx = _mt.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs['B'].default_value = (0.46, 0.20, 0.14, 1)
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
    e = np.minimum(tn, 1 - tn); tend = 1 - np.clip(e / 0.04, 0, 1) ** 2 * (3 - 2 * np.clip(e / 0.04, 0, 1))   # 1 at the ends, 0 in the belly
    at = me.attributes.new('tend', 'FLOAT', 'POINT'); at.data.foreach_set('value', tend.astype(np.float32))
    uvl = me.uv_layers.new(name='fibre'); li = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', li)
    uv = np.c_[uu[li], t[li]].astype(np.float32); uvl.data.foreach_set('uv', uv.ravel())
    o.shape_key_add(name='Basis'); _sk = o.shape_key_add(name='Contract'); _rel = a - c; _tt = _rel @ ax; _new = c + np.outer(_tt * 0.93, ax) + (_rel - np.outer(_tt, ax)) * 1.09   # contraction: 12 % shorter along the fibre axis, 10 % thicker
    for _i, _v in enumerate(_new): _sk.data[_i].co = tuple(_v)
    return len(me.vertices)
for o in MUS: print('belly', o.name, muscle_belly(o, 0.0018, 1.49 if 'trapezius' in o.name else None))
_mt = mMus.node_tree
# hook: the cervical cut faces glow amber at the start (the C-curve is the subject), fading out by f110
mTC, vTC = tint_material(D.materials['Trabecular'], name='TrabC')
for n in ('Axis (C2)', 'Vertebra C3', 'Vertebra C4', 'Vertebra C5', 'Vertebra C6', 'Vertebra C7'):
    o = D.objects[n]; i = [m.name if m else '' for m in o.data.materials].index('Trabecular'); o.data.materials[i] = mTC
for f, v in ((0, 0.0), (84, 0.0), (100, 1.0), (128, 0.3), (140, 0.35), (156, 0.35), (200, 0.35), (212, 0.65), (238, 0.65), (262, 0.65), (278, 1.0), (300, 1.0), (345, 0.0)): vkey(vTC, f, v)   # review 15: number-free load cue, the lower-neck glow steps up with each tilt (15, 30, 60 deg)
# CC0 skin shell: translucent, dissolves in at the start and at the ending
mSkin, nt_, out_, p_ = newmat('SkinGhost'); p_.inputs['Base Color'].default_value = (0.86, 0.60, 0.50, 1); p_.inputs['Roughness'].default_value = 0.5; p_.inputs['Subsurface Weight'].default_value = 0.3
fadeS = nt_.nodes.new('ShaderNodeValue'); fadeS.name = 'Fade'; lw_ = nt_.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.5
mr_ = nt_.nodes.new('ShaderNodeMapRange'); mr_.inputs['To Min'].default_value = 0.16; mr_.inputs['To Max'].default_value = 0.62; nt_.links.new(lw_.outputs['Facing'], mr_.inputs['Value'])
mu_ = nt_.nodes.new('ShaderNodeMath'); mu_.operation = 'MULTIPLY'; nt_.links.new(mr_.outputs['Result'], mu_.inputs[0]); nt_.links.new(fadeS.outputs[0], mu_.inputs[1])   # same opacity on back faces: the far half of the shell is what we look at
geo_ = nt_.nodes.new('ShaderNodeNewGeometry'); sz_ = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], sz_.inputs[0])
mz_ = nt_.nodes.new('ShaderNodeMapRange'); mz_.interpolation_type = 'SMOOTHSTEP'; nt_.links.new(sz_.outputs['Z'], mz_.inputs['Value'])
_zmin = nt_.nodes.new('ShaderNodeValue'); _zmax = nt_.nodes.new('ShaderNodeValue'); nt_.links.new(_zmin.outputs[0], mz_.inputs['From Min']); nt_.links.new(_zmax.outputs[0], mz_.inputs['From Max'])
for f, a, b in ((0, 0.95, 1.38), (20, 0.95, 1.38), (850, 0.95, 1.38), (968, 0.95, 1.38), (1004, 1.33, 1.43), (NF, 1.33, 1.43)): vkey(_zmin, f, a); vkey(_zmax, f, b)   # opening: whole figure; ending: the torso is gone by the frame bottom, no grey slab behind the cord
mu2_ = nt_.nodes.new('ShaderNodeMath'); mu2_.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], mu2_.inputs[0]); nt_.links.new(mz_.outputs['Result'], mu2_.inputs[1]); mu_ = mu2_   # fade out toward the bottom
_gx = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], _gx.inputs[0]); _mx2 = nt_.nodes.new('ShaderNodeMapRange'); _mx2.interpolation_type = 'SMOOTHSTEP'; _mx2.inputs['From Min'].default_value = 0.001; _mx2.inputs['From Max'].default_value = 0.020
nt_.links.new(_gx.outputs['X'], _mx2.inputs['Value']); _mu3 = nt_.nodes.new('ShaderNodeMath'); _mu3.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], _mu3.inputs[0]); nt_.links.new(_mx2.outputs['Result'], _mu3.inputs[1]); mu_ = _mu3   # soft edge where the shell is cut (no jagged rim)
_fy = nt_.nodes.new('ShaderNodeMapRange'); _fy.interpolation_type = 'SMOOTHSTEP'; _fy.inputs['From Min'].default_value = -0.06; _fy.inputs['From Max'].default_value = -0.02; _sy = nt_.nodes.new('ShaderNodeSeparateXYZ'); nt_.links.new(geo_.outputs['Position'], _sy.inputs[0]); nt_.links.new(_sy.outputs['Y'], _fy.inputs['Value'])
_fz = nt_.nodes.new('ShaderNodeMapRange'); _fz.interpolation_type = 'SMOOTHSTEP'; _fz.inputs['From Min'].default_value = 1.46; _fz.inputs['From Max'].default_value = 1.50; nt_.links.new(_sy.outputs['Z'], _fz.inputs['Value'])
_fi = nt_.nodes.new('ShaderNodeMath'); _fi.operation = 'SUBTRACT'; _fi.inputs[0].default_value = 1.0; nt_.links.new(_fz.outputs['Result'], _fi.inputs[1]); _fm = nt_.nodes.new('ShaderNodeMath'); _fm.operation = 'MAXIMUM'; nt_.links.new(_fy.outputs['Result'], _fm.inputs[0]); nt_.links.new(_fi.outputs[0], _fm.inputs[1])
_fmu = nt_.nodes.new('ShaderNodeMath'); _fmu.operation = 'MULTIPLY'; nt_.links.new(mu_.outputs[0], _fmu.inputs[0]); nt_.links.new(_fm.outputs[0], _fmu.inputs[1]); mu_ = _fmu   # the soft orange-brown smear in front of the ghost's lips (f890-f989) is gone: the face front fades out
tr_ = nt_.nodes.new('ShaderNodeBsdfTransparent'); ms_ = nt_.nodes.new('ShaderNodeMixShader'); nt_.links.new(mu_.outputs[0], ms_.inputs['Fac']); nt_.links.new(tr_.outputs[0], ms_.inputs[1]); nt_.links.new(p_.outputs[0], ms_.inputs[2]); nt_.links.new(ms_.outputs[0], out_.inputs['Surface'])
setmat(D.objects['Skin'], mSkin)
_mx = nt_.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs['A'].default_value = (0.86, 0.60, 0.50, 1); _mx.inputs['B'].default_value = (1.0, 0.45, 0.04, 1); tintS = nt_.nodes.new('ShaderNodeValue')
nt_.links.new(tintS.outputs[0], _mx.inputs['Factor']); nt_.links.new(_mx.outputs['Result'], p_.inputs['Base Color']); nt_.links.new(_mx.outputs['Result'], p_.inputs['Emission Color']); _ts = nt_.nodes.new('ShaderNodeMath'); _ts.operation = 'MULTIPLY'; _ts.inputs[1].default_value = 2.2; nt_.links.new(tintS.outputs[0], _ts.inputs[0]); nt_.links.new(_ts.outputs[0], p_.inputs['Emission Strength'])
for f, v in ((0, 1.0), (30, 1.0), (75, 0.0)): vkey(tintS, f, v)   # the establishing figure glows amber (hook subject), then settles to skin tone
for f, v in ((0, 1.0), (3, 1.0), (9, 0.0), (850, 0.0), (900, 1.0), (NF, 1.0)): vkey(fadeS, f, v)   # the ghost dissolves by f9: its throat sheet shears into fans once the head tilts (f9-12 in draft10)
D.objects['Skin'].hide_render = True   # draft20: the CC0 base-mesh ghost is replaced by the rigged MPFB person (kit_human.py); it stays in the file only for provenance   # faded-out skin still rendered dark scratch marks: hide_render as well
mShoulder = D.materials['BoneBase'].copy(); mShoulder.name = 'BoneShoulder'; fadeSh = add_fade(mShoulder)
SHD = (0.78, 0.70, 0.58)   # measured against the spine in the f950 render (verify)
# shoulder girdle: the vertebrae's bone material, darkened toward their tan (review 6/7: it still read brighter and whiter than the spine)
for _n in mShoulder.node_tree.nodes:
    if _n.type == 'VALTORGB':
        for _e in _n.color_ramp.elements: _e.color = (_e.color[0] * SHD[0], _e.color[1] * SHD[1], _e.color[2] * SHD[2], 1)
    if _n.type == 'BSDF_PRINCIPLED': _n.inputs['Subsurface Weight'].default_value = 0.04
for _n in ('Clavicle.l', 'Scapula.l', 'Clavicle.r', 'Scapula.r'):
    obj = D.objects[_n]
    obj.data.materials.clear()
    setmat(obj, mShoulder)
    vis(obj, [(748, 830)] if _n.endswith('.l') else [(1020, NF + 1)])
def mask_material(material, factor):
    tree = material.node_tree
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    previous = output.inputs['Surface'].links[0].from_socket
    mix = tree.nodes.new('ShaderNodeMixShader')
    clear = tree.nodes.new('ShaderNodeBsdfTransparent')
    tree.links.new(factor, mix.inputs[0])
    tree.links.new(clear.outputs[0], mix.inputs[1])
    tree.links.new(previous, mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs['Surface'])

temporal_material = mShoulder.copy()
temporal_fade = add_fade(temporal_material)
for frame, opacity in [(0, 0), (1024, 0), (1034, 1), (NF, 1)]:
    vkey(temporal_fade, frame, opacity)
# Reveal the ear-site cortex under the marker, preserving the sagittal brain view.
tree = temporal_material.node_tree
coords = tree.nodes.new('ShaderNodeTexCoord')
distance = tree.nodes.new('ShaderNodeVectorMath')
distance.operation = 'DISTANCE'
distance.inputs[1].default_value = EAR_P
tree.links.new(coords.outputs['Object'], distance.inputs[0])
edge = tree.nodes.new('ShaderNodeMapRange')
edge.interpolation_type = 'SMOOTHSTEP'
for socket, value in [('From Min', .009), ('From Max', .019), ('To Min', 1), ('To Max', 0)]:
    edge.inputs[socket].default_value = value
tree.links.new(distance.outputs['Value'], edge.inputs['Value'])
mask_material(temporal_material, edge.outputs['Result'])
setmat(D.objects['Temporal.r'], temporal_material)
vis(D.objects['Temporal.r'], [(1024, NF + 1)])
for f, v in ((0, 0), (748, 0), (761, 1), (814, 1), (829, 0), (1000, 0), (1030, 1), (NF, 1)):
    vkey(fadeSh, f, v)
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
zfade_mat(mCord, 1.44, 1.40)   # review 7: the cord hung out as a bare stick below the last vertebra at 27 kg (f270-f330): it fades with the vertebrae it runs through
zfade_mat(mMus, 1.445, 1.41)   # ... and an orange muscle tip poked through the bottom fade at f820
import bmesh as _bmd
_bd = _bmd.new(); _bd.from_mesh(D.objects['Axis (C2)'].data); _bmd.ops.bisect_plane(_bd, geom=_bd.verts[:] + _bd.edges[:] + _bd.faces[:], plane_co=(0, 0.028, 0), plane_no=(0, 1, 0), clear_outer=True)
_be = [e for e in _bd.edges if e.is_boundary]; _bmd.ops.holes_fill(_bd, edges=_be, sides=max(4, len(_be))); _bmd.ops.triangulate(_bd, faces=_bd.faces[:]); _bd.to_mesh(D.objects['Axis (C2)'].data); _bd.free()   # ray cast at f30 (740-810,350-420): the oval is the cut tip of C2's spinous process (rest y 4.3 cm, z 1.514), which overlaps the cerebellum in the reversed pose and read as an ear outline; its tip is trimmed. Before: the beside the cerebellum (f15-f60, f490, f820; review 8)
_bx = _bmd.new(); _bx.from_mesh(D.objects['Axis (C2)'].data); _bmd.ops.bisect_plane(_bx, geom=_bx.verts[:] + _bx.edges[:] + _bx.faces[:], plane_co=(0, 0, 1.536), plane_no=(0, 0, 1), clear_outer=True)
_bxe = [e for e in _bx.edges if e.is_boundary]; _bmd.ops.holes_fill(_bx, edges=_bxe, sides=max(4, len(_bxe))); _bmd.ops.triangulate(_bx, faces=_bx.faces[:]); _bx.to_mesh(D.objects['Axis (C2)'].data); _bx.free()   # review 11: stippled oval on the skull cut face at f28 (790-815,495-515): the dens tip overlapped the skull
_ba = _bmd.new(); _ba.from_mesh(D.objects['Atlas (C1)'].data); _bmd.ops.bisect_plane(_ba, geom=_ba.verts[:] + _ba.edges[:] + _ba.faces[:], plane_co=(0, 0.034, 0), plane_no=(0, 1, 0), clear_outer=True)
_bae = [e for e in _ba.edges if e.is_boundary]; _bmd.ops.holes_fill(_ba, edges=_bae, sides=max(4, len(_bae))); _bmd.ops.triangulate(_ba, faces=_ba.faces[:]); _ba.to_mesh(D.objects['Atlas (C1)'].data); _ba.free()   # review 10: the small outlined shape on the cerebellum at f28 (775-800,395-420; ray cast: Atlas posterior tip)
for _rn in ('Rim_Axis_(C2)', 'Rim_Atlas_(C1)'):
    for _sp in list(D.objects[_rn].data.splines):   # rim loops across C1-C2 looked like wire
        _ps = [p.co.y for p in (_sp.points if _sp.type in ('POLY', 'NURBS') else _sp.bezier_points)]
        if _ps and sum(_ps) / len(_ps) > 0.026: D.objects[_rn].data.splines.remove(_sp)
for _n in ('Brain',): drop_small_parts(D.objects[_n], 5000)   # two stray brain islands (cut face + cortical ring) read as a second "ear" beside the cerebellum at f18-f60 and f765-f800 (review 7)
# review 9: amber beads (root/ganglion ends) float beside the upper neck at f900 (485,440) and f30 (780,410): drop root and ganglion geometry above C2's lower border
import bmesh as _bmg
for _n in ('SpinalRoots', 'SpinalGanglia'):
    _bg = _bmg.new(); _bg.from_mesh(D.objects[_n].data); _bmg.ops.delete(_bg, geom=[v for v in _bg.verts if v.co.z > 1.503], context='VERTS'); _bg.to_mesh(D.objects[_n].data); _bg.free()
# review 7 item 5: cortical rim on every cut vertebra twice as thick and a brighter, denser cortex colour; disc annulus lighter with a visible ring, nucleus translucent
for _o in [o for o in D.objects if o.name.startswith('Rim_') and o.type == 'CURVE']:
    _o.data.bevel_depth *= 2.2
    for _sp in list(_o.data.splines):   # tiny loops left by the deleted islands (Rim_Vertebra_T2's loop was the white speck beside the spine)
        _pp = [p.co.xyz if hasattr(p, 'co') else p.co for p in (_sp.points if _sp.type == 'POLY' or _sp.type == 'NURBS' else _sp.bezier_points)]
        _xs = [Vector(p) for p in _pp]; _d = (Vector((max(v.x for v in _xs), max(v.y for v in _xs), max(v.z for v in _xs))) - Vector((min(v.x for v in _xs), min(v.y for v in _xs), min(v.z for v in _xs)))).length if _xs else 0
        if _d < 0.006: _o.data.splines.remove(_sp)
for _n in D.materials['Cortex'].node_tree.nodes:
    if _n.type == 'BSDF_PRINCIPLED': _n.inputs['Base Color'].default_value = (0.96, 0.90, 0.76, 1); _n.inputs['Roughness'].default_value = 0.35
vis(D.objects['Rim_Skull'], [(0, 12), (62, 540), (800, NF + 1)])   # review 9: the skull rim loop crossed C1-C2 like wire in the disc beat (ray cast f630 at 960,130: Rim_Skull / Cortex) and at f30
# ---------------- rig
# End the displayed cord inside T1 in the undeformed anatomy. The world-height
# material fade alone leaves a long tail when the FK chain pitches forward.
import bmesh
cord = D.objects['SpinalCord']
cut_z = min(vertex.co.z for vertex in B[0].data.vertices)
bm = bmesh.new()
bm.from_mesh(cord.data)
cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                             plane_co=(0, 0, cut_z), plane_no=(0, 0, 1), clear_inner=True)
rim = [edge for edge in cut['geom_cut'] if isinstance(edge, bmesh.types.BMEdge) and edge.is_boundary]
bmesh.ops.holes_fill(bm, edges=rim)
bm.to_mesh(cord.data)
bm.free()
jp = [Vector((0, INFO[t]['yc'], INFO[t]['zm'])) for t in ('C7T1', 'C6C7', 'C5C6', 'C4C5', 'C3C4', 'C2C3')] + [Vector((0, 0.012, 1.5335)), Vector((0, 0.015, 1.5535))]
chain = FKChain(B, jp)
FKChain._parent(D.objects['Temporal.r'], D.objects['Skull'])
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
        o = D.objects[pre + tag]; _zz = [v.co.z for v in o.data.vertices]; _z0, _z1 = min(_zz), max(_zz); gt = o.vertex_groups.new(name='wt'); gb = o.vertex_groups.new(name='wb')
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
        _nt.links.new(_tc.outputs['Object'], _vd.inputs[0]); _sn = _nt.nodes.new('ShaderNodeMath'); _sn.operation = 'SINE'; _mu = _nt.nodes.new('ShaderNodeMath'); _mu.operation = 'MULTIPLY'; _mu.inputs[1].default_value = 13.0
        _dvs = [v.co for v in _o.data.vertices if v.co.x < 0.003]; _day = 0.0045; _daz = 0.0045;   # circular metric: rings are arcs centred on the cut-face centroid (review 11: straight bands)
        _dyc = (max(v.y for v in _dvs) + min(v.y for v in _dvs)) / 2 if _dvs else _i['yc']
        _sp0 = _nt.nodes.new('ShaderNodeSeparateXYZ'); _nt.links.new(_tc.outputs['Object'], _sp0.inputs[0]); _e1 = _nt.nodes.new('ShaderNodeMath'); _e1.operation = 'SUBTRACT'; _e1.inputs[1].default_value = _dyc; _nt.links.new(_sp0.outputs['Y'], _e1.inputs[0]); _e2 = _nt.nodes.new('ShaderNodeMath'); _e2.operation = 'SUBTRACT'; _e2.inputs[1].default_value = _i['zm']; _nt.links.new(_sp0.outputs['Z'], _e2.inputs[0])
        _e3 = _nt.nodes.new('ShaderNodeMath'); _e3.operation = 'DIVIDE'; _e3.inputs[1].default_value = _day; _nt.links.new(_e1.outputs[0], _e3.inputs[0]); _e4 = _nt.nodes.new('ShaderNodeMath'); _e4.operation = 'DIVIDE'; _e4.inputs[1].default_value = _daz; _nt.links.new(_e2.outputs[0], _e4.inputs[0])
        _e5 = _nt.nodes.new('ShaderNodeCombineXYZ'); _nt.links.new(_e3.outputs[0], _e5.inputs[0]); _nt.links.new(_e4.outputs[0], _e5.inputs[1]); _e6 = _nt.nodes.new('ShaderNodeVectorMath'); _e6.operation = 'LENGTH'; _nt.links.new(_e5.outputs[0], _e6.inputs[0]); _nt.links.new(_e6.outputs['Value'], _mu.inputs[0])   # concentric rings in the disc's own cut-face plane, centred on its centroid (review 10: diagonal stripes)
        _nt.links.new(_mu.outputs[0], _sn.inputs[0]); _no = _nt.nodes.new('ShaderNodeTexNoise'); _no.inputs['Scale'].default_value = 700; _nt.links.new(_tc.outputs['Object'], _no.inputs['Vector'])
        _ad = _nt.nodes.new('ShaderNodeMath'); _ad.operation = 'ADD'; _nt.links.new(_sn.outputs[0], _ad.inputs[0]); _nt.links.new(_no.outputs['Fac'], _ad.inputs[1])
        _cr = _nt.nodes.new('ShaderNodeValToRGB'); _cr.color_ramp.elements[0].position = 0.15; _cr.color_ramp.elements[1].position = 1.2; _cr.color_ramp.elements[0].color = (0.28, 0.34, 0.50, 1); _cr.color_ramp.elements[1].color = (0.92, 0.93, 0.97, 1)
        _nt.links.new(_ad.outputs[0], _cr.inputs['Fac']); _nvs = [v.co for v in D.objects['Nuc_' + _t].data.vertices if v.co.x < 0.003]; _ay = max(0.002, (max(v.y for v in _nvs) - min(v.y for v in _nvs)) / 2) if _nvs else 0.004; _az = max(0.0015, (max(v.z for v in _nvs) - min(v.z for v in _nvs)) / 2) if _nvs else 0.002; _ny = (min(v.y for v in _nvs) + max(v.y for v in _nvs)) / 2 if _nvs else _i['yc']
        _sp = _nt.nodes.new('ShaderNodeSeparateXYZ'); _nt.links.new(_tc.outputs['Object'], _sp.inputs[0]); _dy = _nt.nodes.new('ShaderNodeMath'); _dy.operation = 'SUBTRACT'; _dy.inputs[1].default_value = _ny; _nt.links.new(_sp.outputs['Y'], _dy.inputs[0])
        _dz = _nt.nodes.new('ShaderNodeMath'); _dz.operation = 'SUBTRACT'; _dz.inputs[1].default_value = _i['zm']; _nt.links.new(_sp.outputs['Z'], _dz.inputs[0])
        _qy = _nt.nodes.new('ShaderNodeMath'); _qy.operation = 'DIVIDE'; _qy.inputs[1].default_value = _ay; _nt.links.new(_dy.outputs[0], _qy.inputs[0]); _qz = _nt.nodes.new('ShaderNodeMath'); _qz.operation = 'DIVIDE'; _qz.inputs[1].default_value = _az; _nt.links.new(_dz.outputs[0], _qz.inputs[0])
        _cb = _nt.nodes.new('ShaderNodeCombineXYZ'); _nt.links.new(_qy.outputs[0], _cb.inputs[0]); _nt.links.new(_qz.outputs[0], _cb.inputs[1]); _ln = _nt.nodes.new('ShaderNodeVectorMath'); _ln.operation = 'LENGTH'; _nt.links.new(_cb.outputs[0], _ln.inputs[0])
        _nm = _nt.nodes.new('ShaderNodeMapRange'); _nm.interpolation_type = 'SMOOTHSTEP'; _nm.inputs['From Min'].default_value = 1.0; _nm.inputs['From Max'].default_value = 0.55; _nt.links.new(_ln.outputs['Value'], _nm.inputs['Value'])
        _nx = _nt.nodes.new('ShaderNodeMix'); _nx.data_type = 'RGBA'; _nx.inputs['B'].default_value = (0.66, 0.72, 0.84, 1); _nt.links.new(_nm.outputs['Result'], _nx.inputs['Factor']); _nt.links.new(_cr.outputs['Color'], _nx.inputs['A']); _nt.links.new(_nx.outputs['Result'], _p.inputs['Base Color']); _em = _nt.nodes.new('ShaderNodeMath'); _em.operation = 'MULTIPLY'; _em.inputs[1].default_value = 0.0; _nt.links.new(_nm.outputs['Result'], _em.inputs[0]); _nt.links.new(_em.outputs[0], _p.inputs['Emission Strength']); _p.inputs['Emission Color'].default_value = (0, 0, 0, 1)   # review 11: the glowing nucleus showed as a white pearl at each disc's rear edge; now a soft grey-blue, slightly lighter than the annulus, no glow   # the nucleus is a lighter, warmer ellipse inside the annulus ring (review 9), painted on the disc: the separate nucleus mesh stretched into brown strokes; _bp = _nt.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.7; _bp.inputs['Distance'].default_value = 0.00012
        _nt.links.new(_ad.outputs[0], _bp.inputs['Height']); _nt.links.new(_bp.outputs['Normal'], _p.inputs['Normal']); _p.inputs['Subsurface Weight'].default_value = 0.85; _p.inputs['Subsurface Radius'].default_value = (1.0, 0.8, 0.6); _p.inputs['Transmission Weight'].default_value = 0.55
        for _k, _m in enumerate(_o.data.materials):
            if _m and _m.name.startswith('Annulus'): _o.data.materials[_k] = _ma
for _t in INFO:
    _o = D.objects['Nuc_' + _t]
    for _k, _m in enumerate(_o.data.materials):
        if _m:
            _c = _m.copy(); _pp = [n for n in _c.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]; _pp.inputs['Base Color'].default_value = (0.88, 0.70, 0.46, 1); _pp.inputs['Subsurface Weight'].default_value = 0.6
            _pp.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.15); _pp.inputs['Roughness'].default_value = 0.04; _pp.inputs['Transmission Weight'].default_value = 0.7; _pp.inputs['IOR'].default_value = 1.35; _o.data.materials[_k] = _c
# review 9: brown strokes radiate from the nuclei across the neighbouring vertebral cut faces (f630 at 840-910,180-260; hide test: they vanish with Nuc_*). The nucleus cut face was a fan of long
# slivers; rebuild it as one clean filled polygon (boundary loop of the cut -> holes_fill -> beauty triangulation) before the hooks bend it.
import bmesh as _bmn
for _t in INFO:
    _o = D.objects['Nuc_' + _t]; _bn = _bmn.new(); _bn.from_mesh(_o.data); _cut = [f for f in _bn.faces if f.material_index == 1]
    if _cut:
        _bmn.ops.delete(_bn, geom=_cut, context='FACES_ONLY'); _be = [e for e in _bn.edges if e.is_boundary]
        if _be:
            _r = _bmn.ops.holes_fill(_bn, edges=_be, sides=max(4, len(_be))); [setattr(f, 'material_index', 1) for f in _r['faces']]
            _bmn.ops.triangulate(_bn, faces=_r['faces'], quad_method='BEAUTY', ngon_method='BEAUTY')
        _bn.to_mesh(_o.data)
    _bn.free()
for _t in INFO: D.objects['Nuc_' + _t].hide_render = True   # replaced by the painted nucleus on the disc (strokes across the cut faces came from this mesh)
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
P_PAY = add(sc_(P_REV, 0.9), S(50))   # payoff caricature (beat 6): the reversed curve plus 50 deg of lower-neck flexion, head far forward and down; checked by the penetration gate
P = Posture([(0, ST(add(P_C, [0, 0, 0, 0, 0, 0, 9, 12]), 0.014)), (7, ST(add(P_C, [0, 0, 0, 0, 0, 0, -3, -4]), -0.004)), (22, ST(P_REV, -0.025)),   # hook event (review 8): the head starts lifted, drops onto the spine by f7 as the arc lights (pulse sound 0.45 s), then slumps
             (44, ST(P_REV, -0.025)), (100, ST(P_C, 0)), (132, ST(add(P_C, S(15)), -0.004)), (156, ST(add(P_C, S(15)), -0.004)), (208, ST(add(P_C, S(30)), -0.009)), (238, ST(add(P_C, S(30)), -0.009)),
             (275, ST(add(P_C, S(60)), -0.020)), (300, ST(add(P_C, S(60)), -0.020)), (345, ST(P_C, 0)), (380, ST(P_C, 0)), (410, ST(P_STR, -0.010)), (440, ST(P_STR, -0.010)),
             (470, ST(P_REV, -0.025)), (510, ST(P_REV, -0.025)), (750, ST(sc_(P_REV, 1.06), -0.028)), (846, ST(sc_(P_REV, 1.06), -0.028)), (930, ST(P_PAY, -0.07)), (968, ST(P_PAY, -0.07)), (1000, ST(sc_(P_C, 0.3), SL_END)), (NF, ST(sc_(P_C, 0.3), SL_END))])
_at = P.at
def pose(f):
    v = _at(f); tr = 0.0
    # (review 9: a joint tremor shook camera-relative framing and aliased into judder; the tremor is now applied to the muscles only, below)
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
# ---------------- the person (MPFB2 + Mixamo mocap): visible at the start and in the payoff; the skeleton is solved to follow its head and upper back
H = Astra(sc, link).load(); H.retime()
_sb = world_bbox(D.objects['Skull']); SKULL_C = (_sb[0] + _sb[1]) / 2; _cb = world_bbox(D.objects['Vertebra C7']); C7C = (_cb[0] + _cb[1]) / 2
SKR = D.objects.new('SkelRoot', None); link(SKR); SKR.rotation_mode = 'QUATERNION'   # the skeleton's root follows C7 of the person (rigid part of anchors.json bp3d_vertebra_to_world)
for _o in [B[0], chain.joints[0], D.objects['Clavicle.l'], D.objects['Scapula.l'], D.objects['Clavicle.r'], D.objects['Scapula.r']] + [o for o in D.objects if o.name.startswith(('Vertebra T', 'Rim_Vertebra_T')) and o is not B[0] and o.parent is None]: _o.parent = SKR
_fa = [.07, .12, .15, .15, .14, .11, .08, .18]
_wd = lambda f: (1.0 if f < 1010 else max(0.0, 1.0 - ease((f - 1010) / 24.0))) if f >= 846 else 1.0 if f <= 84 else (1.0 - ease((f - 84) / 30.0) if f < 114 else (0.0 if f <= 820 else ease((f - 820) / 26.0)))   # human-driven skeleton: during the opening/dissolve and from the payoff on
_DER = H.derive([f for f in range(NF) if _wd(f) > 0], chain_mats, P_C, [r - c for r, c in zip(P_REV, P_C)], _fa, SKULL_C, C7C)
for _f in range(NF):
    _w = _wd(_f); _R = H.root_matrix(_f, C7C) if _w > 0 else None
    SKR.location = ((_R.translation + Vector((0, -0.02, 0))) * _w) if _R else Vector((0, 0, 0)); SKR.rotation_quaternion = Quaternion((1, 0, 0, 0)).slerp(_R.to_quaternion(), _w) if _R else Quaternion((1, 0, 0, 0))
    SKR.keyframe_insert('location', frame=_f); SKR.keyframe_insert('rotation_quaternion', frame=_f)
RN = Matrix.Identity(4)   # the ending returns to the skeleton's own alignment (w -> 0 by f1034)
_pose_P = pose
def pose(f):
    if f in _DER:
        w = _wd(f); dg, sl = _DER[f]
        if w >= 1.0: return list(dg), sl
        pg, ps = _pose_P(f); return [p + (d - p) * w for p, d in zip(pg, dg)], ps + (sl - ps) * w
    return _pose_P(f)
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
for _f, _v in ((0, 0.0), (84, 0.0), (112, 1.0)): cu.bevel_factor_end = _v; cu.keyframe_insert('bevel_factor_end', frame=_f)   # the arc draws on by f12 (hook event)
NP = 5 * 6 + 1; sp = cu.splines.new('POLY'); sp.points.add(NP - 1); LINE = link(D.objects.new('CurveLine', cu)); LINE['src'] = 'own'
for f in range(NF):
    degs, sl = pose(f); Ms = chain_mats(degs, sl); pp = catmull([Ms[bi] @ p for bi, p in reversed(ARC)], 6)
    for i, q in enumerate(pp[:NP]):
        sp.points[i].co = (q.x, q.y, q.z, 1.0); sp.points[i].keyframe_insert('co', frame=f)
LINE.parent = SKR
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'
json.dump({str(f): pose(f)[0] for f in range(NF)}, open(HERE + '/pose_dump.json', 'w'))   # per-frame joint angles for caption_truth / rigid_bend checks
for tag, sks in BULGE.items():
    for sk in sks:
        for f, v in ((0, 0), (520, 0), (620, 1), (855, 1), (930, 0)): sk.value = v; sk.keyframe_insert('value', frame=f)
# disc beat: the cord turns translucent so the root and the bulging disc can be seen behind it; root + contact pulse
for f, v in ((0, 0.0), (40, 0.0), (70, 1.0), (490, 1.0), (525, 0.18), (565, 0.0), (745, 0.0), (785, 1.0)): vkey(fadeC, f, v)   # review 7: the translucent cord veiled the lobe (pale pink patch); it is fully gone while lobe and root touch
vis(D.objects['SpinalCord'], [(76, 568), (742, 852), (1031, NF + 1)])
pulse(eRoot, [606, 650, 694], base=0.0, peak=5.0, width=10)   # contact flash only
for f, v in ((0, 0.0), (86, 0.0), (112, 1.0), (128, 1.0), (146, 0.0), (290, 0.0), (305, 1.0), (510, 1.0), (540, 0.0), (NF, 0.0)): vkey(fadeL, f, v)   # draft20: the arc lights as the person dissolves (it would be hidden behind the person before)   # arc only in beats 1 and 3; gone before the load arrow
# muscles: fade in, tension pulses on the posterior group, fade out
for f, v in ((0, 0.0), (752, 0.0), (764, 1.0), (814, 1.0), (829, 0.0)): vkey(fadeM, f, v)   # fades out before the ghost body fades in: no pale peach muscle over grey (f860-f876)
for o in MUS: vis(o, [(752, 830)])
for _o in MUS:   # muscle-only tremor (review 8/9): 0.7 mm, 12-frame period, enveloped, keyed on every frame so there is no frame-cadence pattern
    _o.scale = (1,1,1); _o.keyframe_insert('scale', frame=752)
    for f in range(784, 889):
        _e = max(0.0, min((f - 790) / 16.0, (884 - f) / 16.0, 1.0)); _a = 0.0007 * _e * math.sin(2 * math.pi * f / 12.0)
        _c = max(0.0, min(1.0, (f - 776) / 20.0)) * (1.0 - max(0.0, min(1.0, (f - 834) / 12.0))); _c = _c * _c * (3 - 2 * _c); _sz = 1.0 - 0.14 * _c; _sxy = 1.0 + 0.16 * _c   # draft20: visible contraction, the belly shortens 14 % and thickens 16 %, held 27.2-28.0 s, released by 29.7 s (pivot mid-neck)
        _o.scale = (_sxy, _sxy, _sz); _o.location = (0.0 + 0.0 * (1 - _sxy), _a * 0.6 + 0.03 * (1 - _sxy), _a + 1.45 * (1 - _sz)); _o.keyframe_insert('location', frame=f); _o.keyframe_insert('scale', frame=f)
for _o in MUS:   # review 10: one smooth contraction over 28 frames, peaking on the groan (27.0 s = f810)
    _k = _o.data.shape_keys.key_blocks['Contract']
    for f, v in ((796, 0.0), (812, 1.0), (824, 0.0)): _k.value = v; _k.keyframe_insert('value', frame=f)
for f, v in ((0, 0.0), (790, 0.0), (796, 0.05), (812, 0.10), (826, 0.10), (846, 0.10), (862, 0.0)): vkey(eMus, f, v)   # one slow swell: tightening, stays red
for f, v in ((0, 3.0), (9, 3.0), (12, 10.0), (19, 3.0), (23, 3.0), (28, 9.0), (35, 3.0)): vkey(eLine, f, v)   # second arc pulse bridges the held pose f22-f35 (review 9)   # review 7 item 4: the arc finishes drawing at f12 with a flash, in time with the pulse sound (0.45 s)
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
_ac = ACRO_P; anchor('A_Acro', SKR, _ac)   # shoulder tip = acromial end of the clavicle (the clavicle ends exactly here)
anchor('A_Contact', D.objects['Vertebra C6'], anchor_pt)
anchor('A_C56', D.objects['Vertebra C5'], Vector((0.0055, INFO['C5C6']['yc'] + INFO['C5C6']['rb'][12], INFO['C5C6']['zm'])))
_g = [v.co for v in D.objects['SpinalGanglia'].data.vertices if abs(v.co.z - INFO['C5C6']['zm'] + 0.0012) < 0.0025]
anchor('A_Root', D.objects['Vertebra C6'], sum(_g, Vector()) / len(_g))
# ---------------- camera: skull base -> T2 fills the band height
cam = CameraPath(lens=70, fstop=11)
for _f, _v in ((0, 35), (60, 35), (84, 65), (124, 70), (836, 70), (850, 35), (990, 35), (1030, 70)): cam.cam.data.lens = _v; cam.cam.data.keyframe_insert('lens', frame=_f)   # establishing shot: wide full body, zoom into the neck over ~1.5 s
for _f, _v in ((0, 8), (500, 8), (540, 22), (790, 22), (830, 8)): cam.cam.data.dof.aperture_fstop = _v   # shallow DOF on the subject in the wide beats, deeper in the disc close-up; cam.cam.data.dof.keyframe_insert('aperture_fstop', frame=_f)
ENDAZ = -32; ENDEL = -0.12   # ending view: turned 32 deg behind the patient so the shoulder tip (14 cm lateral) separates from the spine on screen
def dirn(az, el=0.03): return Vector((-math.cos(math.radians(az)), math.sin(math.radians(az)), el))
DC0 = Vector((0.004, INFO['C5C6']['yc'], INFO['C5C6']['zm'])); DCa = chain_mats(*pose(570))[2] @ DC0; DCb = chain_mats(*pose(750))[2] @ DC0
for f, tg, d, dist in ((0, Vector((0, -0.02, 1.34)), dirn(-18, 0.0), 0.95), (60, Vector((0, -0.03, 1.46)), dirn(-14, 0.0), 0.88), (84, Vector((0, -0.03, 1.56)), dirn(-8, 0.0), 0.80), (124, Vector((0, 0.008, 1.50)), dirn(2), 0.76), (210, Vector((-0.004, 0.0, 1.49)), dirn(4), 0.84),
                       (300, Vector((-0.012, -0.002, 1.49)), dirn(-3), 0.92), (360, Vector((-0.006, 0.005, 1.495)), dirn(4), 0.70), (440, Vector((-0.01, 0.004, 1.49)), dirn(-2), 0.72), (510, Vector((-0.014, 0.004, 1.49)), dirn(3), 0.74),
                       (570, DCa + Vector((0.0, 0.004, 0.0)), Vector((-1, 0.22, 0.10)), 0.20), (660, DCa + Vector((0.003, 0.007, -0.002)), Vector((-1, 0.27, 0.11)), 0.175), (750, DCb + Vector((0.004, 0.006, 0.0)), Vector((-1, 0.30, 0.12)), 0.15),
                       (800, Vector((0, 0.01, 1.49)), dirn(0), 0.66), (836, Vector((0.006, 0.01, 1.485)), dirn(-3), 0.62), (850, Vector((0, -0.03, 1.36)), dirn(-12, 0.02), 1.40), (868, Vector((0, -0.04, 1.38)), dirn(-10, 0.02), 1.30), (900, Vector((0, -0.05, 1.40)), dirn(-4, 0.02), 1.12), (935, Vector((0, -0.06, 1.41)), dirn(-14, 0.02), 1.02), (970, Vector((0, -0.04, 1.38)), dirn(-10, 0.02), 1.12), (990, Vector((0, -0.045, 1.38)), dirn(-12, 0.02), 1.06), (1030, (RN @ Vector((0.0, 0.02, 1.51))), dirn(-ENDAZ, ENDEL), 0.86), (1056, (RN @ Vector((0.0, 0.02, 1.51))), dirn(-ENDAZ, ENDEL), 0.78), (NF - 1, (RN @ Vector((0.0, 0.02, 1.51))), dirn(-ENDAZ, ENDEL), 0.68)):
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
env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = D.images.load(asset('assets/studio_small_09_2k.exr')); w.node_tree.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.14
render_settings(*EP['render']['res'], spp=EP['render']['spp'], blur=0)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.6
sc.render.use_persistent_data = True; sc.cycles.sample_clamp_direct = 8; sc.cycles.sample_clamp_indirect = 3
# Film the neutral ear and the actual acromion in profile. Moving the shoulder
# girdle to align two screen coordinates changes the anatomy being demonstrated.
sc.frame_set(NF - 1)
ear = D.objects['A_Ear'].matrix_world.translation
acromion = D.objects['A_Acro'].matrix_world.translation
profile = acromion - ear
profile.z = 0
profile.normalize()
profile.z = -.04
focus = (ear + acromion) * .5
for frame, distance in [(1030, .86), (1056, .81), (NF-1, .76)]:
    cam.key(frame, focus, profile, distance)
H.fades(vkey, ((0, 1.0), (60, 1.0), (84, 0.0), (838, 0.0), (852, 1.0), (1010, 1.0), (1034, 0.0), (NF, 0.0)))   # opening: 60 frames opaque, 24-frame dissolve to the skeleton; payoff fades in over 24 frames, straightens, dissolves for the ending
H.vis(vis, [(0, 84), (839, 1034)])
for part in H.objs:
    if part.name.startswith(('Hair', 'Eyes', 'Spectacles')):
        vis(part, [(0, 82), (840, 1030)])
for _o in [o for o in D.objects if o.type in ('MESH', 'CURVE') and (o.name.startswith(('Vertebra T', 'Rim_Vertebra_T')))]: vis(_o, [(76, 852), (1020, NF + 1)])   # the thoracic bones below C7 would stick out of the person's back while he is visible

sc['spp_boost'] = json.dumps([
    [58, 88, 16], [750, 758, 32], [818, 833, 48], [834, 847, 64], [848, 862, 16],
    [1008, 1038, 16], [1026, 1034, 40],
])
# review 14 P0: nothing of the skeleton shows while the person is opaque (skull ahead of the face at f0-f18, through the jaw at f993+, a shrinking skeleton at f824-f846): per-frame visibility
_HN = {o.name for o in H.objs}; _SK = [o for o in D.objects if o.type in ('MESH', 'CURVE') and o.name not in _HN and o.name != 'Skin']
_HEAD = {'Skull', 'Mandible', 'Brain', 'TeethLower', 'TeethUpper', 'Rim_Skull', 'Rim_Mandible', 'Atlas (C1)', 'Rim_Atlas_(C1)'}
from bpy_extras.anim_utils import action_get_channelbag_for_slot

for obj in _SK:
    anim = obj.animation_data
    bag = action_get_channelbag_for_slot(anim.action, anim.action_slot) if anim and anim.action else None
    curve = bag.fcurves.find('hide_render') if bag else None
    # Sample the original boolean visibility before changing the curve. Updating
    # the whole skinned scene 1080 times just to read this channel dominated builds.
    original = [bool(curve.evaluate(f)) for f in range(NF)] if curve else [obj.hide_render] * NF
    hidden = [old or 852 <= f < 1010 or (obj.name in _HEAD and (f < 72 or 852 <= f < 1022))
              for f, old in enumerate(original)]
    if curve:
        curve.keyframe_points.clear()
    for f, value in enumerate(hidden):
        if f == 0 or value != hidden[f - 1]:
            obj.hide_render = value
            obj.keyframe_insert('hide_render', frame=f)
# Keep the bony subject through the entire incoming dissolve. Changing
# hide_render at its first frame removed the thoracic spine in a single frame.
human_materials = {slot.material for obj in H.objs for slot in obj.material_slots}
bone_materials = {slot.material for obj in _SK for slot in obj.material_slots}
for material in bone_materials - human_materials:
    if not material or not material.node_tree:
        continue
    opacity = material.node_tree.nodes.new('ShaderNodeValue')
    for frame, amount in [(0, 1), (838, 1), (845, .65), (852, 0), (1010, 0), (1034, 1), (NF, 1)]:
        vkey(opacity, frame, amount)
    mask_material(material, opacity.outputs[0])
# The sectioned skull extends outside the fitted face during early fades.
# A separate material ramp starts after half opacity on each outgoing person shot.
head_materials = {}
for obj in (obj for obj in _SK if obj.name in _HEAD):
    for slot in obj.material_slots:
        source = slot.material
        if not source or not source.node_tree:
            continue
        if source not in head_materials:
            mat = source.copy()
            opacity = mat.node_tree.nodes.new('ShaderNodeValue')
            for frame, amount in [(0,0), (72,0), (84,1), (852,1), (853,0), (1022,0), (1034,1), (NF,1)]:
                vkey(opacity, frame, amount)
            mask_material(mat, opacity.outputs[0])
            head_materials[source] = mat
        slot.material = head_materials[source]
# the shoulder dot follows the person's own shoulder (anchors.json shoulder_world) while he is visible, then returns to the skeleton's acromion (review 15)
_AC = D.objects['A_Acro']; _ac0 = _AC.location.copy()
for _f in range(NF):
    _w = _wd(_f)
    if _w > 0:
        _Rr = H.root_matrix(_f, C7C); _tg = _Rr.inverted() @ (Vector(H.rec(_f)['shoulder_world']) * 1.05 + Vector((0, 0, 0)))
        _AC.location = _ac0.lerp(_tg, _w) if _w < 1.0 else _tg
    else: _AC.location = _ac0
    _AC.keyframe_insert('location', frame=_f)
# The FK chain translates forward while it takes up the character pose. A
# camera looking at the rest-space neck loses the C-spine during the pull-back.
# Track the evaluated C4 centre until the person becomes the shot's subject.
for frame in (814, 820, 826, 830, 834, 836, 838, 840, 842, 846, 850, 852):
    sc.frame_set(frame)
    vertebra = D.objects['Vertebra C4']
    centre = vertebra.matrix_world @ (sum((Vector(p) for p in vertebra.bound_box), Vector())/8)
    weight = max(0.0, min(1.0, (frame-839)/13.0))
    weight = weight*weight*(3-2*weight)
    focus = centre.lerp(Vector((0,-.04,1.38)),weight)
    cam.key(frame,focus,dirn(-8-2*weight,.02),.78+.52*weight)

# During the human payoff the near-side skin and shirt are the visible landmarks.
# Return to the original bony positions as the character dissolves into the skeleton.
rest_points = (('A_Ear', 'Skin.001', (.067, -.052, 1.555)), ('A_Acro', 'Outfit', (.179, -.010, 1.381)))
surfaces = []
subdivisions = []
for anchor_name, surface_name, rest in rest_points:
    surface = D.objects[surface_name]
    for modifier in surface.modifiers:
        if modifier.type == 'SUBSURF':
            subdivisions.append((modifier, modifier.show_viewport))
            modifier.show_viewport = False
    indices = [min(surface.data.vertices, key=lambda v: (v.co-Vector((side*rest[0], *rest[1:]))).length_squared).index
               for side in (-1, 1)]
    surfaces.append((D.objects[anchor_name], surface, indices))
# Crossfade the two measured targets with the actual skin opacity. Once the
# person is nearly absent the bony landmark owns the entire marker.
skin_mat = next(m for m in D.objects['Skin.001'].data.materials if m and m.node_tree.nodes.get('Fade'))
skin_fade = skin_mat.node_tree.nodes['Fade'].outputs[0]
bone_cutoff = json.loads((Path(os.environ['ANAT_KIT'])/'gates/thresholds.json').read_text())['shot_checks']['bone_landmark_max_skin_alpha']
bone_points = (EAR_P, ACRO_P)
for frame in range(929, 1035):
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    weight = max(0, min(1, frame-929, (skin_fade.default_value-bone_cutoff)/(1-bone_cutoff)))
    for i, (anchor, surface, indices) in enumerate(surfaces):
        evaluated = surface.evaluated_get(dg)
        points = [evaluated.matrix_world @ evaluated.data.vertices[index].co for index in indices]
        near = min(points, key=lambda p: (p-sc.camera.matrix_world.translation).length_squared)
        local = (anchor.parent.matrix_world @ anchor.matrix_parent_inverse).inverted() @ near
        anchor.location = bone_points[i].lerp(local,weight)
        anchor.keyframe_insert('location', frame=frame)
for modifier, enabled in subdivisions:
    modifier.show_viewport = enabled
# Export the applied animation from the Blender action rather than maintaining a
# second hand-authored set of values for the editorial checks.
def animated_values(owner, path, index=0):
    anim = owner.animation_data
    bag = action_get_channelbag_for_slot(anim.action, anim.action_slot)
    curve = bag.fcurves.find(path, index=index)
    if curve is None:
        raise ValueError(f'missing animation for {owner.name} {path}[{index}]')
    return [curve.evaluate(f) for f in range(NF)]

def socket_values(node):
    return animated_values(node.id_data, node.outputs[0].path_from_id('default_value'))

skin_object = D.objects['Skin.001']
left = animated_values(D.objects['Scapula.l'], 'hide_render')
right = animated_values(D.objects['Scapula.r'], 'hide_render')
muscle_hide = animated_values(MUS[0], 'hide_render')
signals = {
    'EarShoulderGapCm': [100 * 1.05 * H.rec(f)['ear_ahead_of_shoulder_m'] for f in range(NF)],
    'SkinRender': [1 - round(hidden) for hidden in animated_values(skin_object, 'hide_render')],
    'HumanFade': socket_values(skin_mat.node_tree.nodes['Fade']),
    'VertebraTint': socket_values(vTC),
    'Herniation': animated_values(HER, 'scale', 1),
    'CurveLine': socket_values(fadeL),
    'Shoulder': [amount * (not (round(a) and round(b))) for amount, a, b in zip(socket_values(fadeSh), left, right)],
    'MuscleGlow': [amount * (not round(hide)) for amount, hide in zip(socket_values(eMus), muscle_hide)],
    'MuscleOpacity': [amount * (not round(hide)) for amount, hide in zip(socket_values(fadeM), muscle_hide)],
    'MuscleShorteningPct': [100 * (1 - scale) for scale in animated_values(MUS[0], 'scale', 2)],
}
scene_dump = {name: {str(f): round(value, 6) for f, value in enumerate(values)} for name, values in signals.items()}
(Path(HERE) / 'scene_dump.json').write_text(json.dumps(scene_dump))
provenance = {obj.name: obj["src"].split(" | ") for obj in sc.objects if str(obj.get("src", "")).startswith("bp3d:")}
(Path(HERE) / "bp3d_provenance.json").write_text(json.dumps(provenance, indent=1))
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=HERE + '/neck.blend'); print('SAVED')
