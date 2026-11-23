"""Blender mesh contact gate. Import MeshCache and measure for an edited timeline,
using the evaluated geometry on each output frame.
Depths are in mm. Geometry is evaluated after shape keys and modifiers.
"""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree


def use_render_modifiers(objects):
    """Match the render modifier stack when evaluating a background viewport graph."""
    for obj in objects:
        for mod in obj.modifiers:
            if mod.show_viewport != mod.show_render:
                mod.show_viewport = mod.show_render
            if mod.type == 'SUBSURF' and mod.levels != mod.render_levels:
                mod.levels = mod.render_levels


class Surface:
    def __init__(self, points, triangles):
        self.points = points
        self.faces = triangles
        self.lo = points.min(axis=0)
        self.hi = points.max(axis=0)
        self._tree = None
        self._representatives = None

    def representatives(self):
        if self._representatives is None:
            # One vertex per connected shell makes a disjoint-surface containment
            # test independent of ray precision at near-tangent points.
            parent = list(range(len(self.points)))
            def root(i):
                while i != parent[i]:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            for a,b,c in self.faces.tolist():
                parent[root(a)] = root(b)
                parent[root(c)] = root(b)
            self._representatives = self.points[list({root(i) for i in self.faces.ravel().tolist()})]
        return self._representatives

    @property
    def tree(self):
        if self._tree is None:
            self._tree = BVHTree.FromPolygons(self.points.tolist(), self.faces.tolist(), all_triangles=True)
        return self._tree


class MeshCache:
    def __init__(self):
        self.local = {}
        self.world = {}

    def get(self, obj, graph, pose):
        # Static bevels and subdivisions are reusable. Boolean operands and shape
        # keys can change locally even if the object's world transform is fixed.
        dynamic = any(m.type not in ('BEVEL', 'WEIGHTED_NORMAL', 'SUBSURF') for m in obj.modifiers)
        keys = getattr(obj.data, 'shape_keys', None)
        key = (pose if dynamic else None, tuple(b.value for b in keys.key_blocks) if keys else None)
        ev = obj.evaluated_get(graph)
        mx = np.array(ev.matrix_world)
        world_key = (key, mx.tobytes())
        if obj.name in self.world and self.world[obj.name][0] == world_key:
            return self.world[obj.name][1]
        if obj.name not in self.local or self.local[obj.name][0] != key:
            mesh = ev.to_mesh()
            try:
                mesh.calc_loop_triangles()
                points = np.empty(len(mesh.vertices)*3, dtype=np.float32)
                mesh.vertices.foreach_get('co', points)
                faces = np.empty(len(mesh.loop_triangles)*3, dtype=np.int32)
                mesh.loop_triangles.foreach_get('vertices', faces)
                self.local[obj.name] = (key, points.reshape(-1,3), faces.reshape(-1,3))
            finally:
                ev.to_mesh_clear()
        _, points, faces = self.local[obj.name]
        surf = None
        if len(faces):
            factor = bpy.context.scene.unit_settings.scale_length * 1000
            surf = Surface((points @ mx[:3,:3].T + mx[:3,3])*factor, faces)
        self.world[obj.name] = (world_key, surf)
        return surf


def inside_distance(p, surf, sheet=False):
    if sheet:
        # Open, upward-facing cortical floor. Only the footprint bounded by the
        # evaluated surface represents material, including its sloping rim.
        hit = surf.tree.ray_cast(p, (0,0,1))
        if hit[0] is None:
            return 0.
    else:
        # Odd-even crossings also work for closed meshes with inward normals.
        votes = 0
        for ix,direction in enumerate(((.312713,.479923,.819625),(-.8171,.5033,.2825),(.2354,-.9012,.3638))):
            pt = p
            count = 0
            while True:
                hit, _, _, _ = surf.tree.ray_cast(pt, direction)
                if hit is None:
                    break
                count += 1
                pt = tuple(hit[i]+.0012*direction[i] for i in range(3))
                if count > 256:
                    raise ValueError('Unresolved mesh parity')
            votes += count % 2
            if votes >= 2:break
            if ix+1-votes >= 2:return 0.
    return surf.tree.find_nearest(p)[3]


def sample_depth(source, target, crossing, sheet=False):
    lo, hi = target.lo-.001, target.hi+.001
    if sheet:
        lo = lo.copy()
        lo[2] = -np.inf
    pts = source.points
    samples = [pts[((pts >= lo) & (pts <= hi)).all(axis=1)]]
    if crossing:
        tri = pts[source.faces[list(crossing)]]
        samples += [tri.mean(axis=1), ((tri+np.roll(tri,1,axis=1))*.5).reshape(-1,3)]
        # Thin crossings can lie wholly between vertices on a long shank face.
        # Include points within the shared box even when all original corners lie outside.
        for vertices in tri:
            poly = list(vertices)
            for axis in range(3):
                for sign,bound in ((1,lo[axis]),(-1,hi[axis])):
                    if not poly or not np.isfinite(bound):
                        continue
                    clipped = []
                    prev = poly[-1]
                    for cur in poly:
                        a, b = sign*(prev[axis]-bound), sign*(cur[axis]-bound)
                        if (a<0) != (b<0):
                            clipped.append(prev+(cur-prev)*(a/(a-b)))
                        if b>=0:
                            clipped.append(cur)
                        prev = cur
                    poly = clipped
            if poly:
                samples.append(np.mean(poly,axis=0)[None,:])
    all_pts = np.unique(np.concatenate(samples).round(5),axis=0)
    all_pts = all_pts[((all_pts>=lo)&(all_pts<=hi)).all(axis=1)]
    return max((inside_distance(p,target,sheet) for p in all_pts.tolist()), default=0.)


def measure(tool, target, *, sheet=False):
    if tool is None or target is None:
        return 0., 0
    if np.any(tool.lo > target.hi+.0001) or np.any((tool.hi < target.lo-.0001)[:2 if sheet else 3]):
        return 0., 0
    pairs = tool.tree.overlap(target.tree)
    if not pairs and not sheet:
        # Disjoint surface shells can still enclose each other. Test one vertex per
        # connected component before measuring enclosed vertices in either direction.
        def contains(source, dest):
            pts=source.representatives()
            within=pts[((pts>=dest.lo)&(pts<=dest.hi)).all(axis=1)]
            return any(inside_distance(p,dest)>0 for p in within.tolist())
        if not contains(tool,target) and not contains(target,tool):
            return 0.,0
    a = sample_depth(tool,target,{i for i,_ in pairs},sheet)
    b = sample_depth(target,tool,{j for _,j in pairs}) if not sheet else 0.
    return max(a,b),len(pairs)

