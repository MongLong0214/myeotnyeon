"""Low-res plates for the main wisdom-tooth episode, built from the draft34 scene."""
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

MAIN = Path(__file__).resolve().parent
EPISODE = MAIN.parent
WORK = EPISODE.parents[1]
KIT = WORK / "anat_kit"
BP3D = WORK / "research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99"
PLATES = MAIN / "plates"
PLATES.mkdir(exist_ok=True)
V = Vector
R = math.radians
D = bpy.data
ANCHORS = {}

if "--draft" not in sys.argv:
    raise SystemExit("This build requires --draft.")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def aim(camera, center):
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = (V(center) - camera.location).to_track_quat("-Z", "Y")

def draft(scene):
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 880
    scene.render.resolution_percentage = 33
    scene.render.fps = 30
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.use_motion_blur = False
    scene.render.use_persistent_data = True
    scene.cycles.samples = 6
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 5
    scene.cycles.transparent_max_bounces = 12
    scene.camera.data.dof.use_dof = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 5
    # Keep this on the CPU while the shared machine is rendering on Metal.
    scene.cycles.device = "CPU"

def render(scene, name, points=None):
    bpy.context.view_layer.update()
    if points:
        coords = {k: world_to_camera_view(scene, scene.camera, V(p)) for k, p in points.items()}
        ANCHORS[name] = {k: [round(p.x, 6), round(1-p.y, 6)] for k,p in coords.items()}
    scene.render.filepath = str(PLATES / (name + ".png"))
    bpy.ops.render.render(write_still=True)

PARTS = {
    "Mandible BP3D": ("FMA52748","FJ3289"),
    "Lower gingiva BP3D": ("FMA59764","FJ1253"),
    "Lower medial incisor.l": ("FMA57143","FJ1258"),
    "Lower lateral incisor.l": ("FMA57141","FJ1259"),
    "Lower canine.l": ("FMA55687","FJ1260"),
    "Lower first premolar.l": ("FMA55693","FJ1255"),
    "Lower second premolar.l": ("FMA55692","FJ1257"),
    "Lower first molar tooth.l": ("FMA55704","FJ1254"),
    "Lower second molar tooth.l": ("FMA55703","FJ1256"),
}

def import_part(name,material):
    fma,fj = PARTS[name]
    path = BP3D / (fj + ".obj")
    bpy.ops.wm.obj_import(filepath=str(path),forward_axis="Y",up_axis="Z")
    o=bpy.context.selected_objects[0]
    o.name=name
    o["src"]=f"bp3d:{fma}:{fj}:{sha(path)}"
    bm=bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        v.co = .001*v.co + V((0,.089,.072))
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.clear()
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth=True
    return o

def box(o):
    lo,hi=(V(tuple(fn((o.matrix_world@v.co)[j] for v in o.data.vertices) for j in range(3))) for fn in (min,max))
    return lo,hi

def simple_material(name, color, rough=.36, emission=0):
    m=D.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough
    p.inputs["Emission Color"].default_value=(*color,1)
    p.inputs["Emission Strength"].default_value=emission
    return m

def gingiva_material():
    mat = simple_material("Gingiva | soft mucosa", (.50,.21,.20), .58)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    tissue = nodes.get("Principled BSDF")
    tissue.inputs["Subsurface Weight"].default_value = .20
    tissue.inputs["Subsurface Radius"].default_value = (1.0,.32,.22)
    tissue.inputs["Subsurface Scale"].default_value = .0018
    tissue.inputs["Specular IOR Level"].default_value = .23

    # Use world metres for the subtle color and surface variation, as in draft34.
    position = nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    mottling = nodes.new("ShaderNodeTexNoise")
    mottling.inputs["Scale"].default_value = 850
    links.new(position, mottling.inputs["Vector"])
    rose = nodes.new("ShaderNodeValToRGB")
    rose.color_ramp.elements[0].color = (.43,.17,.16,1)
    rose.color_ramp.elements[1].color = (.56,.27,.25,1)
    links.new(mottling.outputs["Fac"], rose.inputs["Fac"])
    links.new(rose.outputs["Color"], tissue.inputs["Base Color"])

    grain = nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 1500
    links.new(position, grain.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .12
    bump.inputs["Distance"].default_value = .00008
    links.new(grain.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], tissue.inputs["Normal"])
    return mat

def spot_material(base,name,point,outer,inner,col,scale):
    m=base.copy()
    m.name=name
    nt=m.node_tree
    n=nt.nodes
    p=next(node for node in n if node.type=="BSDF_PRINCIPLED")
    src=p.inputs["Base Color"]
    old=src.links[0].from_socket if src.links else None
    geo=n.new("ShaderNodeNewGeometry")
    diff=n.new("ShaderNodeVectorMath")
    diff.operation="SUBTRACT"
    nt.links.new(geo.outputs["Position"],diff.inputs[0])
    diff.inputs[1].default_value=point
    mul=n.new("ShaderNodeVectorMath")
    mul.operation="MULTIPLY"
    nt.links.new(diff.outputs[0],mul.inputs[0])
    mul.inputs[1].default_value=scale
    norm=n.new("ShaderNodeVectorMath")
    norm.operation="LENGTH"
    nt.links.new(mul.outputs[0],norm.inputs[0])
    ramp=n.new("ShaderNodeMapRange")
    ramp.interpolation_type="SMOOTHSTEP"
    nt.links.new(norm.outputs["Value"],ramp.inputs["Value"])
    for k,v in zip(("From Min","From Max","To Min","To Max"),(inner,outer,1,0)):
        ramp.inputs[k].default_value=v
    mix=n.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value=src.default_value
    if old:
        nt.links.new(old,mix.inputs[1])
    mix.inputs[2].default_value=(*col,1)
    nt.links.new(ramp.outputs["Result"],mix.inputs[0])
    nt.links.new(mix.outputs[0],src)
    return m

def anatomy():
    bpy.ops.wm.open_mainfile(filepath=str(EPISODE / "wisdom_draft34.blend"))
    sc=bpy.context.scene
    camera=sc.camera
    sc.compositing_node_group=None
    for layer in list(sc.view_layers)[1:]:
        sc.view_layers.remove(layer)
    cams={}
    for f in (9,36,62,164,179,197):
        sc.frame_set(f)
        cams[f]=camera.matrix_world.copy()
    sc.frame_set(12)
    bpy.context.view_layer.update()
    bone= D.objects["Mandible"]
    original_t3= D.objects["ThirdMolar"]
    nerve= D.objects["Nerve2"]
    cut_fill=[D.objects[n] for n in ("RimOut","RimRam","M2Septum","CanalPlug")]
    old_teeth={name:D.objects[name] for name in PARTS if name.startswith("Lower") and name.endswith(".l")}
    old_gingiva=D.objects["GumLayer"]
    keep=set([bone,original_t3,nerve,old_gingiva,*cut_fill,*old_teeth.values()])
    for o in list(sc.objects):
        if o.type in {"MESH","CURVE","FONT"} and o not in keep:
            D.objects.remove(o,do_unlink=True)
        elif o.animation_data:
            mw=o.matrix_world.copy()
            o.animation_data_clear()
            o.matrix_world=mw
    sc.timeline_markers.clear()
    for d in (*D.materials,*D.lights):
        if hasattr(d,"node_tree") and d.node_tree and d.node_tree.animation_data:
            d.node_tree.animation_data_clear()
        if getattr(d,"animation_data",None):
            d.animation_data_clear()

    bone["src"]="Z-Anatomy: draft34 Mandible with original cutaway"
    old_gingiva["src"]="Z-Anatomy: draft34 GumLayer formed from the mandible crest"
    for o in cut_fill:
        o["src"]="Z-Anatomy: draft34 cut surface detailing" if o.name != "CanalPlug" else "own"
    nerve["src"]="own: draft34 hand-shaped nerve and mandibular canal path"
    original_t3["src"]="own: kit third_molar_v3b.blend as staged in draft34"
    # Replace every lower tooth mesh with the corresponding archive mesh.
    teeth={}
    for name,old in old_teeth.items():
        old.name="Original " + name
        material=old.data.materials[0]
        new=import_part(name,material)
        if name=="Lower second molar tooth.l":
            low,high=box(new)
            pivot=(low+high)/2
            rot=Matrix.Rotation(R(-12),3,"X")
            z0=low.z+.004
            for v in new.data.vertices:
                if v.co.z < z0:
                    v.co.z=z0+(v.co.z-z0)*.65
                v.co=pivot+rot@(v.co-pivot)
            bpy.context.view_layer.update()
            lo,hi=box(new)
            oldlo,oldhi=box(old)
            shift=((oldlo+oldhi)-(lo+hi))*.5
            for v in new.data.vertices:
                v.co+=shift
        D.objects.remove(old,do_unlink=True)
        teeth[name]=new
    m1=teeth["Lower first molar tooth.l"]
    m2=teeth["Lower second molar tooth.l"]
    for name in ("Enamel","Enamel2"):
        m=D.materials[name]
        for node in m.node_tree.nodes:
            if node.type=="VALUE" and node.name in ("Ghost","Emit","Tint"):
                node.outputs[0].default_value=0
    enamel=simple_material("Wisdom crown | amber",(.83,.46,.13),.29)
    root=simple_material("Wisdom root | warm ivory",(.66,.48,.29),.48)
    original_t3.data.materials.clear()
    for m in (enamel,root):
        original_t3.data.materials.append(m)
    # The intact crown/root slot assignment was already authored in draft34.
    for p in original_t3.data.polygons:
        p.material_index=min(p.material_index,1)
    source_axis=V((.05,-.985,.174)).normalized()
    original_rotation=original_t3.matrix_world.to_quaternion()
    original_position=original_t3.matrix_world.translation.copy()

    bp_bone=import_part("Mandible BP3D",simple_material("BodyParts3D | cortical bone",(.63,.53,.39),.48))
    gum_mat=gingiva_material()
    gum=import_part("Lower gingiva BP3D",gum_mat)
    cortex=bp_bone.data.materials[0]
    nodes=cortex.node_tree.nodes
    links=cortex.node_tree.links
    mix=nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value=.40
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0],mix.inputs[1])
    links.new(nodes.get("Principled BSDF").outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],nodes.get("Material Output").inputs["Surface"])
    # The archive is missing the third tooth. Ease the gingival margin over the staged crown.
    for v in gum.data.vertices:
        x,y,z=v.co
        weight=math.exp(-((x-.031)/.014)**2-((y+.032)/.013)**2)
        v.co.y+=.0065*weight*min(1,max(0,(y+.048)/.015))
        v.co.z+=.0019*weight*min(1,max(0,(z-1.527)/.012))
        posterior=min(1,max(0,(y+.046)/.012))*min(1,max(0,(x-.010)/.010))
        v.co.z-=.86*posterior*max(0,v.co.z-1.5372)
        # Thin the base while keeping the cervical margin over the third molar.
        v.co.z += .68 * max(0,1.532 - v.co.z)
    # The view is a unilateral section. Remove the detached far crest from the shot.
    bm=bmesh.new()
    bm.from_mesh(gum.data)
    cut=bmesh.ops.bisect_plane(bm,geom=[*bm.verts,*bm.edges,*bm.faces],dist=.00001,
                              plane_co=(0,0,0),plane_no=(1,0,0),clear_inner=True)
    edges=[edge for edge in cut["geom_cut"] if isinstance(edge,bmesh.types.BMEdge) and edge.is_boundary]
    bmesh.ops.holes_fill(bm,edges=edges)
    bm.to_mesh(gum.data)
    bm.free()
    sm=gum.modifiers.new("Smooth archive surface","SUBSURF")
    sm.levels=sm.render_levels=1

    m2_lo,m2_hi=box(m2)
    lesion=min((m2.matrix_world@v.co for v in m2.data.vertices),
               key=lambda p:(p-V((.0315,-.0405,1.5308))).length_squared)
    caries=spot_material(m2.data.materials[0],"Distal enamel | caries",lesion,.00195,.0007,(.09,.032,.012),(.58,.50,1.0))
    inflammation=V((.037,-.031,1.5368))
    inflamed=spot_material(gum_mat,"Gingiva | focal redness",inflammation,.006,.0022,(.55,.075,.079),(.54,1.03,1.15))
    focal_gum=spot_material(gum_mat,"Gingiva | marked margin",inflammation,.005,.0025,(.57,.063,.067),(.57,1.2,1.13))
    regular_m2=m2.data.materials[0]
    set_visible=[bone,original_t3,nerve,old_gingiva,bp_bone,gum,*cut_fill,*teeth.values()]
    draft(sc)
    for o in list(sc.objects):
        if o.type=="LIGHT" and o.name=="T3Fill":
            o.data.energy=.025
            o.data.size=.024
    for im in D.images:
        if im.source=="FILE" and ("studio_small_09" in im.name):
            im.filepath=str(KIT / "assets/studio_small_09_2k.exr")
    bpy.ops.file.pack_all()
    center=V((.029,-.038,1.530))
    two=V((.028,-.047,1.534))
    canal=V((.0302,-.035,1.522))
    shot_states = []
    def frame(index, modes, cam, axis=80, delta=(0,0,0), zoom=55, shift=(0,0,0)):
        sc.frame_set((index-1)*60)
        for o in set_visible:
            o.hide_render=o not in modes
        target_axis=V((.055,-math.sin(R(axis)),math.cos(R(axis)))).normalized()
        original_t3.rotation_mode="QUATERNION"
        original_t3.rotation_quaternion=source_axis.rotation_difference(target_axis)@original_rotation
        original_t3.location=original_position+V(delta)
        m2.data.materials[0]=caries if index in (13,14) else regular_m2
        gum.data.materials[0]=inflamed if index==11 else focal_gum if index==12 else gum_mat
        camera.matrix_world=cams[cam]
        camera.location+=V(shift)
        camera.data.lens=zoom
        tooth_top=original_t3.location+target_axis*.0047+V((.002,0,0))
        tooth_bottom=original_t3.location-target_axis*.0064+V((.002,0,0))
        points=dict(m2=two,m3=tooth_top,axis_top=tooth_top,axis_bottom=tooth_bottom,
                    nerve=canal,gum=inflammation,caries=lesion)
        # Preserve the angle and framing of each draft34 view while moving the target within it.
        if index in (1,9,10,11,12):
            aim(camera,(.020,-.046,1.533) if index==1 else (.029,-.035,1.536))
        elif index in (3,4,5,6):
            aim(camera,center)
        elif index in (13,14):
            aim(camera,(.028,-.041,1.532))
        render(sc,f"jaw_{index:02}",points)
        shot_states.append((index, modes, original_t3.location.copy(), original_t3.rotation_quaternion.copy(),
                            camera.location.copy(), camera.rotation_quaternion.copy(), zoom))

    row=[*teeth.values(),original_t3]
    section=[*row,bone,*cut_fill[:3],old_gingiva]
    neuro=[*section,nerve,cut_fill[-1]]
    external=[*row,bp_bone]
    isolated=[m1,m2,original_t3]
    exposed_gum=[*row,bone,*cut_fill[:3],gum]
    frame(1,external,62,zoom=39,shift=(.024,-.002,.011))
    frame(2,section,36)
    frame(3,isolated,36,axis=36,delta=(0,.0015,.0003),zoom=52)
    frame(4,isolated,9,axis=85,delta=(0,.0014,0),zoom=49)
    frame(5,isolated,36,axis=0,delta=(0,.002,.0006),zoom=51)
    frame(6,isolated,36,axis=-34,delta=(0,.002,.0006),zoom=53,shift=(0,0,.003))
    frame(7,neuro,164,zoom=52,shift=(.005,0,0))
    frame(8,neuro,197,zoom=43)
    frame(9,exposed_gum,62,axis=0,delta=(0,.001,.0055),zoom=49,shift=(.002,0,.017))
    frame(10,exposed_gum,36,axis=0,delta=(0,.001,.0055),zoom=56,shift=(.004,0,.018))
    frame(11,exposed_gum,36,axis=0,delta=(0,.001,.0055),zoom=61,shift=(.001,0,.015))
    frame(12,exposed_gum,9,axis=0,delta=(0,.001,.0055),zoom=63,shift=(.005,0,.012))
    frame(13,section,36,zoom=60,shift=(0,0,.002))
    frame(14,section,9,zoom=52,shift=(.005,.022,.011))
    frame(15,neuro,164,zoom=48)
    frame(16,neuro,179,zoom=46)
    for index,modes,location,rotation,camera_location,camera_rotation,lens in shot_states:
        f=(index-1)*60
        for o in set_visible:
            o.hide_render=o not in modes
            o.keyframe_insert(data_path="hide_render",frame=f)
        original_t3.location=location
        original_t3.rotation_quaternion=rotation
        original_t3.keyframe_insert(data_path="location",frame=f)
        original_t3.keyframe_insert(data_path="rotation_quaternion",frame=f)
        camera.location=camera_location
        camera.rotation_quaternion=camera_rotation
        camera.keyframe_insert(data_path="location",frame=f)
        camera.keyframe_insert(data_path="rotation_quaternion",frame=f)
        camera.data.lens=lens
        camera.data.keyframe_insert(data_path="lens",frame=f)
    for obj in (original_t3,camera,camera.data):
        action=obj.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation="CONSTANT"
    sc.frame_start,sc.frame_end=0,len(shot_states)*60-1
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(MAIN / "jaw.blend"))

anatomy()
(MAIN / "anchors.json").write_text(json.dumps(ANCHORS,indent=2)+"\n")
