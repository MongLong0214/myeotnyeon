# per-object visibility diff: Blender -b X.blend -P hide_test.py -- FRAME out_prefix name1 name2 ...   renders the frame with each named object hidden (draft res)
import sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]; f = int(a[0]); pre = a[1]; sc = bpy.context.scene
sc.cycles.samples = 12; sc.render.resolution_percentage = 50; sc.render.use_motion_blur = False
p = bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type = 'METAL'; p.get_devices()
for d in p.devices: d.use = (d.type == 'METAL')
sc.frame_set(f)
for n in a[2:]:
    o = bpy.data.objects[n]; o.hide_render = True; o.animation_data_clear() if o.animation_data else None
    sc.render.filepath = '%s_%s.png' % (pre, n.replace(' ', '_')); bpy.ops.render.render(write_still=True); o.hide_render = False
