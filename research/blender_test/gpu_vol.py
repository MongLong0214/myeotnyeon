import bpy
exec(open('/Users/isaac/projects/verdict-kr/work/research/blender_test/gpu.py').read())
s = bpy.context.scene
s.cycles.volume_step_rate = 4.0; s.cycles.volume_max_steps = 64
s.cycles.samples = 256
