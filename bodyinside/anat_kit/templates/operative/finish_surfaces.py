"""Retain matching root surfaces across the lift and tray, and settle the suture."""
import json
import math
import runpy
import sys
from pathlib import Path

import bpy

args=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
shot=args.get('catalog_shot',args['shot'])
scene=bpy.context.scene
support=None
if shot in ('fracture','reflect','drill','suction','section','separate','elevate',
            'divide_roots','deliver_first_root','deliver_root','irrigate'):
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from alveolar_support import fit_ridge, audit_ridge
    support=fit_ridge()

if shot in ('drill','suction','section','divide_roots'):
    # The head and its six flutes share a carbide finish. This preserves the
    # measured cutting envelope and prevents the dark flutes reading as wires.
    cutter=bpy.data.materials.new('Brushed carbide cutting head')
    cutter.use_nodes=True
    shader=cutter.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.48,.47,.43,1)
    shader.inputs['Metallic'].default_value=.82
    shader.inputs['Roughness'].default_value=.34
    for obj in scene.objects:
        if obj.name=='Round cutting bur' or obj.name.startswith('Cutting flute'):
            obj.data.materials.clear()
            obj.data.materials.append(cutter)

if shot=='suture':
    margins=[o for o in scene.objects if o.type=='MESH' and o.data.shape_keys and
             o.data.shape_keys.key_blocks.get('Edge apposition at knot')]
    if len(margins)!=2:
        raise ValueError('The two evaluated suture margins are required')
    for obj in margins:
        edge=obj.data.shape_keys.key_blocks['Edge apposition at knot']
        for t,value in ((37.85,1.),(38.5,.90),(39.22,.62),(39.94,.18),(40.45,.015),(40.5,.015),(44,.015)):
            edge.value=value
            edge.keyframe_insert('value',frame=1+20*t)
    # The original cut uses a posterior opening to show a clot. The closure
    # edit ends on the approximated margins and tied thread.
    clot=bpy.data.objects.get('Consolidating clot below posterior suture gap')
    if clot:
        clot.visible_camera=False

if shot in ('fracture','section','separate','elevate','divide_roots','deliver_first_root','deliver_root','specimen'):
    for mat in bpy.data.materials:
        if 'cementum' not in mat.name.lower() or not mat.node_tree:
            continue
        tree=mat.node_tree
        for shader in [n for n in tree.nodes if n.type=='BSDF_PRINCIPLED']:
            base=shader.inputs['Base Color']
            if base.is_linked:
                previous=base.links[0].from_socket
                mix=tree.nodes.new('ShaderNodeMixRGB')
                mix.inputs[0].default_value=.40
                mix.inputs[2].default_value=(.52,.38,.22,1)
                tree.links.new(previous,mix.inputs[1])
                tree.links.new(mix.outputs[0],base)
            for name,value in [('Roughness',.46),('Coat Weight',.12),('Coat Roughness',.38)]:
                socket=shader.inputs[name]
                for link in list(socket.links):tree.links.remove(link)
                socket.default_value=value

base='cortical_window.py' if shot in ('reflect','drill','suction') else 'archive_scene.py'
runpy.run_path(str(Path(__file__).with_name(base)),run_name='__main__')
if args['mode']=='audit':
    path=Path(args['out'])/'geometry.json'
    data=json.loads(path.read_text())
    for row in data['frames']:
        row['can_reuse']=False
    if support:
        audit_ridge(data['frames'],json.loads(Path(args['audit']).read_text()),support)
        data['adjacent_molar_support']='Shape key on the original alveolar bed registered to the direct DBCLS second molar'
    if shot=='suture':
        pose=json.loads(Path(args['audit']).read_text())['frames']
        for row in data['frames']:
            fr=pose[row['original']-1]['source_frame']
            scene.frame_set(math.floor(fr),subframe=fr%1)
            row['posterior_opening_weights']=[round(o.data.shape_keys.key_blocks['Edge apposition at knot'].value,5) for o in margins]
    temp=path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False))
    temp.replace(path)
