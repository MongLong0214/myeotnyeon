"""A registered macro finish for waxy enamel or rubber-like gingiva."""
import json
import runpy
import sys
from pathlib import Path

import bpy

options=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())


def texture(scene,*unused):
    bpy.app.handlers.render_pre.remove(texture)
    profiles=[('Hydrated enamel',.30,.24,.018),('Attached mucosa • stipple and subepithelial vessels',.43,.16,.026)]
    for name,roughness,coat,relief in profiles:
        tree=bpy.data.materials[name].node_tree
        shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
        noise=tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=3.2
        noise.inputs['Detail'].default_value=3
        coord=tree.nodes.new('ShaderNodeTexCoord')
        tree.links.new(coord.outputs['Object'],noise.inputs['Vector'])
        ramp=tree.nodes.new('ShaderNodeValToRGB')
        for element,value in zip(ramp.color_ramp.elements,(roughness-.085,roughness+.085)):
            element.color=(value,value,value,1)
        tree.links.new(noise.outputs['Fac'],ramp.inputs[0])
        tree.links.new(ramp.outputs['Color'],shader.inputs['Roughness'])
        film=shader.inputs['Coat Weight']
        for link in list(film.links):tree.links.remove(link)
        film.default_value=coat
        normal=shader.inputs['Normal']
        bump=tree.nodes.new('ShaderNodeBump')
        bump.inputs['Distance'].default_value=relief
        bump.inputs['Strength'].default_value=.16
        if normal.is_linked:
            tree.links.new(normal.links[0].from_socket,bump.inputs['Normal'])
        tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        tree.links.new(bump.outputs['Normal'],normal)
    bpy.context.view_layer.update()


if options['mode']=='render':
    bpy.app.handlers.render_pre.append(texture)
base='socket_view.py' if options.get('empty_socket') else 'scene.py'
runpy.run_path(str(Path(__file__).with_name(base)),run_name='__main__')
