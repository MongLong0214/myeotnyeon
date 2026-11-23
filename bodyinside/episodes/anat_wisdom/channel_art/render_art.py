"""Channel art renders for 바디인사이드 from wisdom_final.blend (anat_kit look: Cycles, AgX, dark bg, key + amber rim).
Usage: blender -b wisdom_final.blend --python render_art.py -- <out_dir> [frame]. Writes profile_rgba.png (1000x1000)
and banner_rgba.png (2560x1440), both with transparent film; compose_art.py adds background and text."""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; frame = int(args[1]) if len(args) > 1 else 0
s = bpy.context.scene
s.frame_set(frame)
s.render.engine = 'CYCLES'; s.cycles.samples = int(args[2]) if len(args) > 2 else 96; s.render.film_transparent = True
s.view_settings.view_transform = 'AgX'; s.view_settings.look = 'AgX - Medium High Contrast'
vis = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and not o.name.startswith('Chip')]
def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi
def light(name, loc, energy, color, size, target):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = color; d.size = size
    o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = loc
    o.rotation_euler = (target - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
def cam(name, loc, target, lens):
    c = bpy.data.cameras.new(name); c.lens = lens; c.clip_start = 0.001
    o = bpy.data.objects.new(name, c); s.collection.objects.link(o); o.location = loc
    o.rotation_euler = (target - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
lo, hi = bbox(vis); ctr = (lo + hi) / 2; size = (hi - lo).length
print('BBOX', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
tm = [o for o in vis if o.name in ('ThirdMolar', 'Lower second molar tooth.l')]
tlo, thi = bbox(tm); tc = (tlo + thi) / 2; ts = (thi - tlo).length
key = light('ArtKey', ctr + Vector((size * 1.4, -size * 0.6, size * 0.9)), 2.5, (1.0, 0.97, 0.92), size * 0.8, ctr)
rim = light('ArtRim', ctr + Vector((-size * 0.4, size * 1.2, size * 0.6)), 6.0, (1.0, 0.62, 0.25), size * 0.5, ctr)
# banner: wide 3/4 view of the whole jaw
s.render.resolution_x, s.render.resolution_y = 2560, 1440
s.camera = cam('ArtBannerCam', ctr + Vector((size * 2.2, -size * 0.25, size * 0.25)), ctr, 50)
s.render.filepath = out + '/banner_rgba.png'; bpy.ops.render.render(write_still=True)
# profile: close on the impacted molar
s.render.resolution_x = s.render.resolution_y = 1000
s.camera = cam('ArtProfCam', tc + Vector((ts * 2.6, -ts * 0.6, ts * 0.9)), tc, 50)
s.render.filepath = out + '/profile_rgba.png'; bpy.ops.render.render(write_still=True)
print('DONE')
