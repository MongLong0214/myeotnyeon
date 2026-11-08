import bpy
def apply(scene):
 nt=scene.world.node_tree
 tc=nt.nodes.new('ShaderNodeTexCoord');n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=3.8;n.inputs['Detail'].default_value=5.5;n.inputs['Roughness'].default_value=.7;n.inputs['Distortion'].default_value=.45
 mp=nt.nodes.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(1,1,3);nt.links.new(tc.outputs['Normal'],mp.inputs[0]);nt.links.new(mp.outputs['Vector'],n.inputs['Vector'])
 r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.31;r.color_ramp.elements[0].color=(.012,.025,.042,1);r.color_ramp.elements[1].position=.65;r.color_ramp.elements[1].color=(.16,.22,.27,1)
 nt.links.new(n.outputs['Fac'],r.inputs[0]);bg=nt.nodes.get('Background');nt.links.new(r.outputs[0],bg.inputs['Color']);bg.inputs['Strength'].default_value=.38

 # Bound the fog to the physical set: infinite world fog otherwise extinguishes every sky ray.
 output=nt.nodes.get('World Output');links=list(output.inputs['Volume'].links)
 if links:
  old=links[0].from_node;density=old.inputs['Density'].default_value
  for link in links:nt.links.remove(link)
  mat=bpy.data.materials.new('bounded thin night haze');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');vol=nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=density;vol.inputs['Color'].default_value=(.55,.62,.68,1);vol.inputs['Anisotropy'].default_value=.5;mat.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume'])
  bpy.ops.mesh.primitive_cube_add(size=1,location=(0,25,15));fog=bpy.context.object;fog.name='bounded thin night haze';fog.scale=(180,200,65);fog.data.materials.append(mat)
