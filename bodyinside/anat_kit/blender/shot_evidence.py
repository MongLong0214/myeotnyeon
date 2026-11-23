"""Measure skin, skeletal and transition evidence against the active camera."""

import json
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree

episode_path, frame_list, output = sys.argv[sys.argv.index("--") + 1 :]
ep = json.loads(Path(episode_path).read_text())
scene = bpy.context.scene
objects = scene.objects
camera = scene.camera
# The registered Astra neck rig is in metres in the DBCLS world frame.
rules = json.loads(
    (Path(__file__).resolve().parents[1] / "gates/thresholds.json").read_text()
)
cord_stop = rules["shot_checks"]["astra_neck_cord_stop_m"]


face_bones = [
    o
    for o in objects
    if o.name.startswith(
        (
            "Skull",
            "Temporal.",
            "Mandible",
            "Rim_Skull",
            "Rim_Mandible",
            "TeethUpper",
            "TeethLower",
        )
    )
]
# Rest-mesh landmarks from Astra's fit. Measure the near-side skin and shirt
# vertices independently of the empties which drive the 2D overlay.
surfaces = [("Skin.001", (0.067, -0.052, 1.555)), ("Outfit", (0.179, -0.010, 1.381))]
indices = {}


def landmarks(name, point):
    if name not in indices:
        mesh = objects[name].data
        indices[name] = [
            min(
                mesh.vertices,
                key=lambda v: (
                    (v.co - Vector((sign * point[0], *point[1:]))).length_squared
                ),
            ).index
            for sign in (-1, 1)
        ]
    return indices[name]


def screen(point):
    q = world_to_camera_view(scene, camera, point)
    return [
        round(q.x * scene.render.resolution_x, 2),
        round((1 - q.y) * scene.render.resolution_y, 2),
    ]


# Landmark indices belong to the unsubdivided, skinned cage used by the
# character's anchor export. Subdivision can change evaluated vertex indices.
for name, _ in surfaces:
    obj = objects.get(name)
    if obj:
        for modifier in obj.modifiers:
            if modifier.type == "SUBSURF":
                modifier.show_viewport = False


def skin_alpha():
    skin = next(
        (
            objects.get(name)
            for name in ("Skin.001", "HumanBody", "Skin")
            if objects.get(name)
        ),
        None,
    )
    if not skin or skin.hide_render:
        return 0.0
    fades = [
        m.node_tree.nodes.get("Fade") for m in skin.data.materials if m and m.node_tree
    ]
    return max((node.outputs[0].default_value for node in fades if node), default=1.0)


rows = {}
acromion_indices = {}


def bony_shoulder(anchor, dg):
    side = (
        "r"
        if (
            objects["SkelRoot"].matrix_world.inverted()
            @ camera.matrix_world.translation
        ).x
        < 0
        else "l"
    )
    scapula, clavicle = (
        objects.get(name + "." + side) for name in ("Scapula", "Clavicle")
    )
    if not scapula or not clavicle or scapula.hide_render or clavicle.hide_render:
        return dict(
            name=anchor,
            side=side,
            visible=False,
            reason="camera-side girdle missing or hidden",
        )
    if side not in acromion_indices:
        choose = min if side == "r" else max
        tip = choose((v.co for v in clavicle.data.vertices), key=lambda p: p.x)
        joint = min(scapula.data.vertices, key=lambda v: (v.co - tip).length_squared).co
        upper = (v for v in scapula.data.vertices if (v.co - joint).length <= .005)
        acromion_indices[side] = max(upper, key=lambda v: v.co.z).index
    surface = scapula.evaluated_get(dg)
    target = surface.data.vertices[acromion_indices[side]].co
    cam = surface.matrix_world.inverted() @ camera.matrix_world.translation
    hit = BVHTree.FromObject(scapula, dg).ray_cast(cam, (target - cam).normalized())[0]
    return dict(
        name=anchor,
        side=side,
        visible=hit is not None
        and (hit - target).length < rules["shot_checks"]["landmark_visibility_depth_m"],
        label_px=screen(objects[anchor].matrix_world.translation),
        landmark_px=screen(surface.matrix_world @ target),
    )


def bony_ear(anchor, dg):
    temporal = objects.get("Temporal.r")
    if temporal is None or temporal.hide_render:
        return dict(
            name=anchor, visible=False, reason="right temporal bone missing or hidden"
        )
    mesh = temporal.evaluated_get(dg)
    tree = BVHTree.FromObject(temporal, dg)
    target = tree.ray_cast(Vector((-0.15, 0.004, 1.578)), Vector((1, 0, 0)))[0]
    if target is None:
        return dict(
            name=anchor,
            visible=False,
            reason="registered ear site missing from temporal surface",
        )
    cam = mesh.matrix_world.inverted() @ camera.matrix_world.translation
    hit = tree.ray_cast(cam, (target - cam).normalized())[0]
    return dict(
        name=anchor,
        side="r",
        visible=cam.x < target.x
        and hit is not None
        and (hit - target).length < rules["shot_checks"]["landmark_visibility_depth_m"],
        label_px=screen(objects[anchor].matrix_world.translation),
        landmark_px=screen(mesh.matrix_world @ target),
    )


def visible_surface(anchor, expected, dg):
    camera_world = camera.matrix_world.translation
    target = objects[anchor].matrix_world.translation
    ray = (target - camera_world).normalized()
    hits = []
    for obj in objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        mesh = obj.evaluated_get(dg)
        inverse = mesh.matrix_world.inverted_safe()
        hit, point, _, _ = mesh.ray_cast(inverse @ camera_world, inverse.to_3x3() @ ray)
        if hit:
            world = mesh.matrix_world @ point
            hits.append(
                ((world - camera_world).length, obj.name, (world - target).length)
            )
    _, front, distance = min(hits) if hits else (None, None, None)
    q = world_to_camera_view(scene, camera, target)
    return dict(
        anchor=anchor,
        expected=expected,
        front=front,
        distance_m=distance,
        in_frame=q.z > 0 and 0 <= q.x <= 1 and 0 <= q.y <= 1,
    )


for f in json.loads(Path(frame_list).read_text()):
    kind = next(s["kind"] for s in ep["shots"] if s["f0"] <= f < s["f1"])
    labels = [
        label
        for label in ep.get("labels", [])
        if label["kind"] in ("gap", "plumb") and label["f0"] <= f <= label["f1"]
    ]
    callouts = [
        label
        for label in ep.get("labels", [])
        if label["kind"] == "callout"
        and label["f0"] <= f <= label["f1"]
        and (ep.get("region") == "jaw" or label.get("surface"))
    ]
    if kind != "person" and not labels and not callouts:
        continue
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    row = {
        "skin_alpha": skin_alpha(),
        "renderable_face_bones": [o.name for o in face_bones if not o.hide_render],
        "dots": [],
    }
    targets = {}
    for label in callouts:
        targets[label["anchor"]] = label.get("surface")
        targets.update(label.get("context_surfaces", {}))
    row["surfaces"] = [
        visible_surface(anchor, surface, dg) for anchor, surface in targets.items()
    ]
    for label in labels:
        if kind != "person":
            if ep.get("region") == "neck" and (
                kind == "anatomy"
                or row["skin_alpha"]
                <= rules["shot_checks"]["bone_landmark_max_skin_alpha"]
            ):
                row["dots"].append(bony_ear(label["anchor"], dg))
                row["dots"].append(bony_shoulder(label["anchor2"], dg))
            continue
        for anchor, (name, rest) in zip(("anchor", "anchor2"), surfaces):
            surface = objects[name].evaluated_get(dg)
            mesh = surface.data
            world = surface.matrix_world
            cam = world.inverted() @ camera.matrix_world.translation
            verts = [mesh.vertices[i].co for i in landmarks(name, rest)]
            target = min(verts, key=lambda v: (v - cam).length_squared)
            # Ray hits the actual near-side mesh, including occlusion in rear views.
            hit = BVHTree.FromObject(objects[name], dg).ray_cast(
                cam, (target - cam).normalized()
            )[0]
            row["dots"].append(
                dict(
                    name=anchor,
                    visible=hit is not None
                    and (hit - target).length
                    < rules["shot_checks"]["landmark_visibility_depth_m"],
                    label_px=screen(objects[label[anchor]].matrix_world.translation),
                    landmark_px=screen(world @ target),
                )
            )
    rows[str(f)] = row


def linked_height_mask(mat):
    if not mat or not mat.node_tree:
        return False
    outputs = [
        node
        for node in mat.node_tree.nodes
        if node.type == "OUTPUT_MATERIAL" and node.is_active_output
    ]
    seen = set()

    def reaches(node):
        if node in seen:
            return False
        seen.add(node)
        if node.type == "MIX_SHADER":
            mask = node.inputs[0].links
            clear = node.inputs[1].links
            if mask and clear and clear[0].from_node.type == "BSDF_TRANSPARENT":
                remap = mask[0].from_node
                if remap.type == "MAP_RANGE" and remap.inputs["Value"].links:
                    z = remap.inputs["Value"].links[0]
                    from_min = remap.inputs["From Min"].default_value
                    if (
                        z.from_node.bl_idname == "ShaderNodeSeparateXYZ"
                        and z.from_socket.name == "Z"
                        and from_min >= cord_stop - 1e-5
                    ):
                        return True
        return any(
            reaches(link.from_node) for socket in node.inputs for link in socket.links
        )

    return any(reaches(node) for node in outputs)


cord = objects.get("SpinalCord")
if cord and ep.get("region") == "neck":
    mats = [m for m in cord.data.materials if m]
    rows["_cord"] = {
        "cord_zfade": bool(mats) and all(linked_height_mask(m) for m in mats),
        "rest_floor_m": min(
            (cord.matrix_world @ vertex.co).z for vertex in cord.data.vertices
        ),
    }
Path(output).write_text(json.dumps(rows))
