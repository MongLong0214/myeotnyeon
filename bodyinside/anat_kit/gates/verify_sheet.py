"""Before/after crop pairs at the exact frame and band coordinates a review cites. usage:
python verify_sheet.py BEFORE_DIR AFTER_DIR items.json out.png
items.json: [{"id":"P0-2","frame":245,"box":[x0,y0,x1,y1]}] in FULL band px (1080x800); frames may be half-res (scaled)."""
import sys, json, os
from PIL import Image, ImageDraw
bd, ad, items, out = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3])), sys.argv[4]
W = 300; rows = []
for it in items:
    pair = []
    for d in (bd, ad):
        im = Image.open(os.path.join(d, 'f_%04d.png' % it['frame'])).convert('RGBA'); s = im.size[0] / 1080
        bg = Image.new('RGBA', im.size, (20, 20, 20, 255)); bg.alpha_composite(im)
        c = bg.crop(tuple(int(v * s) for v in it['box'])); c = c.resize((W, max(1, int(W * c.size[1] / c.size[0]))))
        pair.append(c)
    rows.append((it, pair))
H = sum(max(p[0].size[1], p[1].size[1]) + 24 for _, p in rows)
sheet = Image.new('RGB', (W * 2 + 10, H), (40, 40, 40)); dr = ImageDraw.Draw(sheet); y = 0
for it, (b, a) in rows:
    dr.text((4, y + 4), f"{it['id']}  f{it['frame']}  before | after", fill=(255, 220, 0)); y += 22
    sheet.paste(b.convert('RGB'), (0, y)); sheet.paste(a.convert('RGB'), (W + 10, y)); y += max(b.size[1], a.size[1]) + 2
sheet.save(out); print('saved', out)
