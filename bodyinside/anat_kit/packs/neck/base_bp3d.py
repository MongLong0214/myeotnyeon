# Stage A (BodyParts3D Release 4.0, CC BY 4.0): import the parts used by the neck episode from the DBCLS OBJ archive into base.blend.
# usage: Blender -b --factory-startup -P base_bp3d.py ; every object carries custom property "src" = "bp3d:<FMA>:<FJ file>:<sha256>" (provenance gate)
import bpy, csv, hashlib, json, os
D = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../../research/anatomy3d/bodyparts3d_4.0/'); OBJ = D + 'obj/isa_BP3D_4.0_obj_99/'
OFFSET = (0.0, 0.089, 0.072)      # BodyParts3D body coordinates (mm) -> the neck rig frame used by build.py (metres)
m = {}
for r in csv.reader(open(D + 'isa_element_parts.txt'), delimiter='\t'):
    if r[0].startswith('FMA'): m.setdefault(r[0], []).append(r[2])
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
PARTS = {   # object name: [FMA ids]  (concept ids from isa_parts_list_e.txt, Release 4.0)
 'Atlas (C1)': ['FMA12519'], 'Axis (C2)': ['FMA12520'], 'Vertebra C3': ['FMA12521'], 'Vertebra C4': ['FMA12522'], 'Vertebra C5': ['FMA12523'], 'Vertebra C6': ['FMA12524'], 'Vertebra C7': ['FMA12525'],
 'Vertebra T1': ['FMA9165'], 'Vertebra T2': ['FMA9187'], 'Vertebra T3': ['FMA9209'], 'Vertebra T4': ['FMA9248'],
 'SkullFrontal': ['FMA52734'], 'SkullOccipital': ['FMA52735'], 'SkullParietal': ['FMA9613'], 'SkullTemporal': ['FMA52737'], 'SkullSphenoid': ['FMA52736'], 'SkullZygomatic': ['FMA52747'], 'SkullMaxilla': ['FMA9711'],
 'Mandible': ['FMA52748'],
 'Clavicle.l': ['FMA13323'], 'Scapula.l': ['FMA13396'], 'Clavicle.r': ['FMA13322'], 'Scapula.r': ['FMA13395'],
 'TeethUpper': ['FMA55682', 'FMA55683', 'FMA55799', 'FMA55690', 'FMA55691', 'FMA55699', 'FMA55700'],
 'TeethLower': ['FMA57143', 'FMA57141', 'FMA55687', 'FMA55693', 'FMA55692', 'FMA55704', 'FMA55703'],
 'Brain': ['FMA61820', 'FMA67944', 'FMA61993', 'FMA61998'],
 'Splenius capitis.l': ['FMA22729'], 'Splenius cervicis.l': ['FMA22727'], 'Semispinalis capitis.l': ['FMA22877'], 'Semispinalis cervicis.l': ['FMA22875'], 'Levator scapulae.l': ['FMA32541'],
 'Descending part of trapezius.l': ['FMA33587'], 'Sternocleidomastoid.l': ['FMA13409'], 'Longus colli.l': ['FMA46284', 'FMA46286', 'FMA46288'],
}
bpy.ops.wm.read_factory_settings(use_empty=True); prov = {}
for name, fmas in PARTS.items():
    objs = []; src = []
    for fma in fmas:
        for fj in m[fma]:
            p = OBJ + fj + '.obj'; before = set(bpy.data.objects); bpy.ops.wm.obj_import(filepath=p, forward_axis='Y', up_axis='Z')   # identity: the OBJ is already Z-up, anterior = -y
            objs += list(set(bpy.data.objects) - before); src.append('bp3d:%s:%s:%s' % (fma, fj, sha(p)))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name; o.data.name = name; o['src'] = ' | '.join(src); prov[name] = src
    o.scale = (0.001, 0.001, 0.001); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.location = OFFSET; bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)   # the OBJ stores unwelded triangles: weld -> closed manifold solids
    bm.to_mesh(o.data); bm.free()
    for pg in o.data.polygons: pg.use_smooth = True
    print('K', name, len(o.data.vertices))
json.dump(prov, open(os.environ.get('ANAT_EPISODE', os.getcwd()) + '/bp3d_provenance.json', 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.environ.get('ANAT_EPISODE', os.getcwd()),'base.blend'))
