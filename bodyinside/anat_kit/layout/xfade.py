#!/usr/bin/env python3
"""Compositing crossfade between two 3D shots (camera cuts cannot be dissolved in the render). usage: python xfade.py EPISODE_DIR RAW_DIR
episode.json "xfades": [{"at": 816, "n": 12, "hold": 815}] : the frame `hold` (last frame of the outgoing shot) is held and cross-faded over frames at .. at+n-1 of the incoming shot
(premultiplied-alpha lerp, weight 1 -> 0). Originals of the touched frames are kept in RAW_DIR/../<raw>_xf_orig so the stage is idempotent."""
import sys, os, json, shutil, numpy as np
from PIL import Image
E_, RAW = sys.argv[1], sys.argv[2]; ep = json.load(open(E_ + '/episode.json')); ORIG = RAW.rstrip('/') + '_xf_orig'
def load(p):
    a = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) / 255.0; a[..., :3] *= a[..., 3:4]; return a
for xf in ep.get('xfades', []):
    os.makedirs(ORIG, exist_ok=True)
    for f in [xf['hold']] + list(range(xf['at'], xf['at'] + xf['n'])):
        o = f'{ORIG}/f_{f:04d}.png'
        if not os.path.exists(o): shutil.copyfile(f'{RAW}/f_{f:04d}.png', o)
    hold = load(f'{ORIG}/f_{xf["hold"]:04d}.png')
    for i in range(xf['n']):
        f = xf['at'] + i; t = i / xf['n']; w = 1.0 - (i + 1) / xf['n'] if xf.get('ease') == 'linear' else 1.0 - t * t * (3 - 2 * t)   # 'linear': no near-still first frames (they read as judder to the cadence gate when the outgoing shot is moving)
        new = load(f'{ORIG}/f_{f:04d}.png'); out = hold * w + new * (1 - w); al = out[..., 3:4]
        rgb = np.where(al > 1e-4, out[..., :3] / np.maximum(al, 1e-4), 0.0); res = np.concatenate([np.clip(rgb, 0, 1), al], axis=2)
        Image.fromarray((res * 255 + 0.5).astype(np.uint8), 'RGBA').save(f'{RAW}/f_{f:04d}.png')
print('xfade done', len(ep.get('xfades', [])))
