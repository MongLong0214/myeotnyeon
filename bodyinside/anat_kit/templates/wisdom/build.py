"""Build the lower dental arch directly from the DBCLS 4.0 release."""

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

kit_dir = Path(os.environ["ANAT_KIT"])
episode_dir = Path(os.environ["ANAT_EPISODE"])
sys.path.insert(0, str(kit_dir / "blender"))
from kit import CameraPath, light_rig, link, newmat, render_settings, setmat, vis, vkey
from kit_astra import Astra, SC

dbcls = Path(
    os.environ.get(
        "BP3D_ROOT",
        (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../../../research/anatomy3d/bodyparts3d_4.0"),
    )
)
episode = json.loads((episode_dir / "episode.json").read_text())
scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene.frame_start = 0
scene.frame_end = round(episode["duration"] * episode["fps"]) - 1
scene.render.fps = episode["fps"]
render_settings(*episode["render"]["res"], spp=episode["render"]["spp"], blur=0)
scene.view_settings.view_transform = "AgX"
scene.render.use_persistent_data = True


def material(name, color, roughness):
    mat, nodes, out, shader = newmat(name)
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Emission Color"].default_value = (0.95, 0.33, 0.05, 1)
    glow = nodes.nodes.new("ShaderNodeValue")
    glow.outputs[0].default_value = 0
    nodes.links.new(glow.outputs[0], shader.inputs["Emission Strength"])
    mix = nodes.nodes.new("ShaderNodeMixShader")
    transparent = nodes.nodes.new("ShaderNodeBsdfTransparent")
    opacity = nodes.nodes.new("ShaderNodeValue")
    opacity.name = "Dental opacity"
    for frame, value in [(0, 0), (60, 0), (88, 1)]:
        vkey(opacity, frame, value)
    nodes.links.new(opacity.outputs[0], mix.inputs[0])
    nodes.links.new(transparent.outputs[0], mix.inputs[1])
    nodes.links.new(shader.outputs[0], mix.inputs[2])
    nodes.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat, glow


bone, _ = material("Mandibular cortex", (0.59, 0.43, 0.28), 0.52)
gum, _ = material("Gingiva", (0.45, 0.11, 0.13), 0.39)
enamel, _ = material("Enamel", (0.86, 0.80, 0.62), 0.32)
first, first_glow = material("First molar enamel", (0.86, 0.80, 0.62), 0.32)
second, second_glow = material("Second molar enamel", (0.86, 0.80, 0.62), 0.32)
manifest = {}
teeth = {}
with (dbcls / "isa_element_parts.txt").open() as part_list:
    for concept, name, file_id, *_ in csv.reader(part_list, delimiter="\t"):
        if name not in ("mandible", "gingiva of lower jaw") and not (
            name.startswith(("left lower", "right lower")) and name.endswith("tooth")
        ):
            continue
        path = dbcls / "obj/isa_BP3D_4.0_obj_99" / (file_id + ".obj")
        bpy.ops.wm.obj_import(filepath=str(path), forward_axis="Y", up_axis="Z")
        obj = bpy.context.selected_objects[0]
        obj.name = name.capitalize()
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        bmesh.ops.remove_doubles(mesh, verts=mesh.verts, dist=0.01)
        mesh.to_mesh(obj.data)
        mesh.free()
        for face in obj.data.polygons:
            face.use_smooth = True
        obj.scale = (0.001,) * 3
        obj.location = (0, 0.089, 0.072)
        obj["src"] = "bp3d:{}:{}:{}".format(
            concept, file_id, hashlib.sha256(path.read_bytes()).hexdigest()
        )
        manifest[obj.name] = obj["src"]
        mat = enamel
        if name == "mandible":
            mat, obj.name = bone, "Mandible"
        elif name == "gingiva of lower jaw":
            mat = gum
        elif name == "left lower first secondary molar tooth":
            mat, teeth["first"] = first, obj
        elif name == "left lower second secondary molar tooth":
            mat, teeth["second"] = second, obj
        setmat(obj, mat)
        vis(obj, [(60, scene.frame_end + 1)])


def occlusal_center(tooth):
    surface = [tooth.matrix_world @ vertex.co for vertex in tooth.data.vertices]
    high = max(p.z for p in surface)
    cusp = [p for p in surface if p.z >= high - 0.002]
    return sum(cusp, Vector()) / len(cusp)


bpy.context.view_layer.update()
m1, m2 = [occlusal_center(teeth[name]) for name in ("first", "second")]
# The posterior dot marks actual gingiva, never a substituted third-molar mesh.
projected = m2 + (m2 - m1) * 0.85
gingiva = bpy.data.objects["Gingiva of lower jaw"]
gum_surface = [gingiva.matrix_world @ v.co for v in gingiva.data.vertices]
posterior = min(gum_surface, key=lambda v: (v - projected).length_squared)
for key, point in [("A_First", m1), ("A_Second", m2), ("A_Posterior", posterior)]:
    anchor = link(bpy.data.objects.new(key, None))
    anchor.location = point
arch_parts = list(scene.objects)
dental_collection = bpy.data.collections.new("Dental geometry")
scene.collection.children.link(dental_collection)
for obj in arch_parts:
    if obj.type == "MESH":
        for old_collection in list(obj.users_collection):
            old_collection.objects.unlink(obj)
        dental_collection.objects.link(obj)
human = Astra(scene, link).load()
# Use the fitted skull transform during the dissolve so teeth appear in the
# mouth. After the person's final opening-action frame, the arch stays still.
arch = link(bpy.data.objects.new("Registered dental arch", None))
for part in arch_parts:
    part.parent = arch
arch.rotation_mode = "QUATERNION"
for frame in range(84):
    skull_map = SC @ Matrix(human.rec(frame)["bp3d_skull_to_world"])
    arch.location, arch.rotation_quaternion, arch.scale = skull_map.decompose()
    for prop in ("location", "rotation_quaternion", "scale"):
        arch.keyframe_insert(prop, frame=frame)
arch_local_center = (m1 + m2) / 2
first_local = m1.copy()
m1, m2, posterior = [skull_map @ point for point in (m1, m2, posterior)]
scene["spp_boost"] = json.dumps([[60, 89, 24], [78, 89, 48]])

# Keep the dark hair readable under the studio key during the push-in.
for obj in human.objs:
    if obj.name.startswith("Hair") and obj.type in ("MESH", "CURVES", "CURVE"):
        for mat in obj.data.materials:
            if mat and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == "BSDF_PRINCIPLED":
                        node.inputs["Roughness"].default_value = 0.78
                        node.inputs["Specular IOR Level"].default_value = 0.18
human.retime()
human.vis(vis, [(0, 89)])
human.fades(vkey, [(0, 1), (60, 1), (88, 0)])
for part in human.objs:
    if part.name.startswith(("Hair", "Eyes", "Spectacles")):
        vis(part, [(0, 82)])
# Astra.fades keys a shader Value output. Keep this measurable in the scene dump.
skin = next(obj for obj in human.objs if obj.name.split(".")[0] == "Skin")
fade = next(
    m.node_tree.nodes["Fade"]
    for m in skin.data.materials
    if m and m.node_tree.nodes.get("Fade")
)
for node, keys in [
    (first_glow, [(0, 0), (90, 0), (225, 0.8), (298, 0.65), (340, 0)]),
    (second_glow, [(0, 0), (300, 0), (420, 0.85), (509, 0.65), (555, 0)]),
]:
    for frame, amount in keys:
        vkey(node, frame, amount)
camera = CameraPath(lens=46, fstop=11)
jaw_center = (m1 + m2) / 2
def mouth_target(f):
    return SC @ Matrix(human.rec(f)["bp3d_skull_to_world"]) @ arch_local_center
for frame, target, direction, distance in [
    (0, mouth_target(0), (1, -0.85, 0.10), 0.76),
    (30, mouth_target(30), (1, -0.80, 0.12), 0.68),
    (59, mouth_target(59), (1, -0.74, 0.12), 0.54),
    (84, jaw_center, (1, -0.58, 0.28), 0.20),
    (89, jaw_center, (1, -0.58, 0.32), 0.20),
    (150, m1, (-0.35, -0.65, 1.8), 0.19),
    (299, m1, (-0.55, -0.45, 1.8), 0.16),
    (380, jaw_center, (-0.70, -0.28, 1.9), 0.17),
    (509, m2, (-0.65, -0.10, 2.0), 0.171),
    (615, m2, (-0.55, -0.20, 1.9), 0.184),
    (700, posterior, (-0.45, -0.40, 2.0), 0.17),
    (720, jaw_center, (-0.50, -0.40, 1.9), 0.19),
    (835, jaw_center, (-0.50, -0.40, 1.9), 0.205),
    (959, jaw_center, (-0.50, -0.40, 1.7), 0.214),
]:
    axis = skull_map.to_quaternion() @ Vector(direction) if frame >= 150 else direction
    camera.key(frame, target, axis, distance)
light_rig(jaw_center, scale=0.7)
# Locate the lower jaw on the cheek of the opaque person throughout the hook.
cheek = link(bpy.data.objects.new("A_Cheek", None))
for f in range(60):
    scene.frame_set(f)
    target = arch.matrix_world @ first_local
    origin = camera.cam.matrix_world.translation
    mesh = skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inv = mesh.matrix_world.inverted()
    ok, hit, _, _ = mesh.ray_cast(inv @ origin, inv.to_3x3() @ (target-origin))
    if not ok:
        raise ValueError(f"no cheek over the registered molar at f{f}")
    cheek.location = mesh.matrix_world @ hit
    cheek.keyframe_insert("location", frame=f)

# Only sample what the gates actually consume. These are evaluated material
# strengths and camera positions, including Blender's real interpolation.
scene_dump = {
    key: {} for key in ("HumanFade", "FirstGlow", "SecondGlow", "CameraDistance")
}
samples = set(range(90)) | {
    f
    for beat in episode["beats"]
    for ev in beat["evidence"]
    for f in (ev["f0"], ev["f1"])
}
for f in sorted(samples):
    scene.frame_set(f)
    for key, node in [
        ("HumanFade", fade),
        ("FirstGlow", first_glow),
        ("SecondGlow", second_glow),
    ]:
        scene_dump[key][str(f)] = node.outputs[0].default_value
    scene_dump["CameraDistance"][str(f)] = (
        camera.cam.matrix_world.translation - posterior
    ).length
for name, data in [
    ("bp3d_provenance", manifest),
    ("scene_dump", scene_dump),
    ("pose_dump", {}),
]:
    (episode_dir / (name + ".json")).write_text(
        json.dumps(data, ensure_ascii=False, indent=1)
    )
scene.frame_set(0)
bpy.ops.file.make_paths_absolute()
bpy.context.preferences.filepaths.use_relative_paths = False
bpy.ops.wm.save_as_mainfile(filepath=str(episode_dir / episode["scene"]), relative_remap=False)

# Independent opaque plates avoid stacked transparent hair, shirt and skin
# surfaces as the human fades out. Keep the original scene for measurements.
def opaque_materials(materials, value_name):
    for mat in materials:
        node = mat.node_tree.nodes.get(value_name) if mat and mat.node_tree else None
        if node:
            for edge in list(node.outputs[0].links):
                factor = edge.to_socket
                mat.node_tree.links.remove(edge)
                factor.default_value = 1.0

opaque_materials({m for obj in human.objs if obj.type in ("MESH","CURVES","CURVE")
                  for m in obj.data.materials}, "Fade")
dental_collection.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(episode_dir / "jaw_person.blend"), relative_remap=False)
dental_collection.hide_render = False
bpy.data.collections["Human | character"].hide_render = True
opaque_materials([bone,gum,enamel,first,second], "Dental opacity")
bpy.ops.wm.save_as_mainfile(filepath=str(episode_dir / "jaw_anatomy.blend"), relative_remap=False)
