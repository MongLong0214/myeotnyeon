# Blender 5.2 headless: render 6 evenly spaced frames per animation as tiles.
# usage: Blender -b --factory-startup --python-exit-code 1 --python render_tiles.py -- job.json
# job = {"src": path, "kind": "glb"|"bvh", "height_units": float (bvh only), "tile_dir": dir,
#        "anims": [{"tag": str, "action": str (glb), "start": int|null, "end": int|null}],
#        "azimuth": deg (camera angle from character front, default 55), "n": 6}
import bpy, bmesh, sys, json, os, math
from mathutils import Vector, Matrix

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
N = job.get('n', 6)
TW, TH = 320, 270
os.makedirs(job['tile_dir'], exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def plaster(name, rgb=(0.62, 0.61, 0.59)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = 0.85
    return m


PL = plaster('Plaster')
PLJ = plaster('PlasterJoint', (0.5, 0.5, 0.49))

# ---------------------------------------------------------------- load asset
src = job['src']
if job['kind'] == 'glb':
    bpy.ops.import_scene.gltf(filepath=src)
elif job['kind'] == 'fbx':
    bpy.ops.import_scene.fbx(filepath=src)
elif job['kind'] == 'bvh':
    s = 1.62 / job['height_units']  # head-joint height -> ~1.62 m (stature ~1.75 m)
    bpy.ops.import_anim.bvh(filepath=src, global_scale=s, update_scene_fps=True, update_scene_duration=True,
                            rotate_mode='NATIVE')
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'):
        bpy.data.objects.remove(o)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    for i, slot in enumerate(o.material_slots):
        slot.material = PLJ if (slot.material and 'joint' in slot.material.name.lower()) else PL
    if not o.material_slots:
        o.data.materials.append(PL)


def radius(name, L):
    n = name.lower()
    if 'finger' in n or 'thumb' in n or n[1:].startswith('finger') or n in ('lfingers', 'rfingers'):
        return 0.013
    if 'hand' in n or 'wrist' in n: return 0.034
    if 'forearm' in n or 'elbow' in n or 'lowerarm' in n: return 0.038
    if 'toe' in n: return 0.032
    if 'foot' in n or 'ankle' in n: return 0.042
    if 'upleg' in n or 'thigh' in n or n in ('lefthip', 'righthip'): return 0.072
    if 'hipjoint' in n: return 0.075
    if 'leg' in n or 'knee' in n or 'shin' in n: return 0.052
    if 'collar' in n or 'clavicle' in n: return 0.045
    if 'shoulder' in n: return 0.048 if L > 0.2 else 0.05
    if 'arm' in n: return 0.048
    if 'neck' in n: return 0.048
    if n == 'hips': return 0.13
    if 'spine' in n or 'chest' in n or 'back' in n: return 0.12
    return 0.05


if job['kind'] == 'bvh':
    # build a faceless capsule mannequin skinned 1:1 to the BVH bones
    me = bpy.data.meshes.new('ProxyMannequin')
    bm = bmesh.new()
    groups = []
    mw = arm.matrix_world
    for bi, b in enumerate(arm.data.bones):
        h, t = mw @ b.head_local, mw @ b.tail_local
        L = (t - h).length
        r = radius(b.name, L)
        if L < 0.015: continue
        vs = []
        if 'head' in b.name.lower() and 'end' not in b.name.lower():
            c = (h + t) / 2
            res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.105)
            d = (t - h).normalized()
            rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ rot @ Matrix.Diagonal((0.85, 0.95, 1.15, 1)), verts=res['verts'])
            vs += res['verts']
        else:
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r, radius2=r * 0.9, depth=L)
            d = (t - h).normalized()
            rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=Matrix.Translation((h + t) / 2) @ rot, verts=res['verts'])
            vs += res['verts']
            for p, rr in ((h, r), (t, r * 0.9)):
                s2 = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=rr)
                bmesh.ops.translate(bm, vec=p, verts=s2['verts'])
                vs += s2['verts']
        groups.append((b.name, vs))
    bm.verts.index_update()
    groups = [(n, [v.index for v in vs if v.is_valid]) for n, vs in groups]
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('ProxyMannequin', me)
    scn.collection.objects.link(ob)
    for name, idx in groups:
        vg = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
        vg.add(idx, 1.0, 'REPLACE')
    ob.parent = arm
    ob.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = ob.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm
    me.materials.append(PL)
    for p in me.polygons: p.use_smooth = True
    meshes = [ob]

# ---------------------------------------------------------------- scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x, scn.render.resolution_y = TW, TH
scn.render.film_transparent = False
scn.render.image_settings.file_format = 'PNG'
try:
    scn.eevee.taa_render_samples = 32
except Exception:
    pass
w = bpy.data.worlds.new('W')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.012, 0.014, 0.02, 1)
scn.world = w
# ground with 0.5 m checker so sliding is visible
bpy.ops.mesh.primitive_plane_add(size=60)
gnd = bpy.context.active_object
gm = bpy.data.materials.new('Ground')
gm.use_nodes = True
nt = gm.node_tree
ck = nt.nodes.new('ShaderNodeTexChecker')
ck.inputs['Scale'].default_value = 120  # 60 m / 120 = 0.5 m squares
ck.inputs['Color1'].default_value = (0.03, 0.03, 0.033, 1)
ck.inputs['Color2'].default_value = (0.055, 0.055, 0.06, 1)
nt.links.new(ck.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
gnd.data.materials.append(gm)

cam_data = bpy.data.cameras.new('Cam')
cam_data.lens = 50
cam = bpy.data.objects.new('Cam', cam_data)
scn.collection.objects.link(cam)
scn.camera = cam


def light(name, kind, energy, loc, size=2.0, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA': ld.size = size
    lo = bpy.data.objects.new(name, ld)
    scn.collection.objects.link(lo)
    lo.parent = cam
    lo.location = loc  # camera-local
    tc = lo.constraints.new('TRACK_TO')
    return lo, tc


tgt = bpy.data.objects.new('Target', None)
scn.collection.objects.link(tgt)
for nm, kind, e, loc, col in (('Key', 'AREA', 650, (-2.8, 2.2, 0.5), (1, 0.96, 0.9)),
                              ('Fill', 'AREA', 250, (3.0, -0.6, 0.8), (0.85, 0.9, 1.0)),
                              ('Rim', 'AREA', 1100, (0.8, 2.5, -8.5), (0.9, 0.95, 1.0))):
    lo, tc = light(nm, kind, e, loc, 2.5, col)
    tc.target = tgt
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
ctc = cam.constraints.new('TRACK_TO')
ctc.target = tgt
ctc.track_axis = 'TRACK_NEGATIVE_Z'
ctc.up_axis = 'UP_Y'

ROOTS = ('DEF-hips', 'pelvis', 'Hips', 'hips', 'mixamorig:Hips')
hb = next((n for n in ROOTS if n in arm.pose.bones), arm.pose.bones[0].name)
LEGS = [('DEF-thigh.L', 'DEF-thigh.R'), ('thigh_l', 'thigh_r'), ('LeftUpLeg', 'RightUpLeg'), ('LeftHip', 'RightHip')]
lr = next((p for p in LEGS if p[0] in arm.pose.bones), None)


def bone_world(name):
    return arm.matrix_world @ arm.pose.bones[name].head


def facing():
    if lr:
        left = bone_world(lr[0]) - bone_world(lr[1])
        left.z = 0
        f = left.cross(Vector((0, 0, 1)))
        if f.length > 1e-6: return f.normalized()
    return Vector((0, -1, 0))


def mesh_bounds():
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in meshes:
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            p = ev.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
    return mn, mx


meta = []
ad = arm.animation_data or arm.animation_data_create()
for a in job['anims']:
    if job['kind'] in ('glb', 'fbx'):
        act = bpy.data.actions[a['action']]
        for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
        ad.action = act
        if hasattr(ad, 'action_slot') and act.slots and ad.action_slot is None:
            ad.action_slot = act.slots[0]
        fr = act.frame_range
    else:
        act = ad.action
        fr = act.frame_range
    s0 = a.get('start') if a.get('start') is not None else int(fr[0])
    s1 = a.get('end') if a.get('end') is not None else int(fr[1])
    frames = [round(s0 + (s1 - s0) * i / (N - 1)) for i in range(N)]
    scn.frame_set(frames[0])
    fwd = facing()
    az = math.radians(a.get('azimuth', job.get('azimuth', 40)))
    camdir = Matrix.Rotation(az, 3, 'Z') @ fwd
    info = {'tag': a['tag'], 'frames': frames, 'hips': []}
    for i, f in enumerate(frames):
        scn.frame_set(f)
        hp = bone_world(hb)
        mn, mx = mesh_bounds()
        cz = 0.85
        tgt.location = (hp.x, hp.y, cz)
        cam.location = (hp.x + camdir.x * job.get('dist', 4.8), hp.y + camdir.y * job.get('dist', 4.8), 1.25)
        scn.render.filepath = os.path.join(job['tile_dir'], '%s_%d.png' % (a['tag'], i))
        bpy.ops.render.render(write_still=True)
        info['hips'].append([round(v, 3) for v in hp] + [round(mx.z, 3), round(mn.z, 3)])
    meta.append(info)
    print('RENDERED', a['tag'], frames)
json.dump({'fps': scn.render.fps, 'anims': meta}, open(os.path.join(job['tile_dir'], 'meta_%s.json' % os.path.basename(job.get('name', 'job'))), 'w'), indent=1)
