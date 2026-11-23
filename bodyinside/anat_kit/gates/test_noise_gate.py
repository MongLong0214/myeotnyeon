"""Regression tests for noise_metric (run: python test_noise_gate.py FRAMES_DIR [BAND_BG.png]).
 (a) 50 isolated hot pixels injected into a clean frame must FAIL firefly_max (40)
 (b) the release frames (every 3rd frame of FRAMES_DIR) must PASS hp_std (6.0) and firefly_max (40)
 (c) heavy synthetic grain must still FAIL hp_std
 (d) overlay text/edges alone (bright block with bright neighbours) must NOT count as fireflies"""
import sys, glob, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_metric import frame_metrics
D = sys.argv[1]; bgp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(D)), 'comp', 'band_bg.png')
def load(f):
    im = Image.open(f).convert('RGBA')
    if os.path.exists(bgp): b = Image.open(bgp).convert('RGBA').resize(im.size); b.alpha_composite(im); im = b
    return np.asarray(im.convert('L')).astype(float)
NZ, FF = 6.0, 40
files = sorted(glob.glob(D + '/f_*.png')); fails = []
g = load(files[100]); rng = np.random.default_rng(1); H, W = g.shape
h = g.copy(); n = 0
while n < 50:
    y, x = int(rng.integers(5, H - 5)), int(rng.integers(5, W - 5))
    if g[y - 1:y + 2, x - 1:x + 2].max() < 150: h[y, x] = 255; n += 1
a = frame_metrics(h)[1]; print('(a) 50 hot pixels ->', a, 'fireflies (must be >= %d)' % FF); a_ok = a >= FF
rs = [frame_metrics(load(f)) for f in files[::3]]
b_nz = float(np.median([r[0] for r in rs])); b_ff = max(r[1] for r in rs); print('(b) release frames: hp_std median %.2f (<%.1f), fireflies max %d (<%d)' % (b_nz, NZ, b_ff, FF)); b_ok = b_nz < NZ and b_ff < FF
c = frame_metrics(np.clip(g + rng.normal(0, 12, g.shape), 0, 255))[0]; print('(c) heavy grain -> hp_std %.1f (must be >= %.1f)' % (c, NZ)); c_ok = c >= NZ
t = g.copy(); t[200:230, 300:420] = 255; d = frame_metrics(t)[1]; print('(d) bright text-like block -> fireflies', d, '(must be < %d)' % FF); d_ok = d < FF
ok = a_ok and b_ok and c_ok and d_ok; print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
