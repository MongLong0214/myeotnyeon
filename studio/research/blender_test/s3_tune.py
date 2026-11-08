import bpy, math
s = bpy.context.scene
# 1) thinner haze
w = s.world
for n in w.node_tree.nodes:
    for key in ('Density',):
        if key in n.inputs and n.type in ('PRINCIPLED_VOLUME', 'VOLUME_SCATTER', 'VOLUME_ABSORPTION'):
            n.inputs[key].default_value = 0.0022
# 2) wet asphalt: darker, near-mirror in puddles
m = bpy.data.objects['asphalt'].active_material; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
cr = next(n for n in nt.nodes if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].position - 0.46) < 1e-3)
cr.color_ramp.elements[0].color = (0.015, 0.015, 0.015, 1)
src_col = next((l.from_socket for l in nt.links if l.to_socket == bsdf.inputs['Base Color']), None)
inv = nt.nodes.new('ShaderNodeInvert'); nt.links.new(cr.outputs['Color'], inv.inputs['Color'])
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
nt.links.new(inv.outputs['Color'], mix.inputs['Factor'])
if src_col: nt.links.new(src_col, mix.inputs['A'])
mix.inputs['B'].default_value = (0.32, 0.32, 0.33, 1)
nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
# 3) hero headlights hotter + beams brighter and tighter
for mt in bpy.data.materials:
    if mt.name.startswith('hero_hl'):
        em = next((n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if em and 'Emission Strength' in em.inputs: em.inputs['Emission Strength'].default_value = 140
for o in bpy.data.objects:
    if o.name.startswith('hero_beam') and o.type == 'LIGHT':
        o.data.energy = 2600; o.data.spot_size = math.radians(48); o.data.spot_blend = 0.45
# 4) Cycles, tiled to avoid Metal 'Impacting Interactivity'
s.render.engine = 'CYCLES'
s.cycles.samples = 320; s.cycles.adaptive_threshold = 0.008
s.cycles.use_denoising = True; s.cycles.denoiser = 'OPENIMAGEDENOISE'
s.cycles.max_bounces = 10; s.cycles.glossy_bounces = 6; s.cycles.volume_bounces = 1
s.cycles.use_auto_tile = True; s.cycles.tile_size = 512
s.cycles.use_light_tree = True
s.render.fps = 24; s.frame_start, s.frame_end = 1, 72
s.render.use_motion_blur = True
s.frame_set(36)
bpy.ops.wm.save_as_mainfile(filepath='research/blender_test/s3.blend')
print('TUNED')
