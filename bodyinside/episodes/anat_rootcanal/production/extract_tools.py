"""Capture only the authored instrument meshes in the earlier surgery rig's local space."""
from pathlib import Path
import bpy,numpy as np
root=Path(__file__).resolve().parent/'.cache'
O=bpy.data.objects
for rig,frame,names,base in [
 ('Surgical handpiece',1,['Round cutting bur','Contra-angle head','Power handle','Head retainer']+['Cutting flute'+('.%03d'%i if i else '') for i in range(6)],'bur'),
 ('Blunt irrigation cannula',680,['Irrigation cannula hub'],'rinse'),
 ('Assistant suction • fenestrated Frazier tip',282,['Angled suction shaft','Aspirator ferrule'],'suction')]:
 bpy.context.scene.frame_set(frame);g=bpy.context.evaluated_depsgraph_get()
 inv=O[rig].evaluated_get(g).matrix_world.inverted()
 for i,name in enumerate(names):
  ob=O[name].evaluated_get(g); mesh=ob.to_mesh();mesh.calc_loop_triangles();m=inv@ob.matrix_world
  v=np.array([tuple(m@p.co) for p in mesh.vertices])*1000; f=np.array([p.vertices[:] for p in mesh.loop_triangles])
  print('PART',base,name,len(v),v.min(0).round(1),v.max(0).round(1),flush=True)
  np.savez_compressed(root/f'{base}_{i}.npz',v=v.astype('f'),f=f.astype('i'));ob.to_mesh_clear()
