import bpy, sys, mathutils
nm = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'/Users/isaac/projects/verdict-kr/work/production/assets/objaverse/glb/{nm}.glb')
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    lo = mathutils.Vector(map(min, *[(v.x, v.y, v.z) for v in bb])) if False else None
    xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
    mats = [m.name for m in o.data.materials if m]
    print('OBJ', o.name[:50], '| tris', sum(len(p.vertices)-2 for p in o.data.polygons), '| x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)), '|', mats[:4])
