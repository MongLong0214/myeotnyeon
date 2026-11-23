"""2D overlay of the "약 2 mm" label (drawn over the CG, left of the bracket, so no foreground slab can clip it).
usage: python -I label2d.py RAW_DIR OUT_DIR   (label_pos.json from labelpos.py; frames RGBA band, any scale)"""
import sys, os, json, shutil
from PIL import Image, ImageDraw, ImageFont
raw, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
pos = {int(k): v for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'label_pos.json'))).items()}
FONT = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../branding/_src/public/fonts/Pretendard-Bold.otf')
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def scale_at(f): return sstep((f - 168) / 6) * (1 - sstep((f - 190) / 10))   # in 168-174, out 190-200 (as the 3D label had)
for fn in sorted(os.listdir(raw)):
    if not fn.endswith('.png'): continue
    f = int(fn[2:6]); dst = os.path.join(out, fn); sc_ = scale_at(f) if f in pos else 0
    if sc_ <= 0.01: shutil.copyfile(os.path.join(raw, fn), dst); continue
    im = Image.open(os.path.join(raw, fn)).convert('RGBA'); s = im.size[0] / 1080; P = pos[f]
    font = ImageFont.truetype(FONT, 4 * int(60 * s)); txt = '약 2 mm'
    L = Image.new('RGBA', (4 * int(340 * s), 4 * int(110 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    w = d.textlength(txt, font=font); pw = int(w + 4 * 38 * s); ph = L.size[1]
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 4, fill=(6, 6, 8, 240))
    d.text((pw / 2, ph / 2), txt, font=font, fill=(255, 255, 255, 255), anchor='mm')
    L = L.crop((0, 0, pw, ph)).resize((max(1, int(pw / 4 * sc_)), max(1, int(ph / 4 * sc_))), Image.LANCZOS)
    cx = P['mid'][0] * im.size[0] - 22 * s - (pw / 4) / 2; cy = P['mid'][1] * im.size[1]   # right edge 22 px left of the bracket
    im.alpha_composite(L, (int(cx - L.size[0] / 2), int(cy - L.size[1] / 2)))
    im.save(dst)
print('label2d done', out)
