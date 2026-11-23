"""A/B event gate: an effect must change the rendered frames. usage:
python ab_gate.py ON_DIR OFF_DIR x0,y0,x1,y1(fractions) min_delta frame [frame ...]
OFF_DIR is the same frames rendered with the effect hidden (rset.py --hide=Prefix). Prints JSON, exit 1 if any frame < min."""
import sys, os, json, numpy as np
from PIL import Image
on, off, roi, mn = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(',')], float(sys.argv[4])
res = []
for f in map(int, sys.argv[5:]):
    a, b = [Image.open(os.path.join(d, 'f_%04d.png' % f)).convert('L') for d in (on, off)]
    w, h = a.size; box = (int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h))
    d = float(np.abs(np.asarray(a.crop(box), float) - np.asarray(b.crop(box), float)).mean())
    res.append({'frame': f, 'delta': round(d, 2), 'ok': d >= mn})
ok = all(r['ok'] for r in res); print(json.dumps({'frames': res, 'min': mn, 'ok': ok})); sys.exit(0 if ok else 1)
