import bpy
p = bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type = 'METAL'; p.get_devices()
for d in p.devices: d.use = ('GPU' in d.name)
bpy.context.scene.cycles.device = 'GPU'
