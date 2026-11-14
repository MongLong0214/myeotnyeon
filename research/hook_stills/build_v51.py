"""Local EEVEE hero environments. Reuses world2's CC0 materials, HDRIs and parking set."""
import bpy, sys, math, random, time, json
from pathlib import Path
from mathutils import Vector, noise
W=Path('/Users/isaac/projects/verdict-kr/work');sys.path.insert(0,str(W/'production/blender'))
import world2 as A
q=sys.argv[sys.argv.index('--')+1];random.seed(510+int(q[1:]));start=time.monotonic()
s=A.reset(samples=96);s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100
s.render.use_motion_blur=False;e=s.eevee;e.taa_render_samples=96;e.use_raytracing=True;e.ray_tracing_method='SCREEN';e.ray_tracing_options.resolution_scale='1';e.shadow_ray_count=3;e.shadow_step_count=12;e.volumetric_samples=128;e.volumetric_tile_size='2';e.use_volumetric_shadows=True
s.view_settings.exposure=.55
metal=A.mat('galvanized',(0.24,.28,.29),rough=.26,metal=.85)
yellow=A.mat('tape yellow',(.9,.62,.01),rough=.4)
black=A.mat('tape print',(.012,.014,.016),rough=.65)

def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler();return o

def light(name,loc,power,col,size=3,target=None):
 o=A.light('AREA',name,loc,power,col,size=(size,size))
 if target is not None:aim(o,target)
 return o

def tube(name,pts,r,mat):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=r;c.bevel_resolution=2
 p=c.splines.new('POLY');p.points.add(len(pts)-1)
 for v,co in zip(p.points,pts):v.co=(*co,1)
 o=bpy.data.objects.new(name,c);s.collection.objects.link(o);o.data.materials.append(mat);return o

def tape(a,b,name='police tape'):
 # Physical ribbon, slight sag. Stripes are printed on its front surface, no landmark signage.
 a=Vector(a);b=Vector(b);N=64;verts=[]
 for i in range(N+1):
  t=i/N;p=a.lerp(b,t);p.z-=.16*math.sin(t*math.pi)
  verts.extend([tuple(p+Vector((0,0,-.065))),tuple(p+Vector((0,0,.065)))])
 faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(N)]
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(yellow);me.materials.append(black)
 for i,p in enumerate(me.polygons):p.material_index=1 if i%8<2 else 0
 o=bpy.data.objects.new(name,me);s.collection.objects.link(o)

def wet():
 m=bpy.data.objects['asphalt'].active_material;nt=m.node_tree;b=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 tc=nt.nodes.new('ShaderNodeTexCoord');n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=.35;n.inputs['Detail'].default_value=6
 nt.links.new(tc.outputs['Object'],n.inputs['Vector']);r=nt.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.48;r.color_ramp.elements[0].color=(.025,.025,.025,1);r.color_ramp.elements[1].position=.62;r.color_ramp.elements[1].color=(.56,.56,.56,1)
 nt.links.new(n.outputs['Fac'],r.inputs[0]);nt.links.new(r.outputs[0],b.inputs['Roughness'])
 src=b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
 if src:
  mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.29,.34,.37,1);nt.links.new(src,mix.inputs[1]);nt.links.new(mix.outputs[0],b.inputs['Base Color'])

def fence(y):
 for x in range(-22,24,4):tube('fence post',[(x,y,0),(x,y,3)],.045,metal)
 for z in [.1,2.9]:tube('fence rail',[(-23,y,z),(24,y,z)],.025,metal)
 for i in range(-110,110):
  x=i*.24
  # diagonal wire clipped to 2.8m height
  for direction in [-1,1]:tube('chain link',[(x,y,.15),(x+direction*1.35,y,2.85)],.006,metal)

def emergency():
 light('blue emergency',(-6,-2,1.7),1900,(.02,.13,1),3,(0,5,0))
 light('red emergency',(6,5,1.5),1400,(1,.018,.01),2,(0,0,0))
 for x,col in [(-6,(.02,.15,1)),(6,(1,.02,.01))]:
  m=A.mat('unbranded emergency beacon',col,emit=col,strength=30)
  A.box('distant beacon',(.4,.18,.12),(x,9,1.5),m,bevel=.04)

if q=='q017':
 A.build_lot(haze=.0016)
 # Existing full parking-lot recipe + local debadged vehicle model, no people.
 for x,y,yaw,col in [(7,5.8,math.pi/2,(.08,.09,.1)),(-14,5.7,math.pi/2,(.55,.55,.55)),(13,-5.5,-math.pi/2,(.16,.18,.21))]:A.car('accord_2019',(x,y,0),yaw=yaw,paint=col,tag='parked')
 wet();tape((-10,-.8,1.3),(7,3,1.35));emergency()
 camera=(-9,-11,1.25);target=(-3,12,7.5);lens=27
elif q=='q016':
 A.world(haze=.0016);A.ground();wet()
 A.apartment(-40,35,29,floors=12,lit_frac=.11,name='city_block')
 side=A.apartment(-50,35,35,floors=16,lit_frac=.07,name='city_side');side.rotation_euler.z=math.pi/2;side.location.x=-38
 walk=A.ph_mat('concrete_pavement',tile_m=1.8);A.box('sidewalk',(9,48,.18),(7,4,.09),walk)
 paint=A.mat('weathered crossing',(.64,.65,.61),rough=.42)
 for y in range(-6,8,2):A.box('crosswalk stripe',(7,.75,.006),(-4,y,.007),paint)
 # Bent pedestrian rail with deformed supports and two curved horizontal bars.
 for y in [-5,-2,1,4,7,10]:
  dx=-.8 if y in [-2,1] else 0
  tube('bent rail post',[(2.5,y,.18),(2.5+dx,y+.3,.9)],.055,metal)
 for z in [.5,.9]:tube('buckled guardrail',[(2.5,-7,z),(2.5,-4,z),(1.7,-1,z-.22),(1.6,1,z-.08),(2.5,4,z),(2.5,11,z)],.055,metal)
 for i in range(45):
  m=metal if i%3 else A.mat('broken dark plastic'+str(i),(.025,.03,.035),rough=.25)
  o=A.box('scattered fragments',(random.uniform(.03,.17),random.uniform(.04,.22),.025),(random.uniform(-1,4),random.uniform(-6,2),.05),m,bevel=.008);o.rotation_euler.z=random.random()*6.28
 tape((-5,4,1.3),(10,7,1.6));emergency();A.led_pole(-7,13,name='streetlight',power=6500)
 # unlabelled traffic lights
 tube('signal mast',[(8,11,0),(8,11,6),(0,11,6)],.09,metal)
 housing=A.mat('signal black',(.015,.018,.02),rough=.3);A.box('signal',(1.15,.32,.4),(0,11,5.8),housing,.05)
 red=A.mat('traffic red',(.7,.015,.005),emit=(1,.015,.003),strength=15);A.box('red signal',(.22,.03,.23),(-.35,10.82,5.8),red,.05)
 camera=(-7,-10,1.05);target=(1,8,4.6);lens=28
elif q=='q015':
 A.world('moonless_golf',strength=.22,haze=.0022)
 ground=A.ph_mat('asphalt_02',tile_m=3.5);A.plane('asphalt',(160,160),(0,0,0),ground);wet()
 concrete=A.ph_mat('brushed_concrete',tile_m=2,box=True)
 # Empty, unmarked parade ground bounded by barracks and chain-link.
 wall=A.ph_mat('plastered_wall_02',tile_m=3,box=True,tint=(.55,.62,.53));dark=A.mat('barrack glass',(.012,.024,.025),rough=.2,coat=.5)
 for x in [-21,5]:
  A.box('barracks',(22,9,6),(x,36,3),wall,.08)
  for f in range(2):
   for k in range(9):A.box('unlit barrack window',(1.1,.03,1.1),(x-9+k*2.1,31.45,1.7+f*2.5),dark,.02)
  A.box('barrack roof',(23,10,.4),(x,36,6.1),concrete,.04)
 fence(24)
 for x in [-13,13]:
  tube('floodlight mast',[(x,17,0),(x,17,13)],.12,metal)
  A.box('floodlight rack',(2.2,.25,.18),(x,17,12.8),metal)
  for k in [-.65,0,.65]:
   em=A.mat('warm floodlamp',(1,.8,.5),emit=(1,.78,.45),strength=45);A.box('floodlamp',(.5,.15,.4),(x+k,16.9,12.65),em,.03)
  l=A.light('SPOT','floodlight beam',(x,16.7,12.5),24000,(1,.78,.5),spot=95,blend=.4,soft=.3);aim(l,(x*.25,-2,0))
 for y in range(-16,22,8):A.box('parade ground line',(28,.08,.006),(0,y,.01),A.mat('faded chalk'+str(y),(.35,.36,.33),rough=.8))
 light('cold dusk fill',(-10,-4,20),2200,(.16,.36,.55),15,(0,10,0))
 camera=(-5,-15,1.0);target=(0,24,6.4);lens=29
elif q=='q012':
 A.world('moonless_golf',strength=.10,haze=.0012);s.view_settings.exposure=.35
 earth=A.mat('scorched rocky terrain',(.025,.032,.025),rough=.93)
 # Layered continuous ridges, irregular noise geometry, not a flat backdrop.
 def height(x,y):return 5+7*math.sin(x*.065+y*.026)+3.0*noise.fractal(Vector((x*.055,y*.045,2)),1.1,2,4)+y*.10
 verts=[];faces=[];nx=100;ny=90
 for j in range(ny):
  y=-10+j*1.8
  for i in range(nx):
   x=-90+i*1.8;verts.append((x,y,height(x,y)))
 for j in range(ny-1):
  for i in range(nx-1):a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
 me=bpy.data.meshes.new('mountain mesh');me.from_pydata(verts,[],faces);me.materials.append(earth);o=bpy.data.objects.new('layered mountain',me);s.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=True
 # Reuse a local Poly Haven tree, linked duplicates on the ridge.
 tpl=A.ph_append('tree_small_02',prefix='ridge_tree',lod=2);tpl.location=(0,0,-500)
 children=list(tpl.children_recursive)
 for k in range(110):
  x=random.uniform(-58,58);y=random.uniform(15,95);root=A.empty('ridge vegetation',(x,y,height(x,y)));sc=random.uniform(.7,1.8);root.scale=(sc,sc,sc);root.rotation_euler.z=random.uniform(0,6.28)
  for child in children:
   if child.type=='MESH':
    c=child.copy();s.collection.objects.link(c);c.parent=root;c.matrix_basis=child.matrix_world.copy();c.hide_render=False
 # Flickering fireline as clustered irregular tapered emissive tongues, behind ridge.
 fire=A.mat('orange fire',(.8,.08,.003),emit=(1,.13,.005),strength=18)
 hot=A.mat('fire cores',(1,.4,.02),emit=(1,.48,.035),strength=32)
 for k in range(180):
  x=random.uniform(-43,40);y=39+5*math.sin(x*.12)+random.uniform(-2,2);z=height(x,y)
  h=random.uniform(.8,4.5)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z+h*.35));o=bpy.context.object;o.name='distant fire tongue';o.scale=(random.uniform(.2,.65),.4,h*.7);o.data.materials.append(hot if k%4==0 else fire)
 for x in [-30,-10,10,30]:
  y=40+5*math.sin(x*.12);A.light('POINT','fire light',(x,y,height(x,y)+3),8000,(1,.11,.008),soft=4)
 # Turbulent smoke volumes rising from fire line, noise density gives broken wisps.
 sm=bpy.data.materials.new('turbulent smoke');sm.use_nodes=True;nt=sm.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');v=nt.nodes.new('ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(.16,.18,.19,1)
 tc=nt.nodes.new('ShaderNodeTexCoord');nz=nt.nodes.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=3;nz.inputs['Detail'].default_value=5;nt.links.new(tc.outputs['Generated'],nz.inputs['Vector']);r=nt.nodes.new('ShaderNodeMath');r.operation='MULTIPLY';r.inputs[1].default_value=.18;nt.links.new(nz.outputs['Fac'],r.inputs[0]);nt.links.new(r.outputs[0],v.inputs['Density']);nt.links.new(v.outputs['Volume'],out.inputs['Volume'])
 for x in [-25,-6,17,35]:
  y=44;z=height(x,y)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=(x+4,y,z+16));o=bpy.context.object;o.name='drifting smoke';o.scale=(10,7,21);o.data.materials.append(sm)
 ember=A.mat('embers',(1,.15,.005),emit=(1,.22,.015),strength=12)
 for i in range(100):
  x=random.uniform(-35,35);y=random.uniform(15,55);z=height(x,y)+random.uniform(2,24)
  tube('rising ember',[(x,y,z),(x+.025,y,z+random.uniform(.03,.2))],random.uniform(.008,.025),ember)
 light('moon rim',(-25,-5,40),18000,(.15,.32,.45),35,(0,40,5))
 camera=(-12,-23,11);target=(0,48,22);lens=32
else:raise ValueError(q)
camd=bpy.data.cameras.new('portrait cinematic camera');cam=bpy.data.objects.new('portrait cinematic camera',camd);s.collection.objects.link(cam);s.camera=cam;cam.location=camera;aim(cam,target);camd.lens=lens;camd.sensor_width=36;camd.dof.use_dof=True;camd.dof.focus_distance=(Vector(target)-Vector(camera)).length;camd.dof.aperture_fstop=4
s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16';s.render.filepath=str(W/'research/hook_stills'/f'{q}_raw.png')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'research/hook_stills'/f'{q}.blend'))
build=time.monotonic()-start;rs=time.monotonic();bpy.ops.render.render(write_still=True);elapsed=time.monotonic()-rs
(W/'research/hook_stills'/f'{q}_render.json').write_text(json.dumps(dict(episode=q,engine=s.render.engine,samples=e.taa_render_samples,screen_space_raytracing=e.use_raytracing,volumetric_samples=e.volumetric_samples,build_seconds=build,render_seconds=elapsed,total_seconds=time.monotonic()-start,resolution=[1080,1920]),indent=2))
