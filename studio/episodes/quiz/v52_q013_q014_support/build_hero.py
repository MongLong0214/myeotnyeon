"""Additive local v51-style Blender stills, empty invented sets; no identifiable location."""
import bpy,sys,math,time,json
from pathlib import Path
from mathutils import Vector
W=Path('.');sys.path.insert(0,str(W/'production/blender'));import world2 as A
q=sys.argv[sys.argv.index('--')+1];p=W/'research/hook_stills';start=time.monotonic()
for ext in ['_raw.png','.blend','_render.json']:assert not (p/f'{q}{ext}').exists()
s=A.reset(samples=64);s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.use_motion_blur=False;s.eevee.shadow_pool_size='512';s.eevee.shadow_ray_count=1;s.view_settings.exposure=.6
A.world('moonless_golf',strength=.16,haze=.0005)
ground=A.ph_mat('asphalt_02',tile_m=3);A.plane('asphalt',(100,100),(0,0,0),ground)
bs=next(n for n in ground.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.19
wall=A.ph_mat('plastered_wall_02',tile_m=2,box=True,tint=(.5,.58,.62));metal=A.mat('brushed metal',(.13,.16,.18),rough=.3,metal=.8);glass=A.mat('dark windows',(.009,.018,.023),rough=.12,coat=.7)
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,target,power,col,size):
 o=A.light('AREA',name,loc,power,col,size=size);aim(o,target);o.data.use_shadow=False;return o
if q=='q013':
 A.box('generic factory dormitory',(23,9,9),(0,23,4.5),wall,.05)
 for z in [2,5.3,8]:
  for x in range(-9,11,3):
   A.box('unmarked dorm window',(1.3,.08,1.5),(x,18.43,z),glass,.025)
   A.box('window lintel',(1.5,.15,.12),(x,18.3,z+.8),metal,.02)
 A.box('service door',(2,.13,3),(3,18.35,1.5),metal,.02)
 for x in [-12,12]:A.box('fence pillar',(.2,.2,3),(x,11,1.5),metal)
 for x in range(-12,13):A.box('vertical fence',(.035,.06,2.5),(x,11,1.25),metal)
 # closed generic delivery bag, symbolic prop; no violence, police tape or implied evidence.
 bag=A.mat('unmarked delivery bag',(.2,.15,.09),rough=.75);A.box('closed delivery bag',(.7,.55,.75),(-1,3,.375),bag,.05)
 area('cold facade wash',(-6,3,9),(0,20,3),16000,(.22,.48,.72),(18,12));area('warm doorway',(3,17,4),(0,4,0),2500,(1,.63,.3),(2,2))
 camera=(-5,-9,1.2);target=(0,18,4.3);lens=27
else:
 for side in [-1,1]:
  A.box('generic alley facade',(8,38,13),(side*10,16,6.5),wall,.08)
  for y in range(0,31,6):
   A.box('unmarked closed storefront',( .12,3.4,3),(side*5.94,y,1.5),metal,.03)
   for z in [5,8.5,11]:A.box('unlit window',(.12,1.5,1.6),(side*5.94,y,z),glass,.02)
  for y in [3,15,27]:
   lamp=A.mat('amber unmarked lamp'+str(side)+str(y),(1,.6,.23),emit=(1,.55,.2),strength=8)
   A.box('wall lamp',(.15,.5,.22),(side*5.8,y,3.5),lamp,.03)
   area('warm store spill',(side*5.4,y,3.3),(0,y+1,0),1100,(1,.58,.28),(1,2))
 area('alley blue ambient',(0,4,14),(0,18,0),9000,(.16,.38,.66),(10,20));area('distant cold pool',(0,33,7),(0,12,0),5000,(.3,.55,1),(4,4))
 camera=(-1,-9,1.1);target=(0,22,5.8);lens=26
# Subtle cool/warm wet-night look, exact same local materials and HDRI family as v51.
for im in bpy.data.images:
 if im.source=='FILE' and max(im.size)>1536:
  k=1536/max(im.size);im.scale(max(1,int(im.size[0]*k)),max(1,int(im.size[1]*k)))
camd=bpy.data.cameras.new('portrait camera');cam=bpy.data.objects.new('portrait camera',camd);s.collection.objects.link(cam);s.camera=cam;cam.location=camera;aim(cam,target);camd.lens=lens;camd.dof.use_dof=True;camd.dof.focus_distance=(Vector(target)-Vector(camera)).length;camd.dof.aperture_fstop=4
s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16';s.render.filepath=str(p/f'{q}_raw.png');bpy.ops.wm.save_as_mainfile(filepath=str(p/f'{q}.blend'));bpy.ops.render.render(write_still=True)
with (p/f'{q}_render.json').open('x') as f:json.dump(dict(episode=q,engine=s.render.engine,samples=64,screen_space_raytracing=True,volumetric_samples=64,resolution=[1080,1920],total_seconds=time.monotonic()-start,network=False,people=False,setting='invented unmarked environment, not actual crime-scene footage',texture_cap=1536),f,indent=1)
