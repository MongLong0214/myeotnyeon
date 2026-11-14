import sys, bpy, numpy as np
sys.path.insert(0, '/Users/isaac/projects/verdict-kr/work/production/blender')
import world2 as W
from mathutils import Vector
W.reset(); W.world(); W.ground()
s = bpy.context.scene
W.light('SUN', 'sun', (0, 0, 10), 4.0, rot=(0.6, 0.2, 0.5))
cd = bpy.data.cameras.new('c'); cd.lens = 50; co = bpy.data.objects.new('c', cd); s.collection.objects.link(co); s.camera = co
co.location = (2.2, 0.0, 1.5); co.rotation_euler = (Vector((-0.6, 0, 0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
def r(tag):
    s.render.filepath = f'/tmp/claude-501/diag_{tag}.png'; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(s.render.filepath); px = np.array(im.pixels[:]); print('DIAG', tag, round(px.mean(), 4))
r('base')
s.world.node_tree.links.remove(s.world.node_tree.nodes['World Output'].inputs['Volume'].links[0]); r('novol')
s.render.use_motion_blur = False; r('nomb')
s.eevee.use_raytracing = False; r('nort')
