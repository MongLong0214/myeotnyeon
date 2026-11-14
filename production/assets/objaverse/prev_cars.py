import bpy, sys, pathlib, mathutils, math, json, re
root = pathlib.Path('/Users/isaac/projects/verdict-kr/work/production/assets/objaverse')
PH = pathlib.Path('/Users/isaac/projects/verdict-kr/work/production/assets/polyhaven')
names = sys.argv[sys.argv.index('--') + 1:]
report = {}
for nm in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene; s.render.engine = 'BLENDER_EEVEE'; s.render.resolution_x, s.render.resolution_y = 960, 540
    s.eevee.taa_render_samples = 24; s.eevee.use_raytracing = True; s.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
    env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(str(PH / 'hansaplatz/hansaplatz_2k.hdr'))
    w.node_tree.links.new(env.outputs[0], w.node_tree.nodes['Background'].inputs[0]); w.node_tree.nodes['Background'].inputs[1].default_value = 2.5
    bpy.ops.import_scene.gltf(filepath=str(root / 'glb' / f'{nm}.glb'))
    meshes = [o for o in s.objects if o.type == 'MESH']
    lo = mathutils.Vector((1e9,)*3); hi = mathutils.Vector((-1e9,)*3)
    tris = 0
    for o in meshes:
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
        for c in o.bound_box:
            v = o.matrix_world @ mathutils.Vector(c); lo = mathutils.Vector(map(min, lo, v)); hi = mathutils.Vector(map(max, hi, v))
    dims = hi - lo
    length = max(dims.x, dims.y)
    k = 4.75 / length
    rootE = bpy.data.objects.new('R', None); s.collection.objects.link(rootE)
    for o in s.objects:
        if o.parent is None and o is not rootE: o.parent = rootE
    rootE.scale = (k, k, k)
    ctr = (lo + hi) / 2
    rootE.location = (-ctr.x * k, -ctr.y * k, -lo.z * k)
    bpy.context.view_layer.update()
    longaxis = 'x' if dims.x >= dims.y else 'y'
    suspicious = sorted({o.name for o in meshes if re.search(r'logo|badge|emblem|brand|plate|licen|text|letter|decal|sticker', o.name, re.I)} |
                        {m.name for o in meshes for m in o.data.materials if m and re.search(r'logo|badge|emblem|brand|plate|licen|decal|sticker', m.name, re.I)})
    bpy.ops.mesh.primitive_plane_add(size=40)
    fl = bpy.data.materials.new('f'); fl.use_nodes = True; fl.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.25, 0.25, 1)
    s.objects['Plane'].data.materials.append(fl)
    cd = bpy.data.cameras.new('c'); cd.lens = 40; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
    for view, loc in (('34', (6.2, -5.0, 1.7)), ('side', (0.01, -8.5, 1.2))):
        co.location = loc if longaxis == 'x' else (loc[1], loc[0], loc[2])
        co.rotation_euler = (mathutils.Vector((0, 0, 0.7)) - co.location).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = str(root / '_prev' / f'{nm}_{view}.png'); bpy.ops.render.render(write_still=True)
    report[nm] = dict(raw_dims=[round(x, 3) for x in dims], long_axis=longaxis, scale_to_4_75m=round(k, 4), tris=tris, objects=len(meshes), suspicious=suspicious[:20])
print('REPORT' + json.dumps(report))
