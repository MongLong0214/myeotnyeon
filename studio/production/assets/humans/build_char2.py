"""Build a clothed, faceless, rigged CC0 human for EP001 with MPFB2 (Blender 5.2).

Usage: Blender --background --factory-startup --python-exit-code 1 --python build_char2.py -- <male|female> <clothes> <shoes> <out.blend> <body_rgb> <cloth_rgb>
Body/clothes are one neutral plaster family; fabric keeps its normal map only, so prints/logos vanish.
The face is smoothed into a mannequin surface (no eyes/nose/mouth relief) so no figure resembles a person.
"""
import bpy, sys, os, bmesh, math
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
gender, cloth_id, shoe_id, out_path = a[0], a[1], a[2], a[3]
body_rgb = tuple(float(x) for x in a[4].split(','))
cloth_rgb = tuple(float(x) for x in a[5].split(','))

bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService

scn = bpy.context.scene
scn.MPFB_NH_add_phenotype = True
scn.MPFB_NH_phenotype_gender = gender
scn.MPFB_NH_phenotype_influence = 1.0
scn.MPFB_NH_phenotype_age = 'young'
scn.MPFB_NH_phenotype_muscle = 'averagemuscle'
scn.MPFB_NH_phenotype_weight = 'averageweight'
scn.MPFB_NH_phenotype_height = 'average'
scn.MPFB_NH_phenotype_proportions = 'average'
scn.MPFB_NH_phenotype_race = 'universal'
scn.MPFB_NH_add_breast = False
scn.MPFB_NH_override_skin_model = 'NONE'
scn.MPFB_NH_override_eyes_model = 'NONE'
scn.MPFB_NH_scale_factor = 'METER'
scn.MPFB_NH_mask_helpers = True
scn.MPFB_NH_detailed_helpers = True       # required for correct bone placement (see REPORT.md §2)
scn.MPFB_NH_extra_vertex_groups = True
print('create', bpy.ops.mpfb.create_human())
body = bpy.context.view_layer.objects.active
body.name = f'human_{gender}'
scn.MPFB_ADR_standard_rig = 'cmu_mb'
scn.MPFB_ADR_import_weights = True
print('rig', bpy.ops.mpfb.add_standard_rig())
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.name = f'human_{gender}_rig'

D = os.path.expanduser('~/Library/Application Support/Blender/5.2/mpfb/data/clothes')
added = []
for cid in (cloth_id, shoe_id):
    f = os.path.join(D, cid, cid + '.mhclo')
    c = HumanService.add_mhclo_asset(f, body, asset_type='Clothes', subdiv_levels=0, material_type='MAKESKIN',
                                     set_up_rigging=True, interpolate_weights=True, import_subrig=False, import_weights=True)
    added.append(c)
    print('clothes', cid, c.name if c else None)

# ---- materials: plaster body; fabric = plaster colour + original normal map only
def plaster(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Subsurface Weight'].default_value = 0.05
    return m

body.data.materials.clear(); body.data.materials.append(plaster('plaster_body', body_rgb, 0.55))
for c in added:
    if c is None:
        continue
    normal_img = None
    for m in c.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeTexImage' and n.image and 'normal' in n.image.name.lower():
                    normal_img = n.image
    m = plaster(f'plaster_{c.name}', cloth_rgb, 0.8)
    if normal_img:
        nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = normal_img; normal_img.colorspace_settings.name = 'Non-Color'
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
        uv = nt.nodes.new('ShaderNodeUVMap')
        nt.links.new(uv.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
    c.data.materials.clear(); c.data.materials.append(m)

# ---- faceless: hide the sculpted head, attach a smooth mannequin head to the Head bone
bpy.context.view_layer.update()
mw = body.matrix_world
hb = rig.pose.bones['Head']
hj = rig.matrix_world @ hb.head; ht = rig.matrix_world @ hb.tail
hm = next((m for m in body.modifiers if m.type == 'MASK' and m.name == 'Hide helpers'), None)
gname = hm.vertex_group if hm else None
gi = body.vertex_groups[gname].index if gname and gname in body.vertex_groups else None
inv = hm.invert_vertex_group if hm else False
def visible(v):
    if gi is None:
        return True
    ing = any(g.group == gi and g.weight > 0.5 for g in v.groups)
    return ing != inv
for m in body.modifiers:
    m.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
ev_me = body.evaluated_get(dg).to_mesh()
assert len(ev_me.vertices) == len(body.data.vertices)
P = {v.index: v.co.copy() for v in ev_me.vertices}
body.evaluated_get(dg).to_mesh_clear()
for m in body.modifiers:
    m.show_viewport = True
class _V:  # evaluated-position proxy keeping index + groups
    def __init__(self, v): self.index = v.index; self.groups = v.groups; self.co = P[v.index]
real = [_V(v) for v in body.data.vertices if visible(v)]
print('mask group', gname, 'invert', inv, 'visible verts', len(real))
zs_all = [(mw @ v.co).z for v in real]
height = max(zs_all)
neck_cut = height * 0.865
up = [mw @ v.co for v in real if (mw @ v.co).z > height * 0.93]
hc = Vector((sum(p.x for p in up) / len(up), sum(p.y for p in up) / len(up), 0))
vg = body.vertex_groups.new(name='head_cut')
cut = [v.index for v in real if (mw @ v.co).z > neck_cut and ((mw @ v.co).xy - hc.xy).length < 0.17]
vg.add(cut, 1.0, 'REPLACE')
mk = body.modifiers.new('head_cut', 'MASK'); mk.vertex_group = 'head_cut'; mk.invert_vertex_group = True
bottom = neck_cut - 0.035
H = height + 0.004 - bottom
me = bpy.data.meshes.new('mannequin_head'); bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=0.5)
for v in bm.verts:
    z = v.co.z
    taper = 1.0 - 0.18 * max(0.0, -z) * 2          # narrower toward the chin
    v.co.x *= taper; v.co.y *= taper * (1.0 + 0.06 * z)
bm.to_mesh(me); bm.free()
head = bpy.data.objects.new(f'{body.name}_mannequin_head', me)
bpy.context.scene.collection.objects.link(head)
for p in me.polygons:
    p.use_smooth = True
head.scale = (0.158 if gender == 'male' else 0.148, 0.2 if gender == 'male' else 0.188, H)
head.location = (hc.x, hc.y + 0.01, bottom + H * 0.5)
head.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
mw_head = head.matrix_world.copy()
head.parent = rig; head.parent_type = 'BONE'; head.parent_bone = 'Head'
bpy.context.view_layer.update()
head.matrix_world = mw_head
head.data.materials.append(body.data.materials[0])
sub = head.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
# neck plug: closes the seam between the cut neck and the mannequin head, front and back
nme = bpy.data.meshes.new('neck_plug'); nbm = bmesh.new()
bmesh.ops.create_cone(nbm, cap_ends=True, segments=40, radius1=1.0, radius2=0.9, depth=1.0)
nbm.to_mesh(nme); nbm.free()
plug = bpy.data.objects.new(f'{body.name}_neck_plug', nme); bpy.context.scene.collection.objects.link(plug)
for p_ in nme.polygons:
    p_.use_smooth = True
nr = 0.052 if gender == 'male' else 0.046
plug.scale = (nr, nr * 1.08, 0.11)
plug.location = (hc.x, hc.y + 0.005, neck_cut + 0.01)
bpy.context.view_layer.update()
mwp = plug.matrix_world.copy()
plug.parent = rig; plug.parent_type = 'BONE'; plug.parent_bone = 'Neck1' if 'Neck1' in rig.data.bones else 'Neck'
bpy.context.view_layer.update(); plug.matrix_world = mwp
plug.data.materials.append(body.data.materials[0])
bv = plug.modifiers.new('bevel', 'BEVEL'); bv.width = 0.15; bv.segments = 3

print('modifiers', [m.name for m in body.modifiers], 'head cut verts', len(cut), 'H', round(H, 3))

for name in ('Cube', 'Camera', 'Light'):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
rig.location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('SAVED', out_path, 'objects', [(o.name, o.type) for o in bpy.data.objects])
