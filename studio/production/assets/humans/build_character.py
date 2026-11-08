"""
Build one CC0 rigged human character via the MPFB2 addon (MakeHuman Plugin
For Blender 2), using its built-in "cmu_mb" skeleton which uses the exact
same bone-naming convention as the CMU Graphics Lab BVH motion data used
in this project (Hips, LeftUpLeg, LeftArm, LeftForeArm, ... ).

Usage (headless):
  Blender --background --factory-startup --python-exit-code 1 \
      --python build_character.py -- <gender: male|female> <out_blend_path>
"""
import bpy, sys, os

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
gender = argv[0] if len(argv) > 0 else "male"
out_path = argv[1] if len(argv) > 1 else f"/tmp/mpfb_{gender}.blend"

assert gender in ("male", "female")

# ---------------------------------------------------------------- addon ---
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")

scn = bpy.context.scene

# -------------------------------------------------------- create human ---
scn.MPFB_NH_add_phenotype = True
scn.MPFB_NH_phenotype_gender = gender
scn.MPFB_NH_phenotype_influence = 1.0
scn.MPFB_NH_phenotype_age = "young"
scn.MPFB_NH_phenotype_muscle = "averagemuscle"
scn.MPFB_NH_phenotype_weight = "averageweight"
scn.MPFB_NH_phenotype_height = "average"
scn.MPFB_NH_phenotype_proportions = "average"
scn.MPFB_NH_phenotype_race = "universal"
scn.MPFB_NH_add_breast = False
scn.MPFB_NH_override_skin_model = "NONE"   # no texture - we add a plain plaster material ourselves
scn.MPFB_NH_override_eyes_model = "NONE"
scn.MPFB_NH_scale_factor = "METER"
scn.MPFB_NH_mask_helpers = True
scn.MPFB_NH_detailed_helpers = False
scn.MPFB_NH_extra_vertex_groups = False

r = bpy.ops.mpfb.create_human()
print("create_human:", r)

mesh_obj = bpy.context.view_layer.objects.active
mesh_obj.name = f"human_{gender}"

# ------------------------------------------------------------- add rig ---
scn.MPFB_ADR_standard_rig = "cmu_mb"
scn.MPFB_ADR_import_weights = True
r2 = bpy.ops.mpfb.add_standard_rig()
print("add_standard_rig:", r2)

arm_obj = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        arm_obj = o
arm_obj.name = f"human_{gender}_rig"
mesh_obj.name = f"human_{gender}"  # re-affirm after rig rename churn

print("final objects:", [(o.name, o.type) for o in bpy.data.objects])
print("bone count:", len(arm_obj.data.bones))
print("bone names:", sorted(b.name for b in arm_obj.data.bones))
print("mesh verts:", len(mesh_obj.data.vertices), "dims:", tuple(mesh_obj.dimensions))

# ------------------------------------------------------- grey plaster ---
mat = bpy.data.materials.new(name="PlasterGrey")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.66, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.3
mesh_obj.data.materials.clear()
mesh_obj.data.materials.append(mat)

# ------------------------------------------------------------ cleanup ---
for name in ("Cube", "Camera", "Light"):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

# Make sure the rig is at the world origin, standing on the Z=0 ground plane,
# facing -Y (Blender's default "front").
arm_obj.location = (0.0, 0.0, 0.0)

# save
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print("SAVED", out_path)
