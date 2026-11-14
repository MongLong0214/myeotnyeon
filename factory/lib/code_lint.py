"""Code lint gate: measurable picture defects (idea from AI-Video-Factory lint.ts, MIT; written anew here).

  .venv/bin/python factory/lib/code_lint.py VIDEO --shots shots.json --subtitles captions.json
        [--faces faces.json] [--format longform|shorts] [--out report.json]

Checks, each with its own certainty:
- face_cut       a face box partly outside the frame (8–70 % visible) in >= 1/3 of a shot's samples.  BLOCKING
- text_on_face   the active subtitle box (or a supplied text box) covers > 25 % of a face.          BLOCKING
- subtitle_overflow  each cue measured with the render font: wider than the caption box or more
                 lines than fit its height.                                                         BLOCKING
- subtitle_rules lines over the house 18/16 chars, > 2 lines, particle-first cue (captions.lint).   report-only
- static / repeats / pops  production/lf_toon/tools/scene_check.py `action` (per shot), `repeats`
                 (--repeat-mad 10, > 5 % of seconds), `pops`. Deliberate holds, callbacks and flashes
                 are legitimate, so these never block.                                             report-only
- rhythm         shot-length tempo from the shot list (cinecode validate_shots.py `rhythm`, MIT, notice
                 below): spread (cv) of shot lengths >= 0.30 with 12+ shots, no run of 5+ shots of about
                 the same length (within 15 %), acts/chapters not all at one pace (within 25 %). report-only
- scene_loudness opt-in (scene_loudness=True): scene_check.py `sound` per shot; a scene more than 3 LU off
                 the median scene (cinecode C15).                                                  report-only
- variety        opt-in (variety=True): 3+ consecutive shots of one `size` (wide/medium/close/insert), only
                 when >= half the shots carry `size` (AI-Video-Factory variety.ts idea, MIT).      report-only
Face boxes are not detected from pixels (no installed cartoon face model): they come from render
metadata (`faces.json` rows {frame|t, box:[x,y,w,h], id} in video pixels, or `faces` on a shot).
Without them face checks are NOT_MEASURED, not PASS.

MIT License (AI-Video-Factory, idea and thresholds faceVisible [0.08, 0.7], faceCutShare 1/3, textOnFace 0.25)

Copyright (c) 2026 Ersin KOÇ

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Portions (check_rhythm) adapted from cinecode (MIT) - https://github.com/sarpstar/cinecode @67f9807,
scripts/validate_shots.py `rhythm`. MIT License, Copyright (c) 2026 Sarp Yıldız (@sarpstar). Permission notice
and warranty disclaimer as above (identical MIT text).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from . import captions as cap
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import captions as cap

ROOT = Path(__file__).resolve().parents[2]
SCENE_CHECK = ROOT / 'production/lf_toon/tools/scene_check.py'
FONT = ROOT / 'production/lf_toon/public/fonts/Pretendard-ExtraBold.woff2'
LINT = dict(face_visible=(0.08, 0.7), face_cut_share=1 / 3, text_on_face=0.25, step=3,
            repeat_mad=10.0, repeat_share=0.05, static_share=0.15, action_fps=2.0, action_min=1.0)
# Captions.tsx layout 'full' on the 1920x1080 long-form canvas (left/right 115, top 931, height 132).
LONGFORM_CAPTION = dict(x=115, y=931, w=1690, h=132, size=54, line_height=1.15, stroke=10, canvas=[1920, 1080])


def area(b):
    return max(0.0, b[2]) * max(0.0, b[3])


def overlap(a, b):
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def visible_share(box, width, height):
    return overlap(box, (0, 0, width, height)) / area(box) if area(box) else 0.0


def shot_of(shots, t):
    return next((s for s in shots if s['start_s'] <= t < s['end_s']), None)


def face_rows(shots, faces, fps, step):
    """Per-frame face boxes from metadata; shot-level `faces` are held for every sampled frame of the shot."""
    rows = []
    for f in faces or []:
        t = f['t'] if 't' in f else f['frame'] / fps
        rows.append(dict(t=t, id=str(f.get('id', '?')), box=list(map(float, f['box']))))
    for s in shots:
        for f in s.get('faces', []):
            n0, n1 = round(s['start_s'] * fps), max(round(s['start_s'] * fps) + 1, round(s['end_s'] * fps))
            for n in list(range(n0, n1, step)) + [n1 - 1]:
                rows.append(dict(t=n / fps, id=str(f.get('id', '?')), box=list(map(float, f['box']))))
    return rows


def caption_box(geometry, width, height):
    k = width / geometry['canvas'][0]
    return [geometry['x'] * k, geometry['y'] * k, geometry['w'] * k, geometry['h'] * k], k


def check_faces(shots, faces, subtitles, texts, width, height, fps, geometry):
    rows = face_rows(shots, faces, fps, LINT['step'])
    if not rows:
        return dict(status='NOT_MEASURED', reason='no face boxes in render metadata'), \
            dict(status='NOT_MEASURED', reason='no face boxes in render metadata')
    lo, hi = LINT['face_visible']
    per = {}
    for r in rows:
        s = shot_of(shots, r['t'])
        key = (s['id'] if s else '-', r['id'])
        v = visible_share(r['box'], width, height)
        d = per.setdefault(key, dict(samples=0, cut=[]))
        d['samples'] += 1
        if lo <= v < hi:
            d['cut'].append(round(r['t'], 3))
    cut = [dict(shot=k[0], face=k[1], seconds=v['cut'][:6], share=round(len(v['cut']) / v['samples'], 3))
           for k, v in per.items() if v['cut'] and len(v['cut']) / v['samples'] >= LINT['face_cut_share']]
    sub_box = caption_box(geometry, width, height)[0] if geometry else None
    covered = []
    for r in rows:
        boxes = [('subtitle', sub_box)] if sub_box and any(x['start_s'] <= r['t'] < x['end_s'] and x.get('text', '').strip()
                                                           for x in subtitles) else []
        boxes += [(x.get('text', 'text'), x['box']) for x in texts if x.get('start_s', 0) <= r['t'] < x.get('end_s', 1e9)]
        for name, b in boxes:
            share = overlap(r['box'], b) / area(r['box']) if area(r['box']) else 0
            if share > LINT['text_on_face']:
                covered.append(dict(t=round(r['t'], 3), face=r['id'], text=name, share=round(share, 3)))
    face_cut = dict(status='FAIL' if cut else 'PASS', issues=cut, samples=len(rows))
    text_face = dict(status='FAIL' if covered else 'PASS', issues=covered[:20], count=len(covered))
    return face_cut, text_face


def wrap_measure(text, font, max_w):
    """Browser-like keep-all wrap: explicit lines first, then break between words only."""
    lines = []
    for para in text.split('\n'):
        cur = ''
        for word in para.split():
            trial = (cur + ' ' + word).strip()
            if cur and font.getlength(trial) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def check_overflow(subtitles, width, height, geometry, font_path=FONT):
    if not geometry:
        return dict(status='NOT_MEASURED', reason='no caption box geometry for this format')
    from PIL import ImageFont
    box, k = caption_box(geometry, width, height)
    size = geometry['size'] * k
    font = ImageFont.truetype(str(font_path), max(1, round(size)))
    pad = geometry.get('stroke', 0) * k  # paint-order stroke: half the stroke each side
    capacity = int((box[3] + 1e-6) // (size * geometry['line_height']))
    issues = []
    for i, s in enumerate(subtitles):
        text = s.get('text', '').strip()
        if not text:
            continue
        lines = wrap_measure(text, font, box[2] - pad)
        widest = max(font.getlength(l) + pad for l in lines)
        if widest > box[2] or len(lines) > capacity:
            issues.append(dict(cue=i, start_s=round(s['start_s'], 3), text=text, lines=len(lines), capacity=capacity,
                               width_px=round(widest, 1), box_px=round(box[2], 1)))
    return dict(status='FAIL' if issues else 'PASS', issues=issues[:20], count=len(issues),
                method=f'PIL {Path(font_path).name} at {round(size)} px, keep-all wrap, box {[round(x) for x in box]}')


def scene_check(cmd, video, *extra):
    p = subprocess.run([sys.executable, str(SCENE_CHECK), cmd, str(video), *map(str, extra)], capture_output=True, text=True)
    if p.returncode not in (0, 1):
        raise RuntimeError(p.stderr.strip()[-400:])
    return p.stdout


def stamp_s(s):
    m = re.match(r'(?:(\d+):)?(\d+(?:\.\d+)?)', s)
    return float(m.group(1) or 0) * 60 + float(m.group(2))


def check_video(video, shots, duration):
    out = {}
    try:
        bounds = sorted({round(s['start_s'], 3) for s in shots} | {round(shots[-1]['end_s'], 3)}) if shots else []
        args = ['--fps', LINT['action_fps'], '--min', LINT['action_min']] + (['--scenes', ','.join(map(str, bounds))] if len(bounds) > 1 else [])
        text = scene_check('action', video, *args)
        flagged = [l.strip() for l in text.splitlines() if 'CHECK' in l]
        secs = sum(stamp_s(b) - stamp_s(a) for a, b in (re.search(r'(\S+)-(\S+)\s+residual', l).groups() for l in flagged))
        share = secs / duration if duration else 0
        out['static'] = dict(status='ADVISORY', flagged=flagged[:20], seconds=round(secs, 2), share=round(share, 3),
                             over_threshold=share > LINT['static_share'], threshold=LINT['static_share'])
    except Exception as e:
        out['static'] = dict(status='NOT_MEASURED', reason=str(e))
    try:
        text = scene_check('repeats', video, '--repeat-mad', LINT['repeat_mad'])
        m = re.search(r'(\d+) repeats?, (\d+) s of (\d+)', text)
        secs, total = (int(m.group(2)), int(m.group(3))) if m else (0, 1)
        out['repeats'] = dict(status='ADVISORY', spans=[l.strip() for l in text.splitlines() if ' repeats ' in l][:10],
                              seconds=secs, share=round(secs / max(1, total), 3),
                              over_threshold=secs / max(1, total) > LINT['repeat_share'], threshold=LINT['repeat_share'])
    except Exception as e:
        out['repeats'] = dict(status='NOT_MEASURED', reason=str(e))
    try:
        text = scene_check('pops', video)
        frames = [int(x) for x in re.findall(r'frame (\d+) \(', text)]
        count = int(re.search(r'pops[^:]*: (\d+)', text).group(1))
        out['pops'] = dict(status='ADVISORY', count=count, frames=frames, over_threshold=count > 0, threshold=0)
    except Exception as e:
        out['pops'] = dict(status='NOT_MEASURED', reason=str(e))
    return out


def check_scene_loudness(video, shots, threshold=3.0):
    """Per-scene loudness jumps against the median scene (scene_check.py sound). Report-only."""
    try:
        bounds = sorted({round(s['start_s'], 3) for s in shots} | {round(shots[-1]['end_s'], 3)}) if shots else []
        args = (['--scenes', ','.join(map(str, bounds))] if len(bounds) > 1 else []) + ['--max-lu', threshold]
        text = scene_check('sound', video, *args)
        rows = re.findall(r'^\s*(\S+) (\S+)-(\S+)\s+(-?[\d.]+) LUFS.*?((?:LOUDER|QUIETER) by ([\d.]+) LU)', text, re.M)
        jumps = [dict(scene=n, start_s=stamp_s(a), end_s=stamp_s(b), lufs=float(l), note=note, lu=float(lu))
                 for n, a, b, l, note, lu in rows]
        return dict(status='ADVISORY', jumps=jumps, count=len(jumps), over_threshold=bool(jumps), threshold=threshold)
    except Exception as e:
        return dict(status='NOT_MEASURED', reason=str(e))


def check_variety(shots, run_max=3):
    """3+ consecutive shots of the same size read as one long shot. Measured only when >= half the shots
    carry `size`. Report-only."""
    sized = [s for s in shots if s.get('size')]
    if not shots or len(sized) * 2 < len(shots):
        return dict(status='NOT_MEASURED', reason=f'{len(sized)} of {len(shots)} shots carry size')
    runs, i = [], 0
    while i < len(shots):
        j = i
        while j + 1 < len(shots) and shots[i].get('size') and shots[j + 1].get('size') == shots[i].get('size'):
            j += 1
        if j - i + 1 >= run_max:
            runs.append(dict(size=shots[i]['size'], shots=[s.get('id') for s in shots[i:j + 1]], length=j - i + 1))
        i = j + 1
    return dict(status='ADVISORY', runs=runs, count=len(runs), over_threshold=bool(runs), threshold=run_max)


def check_rhythm(shots, min_cv=0.30, run_max=5, alike=0.15, acts_flat=1.25, min_shots=12):
    """Tempo must move: shot lengths that are all alike, a long run of equal shots, or acts at one pace read
    as monotony. Shots carry start_s/end_s and optionally act/chapter/section. Report-only."""
    d = [max(0.0, s['end_s'] - s['start_s']) for s in shots]
    out = dict(status='ADVISORY', shots=len(d), threshold=dict(min_cv=min_cv, run_max=run_max, acts_flat=acts_flat))
    if len(d) < min_shots:
        return dict(out, status='NOT_MEASURED', reason=f'{len(d)} shots, rhythm needs {min_shots}+')
    issues, mean = [], sum(d) / len(d)
    cv = (sum((x - mean) ** 2 for x in d) / len(d)) ** 0.5 / mean if mean else 0.0
    if cv < min_cv:
        issues.append(f'shot lengths too even (cv {cv:.2f} < {min_cv}): mix quick runs with long holds')
    run, best = 1, (1, 0)
    for i in range(1, len(d)):
        run = run + 1 if abs(d[i] - d[i - 1]) <= alike * max(d[i], d[i - 1]) else 1
        best = max(best, (run, i))
    if best[0] >= run_max:
        a, b = shots[best[1] - best[0] + 1], shots[best[1]]
        issues.append(f"{a.get('id')}..{b.get('id')} ({a['start_s']:.1f}-{b['end_s']:.1f}s): {best[0]} shots in a row "
                      f'of about the same length')
    groups = {}
    for s, x in zip(shots, d):
        key = s.get('act') or s.get('chapter') or s.get('section')
        if key:
            groups.setdefault(str(key), []).append(x)
    avg = {k: round(sum(v) / len(v), 2) for k, v in groups.items()}
    if len(avg) >= 3 and max(avg.values()) <= acts_flat * min(avg.values()):
        issues.append('every act/chapter keeps the same pace (mean shot within 25 %)')
    return dict(out, cv=round(cv, 3), mean_s=round(mean, 2), longest_alike_run=best[0], act_mean_s=avg,
                issues=issues, count=len(issues), over_threshold=bool(issues))


def lint(video, width, height, fps, duration, shots, subtitles, faces=None, texts=(), geometry=None,
         line_max=18, measure_video=True, scene_loudness=False, variety=False):
    """Shots/subtitles carry start_s/end_s. Returns a gate dict (status PASS/FAIL, report_only flag)."""
    face_cut, text_face = check_faces(shots, faces, subtitles, list(texts), width, height, fps, geometry)
    checks = dict(face_cut=face_cut, text_on_face=text_face, subtitle_overflow=check_overflow(subtitles, width, height, geometry))
    rule = cap.lint([dict(text=s.get('text', '')) for s in subtitles if s.get('text', '').strip()], line_max)
    checks['subtitle_rules'] = dict(status='ADVISORY', issues=rule[:20], count=len(rule), line_max=line_max)
    checks['rhythm'] = check_rhythm(shots)
    if measure_video:
        checks.update(check_video(video, shots, duration))
    if scene_loudness:
        checks['scene_loudness'] = check_scene_loudness(video, shots)
    if variety:
        checks['variety'] = check_variety(shots)
    blocking = [k for k in ('face_cut', 'text_on_face', 'subtitle_overflow') if checks[k]['status'] == 'FAIL']
    flagged = [k for k, v in checks.items() if v.get('over_threshold') or (v['status'] == 'ADVISORY' and v.get('count'))]
    unmeasured = [k for k, v in checks.items() if v['status'] == 'NOT_MEASURED']
    return dict(status='FAIL' if blocking else 'PASS', review_state='DECIDED', report_only=not blocking,
                evidence=dict(blocking=blocking, flagged_report_only=flagged, not_measured=unmeasured,
                              thresholds=LINT, checks=checks))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--shots')
    ap.add_argument('--subtitles')
    ap.add_argument('--faces')
    ap.add_argument('--format', choices=['longform', 'shorts'], default='longform')
    ap.add_argument('--caption-box', help='JSON geometry {x,y,w,h,size,line_height,stroke,canvas}')
    ap.add_argument('--no-video', action='store_true', help='skip scene_check (static/repeats/pops)')
    ap.add_argument('--out')
    a = ap.parse_args()
    probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                       'stream=width,height,avg_frame_rate:format=duration', '-of', 'json', a.video],
                                      capture_output=True, check=True).stdout)
    v = probe['streams'][0]
    num, den = map(float, v['avg_frame_rate'].split('/'))
    fps, duration = num / den, float(probe['format']['duration'])

    def seconds(rows):
        out = []
        for r in rows:
            if 'start_s' in r:
                out.append(r)
            elif 'from_' in r:
                out.append(dict(r, start_s=r['from_'] / fps, end_s=r['to'] / fps))
            elif 'start_frame' in r:
                out.append(dict(r, start_s=r['start_frame'] / fps, end_s=r.get('end_frame', r['start_frame']) / fps))
            else:
                out.append(dict(r, start_s=float(r.get('start', r.get('from', 0))), end_s=float(r.get('end', r.get('to', 0)))))
        return out
    load = lambda p: json.loads(Path(p).read_text()) if p else []
    shots = load(a.shots)
    shots = shots.get('shots', []) if isinstance(shots, dict) else shots
    shots = [dict(s, id=str(s.get('id', i))) for i, s in enumerate(seconds(shots))]
    for s, nxt in zip(shots, shots[1:] + [None]):
        if s['end_s'] <= s['start_s']:
            s['end_s'] = nxt['start_s'] if nxt else duration
    subs = load(a.subtitles)
    subs = subs.get('captions', subs.get('subtitles', [])) if isinstance(subs, dict) else subs
    geometry = json.loads(a.caption_box) if a.caption_box else (LONGFORM_CAPTION if a.format == 'longform' else None)
    report = lint(a.video, int(v['width']), int(v['height']), fps, duration, shots, seconds(subs), load(a.faces),
                  geometry=geometry, line_max=18 if a.format == 'longform' else 16, measure_video=not a.no_video)
    text = json.dumps(report, ensure_ascii=False, indent=1)
    Path(a.out).write_text(text + '\n') if a.out else print(text)
    return 1 if report['status'] == 'FAIL' else 0


if __name__ == '__main__':
    sys.exit(main())
