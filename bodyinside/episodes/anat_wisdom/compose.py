"""Layout layers for the 10 s clip (ref style: 2-line title top, CG band middle, own brand bottom). Writes comp/*.png"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, json, os
H = os.path.dirname(os.path.abspath(__file__)); C = f'{H}/comp'
F = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../branding/_src/public/fonts/')
BH = ImageFont.truetype(F + 'BlackHanSans-Regular.ttf', 92)
PB = lambda s: ImageFont.truetype(F + 'Pretendard-Bold.otf', s)
W, HH = 1080, 1920
BAND_Y, BAND_H = 520, 800
rng = np.random.default_rng(7)
# background: dark textured grey with soft vignette (ref1), slightly cool
n = rng.normal(0, 1, (HH // 4, W // 4)); n = np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype('uint8')).resize((W, HH), Image.BICUBIC)) / 255.0
fine = rng.normal(0, 1, (HH, W)) * 0.035
yy, xx = np.mgrid[0:HH, 0:W]; r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - HH / 2) / HH) ** 2)
base = 0.115 + 0.05 * (n - 0.5) + fine - 0.10 * r
rgb = np.stack([base * 0.97, base * 0.99, base * 1.04], -1).clip(0, 1)
bg = Image.fromarray((rgb * 255).astype('uint8'))
d = ImageDraw.Draw(bg)
def ctext(dr, y, s, font, fill, stroke=6):
    w = dr.textlength(s, font=font); dr.text(((W - w) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(16, 14, 12))
# title: shadow layer then text
sh = Image.new('RGBA', (W, HH), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
for y, s in [(250, '누운 사랑니를 뽑을 때'), (360, '턱 속에서 생기는 일')]:
    w = sd.textlength(s, font=BH); sd.text(((W - w) / 2 + 4, y + 6), s, font=BH, fill=(0, 0, 0, 170))
bg.paste(sh.filter(ImageFilter.GaussianBlur(6)), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
ctext(d, 250, '누운 사랑니를 뽑을 때', BH, (255, 184, 28))
ctext(d, 360, '턱 속에서 생기는 일', BH, (250, 250, 248))
# brand (own text, no logos)
bf = PB(44); ctext(d, 1440, '몸속 3D 해부도', bf, (236, 232, 224), 0)
bg.save(f'{C}/base.png')
# band background (behind transparent CG): dark cool haze with vignette, like both refs
bx, by = np.mgrid[0:BAND_H, 0:W]
rr = np.sqrt(((by - W * 0.55) / W) ** 2 + ((bx - BAND_H * 0.42) / BAND_H * 0.8) ** 2)
hz = (0.16 - 0.17 * rr).clip(0.015, 1)
haze = np.stack([hz * 0.80, hz * 0.90, hz * 1.05], -1)
Image.fromarray((haze.clip(0, 1) * 255).astype('uint8')).save(f'{C}/band_bg.png')
# chapter tags (inside band top-left) and keyword captions (under band)
tags = json.load(open(f'{H}/beats10.json'))
for i, b in enumerate(tags):
    im = Image.new('RGBA', (W, HH), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    tf = PB(36); tw = dr.textlength(b['tag'], font=tf)
    dr.rectangle([18, BAND_Y + 18, 18 + 10, BAND_Y + 18 + 54], fill=(40, 120, 255, 255))
    dr.rectangle([28, BAND_Y + 18, 28 + tw + 28, BAND_Y + 72], fill=(250, 250, 250, 235))
    dr.text((42, BAND_Y + 23), b['tag'], font=tf, fill=(20, 24, 32))
    cf = PB(56)
    parts = b['cap']  # list of [text, color]
    tot = sum(dr.textlength(t, font=cf) for t, c in parts); x = (W - tot) / 2
    for t, c in parts:
        dr.text((x, BAND_Y + BAND_H + 26), t, font=cf, fill=tuple(c), stroke_width=5, stroke_fill=(10, 10, 10)); x += dr.textlength(t, font=cf)
    im.save(f'{C}/cap_{i}.png')
print('ok')
