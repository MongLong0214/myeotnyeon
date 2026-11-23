"""Audit every instrument component against the render-visible mineralized geometry."""
import json
import math
import os
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
sys.path[:0] = [str(HERE.parent/'draft4'), str(EP.parents[1]/'anat_kit/gates')]
from edit import at, FPS, FRAMES
from penetration_gate import MeshCache, measure, use_render_modifiers

O = bpy.data.objects
BED = 'Alveolar bed, cortical rim and contiguous vestibule'
RIGS = ['Surgical handpiece','Aspirating dental syringe','No. 15 scalpel','Periosteal elevator',
        'Straight elevator','Blunt irrigation cannula','Suture needle pivot','Needle holder',
        'Iris scissors · trim pivot','Assistant • buccal retraction','Assistant suction • fenestrated Frazier tip',
        'Specimen forceps articulating arm','Specimen forceps articulating arm.001']
DEBRIS = ('Cut bone chip','Angular milling debris','Dentin splinter at fracture')
HARD = ['Mandible','ThirdMolar','Crown','Root','Filler','Superior root segment','Inferior root segment',
        'Buccal cortical bone to be removed','Cutaway lip at the opening bur contact','RimOut','RimRam',
        'M2Septum','CanalPlug',BED]
TOOLS = sorted({c.name for n in RIGS for c in O[n].children_recursive if c.type in ('MESH','CURVE')
                and not c.name.startswith(DEBRIS+('FLIP','Wetted cutting edge'))})
TARGETS = sorted(set(HARD)|{o.name for o in O if o.name.startswith(DEBRIS+('Lower first molar','Lower second molar','Lower second premolar','Rough buccal bone','Retrieved ')) and o.type=='MESH'})

def set_time(frame):
    shot,t = at((frame-1)/FPS)
    src = 1+t*FPS
    bpy.context.scene.frame_set(math.floor(src),subframe=src%1)
    return shot,src

def main():
    use_render_modifiers([O[n] for n in TOOLS+TARGETS])
    cache = MeshCache()
    out = Path(os.environ['AUDIT_OUT'])
    result = dict(tools=TOOLS,targets=TARGETS,threshold_mm=.2,frames=[])
    # Repeated detached-table geometry (also present off camera) has identical poses.
    memo = {}
    if os.getenv('FRAME_LIST'):
        frames=sorted({int(n) for n in os.environ['FRAME_LIST'].split(',')})
    else:
        frames=range(int(os.getenv('FIRST','1')),int(os.getenv('LAST',str(FRAMES)))+1,int(os.getenv('STRIDE','1')))
    for f in frames:
        shot,src = set_time(f)
        graph = bpy.context.evaluated_depsgraph_get()
        tools = [i for i,n in enumerate(TOOLS) if not O[n].hide_render]
        targets = [j for j,n in enumerate(TARGETS) if not O[n].hide_render]
        active = {n:cache.get(O[n],graph,src) for n in [*(TOOLS[i] for i in tools),*(TARGETS[j] for j in targets)]}
        empty=[n for n,surface in active.items() if surface is None]
        # Draft 4's final osteotomy frame has consumed the entire cortical cap.
        # Its hide flag remains on for that pose, but there is no material to hit.
        unexpected=[n for n in empty if n!='Buccal cortical bone to be removed']
        if unexpected:raise ValueError((f,'Empty evaluated render geometry',unexpected))
        hits = []
        for i in tools:
            for j in targets:
                a,b = active[TOOLS[i]],active[TARGETS[j]]
                record = memo.get((i,j))
                if record and record[0] is a and record[1] is b:
                    depth,count = record[2:]
                else:
                    depth,count = measure(a,b,sheet=TARGETS[j]==BED)
                    memo[i,j] = (a,b,depth,count)
                if depth or count:
                    hits.append([i,j,round(depth,5),count])
        result['frames'].append(dict(f=f,source_frame=round(src,6),shot=shot,tools=tools,targets=targets,hits=hits))
        if empty:result['frames'][-1]['empty_meshes']=empty
        if f%25==1 or os.getenv('STRIDE'):
            print('AUDIT',f,shot,max([h[2] for h in hits]+[0]),flush=True)
            out.with_suffix('.progress').write_text(json.dumps(result,separators=(',',':')))
    result['ok'] = not any(h[2]>.2 for fr in result['frames'] for h in fr['hits'])
    out.write_text(json.dumps(result,separators=(',',':')))
    if os.getenv('ENFORCE') and not result['ok']:
        raise RuntimeError('Instrument depth exceeds 0.2 mm')
if __name__=='__main__':
    main()
