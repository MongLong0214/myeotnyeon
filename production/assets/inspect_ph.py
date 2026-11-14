import bpy, sys, json, pathlib, mathutils
root = pathlib.Path('/Users/isaac/projects/verdict-kr/work/production/assets/polyhaven')
out = {}
for d in sorted(root.iterdir()):
    blends = list(d.glob('*.blend'))
    if not blends: continue
    with bpy.data.libraries.load(str(blends[0]), link=False) as (src, dst):
        names = list(src.objects); mats = list(src.materials)
    info = {'objects': names[:12], 'n_objects': len(names), 'materials': mats[:6]}
    if names:
        with bpy.data.libraries.load(str(blends[0]), link=False) as (src, dst):
            dst.objects = names
        lo = mathutils.Vector((1e9,)*3); hi = mathutils.Vector((-1e9,)*3)
        for o in dst.objects:
            if o and o.type == 'MESH':
                for c in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(c)
                    lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
        info['size_m'] = [round(x, 2) for x in (hi - lo)] if hi.x > -1e8 else None
        for o in dst.objects:
            if o: bpy.data.objects.remove(o)
    out[d.name] = info
print('JSON' + json.dumps(out, ensure_ascii=False))
