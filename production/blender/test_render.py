import sys,time,math,bpy
sys.path.insert(0,'/Users/isaac/projects/verdict-kr/work/production/blender')
import importlib,world as W;importlib.reload(W)
W.reset();h=W.build_lot()
for o in bpy.data.objects:
    if o.name.startswith('A'): o.hide_render=True
W.camera(loc=(9,-9,2.4),target=(-1,0.5,0.9),lens=32,dof_dist=True,fstop=4)
s=bpy.context.scene;s.frame_set(1)
for samples,name in ((16,'s16'),(32,'s32')):
    s.eevee.taa_render_samples=samples;s.render.filepath=f'//test/wide_{name}.png'
    t=time.time();bpy.ops.render.render(write_still=True);print('RENDER',name,round(time.time()-t,2),'s')
