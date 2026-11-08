"""EP001 shots v3 (light cut, 2026-10-26). Usage:
  Blender --background --factory-startup --python-exit-code 1 --python shots3.py -- SHOT N OUT_DIR [--still=F,..] [--step=2] [--preview] [--nofig]

Short parking-lot shots for the fast edit (edit.py). Same facts as v2: B stands in front of
the car to stop it, the car pushes B back several times, reverses and drives at B once.
Contact is never on screen: the car always stops short of B, and the fall is cut around.
Figures come from people2.py (ready-made CC0 mannequin + retargeted CMU mocap).
"""
import sys, os, math
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import world2 as W
from shots2 import cam, path, key_loc, args, CAR_X, CAR_FRONT, B_X

OPTS = args()[3]
NOFIG = bool(OPTS.get('nofig'))
if not NOFIG:
    import people2 as F

PARK_SKIP = {('S', 8), ('S', 9), ('S', 10), ('N', 8), ('N', 9)}   # S10 sat in the foreground of the side shots
DRIVER_LOCAL = (-0.30, 0.37, 0.0)


def lot3(lights=True, driver=True):
    W.reset()
    W.build_lot()
    W.parked_cars(skip=PARK_SKIP)
    car = W.car('accord_2019', (CAR_X, 0.0, 0), yaw=0.0, paint=(0.03, 0.035, 0.04), lights=lights, tag='car_A')
    see_through_glass(car)
    A = None
    if driver and not NOFIG:
        A = F.load('figA', F.TONE_A)
    return car, A


def see_through_glass(car):
    """The accord's window glass is opaque black (Color_M09); swap for tinted, see-through glass."""
    g = bpy.data.materials.get('hero_glass') or W.mat('hero_glass', (0.02, 0.025, 0.03), rough=0.04, alpha=0.25)
    for o in car.children:
        if o.type == 'MESH':
            for sl in o.material_slots:
                if sl.material and sl.material.name.startswith('Color_M09'):
                    sl.link = 'OBJECT'; sl.material = g


def person(name='figB', loc=(B_X, 0.0, 0.0), yaw=-90.0):
    """B faces -X (towards the car) at yaw -90 (people2 uses people.py's yaw convention)."""
    if NOFIG:
        return None
    b = F.load(name, F.TONE_B)
    F.place(b, loc, yaw)
    return b


def drive_all(A, n, car=None):
    if A is not None:
        car = car or bpy.data.objects['car_A']
        F.drive(A, 1, n, car=car)
        F.driver_seat(car, A, frame=min(30, n))


def ghost(rig):
    gm = W.mat('ghost', (0.55, 0.85, 0.9), rough=0.3, emit=(0.35, 0.75, 0.82), strength=0.8, alpha=0.32)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is rig:
            o.data.materials.clear(); o.data.materials.append(gm)


# ---------------------------------------------------------------- shots
def L01_aerial(n):
    """Night lot from above, craning down onto the car and B standing in its beams."""
    car, A = lot3(); drive_all(A, n, car)
    B = person()
    if B:
        F.stop(B, 1, n)
    co, tgt = cam(32)
    path(co, tgt, n, [(0, (CAR_X + 15, -17, 14), (CAR_X + 2.2, 0, 0.6)), (1, (CAR_X + 10, -12, 8.5), (CAR_X + 2.4, 0, 0.7))])


def L02_hood(n):
    """Over the hood: B in the headlights, then raises both palms to stop the car."""
    car, A = lot3(); drive_all(A, n, car)
    B = person()
    if B:
        F.idle(B, 1, 54); F.stop(B, 55, n)
    co, tgt = cam(24, 6.0)     # 1.83 m mannequin: keep the raised hands and head inside the frame
    path(co, tgt, n, [(0, (CAR_X + 1.22, 0.40, 1.16), (B_X, -0.05, 1.14)), (1, (CAR_X + 1.40, 0.33, 1.15), (B_X, -0.03, 1.14))])


def L03_beams(n):
    """Reverse angle from behind B into the glare, palms out."""
    car, A = lot3(); drive_all(A, n, car)
    B = person()
    if B:
        F.stop(B, 1, n)
    co, tgt = cam(35, 3.6)
    path(co, tgt, n, [(0, (B_X + 3.3, -1.5, 1.55), (CAR_FRONT - 0.6, 0.2, 1.08)), (1, (B_X + 3.1, -0.9, 1.5), (CAR_FRONT - 0.6, 0.15, 1.08))])


GROUND_B = CAR_FRONT + 1.3 + 1.3   # where B ends up after the pushes (clear of the bumper)
PUSH_B = CAR_FRONT + 0.50     # B stands close for the push shots; the bumper never reaches B


def L04_push(n):
    """Side view: the car creeps forward twice and B is driven back step by step."""
    car, A = lot3(); drive_all(A, n, car)
    B = person(loc=(PUSH_B, 0.0, 0.0))
    key_loc(car, 1, (CAR_X, 0, 0)); key_loc(car, 36, (CAR_X, 0, 0)); key_loc(car, 90, (CAR_X + 0.65, 0, 0))
    key_loc(car, 108, (CAR_X + 0.65, 0, 0)); key_loc(car, 160, (CAR_X + 1.3, 0, 0)); key_loc(car, n, (CAR_X + 1.3, 0, 0))
    if B:
        F.stop(B, 1, 36); F.step_back(B, 37, 104, 0.65); F.step_back(B, 105, n, 0.65)
    co, tgt = cam(35, 4.0)
    path(co, tgt, n, [(0, (PUSH_B - 1.0, -6.0, 1.55), (PUSH_B - 1.3, 0, 0.95)), (1, (PUSH_B + 0.1, -5.7, 1.5), (PUSH_B - 0.1, 0, 0.9))])


def L05_wheel(n):
    """Low insert at the front wheel and bumper as the car creeps forward (no figure)."""
    car, A = lot3(driver=False)
    key_loc(car, 1, (CAR_X, 0, 0)); key_loc(car, n, (CAR_X + 0.8, 0, 0))
    co, tgt = cam(24, 2.8)
    path(co, tgt, n, [(0, (CAR_X + 3.4, 1.55, 0.32), (CAR_X + 1.5, 0.55, 0.5)), (1, (CAR_X + 3.6, 1.45, 0.3), (CAR_X + 2.1, 0.5, 0.5))])


def L06_ground(n):
    """B seated on the asphalt in the headlights after the fall (the fall itself is not shown)."""
    car, A = lot3(); drive_all(A, n, car)
    key_loc(car, 1, (CAR_X + 1.3, 0, 0))
    bx = GROUND_B
    B = person(loc=(bx, 0.05, 0.0))
    if B:
        F.sit_ground(B, 1, n)
    # from B's front-side (B faces the car): the dazed seated pose reads, the stopped car on the left
    co, tgt = cam(35, 3.5)
    path(co, tgt, n, [(0, (bx - 1.0, -3.0, 1.3), (bx - 0.2, 0.1, 0.5)), (1, (bx - 0.8, -2.7, 1.2), (bx - 0.2, 0.1, 0.5))])


def L07_reverse(n):
    """Reverse lamps on, the car backs away, stops, then comes forward again at B, who is standing
    and blocking again; cut long before it reaches B."""
    car, A = lot3(); drive_all(A, n, car)
    bx = GROUND_B
    B = person(loc=(bx, 0.05, 0.0))
    if B:
        F.stop(B, 1, n)          # B is back on their feet (the record has B knocked down again)
    key_loc(car, 1, (CAR_X + 1.3, 0, 0)); key_loc(car, 10, (CAR_X + 1.3, 0, 0)); key_loc(car, 70, (CAR_X - 2.0, 0, 0))
    key_loc(car, 88, (CAR_X - 2.0, 0, 0)); key_loc(car, n, (CAR_X + 0.4, 0, 0))
    rv = W.mat('reverse_lamp', (0.9, 0.9, 0.9), emit=(1, 1, 1), strength=0)
    for sy in (0.45, -0.45):
        o = W.box('rev', (0.02, 0.14, 0.05), (0, 0, 0), rv); o.parent = car; o.location = (-2.47, sy, 0.74)
    bsdf = rv.node_tree.nodes['Principled BSDF']
    # white wash on the asphalt behind the car while reversing (the lamp boxes alone barely read)
    wash = W.light('SPOT', 'reverse_wash', (0, 0, 0), 0, (1.0, 0.97, 0.92), spot=110, blend=0.6, soft=0.2)
    wash.parent = car; wash.location = (-2.55, 0.0, 0.7); wash.rotation_euler = (0, math.radians(70), 0)   # -Z rotated to point back (-X) and down
    for f, e in ((1, 0), (8, 0), (10, 30), (86, 30), (88, 0)):
        bsdf.inputs['Emission Strength'].default_value = e; bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
        wash.data.energy = e * 12; wash.data.keyframe_insert('energy', frame=f)
    co, tgt = cam(24, 4.0)     # wide enough for the reversed car's tail and B standing 2.6 m ahead
    path(co, tgt, n, [(0, (CAR_X + 0.6, -7.6, 2.4), (CAR_X + 0.3, 0, 0.8)), (1, (CAR_X + 0.9, -7.3, 2.3), (CAR_X + 0.6, 0, 0.8))])


def L08_driver(n):
    """Through the windscreen: the faceless driver at the wheel, dashboard glow, beams ahead."""
    car, A = lot3(); drive_all(A, n, car)
    glow = W.light('AREA', 'dash_glow', (0, 0, 0), 6, (0.55, 0.7, 1.0), size=(0.5, 0.15))
    glow.parent = car; glow.location = (0.35, 0.37, 0.98); glow.rotation_euler = (0, math.radians(-100), 0)
    hx, hy, hz = CAR_X + DRIVER_LOCAL[0], DRIVER_LOCAL[1], 1.18
    # low and far enough that the sight line to the head clears the roof edge (x≈+0.25, z≈1.40)
    co, tgt = cam(55, 4.0)
    path(co, tgt, n, [(0, (CAR_X + 3.6, 0.62, 1.5), (hx, hy, hz)), (1, (CAR_X + 3.3, 0.5, 1.48), (hx, hy, hz - 0.02))])


def L09_ghost(n):
    """Defence claim as a translucent layer: a figure hurrying into the car's path."""
    car, A = lot3(); drive_all(A, n, car)
    B = person(loc=(B_X + 2.2, 1.2, 0.0), yaw=-115)
    if B:
        ghost(B)
        F.jog_in(B, 1, int(n * 0.7), None, (CAR_FRONT + 0.55, 0.1), end_yaw=-90)
        F.idle(B, int(n * 0.7) + 1, n)
    co, tgt = cam(32, 4.0)
    path(co, tgt, n, [(0, (B_X - 0.4, -6.2, 1.7), (B_X - 0.6, 0, 0.9)), (1, (B_X - 0.7, -5.7, 1.6), (B_X - 0.8, 0, 0.9))])


def L13_outro(n):
    """Empty lot from above, slow orbit; the car parked with lights off."""
    car, A = lot3(lights=False, driver=False)
    co, tgt = cam(30)
    keys = []
    for i in range(5):
        t = i / 4; a = math.radians(-60 + 30 * t)
        keys.append((t, (math.cos(a) * 20 + CAR_X, math.sin(a) * 20, 16 - 1.5 * t), (CAR_X + 1.5, 0, 0)))
    path(co, tgt, n, keys)


SHOTS = {k: v for k, v in globals().items() if k[:1] == 'L' and k[1:3].isdigit()}


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
