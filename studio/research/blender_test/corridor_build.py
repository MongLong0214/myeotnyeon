# 3-second photoreal-ish night corridor reconstruction. Procedural only (no external assets).
import bpy, math, random
from mathutils import Vector

random.seed(7)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = 48
scn.cycles.use_denoising = True
try:
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scn.cycles.device = 'GPU'
except Exception as e:
    print('GPU setup failed, CPU fallback:', e)
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.fps = 24
scn.frame_start, scn.frame_end = 1, 72
scn.render.use_motion_blur = True
try:
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    scn.view_settings.view_transform = 'Filmic'
scn.render.image_settings.file_format = 'PNG'
scn.render.filepath = bpy.path.abspath('//frames/f_')

def mat(name, base, rough, bump_scale=0.0, wet=False, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 18.0
    noise.inputs['Detail'].default_value = 12.0
    nt.links.new(tex.outputs['Object'], noise.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (base[0]*0.6, base[1]*0.6, base[2]*0.6, 1)
    ramp.color_ramp.elements[1].color = (base[0], base[1], base[2], 1)
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = metallic
    if wet:
        mask = nt.nodes.new('ShaderNodeTexNoise')
        mask.inputs['Scale'].default_value = 2.2
        mask.inputs['Detail'].default_value = 4.0
        nt.links.new(tex.outputs['Object'], mask.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeValToRGB')
        mr.color_ramp.elements[0].position = 0.45
        mr.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1)
        mr.color_ramp.elements[1].position = 0.6
        mr.color_ramp.elements[1].color = (rough, rough, rough, 1)
        nt.links.new(mask.outputs['Fac'], mr.inputs['Fac'])
        nt.links.new(mr.outputs['Color'], bsdf.inputs['Roughness'])
    else:
        bsdf.inputs['Roughness'].default_value = rough
    if bump_scale > 0:
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = bump_scale
        nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m

concrete = mat('concrete', (0.32, 0.31, 0.29), 0.85, bump_scale=0.25)
floor = mat('wetfloor', (0.10, 0.10, 0.11), 0.75, bump_scale=0.08, wet=True)
door_m = mat('door', (0.18, 0.20, 0.22), 0.5, bump_scale=0.05, metallic=0.6)

def box(name, loc, dims, m):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new('bev', 'BEVEL'); bev.width = 0.01; bev.segments = 2
    o.data.materials.append(m)
    return o

L, W, H = 24.0, 2.4, 2.8
box('floor', (0, L/2, -0.05), (W+0.4, L, 0.1), floor)
box('ceil', (0, L/2, H+0.05), (W+0.4, L, 0.1), concrete)
box('wallL', (-W/2-0.1, L/2, H/2), (0.2, L, H), concrete)
box('wallR', (W/2+0.1, L/2, H/2), (0.2, L, H), concrete)
box('end', (0, L+0.1, H/2), (W+0.4, 0.2, H), concrete)
# recessed door frames on right wall, one ajar with warm light behind
for i, y in enumerate([5.0, 11.0, 17.0]):
    box(f'frame{i}', (W/2-0.02, y, 1.05), (0.06, 1.0, 2.1), door_m)
door = box('door_ajar', (W/2-0.05, 11.45, 1.05), (0.05, 0.9, 2.05), door_m)
door.rotation_euler[2] = math.radians(-28)
bpy.ops.object.light_add(type='AREA', location=(W/2+0.8, 11.0, 1.2))
warm = bpy.context.active_object; warm.data.energy = 900; warm.data.color = (1.0, 0.62, 0.32); warm.data.size = 1.2
warm.rotation_euler = (0, math.radians(-90), 0)

# fluorescent tubes with emission + flicker on one
def tube(y, flicker=False):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.2, location=(0, y, H-0.06), rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object
    m = bpy.data.materials.new(f'tube{y}'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.86, 0.93, 1.0, 1)
    em.inputs['Strength'].default_value = 60
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
    t.data.materials.append(m)
    bpy.ops.object.light_add(type='AREA', location=(0, y, H-0.12))
    lt = bpy.context.active_object; lt.data.shape = 'RECTANGLE'; lt.data.size = 1.2; lt.data.size_y = 0.08
    lt.data.energy = 140; lt.data.color = (0.86, 0.93, 1.0)
    if flicker:
        for f in range(1, 73):
            on = not (f in (18, 19, 34, 35, 36, 52) or random.random() < 0.04)
            lt.data.energy = 140 if on else 8
            lt.data.keyframe_insert('energy', frame=f)
            em.inputs['Strength'].default_value = 60 if on else 2
            em.inputs['Strength'].keyframe_insert('default_value', frame=f)
for y in (3.0, 9.0, 15.0, 21.0):
    tube(y, flicker=(y == 9.0))

# world: near black with faint blue
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.006, 0.012, 1)

# camera: slow dolly forward at eye height, slight handheld shake, shallow DOF
bpy.ops.object.camera_add(location=(-0.35, 0.6, 1.55), rotation=(math.radians(88), 0, math.radians(-4)))
cam = bpy.context.active_object; scn.camera = cam
cam.data.lens = 32
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2; cam.data.dof.focus_distance = 9.5
for f in range(1, 73):
    t = (f-1)/71
    cam.location = (-0.35 + 0.015*math.sin(f*0.9), 0.6 + 2.2*t, 1.55 + 0.01*math.sin(f*1.7))
    cam.rotation_euler = (math.radians(88 + 0.25*math.sin(f*0.7)), math.radians(0.3*math.sin(f*0.5)), math.radians(-4 + 0.2*math.sin(f*0.4)))
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)

scn.render.filepath = 'research/blender_test/frames/f_'
bpy.ops.wm.save_as_mainfile(filepath='research/blender_test/corridor.blend')
print('SCENE_BUILT', len(bpy.data.objects))
