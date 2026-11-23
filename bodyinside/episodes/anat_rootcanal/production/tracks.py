"""Project the fitted dam, moving file and descending crown from the saved scene."""
from pathlib import Path
import json
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ep=Path(__file__).resolve().parent.parent
scene=bpy.context.scene
path=ep/'production/.cache/anchors.json'
anchors=json.loads(path.read_text())
dam=scene.objects['Fenestrated green rubber dam • section']
tool=scene.objects['Hand K-file • mesial buccal']
crown=scene.objects['Ceramic crown in section']
def pick_surface_point(obj, frame, pixel):
    scene.frame_set(frame)
    cam=scene.camera
    candidates=[]
    for vertex in obj.data.vertices:
        world=obj.matrix_world@vertex.co
        uv=world_to_camera_view(scene,cam,world)
        distance=(540*uv.x-pixel[0])**2+(960*(1-uv.y)-pixel[1])**2
        candidates.append((distance,vertex.index,world))
    deps=bpy.context.evaluated_depsgraph_get()
    origin=cam.matrix_world.translation
    for _,index,point in sorted(candidates,key=lambda row:row[0]):
        hit,position,_,_,front,_=scene.ray_cast(deps,origin,(point-origin).normalized())
        if hit and front.original==obj:
            return obj.matrix_world.inverted()@position
    raise ValueError(f'No visible attachment on {obj.name}')
dam_point=pick_surface_point(dam,156,(217,300))
crown_point=pick_surface_point(crown,785,(475,553))
for number,record in anchors.items():
    f=int(number)
    scene.frame_set(f)
    label=record['label']
    if label=='러버댐':
        # Far edge of the stretched membrane on the screen-left side.
        pt=dam.matrix_world@dam_point
        record['side']='right'
    elif label=='근관 파일':
        live=tool.evaluated_get(bpy.context.evaluated_depsgraph_get())
        pt=live.matrix_world@live.data.vertices[22*12+9].co
    elif label=='다음 내원':
        pt=crown.matrix_world@crown_point
    else:
        continue
    v=world_to_camera_view(scene,scene.camera,pt)
    record.update(x=round(540*v.x,2),y=round(960*(1-v.y),2))
path.write_text(json.dumps(anchors,ensure_ascii=False))
for label in {v['label'] for v in anchors.values()}:
    values=[v for v in anchors.values() if v['label']==label]
    print(label, [(min(v[k] for v in values),max(v[k] for v in values)) for k in ('x','y')])
