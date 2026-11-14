import bpy, sys
for nm in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'/Users/isaac/projects/verdict-kr/work/production/assets/objaverse/glb/{nm}.glb')
    ms = {}
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            for m in o.data.materials:
                if m:
                    imgs = [n.image.name for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image] if m.use_nodes else []
                    ms[m.name] = imgs[:2]
    print('MATS', nm, '|', '; '.join(f'{k}{v if v else ""}' for k, v in ms.items())[:1500])
