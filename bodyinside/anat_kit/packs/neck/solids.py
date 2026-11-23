import os
# Stage B (slow, run once): remesh every bone into ONE closed solid, cut it once at the sagittal plane, build discs from the real endplates.
# usage: Blender -b base.blend -P solids.py   -> neck_solids.blend
import sys
sys.path.insert(0, os.path.join(os.environ['ANAT_KIT'],'blender'))
import bpy, bmesh, math, json, time, builtins
_t0 = time.time()
_p = builtins.print
def print(*a, **k): _p('[%4.0fs]' % (time.time() - _t0), *a, flush=True, **k)
from mathutils.bvhtree import BVHTree
import random
from kit import *; from kit_spine import *
from mathutils import Matrix, Vector
X_CUT = 0.001                    # sagittal cut plane (everything on x < X_CUT is removed; the camera looks from -x)
mT = trabecular_material(); mC = cortex_material(); mAnn, mNuc = disc_materials()
mBone = bone_material('BoneBase')[0]
import copy
mAnnCut = mAnn.copy(); mAnnCut.name = 'AnnulusCut'; mNucCut = mNuc.copy(); mNucCut.name = 'NucleusCut'
def slot0(o, m): o.data.materials.clear(); o.data.materials.append(m)
VERT = ['Vertebra T4', 'Vertebra T3', 'Vertebra T2', 'Vertebra T1', 'Vertebra C7', 'Vertebra C6', 'Vertebra C5', 'Vertebra C4', 'Vertebra C3', 'Axis (C2)', 'Atlas (C1)']
print('start')
for n in VERT: smooth_solid(D.objects[n], 0.0004, subsurf=1, smooth_iter=6); slot0(D.objects[n], mBone)
print('vertebrae remeshed')
bvh = {n: BVHTree.FromObject(D.objects[n], bpy.context.evaluated_depsgraph_get()) for n in VERT}   # uncut solids: discs are fitted to these
# skull = union of every cranial bone, remeshed into one solid
SKB = [o for o in D.objects if o.name.startswith('Skull')]
print('skull parts', [o.name for o in SKB])
bpy.ops.object.select_all(action='DESELECT')
for o in SKB: o.select_set(True)
_src = ' | '.join(o.get('src', '') for o in SKB); bpy.context.view_layer.objects.active = SKB[0]; bpy.ops.object.join(); SK = bpy.context.active_object; SK.name = 'Skull'; SK['src'] = _src
smooth_solid(SK, 0.001, subsurf=0, smooth_iter=4); slot0(SK, mBone); print('skull verts', len(SK.data.vertices))
print('skull done')
MD = D.objects['Mandible']
# close the jaw: rotate mandible + lower teeth about the condylar axis (BodyParts3D poses the jaw open); -10 deg raises the chin
_zm = max(v.co.z for v in MD.data.vertices); _cv = [v.co for v in MD.data.vertices if v.co.z > _zm - 0.006 and v.co.x > 0.02]
_pv = Vector((0, sum(c.y for c in _cv) / len(_cv), sum(c.z for c in _cv) / len(_cv))); JAW_PIVOT = _pv
for _o in (MD, D.objects['TeethLower']):
    _m = Matrix.Translation(_pv) @ Matrix.Rotation(math.radians(-10), 4, 'X') @ Matrix.Translation(-_pv); _o.data.transform(_m)
smooth_solid(MD, 0.0006, subsurf=1, smooth_iter=4); slot0(MD, mBone)
for _n in ('TeethUpper', 'TeethLower'): smooth_solid(D.objects[_n], 0.0003, subsurf=1, smooth_iter=3)
BR = D.objects['Brain']; smooth_solid(BR, 0.0009, subsurf=0, smooth_iter=6); mBrain = newmat('BrainCut')[0]; _pn = [n for n in mBrain.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
_pn.inputs['Base Color'].default_value = (0.62, 0.50, 0.50, 1); _pn.inputs['Roughness'].default_value = 0.5; mBrain.node_tree.links.new(_pn.outputs[0], [n for n in mBrain.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'][0].inputs['Surface']); slot0(BR, mBrain)
for _n in ('Clavicle.l', 'Scapula.l'): smooth_solid(D.objects[_n], 0.0007, subsurf=1, smooth_iter=4); slot0(D.objects[_n], mBone)
print('mandible done')
# ---- discs (before the vertebrae are cut)
PAIRS = [('Axis (C2)', 'Vertebra C3', 'C2C3'), ('Vertebra C3', 'Vertebra C4', 'C3C4'), ('Vertebra C4', 'Vertebra C5', 'C4C5'), ('Vertebra C5', 'Vertebra C6', 'C5C6'), ('Vertebra C6', 'Vertebra C7', 'C6C7'), ('Vertebra C7', 'Vertebra T1', 'C7T1')]
INFO = {}
for up, lo, tag in PAIRS:
    L = D.objects[lo]; _v = [v.co for v in L.data.vertices if abs(v.co.x) < 0.012 and v.co.y < 0.02]; _zt = max(c.z for c in _v)
    ymin = min(c.y for c in _v if c.z > _zt - 0.004)
    probe = ymin + 0.005
    ann, info = disc_between('Disc_' + tag, bvh[up], bvh[lo], probe, mAnn)
    nuc = nucleus_from(info, ann, 'Nuc_' + tag, mNuc)
    for _o in (ann, nuc):
        _b = bmesh.new(); _b.from_mesh(_o.data); print('CHK', _o.name, 'verts', len(_b.verts), 'nonmanifold', sum(1 for e in _b.edges if not e.is_manifold), 'vol_mm3', round(_b.calc_volume(signed=True) * 1e9, 1)); _b.free()
    INFO[tag] = info; print('DISC', tag, 'gap_mm', info['gap_mm'], 'yc', round(info['yc'], 4), 'r mm', round(min(info['rb']) * 1000, 1), round(max(info['rb']) * 1000, 1))
print('discs done')
# ---- one smooth cut each
for n in VERT + ['Skull', 'Mandible']:
    o = D.objects[n]; cut_half(o, X_CUT, True, mT); flatten_cut(o, 'Trabecular', X_CUT); print('cut', n)
for tag in INFO:   # discs are simple closed meshes: bisect + fill (robust); the gel section sits 0.05 mm in front of the annulus section (no coplanar z-fight)
    for pre, cutmat, dx in (('Disc_', mAnnCut, 0.0), ('Nuc_', mNucCut, 0.00005)):
        src = D.objects[pre + tag]; src.data.materials.append(cutmat)
        new = split_by_plane(src, pre + tag + '_cut', (X_CUT - dx, 0, 0), (1, 0, 0), cap_mat_index=1)
        D.objects.remove(src); new.name = pre + tag
        for pg in new.data.polygons: pg.use_smooth = (pg.material_index == 0)
cut_half(D.objects['Brain'], X_CUT, True, mBrain); print('cut Brain')
for _n in ('Clavicle.l', 'Scapula.l'): pass
# ---- cortical rim tubes on the cut faces
for n in VERT + ['Skull', 'Mandible']:
    o = D.objects[n]; cortical_rim(o, 'Trabecular', mC, 0.00017 if n not in ('Skull', 'Mandible') else 0.0003, 'Rim_' + n.replace(' ', '_'))
cord, roots_, gang_ = cord_and_roots(INFO, ['C2C3', 'C3C4', 'C4C5', 'C5C6', 'C6C7', 'C7T1'])
for o in D.objects:
    if o.name.startswith(('Disc_', 'Nuc_')): o['src'] = 'own'
    if o.name.startswith('Rim_'):
        par = [x for x in D.objects if x.name.replace(' ', '_') == o.name[4:]]; o['src'] = (par[0].get('src', 'own') if par else 'own') + ' (derived)'
# ---- CC0 human skin shell (Blender Studio Human Base Meshes bundle v1.4.1): fitted over the BodyParts3D skull, cut at the same plane, rigged in build.py
HBP = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../../research/anatomy3d/human_base_meshes/x/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend')
with bpy.data.libraries.load(HBP) as (_s, _d): _d.objects = ['GEO-body_male_realistic']
_ho = _d.objects[0]; link(_ho)
for _m in _ho.modifiers:
    if _m.type == 'MULTIRES': _m.levels = 2; _m.render_levels = 2; _m.sculpt_levels = 2
_dg = bpy.context.evaluated_depsgraph_get(); _e = _ho.evaluated_get(_dg); _me = D.meshes.new_from_object(_e); _me.transform(_ho.matrix_world)
D.objects.remove(_ho); SKIN = link(D.objects.new('Skin', _me)); import hashlib
SKIN['src'] = 'cc0:human_base_meshes_bundle_v1.4.1:' + hashlib.sha256(open(HBP, 'rb').read()).hexdigest()
_xs = [v.co.x for v in _me.vertices]; _me.transform(Matrix.Translation((-(max(_xs) + min(_xs)) / 2, 0, 0)))
_zt = max(v.co.z for v in _me.vertices); _skz = max(v.co.z for v in D.objects['Skull'].data.vertices); _sky = max(v.co.y for v in D.objects['Skull'].data.vertices)
_back = max(v.co.y for v in _me.vertices if v.co.z > _zt - 0.2); _me.transform(Matrix.Translation((0, _sky + 0.007 - _back, _skz + 0.012 - _zt)))
_tr = BVHTree.FromObject(SKIN, bpy.context.evaluated_depsgraph_get()); import random; random.seed(3)
_sv = [v.co.copy() for v in random.sample(list(D.objects['Skull'].data.vertices), 600)]; _c = Vector((0, 0.01, 1.62))
def _inside(p):
    h = _tr.find_nearest(p); return h[0] is not None and (p - h[0]).dot(h[1]) < 0
for _k in range(4):   # at most ~5 % scale-up: a bigger skin would stop being the same head
    _fr = sum(1 for p in _sv if _inside(p)) / len(_sv); print('skin containment', round(_fr, 3))
    if _fr > 0.995: break
    _me.transform(Matrix.Translation(_c) @ Matrix.Scale(1.012, 4) @ Matrix.Translation(-_c)); _tr = BVHTree.FromObject(SKIN, bpy.context.evaluated_depsgraph_get())
_bm = bmesh.new(); _bm.from_mesh(_me)
for _co, _no in (((X_CUT, 0, 0), (1, 0, 0)),):   # full body kept (establishing shot): only the sagittal cut
    bmesh.ops.bisect_plane(_bm, geom=list(_bm.verts) + list(_bm.edges) + list(_bm.faces), plane_co=_co, plane_no=_no, clear_inner=True)
_bm.to_mesh(_me); _bm.free()
for _pg in _me.polygons: _pg.use_smooth = True
KEEP = ('Vertebra', 'Axis', 'Atlas', 'Skull', 'Mandible', 'Rim_', 'Disc_', 'Nuc_', 'Skin', 'Teeth', 'Brain', 'Clavicle', 'Scapula', 'SpinalCord', 'SpinalRoots', 'SpinalGanglia', 'Splenius', 'Semispinalis', 'Levator', 'Descending part', 'Longus colli', 'Sternocleido')
for o in list(D.objects):
    if not o.name.startswith(KEEP): print('drop stray', o.name); D.objects.remove(o)   # leftovers of the skull join (face plates) would render as grey scraps
json.dump(dict(INFO, _jaw=list(JAW_PIVOT)) if False else INFO, open(bpy.path.abspath('//disc_info.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath('//neck_solids.blend')); print('SOLIDS SAVED')
