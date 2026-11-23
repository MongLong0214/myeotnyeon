"""Clarify exposed dentin, machined edges and the opening field on the audited mesh."""
import json
import math
import runpy
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


spec=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
shot=spec.get('catalog_shot',spec['shot'])
scene=bpy.context.scene
camera=bpy.data.objects[spec['camera']].data

# The source section includes a UV map generated from its two actual fracture
# outlines. Retain that canal, while removing the broad blood bands and radial
# highlights that masked it on the retrieved pieces.
def section_material(mat):
    tree=mat.node_tree
    shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
    coords=tree.nodes.new('ShaderNodeTexCoord')
    grain=tree.nodes.new('ShaderNodeTexNoise')
    tree.links.new(coords.outputs['Object'],grain.inputs['Vector'])
    grain.inputs['Scale'].default_value=3400
    grain.inputs['Detail'].default_value=2
    tint=tree.nodes.new('ShaderNodeValToRGB')
    tint.color_ramp.elements[0].color=(.54,.39,.22,1)
    tint.color_ramp.elements[1].color=(.84,.72,.48,1)
    tree.links.new(grain.outputs['Fac'],tint.inputs[0])
    color=tint.outputs['Color']
    mask=next((n for n in tree.nodes if n.type=='TEX_IMAGE' and n.image and
               n.image.name.startswith('Canal exposed in')),None)
    if mask:
        channel=tree.nodes.new('ShaderNodeSeparateColor')
        tree.links.new(mask.outputs['Color'],channel.inputs[0])
        mix=tree.nodes.new('ShaderNodeMixRGB')
        tree.links.new(channel.outputs['Red'],mix.inputs[0])
        tree.links.new(color,mix.inputs[1])
        mix.inputs[2].default_value=(.068,.025,.014,1)
        color=mix.outputs[0]
    tree.links.new(color,shader.inputs['Base Color'])
    bump=tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.19
    bump.inputs['Distance'].default_value=.000025
    tree.links.new(grain.outputs['Fac'],bump.inputs['Height'])
    tree.links.new(bump.outputs[0],shader.inputs['Normal'])
    for name,value in [('Roughness',.47),('Coat Roughness',.34),('Coat Weight',.10)]:
        socket=shader.inputs[name]
        for link in list(socket.links):
            tree.links.remove(link)
        socket.default_value=value


if shot in ('inject','incise_wisdom'):
    cam=bpy.data.objects[spec['camera']]
    poses=json.loads(Path(spec['audit']).read_text())['frames']
    count=45 if shot=='inject' else 60
    needle=shot=='inject'
    tool=bpy.data.objects['Hollow needle • oblique bevel and lumen' if needle else 'No. 15 blade']
    axis=Vector((.5,.866,1.7) if needle else (.866,-.5,1.7)).normalized()
    molar=bpy.data.objects['Lower second molar tooth.l']
    crown=molar.matrix_world@max(molar.data.vertices,key=lambda v:(molar.matrix_world@v.co).z).co
    poses=poses[spec['start']-1:spec['start']-1+count]
    cam.animation_data_clear()
    camera.animation_data_clear()
    cam.rotation_quaternion=(-axis).to_track_quat('-Z','Y')
    camera.sensor_fit='HORIZONTAL'
    camera.shift_y=0
    camera.dof.use_dof=False
    for i,pose in enumerate(poses):
        frame=pose['source_frame']
        scene.frame_set(math.floor(frame),subframe=frame%1)
        tip=tool.matrix_world.translation
        u=min(1.,i/(count*.75))
        ease=u*u*(3-2*u)
        pan=(.51 if needle else .34)*(1-ease)+.12*ease
        width=(.026 if needle else .021)*(1-ease)+.014*ease
        cam.location=tip.lerp(crown,pan)+axis*.031
        camera.lens=camera.sensor_width*.031/width
        cam.keyframe_insert('location',frame=frame)
        camera.keyframe_insert('lens',frame=frame)
    if shot=='incise_wisdom':
        for name,roughness in [('No. 15 blade',.30),('Ground bevel',.18)]:
            steel=bpy.data.materials.new('Ground surgical steel '+name)
            steel.use_nodes=True
            bs=steel.node_tree.nodes.get('Principled BSDF')
            bs.inputs['Base Color'].default_value=(.48,.51,.53,1)
            bs.inputs['Metallic'].default_value=.93
            bs.inputs['Roughness'].default_value=roughness
            obj=bpy.data.objects[name]
            obj.data.materials.clear()
            obj.data.materials.append(steel)
else:
    bpy.data.objects['Fracture trace • buccal extent of the groove'].visible_camera=False
    for mat in bpy.data.materials:
        if mat.node_tree and mat.name.startswith(('Longitudinal dentin','Dentin • fresh fracture')):
            section_material(mat)
    for obj in scene.objects:
        if obj.name in ('Superior root segment','Inferior root segment','Retrieved superior root segment',
                        'Retrieved inferior root segment','Root','Filler'):
            slots=obj.data.materials
            for face in obj.data.polygons:
                mat=slots[face.material_index]
                if mat and 'dentin' in mat.name.lower():
                    face.use_smooth=False
    if shot=='specimen':
        camera.shift_y+=.28
        # Present one cementum profile beside the other fragment's cut face.
        # Re-seat the static specimen on the gauze after rotating it. The
        # inferior fragment still follows the measured forceps trajectory.
        piece=bpy.data.objects['Retrieved superior root segment']
        rotation=piece.rotation_quaternion.copy()
        tilted=rotation@Quaternion((0,1,0),-.94)
        def seat(q):
            points=[q@v.co for v in piece.data.vertices]
            return Vector(((min(v.x for v in points)+max(v.x for v in points))/2,
                           (min(v.y for v in points)+max(v.y for v in points))/2,
                           min(v.z for v in points)))
        piece.parent.location+=seat(rotation)-seat(tilted)
        piece.rotation_quaternion=tilted

base='archive_scene.py' if shot in ('inject','incise_wisdom') else 'finish_surfaces.py'
runpy.run_path(str(Path(__file__).with_name(base)),run_name='__main__')
if spec['mode']=='audit':
    path=Path(spec['out'])/'geometry.json'
    data=json.loads(path.read_text())
    for row in data['frames']:
        row['can_reuse']=False
    if shot=='specimen':
        from contact import MeshCache, measure
        source=json.loads(Path(spec['audit']).read_text())['frames']
        cache=MeshCache()
        jaws=[obj for obj in scene.objects if obj.name.startswith('Specimen forceps jaw')]
        if len(jaws)!=2:
            raise ValueError('The two specimen forceps jaws are required')
        for row in data['frames']:
            frame=source[row['original']-1]['source_frame']
            scene.frame_set(math.floor(frame),subframe=frame%1)
            graph=bpy.context.evaluated_depsgraph_get()
            target=cache.get(piece,graph,frame)
            for jaw in jaws:
                if jaw.hide_render:
                    continue
                depth,_=measure(cache.get(jaw,graph,frame),target)
                if depth:
                    row['depths'].append([jaw.name,piece.name,round(depth,6)])
    tmp=path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False))
    tmp.replace(path)
