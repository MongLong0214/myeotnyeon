"""Quantify tooth purchase, bone support and release on the evaluated working surfaces."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit import O, BED, set_time
from penetration_gate import MeshCache,use_render_modifiers

def surface_gap(a,b):
    if a.tree.overlap(b.tree):return 0.
    nearest=min(b.tree.find_nearest(p)[3] for p in a.points.tolist())
    margin=nearest+.001
    within=b.points[((b.points>=a.lo-margin)&(b.points<=a.hi+margin)).all(axis=1)]
    return min([nearest]+[a.tree.find_nearest(p)[3] for p in within.tolist()])

def main():
    sets=[('fracture_crown',8,64,'Crown'),('elevate_crown',495,529,'Crown'),
          ('elevate_first_root',565,610,'Superior root segment'),('elevate_last_root',637,675,'Inferior root segment')]
    rows={};cache=MeshCache()
    use_render_modifiers([O[BED]])
    for label,f0,f1,target in sets:
        checks=[]
        for f in range(f0,f1+1):
            _,src=set_time(f);dg=bpy.context.evaluated_depsgraph_get()
            a,b,bed=[cache.get(O[n],dg,src) for n in ['Straight elevator spatula',target,BED]]
            checks.append([f,round(surface_gap(a,b),4),round(surface_gap(a,bed),4)])
        rows[label]={'columns':['frame','blade_to_piece_gap_mm','blade_to_bone_gap_mm'],'samples':checks,
                     'closest_simultaneous_bearing':min(checks,key=lambda r:max(r[1:]))}
    jaws=['Specimen forceps jaw','Specimen forceps jaw.001']
    samples=[];ref=None;drift=0.
    for f in range(974,1024):
        _,src=set_time(f);dg=bpy.context.evaluated_depsgraph_get()
        piece=O['Retrieved inferior root segment']
        surf=cache.get(piece,dg,src)
        gaps=[surface_gap(cache.get(O[n],dg,src),surf) for n in jaws]
        samples.append([f,*[round(v,4) for v in gaps]])
        if 981<=f<=1005:
            origins=np.array([list(piece.matrix_world.inverted()@O[n].matrix_world.translation) for n in jaws])*1000
            if ref is None:ref=origins
            drift=max(drift,float(np.max(np.linalg.norm(origins-ref,axis=1))))
    rows['forceps']={'columns':['frame','left_gap_mm','right_gap_mm'],'samples':samples,
                     'held_frames':[981,1005],'max_relative_jaw_origin_drift_mm':round(drift,5)}
    (HERE/'contact_checks.json').write_text(json.dumps(rows,separators=(',',':')))
if __name__=='__main__':main()
