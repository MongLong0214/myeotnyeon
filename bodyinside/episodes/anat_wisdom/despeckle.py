import numpy as np, sys, os
from PIL import Image, ImageFilter
src, dst, thr, full = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
os.makedirs(dst, exist_ok=True)
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.png'): continue
    if len(sys.argv) > 5 and int(fn[2:6]) % int(sys.argv[5]): continue
    im = Image.open(os.path.join(src, fn)).convert('RGBA'); a = np.asarray(im).astype(float)
    m3 = np.asarray(im.filter(ImageFilter.MedianFilter(3))).astype(float)
    m5 = np.asarray(im.filter(ImageFilter.MedianFilter(5))).astype(float)
    d = np.abs(a[..., :3] - m3[..., :3]).max(-1)
    w = (d > thr)[..., None]
    out = np.where(w, m5, a)   # outliers -> median5
    out = out * (1 - full) + m3 * full   # optional global 3x3 median share
    out[..., 3] = a[..., 3]
    Image.fromarray(out.astype('uint8'), 'RGBA').save(os.path.join(dst, fn))
