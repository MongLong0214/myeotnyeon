"""Procedural, non-photoreal 3D set for EP001 (판결의 이유).

Everything here is built from primitives so the look stays stylised (clay figures,
blocky cars, fog-lit concept parking lot). Nothing models a real place, vehicle
brand, or person. Layout is a concept plan, not the actual site.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Euler

PAL = {
    'navy': (0.012, 0.024, 0.036, 1),
    'asphalt': (0.045, 0.05, 0.056, 1),
    'paint': (0.55, 0.55, 0.52, 1),
    'clay_b': (0.42, 0.405, 0.38, 1),   # person B — neutral clay
    'clay_a': (0.32, 0.33, 0.345, 1),   # person A — neutral grey clay (no moral colour)
    'car': (0.035, 0.045, 0.055, 1),
    'parked': (0.06, 0.06, 0.065, 1),
    'sodium': (1.0, 0.80, 0.58),
    'teal': (0.09, 0.49, 0.53),
    'amber': (0.78, 0.54, 0.21),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y = 1920, 1080
    s.render.resolution_percentage = 100
    s.render.fps = 30
    e = s.eevee
    e.taa_render_samples = 32
    e.use_shadows = True
    e.volumetric_tile_size = '8'
    e.volumetric_samples = 64
    e.volumetric_start = 0.5
    e.volumetric_end = 120
    e.use_volumetric_shadows = True
    e.use_raytracing = False
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    s.view_settings.exposure = 0.0
    return s


def mat(name, color, rough=0.8, metal=0.0, emit=None, strength=0.0, alpha=1.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = spec
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    return m


def obj_from(prim, name, mtl=None, **kw):
    getattr(bpy.ops.mesh, prim)(**kw)
    o = bpy.context.active_object
    o.name = name
    if mtl:
        o.data.materials.append(mtl)
    return o


def bevel(o, w=0.05, seg=3):
    md = o.modifiers.new('bevel', 'BEVEL')
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    return o


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- world / fog
def world(fog_density=0.010, fog_color=(0.42, 0.58, 0.64)):
    w = bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes['Background'].inputs['Color'].default_value = (0.010, 0.016, 0.024, 1)
    nt.nodes['Background'].inputs['Strength'].default_value = 1.0
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Density'].default_value = fog_density
    vol.inputs['Color'].default_value = (*fog_color, 1)
    vol.inputs['Anisotropy'].default_value = 0.35
    nt.links.new(vol.outputs['Volume'], nt.nodes['World Output'].inputs['Volume'])
    return w


# ---------------------------------------------------------------- ground
def ground(size=160):
    m = bpy.data.materials.new('asphalt')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = PAL['asphalt']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['To Min'].default_value = 0.55
    ramp.inputs['To Max'].default_value = 0.95
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Value'])
    nt.links.new(ramp.outputs['Result'], b.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    g = obj_from('primitive_plane_add', 'ground', m, size=size)
    return g


def stall_lines(origin=(0, 0), n=8, stall_w=2.6, depth=5.2, facing=1, mtl=None):
    """Row of parking stalls; facing=+1 opens toward +y."""
    mtl = mtl or mat('paint', PAL['paint'], rough=0.6)
    x0, y0 = origin
    objs = []
    for i in range(n + 1):
        x = x0 + i * stall_w
        o = obj_from('primitive_plane_add', f'line_{x0}_{y0}_{i}', mtl, size=1)
        o.scale = (0.06, depth / 2, 1)
        o.location = (x, y0 + facing * depth / 2, 0.006)
        objs.append(o)
    return objs


# ---------------------------------------------------------------- props
def street_lamp(loc, height=6.5, power=5200, color=None, name='lamp', arm=(0.0, -1.0)):
    """Pole at loc; lamp head on an arm offset so the light is not inside the pole."""
    color = color or PAL['sodium']
    pole_m = mat('pole', (0.05, 0.05, 0.055, 1), rough=0.5, metal=0.6)
    pole = obj_from('primitive_cylinder_add', name + '_pole', pole_m, radius=0.07, depth=height,
                    location=(loc[0], loc[1], height / 2))
    hx, hy = loc[0] + arm[0], loc[1] + arm[1]
    armo = obj_from('primitive_cube_add', name + '_arm', pole_m, size=1,
                    location=((loc[0] + hx) / 2, (loc[1] + hy) / 2, height + 0.02))
    armo.scale = (abs(arm[0]) + 0.06, abs(arm[1]) + 0.06, 0.05)
    head = obj_from('primitive_cube_add', name + '_head', pole_m, size=1, location=(hx, hy, height + 0.06))
    head.scale = (0.55, 0.3, 0.08)
    glow = obj_from('primitive_plane_add', name + '_glow', mat('glow', (0, 0, 0, 1), emit=color, strength=40), size=1,
                    location=(hx, hy, height + 0.015))
    glow.scale = (0.45, 0.22, 1)
    glow.rotation_euler = (math.pi, 0, 0)
    ld = bpy.data.lights.new(name + '_spot', 'SPOT')
    ld.energy = power
    ld.color = color
    ld.spot_size = math.radians(110)
    ld.spot_blend = 0.55
    ld.shadow_soft_size = 0.3
    lo = bpy.data.objects.new(name + '_spot', ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (hx, hy, height - 0.05)
    return pole, lo


def sedan(name, loc=(0, 0, 0), rot_z=0.0, paint=None, lights=False, headlight_power=420):
    """Brand-less stylised sedan, length ~4.7 m. Returns root empty."""
    paint = paint or mat(name + '_paint', PAL['car'], rough=0.35, metal=0.5)
    glass = mat(name + '_glass', (0.01, 0.012, 0.015, 1), rough=0.08, metal=0.0, spec=0.9)
    rubber = mat('rubber', (0.012, 0.012, 0.012, 1), rough=0.9)
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    body = obj_from('primitive_cube_add', name + '_body', paint, size=1, location=(0, 0, 0.62))
    body.scale = (4.7, 1.84, 0.62)
    bevel(body, 0.16, 4)
    cab = obj_from('primitive_cube_add', name + '_cabin', glass, size=1, location=(-0.25, 0, 1.18))
    cab.scale = (2.5, 1.6, 0.52)
    bm = bmesh.new(); bm.from_mesh(cab.data)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.x *= 0.62
            v.co.y *= 0.86
    bm.to_mesh(cab.data); bm.free()
    bevel(cab, 0.08, 3)
    roof = obj_from('primitive_cube_add', name + '_roof', paint, size=1, location=(-0.25, 0, 1.445))
    roof.scale = (1.5, 1.36, 0.04)
    bevel(roof, 0.02, 2)
    parts = [body, cab, roof]
    for sx in (1.45, -1.45):
        for sy in (0.86, -0.86):
            w = obj_from('primitive_cylinder_add', name + '_wheel', rubber, radius=0.36, depth=0.26,
                         location=(sx, sy, 0.36), rotation=(math.pi / 2, 0, 0))
            bevel(w, 0.04, 2)
            parts.append(w)
    hl = mat(name + '_hl', (0.9, 0.9, 0.85, 1), emit=(1.0, 0.95, 0.85), strength=30 if lights else 0.5)
    tl = mat(name + '_tl', (0.3, 0.02, 0.02, 1), emit=(1.0, 0.05, 0.03), strength=8 if lights else 0.3)
    for sy in (0.62, -0.62):
        h = obj_from('primitive_cube_add', name + '_hl', hl, size=1, location=(2.36, sy, 0.78))
        h.scale = (0.04, 0.42, 0.12)
        t = obj_from('primitive_cube_add', name + '_tl', tl, size=1, location=(-2.36, sy, 0.82))
        t.scale = (0.04, 0.42, 0.1)
        parts += [h, t]
    if lights:
        for sy in (0.62, -0.62):
            ld = bpy.data.lights.new(name + '_beam', 'SPOT')
            ld.energy = headlight_power
            ld.color = (1.0, 0.94, 0.84)
            ld.spot_size = math.radians(48)
            ld.spot_blend = 0.4
            lo = bpy.data.objects.new(name + '_beam', ld)
            bpy.context.collection.objects.link(lo)
            lo.location = (2.45, sy, 0.78)
            lo.rotation_euler = (0, math.radians(-84), 0)  # aim along +x, slightly down
            parts.append(lo)
    for p in parts:
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def _limb(name, mtl, length, radius, parent=None, head_loc=(0, 0, 0)):
    """Capsule hanging down from its origin (joint at origin)."""
    o = obj_from('primitive_cylinder_add', name, mtl, radius=radius, depth=length, vertices=20,
                 location=(0, 0, -length / 2))
    bevel(o, radius * 0.9, 4)
    smooth(o)
    # move origin to joint (top)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    o.location = head_loc
    if parent:
        o.parent = parent
    return o


def mannequin(name, mtl, loc=(0, 0, 0), rot_z=0.0, height=1.76):
    """Faceless clay figure built from capsules. Returns dict of joints (objects)."""
    s = height / 1.76
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    pelvis = bpy.data.objects.new(name + '_pelvis', None)
    bpy.context.collection.objects.link(pelvis)
    pelvis.parent = root
    pelvis.location = (0, 0, 0.95 * s)
    torso = obj_from('primitive_uv_sphere_add', name + '_torso', mtl, radius=1, segments=32, ring_count=16)
    torso.scale = (0.175 * s, 0.11 * s, 0.17 * s)
    torso.location = (0, 0, 0.42 * s)
    torso.parent = pelvis
    smooth(torso)
    abdomen = obj_from('primitive_uv_sphere_add', name + '_abdomen', mtl, radius=1, segments=24, ring_count=12)
    abdomen.scale = (0.135 * s, 0.095 * s, 0.15 * s)
    abdomen.location = (0, 0, 0.20 * s)
    abdomen.parent = pelvis
    smooth(abdomen)
    hips = obj_from('primitive_uv_sphere_add', name + '_hips', mtl, radius=1, segments=24, ring_count=12)
    hips.scale = (0.15 * s, 0.10 * s, 0.11 * s)
    hips.location = (0, 0, 0.0)
    hips.parent = pelvis
    smooth(hips)
    neck = obj_from('primitive_cylinder_add', name + '_neck', mtl, radius=0.055 * s, depth=0.12 * s, location=(0, 0, 0.62 * s))
    neck.parent = pelvis
    smooth(neck)
    head = obj_from('primitive_uv_sphere_add', name + '_head', mtl, radius=1, segments=32, ring_count=16)
    head.scale = (0.088 * s, 0.10 * s, 0.115 * s)
    head.location = (0, 0.005, 0.76 * s)
    head.parent = pelvis
    smooth(head)
    J = {'root': root, 'pelvis': pelvis, 'head': head}
    for side, sx in (('L', 1), ('R', -1)):
        ua = _limb(f'{name}_uarm{side}', mtl, 0.29 * s, 0.045 * s, pelvis, (sx * 0.2 * s, 0, 0.52 * s))
        fa = _limb(f'{name}_farm{side}', mtl, 0.27 * s, 0.038 * s, ua, (0, 0, -0.29 * s))
        th = _limb(f'{name}_thigh{side}', mtl, 0.44 * s, 0.07 * s, pelvis, (sx * 0.09 * s, 0, -0.05 * s))
        sh = _limb(f'{name}_shin{side}', mtl, 0.44 * s, 0.055 * s, th, (0, 0, -0.44 * s))
        J.update({f'uarm{side}': ua, f'farm{side}': fa, f'thigh{side}': th, f'shin{side}': sh})
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return J


def building_block(loc, size=(30, 12, 36), seed=1, lit=0.12):
    random.seed(seed)
    m = bpy.data.materials.new(f'bldg{seed}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.012, 0.014, 0.017, 1)
    b.inputs['Roughness'].default_value = 0.9
    coord = nt.nodes.new('ShaderNodeTexCoord')
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.offset = 0.0
    brick.squash = 1.0
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 1.5
    brick.inputs['Brick Width'].default_value = 3.0
    brick.inputs['Row Height'].default_value = 2.9
    brick.inputs['Color1'].default_value = (1, 1, 1, 1)
    brick.inputs['Color2'].default_value = (0, 0, 0, 1)
    nt.links.new(coord.outputs['Object'], brick.inputs['Vector'])
    noise = nt.nodes.new('ShaderNodeTexWhiteNoise')
    noise.noise_dimensions = '3D'
    snap = nt.nodes.new('ShaderNodeVectorMath'); snap.operation = 'SNAP'
    snap.inputs[1].default_value = (3.0, 3.0, 2.9)
    nt.links.new(coord.outputs['Object'], snap.inputs[0])
    nt.links.new(snap.outputs['Vector'], noise.inputs['Vector'])
    thr = nt.nodes.new('ShaderNodeMath'); thr.operation = 'GREATER_THAN'
    thr.inputs[1].default_value = 1 - lit
    nt.links.new(noise.outputs['Value'], thr.inputs[0])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(brick.outputs['Fac'], inv.inputs[1])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(inv.outputs['Value'], mul.inputs[0])
    nt.links.new(thr.outputs['Value'], mul.inputs[1])
    strength = nt.nodes.new('ShaderNodeMath'); strength.operation = 'MULTIPLY'
    strength.inputs[1].default_value = 0.45
    nt.links.new(mul.outputs['Value'], strength.inputs[0])
    b.inputs['Emission Color'].default_value = (1.0, 0.72, 0.42, 1)
    nt.links.new(strength.outputs['Value'], b.inputs['Emission Strength'])
    o = obj_from('primitive_cube_add', f'bldg{seed}', m, size=1, location=(loc[0], loc[1], size[2] / 2))
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return o


def cctv(loc, yaw=0.0):
    m = mat('cctv', (0.5, 0.5, 0.5, 1), rough=0.4, metal=0.2)
    lens = mat('lens', (0.01, 0.01, 0.01, 1), rough=0.05, emit=(0.1, 0.6, 0.7), strength=0.6)
    root = bpy.data.objects.new('cctv', None)
    bpy.context.collection.objects.link(root)
    pole = obj_from('primitive_cylinder_add', 'cctv_pole', mat('pole2', (0.05, 0.05, 0.05, 1), metal=0.6, rough=0.4),
                    radius=0.06, depth=4.2, location=(0, 0, 2.1))
    arm = obj_from('primitive_cube_add', 'cctv_arm', m, size=1, location=(0.25, 0, 4.1))
    arm.scale = (0.5, 0.06, 0.06)
    body = obj_from('primitive_cube_add', 'cctv_body', m, size=1, location=(0.55, 0, 3.95))
    body.scale = (0.42, 0.16, 0.16)
    body.rotation_euler = (0, math.radians(18), 0)
    bevel(body, 0.03, 2)
    ln = obj_from('primitive_cylinder_add', 'cctv_lens', lens, radius=0.055, depth=0.04,
                  location=(0.77, 0, 3.88), rotation=(0, math.radians(90 + 18), 0))
    for p in (pole, arm, body, ln):
        p.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, yaw)
    return root


def camera(name='cam', loc=(0, -10, 2), target=(0, 0, 1), lens=35, dof_dist=None, fstop=2.8):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    co = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(co)
    co.location = loc
    tgt = bpy.data.objects.new(name + '_tgt', None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = target
    c = co.constraints.new('TRACK_TO')
    c.target = tgt
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    if dof_dist is not None:
        cd.dof.use_dof = True
        cd.dof.focus_object = tgt
        cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = co
    return co, tgt


def key(o, frame, **props):
    for k, v in props.items():
        setattr(o, k, v)
        o.keyframe_insert(data_path=k, frame=frame)


def ease_all(kind='BEZIER'):
    for a in bpy.data.actions:
        for fc in getattr(a, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = kind
                kp.easing = 'AUTO'


def build_lot(seed=7, defendant_lights=True):
    """Concept parking lot used by most EP001 3D shots. Returns handles dict."""
    random.seed(seed)
    world()
    ground()
    paint = mat('paint', PAL['paint'], rough=0.6)
    stall_lines((-12, 4), n=9, facing=1, mtl=paint)
    stall_lines((-12, -4), n=9, facing=-1, mtl=paint)
    parked_m = mat('parked_paint', PAL['parked'], rough=0.45, metal=0.4)
    taken = [0, 1, 3, 5, 6, 8]
    for i in taken:
        sedan(f'parked_n{i}', loc=(-12 + 2.6 * i + 1.3, 6.6, 0), rot_z=math.pi / 2 + random.uniform(-0.04, 0.04), paint=parked_m)
    for i in (0, 7):
        sedan(f'parked_s{i}', loc=(-12 + 2.6 * i + 1.3, -6.6, 0), rot_z=-math.pi / 2 + random.uniform(-0.04, 0.04), paint=parked_m)
    for x in (-11, 3.5, 17):
        street_lamp((x, 3.4), name=f'lamp{x}', arm=(0.0, -1.6))
    street_lamp((-4, -11), name='lampS', power=3000, arm=(0.0, 1.2))
    # faint cool fill from the sky side so silhouettes read (stylised, not physical moonlight)
    fd = bpy.data.lights.new('fill', 'SUN'); fd.energy = 0.08; fd.color = (0.55, 0.7, 0.85)
    fo = bpy.data.objects.new('fill', fd); bpy.context.collection.objects.link(fo)
    fo.rotation_euler = (math.radians(55), 0, math.radians(-30))
    building_block((-6, 34), size=(46, 12, 42), seed=2, lit=0.10)
    building_block((40, 20), size=(14, 40, 30), seed=3, lit=0.08)
    building_block((-46, 18), size=(14, 30, 36), seed=4, lit=0.07)
    defendant_paint = mat('def_paint', (0.05, 0.065, 0.08, 1), rough=0.3, metal=0.55)
    car = sedan('car_A', loc=(-3.0, 0.0, 0), rot_z=0.0, paint=defendant_paint, lights=defendant_lights)
    clay_b = mat('clay_b', PAL['clay_b'], rough=0.65)
    clay_a = mat('clay_a', PAL['clay_a'], rough=0.65)
    B = mannequin('B', clay_b, loc=(1.6, 0.0, 0), rot_z=math.pi / 2)
    A = mannequin('A', clay_a, loc=(-3.0, 0.4, 0.15), rot_z=-math.pi / 2, height=1.66)
    return {'car': car, 'B': B, 'A': A}
