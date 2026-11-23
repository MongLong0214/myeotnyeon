"""Pixel and overlay geometry checks for the neck opening and comparison."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label


def read_opening_atlas(path, crop, count):
    """Read a vertical strip of half-resolution grayscale crops, starting at f0."""
    x0, y0, x1, y1 = crop
    size = ((x1 - x0) // 2, (y1 - y0) // 2)
    with Image.open(path) as image:
        if image.size != (size[0], size[1] * count):
            raise ValueError(f'Unexpected opening fixture size: {image.size}')
        return np.asarray(image.convert('L')).reshape(count, size[1], size[0])


def compare_opening(frames, reference):
    if frames.shape != reference.shape:
        return {'ok': False, 'error': 'Incomplete opaque opening frames'}
    violations = []
    max_patch = 0
    for frame, (observed, clean) in enumerate(zip(frames, reference)):
        # Dark rims and shadows as well as bright bone differ from the person-only render.
        delta = np.abs(observed.astype(np.int16) - clean)
        components, _ = label(delta >= 10)
        largest = int(np.bincount(components.ravel())[1:].max(initial=0))
        max_patch = max(max_patch, largest)
        if largest >= 3:
            violations.append({'frame': frame, 'patch_pixels_at_half_resolution': largest})
    return {'ok': not violations, 'frames_checked': len(frames), 'max_patch': max_patch,
            'violations': violations}


def opening_bone_leak(video, settings):
    count = settings['last_opaque'] + 1
    crop = settings['crop']
    reference = read_opening_atlas(Path(__file__).parent / settings['reference'], crop, count)
    x0, y0, x1, y1 = crop
    h, w = reference.shape[1:]
    decoded = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', video, '-map', '0:v:0', '-vf',
        f'crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={w}:{h}:flags=area,format=gray',
        '-frames:v', str(count), '-fps_mode', 'passthrough', '-f', 'rawvideo', '-',
    ])
    frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, h, w)
    return compare_opening(frames, reference)


def split_label_layout(labels, drawn, band_height):
    """Check the actual pill rectangles in 1080-wide band coordinates."""
    halves = {'left': (0, 540), 'right': (540, 1080)}
    tolerance_px = 540 * 0.02
    violations = []
    errors_px = []
    for frame, boxes in drawn.items():
        centers_y = []
        for label_id, (x0, y0, x1, y1) in boxes.items():
            left, right = halves[labels[label_id]['split_half']]
            dx = abs((x0 + x1 - left - right) / 2)
            errors_px.append(dx)
            centers_y.append((y0 + y1) / 2)
            if dx > tolerance_px or x0 < left + 12 or x1 > right - 12 or y0 < 12 or y1 > band_height - 12:
                violations.append({'frame': int(frame), 'label': label_id, 'box': [x0, y0, x1, y1]})
        if centers_y and max(centers_y) - min(centers_y) > 1:
            violations.append({'frame': int(frame), 'centers_y': centers_y})
    for label_id, spec in labels.items():
        # Every fully visible frame must have an actual box from the compositor.
        start = spec['f0'] + spec.get('ramp', 14)
        end = spec['f1'] - spec.get('ramp_out', spec.get('ramp', 14))
        missing = [f for f in range(start, end + 1) if label_id not in drawn.get(str(f), {})]
        if missing:
            violations.append({'label': label_id, 'missing_frames': missing})
    return {'ok': bool(errors_px) and not violations, 'boxes_checked': len(errors_px),
            'max_center_error_px': max(errors_px, default=None), 'tolerance_px': tolerance_px,
            'violations': violations}
