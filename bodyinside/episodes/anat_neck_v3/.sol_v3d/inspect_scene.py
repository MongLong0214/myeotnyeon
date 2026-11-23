import bpy
scene = bpy.context.scene
human = set(bpy.data.collections['Human | character'].all_objects)
print('SCENE', bpy.data.filepath, scene.cycles.samples, scene.render.resolution_percentage)
print('HUMAN', sorted(o.name for o in human if o.type in {'MESH', 'CURVE', 'CURVES'}))
for frame in [0, 6, 12, 18, 30, 59, 60, 61, 64, 65, 84, 720]:
    scene.frame_set(frame)
    print('VISIBLE', frame, sorted(o.name for o in scene.objects if o not in human and o.type in {'MESH', 'CURVE', 'CURVES'} and not o.hide_render))
