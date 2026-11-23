import bpy, json, sys
from bpy_extras.object_utils import world_to_camera_view
s = bpy.context.scene
o = {}
for f in (3, 65, 100, 150, 210, 275, 296, 299, 714, 800, 811, 829, 843, 856, 878, 920):
    s.frame_set(f)
    c = s.camera
    o[f] = {'pos': list(c.location), 'angle': list(c.rotation_quaternion),
            'lens': c.data.lens, 'dof': c.data.dof.use_dof,
            'finger': list(world_to_camera_view(s, c, bpy.data.objects['A_Ear'].matrix_world.translation))}
d = {'frames': o, 'render': [s.render.resolution_x, s.render.resolution_y,
                             s.render.resolution_percentage, s.cycles.samples, s.get('spp_boost')],
     'relative_images': [im.filepath for im in bpy.data.images if im.filepath.startswith('//') and not im.packed_file]}
with open(sys.argv[-1], 'w') as file:
    json.dump(d, file, indent=2)
