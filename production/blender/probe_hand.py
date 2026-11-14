import bpy, sys, math, json
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/Users/isaac/projects/verdict-kr/work/production/assets/humans/ep001/char_B.blend')
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mw = rig.matrix_world
def w(b, tail=True):
    pb = rig.pose.bones[b]; return mw @ (pb.tail if tail else pb.head)
out = {}
for s in ('Left', 'Right'):
    hand = w(f'{s}Hand', False); fb = w(f'{s}FingerBase', False) if f'{s}FingerBase' in rig.pose.bones else None
    fing = w(f'{s}HandFinger1', True); th = w(('L' if s == 'Left' else 'R') + 'Thumb', True)
    out[s] = dict(hand_head=[round(x, 3) for x in hand], finger_tip=[round(x, 3) for x in fing], thumb_tip=[round(x, 3) for x in th],
                  hand_bone_axes={k: [round(x, 3) for x in (rig.matrix_world.to_3x3() @ rig.data.bones[f'{s}Hand'].matrix_local.to_3x3() @ Vector(v))] for k, v in (('x', (1, 0, 0)), ('y', (0, 1, 0)), ('z', (0, 0, 1)))})
for b in ('LeftFoot', 'LeftToeBase', 'LeftLeg', 'Hips', 'LeftUpLeg'):
    out[b] = dict(head=[round(x, 3) for x in w(b, False)], tail=[round(x, 3) for x in w(b, True)])
print('PROBE', json.dumps(out))
