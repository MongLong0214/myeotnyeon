#!/usr/bin/env python3
"""Automated defect checks (one function per class in defects.yaml). Pure python (numpy/PIL), no Blender.
usage: python checks.py all EPISODE_DIR TAG          -> runs every episode-level check, JSON on stdout, exit 1 on any failure
       python checks.py <check> <args...>             -> one check (used by the meta-gate on regression fixtures)
Each check returns (ok, detail). A fixture for a class is an input that MUST make its check fail (gates/fixtures/<id>/)."""
import sys, json, os, glob
import numpy as np
from PIL import Image

def _load(p): return json.load(open(p))

# ---- subject-size: share of the band covered by the subject's projected bbox (alpha > 40), sampled every `step` frames
def subject_size(frames_dir, step=15, min_area=0.40, min_h=0.62, allow=()):
    bad = []; fs = sorted(glob.glob(os.path.join(frames_dir, 'f_*.png')))
    for path in fs[::step]:
        i = int(os.path.basename(path)[2:-4])
        if any(a <= i <= b for a, b in allow): continue
        a = np.asarray(Image.open(path).convert('RGBA'))[..., 3] > 40; ys, xs = np.nonzero(a)
        if not len(ys): bad.append((i, 'empty')); continue
        h, w = a.shape; bh = (ys.max() - ys.min()) / h; bw = (xs.max() - xs.min()) / w
        if bh * bw < min_area or bh < min_h: bad.append((i, round(bw * bh, 2), round(bh, 2)))
    return not bad, {'violations': bad[:12], 'n': len(bad)}

# ---- dead time: no declared event (label start/end, beat start) and no large motion for > max_s seconds
def dead_time(frames_dir, episode, fps=30, max_s=2.0, motion_min=0.9):
    fs = sorted(glob.glob(os.path.join(frames_dir, 'f_*.png'))); ev = set()
    for l in episode.get('labels', []): ev.update((l['f0'], l['f1']))
    for b in episode['beats']: ev.add(int(b['t0'] * fps))
    prev = None; mot = []
    for f in fs:
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (20, 20, 20, 255)); bg.alpha_composite(im)
        g = np.asarray(bg.convert('L').resize((270, 200))).astype(float); mot.append(0.0 if prev is None else float(np.abs(g - prev).mean())); prev = g
    W = int(max_s * fps); bad = []
    for i in range(0, len(mot) - W, 10):
        if np.mean(mot[i:i + W]) < motion_min and not any(i <= e <= i + W for e in ev): bad.append(i)
    return not bad, {'dead_windows_start_frames': bad[:12], 'n': len(bad)}

# ---- text size: every overlay string at least min px (full-resolution font size)
def text_size(episode, min_px=None):
    min_px = min_px or {'load': 48, 'callout': 48, 'plumb': 48, 'note': 44, 'pill': 48, 'legend': 48}; bad = []   # note 44 font px = ~32 px measured cap height
    for l in episode.get('labels', []):
        need = min_px.get(l['kind'], 48)
        if l.get('size', 54) < need: bad.append((l['id'], l.get('size', 54), need))
    return not bad, {'too_small': bad}

# ---- leaders: callout leader segments (anchor -> label centre) must not intersect each other, per frame
def _seg(a, b, c, d):
    def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0
def leaders_cross(episode, label_pos, W=1080, H=800, auto=True):
    bad = []; cos_ = [l for l in episode.get('labels', []) if l['kind'] == 'callout']
    frames = sorted({int(f) for f in label_pos if not str(f).startswith('_')})
    for f in frames:
        act = [l for l in cos_ if l['f0'] <= f <= l['f1']]; segs = []
        for l in act:
            a = label_pos[str(f)][l['anchor']]; ax, ay = a[0] * W, a[1] * H
            dx, dy = l['dx'], l['dy']
            if auto and len(act) > 1:   # same auto-layout rule as labels2d
                xs = sorted(label_pos[str(f)][c['anchor']][0] for c in act); ys = sorted(label_pos[str(f)][c['anchor']][1] for c in act)
                dx = -260 if label_pos[str(f)][l['anchor']][0] <= xs[0] else 260; dy = -150 if label_pos[str(f)][l['anchor']][1] <= ys[0] else 150
            segs.append(((ax, ay), (ax + dx, ay + dy)))
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if _seg(*segs[i], *segs[j]): bad.append(f); break
    return not bad, {'crossing_frames': sorted(set(bad))[:12], 'n': len(set(bad))}

# ---- rigid bend: declared chain must share the bend: max joint <= max_share of the chain's total rotation, on every held pose frame
def rigid_bend(pose_dump, chain, frames, max_share=0.45):
    bad = []
    for f in frames:
        a = [abs(pose_dump[str(f)][j]) for j in chain]; tot = sum(a)
        if tot > 6 and max(a) / tot > max_share: bad.append((f, round(max(a) / tot, 2)))
    return not bad, {'rigid_frames': bad[:10]}

# ---- caption truth: each beat's declared evidence must be measurable in the scene dumps
def caption_truth(episode, pose_dump, scene_dump, label_pos=None):
    bad = []
    for bi, b in enumerate(episode['beats']):
        for ev in b.get('evidence', []):
            if ev['type'] == 'pose_delta':   # sum of the listed joints' angles changes by >= min_deg between two frames
                s = lambda f: sum(pose_dump[str(f)][j] for j in ev['joints']); d = abs(s(ev['f1']) - s(ev['f0']))
                if d < ev['min_deg']: bad.append((bi, ev['type'], round(d, 1), ev['min_deg']))
            elif ev['type'] == 'object_scale':   # object visibly present (scale * radius_mm * 2 >= min_mm) at frame f
                v = scene_dump[ev['object']][str(ev['f'])] * ev['radius_mm'] * 2
                if v < ev['min_mm']: bad.append((bi, ev['type'], round(v, 2), ev['min_mm']))
            elif ev['type'] == 'pose_ratio':   # the reversed bow is at least min_ratio x the C bow, in the opposite direction
                sc_, sr = (sum(pose_dump[str(ev[k])][j] for j in ev['joints']) for k in ('f_c', 'f_rev'))
                if sc_ * sr >= 0 or abs(sr) < ev['min_ratio'] * abs(sc_): bad.append((bi, 'reversed curve weaker than C', round(sc_, 1), round(sr, 1)))
            elif ev['type'] == 'anchors_apart':   # two landmarks are at least min_dy of the band height apart (ear clearly above the shoulder)
                for f in ev['frames']:
                    pa, pb = label_pos[str(f)][ev['a']], label_pos[str(f)][ev['b']]
                    if abs(pa[1] - pb[1]) < ev['min_dy']: bad.append((bi, 'landmarks too close', ev['a'], f))
            elif ev['type'] == 'anchors_aligned':   # plumb: the two landmarks share a screen x within max_dx of the band width (one straight vertical)
                for f in ev['frames']:
                    pa, pb = label_pos[str(f)][ev['a']], label_pos[str(f)][ev['b']]
                    if abs(pa[0] - pb[0]) > ev['max_dx']: bad.append((bi, 'plumb has a jog', round(abs(pa[0] - pb[0]), 3), f))
            elif ev['type'] == 'dump_change':   # a scene value changes by >= min between two frames (a hook event: arc lit / vertebrae pulse by f12)
                d = abs(scene_dump[ev['key']][str(ev['f1'])] - scene_dump[ev['key']][str(ev['f0'])])
                if d < ev['min']: bad.append((bi, 'no event in window', ev['key'], round(d, 2)))
            elif ev['type'] == 'anchors_visible':   # every named anchor projects inside the band on the listed frames (a caption about the ear/shoulder needs them in frame)
                for f in ev['frames']:
                    for a_ in ev['anchors']:
                        x, y = (label_pos or {}).get(str(f), {}).get(a_, (9, 9))
                        if not (0.03 <= x <= 0.97 and 0.03 <= y <= 0.97): bad.append((bi, 'anchor out of frame', a_, f))
            else: bad.append((bi, 'unknown evidence type', ev['type'], 0))
        if b.get('cap') and not b.get('evidence') and b.get('claims_visual', True): bad.append((bi, 'caption without declared evidence', 0, 0))
    return not bad, {'unproven': bad}

# ---- visibility windows: a named object's opacity/scale (scene_dump) is zero outside its declared windows (arc only in beats 1 and 3; shoulder girdle only at the end)
def visibility_windows(scene_dump, windows, nf=None):
    bad = []
    for key, wins in windows.items():
        samples = scene_dump.get(key, {})
        count = max((int(f) for f in samples), default=-1) + 1
        if not samples or (nf is not None and nf != count) or set(samples) != {str(f) for f in range(count)}:
            bad.append((key, 'missing or extra frame'))
            continue
        for f in range(count):
            v = samples[str(f)]
            if v > 0.02 and not any(a <= f <= b for a, b in wins): bad.append((key, f)); break
    return not bad, {'visible_outside_window': bad}

# ---- steady glow: the signal inside the window has at most `max_turns` direction changes (no blinking)
def steady_glow(scene_dump, key, win, max_turns=2):
    v = [scene_dump[key][str(f)] for f in range(win[0], win[1] + 1)]; d = [b - a for a, b in zip(v, v[1:]) if abs(b - a) > 1e-4]
    turns = sum(1 for a, b in zip(d, d[1:]) if a * b < 0)
    return turns <= max_turns, {'turns': turns}

# ---- contact colour: saturated red pixels exist in the band during the contact frames (the lobe/contact is actually drawn)
def red_contact(frames_dir, f0, f1, min_px):
    best = 0
    _w0 = Image.open(os.path.join(frames_dir, 'f_%04d.png' % f0)).size[0]; min_px = min_px * (_w0 / 1080.0) ** 2   # the pixel budget is stated for a 1080 px band; fast drafts render at 25 % (area scales with the square)
    for f in range(f0, f1 + 1, 5):
        a = np.asarray(Image.open(os.path.join(frames_dir, 'f_%04d.png' % f)).convert('RGBA')).astype(int); m = (a[..., 3] > 200) & (a[..., 0] > 190) & (a[..., 1] < 100) & (a[..., 2] < 70); best = max(best, int(m.sum()))
    return best >= min_px, {'max_red_px': best, 'need': min_px}

# ---- every load arrow is anchored to a second landmark (ends on the lower neck, not in air)
def labels_anchored(episode):
    bad = [l['id'] for l in episode.get('labels', []) if l['kind'] in ('load', 'arrow_load', 'plumb', 'gap') and not l.get('anchor2')]
    return not bad, {'unanchored': bad}

# ---- labels belong to one beat: no label is visible across a caption change (caption/label overlap)
def label_beat_alignment(episode, fps=30, slack=8):
    bad = []; cuts = [int(b['t1'] * fps) for b in episode['beats'][:-1]]
    for l in episode.get('labels', []):
        for c in cuts:
            if l['f0'] + slack < c < l['f1'] - slack: bad.append((l['id'], c))
    return not bad, {'spans_caption_change': bad}

# ---- audio parts fit their descriptions (earshot match z >= 2.0)
def audio_fit(report):
    bad = [k for k, v in report.items() if v['z'] < 2.0]; return not bad, {'poor_fit': bad}

# ---- layout uses the frame height: the band reaches at least y_min (the empty bottom of the frame is used)
def layout_uses_height(episode, y_min=1340):
    l = episode['layout']; return l['band_y'] + l['band_h'] >= y_min, {'band_bottom': l['band_y'] + l['band_h'], 'need': y_min}

# ---- opening (owner round 3): the subject IS THE PERSON. The person's silhouette (alpha > 40) bbox covers >= 30 % of the band at f12 and the slump has started
# (the silhouette differs from f0 by >= 1.5 % of the band by f12).
def opening_event(frames_dir, at=12, min_area=0.30, min_change=0.015):
    def mask(i): return np.asarray(Image.open(os.path.join(frames_dir,f'f_{i:04d}.png')).convert('RGBA'))[..., 3] > 40
    a = mask(at); ys, xs = np.nonzero(a)
    area = 0.0 if not len(ys) else ((ys.max() - ys.min()) / a.shape[0]) * ((xs.max() - xs.min()) / a.shape[1])
    chg = float((mask(0) != a).mean())
    return area >= min_area and chg >= min_change, {'person_bbox_area_at_f%d' % at: round(area, 2), 'silhouette_change_f0_f%d' % at: round(chg, 3)}

# ---- establishing person (owner round 3): the person is on screen at skin opacity >= 0.6 for at least 60 consecutive frames from f0 (scene_dump HumanFade is the keyed material alpha)
from thresholds import T

def establishing_person(scene_dump, min_frames=round(30 * T["human"]["opening_s"]), min_alpha=0.6):   # owner round 5: 2 s (was 3 s); see LOG.md threshold reason log
    fade = scene_dump.get('HumanFade', {}); n = 0
    while str(n) in fade and fade[str(n)] >= min_alpha: n += 1
    return n >= min_frames, {'frames_at_alpha_ge_%.1f' % min_alpha: n, 'need': min_frames}

# ---- person reads as human (owner round 3): human_dump.json is measured by gates/human_gate.py in Blender on the payoff frames: projected body silhouette >= 50 % of the band height,
# head top above the shoulder dot on screen, no skull (or jaw) below the shoulder line, ear 12-15 cm in front of the shoulder (owner instruction 기괴한 자세, see LOG.md threshold reason log), and the gap closed (<= 3 cm) in the neutral frame
def human_reads_as_human(hd, min_h=0.5, gap=T["human"]["payoff_ear_offset_m"], gap_end=0.03):
    bad = []
    for r in hd.get('payoff', []):
        if r['band_h'] < min_h: bad.append((r['f'], 'silhouette height %.2f of the band' % r['band_h']))
        if not r['head_above_shoulder']: bad.append((r['f'], 'head top not above the shoulder dot'))
        if r['skull_min_z'] < r['shoulder_z']: bad.append((r['f'], 'skull below the shoulder line'))
        if not (gap[0] <= r['ear_fwd'] <= gap[1]): bad.append((r['f'], 'ear %.1f cm in front of the shoulder' % (100 * r['ear_fwd'])))
    e = hd.get('neutral')
    if not e: bad.append(('neutral', 'missing'))
    elif abs(e['ear_fwd']) > gap_end: bad.append((e['f'], 'ear-shoulder gap not closed: %.1f cm' % (100 * e['ear_fwd'])))
    if not hd.get('payoff'): bad.append(('payoff', 'no frames'))
    return not bad, {'violations': bad[:10], 'frames': len(hd.get('payoff', []))}

# ---- no on-screen model-estimate chip and no on-screen kg numbers (owner, 20:0x: "컴퓨터 모델추정 이거빼"); the narration keeps the qualifier
import re as _re
def no_kg_on_screen(episode):
    values = list(episode.get('title', [])) + [episode.get('brand','')]
    values.extend(''.join(part[0] for part in beat.get('cap',[])) for beat in episode.get('beats',[]))
    for label in episode.get('labels',[]):
        values.extend((str(label.get('text','')),str(label.get('sub',''))))
        values.extend(str(item.get('text','')) for item in label.get('items',[]))
    values.extend(str(note) for note in episode.get('notes',[]))
    if episode.get('layout',{}).get('tags',False):
        values.extend(b.get('tag','') for b in episode.get('beats',[]))
    bad = [text for text in values if _re.search(r'\d+(?:[.,]\d+)?\s*(?:kg|㎏|킬로|키로)|추정|도해|컴퓨터\s*모델|BodyParts3D|DBCLS|CC\s*BY|모델\s*출처', text, _re.I)]
    if any(item.get('kind') == 'load' for item in episode.get('labels',[])): bad.append('load label')
    if episode.get('credits'): bad.append('in-video credit')
    return not bad, {'on_screen':bad}


# ---- graphics must not cover the subject: legend/inset rectangles must not contain the declared subject anchors on any active frame
def labels_clear_of_anchors(episode, label_pos, anchors, W=1080, H=800):
    bad = []
    for l in episode.get('labels', []):
        if l['kind'] not in ('legend', 'inset'): continue
        w = 360 if l['kind'] == 'legend' else 2 * l.get('src_half', 60) * l.get('zoom', 2.6); h = 3 * 72 + 24 if l['kind'] == 'legend' else w
        x0, y0 = l['dx'], l['dy'] - (h / 2 if l['kind'] == 'inset' else 0); x1, y1 = x0 + w, y0 + h
        for f in range(l['f0'], l['f1'] + 1, 6):
            for a in anchors:
                p = label_pos.get(str(f), {}).get(a)
                if p and x0 <= p[0] * W <= x1 and y0 <= p[1] * H <= y1: bad.append((l['id'], f, a)); break
    return not bad, {'covers_subject': bad[:6]}

# ---- audio balance: share of energy in 500 Hz-3 kHz (phones) and loudness range (silence between events)
def audio_balance(wav, min_mid=0.12, min_range_db=10.0):
    import soundfile as sf
    x, sr = sf.read(wav, always_2d=True); x = x.mean(1); X = np.abs(np.fft.rfft(x)) ** 2; fr = np.fft.rfftfreq(len(x), 1 / sr)
    mid = float(X[(fr >= 500) & (fr <= 3000)].sum() / (X.sum() + 1e-12)); w = int(0.1 * sr)
    rms = np.array([np.sqrt(np.mean(x[i:i + w] ** 2) + 1e-12) for i in range(0, len(x) - w, w)]); db = 20 * np.log10(rms)
    rng = float(np.percentile(db, 95) - np.percentile(db, 10))
    return mid >= min_mid and rng >= min_range_db, {'mid_band_share': round(mid, 3), 'loudness_range_db': round(rng, 1)}

# ---- plumb landmarks, measured in projected pixels (label_pos['_plumb'], written by labelpos.py): the shoulder dot lies inside the ghost body's silhouette (camera ray hits the skin)
#      and OUTSIDE the projected bbox of the cervical vertebrae (not on the spine), on every frame of the plumb label; the ear is above it.
def _rect_dist(px, py, r):   # distance from a point to an axis-aligned rect [x0,y0,x1,y1]
    dx = max(r[0] - px, 0, px - r[2]); dy = max(r[1] - py, 0, py - r[3]); return (dx * dx + dy * dy) ** 0.5
def _in_poly(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def plumb_projected(label_pos, f0, f1, W=1080, H=880, r=13):
    pl = label_pos.get('_plumb'); bad = []
    if not pl: return False, {'error': 'no _plumb section'}
    for f in range(f0, f1 + 1):
        p = pl.get(str(f))
        if p is None: bad.append((f, 'missing')); continue
        if not p['in_skin']: bad.append((f, 'shoulder dot outside the ghost silhouette'))
        elif not p['outside_spine_bbox']: bad.append((f, 'shoulder dot on the spine'))
        elif 'spine_bbox' in p and _rect_dist(p['shoulder'][0] * W, p['shoulder'][1] * H, [v * s_ for v, s_ in zip(p['spine_bbox'], (W, H, W, H))]) < r: bad.append((f, 'shoulder dot disc touches the spine bbox'))
        elif not p['ear_above']: bad.append((f, 'ear not above shoulder'))
        elif 'ear_in_outline' in p and not p['ear_in_outline']: bad.append((f, 'ear dot outside the ghost ear outline'))
        elif 'ear_in_skin' in p and not p['ear_in_skin']: bad.append((f, 'ear dot outside the ghost head silhouette'))
    return not bad, {'bad_frames': bad[:8], 'n': len(bad), 'frames_checked': f1 - f0 + 1}

# ---- plumb as DRAWN (plumb_draw.json written by labels2d + the composited frames): dots exactly on the projected landmarks, ear dot inside the drawn ear outline, each label <= 40 px from its dot,
#      the line's end points are the two dots and its pixels exist on every visible frame, the ear outline pixels exist (k >= 0.9 frames are verified in the image).
def plumb_drawn(draw, label_pos, frames_dir, f0, f1, W=1080, H=880, max_label_px=40, k_min=0.02, k_pix=0.9):
    from PIL import Image
    bad = []; n = 0; pl = label_pos.get('_plumb', {})
    def near(img, x, y, test, rad=1):
        s = img.shape[1] / W; cx, cy = int(round(x * s)), int(round(y * s)); y0, y1, x0, x1 = max(cy - rad, 0), cy + rad + 1, max(cx - rad, 0), cx + rad + 1
        return any(test(*img[yy, xx]) for yy in range(y0, min(y1, img.shape[0])) for xx in range(x0, min(x1, img.shape[1])))
    white = lambda r_, g, b: min(r_, g, b) > 175; amber = lambda r_, g, b: r_ > 200 and 130 < g < 215 and b < 100
    for f in range(f0, f1 + 1):
        d = draw.get(str(f)); p = pl.get(str(f))
        if d is None or p is None: bad.append((f, 'plumb not drawn')); continue
        if d['k'] < k_min: continue
        n += 1
        ear, acro = d['ear'], d['acro']
        if abs(ear[0] - p['ear'][0] * W) > 1.5 or abs(ear[1] - p['ear'][1] * H) > 1.5: bad.append((f, 'ear dot is not on the projected ear landmark')); continue
        if abs(acro[0] - p['shoulder'][0] * W) > 1.5 or abs(acro[1] - p['shoulder'][1] * H) > 1.5: bad.append((f, 'shoulder dot is not on the projected acromion')); continue
        if not _in_poly(d['poly'], ear[0], ear[1]): bad.append((f, 'ear dot not inside the drawn ear outline')); continue
        if max(abs(d['line'][0][0] - ear[0]), abs(d['line'][0][1] - ear[1]), abs(d['line'][1][0] - acro[0]), abs(d['line'][1][1] - acro[1])) > 1.0: bad.append((f, 'line does not join the two dots')); continue
        dl = _rect_dist(ear[0], ear[1], d['pill_ear']); ds = _rect_dist(acro[0], acro[1], d['pill_acro'])
        if dl > max_label_px or ds > max_label_px: bad.append((f, 'label farther than %d px from its dot' % max_label_px, round(dl), round(ds))); continue
        if 'tmj' in d:   # the ear sits just behind and above the jaw joint (review 7: it was drawn over the cerebellum, 130 px behind it)
            ddx = d['tmj'][0] - ear[0]; ddy = d['tmj'][1] - ear[1]
            if not (0 <= ddx <= 90 and 8 <= ddy <= 100): bad.append((f, 'ear not just behind/above the jaw joint', round(ddx), round(ddy))); continue
        if frames_dir and d['k'] >= k_pix:
            img = np.asarray(Image.open(os.path.join(frames_dir, 'f_%04d.png' % f)).convert('RGBA')); a = img[..., 3:4] / 255.0; img = (img[..., :3] * a).astype(np.uint8)
            miss = [t for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.88) if not near(img, ear[0] + (acro[0] - ear[0]) * t, ear[1] + (acro[1] - ear[1]) * t, white)]
            if miss: bad.append((f, 'line pixels missing along the segment', miss)); continue
            if not near(img, ear[0], ear[1], amber, 3) or not near(img, acro[0], acro[1], amber, 3): bad.append((f, 'dot pixels missing')); continue
            P = d['poly']; hits = sum(near(img, P[i][0], P[i][1], amber, 2) for i in range(len(P)))
            if hits < 0.75 * len(P): bad.append((f, 'ear outline not drawn', hits, len(P)))
    return (not bad and n > 0), {'bad_frames': bad[:8], 'n': len(bad), 'frames_checked': n}

# ---- plumb pills sit clear of the dots (pill half width + dot radius < pill_dx)
def labels_clear_of_dots(episode, dot_r=14):
    bad = []
    for l in episode.get('labels', []):
        if l['kind'] == 'plumb':
            half = l.get('pill_half_w', 70); dx = l.get('pill_dx', 140)
            if half + dot_r >= dx: bad.append((l['id'], half, dx))
    return not bad, {'pill_covers_dot': bad}

# ---- per-beat loudness: every beat within max_db of the median beat (no quiet beat lost on a phone)
def audio_beat_balance(wav, beats, fps=30, max_db=6.0):
    import soundfile as sf
    x, sr = sf.read(wav, always_2d=True); x = x.mean(1); out = []
    for b in beats:
        s, e = int(b[0] * sr), int(b[1] * sr); out.append(20 * np.log10(np.sqrt(np.mean(x[s:e] ** 2)) + 1e-9))
    med = float(np.median(out)); bad = [(i, round(v - med, 1)) for i, v in enumerate(out) if abs(v - med) > max_db]
    return not bad, {'beat_rms_db': [round(v, 1) for v in out], 'off_median': bad}

# ---- frame cadence: no periodic low-delta pattern (review 9: f792-f876 every third frame barely changed = judder). Over every 48-frame window with real motion (median delta >= 1.0)
#      fewer than 6 % of frames may fall under half the local (7-frame) median (draft14: 8-12 % in f768-f852, 0 % everywhere else).
def cadence_ok(deltas, win=48, stride=12, min_med=1.0):
    bad = []; d = np.asarray(deltas, float); k = 7; pad = np.pad(d, k // 2, mode='edge'); loc = np.array([np.median(pad[i:i + k]) for i in range(len(d))])   # local median: smooth speed changes are not judder
    res = d - np.array([pad[i:i + k].mean() for i in range(len(d))])
    for i in range(0, len(d) - win, stride):
        w = d[i:i + win]; med = float(np.median(w))
        if med < min_med: continue
        low = float((w < 0.5 * loc[i:i + win]).mean()); x = res[i:i + win]; den = float((x * x).sum()) + 1e-9
        ac = max(float((x[:-l] * x[l:]).sum()) / den for l in range(2, 7))
        if low >= 0.06: bad.append((i, round(low, 2), round(ac, 2)))
    return not bad, {'bad_windows': bad[:8], 'n': len(bad)}
def frame_cadence(frames_dir):
    fs = sorted(glob.glob(os.path.join(frames_dir, 'f_*.png'))); prev = None; dl = []
    for f in fs:
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (20, 20, 20, 255)); bg.alpha_composite(im); g = np.asarray(bg.convert('L').resize((270, 200))).astype(float); dl.append(0.0 if prev is None else float(np.abs(g - prev).mean())); prev = g
    return cadence_ok(dl)

# ---- narration (owner): character error rate of the whisper transcript against the script <= 8 %, and caption/narration sync (each line starts within 0.6 s of its beat start,
#      ends inside the beat, pace 5.6-7.2 syll/s)
def _norm(t):
    import re
    for a in ('씨짜', '씨자', '십자', '시자', '흰시자', 'C자', 'c자'): t = t.replace(a, 'c자')   # spoken/heard variants of the written 'C자' (lexicon: spoken 씨짜)
    t = t.replace('km', '킬로').replace('KM', '킬로')
    return re.sub(r'[^가-힣0-9a-zA-Z]', '', t).lower()
def cer(ref, hyp):
    a, b = _norm(ref), _norm(hyp)
    if not a: return 0.0 if not b else 1.0
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[len(b)] / len(a)
def narration_wer(pairs, max_cer=0.08):
    errs = [(i, round(cer(r, h), 3)) for i, (r, h) in enumerate(pairs)]; tot = sum(cer(r, h) * len(_norm(r)) for r, h in pairs) / max(1, sum(len(_norm(r)) for r, h in pairs))
    return tot <= max_cer, {'cer_total': round(tot, 3), 'per_line': errs}
def narration_sync(lines, beats, start_tol=0.6, rate=(5.6, 7.2)):
    bad = []
    for l in lines:
        b = beats[l['beat']]
        if not (b['t0'] <= l['start'] <= b['t0'] + start_tol): bad.append((l['line'], 'starts off the caption change', round(l['start'] - b['t0'], 2)))
        if l['end'] > b['t1'] + 0.05: bad.append((l['line'], 'runs past its beat', round(l['end'] - b['t1'], 2)))
        if not (rate[0] <= l['rate'] <= rate[1]): bad.append((l['line'], 'pace outside 5.6-7.2 syll/s', l['rate']))
    return not bad, {'bad': bad}

def scene_timing(episode, pose, scene):
    bend = episode.get('rigid_bend_check', {'chain': [], 'frames': []})
    results = {
        'rigid_bend': rigid_bend(pose, bend['chain'], bend['frames']),
        'visibility_windows': visibility_windows(scene, episode.get('scene_visibility', {}),
                                                nf=round(episode['duration']*episode['fps'])),
    }
    for key, window in episode.get('steady_glow', {}).items():
        results['steady_glow_' + key] = steady_glow(scene, key, window)
    return results

def run_all(E, tag):
    ep = _load(E + '/episode.json'); res = {}; frames = f'{E}/frames_{tag}_raw'
    res['subject_size'] = subject_size(frames, allow=tuple(tuple(a) for a in ep.get('subject_size_allow', [])))
    res['dead_time'] = dead_time(frames, ep); res['frame_cadence'] = frame_cadence(frames)
    res['text_size'] = text_size(ep)
    lp = E + '/label_pos.json'; res['leaders_cross'] = leaders_cross(ep, _load(lp)) if os.path.exists(lp) else (False, {'error': 'no label_pos.json'})
    pd = _load(E + '/pose_dump.json'); sd = _load(E + '/scene_dump.json')
    res.update(scene_timing(ep, pd, sd))
    if 'contact_color_check' in ep: cc = ep['contact_color_check']; res['red_contact'] = red_contact(frames, cc['f0'], cc['f1'], cc['min_px'])
    res['establishing_person'] = establishing_person(sd)
    if ep.get('payoff_frames') or ep.get('region','neck')=='neck' and any(l['kind']=='gap' for l in ep.get('labels',[])):
        if os.path.exists(E + '/gates/human_dump.json'):
            from thresholds import episode_gap
            res['human_reads_as_human'] = human_reads_as_human(_load(E + '/gates/human_dump.json'), gap=episode_gap(E))
        else: res['human_reads_as_human'] = (False, {'error': 'no gates/human_dump.json (run human_gate.py)'})
    res['opening_event'] = opening_event(frames); res['labels_clear_of_anchors'] = labels_clear_of_anchors(ep, _load(lp), ['A_Contact', 'A_C56', 'A_Root']) if os.path.exists(lp) else (False, {'error': 'no label_pos'})
    if os.path.exists(E + '/audio/sfx.wav'): res['audio_balance'] = audio_balance(E + '/audio/sfx.wav')
    res['layout_uses_height'] = layout_uses_height(ep)
    pl = [l for l in ep.get('labels', []) if l['kind'] == 'plumb']
    if pl and os.path.exists(lp):
        res['plumb_projected'] = plumb_projected(_load(lp), pl[0]['f0'] + 1, pl[0]['f1'] - 1)
        res['plumb_drawn'] = plumb_drawn(_load(E + '/plumb_draw.json'), _load(lp), f'{E}/frames_{tag}', pl[0]['f0'] + 1, pl[0]['f1'] - 1) if os.path.exists(E + '/plumb_draw.json') else (False, {'error': 'no plumb_draw.json'})
    res['labels_clear_of_dots'] = labels_clear_of_dots(ep)
    if os.path.exists(E + '/audio/sfx.wav'): res['audio_beat_balance'] = audio_beat_balance(E + '/audio/sfx.wav', [(b['t0'], b['t1']) for b in ep['beats']])
    res['no_kg_on_screen'] = no_kg_on_screen(ep)
    res['labels_anchored'] = labels_anchored(ep); res['label_beat_alignment'] = label_beat_alignment(ep)
    if os.path.exists(E + '/audio/sfx_report.json'): res['audio_fit'] = audio_fit(_load(E + '/audio/sfx_report.json'))
    res['caption_truth'] = caption_truth(ep, pd, sd, _load(lp) if os.path.exists(lp) else None)
    return res

if __name__ == '__main__':
    if sys.argv[1] == 'all':
        r = run_all(sys.argv[2], sys.argv[3]); out = {k: {'ok': bool(v[0]), **v[1]} for k, v in r.items()}; out['pass'] = all(v['ok'] for v in out.values())
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str)); sys.exit(0 if out['pass'] else 1)
