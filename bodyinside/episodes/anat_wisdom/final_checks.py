import numpy as np, json, sys
from PIL import Image
D = sys.argv[1]
def L(f):
    im = Image.open('%s/f_%04d.png' % (D, f)).convert('RGBA'); a = np.asarray(im, float)
    bg = np.full(a.shape[:2] + (3,), 20.0); al = a[..., 3:] / 255
    return np.asarray(Image.fromarray((a[..., :3] * al + bg * (1 - al)).astype('uint8')).convert('L'), float)
prev = L(0); d = []
for f in range(1, 300):
    cur = L(f); d.append((f, float(abs(cur - prev).mean()))); prev = cur
v = np.array([x[1] for x in d]); med = np.median(v)
print('median delta', round(med, 2), 'max', round(v.max(), 2), 'at f', d[int(v.argmax())][0])
big = [(f, round(x, 1)) for f, x in d if x > 2.5 * med]
print('deltas > 2.5x median:', big)
# clipping: fraction of pixels >= 250 luma in f90..160 on the right 2/3 (second molar region)
for f in (90, 120, 160, 281, 290, 299):
    a = np.asarray(Image.open('%s/f_%04d.png' % (D, f)).convert('RGBA'), float)
    m = a[..., 3] > 128; print('clip f%d' % f, round(float((a[..., :3].max(-1)[m] >= 252).mean()), 4))
