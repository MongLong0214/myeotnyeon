"""Native 30 fps operative macro set. All working coordinates are millimetres."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from contact import MeshCache, measure

args = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
out = Path(args["out"])
out.mkdir(parents=True, exist_ok=True)
sc = bpy.context.scene
V = Vector
origin = V((4, -181, 1461))
for obj in list(sc.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
sc.unit_settings.scale_length = .001
sc.render.fps = 30
sc.render.resolution_x, sc.render.resolution_y = args.get("size", (270, 480))
sc.render.resolution_percentage = 100
sc.render.engine = 'CYCLES'
sc.cycles.samples = args.get("samples", 8)
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'
if args.get('device', 'METAL') == 'METAL':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.refresh_devices()
    if any(d.type == 'METAL' for d in prefs.devices):
        for d in prefs.devices:
            d.use = d.type == 'METAL'
        sc.cycles.device = 'GPU'
else:
    sc.cycles.device = 'CPU'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    sc.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for p in data.polygons:
        p.use_smooth = True
    return obj

def metal(name):
    return bpy.data.materials[name]

def smooth(obj, level=1, apply=False):
    mod = obj.modifiers.new('Continuous surface', 'SUBSURF')
    mod.levels = mod.render_levels = level
    if apply:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

def section(name, rows, mat):
    """Sweep elliptical cross sections normal to Z through the instrument."""
    verts, faces = [], []
    for x, y, z, rx, ry in rows:
        for k in range(16):
            a = 2*math.pi*k/16
            verts.append((x+rx*math.cos(a), y+ry*math.sin(a), z))
    for j in range(len(rows)-1):
        for k in range(16):
            i = j*16+k
            n = j*16+(k+1)%16
            faces.append((i, n, n+16, i+16))
    faces.extend([tuple(reversed(range(16))), tuple(range(len(verts)-16, len(verts)))])
    obj = mesh(name, verts, faces, mat)
    smooth(obj, 1, True)
    return obj

def lamp(name, pos, target, watts, size, color):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size, light.color = watts, size, color
    obj = bpy.data.objects.new(name, light)
    sc.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (V(target)-obj.location).to_track_quat('-Z','Y').to_euler()

# Use the production materials and studio environment, without importing its Z-Anatomy jaw.
library = Path(args["scene"])
names = ['Hydrated enamel', 'Attached mucosa • stipple and subepithelial vessels',
         'Root surface • cementum', 'Turned surgical steel', 'Socket wall • vascular cancellous bed',
         'Oozing capillary blood', 'Polished instrument steel']
with bpy.data.libraries.load(str(library)) as (source, dest):
    dest.materials = list(names)
    dest.worlds = source.worlds[:1]
if dest.worlds:
    sc.world = dest.worlds[0]

# Draft 5 shaders take metre-space object coordinates. Feed them the same
# physical dimensions on the millimetre set and retain real relief and scatter.
for mat in dest.materials:
    tree = mat.node_tree
    for node in list(tree.nodes):
        if node.type == 'TEX_COORD':
            links = list(node.outputs['Object'].links)
            if links:
                scale = tree.nodes.new('ShaderNodeVectorMath')
                scale.operation = 'SCALE'
                scale.inputs['Scale'].default_value = .001
                tree.links.new(node.outputs['Object'], scale.inputs[0])
                for link in links:
                    tree.links.new(scale.outputs[0], link.to_socket)
        if node.type == 'BUMP':
            node.inputs['Distance'].default_value *= 1000
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Subsurface Scale'].default_value *= 1000
db = Path(args["db"])
teeth, inputs = [], {}
for _, name, file_id, *_ in csv.reader((db/'isa_element_parts.txt').open(), delimiter='\t'):
    if name != 'gingiva of upper jaw' and not (' upper ' in name and name.endswith('tooth')):
        continue
    path = db/'obj/isa_BP3D_4.0_obj_99'/(file_id+'.obj')
    inputs[file_id] = sha(path)
    verts, polys = [], []
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields[:1] == ['v']:
            verts.append(tuple(V(tuple(map(float,fields[1:4]))) - origin))
        if fields[:1] == ['f']:
            polys.append(tuple(int(x.split('/')[0])-1 for x in fields[1:]))
    is_gum = name == 'gingiva of upper jaw'
    obj = mesh(name, verts, polys, metal(names[int(is_gum)]))
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.012)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    smooth(obj, 2 if is_gum else 1, True)
    if is_gum:
        gum = obj
        for vert in gum.data.vertices:
            x,y,z = vert.co
            vert.co.y -= 1.95*math.exp(-(x/7.3)**4-((z-2)/6)**4)*max(0,min(1,(5.5-y)/3))
    else:
        teeth.append(obj)
        obj.data.materials.append(metal(names[2]))
        for poly in obj.data.polygons:
            if poly.center.z > 2.3:
                poly.material_index = 1
    if file_id == 'FJ1265':
        target = obj

# A localized soft-tissue excess for the crown-lengthening illustration. The edge
# advances away from the enamel along the blade path while both papillae stay put.
gum.shape_key_add(name='Rest')
margin = gum.shape_key_add(name='Excess facial margin')
for p in margin.data:
    x, y, z = p.co
    w = math.exp(-((x-.1)/3.8)**4 - ((z-2)/5.8)**4)
    w *= max(0,min(1,(5.5-y)/3))
    p.co.z -= 3.2*w
    p.co.y -= 1.65*w

# Partition the excess into overlapping bands. Each band recedes after the
# blade crosses it; all bands together reproduce the registered initial margin.
basis = gum.data.shape_keys.key_blocks[0]
displacements = [point.co - rest.co for point,rest in zip(margin.data,basis.data)]
bands = []
for index in range(7):
    band = margin if index == 0 else gum.shape_key_add(name=f'Margin zone {index}',from_mix=False)
    for point,rest,delta in zip(band.data,basis.data,displacements):
        coordinate = max(0,min(6,(rest.co.x+3)*1.0))
        point.co = rest.co + delta*max(0,1-abs(coordinate-index))
    bands.append(band)

# Continue the attached tissue into the vestibular reflection above the cropped
# scan and stage the recessed oral lining behind the open incisal embrasures.
def lining(name, center, radii, color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72,ring_count=32,location=center)
    obj = bpy.context.object
    obj.name = name
    for v in obj.data.vertices:
        v.co.x *= radii[0]
        v.co.y *= radii[1]
        v.co.z *= radii[2]
    mat = metal(names[1]).copy()
    bs = mat.node_tree.nodes.get('Principled BSDF')
    base = bs.inputs['Base Color']
    for link in list(base.links):
        mat.node_tree.links.remove(link)
    base.default_value = (*color,1)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj

vestibule = lining('Vestibular reflection',(0,5,25),(55,8,15),(.28,.065,.069))
palate = lining('Deep oral lining',(0,33,2),(49,9,26),(.095,.018,.026))

# Use the actual tooth mesh for the socket wall instead of an elliptical surface.
# Subtract the root and seated crown from the gingiva before lifting the incisor.
cutter = target.copy()
cutter.data = target.data.copy()
cutter.name = 'Registered socket cavity'
sc.collection.objects.link(cutter)
cutter.scale = (1.07,1.08,1.01)
cutter.hide_render = True
cutter.display_type = 'WIRE'
socket = gum.modifiers.new('Registered extraction socket','BOOLEAN')
socket.operation = 'DIFFERENCE'
socket.object = cutter
socket.solver = 'EXACT'

def surface_y(x,z,side):
    hit, loc, _, _ = target.ray_cast(V((x,side*60,z)),V((0,-side,0)))
    if not hit:
        raise ValueError(('tooth ray missed',x,z))
    return loc.y

# Close the two inner faces on the actual buccal and palatal enamel surfaces.
beaks = []
for side in [-1,1]:
    rows = []
    for z,rx,ry,space in [(-45,1.7,1.2,6),(-42,2,1.4,5.8),(-28,2,1.6,4.5),
                           (-20,2.1,1.6,.9),(-18,1.9,1.5,.45),(-15,1.35,1.35,1),
                           (-10,1.1,1.3,1.75),(-6,1.05,1.05,1.15),(-3,.98,.82,.45),
                           (-1,.85,.51,.06),(-.1,.66,.36,.02),(.45,.45,.27,.015),(.72,.12,.09,.04)]:
        # Place each working face tangent to a cross-section of the fitted tooth.
        plane = min(.72,max(-6.3,z))
        offsets = [surface_y(x,plane,side) for x in (-rx*.75,0,rx*.75)]
        y = (min(offsets) if side < 0 else max(offsets)) + side*(space+ry)
        if z < -16:
            y = 2.3+side*(space+ry)
        rows.append((0,y,z,rx,ry))
    arm = section('Extraction forceps '+('labial' if side<0 else 'palatal'),rows,metal(names[3]))
    beaks.append(arm)

# A No.15 blade tapers from a short curved belly into a bevel; the handle extends
# outside the macro field to keep the contact patch visible.
blade = section('Gingival scalpel',[(.1,0,0,.015,.012),(.22,0,.38,.23,.065),
                (.42,0,1.25,.54,.10),(.44,0,2.55,.66,.12),(.20,0,4.1,.43,.13),
                (0,0,6,.39,.14),(0,0,8,.78,.28),(0,0,12,1.35,.5),
                (0,0,29,1.5,.58)],metal(names[6]))
blade.rotation_euler = (math.radians(32),math.radians(-53),math.radians(-10))

camera = bpy.data.cameras.new('Operative macro')
cam = bpy.data.objects.new('Operative macro',camera)
sc.collection.objects.link(cam)
sc.camera = cam
camera.clip_start, camera.clip_end = .1, 1000
camera.lens = 75
camera.dof.use_dof = True
camera.dof.aperture_fstop = args.get('fstop',45)
lamp('Operating softbox',(-25,-35,36),(0,0,0),42000,29,(1,.91,.83))
lamp('Cool return',(26,-16,10),(0,0,0),20000,23,(.77,.89,1))
lamp('Wet rim',(-6,24,-6),(0,0,0),19000,16,(1,.82,.72))

def ease(x):
    x = max(0,min(1,x))
    return x*x*(3-2*x)

def blade_contact(x):
    # Find the enamel boundary each frame; the incision is in the soft lip.
    z = .7 - .11*x*x
    return V((x,surface_y(x,z,-1)-.26,z))

def setup(shot, u):
    crown = args['case']=='crown_lengthening'
    tools = []
    socket.show_render = socket.show_viewport = not crown
    for obj in [*beaks, blade]:
        obj.hide_render = True
    target.location = (0,0,0)
    target.rotation_euler = (0,0,0)
    margin.value = 0
    if crown:
        progress = {'inspect_margin':0,'incise':ease(u),'expose_crown':1,
                    'margin_payoff':1}.get(shot, ease(.49+u*.51))
        for index,band in enumerate(bands):
            band.value = 1-ease(progress*8-index)
        bpy.context.view_layer.update()
        if shot in ('incise','crown_hook'):
            blade.hide_render = False
            tools = [blade]
            pos = blade_contact(-2.8+5.6*progress)
            # Follow the actual moving facial margin, staying on its wet outer surface.
            x = pos.x
            for k in range(104):
                z = -5 + .1*k
                ok, at, _, _ = gum.ray_cast(V((x,-50,z)),V((0,1,0)))
                if ok and at.y < surface_y(x,z,-1)-.03:
                    pos = at + V((-.1,-.035,.10))
                    break
            else:
                raise ValueError(('gingiva misses blade', x))
            blade.location = pos
        focal = V((-.2,0,1.6 if shot=='inspect_margin' else 1.3))
        eye = V((12,-65,-8))
        if shot == 'incise':
            eye = V((-10,-55,-4))
        elif shot == 'expose_crown':
            eye = V((16,-50,-8))
        elif shot == 'margin_payoff':
            eye = V((12,-65,-8))
    else:
        lift = {'grasp':0,'luxate':0,'deliver_whole':ease(u)*17,'socket_payoff':17}.get(shot,8+ease(u)*7)
        tilt = (3.5*math.sin(2*math.pi*u) if shot=='luxate' else 0)
        target.rotation_euler.x = math.radians(tilt)
        target.location = (0,-.36*lift,-lift)
        for arm,side in zip(beaks,(-1,1)):
            arm.hide_render = False
            arm.rotation_euler = target.rotation_euler
            arm.location = target.location+V((0,side*(2.8*(1-ease(u)) if shot=='grasp' else 0),0))
        tools = beaks
        focal = V((0,1.4,-2.2-.43*lift))
        eye = V((23,-75,-20))
        if shot == 'socket_payoff':
            focal = V((0,2,-.6))
            eye = V((7,-24,-49))
    eye.x += (u-.5)*4
    distance = args.get('distance',1.)
    angle = math.radians(args.get('azimuth',0))
    eye.x, eye.y = eye.x*math.cos(angle)-eye.y*math.sin(angle), eye.x*math.sin(angle)+eye.y*math.cos(angle)
    cam.location = focal+eye*distance
    cam.rotation_euler = (focal-cam.location).to_track_quat('-Z','Y').to_euler()
    camera.dof.focus_distance = (cam.location-focal).length
    bpy.context.view_layer.update()
    return tools

def leader():
    graph = bpy.context.evaluated_depsgraph_get()
    anchor_x = -2.3 if args['case']=='simple_extraction' else -.8
    loc = target.matrix_world @ V((anchor_x,surface_y(anchor_x,-3.9,-1),-3.9))
    # Hidden boolean operands can still be returned by scene.ray_cast; intersect
    # only camera-visible evaluated objects in the ray's path.
    direction = (loc-cam.location).normalized()
    first = None
    best = math.inf
    for obj in [*teeth,gum,*beaks,blade,vestibule,palate]:
        if obj.hide_render:
            continue
        inv = obj.matrix_world.inverted()
        hit, p, _, _ = obj.ray_cast(inv@cam.location,inv.to_3x3()@direction,depsgraph=graph)
        if hit:
            d = (obj.matrix_world@p-cam.location).length
            if d < best:
                first,best = obj,d
    xy = world_to_camera_view(sc,cam,loc)
    x,y = xy.x*540,(1-xy.y)*960
    if first == target and 54<x<472 and 289<y<712:
        return dict(x=round(x,2),y=round(y,2),side='right',label='치관')
    return None

cache = MeshCache()
shot = args['shot']
frames = args['frames']
count = args['count']
reports = []
for f in frames:
    # The wrapper splits a single moving hook across the edit boundary.
    u = f/max(1,count-1)
    tools = setup(shot,u)
    if args['mode']=='audit':
        graph = bpy.context.evaluated_depsgraph_get()
        depths, gaps = [], []
        for tool in tools:
            a = cache.get(tool,graph,f)
            for tooth in teeth:
                b = cache.get(tooth,graph,f)
                depth,_ = measure(a,b)
                if depth > 0:
                    depths.append((tool.name,tooth.name,round(depth,6)))
                if tooth == target:
                    gap = min(b.tree.find_nearest(p)[3] for p in a.points.tolist())
                    gaps.append(round(gap,4))
        tissue_gap = None
        if blade in tools:
            tip = blade.matrix_world @ V((.10,0,0))
            hit, p, _, _ = gum.closest_point_on_mesh(tip, depsgraph=graph)
            tissue_gap = round((tip-p).length,4) if hit else None
        reports.append(dict(f=f,depths=depths,gaps=gaps,tissue_gap=tissue_gap,leader=leader()))
    else:
        path = out/f'{f:04}.png'
        sc.render.filepath = str(out/f'working-{f}.png')
        bpy.ops.render.render(write_still=True)
        Path(sc.render.filepath).replace(path)
if args['mode']=='audit':
    (out/'geometry.json').write_text(json.dumps(dict(inputs=inputs,frames=reports),ensure_ascii=False))
