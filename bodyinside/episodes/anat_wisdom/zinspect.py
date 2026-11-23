import bpy, sys
argv = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=argv[0])
obs=[o for o in bpy.data.objects if o.type=='MESH']
print("NMESH",len(obs))
import re
pat=re.compile(argv[1],re.I)
for o in obs:
    if pat.search(o.name):
        bb=[o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
        zs=[v.z for v in bb]; xs=[v.x for v in bb]; ys=[v.y for v in bb]
        print("OBJ",o.name,len(o.data.vertices),"x%.3f..%.3f y%.3f..%.3f z%.3f..%.3f"%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
