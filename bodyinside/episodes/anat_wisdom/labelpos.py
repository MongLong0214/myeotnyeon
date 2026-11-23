"""Blender -b wisdom.blend -P labelpos.py : writes label_pos.json = band-normalised screen position of the nerve-gap bracket per frame (for label2d.py)."""
import bpy, json
from bpy_extras.object_utils import world_to_camera_view
sc = bpy.context.scene; cam = sc.camera; O = bpy.data.objects
out = {}
for f in range(160, 204):
    sc.frame_set(f); bpy.context.view_layer.update()
    g = O['Gap2']; mw = g.matrix_world
    top = mw @ (g.data.vertices[0].co * 0 + __import__('mathutils').Vector((0, 0, g.dimensions.z / 2)))
    bot = mw @ __import__('mathutils').Vector((0, 0, -g.dimensions.z / 2))
    def p(w):
        c = world_to_camera_view(sc, cam, w); return [c.x, 1 - c.y]
    out[f] = {'top': p(top), 'bot': p(bot), 'mid': p(mw.translation)}
json.dump(out, open(bpy.path.abspath('//label_pos.json'), 'w'))
print('LABELPOS', out[185])
