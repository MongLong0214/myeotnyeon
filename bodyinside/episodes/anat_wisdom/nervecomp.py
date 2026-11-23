# applied to a built wisdom.blend: nerve on its own view layer, alpha-over across the ghost region f150-225
import bpy
sc = bpy.context.scene; D = bpy.data
nerve = D.objects['Nerve2']
ev = D.collections.new('Everything'); sc.collection.children.link(ev)
nc = D.collections.new('NerveC'); sc.collection.children.link(nc)
for o in list(sc.collection.objects):
    if o.type in ('MESH', 'CURVE', 'FONT') and o is not nerve:
        ev.objects.link(o); sc.collection.objects.unlink(o)
sc.collection.objects.unlink(nerve); nc.objects.link(nerve)
vl0 = sc.view_layers[0]
vln = sc.view_layers.new('NerveOnly')
for lc in vln.layer_collection.children:
    if lc.name == 'Everything': lc.indirect_only = True
    elif lc.name != 'NerveC': lc.exclude = True   # Cutters etc (hidden anyway)
g = D.node_groups.new('NerveComp', 'CompositorNodeTree')
g.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
a = g.nodes.new('CompositorNodeRLayers'); a.scene = sc; a.layer = vl0.name
b = g.nodes.new('CompositorNodeRLayers'); b.scene = sc; b.layer = 'NerveOnly'
ao = g.nodes.new('CompositorNodeAlphaOver'); fv = g.nodes.new('ShaderNodeValue')
out = g.nodes.new('NodeGroupOutput')
g.links.new(a.outputs['Image'], ao.inputs['Background']); g.links.new(b.outputs['Image'], ao.inputs['Foreground']); g.links.new(fv.outputs[0], ao.inputs['Factor'])
g.links.new(ao.outputs[0], out.inputs[0])
for f, v in ((149, 0.0), (157, 1.0), (218, 1.0), (225, 0.0)):
    fv.outputs[0].default_value = v; fv.outputs[0].keyframe_insert('default_value', frame=f)
sc.compositing_node_group = g; sc.use_nodes = True
# the nerve layer only needs to render the nerve; main keeps everything
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath.replace('.blend', '_nc.blend'))
print('NCSAVED')
