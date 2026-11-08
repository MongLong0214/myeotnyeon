import sys, time, bpy
sys.path.insert(0, 'production/blender')
import world2 as W
from mathutils import Vector
W.reset(); W.world(haze=0.0); W.ground(); W.lot_markings()
W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=False, tag='car_A')
W.car('lexus_es350', (3.5, 2.0, 0), yaw=3.14, paint=(0.85, 0.86, 0.86), tag='lx')
W.car('kia_optima_sx', (3.5, -2.5, 0), yaw=0, paint=(0.45, 0.46, 0.48), tag='op')
s = bpy.context.scene
W.light('SUN', 'sun', (0, 0, 10), 4.0, rot=(0.6, 0.2, 0.5)); bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.5; bpy.context.scene.view_settings.exposure = 1.0
cd = bpy.data.cameras.new('c'); cd.lens = 50; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
for tag, loc, tgt in (('front', (2.2, 0.0, 0.9), (-0.6, 0, 0.7)), ('rear', (-8.2, 0.5, 1.3), (-5.4, 0, 0.9)), ('lx', (8.0, 2.0, 1.0), (5.5, 2.0, 0.6))):
    co.location = loc; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'//test2/scrub_{tag}.png'; bpy.ops.render.render(write_still=True)
