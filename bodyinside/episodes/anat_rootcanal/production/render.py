"""Render native 30 fps plates. Only complete files enter the resumable frame sequence."""
from itertools import groupby
import os
from pathlib import Path
import time

import bpy

episode = Path(__file__).resolve().parent.parent
scene = bpy.context.scene
draft = os.getenv('DRAFT', '1') == '1'
reveal = os.getenv('SECTION_REVEAL') == '1'
variant = 'draft' if draft else 'final'
out = episode / 'production/.cache' / (variant + '_reveal' if reveal else variant)
out.mkdir(exist_ok=True)
extension = 'jpg' if draft else 'png'
settings = bpy.context.preferences.addons['cycles'].preferences
settings.compute_device_type = 'METAL'
settings.refresh_devices()
if not any(device.type == 'METAL' for device in settings.devices):
    raise RuntimeError('Metal device unavailable')
for device in settings.devices:
    device.use = device.type == 'METAL'
scene.cycles.device = 'GPU'
scene.cycles.samples = 8 if draft else 24
scene.cycles.adaptive_min_samples = 3 if draft else 6
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
if not draft and hasattr(scene.cycles, 'denoising_use_gpu'):
    scene.cycles.denoising_use_gpu = True
scene.render.use_persistent_data = True
scene.render.resolution_percentage = 50 if draft else 100
scene.render.image_settings.file_format = 'JPEG' if draft else 'PNG'
scene.render.image_settings.quality = 98
scene.render.image_settings.compression = 18
scene.render.image_settings.color_mode = 'RGB'
frames = range(930) if 'FRAMES' not in os.environ else sorted(set(map(int, os.environ['FRAMES'].split(','))))

def destination(frame):
    return out / f'{frame:04}.{extension}'

def stills():
    exterior, section = [], []
    if reveal:
        exterior = [o for o in scene.objects if o.name.startswith('Restored exterior •')]
        section = [o for o in scene.objects if o.name.startswith(('Prepared M1 section', 'Prepared access core', 'Ceramic crown in section', 'Sealer interface', 'Trimmed gutta-percha'))]
        for obj in exterior + section:
            for layer in obj.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            if curve.data_path in ('hide_render', 'hide_viewport'):
                                curve.mute = True
    working = out / f'writing.{extension}'
    scene.render.filepath = str(working)
    for frame in (range(862, 875) if reveal else frames):
        if destination(frame).exists():
            continue
        scene.frame_set(frame)
        for obj in exterior:
            obj.hide_render = obj.hide_viewport = frame >= 868
        for obj in section:
            obj.hide_render = obj.hide_viewport = frame < 868
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        working.replace(destination(frame))
        print('PLATE', frame, round(time.monotonic() - start, 2), flush=True)

def native_animation():
    # Keep the Cycles session and the denoiser warm between successive full-size frames.
    incoming = out / 'incoming'
    incoming.mkdir(exist_ok=True)
    scene.render.filepath = str(incoming / 'frame_####')
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    last = time.monotonic()
    def publish(frame):
        nonlocal last
        path = incoming / f'frame_{frame:04}.png'
        with path.open('rb') as data:
            data.seek(-12, os.SEEK_END)
            if data.read() != b'\x00\x00\x00\x00IEND\xaeB\x60\x82':
                raise ValueError(f'Incomplete PNG at {path}')
        path.replace(destination(frame))
        now = time.monotonic()
        print('PLATE', frame, round(now - last, 2), flush=True)
        last = now
    def after_write(current_scene, *_):
        publish(current_scene.frame_current)
    bpy.app.handlers.render_write.append(after_write)
    try:
        pending = [frame for frame in frames if not destination(frame).exists()]
        for _, group in groupby(enumerate(pending), key=lambda pair: pair[1] - pair[0]):
            run = [frame for _, frame in group]
            scene.frame_start, scene.frame_end = run[0], run[-1]
            bpy.ops.render.render(animation=True)
            for frame in run:
                if not destination(frame).exists():
                    publish(frame)
    finally:
        bpy.app.handlers.render_write.remove(after_write)

if draft or reveal:
    stills()
else:
    native_animation()
