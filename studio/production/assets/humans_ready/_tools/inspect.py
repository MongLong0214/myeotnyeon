# usage: Blender -b --factory-startup --python-exit-code 1 --python inspect.py -- <file> <out.json>
import bpy, sys, json, os
argv = sys.argv[sys.argv.index('--')+1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
ext = os.path.splitext(src)[1].lower()
if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=src)
elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=src)
elif ext == '.bvh': bpy.ops.import_anim.bvh(filepath=src)
elif ext == '.blend':
    bpy.ops.wm.open_mainfile(filepath=src)
res = {'objects': [], 'actions': []}
for o in bpy.data.objects:
    d = {'name': o.name, 'type': o.type, 'dims': [round(v, 3) for v in o.dimensions]}
    if o.type == 'ARMATURE':
        d['bones'] = [b.name for b in o.data.bones]
    if o.type == 'MESH':
        d['verts'] = len(o.data.vertices); d['mats'] = [m.name for m in o.data.materials if m]
    res['objects'].append(d)
for a in bpy.data.actions:
    fr = a.frame_range
    res['actions'].append({'name': a.name, 'start': round(fr[0], 2), 'end': round(fr[1], 2), 'frames': int(round(fr[1]-fr[0]))+1})
res['fps'] = bpy.context.scene.render.fps
json.dump(res, open(out, 'w'), indent=1)
print('OK', len(res['actions']), 'actions')
