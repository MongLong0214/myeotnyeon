"""Evaluate the registered surgery plates on the published draft-5 pose clock."""
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector as V

sys.path.insert(0,str(Path(__file__).resolve().parent))
from contact import MeshCache, measure, use_render_modifiers

args=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
out=Path(args['out'])
scene=bpy.context.scene
objects=bpy.data.objects
bed=objects['Alveolar bed, cortical rim and contiguous vestibule']
cap=objects['Buccal cortical bone to be removed']
hidden=['Mandible','RimOut','RimRam','M2Septum','GumLayer','CanalPlug']
if args['shot'] in ('elevate','deliver_root'):
    hidden.append('Nerve2')
original_visibility={name:objects[name].hide_render for name in hidden if objects.get(name)}
archive=json.loads(Path(args['audit']).read_text())
shot=args['shot']
alter_bone=shot in ('drill','suction','reflect')
cache=MeshCache()
# The authored radially sampled socket is independent of the inherited cut jaw.
# Join the underside of the cortical cover to its rim, preserving the animated
# swept cutter on the working face. Every altered hard-tissue pair is remeasured.
if alter_bone:
    for v in cap.data.vertices:
        x,y,z=v.co
        weight=max(0,min(1,(.0351-z)/.0025))
        if weight:
            hit, p, _, _=bed.ray_cast(V((x,y,.080)),V((0,0,-1)))
            if hit:
                v.co.z=min(z,z+weight*(p.z-.00035-z))
    cap.data.update()

# Use the real tool material and retain legible focus on the working tip.
cam=objects[args['camera']]
scene.camera=cam
scene.render.engine='CYCLES'
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.render.use_persistent_data=True
scene.render.resolution_x,scene.render.resolution_y=360,640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.refresh_devices()
if any(d.type=='METAL' for d in prefs.devices):
    for d in prefs.devices:
        d.use=d.type=='METAL'
    scene.cycles.device='GPU'
targets=[objects[n] for n in archive['targets']]
tools=[objects[n] for n in archive['tools']]
use_render_modifiers(tools+targets)
rows=[]
proofs=[]
for f in args['frames']:
    original=args['start']+f
    measured=archive['frames'][original-1]
    if measured['frame']!=original:
        raise ValueError('Archive frame index mismatch')
    src=measured['source_frame']
    for name,was_hidden in original_visibility.items():
        objects[name].hide_render=was_hidden
    scene.frame_set(math.floor(src),subframe=src%1)
    changed=alter_bone or shot in ('drill','suction','irrigate','incise_wisdom','elevate','deliver_root')
    for name in hidden:
        obj=objects.get(name)
        if obj:
            changed |= not obj.hide_render
            obj.hide_render=True
    # The broad detached effect on the lower lip does not represent socket fluid.
    if shot in ('elevate','deliver_root'):
        for obj in scene.objects:
            if obj.name.startswith(('FLIP root','FLIP crown','Impact droplets','Saliva filament')):
                obj.hide_render=True
    if shot in ('drill','suction','irrigate','incise_wisdom'):
        cam.data.dof.aperture_fstop=max(cam.data.dof.aperture_fstop,90)
    bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    if args['mode']=='audit':
        hard=[j for j in measured['targets'] if not targets[j].hide_render]
        hits=[[archive['tools'][i],archive['targets'][j],depth] for i,j,depth,_ in measured['draft5_hits']
              if j in hard and not (alter_bone and targets[j]==cap)]
        if alter_bone and not cap.hide_render:
            c=cache.get(cap,graph,src)
            for i in measured['tools']:
                tool=tools[i]
                if not tool.hide_render:
                    depth,_=measure(cache.get(tool,graph,src),c)
                    if depth: hits.append([tool.name,cap.name,round(depth,6)])
        # Only project enamel triangles on the camera-facing crown. Some cut
        # faces belong to this very object; object identity alone is insufficient.
        label=None
        if shot in ('fracture','section','elevate','specimen'):
            crown=objects['Retrieved crown' if shot=='specimen' else 'Crown']
            if not crown.hide_render:
                corners=cam.data.view_frame(scene=scene)
                xmin,xmax=min(v.x for v in corners),max(v.x for v in corners)
                ymin,ymax=min(v.y for v in corners),max(v.y for v in corners)
                for dx,dy in [(0,0),(-.06,-.04),(-.12,-.04),(-.16,-.08),(.08,-.04),(.12,.06),(0,-.12)]:
                    sx,sy=.45+dx,.48+dy
                    axis=V((xmin+sx*(xmax-xmin),ymax-sy*(ymax-ymin),corners[0].z))
                    ray=cam.matrix_world.to_quaternion()@axis.normalized()
                    eye=cam.matrix_world.translation
                    for _ in range(32):
                        ok,p,_,face,obj,_=scene.ray_cast(graph,eye,ray,distance=.4)
                        if not ok:break
                        if obj.hide_render or not obj.visible_camera:
                            eye=p+ray*.000004
                            continue
                        if obj==crown:
                            ev=crown.evaluated_get(graph)
                            mat=ev.data.materials[ev.data.polygons[face].material_index]
                            if mat and 'enamel' in mat.name.lower() and 'sectioned' not in mat.name.lower():
                                label=dict(label='치관',side='left',x=round(sx*540,2),y=round(sy*960,2))
                        break
                    if label:break
        rows.append(dict(f=f,original=original,can_reuse=not changed,depths=hits,gaps=[],tissue_gap=None,leader=label))
    else:
        scene.render.filepath=str(out/f'working-{f}.png')
        bpy.ops.render.render(write_still=True)
        Path(scene.render.filepath).replace(out/f'{f:04}.png')
if args['mode']=='audit':
    (out/'geometry.json.tmp').write_text(json.dumps(dict(frames=rows,excluded=hidden,pose_report=args['audit'])))
    (out/'geometry.json.tmp').replace(out/'geometry.json')
