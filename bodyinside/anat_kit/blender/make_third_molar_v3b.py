"""third_molar_v3b: v3 with a re-shaped buccal face: two shallow lobes (MB, DB) and one buccal groove between them, instead of a cluster of soft knobs.
Same object name, same origin; the bbox is restored exactly at the end.  Frame as v3: crown +z, buccal +x, distal +y, metres.
usage: Blender -b --factory-startup -P make_third_molar_v3b.py -> anat_kit/assets/third_molar_v3b.blend"""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(os.path.dirname(HERE), 'assets')
with bpy.data.libraries.load(os.path.join(ASSETS, 'third_molar_v3.blend')) as (s, d): d.objects = ['ThirdMolarAsset']
ob = d.objects[0]; bpy.context.scene.collection.objects.link(ob); me = ob.data
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3) * 1000.0
lo0, hi0 = P.min(0).copy(), P.max(0).copy()
ss = lambda a, b, t: (lambda u: u * u * (3 - 2 * u))(np.clip((t - a) / (b - a), 0, 1))
g = lambda y, c, s_: np.exp(-((y - c) ** 2) / (2 * s_ ** 2))
x, y, z = P[:, 0], P[:, 1], P[:, 2]
lobe = np.maximum(g(y, -2.5, 1.45), g(y, 1.2, 1.3))                 # MB and DB lobes, 1 at their crowns
groove = g(y, -0.75, 0.5)                                             # the single buccal groove
vert = ss(3.0, 4.4, z)                                                 # fades out toward the cervical line
buc = ss(1.8, 4.2, x)                                                  # buccal surface only
_K = float(os.environ.get('GROOVE_K', '1.0'))
d = -(0.65 * _K * (1 - lobe) + 0.85 * _K * groove) * vert * buc                  # always inward: lobes stay at the old surface, the groove cuts in
P[:, 0] = x + d
me.vertices.foreach_set('co', (P / 1000.0).ravel()); me.update()
ob.modifiers.clear(); sm = ob.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.4; sm.iterations = 4
bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.modifier_apply(modifier='sm')
for p in me.polygons: p.use_smooth = True
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3) * 1000.0
# bbox restored: scale x about the minimum so the buccal extent is the old one
for ax in range(3):
    lo1, hi1 = P[:, ax].min(), P[:, ax].max()
    if abs((hi1 - lo1) - (hi0[ax] - lo0[ax])) > 1e-6: P[:, ax] = lo0[ax] + (P[:, ax] - lo1) * (hi0[ax] - lo0[ax]) / (hi1 - lo1)
me.vertices.foreach_set('co', (P / 1000.0).ravel()); me.update()
a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); a = a.reshape(-1, 3) * 1000
print('v3 bbox', lo0.round(3), hi0.round(3)); print('v3b bbox', a.min(0).round(3), a.max(0).round(3), 'origin', tuple(ob.location))
ob.name = 'ThirdMolarAsset'; me.name = 'ThirdMolarAsset'
out = os.path.join(ASSETS, os.environ.get('V3B_OUT', 'third_molar_v3b.blend')); bpy.data.libraries.write(out, {ob}, fake_user=True); print('ASSET', out)
