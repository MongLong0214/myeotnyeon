"""Build and render the portrait surgery draft from the archived jaw scenes."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector, Quaternion

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "anat_kit/blender"))
from kit import split_by_plane

D = bpy.data
SC = bpy.context.scene
FPS = 20
BEATS = json.loads((HERE / "timing.json").read_text())
V = Vector
UP = V((0, 0, 1))
ZERO = V((0, 0, 1.5))
TAU = math.tau
RNG = random.Random(31)


def world(coords):
    return ZERO + V(coords) / 1000


def frame(t):
    return round(t * FPS) + 1


def link(name, data=None):
    obj = D.objects.new(name, data)
    SC.collection.objects.link(obj)
    return obj


def mesh(name, points, faces, mat, parent=None, origin=ZERO, smooth=True):
    data = D.meshes.new(name)
    data.from_pydata([tuple(V(p) / 1000) for p in points], [], faces)
    data.update()
    obj = link(name, data)
    if mat:
        data.materials.append(mat)
    obj.parent = parent
    obj.location = (0, 0, 0) if parent else origin
    for poly in data.polygons:
        poly.use_smooth = smooth
    return obj


def tube(name, points, width, mat, parent=None, origin=ZERO, radii=None):
    curve = D.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 8
    curve.bevel_depth = width / 1000
    curve.bevel_resolution = 3
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for index, (p, co) in enumerate(zip(spline.bezier_points, points)):
        p.co = V(co) / 1000
        p.handle_left_type = p.handle_right_type = "AUTO"
        if radii:
            p.radius = radii[index]
    obj = link(name, curve)
    obj.parent = parent
    obj.location = (0, 0, 0) if parent else origin
    curve.materials.append(mat)
    return obj


def lathe(name, rings, mat, parent=None, center=(0, 0, 0), n=40):
    points = [(center[0] + r*math.cos(TAU*i/n),
               center[1] + r*math.sin(TAU*i/n), center[2] + z)
              for z, r in rings for i in range(n)]
    faces = [tuple(reversed(range(n)))]
    faces.extend((j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i)
                 for j in range(len(rings)-1) for i in range(n))
    faces.append(tuple(range((len(rings)-1)*n, len(rings)*n)))
    return mesh(name, points, faces, mat, parent)


def key(obj, prop, t, value, interpolation=None):
    target = obj.path_resolve(prop.rsplit(".", 1)[0]) if "." in prop else obj
    setattr(target, prop.rsplit(".", 1)[-1], value)
    f = frame(t)
    obj.keyframe_insert(data_path=prop, frame=f)
    if interpolation:
        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        for curve in action.layers[0].strips[0].channelbag(slot).fcurves:
            if curve.data_path == prop:
                for p in curve.keyframe_points:
                    if p.co.x == f:
                        p.interpolation = interpolation


def visible(obj, windows):
    key(obj, "hide_render", 0, True)
    for start, end in windows:
        key(obj, "hide_render", start, False)
        key(obj, "hide_render", end, True)


def pose(obj, times, scale=False):
    obj.rotation_mode = "XYZ"
    for row in times:
        t, coords, angles = row[:3]
        key(obj, "location", t, world(coords))
        key(obj, "rotation_euler", t, tuple(math.radians(a) for a in angles))
        if scale:
            key(obj, "scale", t, row[3])


def material(name, colors, rough, *, weight=0, coat=0, metal=0, noise=12, bump=.025,
             transmission=0, ior=1.45, glow=0):
    mat = D.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bs = nt.nodes.get("Principled BSDF")
    values = {"Base Color": (*colors[0], 1), "Roughness": rough, "Metallic": metal,
              "Coat Weight": coat, "Coat Roughness": .18, "Transmission Weight": transmission,
              "IOR": ior, "Subsurface Weight": weight, "Subsurface Scale": .0012,
              "Subsurface Radius": (1, .35, .23), "Emission Color": (*colors[0], 1),
              "Emission Strength": glow}
    for name, value in values.items():
        bs.inputs[name].default_value = value
    if len(colors) > 1:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise
        tex.inputs["Detail"].default_value = 3.5
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        for index, color in enumerate(colors):
            ramp.color_ramp.elements[index].position = .25 + .51*index
            ramp.color_ramp.elements[index].color = (*color, 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], bs.inputs["Base Color"])
        relief = nt.nodes.new("ShaderNodeBump")
        relief.inputs["Strength"].default_value = .28
        relief.inputs["Distance"].default_value = bump / 1000
        nt.links.new(tex.outputs["Fac"], relief.inputs["Height"])
        nt.links.new(relief.outputs["Normal"], bs.inputs["Normal"])
    return mat


def replace_materials(obj, materials):
    for index in range(len(obj.data.materials)):
        obj.data.materials[index] = materials[min(index, len(materials)-1)]


def anatomy():
    SC.frame_set(0)
    keep = {"Mandible", "GumLayer", "RimOut", "RimRam", "M2Septum", "CanalPlug",
            "Nerve2", "ThirdMolar", "Crown", "Root", "Filler"}
    for obj in list(SC.objects):
        if obj.name not in keep:
            D.objects.remove(obj, do_unlink=True)
        else:
            matrix = obj.matrix_world.copy()
            obj.animation_data_clear()
            obj.matrix_world = matrix
            obj.hide_render = False
            obj.hide_viewport = False
            obj.hide_set(False)

    main_names = ["Lower gingiva BP3D", "Lower first molar tooth.l", "Lower second molar tooth.l",
                  "Lower second premolar.l"]
    with D.libraries.load(str(HERE.parent / "main/jaw.blend"), link=False) as (_, data):
        data.objects = list(main_names)
    for obj in data.objects:
        SC.collection.objects.link(obj)
        obj.animation_data_clear()
        obj.hide_render = False
        obj.hide_viewport = False
        obj.hide_set(False)
    SC.timeline_markers.clear()
    SC.compositing_node_group = None
    for layer in list(SC.view_layers)[1:]:
        SC.view_layers.remove(layer)
    for mat in D.materials:
        if mat.node_tree:
            mat.node_tree.animation_data_clear()
    for curve in ("RimOut", "RimRam", "Nerve2"):
        D.objects[curve].data.resolution_u = 16
        D.objects[curve].data.bevel_resolution = 3
    # Hold the inherited bone's original section opacity and dress the visible materials.
    for name in ("MandBone", "Trabecular", "Cortex", "Cortex.001"):
        mat = D.materials[name]
        for node in mat.node_tree.nodes:
            if node.type == "VALUE":
                node.outputs[0].default_value = 0.0 if name != "MandBone" else node.outputs[0].default_value
    surface_nodes = D.materials["Trabecular"].node_tree.nodes
    ramp = next(node for node in surface_nodes if node.type == "VALTORGB")
    ramp.color_ramp.elements[0].color = (.45,.35,.27,1)
    ramp.color_ramp.elements[1].color = (.22,.137,.104,1)
    nerve = D.materials["Nerve2"].node_tree
    bs = nerve.nodes.get("Principled BSDF")
    for connection in list(bs.inputs["Emission Strength"].links):
        nerve.links.remove(connection)
    bs.inputs["Base Color"].default_value = (.83,.44,.028,1)
    bs.inputs["Emission Strength"].default_value = .27
    visible(D.objects["CanalPlug"], [(0, 3), (13, 44)])

    mt = {}
    mt["gum"] = material("Wet gingiva", ((.16,.021,.027),(.45,.105,.100)), .29,
                         weight=.29, coat=.55, noise=22, bump=.105)
    mt["inside"] = material("Vascular underside of reflected flap", ((.105,.008,.013),(.265,.048,.046)),
                            .28, weight=.22, coat=.59, noise=25, bump=.12)
    mt["blood"] = material("Deep red liquid blood", ((.053,.002,.006),(.15,.007,.014)), .25,
                           coat=.49, noise=19, bump=.016)
    mt["socket"] = material("Fresh alveolar socket lining", ((.083,.021,.019),(.33,.096,.062)), .47,
                            weight=.12, coat=.20, noise=22, bump=.19)
    mt["mouth"] = material("Shadowed posterior mucosa", ((.023,.004,.007),(.074,.013,.024)), .62,
                           weight=.19, coat=.09, noise=13, bump=.13)
    mt["clot"] = material("Socket coagulum", ((.048,.002,.006),(.19,.016,.025)), .32,
                          coat=.48, noise=31, bump=.10)
    mt["cortex"] = material("Wet cut cortical bone", ((.36,.22,.145),(.83,.69,.50)), .42,
                            weight=.14, coat=.21, noise=36, bump=.16)
    mt["enamel"] = material("Natural enamel", ((.59,.47,.31),(.87,.78,.61)), .29,
                            weight=.21, coat=.28, noise=15, bump=.018)
    mt["root"] = material("Cementum", ((.40,.27,.16),(.71,.56,.36)), .43,
                          weight=.15, coat=.20, noise=26, bump=.08)
    mt["dentin"] = material("Freshly sectioned dentin", ((.63,.47,.30),(.85,.72,.46)), .40,
                            weight=.19, coat=.22, noise=32, bump=.09)
    mt["steel"] = material("Wet surgical stainless steel", ((.60,.64,.69),), .22, metal=.91, coat=.25)
    mt["satin"] = material("Satin instrument grip", ((.29,.34,.39),(.46,.51,.56)), .32,
                           metal=.89, noise=85, bump=.035)
    mt["dark"] = material("Dark metal grooves", ((.09,.11,.14),), .32, metal=.84)
    mt["carbide"] = material("Machined carbide", ((.35,.33,.27),), .31, metal=.83)
    mt["silk"] = material("Braided violet suture", ((.026,.007,.045),(.14,.064,.23)), .35,
                          coat=.15, noise=90, bump=.018)
    mt["salt"] = material("Clear saline", ((.63,.76,.81),), .09, coat=.56, transmission=.46,
                          ior=1.333, glow=.37)
    mt["pinkwater"] = material("Blood diluted in saline", ((.52,.19,.18),), .16, coat=.6,
                               transmission=.22, ior=1.333, glow=.10)
    mandible = D.objects["Mandible"]
    mandible.data.materials[1] = mt["socket"]
    for name in main_names:
        replace_materials(D.objects[name], [mt["gum"] if "gingiva" in name else mt["enamel"]])
    replace_materials(D.objects["GumLayer"], [mt["gum"]])
    for name in ("ThirdMolar", "Crown", "Root", "Filler"):
        replace_materials(D.objects[name], [mt["enamel"], mt["root"], mt["dentin"]])
    # The main cut's gingiva stays anterior to the operated flap.
    gum = D.objects[main_names[0]]
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(gum.data)
    bmesh.ops.bisect_plane(bm, geom=[*bm.verts,*bm.edges,*bm.faces], dist=.00001,
                          plane_co=(0,-.044,0), plane_no=(0,-1,0), clear_inner=True)
    bm.to_mesh(gum.data)
    bm.free()
    return mt


def cameras():
    paths = [
        ("01 | Bur and canal", [(0,(31,-33.7,29),(.97,-.22,.12),36,58,-7),
                               (2.96,(31,-35.1,30.5),(.96,-.16,.23),39,59,-4)]),
        ("02 | Block, incision and reflection", [(3,(32,-26.3,43.0),(.75,-.08,.65),48,55,-4),
                                  (4.95,(31,-28.6,40.0),(.74,-.12,.68),42,56,-4),
                                  (6.8,(31,-35,37.8),(.71,-.22,.66),43,58,-2),
                                  (9.8,(33,-35.4,38.5),(.68,-.09,.73),41,58,0),
                                  (12.96,(32,-35.6,37),(.84,-.14,.55),43,57,2)]),
        ("03 | Osteotomy, sectioning, elevation", [(13,(32,-36,34),(.88,-.22,.43),45,58,2),
                          (17.4,(33,-36,33),(.96,-.18,.26),40,58,3),
                          (22.2,(33,-35.9,33),(.99,-.19,.18),36,59,4),
                          (25.8,(33,-36,36),(.91,-.21,.34),43,59,3),
                          (30.0,(33,-33.2,34),(.97,-.21,.24),42,58,1),
                          (32.96,(33,-33.4,32),(.96,-.20,.20),41,58,0)]),
        ("04 | Socket, saline, closure", [(33,(32,-34.5,33),(.89,-.25,.43),42,59,0),
                           (36.9,(33,-35.0,36),(.77,-.18,.60),42,59,-2),
                           (39.7,(32,-35.7,38),(.72,-.12,.68),41,59,-2),
                           (41.1,(31,-35.0,37),(.88,-.11,.48),41,59,0),
                           (43.96,(31,-35.6,31.7),(1,-.18,.12),36,61,2)])]
    for name, path in paths:
        data = D.cameras.new(name)
        data.sensor_fit = "HORIZONTAL"
        data.clip_start = .001
        data.clip_end = 3
        camera = link(name, data)
        camera.rotation_mode = "QUATERNION"
        for t, at, direction, distance, lens, roll in path:
            target = world(at)
            loc = target + V(direction).normalized() * distance / 1000
            rot = (target - loc).to_track_quat("-Z", "Y") @ Quaternion(UP, math.radians(roll))
            key(camera, "location", t, loc)
            key(camera, "rotation_quaternion", t, rot)
            key(data, "lens", t, lens)
        SC.timeline_markers.new(name, frame=frame(path[0][0])).camera = camera
        if path[0][0] == 0:
            SC.camera = camera


def tool_pose(rig, motion, roll_offset=0):
    rig.rotation_mode = "QUATERNION"
    for t, tip, shaft, roll in motion:
        q = UP.rotation_difference(V(shaft).normalized()) @ Quaternion(UP, math.radians(roll+roll_offset))
        key(rig, "location", t, world(tip))
        key(rig, "rotation_quaternion", t, q)
    return rig


def flat_blade(name, outline, thickness, mat, rig):
    points = [(x, side*thickness, z) for side in (-1, 1) for x,z in outline]
    n = len(outline)
    faces = [tuple(range(n)), tuple(reversed(range(n, 2*n)))]
    faces.extend((i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n))
    blade = mesh(name, points, faces, mat, rig, smooth=False)
    bev = blade.modifiers.new("Ground edges", "BEVEL")
    bev.width, bev.segments = .00009, 3
    blade.modifiers.new("Blade normals", "WEIGHTED_NORMAL")
    return blade


def instruments(mt):
    steel, satin, dark = [mt[n] for n in ("steel","satin","dark")]
    drill = link("Surgical handpiece")
    rotor = link("Rotating carbide")
    rotor.parent = drill
    lathe("Round cutting bur", [(0,.08),(.18,.56),(.43,.79),(.85,.87),(1.25,.67),
                               (1.57,.44),(1.93,.36),(6.45,.36)], mt["carbide"], rotor)
    for f in range(6):
        pts = [(r*math.cos(a+f*TAU/6),r*math.sin(a+f*TAU/6),z)
               for z,r,a in ((.12,.34,0),(.42,.75,.29),(.85,.868,.57),(1.25,.655,.86),(1.60,.40,1.05))]
        tube("Cutting flute", pts, .075, dark, rotor)
    for t in (0,44):
        key(rotor, "rotation_euler", t, (0,0,math.radians(11800*t)), "LINEAR")
    lathe("Contra-angle head", [(5.5,.52),(5.8,1.60),(6.6,2.06),(9.3,2.15),
                              (10.1,1.95),(10.75,1.42),(10.83,.8)], steel, drill)
    lathe("Head retainer", [(9.3,2.12),(9.55,2.12),(9.64,2.03)], dark, drill)
    lathe("Power handle", [(0,1.05),(.45,1.23),(6,1.23),(9,1.31),(13,1.58),
                            (16,1.85),(21,2.20),(38,2.24),(42,2.05)], satin, drill,
          center=(0,0,0)).location=(0,0,.0084)
    grip = D.objects["Power handle"]
    grip.rotation_euler = (0, math.radians(53), 0)
    for x in (-1,1):
        lathe("Irrigation port", [(5.75,.16),(6.27,.25),(6.6,.25)], dark, drill, center=(x,0,0))

    syringe = link("Aspirating dental syringe")
    syringe_parts = [
        lathe("Long bevel needle", [(0,.015),(.47,.17),(15,.177),(16,.22)], steel, syringe),
        lathe("Needle hub", [(14.7,.30),(15.0,.59),(18.7,.65),(19,.54)], satin, syringe),
        lathe("Carpule and plunger", [(18.9,1.1),(19.9,1.8),(22,2.2),(32.8,2.2),
                                     (35.8,2.40),(36.3,2.31),(37,.96),(44,.93),(44.9,.36)], steel, syringe)]
    for angle in (0, math.pi):
        x = math.cos(angle)
        syringe_parts.append(flat_blade("Carpule window", [(x*2.19,23),(x*2.23,24),(x*2.25,31.8),
                              (x*2.18,32.2)], .58, dark, syringe))
    for name, cy, radius in (("Thumb ring",49,4),("Finger loop",36.2,3.35)):
        pts=[(1.1+radius*math.cos(i*TAU/20),0,cy+radius*math.sin(i*TAU/20)) for i in range(21)]
        syringe_parts.append(tube(name, pts, .49, steel, syringe))
    syringe_path = [(3.0,(36,-21.9,59.6),(.59,.16,.80),0),
                    (3.65,(33.1,-24.2,47.4),(.57,.18,.82),0),
                    (4.25,(30.8,-25.5,41.0),(.55,.16,.84),4),
                    (4.95,(26.4,-26.7,35.4),(.58,.14,.82),5),
                    (5.65,(25.5,-26.9,34.8),(.58,.14,.82),6),
                    (6.2,(31.2,-25.1,42.5),(.58,.14,.82),5),
                    (6.7,(38,-22.4,58),(.56,.15,.83),0)]
    tool_pose(syringe,syringe_path)
    for part in syringe_parts:
        visible(part, [(3,6.75)])

    scalpel = link("No. 15 scalpel")
    scalpel_parts = [
        flat_blade("No. 15 blade", [(0,0),(-.93,.45),(-1.58,1.55),(-1.71,3.75),
                   (-1.2,5.75),(-.68,9.2),(1.04,9.2),(1.24,5.0),(1.0,2.5),(.67,.82)], .19, steel, scalpel),
        flat_blade("Ground bevel", [(0,.1),(-.85,.52),(-1.49,1.62),(-1.62,3.63),
                   (-1.21,4.58),(-1.42,2.01),(-.76,.62)], .207, satin, scalpel),
        lathe("Scalpel handle", [(7.6,1.07),(9.6,1.55),(11,1.7),(26,1.7),(30,1.55),
                                 (38,1.36),(40,1.06)], satin, scalpel)]
    for i in range(6):
        scalpel_parts.append(lathe("Scalpel grip ring", [(12+i*1.11,1.712),(12.16+i*1.11,1.712)],
                                   dark, scalpel))
    tool_pose(scalpel,[(7,(33,-47,49),(.37,-.05,.94),8),(7.4,(29.3,-43.5,39.2),(.43,-.34,.95),8),
                        (8.8,(28.8,-34.3,38.68),(.48,-.38,.92),12),
                        (9.6,(31.3,-27.7,39.3),(.39,-.32,.94),16),
                        (10.12,(36,-24,48),(.57,-.18,.85),18)])
    for part in scalpel_parts:
        visible(part, [(7,10.14)])

    for name, purpose in (("Periosteal elevator","flap"), ("Straight elevator","tooth")):
        rig = link(name)
        flat = flat_blade(name+" spatula", [(0,0),(-.86,.38),(-1.02,1.16),(-.83,2.65),
                            (-.57,4.4),(.62,4.4),(.98,1.3),(.75,.35)], .22, steel, rig)
        handle = lathe(name+" stem and grip", [(3.2,.51),(5.1,.83),(12.1,.97),
                    (13,1.9),(15.1,2.09),(28,2.28),(31,1.69)], satin, rig)
        if purpose == "flap":
            used = [(9.85,13.1)]
            path = [(9.85,(31,-44,47),(.37,-.52,.80),-14),(10.46,(28.8,-39.1,38.4),(.27,-.47,.84),3),
                    (11.1,(31.5,-38.8,38.7),(.26,-.52,.86),15),
                    (12.15,(36.8,-38.5,41.7),(.30,-.43,.86),33),
                    (13.08,(48,-45,52),(.50,-.43,.77),36)]
        else:
            used = [(23.1,27.2), (28.0,32.96)]
            path = [(23.1,(36,-32,47),(.12,.28,.94),-18),
                    (23.7,(33.9,-35.58,32.7),(.29,.42,.85),-25),
                    (24.0,(33.8,-35.52,32.5),(.37,.18,.86),26),
                    (25.15,(33,-36.35,33.1),(.48,.01,.90),47),
                    (25.76,(35.5,-36.1,39.1),(.41,.19,.89),55),
                    (26.55,(40,-35,47),(.29,.20,.93),72), (27.13,(46,-32,54),(.29,.20,.93),76),
                    (28.0,(37,-28,44),(.34,.23,.91),-4),
                    (28.42,(31.1,-31.5,32.7),(.35,.35,.88),-14),
                    (29.1,(34,-29.7,35.8),(.43,.45,.80),24),
                    (29.75,(39,-28.3,43),(.43,.36,.85),47),
                    (30.42,(33,-31.3,32.2),(.48,.32,.82),-11),
                    (31.2,(35.8,-29.3,35.4),(.45,.35,.81),49),
                    (32.7,(46,-28,51),(.38,.32,.85),68)]
        tool_pose(rig,path)
        for child in (flat,handle):
            visible(child, used)

    for obj in [*drill.children, *rotor.children]:
        if obj.type != "EMPTY":
            visible(obj,[(0,3),(13,23.1),(26.95,28.12)])
    path = [(0,(31.25,-31.7,26.45),(.77,.14,.64),10),
            (1.15,(31.21,-32.8,26.00),(.76,.13,.65),9),
            (2.35,(31.07,-34.2,26.3),(.73,.17,.66),5),
            (2.96,(31.25,-34.5,26.5),(.74,.16,.66),3),
            (13,(41,-48,51),(.36,-.32,.86),16),
            (13.55,(34.6,-42.15,36.3),(.40,-.27,.87),12),
            (14.7,(34.8,-40.7,35.1),(.43,-.10,.88),7),
            (16,(34.5,-38.2,34.8),(.50,-.07,.87),1),
            (17.1,(34.5,-36.1,34.5),(.53,-.11,.84),-6),
            (18.4,(33.8,-35.45,37.7),(.43,-.15,.86),-9),
            (19.1,(34.5,-35.58,35.8),(.53,.13,.83),-6),
            (20.5,(34.0,-35.56,33.6),(.61,.10,.79),-11),
            (21.75,(33.5,-35.59,30.9),(.66,.09,.74),-15),
            (22.55,(33.2,-35.57,28.9),(.68,.11,.72),-15),
            (23.07,(45,-30,49),(.45,.24,.86),6),
            (26.95,(46,-27,51),(.42,.22,.88),-4),
            (27.28,(32.1,-31.7,32.0),(.68,.28,.68),-8),
            (27.79,(32.6,-29.0,32.1),(.71,.34,.62),-10),
            (28.10,(47,-27,50),(.5,.3,.83),-7)]
    tool_pose(drill,path,roll_offset=81)
    return drill


def margin(s):
    y = -44 + 17*s
    x = 28.8 + 2.6*s**3 + .43*math.cos(s*TAU)
    z = 38.58 + .65*s**3 + .19*math.cos(s*TAU)
    return V((x,y,z))


def tissue_ribbon(name, mat, inner, surface, opened=None, thickness=1.1, reverse=False):
    across, along = 21, 52
    grid = [(i/across,j/along) for i in range(across+1) for j in range(along+1)]
    faces = []
    for i in range(across):
        for j in range(along):
            a = i*(along+1)+j
            faces.append((a,a+along+1,a+along+2,a+1))
    if reverse:
        faces = [tuple(reversed(face)) for face in faces]
    obj = mesh(name, [surface(u,s) for u,s in grid], faces, mat)
    obj.data.materials.append(inner)
    if opened:
        obj.shape_key_add(name="Closed")
        for label, fn, times in opened:
            shape = obj.shape_key_add(name=label)
            for point,(u,s) in zip(shape.data,grid):
                point.co = V(fn(u,s)) / 1000
            for t, value in times:
                key(obj.data.shape_keys, f'key_blocks["{label}"].value', t, value)
    solid = obj.modifiers.new("Full-thickness mucoperiosteum", "SOLIDIFY")
    solid.thickness, solid.offset = thickness/1000, -1
    solid.material_offset = solid.material_offset_rim = 1
    bevel = obj.modifiers.new("Wet, rounded edge", "BEVEL")
    bevel.width, bevel.segments = .00016, 3
    return obj


def gingiva(mt):
    def medial(u,s):
        x,y,z = margin(s)
        return (x-.035-u*(5.7+.26*math.sin(11*s)), y+u*(s-.35)*1.7,
                z-u*.92-.37*math.sin(math.pi*s)*u+.15*math.sin(12*s)*u
                -.85*(s**6+(1-s)**6)*u)

    def closed(u,s):
        x,y,z = margin(s)
        return V((x+.052+u*(5.2+3.45*math.sin(math.pi*s)+.7*s),
                  y+u*(s-.57)*2.5,
                  z+.75*math.sin(u*math.pi)-u**2.3*3.4+.25*math.sin(14*s)*u
                  -1.0*(s**9+(1-s)**9)*u))

    def reflected(u,s, settle):
        p = closed(u,s)
        taper = math.sin(math.pi*(.13+.84*s))**.56
        if settle:
            return V((p.x+(11.5-8.3*u)*taper,
                      p.y+(4.3-2.0*u)*taper+2.4*s**6,
                      p.z+(7.5+2.9*u+.85*math.sin(math.pi*u))*taper-2.6*s**8))
        lift = (1-.58*u)*taper
        return p + V((lift*5.6,lift*1.25,lift*(8.0+2.8*math.sin(u*math.pi))))

    fixed = tissue_ribbon("Lingual edge of gingival incision", mt["gum"],mt["inside"],medial,thickness=.98,reverse=True)
    flap = tissue_ribbon("Buccal mucoperiosteal flap",mt["gum"],mt["inside"],closed,[
        ("Lift",lambda u,s:reflected(u,s,False),[(0,0),(9.85,0),(10.75,.38),(11.72,1),(12.65,0)]),
        ("Reflect",lambda u,s:reflected(u,s,True),[(0,1),(2.96,1),(3,0),(11.65,0),
                                             (12.65,1),(36.66,1),(37.45,.2),(37.92,0)])],1.48)
    def rear_mucosa(u,s):
        return (18.5 - 18*u + 3.8*math.sin(s*math.pi), -66 + 60*s,
                29.7 + 44*u + 8.2*math.sin(3.0*s) - 5.4*math.sin(3.0*u)*math.sin(s*TAU))
    tissue_ribbon("Posterior oral lining", mt["mouth"], mt["mouth"], rear_mucosa,
                  thickness=3.2, reverse=True)

    for obj in (flap,fixed):
        obj["src"] = "Original surgery gingival geometry aligned to the inherited arch"
    old = D.objects["GumLayer"]
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(old.data)
    bmesh.ops.bisect_plane(bm, geom=[*bm.faces,*bm.edges,*bm.verts],dist=.00001,
                          plane_co=(0,-.0438,0),plane_no=(0,-1,0),clear_inner=True)
    bm.to_mesh(old.data)
    bm.free()

    points = [margin(i/20)+V((-.14,0,-.05+.045*math.sin(i*1.9))) for i in range(21)]
    seam = tube("Blood welling along the scalpel track",points,.137,mt["blood"],
                radii=[.11+min(1,i/3,(20-i)/2)*(.72+.2*math.sin(i*2.6)) for i in range(21)])
    for t, amount in ((0,0),(7.39,0),(8.85,.56),(9.65,1)):
        key(seam.data,"bevel_factor_end",t,amount,"LINEAR")
    visible(seam,[(7.38,44)])

    for i,s in enumerate((.11,.19,.32,.39,.52,.63,.77,.84,.91)):
        p = margin(s)
        r = .13 + RNG.random()*.12
        bead = lathe("Blood bead at the wound edge",[
            (-.01,r*.36),(.02,r),(.09,r*.81),(.16,r*.22)],mt["blood"],n=16)
        beat = 7.5+2.05*s
        bead.location = world(p+V((-.17,-.13*math.sin(i),.10)))
        visible(bead,[(beat,44)])
        key(bead,"scale",beat,(.1,.1,.1))
        key(bead,"scale",beat+.58,(1.20,1.33,.73))
        key(bead,"scale",beat+1.8,(1.73,1.47,.62))

    outer = tube("Moist reflection along the flap margin",
                 [closed(.12,i/20)+V((0,0,.033)) for i in range(21)],.047,mt["inside"])
    visible(outer,[(3,9.9),(38,44)])


def osteotomy(mt):
    center = V((0,-38.75,35.15))
    radii = [(26.7,.7),(28.25,1.10),(32.9,1.08),(34.15,1.03),(35.22,.96),
             (35.62,.79),(35.81,.50),(35.82,.08)]
    size = 54
    points = []
    for x,(ax,scale) in enumerate(radii):
        for i in range(size):
            a = i*TAU/size
            r = scale*(1+.106*math.sin(3*a+.72)+.052*math.sin(6*a-.22))
            points.append((ax+.70*math.sin(a)+.18*math.sin(5*a),
                           center.y + 6.14*r*math.cos(a),
                           center.z + 3.07*r*math.sin(a) + .46*math.cos(a)))
    faces = [tuple(reversed(range(size)))]
    faces.extend((j*size+i,j*size+(i+1)%size,(j+1)*size+(i+1)%size,(j+1)*size+i)
                 for j in range(len(radii)-1) for i in range(size))
    faces.append(tuple(range((len(radii)-1)*size,len(radii)*size)))
    cap = mesh("Buccal cortical bone to be removed",points,faces,mt["cortex"])
    visible(cap,[(10.78,18.8)])

    lip = lathe("Cutaway lip at the opening bur contact",
         [(-.60,.34),(-.34,.71),(.06,1.02),(.35,.87),(.58,.60),(.67,.30)],mt["cortex"],n=43)
    lip.rotation_euler = (math.radians(15),math.radians(49),math.radians(-9))
    lip.location = world((29.72,-33.6,25.69))
    visible(lip,[(0,3)])
    key(lip,"scale",0,(1.62,3.58,.85))
    key(lip,"scale",2.96,(1.15,3.13,.64))
    cutter = lathe("Growing bur trough",[
        (-1,.014),(-.89,.48),(-.59,.80),(-.20,.97),(.20,.97),(.59,.80),(.89,.48),(1,.014)],
        mt["cortex"],n=34)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    cutter.hide_set(True)
    times = [(0,(42,-43.8,35.6),(.18,.18,.18)),
             (13.5,(35.8,-43.0,35.8),(1.01,1.14,1.5)),
             (14.7,(35.8,-41.1,35.6),(2.14,2.22,2.1)),
             (16.0,(34.4,-39.8,35.65),(4.97,4.40,3.42)),
             (17.12,(33.9,-38.7,35.1),(7.3,6.3,4.9)),
             (18.71,(32.9,-38.7,35.1),(11,10,8))]
    for t,loc,scale in times:
        key(cutter,"location",t,world(loc))
        key(cutter,"scale",t,scale)
    mod = cap.modifiers.new("Progressive removal of the crown cover","BOOLEAN")
    mod.object, mod.operation, mod.solver = cutter,"DIFFERENCE","EXACT"


def extraction(mt):
    tooth,crown,root,kerf = [D.objects[name] for name in ("ThirdMolar","Crown","Root","Filler")]
    cutter = lathe("Advancing sectioning kerf",[
        (-1,.19),(-.95,.56),(-.72,.88),(0,1),(.72,.88),(.95,.56),(1,.19)],
        mt["dentin"],n=28)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    cutter.hide_set(True)
    for t,loc,scale in (
        (19.0,(34.7,-35.58,37.3),(1.8,.84,1.5)),
        (20.5,(34.1,-35.58,35.0),(2.2,.83,2.65)),
        (21.75,(33.1,-35.58,33.7),(2.5,.86,4.55)),
        (22.96,(33,-35.58,32.1),(2.9,.9,5.1))):
        key(cutter,"location",t,world(loc))
        key(cutter,"scale",t,scale)
    mod = kerf.modifiers.new("Open the bur groove","BOOLEAN")
    mod.object, mod.operation, mod.solver = cutter,"DIFFERENCE","EXACT"
    visible(tooth,[(0,19.04)])
    visible(crown,[(19.04,27.08)])
    visible(root,[(19.04,27.72)])
    visible(kerf,[(19.04,23.89)])
    for t,delta,angles in [
        (0,(0,0,0),(0,0,0)),(23.76,(0,0,0),(0,0,0)),(23.86,(.43,-.27,.22),(-.4,1,-3)),
        (24.05,(1.47,-.66,.93),(-5,7,-8)),(25.18,(1.47,-.66,.93),(-5,7,-8)),
        (25.63,(3.3,-.84,4.75),(-12,16,-13)),(26.09,(6,-.68,9.6),(-26,25,-21)),
        (26.8,(10,-1.5,19.6),(-31,33,-35)),(27.08,(15,-2,26),(-38,39,-45))]:
        if t == 0:
            base = crown.location.copy()
        key(crown,"location",t,base+V(delta)/1000)
        key(crown,"rotation_euler",t,tuple(map(math.radians,angles)))

    root_a = split_by_plane(root,"Superior root segment",world((31,-32,31.70)),(.05,-.10,1))
    root_b = split_by_plane(root,"Inferior root segment",world((31,-32,31.60)),(-.05,.10,-1))
    for obj, windows, states in (
        (root_a,[(27.72,30.28)],
         [(27.72,(0,0,0),(0,0,0)),(28.37,(0,0,0),(0,0,0)),(28.76,(1.7,-.43,2.05),(-5,11,-4)),
          (29.4,(6.15,.65,7.8),(-16,29,-7)),(30.24,(13.8,4.8,22.3),(-28,35,-12))]),
        (root_b,[(27.72,32.96)],
         [(27.72,(0,0,0),(0,0,0)),(30.38,(0,0,0),(0,0,0)),(30.79,(1.6,-.91,1.15),(2,5,-7)),
          (31.31,(4.5,.48,4.91),(-9,19,-12)),(32.22,(9.6,2.8,13.3),(-15,25,-19)),
          (32.95,(15.1,6.75,26.7),(-27,35,-28))])):
        obj["src"] = "Sectioned in surgery from wisdom_draft34.blend:Root"
        obj.scale = root.scale
        visible(obj,windows)
        base = obj.location.copy()
        for t,delta,rot in states:
            key(obj,"location",t,base+V(delta)/1000)
            key(obj,"rotation_euler",t,tuple(map(math.radians,rot)))

    # A narrow blood film stays on the socket floor throughout the extraction.
    p = V((29.76,-35.4,28.15))
    pool = lathe("Shallow blood pool in the empty alveolus",
                 [(-.71,1.25),(-.44,3.13),(-.12,4.16),(.31,4.42),(.62,3.71),(.74,1.65)],
                 mt["blood"],n=58)
    pool.rotation_euler = (math.radians(11),math.radians(-19),0)
    visible(pool,[(25.50,43.98)])
    for t,loc,scale in [
        (25.50,(0,-1.8,-.18),(.15,.44,.34)), (26.7,(0,-1.10,-.06),(.34,1.04,.57)),
        (32.75,(.18,0,.12),(.55,1.67,.95)), (33.76,(.22,0,.24),(.61,1.79,1.18)),
        (35.14,(.08,.32,-.21),(.45,1.48,.52)), (36.54,(.18,0,.12),(.56,1.68,.82)),
        (40.94,(.18,0,.22),(.63,1.70,1.00)), (43.96,(.19,0,.2),(.64,1.73,.8))]:
        key(pool,"location",t,world(p+V(loc)))
        key(pool,"scale",t,scale)

    clot = lathe("Blood clot beneath the sutures",
                 [(-.80,.53),(-.69,2.4),(-.20,3.78),(.46,4.02),(.94,3.45),(1.39,2.25),
                  (1.61,.14)],mt["clot"],n=44)
    for v in clot.data.vertices:
        x,y,z = v.co*1000
        v.co.z += .00024*(math.sin(y*1.28+x*1.7)+.42*math.cos(x*2.80-y*1.31))
    visible(clot,[(41,44)])
    pose(clot,[(41,(30,-35.4,28.45),(11,-22,0),(.47,1.27,.42)),
               (42.55,(30.2,-35.4,28.57),(11,-22,0),(.63,1.56,.75)),
               (43.96,(30.2,-35.4,28.55),(11,-22,0),(.64,1.58,.75))],scale=True)
    for i in range(13):
        d = RNG.uniform(-5.0,6.5)
        pos = (30.0+RNG.uniform(-.35,.45), -35.3+d, 26.72+max(0,d)*.24+RNG.uniform(0,.7))
        r=RNG.uniform(.17,.42)
        fleck = lathe("Blood in the cut socket edge", [(-.1,r*.6),(0,r),(.14,r*.75),(.2,r*.3)],
                      mt["blood"],n=13)
        fleck.location = world(pos)
        fleck.rotation_euler = (0,math.radians(58),0)
        visible(fleck,[(26 + .52*max(0,d),44)])


def saline(mt, drill):
    ang = V((.14,-.21,1))
    nozzle = link("Blunt irrigation cannula")
    tube("Bent metal irrigation tip",[(0,0,0),(0,0,3.8),(.28,0,6.9),(2.1,0,11.0),(5.3,0,15.1)],
         .34,mt["steel"],nozzle)
    grip = lathe("Irrigation cannula hub", [(13,1.1),(16,1.26),(17,1.64),(24,1.7)],
                 mt["satin"],nozzle,center=(4.2,0,0))
    grip.rotation_euler=(0,math.radians(16),0)
    tool_pose(nozzle,[(33.0,(43,-42,51),ang,0),(33.7,(36.5,-38.3,41.1),ang,7),
                      (34.2,(35.8,-39.7,37.7),ang,4),(35.05,(34.78,-33.9,36.10),ang,-5),
                      (36.02,(34.9,-29.8,37.2),ang,-9),(36.65,(42,-24,49),ang,-3)])
    for o in nozzle.children:
        visible(o,[(33,36.70)])
    drill_times = [(0,2.96),(13.64,17.52),(19.33,22.78),(27.27,27.88)]
    rinse_times = [(33.92,36.27)]
    for i,(x,z) in enumerate(((1.02,5.74),(-1.05,5.60))):
        jet=tube("Handpiece saline jet",[(x,.15,z),(x*.69,.10,4.45),(x*.31,.02,2.47),(.05,.01,.64)],
                 .077,mt["salt"],drill,radii=(.92,.8,.61,.24))
        visible(jet,drill_times)
    for i in range(3):
        jet=tube("Saline entering the socket",[(.035*i,0,-.23),(.05*i,.06,-1.25),
                 (.16*i,.14,-3.0),(.21*i,.20,-4.75),(.33*i,.34,-6.88)],
                 .106,mt["salt"],nozzle,radii=(.53,.82,.77,.69,.22))
        visible(jet,rinse_times)

    for rig,windows,counts in ((drill,drill_times,(19,12,7)),(nozzle,rinse_times,(19,0,8))):
        for mat_name,count in zip(("salt","cortex","pinkwater"),counts):
            if not count:
                continue
            for index in range(count):
                label = dict(salt="Saline droplet",cortex="Cut bone chip",pinkwater="Diluted blood droplet")[mat_name]
                o = lathe(label,[(-.92,.08),(-.54,.74),(0,1),(.55,.71),(.9,.10)],
                          mt[mat_name],rig,n=6 if mat_name=="cortex" else 10)
                intervals = []
                cycle = .48 + RNG.random()*.10
                for start,end in windows:
                    t = start + index*cycle/count
                    if start == 0:
                        t -= cycle*.55
                    while t < end-.025:
                        life = RNG.uniform(.23,.37)
                        end_flight = min(t+life,end)
                        if end_flight <= 0:
                            t += cycle
                            continue
                        a = RNG.uniform(0,TAU)
                        spread = RNG.uniform(3.0,9.5 if mat_name=="salt" else 6.5)
                        up = RNG.uniform(.7,5.3)
                        r = RNG.uniform(.086,.25) if mat_name=="salt" else RNG.uniform(.13,.30)
                        for fraction in (0,.44,.77,1):
                            ts = t + (end_flight-t)*fraction
                            if ts < 0:
                                continue
                            y = (math.sin(a)*spread*fraction -.8*fraction*fraction)
                            z = up*fraction - 3.8*fraction*fraction + (-6.0 if rig==nozzle else 1.3)
                            pos = (math.cos(a)*spread*fraction+.1,y,z)
                            stretch = (1.1-fraction*.56)
                            key(o,"location",ts,V(pos)/1000,"LINEAR")
                            key(o,"scale",ts,(r*stretch,r*.70*stretch,r*(1.65-1.02*fraction)*stretch),"LINEAR")
                        intervals.append((max(0,t),max(max(0,t)+1/FPS,end_flight)))
                        t += cycle
                visible(o,intervals)


def suture(mt):
    center = margin(.515)+V((.11,0,1.30))
    needle = link("Suture needle pivot")
    needle.location = world(center)
    start_angle, end_angle = math.radians(199), math.radians(352)
    arc = [start_angle+(end_angle-start_angle)*i/28 for i in range(29)]
    pts = [(2.7*math.cos(a),0,2.7*math.sin(a)) for a in arc]
    curve = tube("3/8-circle stainless suture needle",pts,.157,mt["steel"],needle,
                 radii=[.67]+[1.0]*23+[.91,.79,.60,.34,.09])
    visible(curve,[(37.82,39.37)])
    spin = [(37.82,-102,2.8),(38.01,-68,1.0),(38.32,-42,0),(38.62,2,0),
            (38.94,54,.2),(39.18,91,2.7),(39.34,114,7.2)]
    for t,angle,z in spin:
        key(needle,"location",t,world(center+V((max(0,z-2.8)*.43,0,z))))
        key(needle,"rotation_euler",t,(0,math.radians(angle),0))
    driver = link("Needle holder")
    for side in (-1,1):
        flat_blade("Needle holder gripping jaw",[(side*.04,0),(side*.31,.23),(side*.47,2.8),
                   (side*.66,4.95),(side*.96,4.85),(side*.73,2.26),(side*.27,.11)],.27,mt["steel"],driver)
    lathe("Needle holder shank",[(4.1,1.0),(5.2,1.21),(23,1.26),(28,1.58)],mt["satin"],driver)
    track = []
    for t,angle,z in spin:
        base = center+V((max(0,z-2.8)*.43,0,z))
        rot = Quaternion((0,1,0),math.radians(angle))
        pos = base+rot @ V(pts[9])
        track.append((t,pos+V((0,-.13,0)),(.44,-.47,.87),-15))
    tool_pose(driver,track)
    for o in driver.children:
        visible(o,[(37.82,39.37)])

    x,y,z = margin(.515)
    bite=[(x-1.39,y+.15,z-.24),(x-1.04,y+.16,z+.14),(x-.45,y+.09,z+.32),
          (x+.21,y,z+.35),(x+.98,y-.16,z+.30),(x+1.43,y-.27,z+.10),(x+1.57,y-.35,z-.35)]
    stitch=tube("Suture drawing the incision together",bite,.108,mt["silk"])
    visible(stitch,[(38.49,44)])
    for t,v in ((38.49,.06),(38.88,.53),(39.31,1)):
        key(stitch.data,"bevel_factor_end",t,v)
    for side in (-1,1):
        s=side
        pts=[(x+s*1.32,y-s*.21,z+.01),(x+s*.82,y-s*.10,z+.34),(x+.22,y-.07,z+.53),
             (x+s*.12,y+.36*s,z+.71),(x+s*.68,y+.82*s,z+1.2),
             (x+s*1.41,y+1.9*s,z+2.4),(x+s*2.66,y+4.3*s,z+6.5)]
        tight=[(x+s*1.32,y-s*.21,z+.01),(x+s*.78,y-s*.12,z+.31),(x+.20,y-.03,z+.43),
              (x+.09,y+.22*s,z+.52),(x+s*.30,y+.43*s,z+.42),
              (x+s*.76,y+.73*s,z+.49),(x+s*1.48,y+1.16*s,z+.69)]
        tail=tube("Free suture end tightening the knot",pts,.098,mt["silk"])
        for i,bp in enumerate(tail.data.splines[0].bezier_points):
            prop=f"splines[0].bezier_points[{i}].co"
            for t,co in ((39.24,pts[i]),(39.58,V(pts[i]).lerp(V(tight[i]),.25)),(40.45,tight[i])):
                key(tail.data,prop,t,V(co)/1000)
        visible(tail,[(39.23,44)])
    knot = tube("Tied suture knot",[(x-.25,y+.30,z+.44),(x-.40,y-.02,z+.54),(x-.15,y-.28,z+.62),
               (x+.25,y-.20,z+.60),(x+.39,y+.09,z+.47),(x+.10,y+.27,z+.49),(x-.25,y+.30,z+.44)],
               .112,mt["silk"])
    visible(knot,[(39.85,44)])
    origin = world((x,y,z))
    for t,s in ((39.85,.65),(40.45,1)):
        key(knot,"location",t,ZERO+(origin-ZERO)*(1-s))
        key(knot,"scale",t,(s,s,s))


def lighting():
    # Keep the inherited HDRI as a soft reflection source and put a dark oral
    # background behind the cutaway through the camera-ray branch of the world.
    nt = SC.world.node_tree
    bg = nt.nodes.get("Background")
    bg.inputs["Strength"].default_value = .12
    for node in nt.nodes:
        if node.type == "TEX_ENVIRONMENT":
            node.image.filepath = str(HERE.parents[2] / "anat_kit/assets/studio_small_09_2k.exr")
    back = nt.nodes.new("ShaderNodeBackground")
    back.inputs["Color"].default_value = (.024,.009,.012,1)
    back.inputs["Strength"].default_value = .65
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(path.outputs["Is Camera Ray"],mix.inputs[0])
    nt.links.new(bg.outputs[0],mix.inputs[1])
    nt.links.new(back.outputs[0],mix.inputs[2])
    nt.links.new(mix.outputs[0],nt.nodes.get("World Output").inputs[0])
    at = world((31,-35,34))
    for name,pos,power,width,colour in (
        ("Surgical key",(76,-61,87),.79,36,(1,.93,.86)),
        ("Soft near fill",(76,-20,44),.18,34,(.83,.92,1)),
        ("Wet tissue rim",(18,-8,72),.30,23,(1,.73,.64)),
        ("Soft enamel reflection",(31,-91,54),.13,33,(.85,.93,1)),
        ("Socket bounce",(53,-37,17),.047,24,(1,.82,.69))):
        data = D.lights.new(name,"AREA")
        data.energy,data.size,data.color=power*.19,width/1000,colour
        o=link(name,data)
        o.location=world(pos)
        o.rotation_euler=(at-o.location).to_track_quat("-Z","Y").to_euler()


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--draft",action="store_true",required=True)
    args.add_argument("--previews",action="store_true")
    args.add_argument("--animate",action="store_true")
    options = args.parse_args(sys.argv[sys.argv.index("--")+1:])
    mt = anatomy()
    cameras()
    drill = instruments(mt)
    gingiva(mt)
    osteotomy(mt)
    extraction(mt)
    saline(mt,drill)
    suture(mt)
    lighting()

    SC.render.engine = "BLENDER_EEVEE"
    SC.eevee.taa_render_samples = 4
    SC.render.resolution_x,SC.render.resolution_y = 540,960
    SC.render.resolution_percentage = 100
    SC.render.fps,SC.render.fps_base = FPS,1
    SC.render.use_motion_blur = False
    SC.render.film_transparent = False
    SC.render.image_settings.file_format = "PNG"
    SC.render.image_settings.color_mode = "RGB"
    SC.render.image_settings.compression = 8
    SC.view_settings.view_transform = "AgX"
    SC.view_settings.look = "AgX - Medium High Contrast"
    SC.view_settings.exposure = -.22
    SC.frame_start,SC.frame_end = 1,frame(BEATS[-1]["end"])-1
    SC.frame_set(1)
    D.objects["Buccal cortical bone to be removed"]["src"]="Original surgery cortical cover"
    frames = HERE/"frames"
    frames.mkdir(exist_ok=True)
    SC.render.filepath = "//frames/f_"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/"surgery_draft1.blend"))
    if options.previews:
        previews = HERE/"previews"
        previews.mkdir(exist_ok=True)
        for index,beat in enumerate(BEATS,1):
            SC.frame_set(frame(beat["sample"]))
            SC.render.filepath = str(previews/f"{index:02d}.png")
            bpy.ops.render.render(write_still=True)
    if options.animate:
        SC.render.filepath = str(frames/"f_")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
