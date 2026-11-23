"""Keep the kerf in view while the handpiece and elevator carry load."""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Quaternion,Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_scene import pose_at,key,linear
from audit import O

def turn_lens(name,degrees,times,widen=1.04):
    cam=O['Macro '+name]
    values=[]
    for t in times:
        pose_at(t)
        rot=cam.rotation_quaternion.copy()
        focus=cam.data.dof.focus_distance
        target=cam.location+rot@Vector((0,0,-focus))
        zrot=Quaternion((0,0,1),math.radians(degrees(t) if callable(degrees) else degrees))
        values.append((t,target+zrot@(cam.location-target)*widen,zrot@rot,focus*widen,
                       max(50.,cam.data.dof.aperture_fstop)))
    for block,props in ((cam,{'location','rotation_quaternion'}),(cam.data,{'dof.focus_distance','dof.aperture_fstop'})):
        anim=block.animation_data;bag=anim.action.layers[0].strips[0].channelbag(anim.action_slot)
        for fc in list(bag.fcurves):
            if fc.data_path in props:bag.fcurves.remove(fc)
    for t,loc,rotation,focus,fstop in values:
        key(cam,'location',t,loc);key(cam,'rotation_quaternion',t,rotation)
        cam.data.dof.focus_distance=focus;cam.data.dof.aperture_fstop=fstop
        cam.data.keyframe_insert(data_path='dof.focus_distance',frame=1+20*t)
        cam.data.keyframe_insert(data_path='dof.aperture_fstop',frame=1+20*t)
    linear(cam,{'location','rotation_quaternion'})

def main():
    import os
    angle=float(os.getenv('SURG_VIEW','32'))
    turn_lens('fracture',angle,[23.52,24.58])
    turn_lens('section',angle,[19.2,22.6,24.89])
    turn_lens('osteotomy',angle*.72,[13.47,15.5,16.46])
    turn_lens('aspiration',angle*.4,[16.46,18.06])
    turn_lens('delivery',lambda t: (angle if t>=30.32 else angle*.50 if 26.62<=t<=28.55 else 0),
              [24.89,25.94,26.22,26.62,27.65,28.57,29.21,29.52,29.77,30.32,30.52,31.42,32.02,32.84])
    if os.getenv('SAVE_LENSES'):
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'surgery_draft5.blend'),compress=True)
if __name__=='__main__':main()
