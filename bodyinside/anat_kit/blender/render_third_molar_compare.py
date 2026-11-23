"""Renders ortho close-ups (top, buccal, three-quarter) of third_molar_v2/v3 at 800x800 and tiles them into third_molar_v3_compare.png.
usage: Blender -b --factory-startup -P render_third_molar_compare.py"""
import bpy, os, math, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(os.path.dirname(HERE), 'assets'); TMP = os.path.join(__import__('tempfile').gettempdir(), 'tm_cmp'); os.makedirs(TMP, exist_ok=True)
VIEWS = {'top': ((0, 0, 1), (0, 1, 0), 0.0, 0.0125, (0, 0, 5.0)), 'buccal': ((1, 0, 0), (0, 0, 1), 0, 0.021, (0, 0, -1.5)),
         'three_quarter': ((0.7, -0.55, 0.65), (0, 0, 1), 0, 0.015, (0, 0, 3.0))}
def render(name):
    with bpy.data.libraries.load(os.path.join(ASSETS, name + '.blend')) as (s, d): d.objects = ['ThirdMolarAsset']
    sc = bpy.context.scene
    for o in list(sc.objects): bpy.data.objects.remove(o)
    ob = d.objects[0]; sc.collection.objects.link(ob)
    m = bpy.data.materials.new('grey'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.55, 0.55, 0.55, 1); b.inputs['Roughness'].default_value = 0.85
    ob.data.materials.clear(); ob.data.materials.append(m)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = 800; sc.render.threads = 4
    sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.12, 0.12, 0.13, 1)
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); cam.data.type = 'ORTHO'; sc.camera = cam
    key = bpy.data.objects.new('k', bpy.data.lights.new('k', 'SUN')); sc.collection.objects.link(key); key.data.energy = 3.0; key.data.angle = 0.3
    fill = bpy.data.objects.new('f', bpy.data.lights.new('f', 'SUN')); sc.collection.objects.link(fill); fill.data.energy = 1.0; fill.data.angle = 0.6
    for v, (dirv, up, _, scale, tgt) in VIEWS.items():
        d_ = Vector(dirv).normalized(); t = Vector(tgt) * 0.001
        cam.location = t + d_ * 0.1; cam.rotation_euler = (-d_).to_track_quat('-Z', 'Y').to_euler()
        if v == 'top': cam.rotation_euler = (0, 0, 0)
        cam.data.ortho_scale = scale * 1.0; cam.data.clip_start = 0.001; cam.data.clip_end = 1
        # key from upper-left of the camera, grazing enough to read relief; fill opposite
        q = cam.rotation_euler.to_quaternion()
        key.rotation_euler = (q @ Vector((-0.5, 0.6, 0.62)).normalized()).to_track_quat('-Z', 'Y').to_euler() if False else q.to_euler()
        kd = q @ Vector((-0.55, 0.5, 1)); key.rotation_euler = kd.to_track_quat('Z', 'Y').to_euler()   # sun shines along -Z of its frame
        fd = q @ Vector((0.7, -0.2, 1)); fill.rotation_euler = fd.to_track_quat('Z', 'Y').to_euler()
        sc.render.filepath = f'{TMP}/{name}_{v}.png'; bpy.ops.render.render(write_still=True)
for n in ('third_molar_v2', 'third_molar_v3'): render(n)
import numpy as np
def px(p): i = bpy.data.images.load(p); a = np.array(i.pixels[:], dtype=np.float32).reshape(800, 800, 4); return a
g = np.zeros((1600, 2400, 4), np.float32); g[..., 3] = 1
for r, n in enumerate(('third_molar_v3', 'third_molar_v2')):   # image row 0 (top) = v2, row 1 = v3; Blender rows run bottom-up
    for c, v in enumerate(VIEWS): g[r * 800:(r + 1) * 800, c * 800:(c + 1) * 800] = px(f'{TMP}/{n}_{v}.png')
o = bpy.data.images.new('grid', 2400, 1600); o.pixels = g.ravel().tolist(); o.filepath_raw = os.path.join(ASSETS, 'third_molar_v3_compare.png'); o.file_format = 'PNG'; o.save(); print('GRID done')
