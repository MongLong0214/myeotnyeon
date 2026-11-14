import bpy,math
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x,s.render.resolution_y=640,360
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,0.5))
for kind,loc in (('SPOT',(-3,0,5)),('POINT',(3,0,3))):
    ld=bpy.data.lights.new(kind,kind);ld.energy=1000;lo=bpy.data.objects.new(kind,ld);s.collection.objects.link(lo);lo.location=loc
cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);s.collection.objects.link(co);co.location=(0,-12,6);co.rotation_euler=(math.radians(62),0,0);s.camera=co
s.render.filepath='//test/minimal.png';bpy.ops.render.render(write_still=True)
print('DONE')
