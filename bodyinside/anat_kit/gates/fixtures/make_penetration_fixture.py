# Blender -b --factory-startup -P make_penetration_fixture.py : two intersecting tessellated spheres -> penetration-fixture/scene.blend (+ pairs.json); the gate MUST report a violation
import bpy, json, os
H = os.path.dirname(os.path.abspath(__file__)) + '/interpenetration-jaw-neck'; os.makedirs(H, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
for n, x in (('Mandible', 0.0), ('Vertebra C3', 0.5)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.6, location=(x, 0, 0)); bpy.context.active_object.name = n
bpy.context.scene.frame_start = 0; bpy.context.scene.frame_end = 30
bpy.ops.wm.save_as_mainfile(filepath=H + '/scene.blend'); json.dump([['Mandible', 'Vertebra C3']], open(H + '/pairs.json', 'w'))
