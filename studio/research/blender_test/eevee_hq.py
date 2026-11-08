import bpy
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'
e = s.eevee
e.taa_render_samples = 64
e.use_raytracing = True; e.ray_tracing_method = 'SCREEN'; e.ray_tracing_options.resolution_scale = '1'
e.use_fast_gi = True
e.shadow_resolution_scale = 1.0; e.shadow_ray_count = 3; e.shadow_step_count = 12
e.volumetric_tile_size = '2'; e.volumetric_samples = 128; e.use_volumetric_shadows = True
s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5
s.render.fps = 24; s.frame_start, s.frame_end = 1, 72
s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_depth = '16'
# final look tweaks
m = bpy.data.objects['asphalt'].active_material; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
cr = next(n for n in nt.nodes if n.type == 'VALTORGB' and n.color_ramp.elements[0].color[0] < 0.05)
cr.color_ramp.elements[0].position = 0.52; cr.color_ramp.elements[1].position = 0.60
mix1 = next(n for n in nt.nodes if n.type == 'MIX' and n.data_type == 'RGBA')
mix1.inputs['B'].default_value = (0.22, 0.22, 0.23, 1)
dark = nt.nodes.new('ShaderNodeMix'); dark.data_type = 'RGBA'; dark.blend_type = 'MULTIPLY'
dark.inputs['Factor'].default_value = 1.0; dark.inputs['B'].default_value = (0.5, 0.5, 0.52, 1)
nt.links.new(mix1.outputs['Result'], dark.inputs['A']); nt.links.new(dark.outputs['Result'], bsdf.inputs['Base Color'])
for n in s.world.node_tree.nodes:
    if n.type in ('PRINCIPLED_VOLUME', 'VOLUME_SCATTER') and 'Density' in n.inputs:
        n.inputs['Density'].default_value = 0.0016
