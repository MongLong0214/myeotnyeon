"""Render settings applied at render time. usage: Blender -b X.blend -P rset.py -a -- //out/f_ [--draft|--final] [spp] [pct]
--draft : 25 % resolution, 3 spp + denoise, motion blur off (review renders; assemble upscales)
--final : 100 %, 63 spp (or given), keeps the scene's motion-blur setting"""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type = 'METAL'; p.get_devices()
for d in p.devices: d.use = (d.type == 'METAL')
sc = bpy.context.scene; cy = sc.cycles
mode = 'final'
nums = [a for a in argv[1:] if not a.startswith('--')]
if '--draft' in argv: mode = 'draft'
if '--final-fast' in argv: mode = 'final-fast'
import os
if argv and argv[0].startswith("//"): sc.render.filepath = argv[0]
if mode == 'draft':
    sc.render.use_motion_blur = False
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 0
    # FAST DRAFT PRESET (owner, draft18+): same geometry and framing, far cheaper pixels. 25 % resolution (assemble upscales), 3 spp + OIDN denoise, no DOF, no motion blur,
    # low light-path caps, persistent data. env RS_PCT / RS_SPP override. Final renders (--final / --final-fast) are untouched.
    cy.samples = int(os.environ.get('RS_SPP', 3)); sc.render.resolution_percentage = int(os.environ.get('RS_PCT', 25))
    cy.adaptive_threshold = 0.1; cy.transparent_max_bounces = 8; cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 2; cy.volume_bounces = 0; cy.use_denoising = True
    sc.render.use_persistent_data = True
    if sc.camera and sc.camera.data: sc.camera.data.dof.use_dof = False
elif mode == 'final-fast':   # 30 s finals: measured preset (see RUNBOOK 'render presets'); env RS_SPP / RS_PCT override for experiments
    cy.samples = int(os.environ.get('RS_SPP', 24)); sc.render.resolution_percentage = int(os.environ.get('RS_PCT', 100)); sc.render.use_motion_blur = False
    cy.adaptive_threshold = 0.03; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.transparent_max_bounces = 16; cy.max_bounces = 6; cy.transmission_bounces = 4; cy.diffuse_bounces = 3; cy.glossy_bounces = 3
else:
    if nums: cy.samples = int(nums[0])
    if len(nums) > 1: sc.render.resolution_percentage = int(nums[1])
for a in argv:   # --hide=Dust,Chip : spray-off renders for A/B gates
    if a.startswith('--hide='):
        for o in bpy.data.objects:
            if any(o.name.startswith(k) for k in a[7:].split(',')):
                o.animation_data_clear() if o.animation_data else None; o.hide_render = True
if mode in ('draft', 'final-fast') and 'spp_boost' in sc:
    import json
    from bpy_extras.anim_utils import action_get_channelbag_for_slot
    boosts = json.loads(sc['spp_boost'])
    base = cy.samples
    multiplier = 3 if mode == 'final-fast' else 1
    boundaries = {sc.frame_start, *(frame for low, high, _ in boosts for frame in (low, high))}
    # Cycles reads the evaluated scene. A frame-change handler on the original
    # scene left sparse and animation renders at the base sample count.
    for frame in sorted(boundaries):
        cy.samples = max([base] + [spp * multiplier for low, high, spp in boosts if low <= frame < high])
        cy.keyframe_insert(data_path='samples', frame=frame)
    action = sc.animation_data.action
    bag = action_get_channelbag_for_slot(action, sc.animation_data.action_slot)
    for key in bag.fcurves.find('cycles.samples').keyframe_points:
        key.interpolation = 'CONSTANT'
print('RSET', mode, cy.samples, sc.render.resolution_percentage)
