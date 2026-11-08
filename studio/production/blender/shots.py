"""EP001 3D shot definitions. Usage:
  blender -b -P shots.py -- SHOT_ID N_FRAMES OUT_DIR [--preview]

Each shot rebuilds its own set so renders are reproducible. Animation is kept
minimal and only shows actions reported from the court record: B stands in front of
the car, the car pushes B over several times, reverses and drives into B once.
Contact moments are not shown (cut before contact) per Q10/Q12 rules.
"""
import sys, os, math, json, random
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world as W

HERE = os.path.dirname(os.path.abspath(__file__))


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a[0], int(a[1]), a[2], ('--preview' in a)


# ------------------------------------------------------------------ helpers
def cam_path(cam, tgt, n, keys):
    """keys: list of (t in 0..1, cam_loc, tgt_loc)."""
    for t, cl, tl in keys:
        f = 1 + round(t * (n - 1))
        W.key(cam, f, location=cl)
        W.key(tgt, f, location=tl)


def seat(A, z=0.58):
    A['pelvis'].location.z = z
    for s in 'LR':
        A[f'thigh{s}'].rotation_euler.x = math.radians(-82)
        A[f'shin{s}'].rotation_euler.x = math.radians(84)
        A[f'uarm{s}'].rotation_euler.x = math.radians(-35)
        A[f'farm{s}'].rotation_euler.x = math.radians(-45)


def place_driver(h):
    A = h['A']
    car = h['car']
    A['root'].parent = car
    A['root'].location = (-0.35, 0.36, 0.0)
    A['root'].rotation_euler = (0, 0, math.pi / 2)
    seat(A)


def stance_stop(B, f, arm='R'):
    """B raises one forearm (stop gesture). Keyframe at frame f."""
    ua, fa = B[f'uarm{arm}'], B[f'farm{arm}']
    W.key(ua, f, rotation_euler=(math.radians(-70), 0, 0))
    W.key(fa, f, rotation_euler=(math.radians(-25), 0, 0))


def stance_rest(B, f):
    for s in 'LR':
        W.key(B[f'uarm{s}'], f, rotation_euler=(0, 0, math.radians(4 if s == 'L' else -4)))
        W.key(B[f'farm{s}'], f, rotation_euler=(math.radians(-6), 0, 0))


def b_fallen(B, f):
    """B seated on the ground, leaning back on hands (non-graphic end state)."""
    W.key(B['pelvis'], f, location=(0, 0, 0.16), rotation_euler=(math.radians(14), 0, 0))
    for s in 'LR':
        W.key(B[f'thigh{s}'], f, rotation_euler=(math.radians(-80), 0, 0))
        W.key(B[f'shin{s}'], f, rotation_euler=(math.radians(30), 0, 0))
        W.key(B[f'uarm{s}'], f, rotation_euler=(math.radians(35), 0, math.radians(18 if s == 'L' else -18)))
        W.key(B[f'farm{s}'], f, rotation_euler=(math.radians(10), 0, 0))


def b_standing(B, f):
    W.key(B['pelvis'], f, location=(0, 0, 0.95), rotation_euler=(0, 0, 0))
    for s in 'LR':
        W.key(B[f'thigh{s}'], f, rotation_euler=(0, 0, 0))
        W.key(B[f'shin{s}'], f, rotation_euler=(0, 0, 0))


def b_lean_back(B, f, deg=12):
    W.key(B['pelvis'], f, location=(0, 0, 0.95), rotation_euler=(math.radians(deg), 0, 0))


def lot(defendant_lights=True, with_cctv=True):
    W.reset()
    h = W.build_lot(defendant_lights=defendant_lights)
    place_driver(h)
    B = h['B']
    B['root'].location = (1.75, 0.0, 0)
    B['root'].rotation_euler = (0, 0, -math.pi / 2)   # faces the car (-X)
    if with_cctv:
        W.cctv((-8.5, -3.6, 0), yaw=math.radians(20))
    return h


def void_studio(floor_color=(0.02, 0.025, 0.03, 1), haze=0.02):
    W.reset()
    W.world(fog_density=haze, fog_color=(0.5, 0.58, 0.62))
    fl = W.mat('floor', floor_color, rough=0.32, metal=0.0, spec=0.6)
    W.obj_from('primitive_plane_add', 'floor', fl, size=80)


def spot(name, loc, rot, energy=1500, color=(1, 0.95, 0.88), size=40, blend=0.5, soft=0.4):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = energy
    ld.color = color
    ld.spot_size = math.radians(size)
    ld.spot_blend = blend
    ld.shadow_soft_size = soft
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = rot
    return lo


def aim(obj, target):
    from mathutils import Vector
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def text3d(body, loc, size=0.5, extrude=0.02, mtl=None, font='Pretendard-Bold.otf', align='CENTER', rot=(math.pi / 2, 0, 0)):
    fp = os.path.join(HERE, '..', 'compositor', 'public', 'fonts', font)
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = body
    cu.font = bpy.data.fonts.load(os.path.abspath(fp))
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = 'CENTER'
    o = bpy.data.objects.new('txt', cu)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    if mtl:
        cu.materials.append(mtl)
    return o


# ------------------------------------------------------------------ shots
def SH_hood(n):
    """Q01: over-the-hood, headlights in fog, B standing ahead. Slow push."""
    h = lot()
    stance_rest(h['B'], 1)
    cam, tgt = W.camera(lens=40, dof_dist=True, fstop=2.2)
    cam.data.lens = 50
    cam_path(cam, tgt, n, [(0, (-2.9, 1.25, 1.18), (1.75, -0.25, 1.0)), (1, (-2.45, 1.12, 1.14), (1.75, -0.2, 1.02))])


def SH_beams(n):
    """Q02: from behind/beside B toward glaring headlights; slow lateral track."""
    h = lot()
    stance_stop(h['B'], 1)
    cam, tgt = W.camera(lens=50, dof_dist=True, fstop=2.8)
    cam_path(cam, tgt, n, [(0, (4.6, -1.7, 1.45), (-0.5, 0.2, 0.95)), (1, (4.6, -0.6, 1.4), (-0.5, 0.15, 0.95))])


def SH_aerial(n, a0=-120):
    """Q03/Q13/Q37: high slow orbit over the concept lot (background plate)."""
    lot()
    cam, tgt = W.camera(lens=28, dof_dist=None)
    keys = []
    for i in range(5):
        t = i / 4
        a = math.radians(a0 + 40 * t)
        keys.append((t, (math.cos(a) * 17 - 1, math.sin(a) * 17, 14 - 1.5 * t), (-0.5, 0, 0)))
    cam_path(cam, tgt, n, keys)


def SH_topdown(n):
    """Q08: crane from oblique to overhead concept plan."""
    lot()
    cam, tgt = W.camera(lens=30)
    cam_path(cam, tgt, n, [(0, (10, -12, 6), (-0.5, 0, 0.5)), (0.75, (-0.6, -0.4, 24), (-0.5, 0, 0)), (1, (-0.6, -0.39, 25), (-0.5, 0, 0))])


def SH_block(n):
    """Q09: B steps in front of the car and raises a hand. Medium-wide side view."""
    h = lot()
    B = h['B']
    B['root'].location = (3.6, -1.8, 0)
    W.key(B['root'], 1, location=(3.6, -1.8, 0))
    W.key(B['root'], int(n * 0.45), location=(1.75, 0.0, 0))
    stance_rest(B, 1)
    stance_rest(B, int(n * 0.45))
    stance_stop(B, int(n * 0.6))
    cam, tgt = W.camera(lens=35, dof_dist=True, fstop=4)
    cam_path(cam, tgt, n, [(0, (1.2, -5.6, 1.6), (0.4, 0, 0.95)), (1, (0.8, -5.0, 1.55), (0.2, 0, 0.95))])


def SH_push(n):
    """Q10: car creeps forward twice; B steps back; cut happens in edit before contact.
    The plate ends with B seated on the ground after a hold (contact not shown: the
    edit hides 0.42n–0.62n behind a graphic wipe)."""
    h = lot()
    car, B = h['car'], h['B']
    stance_stop(B, 1)
    W.key(car, 1, location=(-3.0, 0, 0))
    W.key(car, int(n * 0.18), location=(-3.0, 0, 0))
    W.key(car, int(n * 0.30), location=(-2.2, 0, 0))
    W.key(B['root'], int(n * 0.24), location=(1.75, 0, 0))
    W.key(B['root'], int(n * 0.34), location=(2.35, 0, 0))
    b_lean_back(B, int(n * 0.24), 0)
    b_lean_back(B, int(n * 0.32), 10)
    W.key(car, int(n * 0.40), location=(-2.2, 0, 0))
    W.key(car, int(n * 0.52), location=(-1.5, 0, 0))
    b_standing(B, int(n * 0.44))
    b_fallen(B, int(n * 0.62))
    W.key(B['root'], int(n * 0.62), location=(3.2, 0, 0))
    W.key(car, n, location=(-1.5, 0, 0))
    cam, tgt = W.camera(lens=32, dof_dist=True, fstop=4)
    cam_path(cam, tgt, n, [(0, (1.0, -5.8, 1.8), (0.4, 0, 0.85)), (1, (1.4, -5.3, 1.7), (1.0, 0, 0.7))])


def SH_dispute(n):
    """Q11: same space, defendant's account rendered as a translucent ghost layer:
    a figure moving toward the car. Clearly a claim; composited at low opacity."""
    h = lot()
    B = h['B']
    ghost = W.mat('ghost', (0.6, 0.85, 0.9, 1), rough=0.4, emit=(0.4, 0.8, 0.85), strength=0.6, alpha=0.35)
    for o in bpy.data.objects:
        if o.name.startswith('B_') and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(ghost)
    W.key(B['root'], 1, location=(3.2, 0.0, 0))
    W.key(B['root'], int(n * 0.55), location=(1.5, 0.0, 0))
    W.key(B['root'], n, location=(1.5, 0.0, 0))
    stance_rest(B, 1)
    cam, tgt = W.camera(lens=32, dof_dist=True, fstop=4)
    cam_path(cam, tgt, n, [(0, (0.9, -5.8, 1.8), (0.4, 0, 0.9)), (1, (0.6, -5.3, 1.7), (0.4, 0, 0.9))])


def SH_reverse(n):
    """Q12: car reverses (reverse lamps), pauses, then moves forward again. B is
    seated/rising ahead. Edit cuts away before the car reaches B."""
    h = lot()
    car, B = h['car'], h['B']
    B['root'].location = (2.6, 0, 0)
    b_fallen(B, 1)
    b_fallen(B, int(n * 0.35))
    b_standing(B, int(n * 0.6))
    W.key(car, 1, location=(-1.5, 0, 0))
    W.key(car, int(n * 0.12), location=(-1.5, 0, 0))
    W.key(car, int(n * 0.40), location=(-5.0, 0, 0))
    W.key(car, int(n * 0.55), location=(-5.0, 0, 0))
    W.key(car, int(n * 0.80), location=(-1.2, 0, 0))
    W.key(car, n, location=(-1.2, 0, 0))
    rv = W.mat('reverse', (0.9, 0.9, 0.9, 1), emit=(1, 1, 1), strength=0)
    for sy in (0.35, -0.35):
        o = W.obj_from('primitive_cube_add', 'rev', rv, size=1, location=(-2.37, sy, 0.68))
        o.scale = (0.03, 0.14, 0.05)
        o.parent = car
    for f, s in ((1, 0), (int(n * 0.10), 0), (int(n * 0.12), 25), (int(n * 0.55), 25), (int(n * 0.57), 0)):
        rv.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = s
        rv.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    cam, tgt = W.camera(lens=28, dof_dist=True, fstop=4)
    cam_path(cam, tgt, n, [(0, (-0.6, -6.6, 2.3), (-1.4, 0, 0.8)), (1, (-0.2, -6.2, 2.2), (-0.6, 0, 0.8))])


def SH_people(n):
    """Q06/Q07: two neutral clay figures in a dark studio under soft spots, slow arc."""
    void_studio()
    a = W.mat('clay_a', W.PAL['clay_a'], rough=0.65)
    b = W.mat('clay_b', W.PAL['clay_b'], rough=0.65)
    A = W.mannequin('A', a, loc=(-1.6, 0, 0), rot_z=0, height=1.66)
    B = W.mannequin('B', b, loc=(1.6, 0, 0), rot_z=0)
    for J in (A, B):
        stance_rest(J, 1)
    spot('kA', (-1.6, -1.2, 5.5), (0, 0, 0), energy=900, size=34)
    spot('kB', (1.6, -1.2, 5.5), (0, 0, 0), energy=900, size=34)
    for o in bpy.data.objects:
        if o.name in ('kA', 'kB'):
            aim(o, (o.location.x, 0, 0.9))
    rim = spot('rim', (0, 4, 3.5), (0, 0, 0), energy=1200, color=W.PAL['teal'], size=70)
    aim(rim, (0, 0, 1.2))
    cam, tgt = W.camera(lens=45, dof_dist=True, fstop=5.6)
    cam_path(cam, tgt, n, [(0, (-1.2, -8.5, 1.55), (0, 0, 1.0)), (1, (1.2, -8.3, 1.5), (0, 0, 1.0))])


def SH_court(n, push=0.8, height=1.3, preset='far'):
    """Q14-18, Q24-26, Q29-31: abstract courtroom — an empty raised bench under one
    light. No judge figure, no gavel. Slow push toward the bench."""
    void_studio(floor_color=(0.025, 0.022, 0.02, 1), haze=0.03)
    wood = W.mat('bench', (0.05, 0.035, 0.025, 1), rough=0.45)
    bench = W.obj_from('primitive_cube_add', 'bench', wood, size=1, location=(0, 4, 0.75))
    bench.scale = (5.5, 1.2, 1.5)
    W.bevel(bench, 0.03, 2)
    top = W.obj_from('primitive_cube_add', 'bench_top', wood, size=1, location=(0, 3.85, 1.52))
    top.scale = (5.8, 1.5, 0.06)
    back = W.obj_from('primitive_cube_add', 'wall', W.mat('wall', (0.03, 0.035, 0.04, 1), rough=0.8), size=1, location=(0, 6.5, 4))
    back.scale = (16, 0.2, 8)
    for x in (-4.5, 4.5):
        p = W.obj_from('primitive_cube_add', 'panel', W.mat('panel', (0.045, 0.04, 0.035, 1), rough=0.5), size=1, location=(x, 6.35, 3))
        p.scale = (2.2, 0.1, 5)
    for x in (-2.6, 2.6):
        tb = W.obj_from('primitive_cube_add', 'counsel', wood, size=1, location=(x, -0.4, 0.4))
        tb.scale = (2.2, 0.9, 0.8)
        W.bevel(tb, 0.02, 2)
    chair = W.obj_from('primitive_cube_add', 'chair', W.mat('chair', (0.02, 0.02, 0.022, 1), rough=0.6), size=1, location=(0, 5.0, 2.0))
    chair.scale = (0.8, 0.2, 1.4)
    k = spot('key', (0, 0.5, 6.5), (0, 0, 0), energy=9000, color=(1.0, 0.86, 0.66), size=55, blend=0.7)
    aim(k, (0, 4, 1.2))
    r = spot('rim', (-6, 1, 5), (0, 0, 0), energy=4000, color=W.PAL['teal'], size=60)
    aim(r, (0, 4, 1.5))
    cam, tgt = W.camera(lens=35, dof_dist=True, fstop=4)
    if preset == 'far':
        cam_path(cam, tgt, n, [(0, (0, -7.5, height), (0, 4, 1.6)), (1, (0, -7.5 + push * 4, height), (0, 4, 1.6))])
    elif preset == 'side':
        cam_path(cam, tgt, n, [(0, (-7.0, -3.5, 1.7), (0, 4, 1.4)), (1, (-5.6, -3.9, 1.6), (0, 4, 1.4))])
    elif preset == 'verdict':
        cam.data.lens = 40
        cam_path(cam, tgt, n, [(0, (0, -6.0, 1.15), (0, 4, 1.9)), (1, (0, -5.7, 1.15), (0, 4, 1.9))])
    elif preset == 'high':
        cam_path(cam, tgt, n, [(0, (3.5, -5.5, 5.5), (0, 3.5, 1.0)), (1, (1.5, -5.0, 5.2), (0, 3.5, 1.0))])


def SH_cctv(n):
    """Q19/Q20: the lot's CCTV unit as an evidence object (no footage is shown)."""
    lot()
    cam, tgt = W.camera(lens=60, dof_dist=True, fstop=2.0)
    cam_path(cam, tgt, n, [(0, (-6.6, -5.6, 3.3), (-7.9, -3.6, 3.9)), (1, (-6.9, -5.2, 3.6), (-7.9, -3.6, 3.95))])


def SH_folder(n):
    """Q22: closed medical-record folder on a dark table, top light. Not readable."""
    void_studio(floor_color=(0.018, 0.02, 0.024, 1), haze=0.015)
    table = W.obj_from('primitive_cube_add', 'table', W.mat('table', (0.03, 0.028, 0.026, 1), rough=0.35), size=1, location=(0, 0, 0.75))
    table.scale = (3, 2, 0.06)
    paper = W.mat('folder', (0.42, 0.40, 0.36, 1), rough=0.7)
    f1 = W.obj_from('primitive_cube_add', 'folder', paper, size=1, location=(0, 0, 0.8))
    f1.scale = (0.32, 0.44, 0.012)
    f1.rotation_euler = (0, 0, math.radians(-8))
    tab = W.obj_from('primitive_cube_add', 'tab', W.mat('tab', W.PAL['teal'] + (1,), rough=0.6), size=1, location=(0.17, 0.2, 0.808))
    tab.scale = (0.06, 0.03, 0.004)
    tab.rotation_euler = (0, 0, math.radians(-8))
    k = spot('key', (0.3, -0.6, 3.2), (0, 0, 0), energy=600, size=30, blend=0.8)
    aim(k, (0, 0, 0.8))
    cam, tgt = W.camera(lens=50, dof_dist=True, fstop=2.8)
    cam_path(cam, tgt, n, [(0, (0.0, -1.6, 1.75), (0, 0, 0.8)), (1, (0.05, -1.25, 1.55), (0, 0.02, 0.8))])


def SH_table(n):
    """Q27/Q28: two pools of light on a dark table — left and right card zones."""
    void_studio(floor_color=(0.018, 0.02, 0.024, 1), haze=0.01)
    table = W.obj_from('primitive_cube_add', 'table', W.mat('table', (0.035, 0.032, 0.03, 1), rough=0.3), size=1, location=(0, 0, 0.75))
    table.scale = (5, 3, 0.06)
    for x, c in ((-1.1, (0.9, 0.9, 0.95)), (1.1, (1.0, 0.85, 0.6))):
        s = spot('pool', (x, 0, 3.5), (0, 0, 0), energy=500, color=c, size=34, blend=0.6)
        aim(s, (x, 0, 0.78))
    cam, tgt = W.camera(lens=35)
    cam_path(cam, tgt, n, [(0, (0, -0.01, 4.4), (0, 0, 0.78)), (1, (0, -0.01, 4.1), (0, 0, 0.78))])


def SH_map(n):
    """Q05: extruded Korea outline (Natural Earth, public domain) with a pin at Daegu."""
    void_studio(floor_color=(0.014, 0.018, 0.024, 1), haze=0.0)
    g = json.load(open(os.path.join(HERE, 'data', 'kor_ne50m.geojson')))
    lon0, lat0 = 127.8, 36.3
    kx = math.cos(math.radians(lat0)) * 1.11
    land = W.mat('land', (0.06, 0.09, 0.11, 1), rough=0.5, emit=(0.09, 0.49, 0.53), strength=0.05)
    import bmesh
    for k, poly in enumerate(g['geometry']['coordinates']):
        ring = poly[0]
        me = bpy.data.meshes.new(f'kor{k}')
        bm = bmesh.new()
        vs = [bm.verts.new(((x - lon0) * kx, (y - lat0) * 1.11, 0)) for x, y in ring[:-1]]
        if len(vs) < 3:
            bm.free(); continue
        f = bm.faces.new(vs)
        bmesh.ops.triangulate(bm, faces=[f])
        ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]:
            v.co.z += 0.12
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(f'kor{k}', me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(land)
    for nm, lon, lat in (('ulleung', 130.87, 37.49), ('dokdo', 131.87, 37.24)):
        o = W.obj_from('primitive_cylinder_add', nm, land, radius=0.04 if nm == 'ulleung' else 0.02, depth=0.12,
                       location=((lon - lon0) * kx, (lat - lat0) * 1.11, 0.06))
    dx, dy = (128.60 - lon0) * kx, (35.87 - lat0) * 1.11
    pin = W.mat('pin', (1, 0.7, 0.3, 1), emit=W.PAL['amber'], strength=5)
    W.obj_from('primitive_uv_sphere_add', 'pin', pin, radius=0.07, location=(dx, dy, 0.22))
    ld = bpy.data.lights.new('pinl', 'POINT'); ld.energy = 12; ld.color = W.PAL['amber']
    lo = bpy.data.objects.new('pinl', ld); bpy.context.collection.objects.link(lo); lo.location = (dx, dy, 0.5)
    k = spot('key', (-2, -4, 9), (0, 0, 0), energy=1800, color=(0.8, 0.9, 1.0), size=60, blend=0.8)
    aim(k, (0, 0, 0))
    cam, tgt = W.camera(lens=50, dof_dist=True, fstop=8)
    cam_path(cam, tgt, n, [(0, (0.2, -5.4, 7.2), (0.1, 0.0, 0)), (1, (dx * 0.6, dy - 3.2, 4.6), (dx * 0.7, dy + 0.2, 0.1))])


def SH_ident(n):
    """Q04: series ident — own Korean logotype, light sweep. 4 s."""
    void_studio(floor_color=(0.01, 0.012, 0.015, 1), haze=0.0)
    face = W.mat('logo', (0.85, 0.82, 0.76, 1), rough=0.3, metal=0.7)
    text3d('판결의 이유', (0, 0, 1.0), size=0.9, extrude=0.06, mtl=face)
    sweep = spot('sweep', (-5, -3, 3), (0, 0, 0), energy=3500, color=(1, 0.92, 0.8), size=22, blend=0.4)
    W.key(sweep, 1, location=(-5, -3, 3))
    W.key(sweep, n, location=(5, -3, 3))
    tgt_s = bpy.data.objects.new('st', None); bpy.context.collection.objects.link(tgt_s); tgt_s.location = (0, 0, 1)
    c = sweep.constraints.new('TRACK_TO'); c.target = tgt_s; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    fill = spot('fill', (0, -4, 1.0), (0, 0, 0), energy=60, color=W.PAL['teal'], size=80)
    aim(fill, (0, 0, 1))
    cam, tgt = W.camera(lens=50, dof_dist=True, fstop=5.6)
    cam_path(cam, tgt, n, [(0, (0, -6.2, 1.05), (0, 0, 1.0)), (1, (0, -5.6, 1.02), (0, 0, 1.0))])


def SH_reread(n):
    """Q32/Q33: the same lot re-read from overhead-oblique; car path ghosted."""
    h = lot()
    car, B = h['car'], h['B']
    W.key(car, 1, location=(-3.0, 0, 0))
    W.key(car, int(n * 0.35), location=(-2.2, 0, 0))
    W.key(car, int(n * 0.55), location=(-1.5, 0, 0))
    W.key(car, int(n * 0.70), location=(-5.0, 0, 0))
    W.key(car, n, location=(-1.2, 0, 0))
    stance_stop(B, 1)
    cam, tgt = W.camera(lens=30)
    cam_path(cam, tgt, n, [(0, (6, -9, 9), (-1.5, 0, 0.3)), (1, (4, -10, 8), (-1.5, 0, 0.3))])


SHOTS = {
    'hood': SH_hood, 'beams': SH_beams, 'aerial': SH_aerial, 'topdown': SH_topdown,
    'block': SH_block, 'push': SH_push, 'dispute': SH_dispute, 'reverse': SH_reverse,
    'people': SH_people, 'court': SH_court, 'court_low': lambda n: SH_court(n, push=0.5, height=0.9),
    'court_side': lambda n: SH_court(n, preset='side'), 'court_verdict': lambda n: SH_court(n, preset='verdict'),
    'court_high': lambda n: SH_court(n, preset='high'),
    'cctv': SH_cctv, 'folder': SH_folder, 'table': SH_table, 'map': SH_map, 'ident': SH_ident,
    'reread': SH_reread, 'aerial2': lambda n: SH_aerial(n, a0=-30), 'aerial3': lambda n: SH_aerial(n, a0=60),
}


def main():
    sid, n, out, preview = args()
    SHOTS[sid](n)
    W.ease_all()
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, n
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.compression = 15
    if preview:
        s.render.resolution_percentage = 50
        s.eevee.taa_render_samples = 16
    else:
        s.eevee.volumetric_tile_size = '4'
        s.eevee.volumetric_samples = 64
        s.eevee.taa_render_samples = 24
    os.makedirs(out, exist_ok=True)
    still = [a for a in sys.argv if a.startswith('--still=')]
    if still:
        for fr in still[0].split('=')[1].split(','):
            s.frame_set(int(fr))
            s.render.filepath = os.path.join(out, f'{sid}_{int(fr):04d}.png')
            bpy.ops.render.render(write_still=True)
        return
    s.render.filepath = os.path.join(out, 'f_')
    bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
