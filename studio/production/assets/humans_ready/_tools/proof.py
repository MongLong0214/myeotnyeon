# Blender 5.2 headless proof: import every model/motion file in an asset dir, list actions + frame counts + bones.
# usage: Blender -b --factory-startup --python-exit-code 1 --python proof.py -- <asset_dir>
import bpy, sys, os, json
d = sys.argv[sys.argv.index('--') + 1]
out = {'blender': bpy.app.version_string, 'files': {}}
for fn in sorted(os.listdir(d)):
    ext = os.path.splitext(fn)[1].lower()
    if ext not in ('.glb', '.gltf', '.fbx', '.bvh'): continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = os.path.join(d, fn)
    if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=p)
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=p)
    else: bpy.ops.import_anim.bvh(filepath=p, update_scene_fps=True, update_scene_duration=True)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    bones = [b.name for b in arms[0].data.bones] if arms else []
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    acts = [{'name': a.name, 'frame_start': int(a.frame_range[0]), 'frame_end': int(a.frame_range[1]),
             'frames': int(round(a.frame_range[1] - a.frame_range[0])) + 1,
             'seconds': round((a.frame_range[1] - a.frame_range[0]) / fps, 2)} for a in bpy.data.actions]
    out['files'][fn] = {'scene_fps': fps, 'armatures': [a.name for a in arms], 'bone_count': len(bones),
                        'bones_sample': bones[:24], 'mixamorig_bones': any('mixamo' in b.lower() for b in bones),
                        'meshes': [{'name': m.name, 'verts': len(m.data.vertices), 'dims_m': [round(v, 3) for v in m.dimensions]} for m in meshes],
                        'actions': acts}
    print('PROOF', fn, len(acts), 'actions', len(bones), 'bones')
json.dump(out, open(os.path.join(d, 'blender_proof.json'), 'w'), indent=1)
