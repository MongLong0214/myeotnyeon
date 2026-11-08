import bpy, sys, pathlib, mathutils, math
root = pathlib.Path('production/assets/polyhaven')
ids = sys.argv[sys.argv.index('--') + 1:]
for aid in ids:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene; s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x, s.render.resolution_y = 640, 400
    s.eevee.taa_render_samples = 16
    w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
    env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(str(root / 'hansaplatz/hansaplatz_2k.hdr'))
    w.node_tree.links.new(env.outputs[0], w.node_tree.nodes['Background'].inputs[0]); w.node_tree.nodes['Background'].inputs[1].default_value = 3.0
    blend = next((root / aid).glob('*.blend'))
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith('wdg_') and 'LOD1' not in n and 'LOD2' not in n and 'LOD3' not in n and 'LOD4' not in n and 'LOD5' not in n and n not in ('Sun', 'Spot', 'Camera')]
    lo = mathutils.Vector((1e9,)*3); hi = mathutils.Vector((-1e9,)*3)
    for o in dst.objects:
        if o is None: continue
        s.collection.objects.link(o)
        if o.type == 'MESH':
            for c in o.bound_box:
                v = o.matrix_world @ mathutils.Vector(c); lo = mathutils.Vector(map(min, lo, v)); hi = mathutils.Vector(map(max, hi, v))
    c = (lo + hi) / 2; r = (hi - lo).length / 2
    cd = bpy.data.cameras.new('c'); cd.lens = 50; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
    co.location = c + mathutils.Vector((r * 1.6, -r * 2.4, r * 0.9))
    co.rotation_euler = (c - co.location).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = str(pathlib.Path('production/assets/_previews') / f'{aid}.png')
    bpy.ops.render.render(write_still=True)
