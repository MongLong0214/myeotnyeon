import bpy
from mathutils import Vector
s=bpy.context.scene
for f in (100,590,630,680):
 s.frame_set(f); bpy.context.view_layer.update()
 print('FRAME',f,'render',s.render.resolution_x,s.render.resolution_y,s.cycles.samples)
 for o in s.objects:
  if (f==100 and not o.hide_render and o.type in {'MESH','CURVE'}) or o.name.startswith(('J_', 'SkelRoot','Herniation','ContactRing','A_C56','A_Root','A_Contact', 'Camera')):
   print(o.name,o.hide_render, tuple(round(x,4) for x in o.matrix_world.translation),tuple(round(x,4) for x in o.rotation_euler),o.animation_data.action.name if o.animation_data and o.animation_data.action else None)
