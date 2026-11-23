import bpy, sys
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
for d in p.devices: d.use=(d.type=='METAL')
sc=bpy.context.scene
if argv and argv[0].startswith("//"):
    sc.render.filepath=argv[0]
    if len(argv)>1: sc.cycles.samples=int(argv[1])
    if len(argv)>2: sc.render.resolution_percentage=int(argv[2])
