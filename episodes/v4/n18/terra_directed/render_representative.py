import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
OUT=Path('/Users/isaac/projects/verdict-kr/work/episodes/v4/n18/terra_directed'); FPS=15; W,H=640,360
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []; KIND=args[0] if args and args[0] in ('training','court') else 'training'; PREVIEW='--preview' in args
DUR={'training':21.066667,'court':15.666667}[KIND]; END=1 if PREVIEW else round(DUR*FPS); FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def mat(n,c): m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
NAVY=mat('uniform navy',(.035,.10,.16)); OLIVE=mat('pack olive',(.18,.24,.11)); SKIN=mat('anonymous skin',(.42,.27,.18)); DARK=mat('court charcoal',(.055,.06,.08)); WOOD=mat('bench wood',(.25,.12,.05)); FLOOR=mat('floor',(.10,.14,.13)); WALL=mat('wall',(.31,.34,.33)); RED=mat('bench backing',(.25,.035,.025)); WHITE=mat('subtitle',(.93,.91,.82))
def box(n,l,s,m,p=None):
 bpy.ops.mesh.primitive_cube_add(location=l);o=bpy.context.object;o.name=n;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('soft','BEVEL');mod.width=.04;mod.segments=2
 if p:o.parent=p;o.matrix_parent_inverse=Matrix.Identity(4)
 return o
def cyl(n,l,r,d,m,p=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d,location=l);o=bpy.context.object;o.name=n;o.data.materials.append(m)
 if p:o.parent=p;o.matrix_parent_inverse=Matrix.Identity(4)
 return o
def sph(n,l,s,m,p=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=l);o=bpy.context.object;o.name=n;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if p:o.parent=p;o.matrix_parent_inverse=Matrix.Identity(4)
 return o
def k(o,f,l=None,r=None,h=None):
 if l is not None:o.location=l;o.keyframe_insert('location',frame=f)
 if r is not None:o.rotation_euler=r;o.keyframe_insert('rotation_euler',frame=f)
 if h is not None:o.hide_render=h;o.keyframe_insert('hide_render',frame=f)
def fr(s):return max(1,round(s*FPS))
def person(n,l,uniform=NAVY,pack=False):
 # Every child is root-local before parenting: root translations are not doubled.
 root=bpy.data.objects.new(n,None);bpy.context.collection.objects.link(root);root.location=l; box(n+'_torso',(0,0,1.48),(.34,.19,.55),uniform,root);sph(n+'_head',(0,-.02,2.25),(.25,.23,.28),SKIN,root);box(n+'_cap',(0,-.02,2.49),(.27,.25,.07),uniform,root);parts=[]
 for side in(-1,1):
  a=cyl(n+'_arm'+str(side),(side*.43,0,1.5),.085,.78,uniform,root);a.rotation_euler=(0,side*.2,0);parts.append(a);q=cyl(n+'_leg'+str(side),(side*.17,0,.48),.1,.9,uniform,root);q.rotation_euler=(0,side*.08,0);parts.append(q)
 if pack:
  box(n+'_rucksack',(0,.27,1.55),(.42,.18,.54),OLIVE,root)
  for side in(-1,1):st=cyl(n+'_shoulder_strap'+str(side),(side*.24,-.205,1.61),.032,.77,OLIVE,root);st.rotation_euler=(0,side*.48,0)
 return root,parts
def stride(parts,a,beg,end):
 for p in parts:
  sign=1 if ('1' in p.name) else -1
  if 'arm' in p.name:sign=-sign
  k(p,beg,r=(0,sign*a,0));k(p,(beg+end)//2,r=(0,-sign*a,0));k(p,end,r=(0,sign*a,0))
def sub(txt,a,b):
 bpy.ops.object.text_add(location=(0,-.7,.22),rotation=(math.pi/2,0,0));t=bpy.context.object;t.name='subtitle';t.data.body=txt;t.data.align_x='CENTER';t.data.align_y='CENTER';t.data.size=.32;t.data.extrude=.003;t.data.materials.append(WHITE)
 if Path(FONT).exists():t.data.font=bpy.data.fonts.load(FONT)
 k(t,1,h=True);k(t,fr(a),h=False);k(t,fr(b),h=False);k(t,min(END,fr(b)+1),h=True)
def setup():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=W;s.render.resolution_y=H;s.render.resolution_percentage=100;s.render.fps=FPS;s.frame_start=1;s.frame_end=END;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.filepath=str(OUT/('preview_'+KIND+'.png' if PREVIEW else 'n18_'+KIND+'_frames/frame_'));s.world.color=(.018,.022,.028)
 bpy.ops.object.light_add(type='AREA',location=(0,-4,8));bpy.context.object.data.energy=900;bpy.context.object.data.size=8;bpy.ops.object.light_add(type='AREA',location=(-5,1,4));bpy.context.object.data.energy=450;bpy.context.object.data.size=5;bpy.ops.object.camera_add(location=(0,-16,6));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13.2;cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
def training():
 box('parade_ground',(0,1,-.12),(8,5,.12),FLOOR);box('far_wall',(0,4.5,2),(8,.15,2.1),WALL);people=[]
 for i in range(6):
  r,p=person('trainee_'+str(i),(-5.1+i*1.45,.35+(i%2)*.45,0),pack=True);people.append((r,p));x=-5.1+i*1.45;y=.35+(i%2)*.45;k(r,1,l=(x,y,0));k(r,fr(8.533),l=(x+1.45,y,0));k(r,fr(9.467),l=(x+1.45,y,0));k(r,fr(16.5),l=(x+4.05,y,0));stride(p,.22,1,fr(8.533));stride(p,.48,fr(9.467),fr(16.5))
 focal,p=people[2];k(focal,fr(8.533),l=(-.75,.35,0),r=(0,0,0));k(focal,fr(8.667),l=(-.75,.35,.16),r=(0,math.pi/2,0));k(focal,fr(9.333),l=(-.75,.35,.16),r=(0,math.pi/2,0));k(focal,fr(9.467),l=(-.75,.35,0),r=(0,0,0));k(focal,fr(16.5),l=(1.85,.35,0),r=(0,0,0));k(focal,fr(17.65),l=(2.18,.35,.15),r=(0,.18,-.42));k(focal,fr(18.35),l=(2.32,.35,.15),r=(0,math.pi/2,-math.pi/2));k(focal,END,l=(2.32,.35,.15),r=(0,math.pi/2,-math.pi/2))
 for r,_ in people:
  if r!=focal:k(r,fr(16.5),r=(0,0,0));k(r,fr(18.35),r=(0,0,.24 if r.location.x<0 else -.24));k(r,END,r=(0,0,.24 if r.location.x<0 else -.24))
 sub('완전군장·총기 휴대 훈련병들',0,6.033);sub('팔굽혀펴기',8.533,9.467);sub('뜀걸음 세 바퀴·완전군장',9.467,12.6);sub('17시 11분쯤, 뛰던 훈련병이 쓰러졌습니다.',16.5,19.433)
def court():
 box('court_floor',(0,1,-.12),(8,5,.12),mat('court floor',(.10,.085,.07)));box('court_wall',(0,4.5,2.2),(8,.15,2.3),WALL);box('bench',(0,2.9,3.1),(2.7,.45,.55),WOOD);box('bench_back',(0,3.4,4),(3,.15,.65),RED);judge,jp=person('judge',(0,2.7,2.75),DARK);pro,pp=person('prosecutor',(-4.9,.4,0),DARK);d1,_=person('defendant_a',(2.05,.65,0),DARK);d2,_=person('defendant_b',(3.35,.65,0),DARK);box('lectern',(-2.9,.85,.9),(.46,.36,.9),WOOD);box('defense_table',(2.7,1.1,.68),(1.65,.42,.62),WOOD)
 k(pro,1,l=(-4.9,.4,0));k(pro,fr(2.2),l=(-2.9,.4,0),r=(0,0,.12));k(pro,fr(9.667),l=(-2.9,.4,0),r=(0,0,.12));stride(pp,.22,1,fr(2.2))
 for p in pp:
  if 'arm' in p.name:k(p,fr(2.2),r=(0,.58 if '1' in p.name else -.58,0));k(p,fr(9.667),r=(0,.25 if '1' in p.name else -.25,0))
 k(judge,1,r=(0,0,0));k(judge,fr(9.667),r=(0,0,0));k(judge,fr(10.2),r=(0,0,-.16));k(judge,END,r=(0,0,-.16))
 for p in jp:
  if 'arm' in p.name:k(p,fr(9.667),r=(0,.08,0));k(p,fr(10.2),r=(0,-.38 if '1' in p.name else .38,0));k(p,END,r=(0,-.18 if '1' in p.name else .18,0))
 for d,a in((d1,.14),(d2,-.14)):k(d,1,r=(0,0,0));k(d,fr(10.4),r=(0,0,a));k(d,END,r=(0,0,a))
 sub('2024년 11월 12일 · 검찰 구형',0,5.467);sub('중대장 징역 10년 · 부중대장 징역 7년 구형',.7,5.467);sub('군의 지도력과 관리 체제에 대한 국민 신뢰 훼손',5.467,9.667);sub('2025년 1월 7일 · 1심 판결',9.667,15.667);sub('중대장 징역 5년 · 부중대장 징역 3년 선고',10.3,15.667)
setup();training() if KIND=='training' else court();s=bpy.context.scene;print(json.dumps({'blender_version':bpy.app.version_string,'engine':s.render.engine,'ffmpeg_format':s.render.ffmpeg.format,'output_format':s.render.image_settings.file_format,'kind':KIND,'fps':FPS,'frames':END},ensure_ascii=False));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('n18_training_direct.blend' if KIND=='training' else 'n18_court_direct.blend')));bpy.ops.render.render(write_still=PREVIEW,animation=not PREVIEW)
