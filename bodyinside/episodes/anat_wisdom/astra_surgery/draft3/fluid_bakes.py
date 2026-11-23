"""Bake local Mantaflow FLIP volumes and export their changing topology to Alembic.

Run from the episode directory with Blender in background. The solver is enlarged
100 times for millimetre anatomy. One solver unit therefore represents 10 mm.
The socket and extraction bakes use the registered surgical scene directly.
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('ASTRA_FLIP_WORK', '/tmp/astra3check/bakes'))
DEST = Path(os.environ.get('ASTRA_FLIP_DEST', str(HERE)))
SOURCE = HERE.parent / 'surgery_draft2.blend'
ZERO = Vector((0, 0, 1.5))
V = Vector
PRESETS = {
    # name: local domain centre (mm), dimensions (mm), divisions, bake frames
    'bur': ((0, 0, 2.1), (8.6, 7.4, 7.8), 112, 90),
    'puncture': ((0, 0, .35), (2.5, 2.3, 2.4), 64, 25),
    'margin': ((0, 0, .5), (3.4, 5.4, 2.8), 76, 36),
    'socket': ((0, 0, 3.1), (16.4, 22.0, 21.0), 132, 129),
    'crown': ((0, 0, 4), (10, 10, 15), 100, 31),
    'root1': ((0, 0, 4), (10, 10, 15), 100, 32),
    'root2': ((0, 0, 4), (10, 10, 15), 100, 38),
    'suction': ((0, .4, .24), (3.5, 5.5, 2.6), 76, 55),
}
PULLS = {'crown': ('Crown', (1,1,-3), (31.15,-38.35,28.2), 25.35),
         'root1': ('Superior root segment',(1.5,2.9,-.25),(30.5,-29.30,28.8),28.46),
         'root2': ('Inferior root segment',(1.3,2.8,-1.6),(30.25,-29.6,27.7),30.52)}
SOCKET_ORIGIN = V((30.05, -35.65, 28.0))


def box(name, p, dims):
    bpy.ops.mesh.primitive_cube_add(size=1, location=V(p)*.1)
    ob = bpy.context.object
    ob.name = name
    ob.scale = V(dims)*.1
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def ellipsoid(name, p, radii):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, location=V(p)*.1)
    ob = bpy.context.object
    ob.name = name
    ob.scale = V(radii)*.1
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def fluid(ob, kind):
    mod = ob.modifiers.new(kind.title(), 'FLUID')
    mod.fluid_type = kind
    bpy.context.view_layer.update()
    return getattr(mod, kind.lower()+'_settings')


def flow(ob, behavior, velocity=None, window=None):
    f = fluid(ob, 'FLOW')
    f.flow_type = 'LIQUID'
    f.flow_behavior = behavior
    f.surface_distance = 0
    if velocity is not None:
        f.use_initial_velocity = True
        f.velocity_coord = velocity
    if window:
        for fr, on in window:
            f.use_inflow = on
            f.keyframe_insert(data_path='use_inflow', frame=fr)
    return f


def select_only(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def socket_frame(f):
    # Pre-fill develops slowly before the cannula enters. The wash itself plays 1:1.
    if f <= 42:
        return round(508 + (675-508)*(f-1)/41)
    return 675 + f-42


def register(name, length):
    if name != 'socket' and name not in PULLS:
        return {}
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    s = bpy.context.scene
    if name in PULLS:
        part, local, anchor, start = PULLS[name]
        path = []
        for fr in range(length):
            s.frame_set(round(start*20)+1+fr)
            pos = (s.objects[part].matrix_world @ (V(local)*.001) - ZERO)*1000
            path.append(pos - V(anchor))
        return {'path':path}
    bed = s.objects['Alveolar bed, cortical rim and contiguous vestibule']
    # Use the actual first ten concentric rings including the lateral overflow sill.
    verts = [v.co.copy()*1000-SOCKET_ORIGIN for v in bed.data.vertices[:1280]]
    path = []
    for fr in range(1, length+1):
        s.frame_set(socket_frame(fr))
        mat = s.objects['Blunt irrigation cannula'].matrix_world
        path.append((mat.translation-ZERO)*1000-SOCKET_ORIGIN)
    return {'verts':verts, 'path':path}


def solve(name):
    center, dims, res, length = PRESETS[name]
    if (DEST/(name+'.abc')).is_file():
        return
    reg = register(name, length)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = 20
    s.frame_end = length
    s.gravity = (0, 0, -5.5)
    domain = box('Liquid_'+name, center, dims)
    a = fluid(domain, 'DOMAIN')
    a.domain_type = 'LIQUID'
    a.simulation_method = 'FLIP'
    a.cache_type = 'ALL'
    a.cache_directory = str(CACHE/name)
    a.cache_frame_end = length
    a.resolution_max = res
    a.use_mesh = True
    a.mesh_scale = 2
    a.mesh_particle_radius = 1.65
    a.cache_mesh_format = 'BOBJECT'
    a.timesteps_max = 6
    a.flip_ratio = .91 if name in ('bur','suction') else .83
    a.surface_tension = .40 if name in ('bur','suction') else 1.3
    a.use_diffusion = True
    a.viscosity_base = 1 if name in ('bur','suction') else 4
    a.viscosity_exponent = 6 if name in ('bur','suction') else 4
    for side in ('front','back','right','left','top','bottom'):
        setattr(a,'use_collision_border_'+side,False)
    if name == 'bur':
        # Measured port and contact patch are in handpiece-local coordinates.
        ball=ellipsoid('Milled cortical contact',(-.2,-.12,-1.6),(3.5,3.4,1.84))
        fluid(ball,'EFFECTOR')
        flow(ellipsoid('Crossing spray at port',(2.15,.76,4.65),(.21,.21,.27)),
             'INFLOW',(-1.55,-.56,-3.65))
        flow(ellipsoid('Rotary throw',(.34,.02,.43),(.27,.31,.19)),
             'INFLOW',(-1.15,.70,1.05),[(1,False),(8,True),(16,False),(29,True),(38,False),(57,True),(66,False),(73,True),(79,False)])
    elif name == 'puncture':
        fluid(ellipsoid('Dimpled epithelium',(0,0,-1.65),(2.4,2.5,1.70)),'EFFECTOR')
        flow(ellipsoid('Punctured capillary',(0,0,.14),(.14,.14,.12)),'INFLOW',(0,0,.29),[(1,True),(10,False)])
    elif name == 'margin':
        slab=box('Cut mucosal edge',(0,0,-.70),(2.45,5.85,1.45))
        slab.rotation_euler=(.10,-.21,.08)
        fluid(slab,'EFFECTOR')
        for k,(x,y) in enumerate([(-.64,-1.14),(-.79,.55),(-.61,1.49)]):
            flow(ellipsoid('Capillary', (x,y,.25),(.16,.21,.15)),'INFLOW',
                 (-.18,.14,.13),[(1,k==0),(3+k*3,True),(14+k*3,False)])
    elif name == 'suction':
        floor=box('Trough floor',(0,0,-.53),(5.9,7.8,1))
        floor.rotation_euler.x=.14
        fluid(floor,'EFFECTOR')
        flow(ellipsoid('Effluent on cortex',(.10,1.85,.30),(.31,.31,.21)),'INFLOW',(-.06,-1.25,-.02))
        flow(ellipsoid('Aspiration lumen',(0,-.23,.22),(.62,.59,.50)),'OUTFLOW')
    elif name == 'socket':
        verts=reg['verts']
        n=128
        # Seal the floor hole and extend the measured shell downward for a closed collider.
        bottom=[V((p.x,p.y,-11)) for p in verts[-n:]]
        faces=[tuple(range(n))]
        for j in range(9):
            faces.extend((j*n+i,(j+1)*n+i,(j+1)*n+(i+1)%n,j*n+(i+1)%n) for i in range(n))
        faces.extend((9*n+i,10*n+i,10*n+(i+1)%n,9*n+(i+1)%n) for i in range(n))
        faces.append(tuple(reversed(range(10*n,11*n))))
        me=bpy.data.meshes.new('Measured alveolus');me.from_pydata([p*.1 for p in verts+bottom],[],faces)
        ob=bpy.data.objects.new('Socket wall',me);s.collection.objects.link(ob);fluid(ob,'EFFECTOR')
        # The teaching window cuts away part of the buccal socket floor.
        # Seal it for fluid collisions, underneath the visible cut-bone wall.
        plug=box('Floor below canal teaching window',(0,0,-3.25),(15.7,21.25,3.18))
        fluid(plug,'EFFECTOR')
        flow(ellipsoid('Initial blood in floor',(0,-.15,-.51),(3.90,6.05,1.19)),'GEOMETRY')
        # Low, wide seeps sit beneath the pooled surface, where blood enters
        # from cancellous bone. Exposed spherical source volumes imprint the mesh.
        for x,y,z in [(-2.02,-.72,-.99),(1.53,2.33,-.97)]:
            flow(ellipsoid('Submerged cancellous seep',(x,y,z),(.85,1.02,.22)),
                 'INFLOW',(.07,-.06,.21))
        jet=ellipsoid('Moving cannula',reg['path'][0],(.255,.255,.34))
        for i,p in enumerate(reg['path'],1):
            jet.location=p*.1;jet.keyframe_insert(data_path='location',frame=i)
        flow(jet,'INFLOW',(-.42,.52,-4.15),[(1,False),(47,True),(93,False)])
        flow(ellipsoid('Washout at lateral margin',(3.85,.0,.18),(1.0,1.65,.60)),
             'OUTFLOW',window=[(1,False),(59,True),(94,False)])
    else:
        start=reg['path'][0]
        end=reg['path'][-1]
        # The mobile contact holds a wet patch. The socket end replenishes it
        # briefly as the actual tooth moves away, until the neck pinches off.
        contact=ellipsoid('Adhering liquid on segment',start,(.68,.53,.48))
        for i,p in enumerate(reg['path'],1):
            contact.location=p*.1
            contact.keyframe_insert(data_path='location',frame=i)
        flow(contact,'INFLOW',window=[(1,True),(length-7,False)])
        distance=start.length
        column=ellipsoid('Initial periodontal film',start*.5,(.44,.33,max(.38,distance*.54)))
        if distance>.01:
            column.rotation_euler=V((0,0,1)).rotation_difference(start.normalized()).to_euler()
        flow(column,'GEOMETRY')
        fluid(ellipsoid('Socket wall at attachment',(0,0,-1.46),(2.6,2.6,1.55)),'EFFECTOR')
        flow(ellipsoid('Wet anchor',(0,0,.22),(.46,.33,.20)),'INFLOW',window=[(1,True),(9,False)])
    select_only(domain)
    s.frame_set(1)
    CACHE.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(CACHE/(name+'.blend')))
    print('BAKING',name,res,length,flush=True)
    if 'FINISHED' not in bpy.ops.fluid.bake_all():
        raise RuntimeError('Bake failed for '+name)
    counts=[]
    for fr in (2,length//2,length-1):
        s.frame_set(fr)
        counts.append(len(domain.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices))
    if max(counts)<30:
        raise RuntimeError(f'Empty {name} mesh {counts}')
    DEST.mkdir(parents=True,exist_ok=True)
    destination=DEST/(name+'.partial.abc')
    bpy.ops.wm.alembic_export(filepath=str(destination),start=1,end=length,selected=True,
                              as_background_job=False,flatten=True,uvs=False,normals=False,
                              export_particles=False,export_hair=False,face_sets=False)
    destination.rename(DEST/(name+'.abc'))
    print('FINISHED',name,counts,flush=True)


if __name__=='__main__':
    for effect in sys.argv[sys.argv.index('--')+1:] or PRESETS:
        solve(effect)
