"""Fit the removable cortical shelf to the native alveolar bed and bur path."""
import json
import math
import runpy
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
scene=bpy.context.scene
objects=bpy.data.objects
built=False


def smooth(value):
    value=max(0.,min(1.,value))
    return value*value*(3-2*value)


def cortical_shelf(scene,*unused):
    global built
    bpy.app.handlers.frame_change_pre.remove(cortical_shelf)
    cap=objects['Buccal cortical bone to be removed']
    bed=objects['Alveolar bed, cortical rim and contiguous vestibule']
    materials=list(cap.data.materials)
    points=[]
    floor=[]
    grid=[]
    nx,ny=30,46
    # Both surfaces are expressed in the local coordinates of the authored
    # socket and cortex. Their matrix origins are coincident in the source.
    if (cap.matrix_world.translation-bed.matrix_world.translation).length>1e-6:
        raise ValueError('Cortical and socket coordinate systems differ')
    support=BVHTree.FromPolygons([v.co.copy() for v in bed.data.vertices],
                                 [tuple(p.vertices) for p in bed.data.polygons])
    for j in range(ny):
        y=-46.8+15.5*j/(ny-1)
        for i in range(nx):
            x=31.2+7.7*i/(nx-1)
            p,_,_,_=support.ray_cast(Vector((x*.001,y*.001,.080)),Vector((0,0,-1)))
            if p is None:
                raise ValueError(('Missing alveolar support',x,y))
            base=p.z*1000
            lateral=smooth((x-31.2)/2.65)*smooth((38.9-x)/3.45)
            ends=smooth((y+46.8)/2.4)*smooth((-31.3-y)/2.7)
            contour=36.28+.27*math.sin((y+42)*.65)+.13*math.sin(x*2.7+y*1.43)
            thickness=.06+max(0.,contour-base)*lateral*ends
            point=(x*.001,y*.001,(base+thickness-.075)*.001)
            points.append(point)
            floor.append((base-.20)*.001)
            grid.append((x,y,thickness))
    size=len(points)
    points.extend((p[0],p[1],z) for p,z in zip(points[:size],floor,strict=True))
    faces=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i
            quad=(a,a+1,a+nx+1,a+nx)
            faces.extend((quad,tuple(size+k for k in reversed(quad))))
    border=[*range(nx),*(j*nx+nx-1 for j in range(1,ny)),
            *((ny-1)*nx+i for i in range(nx-2,-1,-1)),*(j*nx for j in range(ny-2,0,-1))]
    for a,b in zip(border,border[1:]+border[:1],strict=True):
        faces.append((b,a,a+size,b+size))
    mesh=bpy.data.meshes.new('Cortex continuously fitted to the registered socket')
    mesh.from_pydata(points,[],faces)
    mesh.update()
    cap.data=mesh
    for mat in materials:
        mesh.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth=True
    cap.shape_key_add(name='Buccal cortical shelf')
    # Eight overlapping bands recede sequentially behind the documented bur
    # sweep. Outer cortex stays continuous with the socket after the cut.
    timing=[(0,13.18),(.29,13.61),(.85,16.45),(1,17.32)]
    for band in range(8):
        part=cap.shape_key_add(name=f'Milled cortical window {band+1}')
        for k,(x,y,h) in enumerate(grid):
            lane=max(0.,min(7.,(y+45.6)*7/10.2))
            influence=max(0.,1-abs(lane-band))
            width=smooth((x-31.2)/1.6)*smooth((37.7-x)/1.85)
            part.data[k].co.z-=max(0,h-.075)*.001*influence*width
        phase=band/7
        lo,hi=next((a,b) for a,b in zip(timing,timing[1:]) if a[0]<=phase<=b[0])
        stamp=lo[1]+(phase-lo[0])/(hi[0]-lo[0])*(hi[1]-lo[1])
        for seconds,value in ((stamp+.42,0.),(stamp+.84,1.)):
            part.value=value
            part.keyframe_insert('value',frame=1+20*seconds)
    # The cortex grades into the vascular socket wall. The fine pores and
    # fracture face are in millimetres, independent of camera magnification.
    attribute=mesh.color_attributes.new(name='Cortical coverage',type='FLOAT_COLOR',domain='POINT')
    for i,(_,_,h) in enumerate(grid):
        level=smooth((h-.16)/2.2)
        attribute.data[i].color=(level,level,level,1)
        attribute.data[i+size].color=(0,0,0,1)
    surface=bpy.data.materials.new('Operative cortex and vascular cut margin')
    surface.use_nodes=True
    tree=surface.node_tree
    shader=tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.51
    shader.inputs['Subsurface Weight'].default_value=.085
    shader.inputs['Subsurface Scale'].default_value=.00063
    shader.inputs['Coat Weight'].default_value=.08
    shader.inputs['Coat Roughness'].default_value=.39
    coords=tree.nodes.new('ShaderNodeTexCoord')
    noise=tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=3820
    noise.inputs['Detail'].default_value=3.5
    tree.links.new(coords.outputs['Object'],noise.inputs['Vector'])
    pores=tree.nodes.new('ShaderNodeValToRGB')
    stops=pores.color_ramp.elements
    stops[0].position=.28
    stops[0].color=(.19,.084,.049,1)
    stops[1].position=.70
    stops[1].color=(.72,.54,.36,1)
    tree.links.new(noise.outputs['Fac'],pores.inputs[0])
    tissue=tree.nodes.new('ShaderNodeValToRGB')
    stops=tissue.color_ramp.elements
    stops[0].position=.19
    stops[0].color=(.12,.028,.015,1)
    stops[1].position=.72
    stops[1].color=(.41,.17,.10,1)
    tree.links.new(noise.outputs['Fac'],tissue.inputs[0])
    weight=tree.nodes.new('ShaderNodeVertexColor')
    weight.layer_name=attribute.name
    mix=tree.nodes.new('ShaderNodeMixRGB')
    tree.links.new(weight.outputs['Color'],mix.inputs[0])
    tree.links.new(tissue.outputs['Color'],mix.inputs[1])
    tree.links.new(pores.outputs['Color'],mix.inputs[2])
    tree.links.new(mix.outputs[0],shader.inputs['Base Color'])
    bump=tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.34
    bump.inputs['Distance'].default_value=.00012
    tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    for i in range(len(mesh.materials)):
        mesh.materials[i]=surface
    for modifier in cap.modifiers:
        if modifier.type=='BOOLEAN' and modifier.object is not None:
            for i in range(len(modifier.object.data.materials)):
                modifier.object.data.materials[i]=surface
    built=True


if args['shot'] in ('reflect','drill','suction'):
    bpy.app.handlers.frame_change_pre.append(cortical_shelf)
runpy.run_path(str(Path(__file__).with_name('archive_scene.py')),run_name='__main__')
if args['shot'] in ('reflect','drill','suction') and not built:
    if args['mode']=='audit':
        (Path(args['out'])/'geometry.json').unlink(missing_ok=True)
    raise RuntimeError('The cortical shelf could not be built')

if args['mode']=='audit' and args['shot'] in ('drill','suction'):
    from contact import MeshCache
    cache=MeshCache()
    source=json.loads(Path(args['audit']).read_text())
    output=Path(args['out'])/'geometry.json'
    cells=json.loads(output.read_text())
    tools=[objects[name] for name in source['tools'] if name=='Round cutting bur' or name.startswith('Cutting flute')]
    for row in cells['frames']:
        frame=source['frames'][row['original']-1]['source_frame']
        if 13.18<=(frame-1)/20<=17.32:
            scene.frame_set(math.floor(frame),subframe=frame%1)
            graph=bpy.context.evaluated_depsgraph_get()
            surface=cache.get(objects['Buccal cortical bone to be removed'],graph,frame)
            gaps=[]
            for tool in tools:
                bur=cache.get(tool,graph,frame)
                gaps.append(0. if bur.tree.overlap(surface.tree) else
                            min(surface.tree.find_nearest(p)[3] for p in bur.points.tolist()))
            row['bur_gap_mm']=round(min(gaps),6)
    temp=output.with_suffix('.json.tmp')
    temp.write_text(json.dumps(cells,ensure_ascii=False))
    temp.replace(output)
