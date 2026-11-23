import numpy as np, sys, glob
from PIL import Image
nz, ff = [], []
bg = Image.open('comp/band_bg.png').convert('RGBA')
for f in sorted(glob.glob(sys.argv[1] + '/f_*.png')):
    im = Image.open(f).convert('RGBA'); b = bg.resize(im.size); b.alpha_composite(im)
    g = np.asarray(b.convert('L')).astype(float)
    hp = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    flat = np.abs(g[1:-1, 1:-1] - np.median(g)) < 25
    nz.append(float(np.std(hp[flat])) if flat.any() else 0); ff.append(int(((hp > 120) & (g[1:-1, 1:-1] > 200)).sum()))
print('hp_std', round(float(np.median(nz)), 2), 'fireflies_max', max(ff))
