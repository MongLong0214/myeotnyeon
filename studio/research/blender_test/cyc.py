import bpy
s = bpy.context.scene
s.render.engine = 'CYCLES'
p = bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type = 'METAL'; p.get_devices()
for d in p.devices: d.use = ('GPU' in d.name)
s.cycles.device = 'GPU'
s.cycles.samples = 256; s.cycles.adaptive_threshold = 0.01
s.cycles.use_denoising = True; s.cycles.denoiser = 'OPENIMAGEDENOISE'
s.cycles.max_bounces = 8; s.cycles.volume_bounces = 1
s.cycles.use_light_tree = True
