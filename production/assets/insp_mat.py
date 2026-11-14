import bpy, pathlib
root = pathlib.Path('/Users/isaac/projects/verdict-kr/work/production/assets/polyhaven')
for aid in ['asphalt_02','clean_asphalt','concrete_pavement','brushed_concrete','painted_concrete','dark_paneled_wood','american_walnut_veneer','beige_wall_001','plastered_wall_02','large_floor_tiles_02','dark_wood','concrete_floor_02']:
    b = next((root/aid).glob('*.blend'))
    with bpy.data.libraries.load(str(b), link=False) as (src, dst):
        dst.materials = list(src.materials)
    for m in dst.materials:
        nodes = [n.bl_idname for n in m.node_tree.nodes] if m and m.use_nodes else []
        imgs = [n.image.filepath for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image]
        print('MAT', aid, '|', m.name, '| mapping' if 'ShaderNodeMapping' in nodes else '', '| disp' if 'ShaderNodeDisplacement' in nodes else '', imgs[:4])
