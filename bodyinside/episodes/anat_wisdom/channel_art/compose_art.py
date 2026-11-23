"""Compose Body Inside channel art from render_art.py outputs.
banner.png 2560x1440 (all text and the jaw inside the 1546x423 centred safe area), profile.png 800x800."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

D = os.path.dirname(os.path.abspath(__file__))
F = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../../branding/_src/public/fonts/')
IVORY, AMBER, BG = (236, 232, 224), (232, 160, 80), (10, 10, 12)


def glow(size, center, radius, color, alpha):
    g = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    x, y = center
    d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (alpha,))
    return g.filter(ImageFilter.GaussianBlur(radius * 0.6))


def banner():
    W, H = 2560, 1440
    sx0, sy0, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423
    im = Image.new('RGBA', (W, H), BG + (255,))
    jaw = Image.open(os.path.join(D, 'banner_rgba.png'))
    jaw = jaw.crop(jaw.split()[3].getbbox())
    s = (sh - 10) / jaw.height
    jaw = jaw.resize((int(jaw.width * s), int(jaw.height * s)), Image.LANCZOS)
    jx = sx0 + sw - jaw.width - 10
    jy = sy0 + (sh - jaw.height) // 2
    im.alpha_composite(glow((W, H), (jx + jaw.width // 2, jy + jaw.height // 2), 360, AMBER, 60))
    im.alpha_composite(jaw, (jx, jy))
    d = ImageDraw.Draw(im)
    title = ImageFont.truetype(F + 'Pretendard-Bold.otf', 150)
    tag = ImageFont.truetype(F + 'Pretendard-Bold.otf', 58)
    tx = sx0 + 30
    d.text((tx, sy0 + 70), 'Body Inside', font=title, fill=IVORY)
    d.text((tx + 6, sy0 + 265), '보이지 않던 몸속을 3D로', font=tag, fill=AMBER)
    assert tx + d.textlength('Body Inside', font=title) < jx, 'title overlaps jaw'
    im.convert('RGB').save(os.path.join(D, 'banner.png'))


def profile():
    S = 800
    im = Image.new('RGBA', (S, S), BG + (255,))
    t = Image.open(os.path.join(D, 'profile_rgba.png')).resize((S, S), Image.LANCZOS)
    im.alpha_composite(glow((S, S), (S // 2, S // 2 - 40), 260, AMBER, 50))
    im.alpha_composite(t)
    # darken the bottom band so the wordmark reads at small sizes
    band = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(260):
        bd.line((0, S - 260 + i, S, S - 260 + i), fill=BG + (int(235 * i / 260),))
    im.alpha_composite(band)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F + 'Pretendard-Bold.otf', 92)
    w = d.textlength('BODY INSIDE', font=f)
    d.text(((S - w) / 2, S - 215), 'BODY INSIDE', font=f, fill=IVORY)
    im.convert('RGB').save(os.path.join(D, 'profile.png'))


banner()
profile()
print('ok')
