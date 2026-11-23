import os
# Episode build template. Copy to episodes/<id>/build.py, fill the marked parts, run:
#   blender -b --factory-startup -P build.py
# It must leave <id>.blend with: one camera (CameraPath), named meshes used by episode.json geometry_gates,
# film-transparent RGBA band render at episode.json render.res.
import sys, os, math, json
sys.path.insert(0, os.path.join(os.environ['ANAT_KIT'],'blender'))
import bpy
from kit import *
HERE = os.environ['ANAT_EPISODE']; EP = json.load(open(HERE + '/episode.json'))
sc = bpy.context.scene; sc.render.fps = EP['fps']; sc.frame_start = 0; sc.frame_end = round(EP['fps'] * EP['duration']) - 1
# Open the approved DBCLS solids as base_blend; name the structures the shot needs.
bones = [bpy.data.objects[n] for n in ('Vertebra C3', 'Vertebra C4')]
# 2. MATERIALS: frosted_bone (translucent), enamel, gum_material, metal; ONE highlight hue = HIGHLIGHT
mB, gB, eB = frosted_bone('Bone')
for o in bones: setmat(o, mB)
# 3. ACTIONS (key with vkey/kloc/krot/vis/pulse). Highlight exactly one structure.
# 4. CAMERA: one continuous move, no cuts unless declared in episode.json scene_cuts_declared
cam = CameraPath(lens=55, fstop=8, roll_deg=0)
center = sum((o.matrix_world.translation for o in bones), Vector()) / max(1, len(bones))
cam.key(0, center, (1, -0.1, 0.1), 0.12); cam.key(sc.frame_end + 1, center, (1, -0.05, 0.08), 0.08)
# 5. LIGHT + RENDER
light_rig(center); render_settings(*EP['render']['res'], spp=EP['render']['spp'], blur=0)
bpy.ops.wm.save_as_mainfile(filepath=HERE + '/' + EP['id'] + '.blend'); print('SAVED')
