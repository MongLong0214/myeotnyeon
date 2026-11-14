import bpy, math
bpy.ops.wm.open_mainfile(filepath='/Users/isaac/projects/verdict-kr/work/production/assets/humans/ep001/char_B.blend')
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
pb = rig.pose.bones
def tail(b):
    bpy.context.view_layer.update(); return tuple(round(x, 3) for x in (rig.matrix_world @ pb[b].tail))
print('REST hand L', tail('LeftHand'), 'R', tail('RightHand'), 'footL', tail('LeftFoot'), 'head', tail('Head'))
for bone, end in (('LeftArm', 'LeftHand'), ('RightArm', 'RightHand'), ('LeftForeArm', 'LeftHand'), ('LeftUpLeg', 'LeftFoot'), ('LeftLeg', 'LeftFoot'), ('Spine', 'Head'), ('Hips', 'Head')):
    for ax in range(3):
        for ang in (40, -40):
            e = [0, 0, 0]; e[ax] = math.radians(ang)
            pb[bone].rotation_mode = 'XYZ'; pb[bone].rotation_euler = e
            print('PROBE', bone, 'XYZ'[ax], ang, '->', end, tail(end))
        pb[bone].rotation_euler = (0, 0, 0)
