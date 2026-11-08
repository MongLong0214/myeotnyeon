"""EP001 shots v2 (realistic set). Usage:
  Blender --background --factory-startup --python-exit-code 1 --python shots2.py -- SHOT N OUT_DIR [--still=F,..] [--step=2] [--preview]

--step=2 renders every 2nd frame (for slow camera moves; the encoder interpolates to 30 fps).
Action follows the court-found facts only: B stands in front of the car to stop it, the car
pushes B over several times, reverses and drives into B once. Contact is never shown on screen
(the edit covers it), and nothing is depicted that the record does not contain.
"""
import sys, os, math, json, random
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world2 as W
import people as P

CAR_X = -3.0          # hero car centre (front faces +X)
CAR_FRONT = CAR_X + 4.89 / 2
B_X = CAR_FRONT + 1.15


def args():
    a = sys.argv[sys.argv.index('--') + 1:]
    opts = {k[2:].split('=')[0]: (k.split('=')[1] if '=' in k else True) for k in a if k.startswith('--')}
    pos = [x for x in a if not x.startswith('--')]
    return pos[0], int(pos[1]), pos[2], opts


def cam(lens=35, fstop=None):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.sensor_width = 36
    co = bpy.data.objects.new('cam', cd); bpy.context.scene.collection.objects.link(co)
    tgt = bpy.data.objects.new('cam_tgt', None); bpy.context.scene.collection.objects.link(tgt)
    c = co.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    if fstop:
        cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = co
    return co, tgt


def path(co, tgt, n, keys):
    for t, cl, tl in keys:
        f = 1 + round(t * (n - 1))
        co.location = cl; co.keyframe_insert('location', frame=f)
        tgt.location = tl; tgt.keyframe_insert('location', frame=f)


def key_loc(o, f, loc):
    o.location = loc; o.keyframe_insert('location', frame=f)


def lot(parked=True, hero_lights=True):
    W.reset()
    W.build_lot()
    if parked:
        W.parked_cars(skip={('S', 8), ('S', 9), ('N', 8), ('N', 9)})
    car = W.car('accord_2019', (CAR_X, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=hero_lights, tag='car_A')
    A = P.load('A', 'figA'); TA = P.add_ik(A)
    A.parent = car
    A.location = (-0.30, 0.37, 0.0); A.rotation_euler = (0, 0, math.radians(90))     # driver seat (left), facing +X
    P.ik_pose(A, TA, 'drive')
    B = P.load('B', 'figB'); TB = P.add_ik(B)
    P.place(B, (B_X, 0.0, 0), -90)           # faces -X (toward the car)
    P.ik_pose(B, TB, 'stand')
    return car, A, TA, B, TB


def walk(B, TB, f0, f1, start, end, yaw=None, step=0.62):
    """Simple planted-foot walk with IK targets (rig space), root moves start→end."""
    n = f1 - f0
    d = Vector(end) - Vector(start)
    if yaw is None:
        yaw = math.degrees(math.atan2(d.x, -d.y))
    dist = (Vector(end) - Vector(start)).length
    steps = max(2, int(dist / step))
    P.place(B, start, yaw, frame=f0)
    for k in range(steps + 1):
        f = f0 + round(k * n / steps)
        p = Vector(start).lerp(Vector(end), k / steps)
        B.location = p; B.keyframe_insert('location', frame=f)
        side = 'L' if k % 2 == 0 else 'R'
        other = 'R' if side == 'L' else 'L'
        sx = 1 if side == 'L' else -1
        TB[f'foot{side}'].location = (0.1 * sx, -0.18, 0.12); TB[f'foot{side}'].keyframe_insert('location', frame=f)
        TB[f'foot{other}'].location = (-0.1 * sx, 0.18, 0.09); TB[f'foot{other}'].keyframe_insert('location', frame=f)
        TB[f'hand{side}'].location = (0.2 * sx, 0.1, 0.85); TB[f'hand{side}'].keyframe_insert('location', frame=f)
        TB[f'hand{other}'].location = (-0.2 * sx, -0.12, 0.86); TB[f'hand{other}'].keyframe_insert('location', frame=f)
        for e in ('elbowL', 'elbowR'):
            TB[e].location = (0.3 if e[-1] == 'L' else -0.3, 0.5, 1.0); TB[e].keyframe_insert('location', frame=f)
    B.rotation_euler = (0, 0, math.radians(yaw)); B.keyframe_insert('rotation_euler', frame=f1)


# ---------------------------------------------------------------- shots
def SH01(n):
    """Q01 hood: low over-the-hood view, B in the headlight beams. Slow push."""
    car, A, TA, B, TB = lot()
    # over the hood from just ahead of the windscreen (hood top ~0.95 m there); the earlier
    # camera beside the door put the wing mirror, faceted at that range, across the frame
    co, tgt = cam(28, 6.0)
    path(co, tgt, n, [(0, (CAR_X + 1.22, 0.40, 1.16), (B_X, -0.05, 0.98)), (1, (CAR_X + 1.40, 0.33, 1.15), (B_X, -0.03, 0.98))])


def SH02(n):
    """Q02 beams: from behind B toward the glare; B with one hand raised."""
    car, A, TA, B, TB = lot()
    P.ik_pose(B, TB, 'stop')
    co, tgt = cam(55, 2.8)
    path(co, tgt, n, [(0, (B_X + 3.2, -1.6, 1.5), (CAR_FRONT - 0.5, 0.25, 1.0)), (1, (B_X + 3.0, -0.7, 1.45), (CAR_FRONT - 0.5, 0.2, 1.0))])


def SH03(n, a0=-125):
    """Q03 aerial orbit (background plate for the question)."""
    car, A, TA, B, TB = lot()
    co, tgt = cam(30)
    keys = []
    for i in range(5):
        t = i / 4; a = math.radians(a0 + 35 * t)
        keys.append((t, (math.cos(a) * 19 + CAR_X, math.sin(a) * 19, 15 - 1.5 * t), (CAR_X + 1.5, 0, 0)))
    path(co, tgt, n, keys)


def SH07(n):
    """Q08 crane from oblique to overhead (concept plan overlay goes on top)."""
    car, A, TA, B, TB = lot()
    co, tgt = cam(30)
    path(co, tgt, n, [(0, (10, -12, 6), (CAR_X + 2, 0, 0.5)), (0.8, (CAR_X + 2.0, -0.4, 26), (CAR_X + 2, 0, 0)), (1, (CAR_X + 2.0, -0.39, 27), (CAR_X + 2, 0, 0))])


def SH08(n):
    """Q09 B walks in front of the car and raises a hand. Side view."""
    car, A, TA, B, TB = lot()
    walk(B, TB, 1, int(n * 0.45), (B_X + 1.6, -2.4, 0), (B_X, 0.0, 0))
    P.ik_pose(B, TB, 'stand', frame=int(n * 0.48))
    B.rotation_euler = (0, 0, math.radians(-90)); B.keyframe_insert('rotation_euler', frame=int(n * 0.5))
    P.ik_pose(B, TB, 'stop', frame=int(n * 0.62))
    co, tgt = cam(35, 4)
    path(co, tgt, n, [(0, (B_X - 1.0, -6.0, 1.6), (B_X - 1.2, 0, 1.0)), (1, (B_X - 1.4, -5.4, 1.55), (B_X - 1.6, 0, 1.0))])


def SH09(n):
    """Q10 the car creeps forward twice; B is pushed back and ends seated on the ground.
    The edit covers 0.40n–0.66n with an 'omitted' card, so the fall itself is not shown."""
    car, A, TA, B, TB = lot()
    P.ik_pose(B, TB, 'stop', frame=1)
    key_loc(car, 1, (CAR_X, 0, 0)); key_loc(car, int(n * .16), (CAR_X, 0, 0)); key_loc(car, int(n * .30), (CAR_X + 0.7, 0, 0))
    key_loc(B, int(n * .22), (B_X, 0, 0)); key_loc(B, int(n * .34), (B_X + 0.55, 0, 0))
    P.ik_pose(B, TB, 'step_back', frame=int(n * .30))
    key_loc(car, int(n * .40), (CAR_X + 0.7, 0, 0)); key_loc(car, int(n * .52), (CAR_X + 1.3, 0, 0))
    key_loc(B, int(n * .44), (B_X + 0.6, 0, 0)); key_loc(B, int(n * .62), (B_X + 1.35, 0, 0))
    P.ik_pose(B, TB, 'step_back', frame=int(n * .44))
    P.ik_pose(B, TB, 'ground', frame=int(n * .62))
    key_loc(car, n, (CAR_X + 1.3, 0, 0))
    co, tgt = cam(32, 4)
    path(co, tgt, n, [(0, (B_X - 0.6, -6.2, 1.7), (B_X - 0.8, 0, 0.9)), (1, (B_X - 0.1, -5.6, 1.6), (B_X, 0, 0.7))])


def SH10(n, ghost=True):
    """Q11 the defence account as a translucent layer: a figure moving toward the car."""
    car, A, TA, B, TB = lot()
    gm = W.mat('ghost', (0.55, 0.85, 0.9), rough=0.3, emit=(0.35, 0.75, 0.82), strength=0.8, alpha=0.32)
    for o in bpy.data.objects:
        if o.name.startswith('figB_') and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(gm)
    for o in bpy.data.objects:
        if o.name.startswith('figB_') and o.type == 'MESH':
            for m in o.modifiers:
                pass
    walk(B, TB, 1, int(n * 0.55), (B_X + 2.2, 0.0, 0), (B_X - 0.2, 0.0, 0))
    P.ik_pose(B, TB, 'stand', frame=int(n * 0.6))
    co, tgt = cam(32, 4)
    path(co, tgt, n, [(0, (B_X - 0.4, -6.2, 1.7), (B_X - 0.6, 0, 0.9)), (1, (B_X - 0.7, -5.7, 1.6), (B_X - 0.8, 0, 0.9))])


def SH11(n):
    """Q12 the car reverses (reverse lamps), stops, drives forward again. B seated → rising.
    The edit cuts away before the car reaches B."""
    car, A, TA, B, TB = lot()
    P.place(B, (B_X + 1.35, 0, 0), -90)
    P.ik_pose(B, TB, 'ground', frame=1); P.ik_pose(B, TB, 'ground', frame=int(n * .35))
    P.ik_pose(B, TB, 'step_back', frame=int(n * .62))
    key_loc(car, 1, (CAR_X + 1.3, 0, 0)); key_loc(car, int(n * .12), (CAR_X + 1.3, 0, 0))
    key_loc(car, int(n * .40), (CAR_X - 2.2, 0, 0)); key_loc(car, int(n * .55), (CAR_X - 2.2, 0, 0))
    key_loc(car, int(n * .80), (CAR_X + 1.6, 0, 0)); key_loc(car, n, (CAR_X + 1.6, 0, 0))
    rv = W.mat('reverse_lamp', (0.9, 0.9, 0.9), emit=(1, 1, 1), strength=0)
    for sy in (0.45, -0.45):
        o = W.box('rev', (0.02, 0.12, 0.05), (CAR_X - 2.44, sy, 0.72), rv); o.parent = car
        o.location = (-2.44, sy, 0.72)
    bsdf = rv.node_tree.nodes['Principled BSDF']
    for f, s in ((1, 0), (int(n * .10), 0), (int(n * .12), 30), (int(n * .55), 30), (int(n * .57), 0)):
        bsdf.inputs['Emission Strength'].default_value = s; bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    co, tgt = cam(28, 4)
    path(co, tgt, n, [(0, (CAR_X + 2.0, -7.0, 2.3), (CAR_X + 0.5, 0, 0.8)), (1, (CAR_X + 2.6, -6.6, 2.2), (CAR_X + 1.5, 0, 0.8))])


def SH15(n):
    """Q19 the lot's CCTV unit as an evidence object (no footage)."""
    lot()
    co, tgt = cam(70, 2.0)
    bpy.context.view_layer.update()
    m = next(o for o in bpy.data.objects if o.name.startswith('security_camera_01') and o.type == 'MESH' and o.parent and 'cctv' in o.parent.name)
    pts = [m.matrix_world @ Vector(c) for c in m.bound_box]
    hc = sum(pts, Vector()) / 8          # aim at the housing, not the pole axis
    cx, cy = -8.5, W.ROW_S_Y - W.STALL_D - 0.6
    path(co, tgt, n, [(0, (cx + 1.6, cy - 1.6, 3.6), (hc.x, hc.y, hc.z)), (1, (cx + 1.3, cy - 1.9, 3.85), (hc.x, hc.y, hc.z))])


def SH22(n):
    """Q32 re-reading the same scene from high-oblique: the car's path, B's position."""
    car, A, TA, B, TB = lot()
    P.ik_pose(B, TB, 'stop')
    key_loc(car, 1, (CAR_X, 0, 0)); key_loc(car, int(n * .3), (CAR_X + 0.7, 0, 0)); key_loc(car, int(n * .45), (CAR_X + 1.3, 0, 0))
    key_loc(car, int(n * .65), (CAR_X - 2.2, 0, 0)); key_loc(car, n, (CAR_X + 1.0, 0, 0))
    co, tgt = cam(30)
    path(co, tgt, n, [(0, (8, -10, 10), (CAR_X + 1, 0, 0.3)), (1, (6, -11, 9), (CAR_X + 1, 0, 0.3))])


# ---------------------------------------------------------------- interiors
def desk_props(x, y, top, facing=1, folder=True):
    """A flat monitor (back to the gallery), a gooseneck microphone and a closed folder.
    facing=+1: the seated person is on the +Y side."""
    plastic = bpy.data.materials.get('mon_plastic') or W.mat('mon_plastic', (0.018, 0.018, 0.02), rough=0.42)
    screen = bpy.data.materials.get('mon_screen') or W.mat('mon_screen', (0.006, 0.007, 0.009), rough=0.12)
    metal = bpy.data.materials.get('mic_metal') or W.mat('mic_metal', (0.05, 0.05, 0.055), rough=0.3, metal=0.9)
    f = facing
    mx = x + 0.55        # beside the seat, so the chair stays visible from straight ahead
    W.box('mon_base', (0.22, 0.17, 0.012), (mx, y, top + 0.006), plastic, bevel=0.004)
    W.box('mon_neck', (0.05, 0.025, 0.2), (mx, y - 0.03 * f, top + 0.1), plastic, bevel=0.006)
    W.box('mon_body', (0.56, 0.03, 0.34), (mx, y - 0.01 * f, top + 0.31), plastic, bevel=0.006)
    W.box('mon_panel', (0.535, 0.004, 0.315), (mx, y + 0.006 * f, top + 0.31), screen)
    # gooseneck: base puck, arc rising and bending toward the speaker, capsule
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=0.055, radius2=0.05, depth=0.025)
    me = bpy.data.meshes.new('mic_base'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('mic_base', me); bpy.context.scene.collection.objects.link(o); o.location = (x - 0.38, y, top + 0.0125)
    me.materials.append(plastic)
    for poly in me.polygons:
        poly.use_smooth = True
    cu = bpy.data.curves.new('mic_arm', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0045; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); pts = []
    for i in range(13):
        t = i / 12; a = t * math.radians(70)
        pts.append((x - 0.38, y + f * 0.2 * (1 - math.cos(a)), top + 0.025 + 0.36 * math.sin(a) / math.sin(math.radians(70)) * (0.55 + 0.45 * t)))
    sp.points.add(len(pts) - 1)
    for pt, c in zip(sp.points, pts):
        pt.co = (*c, 1)
    arm = bpy.data.objects.new('mic_arm', cu); bpy.context.scene.collection.objects.link(arm); cu.materials.append(metal)
    end, prev = Vector(pts[-1]), Vector(pts[-2]); d = (end - prev).normalized()
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.011, radius2=0.013, depth=0.07)
    me = bpy.data.meshes.new('mic_cap'); bm.to_mesh(me); bm.free()
    cap = bpy.data.objects.new('mic_cap', me); bpy.context.scene.collection.objects.link(cap)
    cap.location = end + d * 0.035; cap.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); me.materials.append(plastic)
    for poly in me.polygons:
        poly.use_smooth = True
    if folder:
        fm = bpy.data.materials.get('folder_navy') or W.mat('folder_navy', (0.03, 0.045, 0.08), rough=0.55)
        W.box('folder', (0.32, 0.24, 0.018), (x + 0.02, y + 0.05 * f, top + 0.009), fm, bevel=0.003).rotation_euler = (0, 0, math.radians(4))


JUDGE_CHAIR_YAW = 0.0     # model front faces -Y at yaw 0 (checked in a test still)


def courtroom():
    """Modern Korean-style courtroom: raised walnut bench with three empty chairs, full-height
    wood panelling, counsel desks, gallery rail, recessed downlights. No judge figure, no gavel."""
    W.reset()
    W.world(hdri='hansaplatz', strength=0.01, haze=0.004, haze_color=(0.62, 0.62, 0.64))
    bpy.context.scene.view_settings.exposure = 0.6
    wood = W.ph_mat('dark_wood', 1.2, box=True, tint=(0.75, 0.62, 0.5))
    panel = W.ph_mat('dark_wood', 1.6, box=True, tint=(0.5, 0.42, 0.36))
    wall = W.ph_mat('plastered_wall_02', 3.0, box=True, tint=(0.55, 0.53, 0.5))
    floor = W.ph_mat('dirty_carpet', 1.5, tint=(0.16, 0.19, 0.24))
    W.plane('floor', (30, 30), (0, 0, 0), floor)
    W.box('back_wall', (18, 0.3, 8), (0, 6.8, 4.0), wall)
    slat = W.ph_mat('american_walnut_veneer', 1.0, box=True, tint=(0.75, 0.6, 0.45))
    for k in range(-27, 28):
        W.box(f'slat{k}', (0.12, 0.08, 5.6), (k * 0.2, 6.6, 2.8), slat)
    W.box('slat_back', (11.2, 0.05, 5.6), (0, 6.66, 2.8), W.mat('slat_gap', (0.02, 0.015, 0.012), rough=0.8))
    wash = W.light('AREA', 'wall_wash', (0, 5.9, 6.0), 900, (1.0, 0.85, 0.66), size=(10.5, 0.3), rot=(math.radians(-35), 0, 0))
    for x in (-9, 9):
        W.box(f'side_wall{x}', (0.3, 20, 8), (x, -2, 4), wall)
        W.box(f'side_panel{x}', (0.12, 20, 2.4), (x - 0.15 * (1 if x > 0 else -1), -2, 1.2), panel)
    W.box('ceiling', (18, 20, 0.2), (0, -2, 6.4), W.mat('ceil', (0.08, 0.08, 0.085), rough=0.9))
    W.box('dais', (11, 3.4, 0.75), (0, 5.0, 0.375), wood)
    # bench proportioned to a seated judge: desk surface 0.78 m above the dais, so the high chair
    # backs show above it from the gallery (the earlier 1.24 m bench hid the chairs entirely)
    W.box('bench', (9.0, 0.95, 0.72), (0, 3.85, 0.75 + 0.36), wood, bevel=0.01)
    W.box('bench_top', (9.3, 1.25, 0.06), (0, 3.95, 0.75 + 0.75), wood, bevel=0.008)
    trim = W.ph_mat('dark_wood', 1.0, box=True, tint=(0.32, 0.25, 0.2))
    W.box('bench_plinth', (9.05, 0.97, 0.1), (0, 3.85, 0.8), trim)
    for k in range(-3, 4):      # raised panel frames on the bench front
        W.box(f'bench_rail{k}', (0.05, 0.03, 0.6), (k * 1.5, 3.365, 1.13), trim, bevel=0.006)
    W.box('bench_rail_top', (9.0, 0.03, 0.05), (0, 3.365, 1.43), trim, bevel=0.006)
    for x in (-2.9, 0, 2.9):
        desk_props(x, 4.2, 1.53, facing=1)
    for x in (-2.9, 0, 2.9):     # empty judges' chairs (CC-BY Sketchfab model, assets/objaverse/props)
        W.glb_prop('chair_exec', 1.3, (x, 5.2, 0.75), yaw=JUDGE_CHAIR_YAW, tag=f'jchair{x}')
    W.box('clerk_desk', (6.0, 0.85, 0.95), (0, 2.5, 0.47), wood, bevel=0.01)
    for x in (-1.4, 1.4):
        desk_props(x, 2.65, 0.945, facing=1, folder=False)
    for x in (-3.6, 3.6):
        W.box(f'counsel{x}', (3.2, 0.95, 0.78), (x, -0.3, 0.39), wood, bevel=0.01)
        for k in (-0.9, 0.9):
            desk_props(x + k, -0.55, 0.78, facing=-1)
        for k in (-0.9, 0.9):
            W.glb_prop('chair_highpoly_office', 1.02, (x + k, -1.05, 0), yaw=JUDGE_CHAIR_YAW + math.pi, tag=f'cchair{x}{k}')
    W.box('rail', (16, 0.1, 0.95), (0, -2.6, 0.47), wood, bevel=0.01)
    for r in range(3):
        W.box(f'gallery{r}', (12, 0.5, 0.45), (0, -4.0 - r * 1.2, 0.45), wood, bevel=0.02)
    i = 0
    for x in (-6, -3, 0, 3, 6):
        for y in (4.2, 1.0, -2.0, -5.0):
            W.light('SPOT', f'down{i}', (x, y, 6.25), 900, (1.0, 0.9, 0.78), spot=75, blend=0.9, soft=0.15).rotation_euler = (0, 0, 0)
            W.box(f'can{i}', (0.22, 0.22, 0.02), (x, y, 6.29), W.mat(f'canm{i}', (1, 1, 1), emit=(1.0, 0.92, 0.82), strength=30))
            i += 1
    k = W.light('SPOT', 'key', (0, -1.0, 6.0), 2200, (1.0, 0.86, 0.68), spot=40, blend=0.85, soft=0.4)
    k.rotation_euler = (Vector((0, 4.2, 1.6)) - k.location).to_track_quat('-Z', 'Y').to_euler()
    r = W.light('SPOT', 'rim', (-7, 3, 5), 900, (0.55, 0.78, 0.85), spot=50, blend=0.8, soft=0.4)
    r.rotation_euler = (Vector((0, 4.5, 1.8)) - r.location).to_track_quat('-Z', 'Y').to_euler()


def COURT(n, preset='far'):
    courtroom()
    co, tgt = cam(35, 4)
    if preset == 'far':
        co.data.lens = 26
        path(co, tgt, n, [(0, (0.9, -7.6, 2.1), (0, 3.5, 1.35)), (1, (0.4, -6.4, 2.0), (0, 3.5, 1.35))])
    elif preset == 'low':
        path(co, tgt, n, [(0, (1.0, -2.0, 0.85), (0, 4, 1.75)), (1, (0.6, -1.0, 0.8), (0, 4, 1.75))])
    elif preset == 'side':
        path(co, tgt, n, [(0, (-7.2, -1.8, 1.8), (0, 4, 1.5)), (1, (-6.2, -2.3, 1.7), (0, 4, 1.5))])
    elif preset == 'verdict':
        co.data.lens = 40
        path(co, tgt, n, [(0, (0, -2.2, 1.35), (0, 4, 1.75)), (1, (0, -1.9, 1.35), (0, 4, 1.75))])
    elif preset == 'high':
        path(co, tgt, n, [(0, (4.0, -4.0, 5.6), (0, 3.0, 1.0)), (1, (2.2, -3.6, 5.3), (0, 3.0, 1.0))])


def records_table(n, what='folder'):
    """Q22/Q23/Q27-28: evidence/records desk — closed records binder, clipboard, top light."""
    W.reset()
    W.world(hdri='hansaplatz', strength=0.015, haze=0.0)
    W.plane('floor', (20, 20), (0, 0, 0), W.ph_mat('concrete_floor_02', 2.0, tint=(0.4, 0.4, 0.42)))
    desk = W.ph_append('metal_office_desk', 'desk'); desk.location = (0, 0, 0)
    b = W.ph_append('binder_notebook', 'binder', keep=['closed']); b.location = (-0.15, -0.05, 0.795); b.rotation_euler = (0, 0, math.radians(-12))
    c = W.ph_append('clipboard', 'clip'); c.location = (0.45, 0.08, 0.795); c.rotation_euler = (0, 0, math.radians(8))
    s = W.ph_append('stationery_supplies', 'stat'); s.location = (0.75, 0.25, 0.79)
    k = W.light('SPOT', 'key', (0.2, -0.6, 2.6), 70, (1.0, 0.92, 0.82), spot=34, blend=0.85, soft=0.3)
    k.rotation_euler = (Vector((0, 0, 0.8)) - k.location).to_track_quat('-Z', 'Y').to_euler()
    W.light('AREA', 'fill', (-2, -2, 2), 40, (0.6, 0.75, 0.85), size=(2, 2), rot=(math.radians(60), 0, math.radians(-45)))
    co, tgt = cam(50, 2.8)
    if what == 'folder':
        path(co, tgt, n, [(0, (0.1, -1.7, 1.75), (0.05, 0.0, 0.8)), (1, (0.12, -1.35, 1.55), (0.05, 0.02, 0.8))])
    else:
        path(co, tgt, n, [(0, (0, -0.02, 3.4), (0, 0, 0.8)), (1, (0, -0.02, 3.1), (0, 0, 0.8))])


def SH06(n):
    """Q06/Q07 the two people as neutral figures in a dark studio (roles introduced by labels)."""
    W.reset()
    W.world(hdri='hansaplatz', strength=0.01, haze=0.01, haze_color=(0.55, 0.62, 0.66))
    W.plane('floor', (40, 40), (0, 0, 0), W.mat('studio_floor', (0.02, 0.022, 0.025), rough=0.25, coat=0.3))
    A = P.load('A', 'figA'); TA = P.add_ik(A); P.place(A, (-1.3, 0, 0), 0); P.ik_pose(A, TA, 'stand')
    B = P.load('B', 'figB'); TB = P.add_ik(B); P.place(B, (1.3, 0, 0), 0); P.ik_pose(B, TB, 'stand')
    for x in (-1.3, 1.3):
        k = W.light('SPOT', f'k{x}', (x * 1.2, -1.6, 5.2), 1100, (1.0, 0.93, 0.85), spot=30, blend=0.7, soft=0.4)
        k.rotation_euler = (Vector((x, 0, 1.0)) - k.location).to_track_quat('-Z', 'Y').to_euler()
    r = W.light('SPOT', 'rim', (0, 4.5, 3.6), 1800, (0.45, 0.78, 0.84), spot=70, blend=0.8, soft=0.5)
    r.rotation_euler = (Vector((0, 0, 1.2)) - r.location).to_track_quat('-Z', 'Y').to_euler()
    co, tgt = cam(45, 4.0)
    path(co, tgt, n, [(0, (-1.4, -7.8, 1.6), (0, 0, 1.05)), (1, (1.4, -7.6, 1.55), (0, 0, 1.05))])


SHOTS = {'SH06': SH06,
    'SH01': SH01, 'SH02': SH02, 'SH03': SH03, 'SH07': SH07, 'SH08': SH08, 'SH09': SH09, 'SH10': SH10,
    'SH11': SH11, 'SH12': lambda n: SH03(n, a0=-40), 'SH15': SH15, 'SH22': SH22, 'SH24': lambda n: SH03(n, a0=55),
    'SH13': lambda n: COURT(n, 'far'), 'SH14': lambda n: COURT(n, 'low'), 'SH19': lambda n: COURT(n, 'side'),
    'SH21': lambda n: COURT(n, 'verdict'), 'SH23': lambda n: COURT(n, 'high'),
    'SH17': lambda n: records_table(n, 'folder'), 'SH18': lambda n: records_table(n, 'top'), 'SH20': lambda n: records_table(n, 'top'),
}


def main():
    sid, n, out, opts = args()
    SHOTS[sid](n)
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, n
    s.frame_step = int(opts.get('step', 1))
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.compression = 15
    if opts.get('preview'):
        s.render.resolution_percentage = 50
        s.eevee.taa_render_samples = 8
    os.makedirs(out, exist_ok=True)
    if 'still' in opts:
        for fr in str(opts['still']).split(','):
            s.frame_set(int(fr))
            s.render.filepath = os.path.join(out, f'{sid}_{int(fr):04d}.png')
            bpy.ops.render.render(write_still=True)
        return
    s.render.filepath = os.path.join(out, 'f_')
    bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
