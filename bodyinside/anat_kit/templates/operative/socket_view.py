"""Show the empty socket after the delivered tooth has left the surgical field."""
import json
import runpy
import sys
from pathlib import Path

import bpy

config=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
if config['case']!='simple_extraction' or config['shot']!='socket_payoff':
    raise ValueError('The clear-socket camera is limited to the post-extraction payoff')


def clear_field(scene, *unused):
    for name in ('left upper central secondary incisor tooth','Extraction forceps labial','Extraction forceps palatal'):
        bpy.data.objects[name].hide_render=True
    bpy.context.view_layer.update()


if config['mode']=='render':
    bpy.app.handlers.render_pre.append(clear_field)
runpy.run_path(str(Path(__file__).with_name('scene.py')),run_name='__main__')
if config['mode']=='audit':
    # Retain the stricter original penetration test including the withdrawn
    # specimen and both jaws. The empty field cannot carry an enamel leader.
    path=Path(config['out'])/'geometry.json'
    result=json.loads(path.read_text())
    for row in result['frames']:
        row['leader']=None
    result['visibility']='Extracted tooth and both forceps jaws withdrawn at the cut'
    path.write_text(json.dumps(result,ensure_ascii=False))
