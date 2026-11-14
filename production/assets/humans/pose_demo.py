"""
pose_demo.py
============

Proof-of-work script for the two CC0 rigged human characters under
assets/humans/mpfb_male/ and assets/humans/mpfb_female/.

For each character it:
  1. Opens the character's own .blend file (mesh + 'cmu_mb'-named armature
     + grey plaster material, already baked in by build_character.py).
  2. Applies three poses in turn:
       - "standing"   : the rig's natural rest pose (no rotation needed -
                         MPFB2's cmu_mb rest pose is already a relaxed
                         standing stance, not a T-pose - see REPORT.md).
       - "stop"       : a hand-set "raised arm, palm forward" halt gesture.
       - "seated"     : a hand-set pose sitting on the ground.
  3. Sets up a simple grey studio environment (ground plane, 3-point
     lighting, camera) and renders each pose with Eevee to
       assets/humans/_previews/<character>_<pose>.png  (1280x720)

It also includes retarget_bvh_pose(), a small, real, working BVH-to-rig
retargeting function (same technique MPFB2's own
AnimationService.import_bvh_file_as_pose uses, with added frame control)
that can drive this rig from any of the CMU BVH clips under
assets/humans/motion/ - see use_retarget_bonus_pose() for a worked example
that is exercised at the bottom of this file to prove it actually works
(renders one bonus frame from walk_forward onto the male rig).

Usage (headless, Blender 5.2.3):
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      --factory-startup --python-exit-code 1 \
      --python assets/humans/pose_demo.py
"""

import bpy
import math
import os
from mathutils import Vector, Matrix

HUMANS_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR = os.path.join(HUMANS_DIR, "_previews")
MOTION_DIR = os.path.join(HUMANS_DIR, "motion")

CHARACTERS = {
    "human_male": os.path.join(HUMANS_DIR, "mpfb_male", "human_male.blend"),
    "human_female": os.path.join(HUMANS_DIR, "mpfb_female", "human_female.blend"),
}


# --------------------------------------------------------------------- #
# Generic helpers
# --------------------------------------------------------------------- #

def clear_pose(arm_obj):
    for pb in arm_obj.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def set_bone(pose_bone, x_deg=0.0, y_deg=0.0, z_deg=0.0):
    """Set a bone's local-space XYZ Euler pose rotation outright (relative
    to its own rest orientation - ordinary matrix_basis, Blender's normal
    pose representation).

    We tried driving these poses with IK constraints + target empties
    first; it worked but needed a lot of machinery (create empties, bake
    visual transform, clean up) for only two bones per limb. Once the rig's
    bone *rest positions* were fixed (see REPORT.md - detailed_helpers/
    extra_vertex_groups must stay True or MPFB mis-places every bone), a
    handful of plain local-Euler rotations turned out to pose this rig just
    as well and are far easier to read, tune and reuse. Axis meaning was
    determined empirically per bone chain (see REPORT.md "how to retarget /
    how to hand-pose"): for both the arm and the leg chains on this rig,
    local X is the main forward/back swing (hip or shoulder flexion, elbow/
    knee bend); Z on the shoulder/upper-arm bones abducts (raises the arm
    out to the side).
    """
    pose_bone.rotation_mode = 'XYZ'
    pose_bone.rotation_euler = (math.radians(x_deg), math.radians(y_deg), math.radians(z_deg))


# --------------------------------------------------------------------- #
# Pose 1: standing - MPFB2's cmu_mb rest pose IS a relaxed standing
# mannequin stance already (arms hang naturally at the sides, not a
# T-pose - confirmed by inspecting edit-bone directions, see REPORT.md).
# So "standing" is simply: apply no pose rotations at all.
# --------------------------------------------------------------------- #

def pose_standing(arm_obj):
    clear_pose(arm_obj)


# --------------------------------------------------------------------- #
# Pose 2: "stop" gesture - raise the right arm, elbow bent, palm forward.
# Hand-set bone rotations (explicitly allowed by the brief for this pose).
# --------------------------------------------------------------------- #

def pose_stop_gesture(arm_obj):
    clear_pose(arm_obj)
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones

    # Right arm: raise it out to the side and up to shoulder height
    # (RightArm Z=-90 = abduct), then bend the elbow so the forearm points
    # up (RightForeArm X=60), and twist the hand so the palm faces forward
    # - a traffic-halt "stop" silhouette. Values found by a small numeric
    # sweep over hand-tip position, see assets/humans/REPORT.md.
    set_bone(pb["RightArm"], x_deg=5, y_deg=0, z_deg=-85)
    set_bone(pb["RightForeArm"], x_deg=85, y_deg=0, z_deg=0)
    set_bone(pb["RightHand"], x_deg=-20, y_deg=100, z_deg=0)
    bpy.context.view_layer.update()


# --------------------------------------------------------------------- #
# Pose 3: seated on the ground - hand-set bone rotations.
# --------------------------------------------------------------------- #

def pose_seated_on_ground(arm_obj):
    clear_pose(arm_obj)
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones

    # Hip flexion ~95 deg swings each thigh forward to roughly horizontal;
    # knee flexion ~100 deg folds the shin back down towards the floor;
    # a small ankle correction lays the foot flat. Same angles for both
    # legs (mirrored automatically - Left/Right share the same local-axis
    # convention on this rig). Values found by numeric + visual testing,
    # see REPORT.md.
    for side in ("Right", "Left"):
        set_bone(pb[f"{side}UpLeg"], x_deg=-95, y_deg=0, z_deg=0)
        set_bone(pb[f"{side}Leg"], x_deg=100, y_deg=0, z_deg=0)
        set_bone(pb[f"{side}Foot"], x_deg=-10, y_deg=0, z_deg=0)
    bpy.context.view_layer.update()

    # Drop the whole rig so the lowest foot/toe point rests on the ground
    # plane (z=0), rather than guessing a fixed hip height - this makes the
    # pose self-adjusting for any character's proportions/leg length.
    lowest_z = min(
        pb[f"{side}Foot"].tail.z for side in ("Right", "Left")
    )
    arm_obj.location.z -= (lowest_z - 0.015)
    bpy.context.view_layer.update()


# --------------------------------------------------------------------- #
# BVH retargeting (real, working, used for the bonus walk-cycle render).
# Same technique as MPFB2's own AnimationService.import_bvh_file_as_pose:
# bone names in CMU BVH clips match this rig's bone names exactly (both
# follow the Hahne/CMU-MB convention), so we (1) import the BVH, (2) copy
# EDIT-BONE ROLL values across by name (this is destructive - it overwrites
# this rig's own roll values - fine for a one-off static pose snapshot),
# then (3) copy the source's pose rotation_euler at a chosen frame across
# by name, then (4) delete the imported BVH armature.
# --------------------------------------------------------------------- #

def retarget_bvh_pose(dest_rig, bvh_file_path, frame):
    if bpy.context.object is not None and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_anim.bvh(filepath=bvh_file_path, axis_forward='Y', axis_up='Z',
                             rotate_mode='XYZ', update_scene_fps=False, use_fps_scale=False)
    source_rig = bpy.context.object

    bpy.context.view_layer.objects.active = source_rig
    bpy.ops.object.mode_set(mode='EDIT')
    source_rolls = {b.name: b.roll for b in source_rig.data.edit_bones}
    bpy.ops.object.mode_set(mode='POSE')

    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    source_eulers = {}
    for spb in source_rig.pose.bones:
        spb.rotation_mode = 'XYZ'
        source_eulers[spb.name] = spb.rotation_euler.copy()

    bpy.context.view_layer.objects.active = dest_rig
    bpy.ops.object.mode_set(mode='EDIT')
    for deb in dest_rig.data.edit_bones:
        if deb.name in source_rolls:
            deb.roll = source_rolls[deb.name]
    bpy.ops.object.mode_set(mode='POSE')
    for dpb in dest_rig.pose.bones:
        if dpb.name in source_eulers:
            dpb.rotation_mode = 'XYZ'
            dpb.rotation_euler = source_eulers[dpb.name]

    bpy.data.objects.remove(source_rig, do_unlink=True)
    bpy.context.view_layer.objects.active = dest_rig
    bpy.ops.object.mode_set(mode='OBJECT')


# --------------------------------------------------------------------- #
# Scene / render setup
# --------------------------------------------------------------------- #

def setup_render_scene(mesh_obj):
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    scn.render.film_transparent = False

    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    gmat = bpy.data.materials.new("GroundGrey")
    gmat.use_nodes = True
    bsdf = gmat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
    ground.data.materials.append(gmat)

    height = mesh_obj.dimensions.z or 1.7

    # Camera - wide enough, and far enough back, to keep the whole figure
    # (head to feet, plus margin for the seated pose's forward-splayed
    # knees) inside frame. Using an explicit vertical FOV + sensor_fit so
    # the framing maths doesn't depend on guessing a focal length (a first
    # pass at 50mm/3.1m cropped the head off - see REPORT.md).
    vertical_span = height * 1.35
    fov_deg = 38.0
    distance = (vertical_span / 2.0) / math.tan(math.radians(fov_deg / 2.0))

    cam_data = bpy.data.cameras.new("DemoCam")
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.angle = math.radians(fov_deg)
    cam_obj = bpy.data.objects.new("DemoCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    look_at = Vector((0.0, 0.0, height * 0.42))
    cam_obj.location = (0.0, -distance, height * 0.42)
    direction = look_at - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scn.camera = cam_obj

    # Simple 3-point lighting
    def add_light(name, loc, energy, size=2.0):
        ldata = bpy.data.lights.new(name, type='AREA')
        ldata.energy = energy
        ldata.size = size
        lobj = bpy.data.objects.new(name, ldata)
        bpy.context.scene.collection.objects.link(lobj)
        lobj.location = loc
        direction = Vector((0, 0, height * 0.5)) - Vector(loc)
        lobj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        return lobj

    add_light("KeyLight", (2.5, -2.5, height * 1.6), 400)
    add_light("FillLight", (-2.8, -1.8, height * 1.0), 150)
    add_light("RimLight", (0.0, 2.5, height * 1.8), 200)

    return ground, cam_obj


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)


# --------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------- #

def find_mesh_and_rig(gender_prefix):
    mesh_obj = None
    arm_obj = None
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name == gender_prefix:
            mesh_obj = o
        if o.type == 'ARMATURE' and o.name == f"{gender_prefix}_rig":
            arm_obj = o
    return mesh_obj, arm_obj


def run_character(char_name, blend_path):
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    mesh_obj, arm_obj = find_mesh_and_rig(char_name)
    assert mesh_obj is not None and arm_obj is not None, f"could not find mesh/rig for {char_name}"

    ground, cam_obj = setup_render_scene(mesh_obj)

    poses = [
        ("standing", pose_standing),
        ("stop", pose_stop_gesture),
        ("seated", pose_seated_on_ground),
    ]
    for pose_name, pose_fn in poses:
        arm_obj.location = (0.0, 0.0, 0.0)
        pose_fn(arm_obj)
        bpy.context.view_layer.update()
        out_path = os.path.join(PREVIEW_DIR, f"{char_name}_{pose_name}.png")
        render_to(out_path)
        clear_pose(arm_obj)
        arm_obj.location = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    return mesh_obj, arm_obj


def bonus_retarget_render(char_name, arm_obj):
    """Prove retarget_bvh_pose() actually drives the rig with real CMU
    motion capture data: apply frame 300 of walk_forward.bvh (mid-stride)
    and render it as a bonus preview beyond the 3 required poses."""
    clear_pose(arm_obj)
    arm_obj.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    bvh_path = os.path.join(MOTION_DIR, "walk_forward", "141_19.bvh")
    retarget_bvh_pose(arm_obj, bvh_path, frame=80)
    bpy.context.view_layer.update()
    out_path = os.path.join(PREVIEW_DIR, f"{char_name}_walk_retarget_bonus.png")
    render_to(out_path)


if __name__ == "__main__":
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    mesh_obj, arm_obj = run_character("human_male", CHARACTERS["human_male"])
    bonus_retarget_render("human_male", arm_obj)

    run_character("human_female", CHARACTERS["human_female"])

    print("ALL DONE")
