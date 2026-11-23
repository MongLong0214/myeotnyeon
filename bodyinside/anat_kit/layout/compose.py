"""Layout layers from episode.json. usage: python compose.py EPISODE_DIR  -> EPISODE_DIR/comp/{base,band_bg,cap_i}.png
Layout (Shorts-safe): title 2 lines at y 250/360, CG band at y 520 (1080 x band_h), caption under band, brand at y 1440 (< 1500)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, json, os, sys
E = sys.argv[1]; ep = json.load(open(f'{E}/episode.json')); C = f'{E}/comp'; os.makedirs(C, exist_ok=True)
F = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../branding/_src/public/fonts/')
BH = ImageFont.truetype(F + 'BlackHanSans-Regular.ttf', 92); PB = lambda s: ImageFont.truetype(F + 'Pretendard-Bold.otf', s)
BRAND_DEFAULT = 'Body Inside'   # channel brand line (was 몸속 3D 해부도, then 바디인사이드); episode.json 'brand' may override
W, HH = 1080, 1920; BAND_Y = ep['layout']['band_y']; BAND_H = ep['layout']['band_h']
rng = np.random.default_rng(7)
n = rng.normal(0, 1, (HH // 4, W // 4)); n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype('uint8')).resize((W, HH), Image.BICUBIC)) / 255.0
yy, xx = np.mgrid[0:HH, 0:W]; r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - HH / 2) / HH) ** 2)
base = 0.115 + 0.05 * (n - 0.5) + rng.normal(0, 1, (HH, W)) * 0.035 - 0.10 * r
bg = Image.fromarray((np.stack([base * 0.97, base * 0.99, base * 1.04], -1).clip(0, 1) * 255).astype('uint8')); d = ImageDraw.Draw(bg)
def ctext(dr, y, s, font, fill, stroke=6):
    w = dr.textlength(s, font=font); dr.text(((W - w) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(16, 14, 12))
t1, t2 = ep['title']
sh = Image.new('RGBA', (W, HH), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
for y, s in [(250, t1), (360, t2)]:
    w = sd.textlength(s, font=BH); sd.text(((W - w) / 2 + 4, y + 6), s, font=BH, fill=(0, 0, 0, 170))
blur = sh.filter(ImageFilter.GaussianBlur(6)); bg.paste(blur, (0, 0), blur)
ctext(d, 250, t1, BH, (255, 184, 28)); ctext(d, 360, t2, BH, (250, 250, 248))
ctext(d, ep['layout'].get('brand_y', 1440), ep.get('brand', BRAND_DEFAULT), PB(44), (236, 232, 224), 0)
bg.save(f'{C}/base.png')
bx, by = np.mgrid[0:BAND_H, 0:W]; rr = np.sqrt(((by - W * 0.55) / W) ** 2 + ((bx - BAND_H * 0.42) / BAND_H * 0.8) ** 2)
hz = (0.16 - 0.17 * rr).clip(0.015, 1)
Image.fromarray((np.stack([hz * 0.80, hz * 0.90, hz * 1.05], -1).clip(0, 1) * 255).astype('uint8')).save(f'{C}/band_bg.png')
boxes = [[150, 250, 930, 345], [150, 360, 930, 455], [380, ep['layout'].get('brand_y', 1440), 700, ep['layout'].get('brand_y', 1440) + 50]]
for i, b in enumerate(ep['beats']):
    im = Image.new('RGBA', (W, HH), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    tf = PB(36); tw = dr.textlength(b['tag'], font=tf)
    if ep['layout'].get('tags', False) and b.get('tag'):   # legacy layout option
        dr.rectangle([18, BAND_Y + 18, 28, BAND_Y + 72], fill=(40, 120, 255, 255))
        dr.rectangle([28, BAND_Y + 18, 28 + tw + 28, BAND_Y + 72], fill=(250, 250, 250, 235)); dr.text((42, BAND_Y + 23), b['tag'], font=tf, fill=(20, 24, 32))
    cf = PB(ep['layout'].get('caption_size', 56)); tot = sum(dr.textlength(t, font=cf) for t, c in b['cap']); x = (W - tot) / 2; x0 = x
    for t, c in b['cap']:
        dr.text((x, BAND_Y + BAND_H + ep['layout'].get('caption_dy', 26)), t, font=cf, fill=tuple(c), stroke_width=5, stroke_fill=(10, 10, 10)); x += dr.textlength(t, font=cf)
    im.save(f'{C}/cap_{i}.png'); boxes += ([[18, BAND_Y + 18, int(56 + tw), BAND_Y + 72]] if ep['layout'].get('tags', False) and b.get('tag') else []) + [[int(x0), BAND_Y + BAND_H + ep['layout'].get('caption_dy', 26), int(x), BAND_Y + BAND_H + 96]]
if ep.get('credits'): raise ValueError('put attribution in description.txt')
json.dump(boxes, open(f'{C}/text_boxes.json', 'w'))
print('ok')
