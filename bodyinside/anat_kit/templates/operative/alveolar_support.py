"""Form the interdental ridge from the authored socket beneath the adjacent DBCLS molar."""
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from contact import MeshCache, measure


def fit_ridge():
    bed=bpy.data.objects['Alveolar bed, cortical rim and contiguous vestibule']
    molar=bpy.data.objects['Lower second molar tooth.l']
    points=np.asarray([list(bed.matrix_world.inverted()@molar.matrix_world@v.co) for v in molar.data.vertices])*1000
    low,high=points.min(axis=0),points.max(axis=0)
    centre=(low+high)/2
    radii=(high-low)/2
    height=high[2]-.17*(high[2]-low[2])
    basis=bed.data.shape_keys.reference_key
    ridge=bed.shape_key_add(name='Distal alveolar ridge fitted to the direct second molar',from_mix=False)
    changed=[]
    for i,vertex in enumerate(basis.data):
        ridge.data[i].co=vertex.co
        x,y,z=vertex.co*1000
        dx=(x-centre[0])/radii[0]
        dy=(y-centre[1])/radii[1]
        radius=math.hypot(dx,dy)
        if not radius:
            continue
        distal=(.35*dx+.94*dy)/radius
        edge=max(0.,min(1.,(distal-.30)/.45))
        band=max(0.,min(1.,(.48-abs(radius-.92))/.25))
        weight=(edge*edge*(3-2*edge))*(band*band*(3-2*band))
        target=height+.18*math.sin(1.24*x+.56*y)
        rise=max(0.,target-z)*weight
        if rise>.001:
            ridge.data[i].co.z+=rise*.001
            delta=bed.matrix_world@vertex.co
            raised=bed.matrix_world@ridge.data[i].co
            changed.extend((list(delta),list(raised)))
    if not changed:
        raise ValueError('Adjacent tooth did not register to the socket')
    ridge.value=1.
    box=np.asarray(changed)*bpy.context.scene.unit_settings.scale_length*1000
    return bed,box.min(axis=0)-2.,box.max(axis=0)+2.


def audit_ridge(rows,source,support):
    scene=bpy.context.scene
    bed,low,high=support
    cache=MeshCache()
    for row in rows:
        pose=source['frames'][row['original']-1]
        frame=pose['source_frame']
        scene.frame_set(math.floor(frame),subframe=frame%1)
        graph=bpy.context.evaluated_depsgraph_get()
        surface=cache.get(bed,graph,frame)
        for index in pose['tools']:
            tool=bpy.data.objects[source['tools'][index]]
            if tool.hide_render:
                continue
            moving=cache.get(tool,graph,frame)
            # Outside this envelope the socket equals the separately audited
            # source mesh, whose original contact measurements remain in rows.
            if moving is None or np.any(moving.hi<low) or np.any(moving.lo>high):
                continue
            depth,_=measure(moving,surface,sheet=True)
            if depth:
                row['depths'].append([tool.name,bed.name,round(depth,6)])
