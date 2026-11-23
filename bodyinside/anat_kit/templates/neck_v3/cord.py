"""End the displayed cord inside the last pictured vertebra in each camera plate."""

import sys
from pathlib import Path

import bmesh
import bpy


def clip_displayed_cord():
    cord = bpy.data.objects["SpinalCord"]
    floor = min(v.co.z for v in bpy.data.objects["Vertebra T1"].data.vertices)
    mesh = bmesh.new()
    try:
        mesh.from_mesh(cord.data)
        cut = bmesh.ops.bisect_plane(
            mesh,
            geom=mesh.verts[:] + mesh.edges[:] + mesh.faces[:],
            plane_co=(0, 0, floor),
            plane_no=(0, 0, 1),
            clear_inner=True,
        )
        rim = [
            edge
            for edge in cut["geom_cut"]
            if isinstance(edge, bmesh.types.BMEdge) and edge.is_boundary
        ]
        bmesh.ops.holes_fill(mesh, edges=rim)
        mesh.to_mesh(cord.data)
    finally:
        mesh.free()
    for mat in cord.data.materials:
        # Preserve upstream material and transparency animation. Align the topmost
        # existing world-height fade with the new physical end of the cord.
        fades = []
        for node in mat.node_tree.nodes:
            if node.type != "MAP_RANGE" or not node.inputs["Value"].links:
                continue
            z = node.inputs["Value"].links[0]
            if z.from_node.type != "SEPXYZ" or z.from_socket.name != "Z":
                continue
            vectors = z.from_node.inputs[0].links
            if (
                vectors
                and vectors[0].from_node.type == "NEW_GEOMETRY"
                and vectors[0].from_socket.name == "Position"
            ):
                fades.append(node)
        fade = max(fades, key=lambda node: node.inputs["From Min"].default_value)
        fade.inputs["From Min"].default_value = floor
        fade.inputs["From Max"].default_value = floor + 0.02


source, destination = map(Path, sys.argv[sys.argv.index("--") + 1 :])
bpy.context.preferences.filepaths.save_version = 0
bpy.context.preferences.filepaths.use_relative_paths = False
for name in ("neck.blend", "neck_A.blend", "neck_B.blend"):
    bpy.ops.wm.open_mainfile(filepath=str(source / name))
    bpy.ops.file.make_paths_absolute()
    clip_displayed_cord()
    bpy.ops.wm.save_as_mainfile(filepath=str(destination / name), relative_remap=False)
