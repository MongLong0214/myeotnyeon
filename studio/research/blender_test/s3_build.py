# Built inside the running Blender through the official Blender MCP (execute_blender_code).
import sys, math, bpy
sys.path.insert(0, 'production/blender')
import importlib, world2 as W
importlib.reload(W)
# clear the current file without a factory reset (keeps the MCP add-on alive)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds, bpy.data.images, bpy.data.node_groups):
    for d in list(blk):
        try: blk.remove(d)
        except Exception: pass
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.render.fps = 30
e = s.eevee
e.taa_render_samples = 64
e.shadow_resolution_scale = 1.0
e.use_shadows = True; e.shadow_ray_count = 3; e.shadow_step_count = 12
e.use_raytracing = True; e.ray_tracing_method = 'SCREEN'; e.ray_tracing_options.resolution_scale = '2'
e.use_fast_gi = True
e.volumetric_tile_size = '2'; e.volumetric_samples = 96; e.volumetric_end = 120; e.use_volumetric_shadows = True
e.shadow_pool_size = '1024'
s.render.use_motion_blur = True; s.render.motion_blur_shutter = 0.5
s.view_settings.view_transform = 'AgX'
try: s.view_settings.look = 'AgX - Medium High Contrast'
except TypeError: pass
W._mat_cache.clear() if hasattr(W, '_mat_cache') else None
W._car_cache.clear() if hasattr(W, '_car_cache') else None
W.build_lot(hdri='modern_buildings_night', haze=0.0055, with_parked=True)
try: W.parked_cars(seed=21, occupancy=0.7)
except Exception as ex: print('parked_cars skipped', ex)
hero = W.car('accord_2019', (7.5, 0.25, 0), yaw=math.pi + math.radians(4), paint=(0.012, 0.012, 0.014), lights=True, tag='hero')
# wet asphalt: puddle mask drives roughness down in patches
g = bpy.data.objects.get('asphalt')
m = g.active_material if g else None
if m and m.use_nodes:
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 6.0; nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.46; cr.color_ramp.elements[0].color = (0.07, 0.07, 0.07, 1)
    cr.color_ramp.elements[1].position = 0.56; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    src = next((l.from_socket for l in nt.links if l.to_socket == bsdf.inputs['Roughness']), None)
    if src: nt.links.new(src, mul.inputs[0])
    else: mul.inputs[0].default_value = bsdf.inputs['Roughness'].default_value
    nt.links.new(cr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], bsdf.inputs['Roughness'])
    # darken wet patches slightly
    print('WET_OK')
# camera: bumper-height dolly toward the hero's headlights, slow, with slight drift
cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); s.collection.objects.link(cam); s.camera = cam
cam_d.lens = 35; cam_d.sensor_width = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 1.8; cam_d.dof.aperture_blades = 7
N = 90
for f in range(1, N + 1):
    t = (f - 1) / (N - 1); ease = t * t * (3 - 2 * t)
    cam.location = (-5.2 + 1.6 * ease, -1.15 + 0.10 * ease, 0.42 + 0.03 * math.sin(f * 0.21))
    cam.rotation_euler = (math.radians(88.6 - 0.5 * ease), math.radians(0.25 * math.sin(f * 0.17)), math.radians(-86.5 - 1.2 * ease))
    cam_d.dof.focus_distance = 12.6 - 1.6 * ease
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    cam_d.dof.keyframe_insert('focus_distance', frame=f)
s.frame_start, s.frame_end = 1, N
s.frame_set(45)
bpy.ops.wm.save_as_mainfile(filepath='research/blender_test/s3.blend')
print('S3_BUILT', len(bpy.data.objects))
