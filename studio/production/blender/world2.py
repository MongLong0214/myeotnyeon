"""EP001 set v2 — realistic environment built from CC0 assets (Poly Haven) plus
procedural Korean apartment architecture. Figures stay faceless plaster mannequins
so the reconstruction cannot be mistaken for real footage of real people.

Units: 1 Blender unit = 1 metre. Target: Blender 5.2 LTS (engine id BLENDER_EEVEE).
"""
import bpy, bmesh, math, random, json, pathlib
from mathutils import Vector, Matrix

ASSETS = pathlib.Path('production/assets')
PH = ASSETS / 'polyhaven'

# ---------------------------------------------------------------- constants
STALL_W, STALL_D, AISLE = 2.5, 5.0, 6.0
LOT_X0, LOT_X1 = -24.0, 24.0
ROW_N_Y = AISLE / 2            # north stall row starts here (+y)
ROW_S_Y = -AISLE / 2           # south stall row starts here (-y)
CURB_N_Y = ROW_N_Y + STALL_D   # curb / walkway in front of the apartment
BLDG_Y = CURB_N_Y + 9.0        # apartment front face
FLOOR_H = 2.8
LAMP_H = 7.5
LED_K = (1.0, 0.93, 0.84)      # ~4300 K LED, linear-ish RGB
WARM = (1.0, 0.72, 0.45)


def reset(samples=20):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
    s.render.fps = 30
    e = s.eevee
    e.taa_render_samples = samples
    e.shadow_resolution_scale = 0.5
    e.use_shadows = True
    e.shadow_ray_count = 2
    e.shadow_step_count = 8
    e.use_raytracing = True
    e.ray_tracing_method = 'SCREEN'
    e.ray_tracing_options.resolution_scale = '2'
    e.use_fast_gi = True
    e.volumetric_tile_size = '4'
    e.volumetric_samples = 64
    e.volumetric_end = 150
    e.use_volumetric_shadows = True
    e.shadow_pool_size = '1024'
    s.render.use_motion_blur = True
    s.render.motion_blur_shutter = 0.5
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    return s


# ---------------------------------------------------------------- materials
_mat_cache = {}


def ph_mat(aid, tile_m=2.0, box=False, tint=None, rough_mul=None):
    """Append a Poly Haven material and drive its mapping from object coords."""
    key = (aid, tile_m, box, tint, rough_mul)
    if key in _mat_cache:
        return _mat_cache[key]
    blend = next((PH / aid).glob('*.blend'))
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.materials = [aid]
    m = dst.materials[0]
    m.name = f'{aid}_{tile_m}_{int(box)}'
    nt = m.node_tree
    mp = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeMapping')
    tc = next((n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexCoord'), None) or nt.nodes.new('ShaderNodeTexCoord')
    for l in list(mp.inputs['Vector'].links):
        nt.links.remove(l)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (1 / tile_m,) * 3
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeTexImage' and box:
            n.projection = 'BOX'
            n.projection_blend = 0.25
        if n.bl_idname == 'ShaderNodeDisplacement':
            n.inputs['Scale'].default_value = 0.0   # bump only via normal map; no true displacement
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    if tint:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        src_link = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
        if src_link:
            nt.links.new(src_link, mix.inputs['A'])
            mix.inputs['B'].default_value = (*tint, 1)
            nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    _mat_cache[key] = m
    return m


def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0, alpha=1.0, coat=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color[:3], 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = ior
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    return m


def plaster(name='plaster', color=(0.78, 0.76, 0.72)):
    """Matte plaster for the faceless figures (subtle SSS, no skin)."""
    m = mat(name, color, rough=0.55)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.08
    b.inputs['Subsurface Radius'].default_value = (0.4, 0.3, 0.25)
    b.inputs['Subsurface Scale'].default_value = 0.02
    return m


# ---------------------------------------------------------------- geometry helpers
def box(name, size, loc, material=None, bevel=0.0, parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if material:
        me.materials.append(material)
    if bevel:
        md = o.modifiers.new('bevel', 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
    if parent:
        o.parent = parent
    return o


def plane(name, size, loc, material=None, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if material:
        me.materials.append(material)
    return o


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    return e


def ph_append(aid, prefix=None, keep=None, lod=0):
    """Append one LOD level (default LOD0) of a Poly Haven model under one root empty."""
    blend = next((PH / aid).glob('*.blend'))
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        has_lod = any('LOD' in n for n in src.objects)
        avail = sorted({int(n.split('LOD')[1][0]) for n in src.objects if 'LOD' in n and n.split('LOD')[1][:1].isdigit()}) if has_lod else [0]
        use = min(avail, key=lambda v: abs(v - lod)) if avail else 0
        names = [n for n in src.objects if not n.startswith(('wdg_', 'rig_')) and (not has_lod or 'LOD' not in n or f'LOD{use}' in n)]
        if keep:
            names = [n for n in names if any(k in n for k in keep)]
        dst.objects = names
    root = empty(prefix or aid)
    for o in dst.objects:
        if o is None:
            continue
        bpy.context.scene.collection.objects.link(o)
    for o in dst.objects:
        if o is None:
            continue
        mw = o.matrix_world.copy()
        if o.parent is None or o.parent not in dst.objects:
            o.parent = None
            o.matrix_world = mw
            o.parent = root
        o.constraints.clear()
    return root


PROPS = ASSETS / 'objaverse' / 'props'
_prop_cache = {}


def glb_prop(name, height, loc, yaw=0.0, tag=None):
    """Instance a downloaded glTF prop (assets/objaverse/props/<name>.glb, CC-BY, see props_meta.json)
    scaled to `height` metres, centred in x/y, base on z=0. Copies share mesh data."""
    from mathutils import Matrix
    if name not in _prop_cache:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(PROPS / f'{name}.glb'))
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons)]
        bpy.context.view_layer.update()
        lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
        for o in meshes:
            for c in o.bound_box:
                v = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
        tpl = empty(f'{name}_tpl')
        for o in new:
            if o.parent is None:
                o.parent = tpl
        k = height / (hi.z - lo.z)
        tpl.scale = (k, k, k)
        tpl.location = (-(lo.x + hi.x) / 2 * k, -(lo.y + hi.y) / 2 * k, -lo.z * k - 1000)
        for o in meshes:
            o.hide_render = True
        bpy.context.view_layer.update()
        _prop_cache[name] = meshes
    meshes = _prop_cache[name]
    lift = Matrix.Translation((0, 0, 1000))
    root = empty(tag or f'{name}_inst', loc)
    root.rotation_euler = (0, 0, yaw)
    for o in meshes:
        c = o.copy(); bpy.context.scene.collection.objects.link(c)
        c.parent = root; c.matrix_parent_inverse.identity()
        c.matrix_basis = lift @ o.matrix_world
        c.hide_render = False; c.hide_viewport = False
    return root


def light(kind, name, loc, energy, color=(1, 1, 1), rot=(0, 0, 0), size=None, spot=None, blend=0.5, soft=0.2):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy; ld.color = color
    if kind == 'SPOT':
        ld.spot_size = math.radians(spot or 90); ld.spot_blend = blend; ld.shadow_soft_size = soft
    if kind == 'AREA':
        ld.shape = 'RECTANGLE'; ld.size, ld.size_y = size or (1, 1)
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc; lo.rotation_euler = rot
    return lo


# ---------------------------------------------------------------- world
def world(hdri='modern_buildings_night', strength=0.12, haze=0.0018, haze_color=(0.55, 0.62, 0.68)):
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    f = next((PH / hdri).glob('*.hdr'))
    env.image = bpy.data.images.load(str(f))
    mpn = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
    mpn.inputs['Rotation'].default_value = (0, 0, math.radians(140))
    nt.links.new(tc.outputs['Generated'], mpn.inputs['Vector']); nt.links.new(mpn.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = strength
    if haze > 0:
        vol = nt.nodes.new('ShaderNodeVolumePrincipled')
        vol.inputs['Density'].default_value = haze
        vol.inputs['Color'].default_value = (*haze_color, 1)
        vol.inputs['Anisotropy'].default_value = 0.5
        nt.links.new(vol.outputs['Volume'], nt.nodes['World Output'].inputs['Volume'])
    return w


# ---------------------------------------------------------------- korean apartment block
def apartment(x0, x1, y, floors=15, seed=3, lit_frac=0.07, name='apt'):
    """Slab-type Korean apartment: balcony glass bands, slab edges, stair-core windows."""
    random.seed(seed)
    root = empty(name)
    wall = ph_mat('plastered_wall_02', tile_m=3.0, box=True, tint=(1.0, 0.97, 0.92))
    trim = ph_mat('brushed_concrete', tile_m=2.0, box=True)
    W = x1 - x0; H = floors * FLOOR_H + 2.4; D = 13.0
    body = box(f'{name}_body', (W, D, H), ((x0 + x1) / 2, y + D / 2, H / 2), wall, parent=root)
    glass_dark = mat('glass_dark', (0.015, 0.02, 0.025), rough=0.05, metal=0.0, coat=0.6)
    glass_lit = mat('glass_lit', (0.05, 0.04, 0.03), rough=0.2, emit=(1.0, 0.72, 0.45), strength=0.9)
    glass_tv = mat('glass_tv', (0.03, 0.04, 0.05), rough=0.2, emit=(0.55, 0.7, 1.0), strength=0.45)
    glass_curtain = mat('glass_curtain', (0.08, 0.07, 0.06), rough=0.4, emit=(1.0, 0.8, 0.6), strength=0.28)
    frame_m = mat('frame', (0.75, 0.75, 0.73), rough=0.35, metal=0.2)
    rail_m = mat('rail', (0.25, 0.26, 0.27), rough=0.3, metal=0.8)
    stair_lit = mat('stair_lit', (0.1, 0.1, 0.1), emit=(0.85, 0.95, 1.0), strength=0.8)
    unit_w = 9.6
    n_units = int(W // unit_w)
    core_every = 2
    xs = x0 + (W - n_units * unit_w) / 2
    for f in range(floors):
        z = 1.6 + f * FLOOR_H
        # slab edge band
        box(f'{name}_slab{f}', (W + 0.02, 0.35, 0.22), ((x0 + x1) / 2, y - 0.05, z - 0.11), trim, parent=root)
        for u in range(n_units):
            ux = xs + u * unit_w
            # balcony glass (3 panels) slightly recessed
            for p in range(3):
                px = ux + 0.9 + p * 2.6
                r = random.random()
                g = glass_lit if r < lit_frac else glass_tv if r < lit_frac * 1.2 else glass_curtain if r < lit_frac * 1.35 else glass_dark
                plane(f'{name}_g{f}_{u}_{p}', (2.5, 1.85), (px + 1.25, y - 0.02, z + 1.05), g, rot=(math.radians(90), 0, 0)).parent = root
                box(f'{name}_mul{f}_{u}_{p}', (0.06, 0.08, 1.95), (px, y - 0.06, z + 1.05), frame_m, parent=root)
            box(f'{name}_rail{f}_{u}', (unit_w - 1.4, 0.05, 0.05), (ux + unit_w / 2, y - 0.12, z + 0.95), rail_m, parent=root)
            # stair/elevator core window between unit pairs
            if u % core_every == 1 and u < n_units - 1:
                cx = ux + unit_w
                plane(f'{name}_core{f}_{u}', (0.9, 1.2), (cx, y - 0.02, z + 1.2), stair_lit, rot=(math.radians(90), 0, 0)).parent = root
    # roof parapet
    box(f'{name}_parapet', (W + 0.3, D + 0.3, 1.0), ((x0 + x1) / 2, y + D / 2, H + 0.5), trim, parent=root)
    # ground-floor entrance canopy with warm light
    ex = (x0 + x1) / 2 - unit_w
    box(f'{name}_canopy', (4.5, 2.2, 0.18), (ex, y - 1.1, 3.0), trim, parent=root)
    le = light('AREA', f'{name}_entr', (ex, y - 1.1, 2.88), 260, WARM, size=(3.8, 1.6))
    le.data.use_shadow = False
    # faint city-glow wash so the facade structure reads at night (stylistic fill)
    lw = light('AREA', f'{name}_wash', ((x0 + x1) / 2, y - 40, H * 0.55), 2600, (0.62, 0.72, 0.85), rot=(math.radians(90), 0, 0), size=(W, H))
    lw.data.use_shadow = False
    lw.data.volume_factor = 0.0
    return root


# ---------------------------------------------------------------- lot pieces
def led_pole(x, y, facing=-1, name='pole', power=7000):
    """Modern LED pole: tapered galvanised pole + slim head with emissive panel."""
    root = empty(name, (x, y, 0))
    galv = mat(f'{name}_galv', (0.55, 0.56, 0.57), rough=0.42, metal=0.85)
    me = bpy.data.meshes.new(name + '_pole')
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.085, radius2=0.05, depth=LAMP_H)
    bm.to_mesh(me); bm.free()
    p = bpy.data.objects.new(name + '_pole', me); bpy.context.scene.collection.objects.link(p)
    p.location = (0, 0, LAMP_H / 2); p.parent = root; me.materials.append(galv)
    for poly in me.polygons:
        poly.use_smooth = True
    arm_len = 1.4
    box(name + '_arm', (0.06, arm_len, 0.06), (0, facing * arm_len / 2, LAMP_H - 0.1), galv, parent=root)
    head = box(name + '_head', (0.32, 0.72, 0.09), (0, facing * (arm_len + 0.25), LAMP_H - 0.12), galv, bevel=0.015, parent=root)
    led = mat(f'{name}_led', (0.9, 0.9, 0.9), emit=LED_K, strength=60)
    plane(name + '_ledpanel', (0.26, 0.6), (0, facing * (arm_len + 0.25), LAMP_H - 0.168), led, rot=(math.pi, 0, 0)).parent = root
    box(name + '_base', (0.36, 0.36, 0.5), (0, 0, 0.25), ph_mat('brushed_concrete', 1.0, box=True), parent=root)
    sl = light('SPOT', name + '_spot', (x, y + facing * (arm_len + 0.25), LAMP_H - 0.2), power, LED_K, spot=150, blend=0.75, soft=0.25)
    return root


def lot_markings():
    paint = mat('line_paint', (0.78, 0.77, 0.72), rough=0.55)
    n = int((LOT_X1 - LOT_X0) // STALL_W)
    for i in range(n + 1):
        x = LOT_X0 + i * STALL_W
        for ys in (ROW_N_Y + STALL_D / 2, ROW_S_Y - STALL_D / 2):
            box(f'stall_{i}_{ys:.0f}', (0.12, STALL_D, 0.004), (x, ys, 0.002), paint)
    for ys in (ROW_N_Y, ROW_S_Y):
        box(f'aisle_edge_{ys:.0f}', (LOT_X1 - LOT_X0, 0.12, 0.004), ((LOT_X0 + LOT_X1) / 2, ys, 0.002), paint)
    stop = mat('wheel_stop', (0.8, 0.62, 0.05), rough=0.6)
    for i in range(n):
        x = LOT_X0 + (i + 0.5) * STALL_W
        box(f'stopN_{i}', (1.6, 0.15, 0.12), (x, CURB_N_Y - 0.9, 0.06), stop, bevel=0.02)


def ground():
    asphalt = ph_mat('asphalt_02', tile_m=3.5)
    plane('asphalt', (120, 80), (0, 0, 0), asphalt)
    walk = ph_mat('concrete_pavement', tile_m=1.8)
    plane('walkway', (LOT_X1 - LOT_X0 + 20, BLDG_Y - CURB_N_Y - 3.2), ((LOT_X0 + LOT_X1) / 2, CURB_N_Y + 0.15 + (BLDG_Y - CURB_N_Y - 3.2) / 2, 0.15), walk)
    curb = ph_mat('brushed_concrete', tile_m=1.0, box=True)
    box('curbN', (LOT_X1 - LOT_X0 + 20, 0.2, 0.16), ((LOT_X0 + LOT_X1) / 2, CURB_N_Y + 0.1, 0.08), curb)
    # planting bed in front of the building
    soil = mat('soil', (0.035, 0.028, 0.022), rough=0.95)
    bed_y = BLDG_Y - 1.6
    box('bed', (LOT_X1 - LOT_X0 + 20, 3.0, 0.3), ((LOT_X0 + LOT_X1) / 2, bed_y, 0.15), soil)
    box('bed_curb', (LOT_X1 - LOT_X0 + 20, 0.15, 0.4), ((LOT_X0 + LOT_X1) / 2, bed_y - 1.55, 0.2), curb)
    return bed_y


def vegetation(bed_y, seed=11, tree_lod=1, shrub_lod=2, shrub_step=6):
    random.seed(seed)
    for i, x in enumerate(range(int(LOT_X0) - 6, int(LOT_X1) + 7, 8)):
        aid = 'tree_small_02' if i % 2 else 'island_tree_01'
        r = ph_append(aid, prefix=f'tree{i}', lod=tree_lod)
        r.location = (x + random.uniform(-1, 1), bed_y + random.uniform(-0.4, 0.4), 0.3)
        r.rotation_euler = (0, 0, random.uniform(0, 6.28))
        sc = random.uniform(0.95, 1.3)
        r.scale = (sc, sc, sc)
    for i, x in enumerate(range(int(LOT_X0) - 8, int(LOT_X1) + 8, shrub_step)):
        r = ph_append('shrub_02', prefix=f'shrub{i}', lod=shrub_lod)
        r.location = (x + random.uniform(-0.5, 0.5), bed_y - 0.8 + random.uniform(-0.2, 0.2), 0.3)
        r.rotation_euler = (0, 0, random.uniform(0, 6.28))
        r.scale = (0.7, 0.7, 0.6)


def cctv_pole(x, y, yaw):
    root = empty('cctv', (x, y, 0))
    galv = mat('cctv_galv', (0.6, 0.6, 0.6), rough=0.4, metal=0.8)
    me = bpy.data.meshes.new('cctv_pole'); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.06, radius2=0.05, depth=3.95)
    bm.to_mesh(me); bm.free()
    p = bpy.data.objects.new('cctv_pole', me); bpy.context.scene.collection.objects.link(p)
    p.location = (0, 0, 1.975); p.parent = root; me.materials.append(galv)
    cam = ph_append('security_camera_01', prefix='cctv_cam')
    cam.parent = root
    # the model's wall plate is its +Y end (y 0.27–0.30, z −0.03–0.06); bolt it to the pole's side
    off = Vector((0, -(0.303 + 0.052), 0))
    off.rotate(Matrix.Rotation(yaw, 3, 'Z'))
    cam.location = (off.x, off.y, 3.83)
    cam.rotation_euler = (0, 0, yaw)
    clamp = box('cctv_clamp', (0.13, 0.13, 0.05), (0, 0, 3.85), galv, bevel=0.01, parent=root)
    clamp.location = (0, 0, 3.85)
    return root


def build_lot(hdri='modern_buildings_night', haze=0.0018, with_parked=True):
    world(hdri=hdri, haze=haze)
    ground()
    lot_markings()
    bed_y = BLDG_Y - 1.6
    vegetation(bed_y)
    apartment(LOT_X0 - 14, LOT_X1 + 14, BLDG_Y, floors=15, seed=4)
    # a second block across the road, further away, mostly dark
    apartment(-60, -12, -40, floors=18, seed=8, lit_frac=0.04, name='apt_far')
    side = apartment(-30, 18, 0, floors=16, seed=12, lit_frac=0.05, name='apt_west')   # west block, rotated below
    side.rotation_euler = (0, 0, math.radians(90)); side.location = (-52, -22, 0)
    for i, x in enumerate((-16.0, -4.0, 8.0, 20.0)):
        led_pole(x, CURB_N_Y + 0.6, facing=-1, name=f'pole{i}')
    for i, x in enumerate((-10.0, 14.0)):
        led_pole(x, ROW_S_Y - STALL_D - 0.8, facing=1, name=f'poleS{i}', power=5000)
    cctv_pole(-8.5, ROW_S_Y - STALL_D - 0.6, yaw=math.radians(-35))
    return {}


# ---------------------------------------------------------------- cars (Objaverse / Sketchfab CC-BY)
OBJ = ASSETS / 'objaverse' / 'glb'
# name: (real length m, long axis, front sign along that axis, plate material names to hide, headlight mats, tail mats, body mats)
CARS = {
    'accord_2019': (4.89, 'y', -1, ['material'], ['HeadLights_Glass'], ['BrakeLights_Glass'], ['Platinum_White_Metallic']),
    'malibu_2022': (4.93, 'y', -1, [], [], [], ['malibupaint']),
    'mazda_cx5': (4.55, 'y', -1, [], [], [], ['Main']),
    'kia_sportage': (4.44, 'y', -1, [], [], [], ['Body_1', 'Body_4']),
    'nissan_sylphy': (4.63, 'y', -1, [], [], [], ['default_5']),
    'sentra_b17': (4.63, 'x', -1, [], [], [], ['wire_143224087_2']),
    'lexus_es350': (4.98, 'y', -1, [], [], [], ['2021_Lexus_ES350_F_Sport_LexusES_F_Sport2019_lowcarpaint']),
    'kia_optima_sx': (4.85, 'y', -1, [], [], [], ['body', 'roof']),
}
_car_cache = {}
CHROME = {'accord_2019': ('Color_M02', 'Color_M03')}


def _import_car(name):
    """Import once, normalise to metres, front facing +X, wheels on z=0. Returns root (hidden template)."""
    if name in _car_cache:
        return _car_cache[name]
    length, axis, sign, plates, hl, tl, body = CARS[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(OBJ / f'{name}.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and len(o.data.polygons)]
    drop = [o for o in new if o.type == 'MESH' and not len(o.data.polygons)]
    new = [o for o in new if o not in drop]
    for o in drop:
        for ch in list(o.children):
            mw = ch.matrix_world.copy(); ch.parent = o.parent; ch.matrix_world = mw
        bpy.data.objects.remove(o)
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    dims = hi - lo
    k = length / (dims.y if axis == 'y' else dims.x)
    root = empty(f'{name}_tpl')
    for o in new:
        if o.parent is None:
            o.parent = root
    ctr = (lo + hi) / 2
    # rotate so front → +X
    if axis == 'y':
        rot = math.radians(-90) if sign > 0 else math.radians(90)
    else:
        rot = 0.0 if sign > 0 else math.pi
    inner = empty(f'{name}_inner')
    for o in new:
        if o.parent is root:
            o.parent = inner
    inner.parent = root
    inner.location = (-ctr.x * k, -ctr.y * k, -lo.z * k)
    inner.scale = (k, k, k)
    root.rotation_euler = (0, 0, rot)
    for o in meshes:
        for i, m in enumerate(o.data.materials):
            if m and m.name.split('.')[0] in plates:
                o.hide_render = True; o.hide_viewport = True
    if not body:   # auto-detect body paint = largest-area material that is not glass/tyre/trim
        import re as _re
        area = {}
        for o in meshes:
            for p in o.data.polygons:
                m = o.data.materials[p.material_index] if o.data.materials else None
                if m is None:
                    continue
                area[m.name] = area.get(m.name, 0) + p.area
        print('CARAREA', name, [(k, round(v)) for k, v in sorted(area.items(), key=lambda kv: -kv[1])[:5]])
        for mn, _ in sorted(area.items(), key=lambda kv: -kv[1]):
            if not _re.search(r'glass|tyre|tire|rubber|black|chrome|interior|seat|trim|wheel|rim|light|plastic|grill|mirror', mn, _re.I):
                CARS[name] = (length, axis, sign, plates, hl, tl, [mn.split('.')[0]])
                break
    for mn in CHROME.get(name, ()):     # glTF export dropped metallic on the trim; restore it as chrome
        m = bpy.data.materials.get(mn)
        b = m.node_tree.nodes.get('Principled BSDF') if m and m.use_nodes else None
        if b:
            b.inputs['Metallic'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.16
            b.inputs['Base Color'].default_value = (0.85, 0.85, 0.86, 1.0)
    bpy.context.view_layer.update()
    scrub(meshes, length, set(body), hero=(name == 'accord_2019'), root=root)
    if name != 'accord_2019':
        decimate_meshes(meshes, target_total=PARKED_FACES)
    _car_cache[name] = (root, meshes)
    return root, meshes


PARKED_FACES = 140000


_LIGHTISH = __import__('re').compile(r'light|lamp|glass|led|tail|brake|lens|reflect|signal|indicat|red|amber|orange|turn|fog|tled', __import__('re').I)


def _lightish(m):
    """Lamp lenses, glass and emissive parts must keep their material."""
    if m is None:
        return False
    if _LIGHTISH.search(m.name):
        return True
    b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    if b is None:
        return False
    c = b.inputs['Base Color'].default_value
    if c[0] > 0.25 and c[0] > 2.2 * c[1]:
        return True
    if b.inputs['Alpha'].default_value < 0.95 or b.inputs['Transmission Weight'].default_value > 0.2:
        return True
    return b.inputs['Emission Strength'].default_value > 0 and sum(b.inputs['Emission Color'].default_value[:3]) > 0.1


def _slot(me, m):
    for i, x in enumerate(me.materials):
        if x == m:
            return i
    me.materials.append(m)
    return len(me.materials) - 1


def scrub(meshes, length, body, hero=False, root=None):
    """De-badge by removing whole small islands (emblems, model lettering) near the front and
    rear centre. Deleting faces inside a fixed band (the earlier approach) tore holes in grilles
    and boot lids; repainting islands left the logo legible as relief. Licence-plate textures
    become a plain dark plate. Located by position in car space (front = +X)."""
    L2 = length / 2
    plate_m = bpy.data.materials.get('blank_plate') or mat('blank_plate', (0.05, 0.05, 0.055), rough=0.7)
    stats = dict(front=0, rear=0, plate=0)
    for o in meshes:
        me = o.data
        if not me.materials:
            continue
        mw = o.matrix_world
        textured = {i for i, m in enumerate(me.materials)
                    if m and m.use_nodes and any(n.bl_idname == 'ShaderNodeTexImage' for n in m.node_tree.nodes)}
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        ctr = {f.index: mw @ f.calc_center_median() for f in bm.faces}
        def cand(f):
            m = me.materials[f.material_index]
            return m is not None and m.name.split('.')[0] not in body and not _lightish(m)
        assign = {}
        for f in bm.faces:
            c = ctr[f.index]
            if f.material_index in textured and abs(c.x) > L2 - 0.2 and abs(c.y) < 0.36 and 0.2 < c.z < 1.15 and cand(f):
                assign[f.index] = 'plate'
        seen = set()
        for f in bm.faces:
            if f.index in seen or f.index in assign or not cand(f):
                continue
            isl, stack = [], [f]; seen.add(f.index)
            while stack:
                g = stack.pop(); isl.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in seen and h.index not in assign and cand(h):
                            seen.add(h.index); stack.append(h)
            pts = [ctr[g.index] for g in isl]
            lo = Vector(map(min, *pts)) if len(pts) > 1 else pts[0]; hi = Vector(map(max, *pts)) if len(pts) > 1 else pts[0]
            size = max(hi - lo)
            if all(p.x > L2 - 0.45 and abs(p.y) < 0.35 and 0.35 < p.z < 1.05 for p in pts) and size < 0.32:
                for g in isl:
                    assign[g.index] = 'front'
            elif all(p.x < -L2 + 0.5 and abs(p.y) < 0.72 and 0.55 < p.z < 1.25 for p in pts) and size < 0.36:
                for g in isl:
                    assign[g.index] = 'rear'
        if assign:
            # emblem / lettering islands float on the panel, so removing the whole island leaves
            # the panel intact; plates are repainted because they are part of the bumper surface
            pidx = _slot(me, plate_m)
            kill = []
            for f in bm.faces:
                k = assign.get(f.index)
                if k == 'plate':
                    f.material_index = pidx
                elif k:
                    kill.append(f)
                if k:
                    stats[k] += 1
            if kill:
                bmesh.ops.delete(bm, geom=kill, context='FACES')
            bm.to_mesh(me)
        bm.free()
    print('SCRUB', stats)


def decimate_meshes(meshes, target_total=50000):
    """Bake a collapse-decimated copy into each mesh's data (copies share it)."""
    total = sum(len(o.data.polygons) for o in meshes)
    if total <= target_total:
        return
    ratio = max(0.04, target_total / total)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        if len(o.data.polygons) < 400:
            continue
        md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = ratio; md.use_collapse_triangulate = True
        dg.update()
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        o.modifiers.remove(md)
        old = o.data; o.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)


def car(name, loc, yaw=0.0, paint=None, lights=False, tag=None):
    """Instance a car (linked mesh data). paint: (r,g,b) overrides body material."""
    tpl, meshes = _import_car(name)
    length, axis, sign, plates, hl, tl, body = CARS[name]
    if tpl.location.z > -500:
        tpl.location = (0, 0, -1000)   # park template far below the set
        for o in meshes:
            o.hide_render = True
    bpy.context.view_layer.update()
    from mathutils import Matrix
    Wt_inv = Matrix.Translation(-tpl.matrix_world.translation)
    root = empty(tag or f'{name}_inst', loc)
    root.rotation_euler = (0, 0, yaw)
    paint_m = None
    if paint is not None:
        paint_m = mat(f'{root.name}_paint', paint, rough=0.22, metal=0.6, coat=1.0)
        paint_m.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.05
    hl_m = mat(f'{root.name}_hl', (0.9, 0.9, 0.9), rough=0.05, emit=(1.0, 0.96, 0.9), strength=45) if lights else None
    tl_m = mat(f'{root.name}_tl', (0.4, 0.02, 0.02), rough=0.1, emit=(1.0, 0.04, 0.02), strength=6) if lights else None
    for o in meshes:
        if not o.data.polygons or (o.hide_render and any(m and m.name.split('.')[0] in plates for m in o.data.materials)):
            continue
        c = o.copy()                      # shares mesh data
        bpy.context.scene.collection.objects.link(c)
        c.parent = root
        c.matrix_parent_inverse.identity()
        c.matrix_basis = Wt_inv @ o.matrix_world
        c.hide_render = False; c.hide_viewport = False
        for i, m in enumerate(c.data.materials):
            base = m.name.split('.')[0] if m else ''
            if paint_m and base in body:
                c.material_slots[i].link = 'OBJECT'; c.material_slots[i].material = paint_m
            if hl_m and base in hl:
                c.material_slots[i].link = 'OBJECT'; c.material_slots[i].material = hl_m
            if tl_m and base in tl:
                c.material_slots[i].link = 'OBJECT'; c.material_slots[i].material = tl_m
    if lights:
        for sy in (0.62, -0.62):
            l = light('SPOT', f'{root.name}_beam', (length / 2 - 0.05, sy, 0.72), 900, (1.0, 0.95, 0.88), spot=55, blend=0.35, soft=0.08)
            l.parent = root; l.location = (length / 2 - 0.05, sy, 0.72); l.rotation_euler = (0, math.radians(-86), 0)
    return root


PARKED_COLORS = [(0.85, 0.86, 0.86), (0.02, 0.02, 0.022), (0.45, 0.46, 0.48), (0.75, 0.76, 0.77), (0.15, 0.16, 0.17), (0.86, 0.85, 0.82), (0.05, 0.08, 0.16), (0.85, 0.86, 0.86), (0.3, 0.05, 0.05)]


def parked_cars(seed=21, occupancy=0.7, skip=()):
    random.seed(seed)
    # close-up QA (front/rear sheets): sylphy keeps Chinese-market lettering; sportage, optima and
    # sentra show see-through grilles or boot-lid holes once their emblems are removed, and the
    # sentra/sportage paint override only reaches some panels
    names = [n for n in CARS if n not in ('accord_2019', 'nissan_sylphy', 'kia_sportage', 'kia_optima_sx', 'sentra_b17')]
    n = int((LOT_X1 - LOT_X0) // STALL_W)
    k = 0
    for row, ys, yaw in (('N', ROW_N_Y + STALL_D / 2, math.pi / 2), ('S', ROW_S_Y - STALL_D / 2, -math.pi / 2)):
        for i in range(n):
            if (row, i) in skip or random.random() > occupancy:
                continue
            x = LOT_X0 + (i + 0.5) * STALL_W
            nm = names[k % len(names)]; k += 1
            col = random.choice(PARKED_COLORS)
            car(nm, (x + random.uniform(-0.08, 0.08), ys + random.uniform(-0.15, 0.15), 0), yaw=yaw + random.uniform(-0.03, 0.03), paint=col, tag=f'park_{row}{i}')
