"""Camera drift for the neck comparison and payoff."""

from math import cos, pi, sin


SPLIT_START = 300
SPLIT_END = 713
LOWER_SPINE_HIDE = SPLIT_END + 1
PAYOFF_DRIFT_START = 760
PAYOFF_DRIFT_END = 819


def _smoothstep(value):
    t = min(1.0, max(0.0, value))
    return t * t * (3.0 - 2.0 * t)


def drift_pixels(frame):
    """Full-resolution image displacement, with eased ends at the cuts."""
    if not SPLIT_START < frame < SPLIT_END:
        return 0.0, 0.0
    envelope = _smoothstep((frame - SPLIT_START) / 38)
    envelope *= _smoothstep((SPLIT_END - frame) / 29)
    phase = 2 * pi * (frame - 335) / 130 + pi
    return envelope * 18 * sin(phase), envelope * (7 + 21 * cos(phase))


def _key_lens_shift(scene, start, end, offsets):
    camera = scene.camera.data
    width = scene.render.resolution_x
    base_x, base_y = camera.shift_x, camera.shift_y
    for frame in range(start, end + 1):
        dx, dy = offsets(frame)
        camera.shift_x = base_x - dx / width
        camera.shift_y = base_y + dy / width
        camera.keyframe_insert('shift_x', frame=frame)
        camera.keyframe_insert('shift_y', frame=frame)


def key_camera_drift(scene):
    # Lens shift gives both postures identical screen-space motion at every depth.
    _key_lens_shift(scene, SPLIT_START, SPLIT_END, drift_pixels)


def payoff_drift_pixels(frame):
    if not PAYOFF_DRIFT_START < frame < PAYOFF_DRIFT_END:
        return 0.0, 0.0
    t = (frame - PAYOFF_DRIFT_START) / (PAYOFF_DRIFT_END - PAYOFF_DRIFT_START)
    weight = sin(pi * t) ** 2
    return 16 * weight, 18 * weight


def key_payoff_drift(scene):
    _key_lens_shift(scene, PAYOFF_DRIFT_START, PAYOFF_DRIFT_END, payoff_drift_pixels)
