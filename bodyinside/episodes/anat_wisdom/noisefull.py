import numpy as np, sys, glob
from PIL import Image
bg = Image.open('comp/band_bg.png').convert('RGBA')
def run(d):
    nz, ff = [], []; worst = (0, None, None)
    for f in sorted(glob.glob(d + '/f_*.png')):
        im = Image.open(f).convert('RGBA'); b = bg.resize(im.size); b.alpha_composite(im)
        g = np.asarray(b.convert('L')).astype(float)
        hp = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
        flat = np.abs(g[1:-1, 1:-1] - np.median(g)) < 25
        m = (hp > 120) & (g[1:-1, 1:-1] > 200)
        nz.append(float(np.std(hp[flat])) if flat.any() else 0); n = int(m.sum()); ff.append(n)
        if n > worst[0]:
            ys, xs = np.nonzero(m); worst = (n, f[-8:-4], (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    return round(float(np.median(nz)), 2), max(ff), worst, [i for i, v in enumerate(ff) if v >= 40]
for d in sys.argv[1:]:
    print(d, run(d))
