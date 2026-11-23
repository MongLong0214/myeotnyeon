"""Attach the v3 ear and acromion overlays to the depicted surface across the closing dissolve."""

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(os.environ["ANAT_KIT"]) / "blender"))
from kit import CameraPath, vis, vkey

dest, obj_dir, settings_file, skin_pack = map(Path, sys.argv[sys.argv.index("--") + 1 :])
settings = json.loads(settings_file.read_text())
scene = bpy.context.scene
objects = bpy.data.objects


def restore_skin():
    actor = objects["Skin.001"]
    previous = actor.data
    with bpy.data.libraries.load(str(skin_pack / "skin.blend")) as (_, loaded):
        loaded.meshes = ["Intact shirt-covered skin"]
    mesh = loaded.meshes[0]
    groups = json.loads((skin_pack / "skin_groups.json").read_text())
    if groups != [g.name for g in actor.vertex_groups]:
        raise ValueError("restored skin uses different armature weights")
    new_ids = {v.value: i for i, v in enumerate(mesh.attributes["hm08_index"].data)}
    old_ids = [new_ids[v.value] for v in previous.attributes["hm08_index"].data]
    if any(
        (previous.vertices[i].co - mesh.vertices[j].co).length > 1e-6
        for i, j in enumerate(old_ids)
    ):
        raise ValueError("restored skin and published cast have different rest poses")
    for material in previous.materials:
        mesh.materials.append(material)
    actor.data = mesh
    # Preserve the original blink on every original vertex. The added torso
    # vertices retain their rest positions in both shape keys.
    blink = previous.shape_keys.key_blocks["Blink"]
    actor.shape_key_add(name="Basis")
    restored = actor.shape_key_add(name="Blink")
    original_color = previous.color_attributes["Complexion"].data
    restored_color = mesh.color_attributes["Complexion"].data
    for i, j in enumerate(old_ids):
        restored.data[j].co = blink.data[i].co
        restored_color[j].color = original_color[i].color
    driver = restored.driver_add("value").driver
    driver.type = "AVERAGE"
    target = driver.variables.new().targets[0]
    target.id = actor.find_armature()
    target.data_path = 'pose.bones["head"]["blink"]'


restore_skin()
# The original garment cut away the torso underneath it. Keep the fabric
# outside the reconstructed shoulder as the character moves.
shirt = objects["Outfit"]
shoulders = shirt.vertex_groups.new(name="Shirt shoulder fit")
for v in shirt.data.vertices:
    x, _, z = v.co
    weight = min(1, (abs(x) - 0.055) / 0.04, (z - 1.19) / 0.07, (1.52 - z) / 0.05)
    if weight > 0:
        shoulders.add([v.index], weight, "REPLACE")
fit = shirt.modifiers.new("Allow for the skin beneath the shirt", "SHRINKWRAP")
fit.target = objects["Skin.001"]
fit.wrap_method = "NEAREST_SURFACEPOINT"
fit.wrap_mode = "OUTSIDE"
fit.offset = 0.004
fit.vertex_group = shoulders.name
end = scene.frame_end
closing = settings["closing"]
fade_start, fade_end = closing["f0"], closing["f1"] - 1
manifest = json.loads((dest / "bp3d_provenance.json").read_text())
bone_material = bpy.data.materials["BoneBase"].copy()
bone_material.name = "Closing landmark cortex"


def mask(material, factor):
    tree = material.node_tree
    output = next(
        n for n in tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output
    )
    original = output.inputs["Surface"].links[0].from_socket
    mix = tree.nodes.new("ShaderNodeMixShader")
    clear = tree.nodes.new("ShaderNodeBsdfTransparent")
    tree.links.new(factor, mix.inputs[0])
    tree.links.new(clear.outputs[0], mix.inputs[1])
    tree.links.new(original, mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs["Surface"])


opacity = bone_material.node_tree.nodes.new("ShaderNodeValue")
for frame, value in ((0, 0), (fade_start, 0), (fade_end, 1), (end, 1)):
    vkey(opacity, frame, value)
mask(bone_material, opacity.outputs[0])
for name, part in json.loads(Path(__file__).with_suffix(".json").read_text()).items():
    fma, fj = part["concept"], part["file"]
    path = obj_dir / (fj + ".obj")
    bone = objects.get(name)
    if bone is None:
        bpy.ops.wm.obj_import(filepath=str(path), forward_axis="Y", up_axis="Z")
        bone = bpy.context.selected_objects[0]
        bone.name = name
        bone.data.transform(
            Matrix.Translation((0, 0.089, 0.072)) @ Matrix.Scale(0.001, 4)
        )
        bone.parent = objects["Skull" if name == "Temporal.r" else "SkelRoot"]
        bone.matrix_parent_inverse = Matrix.Identity(4)
        for face in bone.data.polygons:
            face.use_smooth = True
    bone["src"] = f"bp3d:{fma}:{fj}:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    manifest[name] = [bone["src"]]
    bone.data.materials.clear()
    bone.data.materials.append(bone_material)
    vis(bone, [(fade_start, end + 1)])

bpy.context.view_layer.update()
temporal = objects["Temporal.r"]
hit, ear, _, _ = temporal.ray_cast(Vector((-0.15, 0.004, 1.578)), Vector((1, 0, 0)))
if not hit:
    raise ValueError("registered temporal ear recess missing")
# Reveal the local cortex around the recess while preserving the sagittal view.
material = bone_material.copy()
temporal.data.materials[0] = material
tree = material.node_tree
coords = tree.nodes.new("ShaderNodeTexCoord")
distance = tree.nodes.new("ShaderNodeVectorMath")
distance.operation = "DISTANCE"
distance.inputs[1].default_value = ear
tree.links.new(coords.outputs["Object"], distance.inputs[0])
edge = tree.nodes.new("ShaderNodeMapRange")
edge.interpolation_type = "SMOOTHSTEP"
for socket, value in (
    ("From Min", 0.009),
    ("From Max", 0.019),
    ("To Min", 1),
    ("To Max", 0),
):
    edge.inputs[socket].default_value = value
tree.links.new(distance.outputs["Value"], edge.inputs["Value"])
mask(material, edge.outputs["Result"])

scapula = objects["Scapula.r"]
tip = min((v.co for v in objects["Clavicle.r"].data.vertices), key=lambda p: p.x)
joint = min(
    (v.co for v in scapula.data.vertices), key=lambda p: (p - tip).length_squared
)
acromion = max(
    (v.co for v in scapula.data.vertices if (v.co - joint).length <= 0.005),
    key=lambda p: p.z,
).copy()
# A profile along the ear-to-shoulder horizontal axis projects a vertical plumb
# line without relocating either joint.
scene.frame_set(end)
ear_world = temporal.matrix_world @ ear
acro_world = scapula.matrix_world @ acromion
axis = acro_world - ear_world
axis.z = 0
axis.normalize()
axis = Matrix.Rotation(math.radians(-3), 3, "Z") @ axis
axis.z = -0.04
focus = (ear_world + acro_world) * 0.5
cam = CameraPath.__new__(CameraPath)
cam.cam, cam.focus, cam.roll = scene.camera, scene.camera.data.dof.focus_object, 0
for frame, dist in ((fade_end - 2, 0.82), (879, 0.82), (903, 0.81), (end, 0.80)):
    cam.key(frame, focus, axis, dist)
lenses = []
for frame, scale in (
    (0, 0.90),
    (15, 1),
    (60, 1),
    (76, 1.22),
    (83, 1.22),
    (84, 1.22),
    (94, 1.18),
    (101, 1.15),
    (104, 1.14),
    (124, 1),
):
    scene.frame_set(frame)
    lenses.append((frame, cam.cam.data.lens * scale))
for frame, lens in lenses:
    cam.cam.data.lens = lens
    cam.cam.data.keyframe_insert("lens", frame=frame)

landmarks = []
subdivisions = []
for anchor, skin_name, rest, bone, point in (
    ("A_Ear", "Skin.001", (0.067, -0.052, 1.555), temporal, ear),
    ("A_Acro", "Outfit", (0.179, -0.010, 1.381), scapula, acromion),
):
    surface = objects[skin_name]
    for mod in surface.modifiers:
        if mod.type == "SUBSURF":
            subdivisions.append((mod, mod.show_viewport))
            mod.show_viewport = False
    indexes = [
        min(
            surface.data.vertices,
            key=lambda v: (v.co - Vector((side * rest[0], *rest[1:]))).length_squared,
        ).index
        for side in (-1, 1)
    ]
    landmarks.append((objects[anchor], surface, indexes, bone, point))
start = settings["marker_start"]
skin_fade = next(
    m.node_tree.nodes["Fade"].outputs[0]
    for m in objects["Skin.001"].data.materials
    if m and m.node_tree.nodes.get("Fade")
)
for frame in range(start, end + 1):
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    # Bring the marker onto the bony landmark before the skin becomes transparent.
    weight = min(1, max(0, (skin_fade.default_value - 0.35) / 0.65))
    for anchor, surface, indexes, bone, point in landmarks:
        actual = surface.evaluated_get(dg)
        candidates = [actual.matrix_world @ actual.data.vertices[i].co for i in indexes]
        near = min(
            candidates,
            key=lambda p: (p - scene.camera.matrix_world.translation).length_squared,
        )
        target = (bone.matrix_world @ point).lerp(near, weight)
        anchor.location = (
            anchor.parent.matrix_world @ anchor.matrix_parent_inverse
        ).inverted() @ target
        anchor.keyframe_insert("location", frame=frame)
for mod, enabled in subdivisions:
    mod.show_viewport = enabled
scene.frame_set(0)
(dest / "bp3d_provenance.json").write_text(json.dumps(manifest, indent=1))
bpy.ops.file.make_paths_absolute()
bpy.context.preferences.filepaths.use_relative_paths = False
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(dest / "neck.blend"), relative_remap=False)
