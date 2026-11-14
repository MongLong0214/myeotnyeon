import sys, time, bpy, math
sys.path.insert(0, '/Users/isaac/projects/verdict-kr/work/production/blender')
import world2 as W
from mathutils import Vector
W.reset(samples=32); W.build_lot(); W.parked_cars()
hero = W.car('accord_2019', (-3.0, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=True, tag='car_A')
s = bpy.context.scene; e = s.eevee
cd = bpy.data.cameras.new('c'); cd.lens = 35; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (6.5, -5.5, 1.5); co.rotation_euler = (Vector((-3, 0.3, 0.9)) - co.location).to_track_quat('-Z', 'Y').to_euler()
def r(tag):
    s.render.filepath = f'//test2/prof_{tag}.png'; t = time.time(); bpy.ops.render.render(write_still=True); print('PROF', tag, round(time.time() - t, 1), flush=True)
r('warmup')
r('baseline')
s.render.use_motion_blur = False; r('no_mblur')
e.taa_render_samples = 16; r('s16')
e.use_raytracing = False; r('no_rt')
wo = s.world.node_tree; lk = wo.nodes['World Output'].inputs['Volume'].links
if lk: wo.links.remove(lk[0])
r('no_vol')
e.shadow_resolution_scale = 0.5; r('shadow_half')
for o in s.objects:
    if o.name.startswith('park_') and o.type == 'MESH': o.hide_render = True
r('no_parked')
for o in s.objects:
    if o.name.startswith(('tree', 'shrub')) or (o.parent and o.parent.name.startswith(('tree', 'shrub'))): o.hide_render = True
r('no_veg')
