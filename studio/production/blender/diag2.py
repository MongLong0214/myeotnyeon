import os, sys, tempfile, bpy, numpy as np
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(); W.world(); W.ground()
s = bpy.context.scene
W.light('SUN', 'sun', (0, 0, 10), 4.0, rot=(0.6, 0.2, 0.5))
cd = bpy.data.cameras.new('c'); cd.lens = 50; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (-8.2, 0.5, 1.3); co.rotation_euler = (Vector((-5.4, 0, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
def r(tag):
    s.render.filepath = os.path.join(tempfile.gettempdir(), f'diag2_{tag}.png'); bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(s.render.filepath); px = np.array(im.pixels[:]); print('DIAG', tag, round(px.mean(), 4), 'camera', s.camera.name, flush=True)
r('base')
W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.25, 0.27, 0.3), lights=False, tag='car_A'); r('hero')
print('CAMS', [o.name for o in s.objects if o.type == 'CAMERA'], 'scene cam', s.camera.name)
big = [(o.name, tuple(round(d, 1) for d in o.dimensions)) for o in s.objects if o.type == 'MESH' and max(o.dimensions) > 20]
print('BIG', big[:10])
bpy.context.view_layer.update()
inst = [o for o in s.objects if o.type == 'MESH' and o.parent and o.parent.name == 'car_A']
print('INST', len(inst))
for o in inst[:4]:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    print('  ', o.name, o.hide_render, [round(min(v[i] for v in bb), 2) for i in range(3)], [round(max(v[i] for v in bb), 2) for i in range(3)])
tpl = s.objects.get('accord_2019_tpl'); print('TPL', tpl.location[:], tpl.rotation_euler[:])
