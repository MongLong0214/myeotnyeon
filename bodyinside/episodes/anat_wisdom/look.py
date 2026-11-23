import bpy, sys, re
from mathutils import Vector
sc=bpy.context.scene
argv=sys.argv[sys.argv.index("--")+1:]
p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices()
for d in p.devices: d.use=(d.type=='METAL')
def mat(name,col):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=col; return m
cols={'bone':(0.8,0.75,0.62,1),'tooth':(0.95,0.95,0.92,1),'gum':(0.8,0.3,0.3,1),'nerve':(1,0.8,0.1,1),'skin':(0.8,0.55,0.45,1)}
M={k:mat(k,v) for k,v in cols.items()}
for o in bpy.data.objects:
    n=o.name
    k='skin'
    if re.search(r'molar|premolar|incisor|canine',n): k='tooth'
    elif n=='Gingiva': k='gum'
    elif 'nerve' in n: k='nerve'
    elif re.search(r'bone|Mandible|Maxilla|Vomer|Atlas|Axis|Vertebra',n): k='bone'
    o.data.materials.clear(); o.data.materials.append(M[k])
    if k=='skin' or n=='Tongue': o.hide_render=True
cam=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=50; cam.data.clip_start=0.002
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7
sc.render.engine='CYCLES'; sc.cycles.device='GPU'; sc.cycles.samples=16; sc.render.resolution_x=640; sc.render.resolution_y=400
T=Vector(eval(argv[0]))
for i,off in enumerate(eval(argv[1])):
    cam.location=T+Vector(off)
    d=T-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"//look/{argv[2]}_{i}.png"; bpy.ops.render.render(write_still=True)
