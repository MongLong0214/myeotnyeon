import sys,time,bpy
sys.path.insert(0,'/Users/isaac/projects/verdict-kr/work/production/blender')
import world as W
W.reset();h=W.build_lot()
lights=[o for o in bpy.data.objects if o.type=='LIGHT']
print('LIGHTS',len(lights),[(o.name,o.data.energy,tuple(round(x,1) for x in o.location),o.visible_get()) for o in lights][:4])
print('VIEWLAYER', [o.name for o in bpy.context.view_layer.objects if o.type=='LIGHT'][:3])
s=bpy.context.scene
s.world.node_tree.links.remove(s.world.node_tree.nodes['World Output'].inputs['Volume'].links[0])
W.camera(loc=(9,-9,2.4),target=(-1,0.5,0.9),lens=32)
s.render.filepath='//test/novol.png';bpy.ops.render.render(write_still=True)
