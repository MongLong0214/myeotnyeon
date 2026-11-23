# quick workbench still of a .blend: Blender -b X.blend -P look.py -- out.png [x y z ortho_scale azimuth_deg]
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; c = Vector((float(a[1]), float(a[2]), float(a[3]))) if len(a) > 3 else Vector((0, 0.03, 1.52)); sc_ = float(a[4]) if len(a) > 4 else 0.36; az = math.radians(float(a[5])) if len(a) > 5 else 0
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = 1080; sc.render.resolution_y = 800
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'; sc.display.shading.show_cavity = True
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = sc_; co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
d = Vector((-math.cos(az), -math.sin(az) * -1, 0)).normalized(); co.location = c + d * 1.0
co.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out; sc.render.film_transparent = False
bpy.ops.render.render(write_still=True)
