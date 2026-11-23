"""Generate the Body Inside adult male with MPFB2 (CC0 output) + Mixamo rig; save assets/mpfb/human_mpfb.blend.
usage: Blender -b -P mpfb_make.py"""
import bpy, sys, os, json, addon_utils
MOD = 'bl_ext.user_default.mpfb'
if MOD not in bpy.context.preferences.addons: bpy.context.preferences.addons.new().module = MOD   # register() reads its own preferences entry, which a -b run does not have
try: addon_utils.enable(MOD, default_set=False, persistent=False)
except Exception as e: print('enable failed', e)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'mpfb', 'human_mpfb.blend')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
d = TargetService.get_default_macro_info_dict(); d.update(gender=1.0, age=0.62, muscle=0.45, weight=0.45, proportions=0.5, height=0.55); d['race'] = {'asian': 0.8, 'caucasian': 0.1, 'african': 0.1}
body = HumanService.create_human(mask_helpers=False, detailed_helpers=False, extra_vertex_groups=False, feet_on_ground=True, scale=0.1, macro_detail_dict=d)
rig = HumanService.add_builtin_rig(body, 'game_engine', import_weights=True)
body.name = 'HumanBody'; rig.name = 'HumanRig'
# drop helper geometry (everything that is not the body)
import bmesh
if 'body' in body.vertex_groups:
    bpy.context.view_layer.objects.active = body; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for n in ('lowerarm_r','hand_r','head','neck_01','spine_03','upperarm_r','clavicle_r'):
    b_ = rig.data.bones[n]; print('PB', n, [round(x, 3) for x in b_.head_local], [round(x, 3) for x in b_.tail_local])
top = max(v.co.z for v in body.data.vertices if v.co.z < 1.9); dz = top - rig.data.bones['head'].tail_local.z; rig.location.z = dz; bpy.context.view_layer.update(); body.matrix_parent_inverse = rig.matrix_world.inverted()   # the game_engine rig comes out ~0.89 m low: fit the rig to the mesh by crown height
print('DZ', dz)
HAIR = os.path.expanduser('~/Library/Application Support/Blender/5.2/mpfb/data/hair/short02/short02.mhclo')
hair = HumanService.add_mhclo_asset(HAIR, body, asset_type='Hair', subdiv_levels=0, material_type='MAKESKIN')
print('HAIR', hair.name if hair else None, hair.parent.name if hair and hair.parent else None, [m.type for m in hair.modifiers] if hair else None, len(hair.vertex_groups) if hair else None)
if hair: hair.name = 'HumanHair'
print('BONES', [b.name for b in rig.data.bones][:80]); print('DIMS', tuple(body.dimensions), len(body.data.vertices), [m.name for m in body.modifiers])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
