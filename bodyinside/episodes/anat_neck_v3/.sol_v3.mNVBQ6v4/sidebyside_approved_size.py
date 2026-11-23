#!/usr/bin/env python3
"""Two renders of the same shot with different postures -> one side-by-side frame (left half from A, right half from B). usage: python sidebyside.py RAW_A RAW_B OUT_RAW F0 F1 [split_x=540]
Both renders place their skeleton in their own half (camera target shifted), so the halves can be joined with a hard split. A faint 2 px divider is drawn."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
A, Bd, OUT, F0, F1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]); SX = int(sys.argv[6]) if len(sys.argv) > 6 else None
os.makedirs(OUT, exist_ok=True)
for f in range(F0, F1 + 1):
    a = Image.open(f'{A}/f_{f:04d}.png').convert('RGBA'); b = Image.open(f'{Bd}/f_{f:04d}.png').convert('RGBA'); W, H = a.size; sx = SX if SX is not None else W // 2
    # faint outline of the NEUTRAL skeleton on the texting half: A shifted so that the unchanged lower neck (bottom rows) coincides with B's
    an = np.asarray(a)[..., 3] > 128; bn = np.asarray(b)[..., 3] > 128; y0, y1 = int(H * 0.62), int(H * 0.86)
    cx = lambda m: np.nonzero(m[y0:y1])[1].mean() if m[y0:y1].any() else 0
    dxs = int(round(cx(bn[:, sx:] if False else bn) - cx(an))) if bn[y0:y1, sx:].any() else 0
    sh = np.zeros_like(an); 
    if dxs > 0: sh[:, dxs:] = an[:, :W - dxs]
    sh[:, :sx] = False
    ma = Image.fromarray((sh * 255).astype(np.uint8)); edge = np.asarray(ma.filter(ImageFilter.MaxFilter(3))).astype(int) - np.asarray(ma.filter(ImageFilter.MinFilter(3))).astype(int)
    ghost = np.zeros((H, W, 4), np.uint8); ghost[..., :3] = (215, 228, 245); ghost[..., 3] = np.clip(edge, 0, 255) * 0.0   # ghost outline off: the two halves are the comparison
    base = Image.fromarray(ghost, 'RGBA'); base.alpha_composite(b); out = base
    out.paste(a.crop((0, 0, sx, H)), (0, 0))
    px = out.load()
    for y in range(int(H * 0.12), int(H * 0.88)):
        for dx in range(-W // 270, W // 270):
            r, g, bl, al = px[sx + dx, y]; px[sx + dx, y] = (170, 175, 185, max(al, 70))
    out.save(f'{OUT}/f_{f:04d}.png')
print('sidebyside', F0, F1)
