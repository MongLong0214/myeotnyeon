import bpy, sys, mathutils
for nm in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'/Users/isaac/projects/verdict-kr/work/production/assets/objaverse/glb/{nm}.glb')
    from collections import Counter
    print('TYPES', nm, Counter(o.type for o in bpy.context.scene.objects))
    for o in bpy.context.scene.objects:
        if o.type in ('LIGHT', 'CAMERA'):
            print('  NONMESH', o.type, o.name, getattr(o.data, 'energy', None))
        if o.type == 'MESH':
            for m in o.data.materials:
                if m and m.use_nodes and any(n.bl_idname.startswith('ShaderNodeVolume') or 'Volume' in n.bl_idname for n in m.node_tree.nodes):
                    print('  VOLUME MAT', o.name, m.name)
                if m and m.use_nodes:
                    out = m.node_tree.nodes.get('Material Output')
                    if out and out.inputs['Volume'].links: print('  VOLUME LINK', o.name, m.name)
