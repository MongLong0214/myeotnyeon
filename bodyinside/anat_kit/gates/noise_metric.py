"""Per-frame noise metrics for video_gates (thresholds live in the layout json: noise_max, firefly_max).
hp_std : std of a 4-neighbour high-pass on FLAT pixels only. Flat = near the frame's median luma AND not textured; texture is local std of the
         5x5-smoothed luma over 15x15 (grain averages out under the 5x5 mean, so heavy grain still counts; trabecular bone pattern does not).
fireflies : ISOLATED hot pixels - luma > 200 and brighter than all 8 neighbours by more than 60. Bright edges and text have bright neighbours,
         so they are not counted."""
import numpy as np
from scipy.ndimage import uniform_filter

def frame_metrics(g):
    g = np.asarray(g, float)
    hp = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    sm = uniform_filter(g, 5); m1 = uniform_filter(sm, 15)
    sd = np.sqrt(np.maximum(uniform_filter(sm * sm, 15) - m1 * m1, 0))
    flat = ((np.abs(g - np.median(g)) < 25) & (sd < 6))[1:-1, 1:-1]
    hp_std = float(np.std(hp[flat])) if flat.any() else 0.0
    pad = np.pad(g, 1, mode='edge')
    nmax = np.max([pad[1 + dy:1 + dy + g.shape[0], 1 + dx:1 + dx + g.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)], 0)
    fireflies = int(((g - nmax > 60) & (g > 200))[1:-1, 1:-1].sum())
    return hp_std, fireflies
