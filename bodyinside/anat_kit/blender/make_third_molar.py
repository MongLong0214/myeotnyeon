"""Builds the anat_kit third-molar asset (lower left) and saves it to anat_kit/assets/third_molar_l.blend.
usage: Blender -b <any blend with Z-Anatomy "Lower first molar tooth.l"> -P make_third_molar.py
Z-Anatomy and BodyParts3D have no third molars. This copies the first molar, subdivides it to multires density (level 3)
and sculpts it procedurally with sculpt_molar: 5 cusps, central/buccal/lingual/distobuccal fissures, cervical line,
two shorter converging roots. Object "ThirdMolarAsset" stays in the Z-Anatomy world frame (left mandible), unrotated."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import sculpt_molar, link, sel_only
src = bpy.data.objects['Lower first molar tooth.l']
t = src.copy(); t.data = src.data.copy(); t.name = 'ThirdMolarAsset'; t.data.name = 'ThirdMolarAsset'; link(t)
for m in list(t.modifiers): t.modifiers.remove(m)
sel_only(t); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
sculpt_molar(t, levels=3, root_converge=0.30, root_curve=0.0, distal=(0, 1, 0), root_len=0.72, cusp=0.0016, fissure=0.0012, cervical=0.0003)
for pg in t.data.polygons: pg.use_smooth = True
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'third_molar_l.blend')
bpy.data.libraries.write(out, {t}, fake_user=True); print('ASSET', out, len(t.data.vertices))
