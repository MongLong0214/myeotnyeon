import bpy, bmesh
g=bpy.data.objects['Gingiva']
bm=bmesh.new(); bm.from_mesh(g.data)
# loose parts
import collections
seen=set(); parts=[]
for v in bm.verts:
    if v.index in seen: continue
    stack=[v]; comp=[]
    seen.add(v.index)
    while stack:
        x=stack.pop(); comp.append(x)
        for e in x.link_edges:
            y=e.other_vert(x)
            if y.index not in seen: seen.add(y.index); stack.append(y)
    zs=[c.co.z for c in comp]; print("PART",len(comp),round(min(zs),3),round(max(zs),3))
keep=lambda n: n in ('Mandible','Gingiva','Inferior alveolar nerve.l','Mental nerve.l') or n.startswith('Lower')
for o in bpy.data.objects:
    if not keep(o.name): o.hide_render=True
