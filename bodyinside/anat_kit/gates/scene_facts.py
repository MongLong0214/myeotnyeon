"""Scene facts for the material and text-layering checks (runs inside Blender, renders nothing).
usage: Blender -b X.blend -P scene_facts.py -- OUT.json [FRAME]
Writes: rims (Rim_* curves: bevel depth in mm, render-visible at FRAME), cut structures (Vertebra*/Axis/Atlas meshes visible at
FRAME), disc material texture nodes (for the record), and every FONT object that is render-visible at any frame (3D text breaks
the rule that labels live only in the 2D layer; wisdom draft30 still carried a keyed 3D 'GapLabel')."""
import bpy, sys, json, re

a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; frame = int(a[1]) if len(a) > 1 else bpy.context.scene.frame_start
sc = bpy.context.scene; sc.frame_set(frame); bpy.context.view_layer.update(); R = {'blend': bpy.data.filepath, 'frame': frame}

def keyed_visible(o):
    """True if the object renders on any frame: hide_render False now, or a hide_render key with value 0."""
    if not o.hide_render: return True
    ad = o.animation_data
    if ad and ad.action:
        act = ad.action
        fcs = list(act.fcurves) if hasattr(act, 'fcurves') else [fc for ly in act.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            if fc.data_path == 'hide_render' and any(k.co[1] < 0.5 for k in fc.keyframe_points): return True
    return False

R['rims'] = [{'name': o.name, 'bevel_mm': round(o.data.bevel_depth * 1000, 3), 'visible': not o.hide_render}
             for o in bpy.data.objects if o.name.startswith('Rim_') and o.type == 'CURVE']
R['cut_structures'] = [o.name for o in bpy.data.objects if o.type == 'MESH' and re.match(r'(Vertebra|Axis|Atlas)', o.name) and not o.hide_render]
R['disc_materials'] = {m.name: sorted({nd.type for nd in m.node_tree.nodes if nd.type.startswith('TEX')})
                       for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Disc')
                       for m in [s.material for s in o.material_slots if s.material] if m.use_nodes}
R['font_objects_rendered'] = [o.name for o in bpy.data.objects if o.type == 'FONT' and keyed_visible(o)]
json.dump(R, open(out, 'w'), indent=1); print('SCENE_FACTS', out)
