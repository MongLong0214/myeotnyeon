"""Project persistent surface points. Omit labels when another rendered surface occludes them."""
import json
import math
import sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector as V
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit import set_time, O

# Edited time window, material surface, Korean name, approximate screen point,
# label side. Windows give each term time to be read at phone size.
LABELS=[
    (.60,2.95,'Crown','치관',(.47,.52),'left'),
    (13.15,15.85,'Buccal cortical bone to be removed','피질골',(.56,.50),'right'),
    (17.05,18.48,'ThirdMolar','사랑니',(.57,.48),'right'),
    (19.40,21.73,'Crown','치관',(.51,.47),'right'),
    (25.05,26.65,'Crown','치관',(.51,.49),'right'),
    (28.77,30.37,'Superior root segment','치근',(.53,.48),'right'),
    (32.25,33.84,'Inferior root segment','치근',(.54,.46),'left'),
    (49.0,50.56,'Retrieved inferior root segment','치근',(.51,.56),'right'),
    (51.0,52.62,'Retrieved crown','치관',(.52,.47),'left'),
]

def render_hit(scene,graph,origin,direction):
    for _ in range(100):
        hit,p,_,face,obj,_=scene.ray_cast(graph,origin,direction,distance=.20)
        if not hit:return None,None
        if not obj.hide_render and obj.visible_camera and not obj.name.startswith('FLIP'):
            return obj,p
        origin=p+direction*.000004
    return None,None

def main():
    sc=bpy.context.scene
    records={}
    for start,end,name,label,aim,side in LABELS:
        frames=range(math.ceil(start*20)+1,math.ceil(end*20)+1)
        local=None
        valid=0
        for f in frames:
            shot,_=set_time(f);cam=O['Macro '+shot];dg=bpy.context.evaluated_depsgraph_get()
            obj=O[name];matrix=obj.matrix_world;eye=cam.matrix_world.translation
            if obj.hide_render:continue
            pos=matrix@local if local is not None else None
            if pos is not None:
                first,hit=render_hit(sc,dg,eye,(pos-eye).normalized())
                if first!=obj or (hit-pos).length>.00045:pos=None
            if pos is None:
                # Target an exposed triangle near the intended location. Search in
                # screen pixels, retaining the same local point on successive frames.
                corners=cam.data.view_frame(scene=sc)
                prev=world_to_camera_view(sc,cam,matrix@local) if local is not None else None
                cx,cy=(prev.x,1-prev.y) if prev is not None else aim
                found=False
                for r in (0,14,28,43,61,80,104,128,153):
                    for k in range(1 if r==0 else 14):
                        theta=2*math.pi*k/14
                        x=cx+r*math.cos(theta)/540;y=cy+r*math.sin(theta)/960
                        if not .16<x<.82 or not .31<y<.71:continue
                        v=V((min(c.x for c in corners)+x*(max(c.x for c in corners)-min(c.x for c in corners)),
                             max(c.y for c in corners)-y*(max(c.y for c in corners)-min(c.y for c in corners)),corners[0].z))
                        direction=(cam.matrix_world.to_quaternion()@v).normalized()
                        first,p=render_hit(sc,dg,eye,direction)
                        if first==obj:
                            pos=p;local=matrix.inverted()@p;found=True;break
                    if found:break
            if pos is None:continue
            proj=world_to_camera_view(sc,cam,pos)
            x,y=round(proj.x*540,2),round((1-proj.y)*960,2)
            if not 54<x<472 or not 289<y<712:continue
            records[f]=dict(label=label,side=side,x=x,y=y)
            valid+=1
        print('LABEL',name,start,end,valid,flush=True)
    # A leader should stay attached long enough to read. End the label when
    # reacquiring its surface would make the endpoint jump across the field.
    stable={}
    run=[]
    def keep(window):
        if len(window)<12:return
        for index,f in enumerate(window):
            item=records[f].copy()
            item['opacity']=round(min(1.,(index+1)/4,(len(window)-index)/3),3)
            stable[f]=item
    for f,item in records.items():
        if run:
            last=records[run[-1]]
            if f!=run[-1]+1 or item['label']!=last['label'] or math.hypot(item['x']-last['x'],item['y']-last['y'])>35:
                keep(run)
                run=[]
        run.append(f)
    keep(run)
    records=stable
    (HERE/'label_tracks.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':main()
