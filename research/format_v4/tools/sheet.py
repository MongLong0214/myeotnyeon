"""Timestamped storyboard contact sheet: sheet.py ID [t0 t1 step cols scale] -> frames/ID/sheet_<t0>_<t1>.jpg"""
import json, sys, pathlib
from PIL import Image, ImageDraw, ImageFont
R = pathlib.Path(__file__).resolve().parents[1]
def cells(vid):
    d = json.load(open(R / 'meta' / f'{vid}.json'))
    f = [x for x in d['formats'] if x['format_id'] == 'sb0'] or [x for x in d['formats'] if x['format_id'] == 'sb1']
    f = f[0]; out = []; t0 = 0
    for i, fr in enumerate(f['fragments']):
        p = R / 'frames' / vid / f"{f['format_id']}_{i:02d}.jpg"
        im = Image.open(p).convert('RGB'); n = f['rows'] * f['columns']; per = fr['duration'] / n
        for k in range(n):
            r, c = divmod(k, f['columns']); t = t0 + k * per
            box = (c * f['width'], r * f['height'], (c + 1) * f['width'], (r + 1) * f['height'])
            if t <= d['duration'] + 0.01 and box[3] <= im.height and box[2] <= im.width:
                out.append((t, im.crop(box)))
        t0 += fr['duration']
    return out, d
if __name__ == '__main__':
    vid = sys.argv[1]; a = [float(x) for x in sys.argv[2:]] + [None] * 5
    t0, t1, step, cols, scale = a[0] or 0, a[1] or 1e9, a[2] or 0, int(a[3] or 12), a[4] or 1.4
    cs, d = cells(vid); sel = []; last = -1e9
    for t, c in cs:
        if t0 <= t <= t1 and t - last >= step - 1e-6: sel.append((t, c)); last = t
    w, h = sel[0][1].size; W, H = int(w * scale), int(h * scale); rows = (len(sel) + cols - 1) // cols
    out = Image.new('RGB', (cols * W, rows * (H + 16)), 'white'); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 13)
    for i, (t, c) in enumerate(sel):
        r, cc = divmod(i, cols); out.paste(c.resize((W, H), Image.LANCZOS), (cc * W, r * (H + 16) + 16)); dr.text((cc * W + 2, r * (H + 16) + 1), f'{t:.1f}', fill=(200, 0, 0), font=font)
    p = R / 'frames' / vid / f'sheet_{int(t0)}_{int(min(t1, d["duration"]))}.jpg'; out.save(p, quality=88); print(p, out.size, len(sel))
