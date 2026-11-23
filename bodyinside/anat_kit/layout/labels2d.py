"""2D label layer drawn ABOVE the finished 3D band frames (nothing can occlude it). usage: python -I labels2d.py EPISODE_DIR RAW_DIR OUT_DIR
episode.json "labels": [{"id","kind","text","sub","anchor","f0","f1","kg","dx","dy"}]
kinds: load    amber arrow from the anchor straight down, length ~ kg, pill "text" (+ small "sub") left of the arrow tail
       callout dark pill at (dx,dy) px offset from the anchor with a thin leader line to the anchor and a dot on it
       note    small pill at a fixed band position (dx,dy in band px from the top-left): source / disclaimer lines
Scale in over 14 frames, out over 14 (no pops). Frames may be half resolution."""
import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
from note_layers import note_layers
from PIL import Image, ImageDraw, ImageFont
E, raw, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
ep = json.load(open(E + '/episode.json')); L = note_layers(ep.get('labels', [])); _lp = json.load(open(E + '/label_pos.json')) if os.path.exists(E + '/label_pos.json') else {}; pos = {int(k): v for k, v in _lp.items() if not k.startswith('_')}; PLUMB = _lp.get('_plumb', {}); PDRAW = {}
FONT = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../branding/_src/public/fonts/Pretendard-Bold.otf'); AMBER = (255, 184, 28, 255)
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def scale_at(l, f):
    r = l.get('ramp', 20 if l['kind'] == 'load' else 14)
    ro = l.get('ramp_out', r)
    held_end = l.get('hold_to_end') and l['f1'] == round(ep['duration']*ep['fps'])-1
    remaining = 1 if ro == 0 or held_end else 1 - sstep((f - (l['f1'] - ro)) / ro)
    entering = 1 if r == 0 else sstep((f - l['f0']) / r)
    return entering * remaining
def pill(txt, sub, size, S):
    f1 = ImageFont.truetype(FONT, int(size * S)); f2 = ImageFont.truetype(FONT, int(size * 0.55 * S)); d0 = ImageDraw.Draw(Image.new('RGBA', (4, 4)))
    w1 = d0.textlength(txt, font=f1); w2 = d0.textlength(sub, font=f2) if sub else 0; w = int(max(w1, w2) + 44 * S); h = int((size * 1.45 + (size * 0.7 if sub else 0)) * S)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 4, fill=(6, 6, 8, 235), outline=(255, 255, 255, 60), width=max(1, int(2 * S)))
    if sub:
        d.text((w / 2, h * 0.30), sub, font=f2, fill=(200, 200, 205, 255), anchor='mm'); d.text((w / 2, h * 0.68), txt, font=f1, fill=(255, 255, 255, 255), anchor='mm')
    else: d.text((w / 2, h / 2), txt, font=f1, fill=(255, 255, 255, 255), anchor='mm')
    return im
def put(pl, layer, cx, cy, k):
    if k < 0.02: return
    w, h = layer.size; layer = layer.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS); im.alpha_composite(layer, (int(cx - layer.size[0] / 2), int(cy - layer.size[1] / 2)))
for fn in sorted(os.listdir(raw)):
    if not fn.endswith('.png'): continue
    f = int(fn[2:6]); act = [l for l in L if l['f0'] <= f <= l['f1']]; dst = os.path.join(out, fn)
    if not act: shutil.copyfile(os.path.join(raw, fn), dst); continue
    im = Image.open(os.path.join(raw, fn)).convert('RGBA'); W, H = im.size; S = W / 1080; sc_ = lambda v: v * S
    base = im.copy(); pl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)   # lines/arrows go on an overlay that is alpha-composited (drawing straight onto the RGBA band punched translucent holes)
    cos_ = [l for l in act if l['kind'] == 'callout']
    if len(cos_) > 1:
        for l in cos_:
            xs = sorted(pos[f][c['anchor']][0] for c in cos_); ys = sorted(pos[f][c['anchor']][1] for c in cos_)
            l['dx'] = -260 if pos[f][l['anchor']][0] <= xs[0] else 260; l['dy'] = -150 if pos[f][l['anchor']][1] <= ys[0] else 150
    loads = [l for l in act if l['kind'] == 'load']
    if len(loads) > 1:
        old, new = loads[-2:]
        amount = scale_at(new,f)
        load = dict(new, kg=old['kg']*(1-amount) + new['kg']*amount, joined=True)
        act = [l for l in act if l['kind'] != 'load'] + [load]
    for l in act:
        k = 1.0 if l.get('joined') else scale_at(l, f); kind = l['kind']; size = l.get('size', 54)
        if kind == 'inset':   # picture-in-picture close-up of the contact: circular magnified crop of the same frame around the anchor, amber ring, leader line
            ax_, ay_ = pos[f][l['anchor']][0]*W, pos[f][l['anchor']][1]*H; hr = sc_(l.get('src_half', 70)); z = l.get('zoom', 2.6); R_ = int(hr * z); cx_, cy_ = sc_(l['dx']), sc_(l['dy'])
            crop = base.crop((int(ax_ - hr), int(ay_ - hr), int(ax_ + hr), int(ay_ + hr))).resize((2 * R_, 2 * R_), Image.LANCZOS)
            mk = Image.new('L', (2 * R_, 2 * R_), 0); ImageDraw.Draw(mk).ellipse([0, 0, 2 * R_ - 1, 2 * R_ - 1], fill=255); ring = Image.new('RGBA', (2 * R_, 2 * R_), (0, 0, 0, 0))
            bg_ = Image.new('RGBA', (2 * R_, 2 * R_), (14, 14, 16, 255)); bg_.alpha_composite(crop); ImageDraw.Draw(ring).ellipse([0, 0, 2 * R_ - 1, 2 * R_ - 1], outline=AMBER, width=max(3, int(sc_(6))))
            bg_.alpha_composite(ring); bg_.putalpha(mk); lay = bg_.resize((max(1, int(2 * R_ * k)), max(1, int(2 * R_ * k))), Image.LANCZOS)
            dr.line([(ax_, ay_), (cx_, cy_)], fill=(255, 255, 255, int(200 * k)), width=max(1, int(sc_(3)))); pl.alpha_composite(lay, (int(cx_ - lay.size[0] / 2), int(cy_ - lay.size[1] / 2)))
            put(pl, pill(l['text'], None, l.get('size', 44), S), cx_, cy_ + R_ * k + sc_(34), k); continue
        if kind == 'legend':   # colour legend box, lower-left: dot + term per item, colours match the scene (l['items'] = [{'color': [r,g,b], 'text': ...}])
            f1 = ImageFont.truetype(FONT, int(l.get('size', 40) * S)); rh = int(l.get('size', 40) * 1.5 * S); d0 = ImageDraw.Draw(Image.new('RGBA', (4, 4)))
            wmax = max(d0.textlength(it['text'], font=f1) for it in l['items']); bw = int(wmax + 90 * S); bh = int(rh * len(l['items']) + 24 * S)
            bx = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(bx); bd.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=int(16 * S), fill=(20, 20, 22, 170))   # one small flat panel
            for i, it in enumerate(l['items']):
                cy = 12 * S + rh * (i + 0.5); bd.ellipse([22 * S, cy - 13 * S, 48 * S, cy + 13 * S], fill=tuple(it['color']) + (255,)); bd.text((64 * S, cy), it['text'], font=f1, fill=(255, 255, 255, 255), anchor='lm')
            lay = bx.resize((max(1, int(bw * k)), max(1, int(bh * k))), Image.LANCZOS); pl.alpha_composite(lay, (int(sc_(l['dx'])), int(sc_(l['dy']) - lay.size[1] / 2 * 0 + (bh - lay.size[1]) / 2 - bh / 2)))
            continue
        if kind == 'note':
            layer = pill(l['text'], l.get('sub'), l.get('size', 30), S)
            if l.get('fade_at_size'):
                layer.putalpha(layer.getchannel('A').point(lambda a: round(a * k)))
                k = 1
            put(pl, layer, sc_(l['dx']), sc_(l['dy']), k); continue
        ax, ay = pos[f][l['anchor']][0] * W, pos[f][l['anchor']][1] * H
        if kind in ('load','arrow_load'):   # arrow from the skull centre of mass to the C7 anchor (the load path), thickness ~ kg; pill beside it
            import math as _m
            x1, y1 = pos[f][l['anchor2']][0] * W, pos[f][l['anchor2']][1] * H; w = sc_(l['width_px'] if kind=='arrow_load' else 6 + l['kg'] * 1.1) * k; dx_, dy_ = x1 - ax, y1 - ay; ln_ = max(1.0, _m.hypot(dx_, dy_)); ux, uy = dx_ / ln_, dy_ / ln_; nx, ny = -uy, ux
            ex, ey = ax + dx_ * k, ay + dy_ * k; bx, by = ex - ux * w * 1.8, ey - uy * w * 1.8
            dr.polygon([(ax + nx * w / 2, ay + ny * w / 2), (ax - nx * w / 2, ay - ny * w / 2), (bx - nx * w / 2, by - ny * w / 2), (bx + nx * w / 2, by + ny * w / 2)], fill=AMBER)
            dr.polygon([(bx + nx * w * 1.6, by + ny * w * 1.6), (bx - nx * w * 1.6, by - ny * w * 1.6), (ex, ey)], fill=AMBER)
            if kind=='load' and l['text']: put(pl, pill(l['text'], l.get('sub'), size, S), min(ax, x1) - sc_(175), (ay + y1) / 2, k)
        elif kind == 'plumb':   # landmarks drawn at their TRUE projected positions: the ear outline is the hull of the ghost's own ear vertices, the ear dot sits inside it,
            # the shoulder dot sits on the acromial end of the clavicle; the line joins the two dots (it is vertical only because the pose really stacks ear over shoulder). Pills hug their dots.
            pp = PLUMB[str(f)]; ex, ey = pp['ear'][0] * W, pp['ear'][1] * H; sx, sy = pp['shoulder'][0] * W, pp['shoulder'][1] * H; al = int(255 * k); r = sc_(13); wl = max(2, int(sc_(5)))
            poly = [(a * W, b * H) for a, b in pp['ear_poly']]
            dr.line(poly + [poly[0]], fill=(10, 8, 6, int(200 * k)), width=wl + max(2, int(sc_(4))), joint='curve'); dr.line(poly + [poly[0]], fill=(255, 184, 28, al), width=wl, joint='curve')
            for key_, w_ in (('ear_inner', max(2, int(wl * 0.7))), ('ear_tragus', max(2, int(wl * 0.7)))):   # antihelix arc and tragus tick make the outline read as an ear
                pts_ = [(a * W, b * H) for a, b in pp[key_]]; dr.line(pts_, fill=(10, 8, 6, int(170 * k)), width=w_ + max(1, int(sc_(3))), joint='curve'); dr.line(pts_, fill=(255, 184, 28, int(230 * k)), width=w_, joint='curve')
            _SS = 4; _x0, _x1 = int(min(ex, sx) - wl * 2 - 2), int(max(ex, sx) + wl * 2 + 2); _y0, _y1 = int(min(ey, sy)) - 1, int(max(ey, sy)) + 2   # one anti-aliased segment (review 8: a 1 px kink at mid-height)
            _ln = Image.new('RGBA', ((_x1 - _x0) * _SS, (_y1 - _y0) * _SS), (0, 0, 0, 0)); ImageDraw.Draw(_ln).line([((ex - _x0) * _SS, (ey - _y0) * _SS), ((sx - _x0) * _SS, (sy - _y0) * _SS)], fill=(255, 255, 255, int(235 * k)), width=wl * _SS)
            ov.alpha_composite(_ln.resize((_x1 - _x0, _y1 - _y0), Image.LANCZOS), (_x0, _y0))
            for cx_, cy_ in ((ex, ey), (sx, sy)): dr.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=(255, 184, 28, al), outline=(10, 8, 6, al), width=max(1, int(sc_(3))))
            gap = sc_(l.get('pill_gap', 16)); geo = {'k': round(k, 3), 'ear': [ex / S, ey / S], 'acro': [sx / S, sy / S], 'tmj': [pp['tmj'][0] * W / S, pp['tmj'][1] * H / S], 'r': 13, 'line': [[ex / S, ey / S], [sx / S, sy / S]], 'poly': [[a / S, b / S] for a, b in poly]}
            for nm, txt, cx_, cy_ in (('ear', '귀', ex, ey), ('acro', '어깨', sx, sy)):
                lay = pill(txt, None, 46, S); pw, ph = lay.size; pcx = cx_ + (r + gap + pw * k / 2 if nm == 'ear' else -(r + gap + pw * k / 2)); put(pl, lay, pcx, cy_, k)   # the ear's outline extends behind its dot, so its pill sits in front of the dot
                geo['pill_' + nm] = [(pcx - pw * k / 2) / S, (cy_ - ph * k / 2) / S, (pcx + pw * k / 2) / S, (cy_ + ph * k / 2) / S]
            if l.get('text'): lay = pill(l['text'], l.get('sub'), size, S); pw, ph = lay.size; put(pl, lay, ex - r - gap - pw * k / 2 - sc_(10), (ey + sy) / 2, k)
            PDRAW[str(f)] = geo
        elif kind == 'gap':   # payoff figure: the ear is far in front of the shoulder; a dashed segment marks the gap between the two true projected landmarks
            import math as _g
            gx0, gy0 = pos[f][l['anchor']][0] * W, pos[f][l['anchor']][1] * H; gx1, gy1 = pos[f][l['anchor2']][0] * W, pos[f][l['anchor2']][1] * H; gl = max(1.0, _g.hypot(gx1 - gx0, gy1 - gy0)); ux, uy = (gx1 - gx0) / gl, (gy1 - gy0) / gl; dsh, gp = sc_(16), sc_(10); t_ = 0.0; wl = max(2, int(sc_(5)))
            while t_ < gl:
                dr.line([(gx0 + ux * t_, gy0 + uy * t_), (gx0 + ux * min(t_ + dsh, gl), gy0 + uy * min(t_ + dsh, gl))], fill=(255, 255, 255, int(235 * k)), width=wl); t_ += dsh + gp
            r = sc_(13)
            for nm_, txt_, cx_, cy_ in (('ear', '귀', gx0, gy0), ('acro', '어깨', gx1, gy1)):
                dr.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=(255, 184, 28, int(255 * k)), outline=(10, 8, 6, int(255 * k)), width=max(1, int(sc_(3))))
                lay = pill(txt_, None, 46, S); pw, ph = lay.size; put(pl, lay, cx_ + (r + sc_(16) + pw * k / 2) * (1 if nm_ == 'ear' else -1), cy_, k)
        elif kind == 'callout':
            px, py = ax + sc_(l['dx']), ay + sc_(l['dy']); dr.line([(px, py), (ax, ay)], fill=(255, 255, 255, int(220 * k)), width=max(1, int(sc_(3))))
            r = sc_(8) * k; dr.ellipse([ax - r, ay - r, ax + r, ay + r], fill=AMBER); put(pl, pill(l['text'], l.get('sub'), size, S), px, py, k)
    im.alpha_composite(ov); im.alpha_composite(pl); im.save(dst)
json.dump(PDRAW, open(E + '/plumb_draw.json', 'w')); print('labels2d done', out)
