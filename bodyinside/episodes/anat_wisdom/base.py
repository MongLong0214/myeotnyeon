# Stage A: import the Z-Anatomy parts used by the episode into base.blend (world-space, transforms applied).
import bpy, re
from mathutils import Vector
A=(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../../research/anatomy3d/zanatomy/")
OUT=(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../../episodes/anat_wisdom/base.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(path, keep):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=A+path)
    new=[o for o in bpy.data.objects if o not in before]
    meshes=[o for o in new if o.type=='MESH']
    for o in meshes:
        mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
    for o in new:
        if o.type!='MESH' or not keep(o): bpy.data.objects.remove(o)
SK=re.compile(r"^(Mandible|Maxilla\.[lr]|Lower .*(molar|premolar|incisor|canine).*|Upper .*(molar|premolar|incisor|canine).*|Frontal bone|Parietal bone\.[lr]|Occipital bone|Temporal bone\.[lr]|Sphenoid bone|Zygomatic bone\.[lr]|Nasal bone\.[lr]|Ethmoid bone|Lacrimal bone\.[lr]|Palatine bone\.[lr]|Vomer|Inferior nasal concha bone\.[lr]|Hyoid bone|Atlas \(C1\)|Axis \(C2\)|Vertebra C[3-5])$")
imp("SkeletalSystem100.fbx", lambda o: bool(SK.match(o.name)))
imp("NervousSystem100.fbx", lambda o: o.name in ("Inferior alveolar nerve.l","Mental nerve.l","Lingual nerve.l"))
imp("VisceralSystem100.fbx", lambda o: o.name in ("Gingiva","Tongue"))
imp("Regions of human body100.fbx", lambda o: (not o.name.endswith('.j')) and 'Cross' not in o.name and not re.search(r'Hair|Eyelash|Eyebrow',o.name) and min((o.matrix_world@Vector(c)).z for c in o.bound_box)>1.40 and abs(min((o.matrix_world@Vector(c)).x for c in o.bound_box))<0.2)
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=bpy.data.objects['Mandible']
bpy.ops.object.make_single_user(object=True,obdata=True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
for o in bpy.data.objects: print("K",o.name,len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
