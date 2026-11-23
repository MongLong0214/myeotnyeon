"""Render settings applied at render time. usage: Blender -b X.blend -P rset.py -a -- //out/f_ [--draft|--final] [spp] [pct]
--draft : 50 % resolution, 16 spp + denoise, motion blur off (review renders; assemble upscales)
--final : 100 %, 64 spp (or given), keeps the scene's motion-blur setting"""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type = 'METAL'; p.get_devices()
for d in p.devices: d.use = (d.type == 'METAL')
sc = bpy.context.scene; cy = sc.cycles
mode = 'final'
nums = [a for a in argv[1:] if not a.startswith('--')]
if '--draft' in argv: mode = 'draft'
if argv and argv[0].startswith("//"): sc.render.filepath = argv[0]
if mode == 'draft':
    cy.samples = 16; sc.render.resolution_percentage = 50; sc.render.use_motion_blur = False
    cy.adaptive_threshold = 0.05; cy.transparent_max_bounces = 12; cy.max_bounces = 6; cy.use_denoising = True
else:
    if nums: cy.samples = int(nums[0])
    if len(nums) > 1: sc.render.resolution_percentage = int(nums[1])
print('RSET', mode, cy.samples, sc.render.resolution_percentage)
