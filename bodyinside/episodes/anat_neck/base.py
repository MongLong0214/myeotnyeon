# Stage A: import the Z-Anatomy parts used by the neck episode into base.blend (world space, left half + midline only).
# usage: Blender -b --factory-startup -P base.py
import sys, re
sys.path.insert(0, (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit/blender'))
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
from kit import import_parts
SK = re.compile(r"^(Atlas \(C1\)|Axis \(C2\)|Vertebra (C[3-7]|T[1-4])|Occipital bone|Frontal bone|Sphenoid bone|Ethmoid bone|Vomer|Mandible|"
                r"(Parietal bone|Temporal bone|Maxilla|Zygomatic bone|Nasal bone|Lacrimal bone|Palatine bone|Inferior nasal concha bone)\.l)$")
import_parts('SkeletalSystem100.fbx', lambda o: bool(SK.match(o.name)))
NV = ("White matter of spinal cord", "Anterior root of spinal nerve.l", "Posterior root of spinal nerve.l", "Spinal ganglion.l")
import_parts('NervousSystem100.fbx', lambda o: o.name in NV)
MU = re.compile(r"^(Splenius capitis muscle|Semispinalis colli muscle|Semispinalis capitis muscle|Levator scapulae|Descending part of trapezius muscle|Spinalis capitis muscle|Longus colli muscle|Sternocleidomastoid muscle|Rhomboid minor muscle)\.l$")
import_parts('MuscularSystem100.fbx', lambda o: bool(MU.match(o.name)))
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = bpy.data.objects['Mandible']
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # origins at world 0: mesh coordinates are world metres
for o in bpy.data.objects: print('K', o.name, len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../episodes/anat_neck/base.blend'))
