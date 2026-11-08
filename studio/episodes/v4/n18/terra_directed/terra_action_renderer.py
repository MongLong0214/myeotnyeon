import bpy, math, sys
from pathlib import Path
O=Path('episodes/v4/n18/terra_directed'); K=sys.argv[-1]; FPS=15; N=316 if K=='training' else 235
M={}
def ma(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
U=ma('navy',(0.03,.10,.18));P=ma('pack',(0.16,.25,.12));S=ma('skin',(.42,.25,.16));G=ma('ground',(.23,.28,.24));W=ma('wall',(.50,.53,.49));D=ma('dark',(.06,.06,.07));B=ma('wood',(.22,.10,.035));R=ma('red',(.32,.035,.03))
def box(n,x,z,a,b,m,depth=0):
 bpy.ops.mesh.primitive_cube_add(location=(x,depth,z));o=bpy.context.object;o.name=n;o.scale=(a,.18,b);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def ball(n,x,z,r,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(x,-.1,z));o=bpy.context.object;o.name=n;o.scale=(r,.18,r);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def k(o,f,x=None,z=None,r=None):
 if x is not None:o.location.x=x
 if z is not None:o.location.z=z
 if r is not None:o.rotation_euler[1]=r
 o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
def person(n,x,z,uniform,pack=False):
 root=bpy.data.objects.new(n,None);bpy.context.collection.objects.link(root);root.location=(x,0,z)
 for o in [box(n+' body',0,1.25,.34,.62,uniform),ball(n+' head',0,2.12,.25,S),box(n+' cap',0,2.34,.30,.07,uniform),box(n+' armL',-.48,1.28,.07,.50,uniform),box(n+' armR',.48,1.28,.07,.50,uniform),box(n+' legL',-.18,.35,.10,.45,uniform),box(n+' legR',.18,.35,.10,.45,uniform)]:o.parent=root
 if pack:
  for o in [box(n+' rucksack',0,1.30,.49,.62,P,.32),box(n+' strapL',-.21,1.35,.035,.62,P,-.25),box(n+' strapR',.21,1.35,.035,.62,P,-.25)]:o.parent=root
 return root
def setup():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=640;s.render.resolution_y=360;s.render.resolution_percentage=100;s.render.fps=FPS;s.frame_end=N;s.render.image_settings.file_format='PNG';s.render.filepath=str(O/f'terra_{K}_frames/frame_');(O/f'terra_{K}_frames').mkdir(exist_ok=True);s.world.color=(.02,.02,.025)
 bpy.ops.object.light_add(type='AREA',location=(0,-6,8));bpy.context.object.data.energy=1500;bpy.context.object.data.shape='RECTANGLE';bpy.context.object.data.size=14
 bpy.ops.object.camera_add(location=(0,-18,4));cam=bpy.context.object;cam.rotation_euler=(math.pi/2,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=14;s.camera=cam
def train():
 box('field',0,-.2,8,.18,G);box('sky',0,4,8,4,W,.6); people=[]
 for i in range(6):
  q=person('trainee'+str(i),-5+i*1.75,-.15,U,True);people.append(q);k(q,1,-5+i*1.75,-.15,0);k(q,130,-2.7+i*1.35,-.15,0);k(q,200,-.7+i*.48,-.15,0)
 focal=people[2];k(focal,200,.2,-.15,0);k(focal,245,.7,.2,-.55);k(focal,285,1.1,-.55,-math.pi/2);k(focal,N,1.1,-.55,-math.pi/2)
 for q in people:
  if q!=focal:k(q,200,q.location.x,q.location.z,0);k(q,285,q.location.x,q.location.z,.22);k(q,N,q.location.x,q.location.z,.22)
def court():
 box('floor',0,-.2,8,.2,G);box('wall',0,4,8,4,W,.6);box('judge bench',0,3.0,3,.55,B);box('red backing',0,4.1,3.5,.35,R,.55);box('lectern',-3,-.1,.65,1.05,B);box('defense table',3,-.1,2,.65,B)
 judge=person('judge',0,1.8,D);pro=person('prosecutor',-5,-.1,D);a=person('defendant1',2.4,-.1,D);b=person('defendant2',3.7,-.1,D)
 k(pro,1,-5,-.1,0);k(pro,65,-3,-.1,.12);k(pro,120,-3,-.1,.12);k(judge,1,0,1.8,0);k(judge,120,0,1.8,0);k(judge,170,0,1.8,-.22);k(judge,N,0,1.8,-.22);k(a,1,2.4,-.1,0);k(a,170,2.4,-.1,.18);k(b,1,3.7,-.1,0);k(b,170,3.7,-.1,.18)
setup();train() if K=='training' else court();bpy.ops.wm.save_as_mainfile(filepath=str(O/f'terra_{K}_direct.blend'));bpy.ops.render.render(animation=True)
