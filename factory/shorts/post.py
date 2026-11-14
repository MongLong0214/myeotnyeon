"""Post-render numeric checks for a B3 package (every frame decoded at 108x192, render-time actor boxes) and the
1 fps review sheet. Every check is a number with a fixed limit; nothing here needs taste.

  .venv/bin/python -m factory.shorts.post upload/pkg/<id>_B        -> shorts_checks.json, shorts_checks.md, sheet_1fps.jpg"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import math

from factory.shorts.core import LIB, fit, em

FPS, W, H = 30, 1080, 1920
LIMITS = dict(motion_pct_min=95.0, static_hold_s_max=2.0, bg_changes_per_min_min=35.0, bg_changes_per_min_max=75.0,
              longest_same_bg_s_max=5.0, loop_seam_max=25.0, subject_height_min=0.40, hook_overlap_frames_max=0)
# gate.py items that PASS on >= 80% of the 15 hand-made reference packages (q038-q046, en001-003, ja001-003; 2026-11-13).
# They block. The rest fail or need review on references too and are listed for REVIEW.md, not blocking.
GATE_BLOCKING = ['static_holds', 'flash_black_frames', 'jump_cuts', 'hook_text_over_face_ocr', 'subtitle_over_face', 'small_characters',
                 'onscreen_text_clip_size', 'hook_title_overstatement', 'loudness_true_peak', 'thumbnail_reuses_frame']


def frames(video, w=108, h=192):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def cadence(F):
    n = len(F)
    diff = np.abs(F[1:] - F[:-1]).mean((1, 2, 3))
    still = diff <= .25
    run = best = 0
    for s in still:
        run = run + 1 if s else 0
        best = max(best, run)

    def hist(f):
        return np.concatenate([np.histogram(f[..., k], 16, (0, 256))[0] for k in range(3)]) / (f.shape[0] * f.shape[1])
    Hs = np.array([hist(f) for f in F])
    jump = .5 * np.abs(Hs[1:] - Hs[:-1]).sum(1)
    cuts = [i + 1 for i in np.where(jump > .25)[0]]
    segs = np.diff([0] + cuts + [n])
    return dict(frames=n, motion_pct=round(100 * float((diff > .25).mean()), 1), static_hold_s=round((best + 1) / FPS, 2),
                bg_changes_per_min=round(len(cuts) / (n / FPS) * 60, 1), longest_same_bg_s=round(float(segs.max()) / FPS, 2),
                loop_seam=round(float(np.abs(F[-1] - F[0]).mean()), 1)), [int(x) for x in cuts]


def shot_spans(c):
    """[(line id, shot index, scene, f0, f1)] exactly as B3FilmIn splits a line's frames between its shots"""
    out = []
    for u in c['utterances']:
        sh = u.get('shots') or []
        if not sh or u['mode'] == 'loop':
            continue
        n, seg = len(sh), round(u['dur'] / len(sh))
        for k, s in enumerate(sh):
            f0 = u['from_frame'] + k * seg
            f1 = u['from_frame'] + (u['dur'] if k == n - 1 else (k + 1) * seg)
            out.append((u['id'], k, s['s'], f0, f1))
    return out


def subjects(c, boxes):
    """per shot that contains characters: tallest actor box (clipped to the frame) / frame height, max over the shot"""
    rows = []
    for lid, k, scene, f0, f1 in shot_spans(c):
        hs = []
        for f in range(f0, f1):
            bs = boxes.get(str(f)) or []
            hs.append(max([(min(H, b[3]) - max(0, b[1])) / H for b in bs] or [0]))
        if max(hs or [0]) > 0:
            rows.append(dict(line=lid, shot=k, scene=scene, frames=[f0, f1 - 1], subject_height=round(max(hs), 3)))
    return rows


def where(c, f0, f1):
    """(line id, shot index, scene, line mode) of the shot holding most of frames f0..f1"""
    best = None
    for lid, k, scene, a, b in shot_spans(c):
        ov = min(b, f1 + 1) - max(a, f0)
        if ov > 0 and (best is None or ov > best[0]):
            best = (ov, lid, k, scene)
    if best is None:
        return None
    mode = next((u['mode'] for u in c['utterances'] if u['id'] == best[1]), '')
    return best[1], best[2], best[3], mode


def fix_hint(c, lid, k, scene, mode, what):
    """the concrete operator action for a too-small character / subtitle over a face in one shot"""
    if lid == 'L01' or mode == c.get('stage'):
        return (f"the open line always shows the spec stage (its shots are ignored): `{scene}` stage layout bug in B3Kit.tsx -> "
                f"set spec \"stage\" to another stage with a character and report `{scene}` to the CTO; changing L01 shots does nothing")
    if scene == 'react':
        if what == 'face':
            return f"replace {lid} shot {k + 1} with a non-character shot (paper/stamp/money/bubble), or set its y to 1960 (head higher)"
        return f"{lid} shot {k + 1} react: remove sc (or sc >= 2.45) and use y 1960-2090"
    return f"replace {lid} shot {k + 1} `{scene}` with a react close-up shot, rerun --from compile"


def gate_face_detail(c, it):
    """gate subtitle_over_face per span: line, shot, scene, frames, fix"""
    out = []
    for fd in (it or {}).get('findings', [])[:4]:
        f0, f1 = fd['frames']
        w = where(c, f0, f1)
        if w:
            lid, k, scene, mode = w
            out.append(f"{lid} shot {k + 1} `{scene}` frames {f0}-{f1} ({fd['seconds'][0]}-{fd['seconds'][1]} s, see gate/{fd.get('evidence')}): "
                       f"subtitle covers >12% of the detected face -> " + fix_hint(c, lid, k, scene, mode, 'face'))
        else:
            out.append(f"frames {f0}-{f1}: subtitle covers >12% of the detected face (loop line: fix the stage)")
    return '; '.join(out)


def bg_rate_hint(c, m, cuts):
    """which lines to cut shots from (or add to) so background changes/min lands inside the limit"""
    mins = m['frames'] / FPS / 60
    hi = m['bg_changes_per_min'] > LIMITS['bg_changes_per_min_max']
    need = (math.ceil(len(cuts) - LIMITS['bg_changes_per_min_max'] * mins + 1e-9) if hi
            else math.ceil(LIMITS['bg_changes_per_min_min'] * mins - len(cuts) - 1e-9))
    per = []
    for u in c['utterances']:
        n = sum(1 for f in cuts if u['from_frame'] <= f < u['from_frame'] + u['dur'])
        per.append((u['id'], u['mode'], len(u.get('shots') or []), n))
    if hi:
        top = sorted([p for p in per if p[3]], key=lambda p: -p[3])[:4]
        stagey = [a for a, b, k, n in top if n > k + 2]
        cut = [p for p in sorted(per, key=lambda p: -p[3]) if p[2] > 1 and p[0] != 'L01' and p[1] != 'loop']
        msg = f"; {len(cuts)} changes, remove >= {need}. Most changes: " + ', '.join(f"{a} ({b}, {k} shots, {n} changes)" for a, b, k, n in top)
        if stagey:
            msg += (f". {', '.join(stagey)} change far more often than their shots: the stage itself flickers (frames "
                    f"{[f for f in cuts if any(u['id'] in stagey and u['from_frame'] <= f < u['from_frame'] + u['dur'] for u in c['utterances'])][:6]}) -> "
                    f"stage layout bug in B3Kit.tsx: set spec \"stage\" to another stage and report it")
        if cut:
            msg += ". Otherwise drop 1 shot each from " + ', '.join(f"{a} ({b})" for a, b, k, n in cut[:need + 1]) + " (keep <= 2.6 s of speech per shot), rerun --from compile"
        return msg
    cand = [p for p in per if p[1] not in ('loop', 'choices', 'options', 'opinion', 'answer') and p[0] != 'L01' and p[2] < 2]  # a line takes 1-2 shots
    msg = f"; {len(cuts)} changes, add >= {need}"
    if cand:
        msg += ": give a 2nd shot to " + ', '.join(f"{a} ({b})" for a, b, k, _ in cand[:need])
    if len(cand) < need:
        n_fact = sum(1 for p in per if p[1].startswith('fact'))
        msg += (f"{' and' if cand else ':'} add {min(need - len(cand), 4 - n_fact)} fact line(s) with 2 shots each (spec allows 1-4 fact lines, now {n_fact})"
                if n_fact < 4 else "; every line already has 2 shots and 4 facts -> split a long line in two")
    return msg + ", rerun --from compile"


def hook_overlap(c, boxes):
    """frames where the hook text is on screen and an actor box reaches into the hook band"""
    L = c.get('locale', 'ko')
    h0, h1 = c['hook_text']
    D = LIB['defaults']
    s0, s1 = fit(h0, D['fixed_size']['hook1'], D['fit_box_px']['hook'], L), fit(h1, D['fixed_size']['hook2'], D['fit_box_px']['hook'], L)
    bottom = 150 + 1.25 * s0 + 1.0 * s1
    U = c['utterances']
    first, last = U[0], U[-1]
    vis = list(range(first['from_frame'], first['from_frame'] + first['dur'])) + list(range(last['from_frame'] + last['dur'] - 16, c['n']))
    bad = [f for f in vis if any(b[1] < bottom - 10 and b[2] > 60 and b[0] < 1020 for b in boxes.get(str(f)) or [])]
    return round(bottom), bad


def caption_boxes(cue, L):
    """drawn subtitle box in canvas px (BStandard captionStyle: centre x540, band y1192-1342, 72 px ko / fitted en, ja)"""
    lines = cue['text'].split('\n')
    size = 72 if L == 'ko' else max(44, min(72, math.floor(860 / max(1e-6, max(em(x, L) for x in lines)))))
    w = max(em(x, L) for x in lines) * size + 20  # + 10 px outline each side
    h = len(lines) * size * 1.04 + 20
    cy = 1192 + 75
    return [540 - w / 2, cy - h / 2, 540 + w / 2, cy + h / 2]


def subtitle_over_head(c, heads, limit=0.12):
    """frames where a drawn subtitle covers more than `limit` of a character's head box (render-time boxes)"""
    L = c.get('locale', 'ko')
    bad = []
    for cue in c['subtitles']:
        sb = caption_boxes(cue, L)
        for f in range(int(cue['start_s'] * FPS), int(cue['end_s'] * FPS)):
            for hb in heads.get(str(f)) or []:
                ix = max(0, min(sb[2], hb[2]) - max(sb[0], hb[0]))
                iy = max(0, min(sb[3], hb[3]) - max(sb[1], hb[1]))
                area = max(1, (hb[2] - hb[0]) * (hb[3] - hb[1]))
                if ix * iy / area > limit:
                    bad.append((f, cue['parent'], round(ix * iy / area, 2)))
    return bad


def sheet_1fps(video, out, n):
    tmp = Path(out).with_suffix('')
    tmp.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', 'fps=1:start_time=0.5,scale=216:384', str(tmp / '%03d.png')], check=True)
    fs = sorted(tmp.glob('*.png'))
    cols = 6
    im = Image.new('RGB', (cols * 216, -(-len(fs) // cols) * 404), '#111')
    d = ImageDraw.Draw(im)
    for i, f in enumerate(fs):
        x, y = i % cols * 216, i // cols * 404
        im.paste(Image.open(f), (x, y + 20))
        t = i + .5
        d.text((x + 4, y + 3), f'{t:.1f}s  f{int(t * FPS)}', fill='white')
        f.unlink()
    tmp.rmdir()
    im.save(out, quality=88)
    return len(fs)


def face_crop_box(box, w, h, margin=.18):
    """head box [x0,y0,x1,y1] grown by margin of its size on each side, clamped to the frame; None if nothing is left"""
    x0, y0, x1, y1 = box
    mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    a, b, c, d = max(0, int(x0 - mx)), max(0, int(y0 - my)), min(w, int(x1 + mx)), min(h, int(y1 + my))
    return (a, b, c, d) if c - a >= 8 and d - b >= 8 else None


def faces_1fps(video, boxes_path, out, height=220, cols=8):
    """every head box at the same 1 fps times as sheet_1fps (t+0.5 s), cropped and tiled, so R1 (anything over eyes,
    nose or mouth) is answered from close crops instead of 216 px tiles. Returns the number of crops."""
    hb = json.loads(Path(boxes_path).read_text())
    keys = sorted(int(k) for k in hb)
    if not keys:
        return 0
    tmp = Path(out).with_suffix('')
    tmp.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', 'fps=1:start_time=0.5', str(tmp / '%03d.png')], check=True)
    crops = []
    for i, f in enumerate(sorted(tmp.glob('*.png'))):
        t = i + .5
        fr = int(t * FPS)
        k = min(keys, key=lambda z: abs(z - fr))
        fim = Image.open(f).convert('RGB')
        for j, box in enumerate(hb[str(k)] if abs(k - fr) <= 3 else []):
            cb = face_crop_box(box, *fim.size)
            if cb:
                c = fim.crop(cb)
                crops.append((f'{t:.1f}s f{fr} #{j}', c.resize((max(1, round(c.width * height / c.height)), height))))
        f.unlink()
    tmp.rmdir()
    if not crops:
        return 0
    cw = max(c.width for _, c in crops)
    im = Image.new('RGB', (cols * cw, -(-len(crops) // cols) * (height + 20)), '#111')
    d = ImageDraw.Draw(im)
    for i, (lab, c) in enumerate(crops):
        x, y = i % cols * cw, i // cols * (height + 20)
        im.paste(c, (x, y + 20))
        d.text((x + 4, y + 3), lab, fill='white')
    im.save(out, quality=88)
    return len(crops)


def run(pkg):
    P = Path(pkg)
    c = json.loads((P / 'case.json').read_text())
    boxes = json.loads((P / 'actor_boxes.json').read_text()) if (P / 'actor_boxes.json').exists() else {}
    F = frames(P / 'video.mp4')
    m, cuts = cadence(F)
    subj = subjects(c, boxes) if boxes else []
    small = [r for r in subj if r['subject_height'] < LIMITS['subject_height_min'] and r['scene'] not in ('react', 'cell')]
    small += [r for r in subj if r['subject_height'] < LIMITS['subject_height_min'] and r['scene'] in ('react', 'cell')]
    band, hook_bad = hook_overlap(c, boxes) if boxes else (None, [])
    heads = json.loads((P / 'head_boxes.json').read_text()) if (P / 'head_boxes.json').exists() else None
    sub_head = subtitle_over_head(c, heads) if heads is not None else None
    g = json.loads((P / 'gate/gate.json').read_text()) if (P / 'gate/gate.json').exists() else {'items': []}
    gi = {i['check']: i for i in g['items']}
    rows = [
        ('motion', m['motion_pct'] >= LIMITS['motion_pct_min'], f"{m['motion_pct']}% of frame pairs move (min {LIMITS['motion_pct_min']})"),
        ('static_hold', m['static_hold_s'] <= LIMITS['static_hold_s_max'], f"longest still run {m['static_hold_s']} s (max {LIMITS['static_hold_s_max']})"),
        ('bg_change_rate', LIMITS['bg_changes_per_min_min'] <= m['bg_changes_per_min'] <= LIMITS['bg_changes_per_min_max'],
         f"{m['bg_changes_per_min']} background changes/min (allowed {LIMITS['bg_changes_per_min_min']}-{LIMITS['bg_changes_per_min_max']})"
         + ('' if LIMITS['bg_changes_per_min_min'] <= m['bg_changes_per_min'] <= LIMITS['bg_changes_per_min_max'] else bg_rate_hint(c, m, cuts))),
        ('longest_same_bg', m['longest_same_bg_s'] <= LIMITS['longest_same_bg_s_max'], f"longest same background {m['longest_same_bg_s']} s (max {LIMITS['longest_same_bg_s_max']})"),
        ('loop_seam', m['loop_seam'] <= LIMITS['loop_seam_max'], f"last vs first frame {m['loop_seam']}/255 (max {LIMITS['loop_seam_max']})"),
        ('subject_size', bool(boxes) and not small, (f"{len(subj)} character shots, smallest {min([r['subject_height'] for r in subj] or [0]):.2f} of frame height (min {LIMITS['subject_height_min']}); "
                                                     "under: " + '; '.join(f"{r['line']} shot {r['shot'] + 1} `{r['scene']}` frames {r['frames'][0]}-{r['frames'][1]}: character {r['subject_height']:.3f} < {LIMITS['subject_height_min']} of frame height -> " + fix_hint(c, r['line'], r['shot'], r['scene'], next((u['mode'] for u in c['utterances'] if u['id'] == r['line']), ''), 'size') for r in small)) if boxes else 'no actor_boxes.json (render with the current render.cjs)'),
        ('subtitle_over_head', sub_head is not None and not sub_head,
         (f"{len(sub_head)} frames where the subtitle covers >12% of a head; lines {sorted({x[1] for x in sub_head})}, frames {[x[0] for x in sub_head][:6]}"
          if sub_head is not None else 'no head_boxes.json (render with the current render.cjs)')),
        ('hook_over_actor', bool(boxes) and len(hook_bad) <= LIMITS['hook_overlap_frames_max'], f"{len(hook_bad)} hook frames with a character above y={band} (frames {hook_bad[:6]})" if boxes else 'no actor boxes'),
    ]
    for k in GATE_BLOCKING:
        it = gi.get(k)
        ok = bool(it) and it['status'].startswith('PASS')
        det = (it or {}).get('summary', 'gate item missing')[:140]
        if k == 'subtitle_over_face' and not ok and it:
            det += ' -- ' + gate_face_detail(c, it)
        rows.append((f'gate:{k}', ok, det))
    nonblock = [dict(check=i['check'], id=i['id'], status=i['status'], summary=i['summary'][:160]) for i in g['items'] if i['check'] not in GATE_BLOCKING and not i['status'].startswith('PASS')]
    sheet_n = sheet_1fps(P / 'video.mp4', P / 'sheet_1fps.jpg', m['frames'])
    if (P / 'head_boxes.json').exists():
        faces_1fps(P / 'video.mp4', P / 'head_boxes.json', P / 'faces_1fps.jpg')
    res = dict(pkg=str(P), metrics=m, limits=LIMITS, checks=[dict(check=a, ok=bool(b), detail=d) for a, b, d in rows], subjects=subj,
               gate_pass=sum(1 for i in g['items'] if i['status'].startswith('PASS')), gate_items=len(g['items']), gate_review=nonblock, sheet_1fps=sheet_n,
               ok=all(b for _, b, _ in rows))
    (P / 'shorts_checks.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    md = [f"# shorts checks — {P.name}: {'PASS' if res['ok'] else 'FAIL'}", '', '| check | ok | detail |', '|---|---|---|']
    md += [f"| {a} | {'PASS' if b else 'FAIL'} | {d} |" for a, b, d in rows]
    md += ['', f"gate.py: {res['gate_pass']}/{res['gate_items']} PASS. Non-blocking items for REVIEW.md:"] + [f"- {x['check']} ({x['id']}): {x['status']} — {x['summary']}" for x in nonblock]
    (P / 'shorts_checks.md').write_text('\n'.join(md) + '\n')
    return res


if __name__ == '__main__':
    r = run(sys.argv[1])
    print(Path(sys.argv[1], 'shorts_checks.md').read_text())
    sys.exit(0 if r['ok'] else 1)
