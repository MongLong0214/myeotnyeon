import sys, time, bpy
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(samples=32); W.build_lot()
cd = bpy.data.cameras.new('c'); cd.lens = 28; co = bpy.data.objects.new('c', cd); bpy.context.scene.collection.objects.link(co)
bpy.context.scene.camera = co
s = bpy.context.scene
co.location = (12, -13, 2.2); co.keyframe_insert('location', frame=1)
co.location = (11, -12, 2.2); co.keyframe_insert('location', frame=8)
co.rotation_euler = (Vector((-2, 6, 3.5)) - Vector((12, -13, 2.2))).to_track_quat('-Z', 'Y').to_euler()
s.frame_start, s.frame_end = 1, 8
s.render.filepath = '//test2/anim_'
t = time.time(); bpy.ops.render.render(animation=True); print('ANIM8', round(time.time() - t, 1), 's')
