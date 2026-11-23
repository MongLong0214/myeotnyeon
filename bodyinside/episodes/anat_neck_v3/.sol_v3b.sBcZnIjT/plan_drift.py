from itertools import product
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import shift

old = Path('.sol_v3.mNVBQ6v4')
ep = json.loads((old / 'episode.json').read_text())
events = {int(beat['t0'] * 30) for beat in ep['beats']}
events |= {label[k] for label in ep['labels'] for k in ('f0', 'f1')}
starts = [f for f in range(260, 710, 10) if not any(f <= e <= f + 60 for e in events)]

def make_gray(frame):
    im = Image.open(old / 'frames_final_hq_v3_raw' / f'f_{frame:04}.png').convert('RGBA')
    page = Image.new('RGBA', im.size, (20, 20, 20, 255))
    page.alpha_composite(im)
    return np.asarray(page.convert('L').resize((270, 200)), dtype=np.float32)

def envelope(f):
    t = min(1., max(0., (f - 304) / 31))
    u = min(1., max(0., (729 - f) / 40))
    return t*t*(3-2*t)*u*u*(3-2*u)

def offset(f, ax, ay, period, phase):
    angle = 2 * np.pi * (f - 335) / period + phase
    return envelope(f)*ax*np.sin(angle), envelope(f)*ay*np.cos(angle)

if __name__ == '__main__':
    fs = range(min(starts)-1, max(starts)+60)
    images = np.array([make_gray(f) for f in fs])
    imin = np.array(starts) - fs.start - 1
    window_len = 60
    records = []
    print('Windows', starts, flush=True)
    for ax, ay, period, phase in product([20, 30, 40], [42, 55, 68], [85, 100, 115, 130], [0., np.pi/2, np.pi, 3*np.pi/2]):
        previous = None
        deltas = []
        for f, image in zip(fs, images):
            dx, dy = offset(f, ax, ay, period, phase)
            moved = shift(image, (dy / 4.4, dx / 4.0), order=1, mode='constant', cval=20, prefilter=False)
            moved[:,134:137] = image[:,134:137]
            if previous is not None:
                deltas.append(np.abs(moved-previous).mean())
            previous = moved
        window_mins = [float(np.mean(deltas[i:i+window_len])) for i in imin]
        records.append((min(window_mins), ax, ay, period, round(phase,3), [round(v,3) for v in window_mins]))
    for row in sorted(records, reverse=True)[:32]:
        print(row)
