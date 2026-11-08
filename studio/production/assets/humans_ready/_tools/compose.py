# compose 6 tiles into a 960x540 contact sheet. usage: python3 compose.py meta.json out_dir [title_prefix]
import json, sys, os
from PIL import Image, ImageDraw, ImageFont
meta = json.load(open(sys.argv[1]))
out_dir = sys.argv[2]
prefix = sys.argv[3] if len(sys.argv) > 3 else ''
tile_dir = os.path.dirname(sys.argv[1])
os.makedirs(out_dir, exist_ok=True)
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
except Exception:
    font = ImageFont.load_default()
fps = meta['fps']
for a in meta['anims']:
    sheet = Image.new('RGB', (960, 540), (10, 10, 12))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(a['frames']):
        t = Image.open(os.path.join(tile_dir, '%s_%d.png' % (a['tag'], i))).convert('RGB')
        x, y = (i % 3) * 320, (i // 3) * 270
        sheet.paste(t, (x, y))
        d.text((x + 6, y + 252), 'f%d  t=%.2fs' % (f, f / fps), fill=(230, 230, 230), font=font)
    d.text((6, 4), (prefix + a['tag'])[:110], fill=(255, 220, 120), font=font)
    out = os.path.join(out_dir, a['tag'] + '.jpg')
    sheet.save(out, quality=88)
    print(out)
