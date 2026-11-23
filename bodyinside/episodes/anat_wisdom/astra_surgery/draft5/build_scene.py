"""Revise the instrument paths in the draft-4 source scene, in surgical-field mm."""
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector as V, Quaternion
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit import BED, O, set_time, FPS, FRAMES
S = bpy.context.scene
ZERO = V((0,0,1.5))
Z = V((0,0,1))

def pose_at(t):
    f=1+20*t
    S.frame_set(math.floor(f),subframe=f%1)

def key(obj, prop, t, value):
    setattr(obj,prop,value)
    obj.keyframe_insert(data_path=prop,frame=1+20*t)

def linear(obj, props):
    action=obj.animation_data.action
    for fc in action.layers[0].strips[0].channelbag(obj.animation_data.action_slot).fcurves:
        if fc.data_path in props:
            for k in fc.keyframe_points:k.interpolation='LINEAR'

def position(obj,t,p):
    key(obj,'location',t,ZERO+V(p)*.001)

def world_verts(obj):
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
    try:
        vs=[(e.matrix_world@v.co-ZERO)*1000 for v in m.vertices]
        tri=[tuple(p.vertices) for p in m.polygons]
        return vs,tri
    finally:e.to_mesh_clear()

def tree(obj):
    return BVHTree.FromPolygons(*world_verts(obj))

def animated_cut(name, target, axis, start, end, times, material, plunge):
    # A convex sweep of the cutting head. The trailing side stays fixed at its
    # entry point while the leading side follows the bur. Each piece retains
    # its own copy in local coordinates once the fragments separate.
    start,end,axis=V(start),V(end),V(axis).normalized()
    q=Z.rotation_difference(axis)
    profile=[(-.049,.13),(.085,.48),(.24,.72),(.47,.89),(.73,.97),(1.02,.97),(1.32,.76),(1.61,.52),(1.85,.414)]
    if plunge:profile=profile[:6]+[(1.5,.97)]
    bm=bmesh.new()
    membership={}
    for tag,tip in enumerate((start,end)):
        for h,r in profile:
            for k in range(32):
                ang=k*math.tau/32
                v=bm.verts.new((tip+q@V((r*math.cos(ang),r*math.sin(ang),h)))*.001)
                membership[v]=tag
    hull=bmesh.ops.convex_hull(bm,input=list(bm.verts))
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    moving=[v.index for v in bm.verts if membership[v]]
    data=bpy.data.meshes.new(name);bm.to_mesh(data);bm.free()
    ob=bpy.data.objects.new(name,data);S.collection.objects.link(ob)
    pose_at(19.20 if target.name!='Buccal cortical bone to be removed' else 13.2)
    ob.parent=target
    ob.matrix_parent_inverse=target.matrix_world.inverted()
    ob.location=ZERO;ob.hide_render=True;ob.display_type='WIRE';ob.hide_set(True)
    ob.data.materials.append(material)
    ob.shape_key_add(name='Head at full depth')
    part=ob.shape_key_add(name='Untravelled feed')
    for i in moving:part.data[i].co-=(end-start)*.001
    for t,frac in times:key(part,'value',t,1-frac)
    linear(ob.data.shape_keys, {part.path_from_id('value')})
    mod=target.modifiers.new(name,'BOOLEAN');mod.object=ob;mod.operation='DIFFERENCE'
    mod.solver='MANIFOLD';mod.double_threshold=.0000001;mod.material_mode='TRANSFER'
    return ob

def drill():
    rig=O['Surgical handpiece']
    axis=V((.72,0,.694)).normalized()
    primary=V((34.6,-35.57,34.1));deep=primary-axis*4.45
    axroot=V((.90,0,.436)).normalized()
    entry=V((34.22,-31.25,33.95));end=entry-axroot*2.70
    bone_axis=V((.84,0,.543)).normalized()
    bone_start=V((35.30,-45.6,35.22));bone_end=V((35.30,-35.40,35.22))
    bone=[(13.18,0),(13.61,.29),(16.45,.85),(17.32,1)]
    main=[(18.85,0),(19.35,.10),(20.70,.44),(22.47,1)]
    split=[(27.03,0),(27.35,.46),(27.75,1)]
    path=[]
    for a,b,d,marks,approach,exit_t in [(bone_start,bone_end,bone_axis,bone,12.95,18.3),
                                          (primary,deep,axis,main,18.48,23.06),
                                          (entry,end,axroot,split,26.95,28.10)]:
        path += [(approach,a+d*10,d)]
        path += [(t,a.lerp(b,f),d) for t,f in marks]
        path += [(exit_t,b+d*13,d)]
    for t,p,d in path:
        position(rig,t,p)
        key(rig,'rotation_quaternion',t,Z.rotation_difference(d)@Quaternion(Z,math.radians(72)))
    # Replace inherited location/rotation curves inside edited intervals.
    keep=[round(1+t*20,3) for t,_,_ in path]
    for fc in rig.animation_data.action.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves:
        if fc.data_path not in ('location','rotation_quaternion'):continue
        for k in list(fc.keyframe_points)[::-1]:
            if k.co.x>200 and round(k.co.x,3) not in keep:fc.keyframe_points.remove(k,fast=True)
        fc.update()
    linear(rig,{'location','rotation_quaternion'})
    cap=O['Buccal cortical bone to be removed'];cap.modifiers.clear()
    O['Filler'].modifiers.clear()
    dentin=bpy.data.materials['Dentin • fresh fracture']
    animated_cut('Buccal milling track',cap,bone_axis,bone_start,bone_end,bone,bpy.data.materials['Arcuate bur marks on the cut cortical trough'],False)
    for n in ['Crown','Root','Filler','Superior root segment','Inferior root segment']:
        animated_cut('Coronal section '+n,O[n],axis,primary,deep,main,dentin,True)
    for n in ['Root','Superior root segment','Inferior root segment']:
        animated_cut('Radicular section '+n,O[n],axroot,entry,end,split,dentin,True)
    # A chip leaves the outside of a flute in its own radial flight direction.
    for obj in rig.children:
        if not obj.name.startswith(('Cut bone chip','Angular milling debris')):continue
        ac=obj.animation_data.action
        curves=list(ac.layers[0].strips[0].channelbag(obj.animation_data.action_slot).fcurves)
        locs=sorted([c for c in curves if c.data_path=='location'],key=lambda c:c.array_index)
        xs,ys=locs[:2];keys=list(xs.keyframe_points)
        for j in range(len(keys)):
            x=xs.keyframe_points[j];y=ys.keyframe_points[j]
            dx,dy=x.co.y,y.co.y
            if math.hypot(dx,dy)<.00001:
                k=min(j+1,len(keys)-1);dx,dy=xs.keyframe_points[k].co.y,ys.keyframe_points[k].co.y
            norm=max(1e-12,math.hypot(dx,dy))
            x.co.y+=.00232*dx/norm;y.co.y+=.00232*dy/norm
        xs.update();ys.update()
    # Keep the spray port's extended steel tube above the shank shoulder.
    O['External saline spray port'].delta_location.z+=.0028

def forceps():
    piece=O['Retrieved inferior root segment']
    pose_at(45.7)
    rot=piece.rotation_quaternion
    vs=[rot@v.co*1000 for v in piece.data.vertices]
    for sign,suffix in [(-1,''),(1,'.001')]:
        arm=O['Specimen forceps articulating arm'+suffix]
        jaw=O['Specimen forceps jaw'+suffix]
        normal=V((sign,0,.48)).normalized()
        contact=max(vs,key=lambda p:p.dot(normal))
        # The inner margin of the pad touches a supporting tangent plane.
        # The arm flares away from the specimen as its section thickens.
        side=V((sign,0,0));tangent=V((-sign*.48,0,1)).normalized()
        profile=[(0,.035,.18),(.65,.14,.26),(3.4,.24,.42),(10,.42,.60),(21,.52,.76)]
        for j,(height,width,half_y) in enumerate(profile):
            centre=normal*(.015+width+.10*height)+tangent*height+V((0,.45*height,0))
            for k,(dx,dy) in enumerate([(-1,-1),(1,-1),(1,1),(-1,1)]):
                jaw.data.vertices[4*j+k].co=(centre+normal*width*dx+V((0,dy*half_y,0)))*.001
        jaw.data.update()
        arm.animation_data_clear()
        for t,spread,rise,back in [(43.5,.75,0,0),(44.05,0,0,0),(45.68,0,0,0),
                                    (45.90,.23,.35,0),(46.28,.42,3.7,-.1),(47.25,.55,24,-4)]:
            key(arm,'location',t,(contact+side*spread+V((0,back,rise)))*.001)
        linear(arm,{'location'})

def passive():
    for n,offset in [('Assistant suction • fenestrated Frazier tip',(3.25,.0,3.55)),
                     ('Periosteal elevator',(0,0,1.15))]:
        O[n].delta_location=V(offset)*.001

def elevator():
    rig=O['Straight elevator'];blade=O['Straight elevator spatula'];stem=O['Straight elevator stem and grip']
    # Narrow working end fits the sectioning instrument's 1.94 mm kerf.
    for v in blade.data.vertices:v.co.x*=.62
    for child in blade.children:child.scale.x*=.62
    axis=V((.72,0,.694)).normalized(); primary=V((34.6,-35.57,34.1))
    from penetration_gate import MeshCache, Surface
    from audit import at
    from mathutils import Matrix
    times=sorted({round(at((f-1)/20)[1],6) for f in range(1,FRAMES+1)} |
                 {i/20 for i in range(461,661)})
    pose_at(23.50)
    home=O['Crown'].matrix_world.copy()
    # Evaluate the two working steel meshes in their own rigid frame once.
    solids=[]
    for part in (blade,stem):
        ev=part.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m=ev.to_mesh();m.calc_loop_triangles()
        pts=np.array([list(v.co*1000) for v in m.vertices])
        tri=np.array([list(face.vertices) for face in m.loop_triangles])
        solids.append((pts,tri))
        ev.to_mesh_clear()
    cache=MeshCache();path=[]
    for t in times:
        if not 23.05<=t<=32.95:continue
        pose_at(t)
        dg=bpy.context.evaluated_depsgraph_get()
        hard=[n for n in ('Crown','Root','Superior root segment','Inferior root segment','Filler',BED)
              if not O[n].hide_render]
        surfaces={n:cache.get(O[n],dg,t) for n in hard}
        if t<27.05:
            n='Crown'
            delta=O[n].matrix_world@home.inverted()
            rotation=delta.to_quaternion()
            d=(rotation@axis).normalized()
            roll=max(0,min(1,(t-23.72)/.65))*18.
            rot=rotation@Z.rotation_difference(axis)@Quaternion(Z,math.radians(roll))
            # Load the coronal wall, then carry that very same kerf with the
            # crown. The steel never needs to pass through its outer enamel.
            reach=np.interp(t,[23.05,23.46,23.7,26.78,27.05],[7,1.5,-2.5,-2.5,6.5])
            centre=delta@(ZERO+(primary+axis*reach)*.001)
            target=np.array(centre*1000)
            direction=np.array(rotation@V((0,-1,0)))
            max_feed=.89*min(1,max(0,(t-23.55)/.20))
            approach=True
        else:
            n='Superior root segment' if t<30.18 else 'Inferior root segment'
            local=V((2.2,-.5,1.10)) if t<30.18 else V((2.,-.33,.0))
            target=np.array((O[n].matrix_world@(local*.001))*1000)
            off=np.interp(t,[27.05,28.00,28.36,29.91,30.12,30.43,32.25,32.95],
                             [11,11,0,0,8,0,0,10])
            target+=np.array([.4*off,0,off])
            tilt=np.interp(t,[28.36,29.09,30.15,30.43,31.16],[0,1,1,0,1])
            shaft=V((.77+.11*tilt,-.10+.10*tilt,.65-.14*tilt)).normalized()
            rot=Z.rotation_difference(shaft)@Quaternion(Z,math.radians(-16+42*tilt))
            direction=np.array([-1.,.055,-.08]);direction/=np.linalg.norm(direction)
            target-=direction*5.
            max_feed=6.9
            approach=False
        matrix=np.array(rot.to_matrix())
        meshes=[(p@matrix.T+target,tri) for p,tri in solids]
        def intersects(dist, lift=0.):
            offset=direction*dist+np.array([0,0,lift])
            for pts,tri in meshes:
                tool=Surface(pts+offset,tri)
                for surf in surfaces.values():
                    if surf is None or np.any(tool.hi<surf.lo) or np.any(tool.lo>surf.hi):continue
                    if tool.tree.overlap(surf.tree):return True
            return False
        # The final pose approaches from free space and stops on the first
        # evaluated steel/anatomy contact, including the unsectioned neighbour.
        lift=0.
        while intersects(0,lift) and lift<5:lift+=.08
        previous=0.;touch=max_feed
        for dist in np.linspace(0,max_feed,8 if approach else 19)[1:]:
            if intersects(dist,lift):
                lo,hi=previous,dist
                for _ in range(10):
                    mid=(lo+hi)*.5
                    if intersects(mid,lift):hi=mid
                    else:lo=mid
                touch=max(0,lo-.014)
                break
            previous=dist
        if not approach and previous==max_feed:
            # On approach/retraction, do not slide sideways looking for a piece.
            touch=5.
        p=V(target+direction*touch+np.array([0,0,lift]))-ZERO*1000
        path.append((t,p,rot))
    rig.animation_data_clear()
    for t,p,rot in path:
        position(rig,t,p)
        key(rig,'rotation_quaternion',t,rot)
    linear(rig,{'location','rotation_quaternion'})

def main():
    drill();forceps();passive();elevator()
    S.render.use_motion_blur=False
    bpy.context.preferences.filepaths.save_version=0
    pose_at(23.82)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'surgery_draft5.blend'),compress=True,relative_remap=True)
if __name__=='__main__':main()
