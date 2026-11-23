"""Finish placement, retain machined specimen faces and clear newly detached chips."""
import json
import itertools
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector as V
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_scene import O,S,ZERO,pose_at,key,linear
from audit import set_time,BED,DEBRIS
from penetration_gate import MeshCache,Surface,measure

def specimen():
    # Copy the finished evaluated geometry back into the cutaway's local space.
    pose_at(32.46)
    dg=bpy.context.evaluated_depsgraph_get()
    for name in ('Crown','Superior root segment','Inferior root segment'):
        mesh=bpy.data.meshes.new_from_object(O[name].evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
        mesh.name='Machined specimen '+name
        O['Retrieved '+name.lower()].data=mesh
    holder=O['Specimen placement Inferior root segment'];pose_at(44.1)
    for prop in ('location','rotation_euler'):
        key(holder,prop,44.40,getattr(holder,prop).copy())
    for sign,suffix in [(-1,''),(1,'.001')]:
        arm=O['Specimen forceps articulating arm'+suffix];pose_at(44.6)
        contact=arm.location.copy()
        key(arm,'location',44.10,contact+V((sign*.70,0,.12))*.001)
        key(arm,'location',44.39,contact)
        linear(arm,{'location'})

def tool_clearance():
    # A shallower pass leaves intact cortex beyond the swept cutting envelope.
    rig=O['Surgical handpiece']
    shift=V((.84,0,.543)).normalized()*.00047
    O['Buccal milling track'].location+=shift
    for t,delta in [(12.8,V()),(13.15,shift),(18.35,shift),(18.65,V()),
                     (26.82,V()),(26.97,V((0,0,.00014))),(28.12,V((0,0,.00014))),(28.26,V())]:
        key(rig,'delta_location',t,delta)
    for ob in O:
        if ob.name.startswith('Radicular section '):ob.location.z+=.00014
    O['Periosteal elevator'].delta_location.z+=.00013
    # Position the external spray lip and its outgoing jet together.
    port=O['External saline spray port']
    port.delta_location.z=0
    linear(rig,{'delta_location'})

def inferior_purchase():
    from mathutils import Quaternion
    from audit import at
    from build_scene import Z
    rig=O['Straight elevator'];cache=MeshCache()
    target=O['Inferior root segment'];parts=[]
    for name in ('Straight elevator spatula','Straight elevator stem and grip'):
        ev=O[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        m=ev.to_mesh();m.calc_loop_triangles()
        parts.append((np.array([v.co[:] for v in m.vertices])*1000,
                      np.array([p.vertices[:] for p in m.loop_triangles])))
        ev.to_mesh_clear()
    times=sorted({round(at((f-1)/20)[1],6) for f in range(1,1054)} |
                 {f/20 for f in range(603,661)})
    for t in times:
        if not 30.18<=t<=32.95:continue
        pose_at(t);dg=bpy.context.evaluated_depsgraph_get()
        tooth=cache.get(target,dg,t);bed=cache.get(O[BED],dg,t)
        # The occlusal approach clears the buccal wall of the deep fragment.
        # Swing outward until the shank bears on the cortical lip.
        centre=target.matrix_world@V((.00165,-.00037,0))
        start=np.array(centre*1000)+[0,0,9]
        tilt=np.interp(t,[30.18,30.43,30.72,31.15,32.95],[.45,.50,.70,.84,.85])
        for slope in np.linspace(tilt,.13,7):
            shaft=V((slope,.04,1)).normalized()
            rot=Z.rotation_difference(shaft)@Quaternion(Z,np.interp(t,[30.40,31.21],[-.28,.64]))
            rotated=[(p@np.array(rot.to_matrix()).T+start,tri) for p,tri in parts]
            def hit(depth):
                steel=[Surface(pts-[0,0,depth],tri) for pts,tri in rotated]
                for name,surf in [('bed',bed),('tooth',tooth)]:
                    if any(np.all(k.lo<=surf.hi) and np.all(k.hi>=surf.lo) and k.tree.overlap(surf.tree) for k in steel):return name
                return None
            lo=0
            for hi in np.arange(.5,15,.5):
                if hit(hi):break
                lo=hi
            for _ in range(12):
                mid=(lo+hi)*.5
                if hit(mid):hi=mid
                else:lo=mid
            if hit(hi)=='tooth':break
        rise=float(np.interp(t,[30.18,30.42,32.25,32.95],[8,0,0,10]))
        key(rig,'location',t,V(start-[0,0,lo-.016-rise])*.001)
        key(rig,'rotation_quaternion',t,rot)
    linear(rig,{'location','rotation_quaternion'})

def particles(report):
    cache=MeshCache()
    frames=report['frames'];times=sorted({round(r['source_frame'],5) for r in frames})
    affected={}
    for row in frames:
        for _,j,d,count in row['hits']:
            name=report['targets'][j]
            if name.startswith(DEBRIS):
                affected.setdefault(name,{})[round(row['source_frame'],5)]=row
    for n,rows in affected.items():
        part=O[n];keys={}
        anim=part.animation_data
        curves=anim.action.layers[0].strips[0].channelbag(anim.action_slot).fcurves
        delta_curves={f.array_index:f for f in curves if f.data_path=='delta_location'}
        previous={src:V([delta_curves[i].evaluate(src) if i in delta_curves else 0. for i in range(3)]) for src in times}
        for src,row in sorted(rows.items()):
            set_time(row['f'])
            dg=bpy.context.evaluated_depsgraph_get()
            chip=cache.get(part,dg,src)
            tools=[cache.get(O[report['tools'][i]],dg,src) for i in row['tools']]
            relevant=[tool for tool in tools if tool is not None and
                      np.all(chip.hi+3>tool.lo) and np.all(tool.hi+3>chip.lo)]
            if part.parent:
                p=part.location*1000;angle=np.arctan2(p.y,p.x)
                rb=part.parent.matrix_world.to_quaternion()
                dirs=[rb@V((np.cos(angle+offset),np.sin(angle+offset),z)).normalized()
                      for z in (.12,.60,-.23) for offset in (0,.55,-.55,1.12,-1.12,2.1,-2.1)]
            else:
                dirs=[V((x,y,z)).normalized() for x,y,z in
                      [(0,-1,.4),(.5,-1,.2),(-.5,-1,.2),(0,1,.5),(1,0,.4),(0,0,1)]]
            for length,direction in itertools.product((.065,.14,.25,.42,.63,.88,1.20,1.65,2.25,3.1),dirs):
                offset=np.array(direction)*length
                test=Surface(chip.points+offset,chip.faces)
                if any((lambda result: result[0]>.0001 or result[1]>0)(measure(tool,test)) for tool in relevant):
                    continue
                dp=V(offset)*.001
                if part.parent:dp=part.parent.matrix_world.inverted().to_3x3()@dp
                keys[src]=dp
                break
            else:raise ValueError(('Chip path has no free exit',n,src))
        for i,src in enumerate(times):
            if src in keys or (i and times[i-1] in keys) or (i+1<len(times) and times[i+1] in keys):
                key(part,'delta_location',(src-1)/20,previous[src]+keys.get(src,V((0,0,0))))
        if keys:linear(part,{'delta_location'})

def return_around_fragment():
    # Swing around the delivered superior root while approaching the last
    # fragment. Receiver and departing specimen occupy different sides of the arc.
    rig=O['Straight elevator']
    for t,dy in [(30.05,0),(30.14,-2.0),(30.19,-4.9),(30.29,-4.9),(30.36,-2.0),(30.43,0)]:
        key(rig,'delta_location',t,V((0,dy,0))*.001)
    linear(rig,{'delta_location'})

def main():
    import os
    report=json.loads(Path(os.environ['INPUT_AUDIT']).read_text())
    if not os.getenv('CHIPS_ONLY'):
        tool_clearance();inferior_purchase();specimen()
    if os.getenv('CHIPS_ONLY'):
        return_around_fragment()
    particles(report)
    pose_at(23.8)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'surgery_draft5.blend'),compress=True,relative_remap=True)
if __name__=='__main__':main()
