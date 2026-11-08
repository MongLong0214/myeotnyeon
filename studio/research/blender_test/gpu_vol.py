import bpy
exec(open('research/blender_test/gpu.py').read())
s = bpy.context.scene
s.cycles.volume_step_rate = 4.0; s.cycles.volume_max_steps = 64
s.cycles.samples = 256
