"""Where viewers leave: audience-retention curve -> hook leak, steepest drops, middle slide,
with the line spoken at each drop.

Portions adapted from youtube-agent-skill (MIT, © 2026 UtilLayer)
  source: research/youtube-agent-skill/src/skills/yt-retention/retention.py (curve analysis, CSV loader)
          research/youtube-agent-skill/src/skills/yt-edit/deadair.py (SRT/VTT/whisper-json cue loader)
  Copyright (c) 2026 UtilLayer, Copyright (c) 2026 Jake Schincariol. MIT License: permission is hereby
  granted, free of charge, to any person obtaining a copy of this software and associated documentation
  files, to deal in the Software without restriction, subject to the condition that the copyright notice
  and this permission notice be included in all copies or substantial portions of the Software. THE
  SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. Full text: research/youtube-agent-skill/src/LICENSE.

Changes from upstream: the hook cutoff is an argument in seconds (Shorts use a 2-3 s window, long
form 30 s); rows can come straight from a YouTube Analytics API response (elapsedVideoTimeRatio,
audienceWatchRatio, relativeRetentionPerformance); watch ratios above 1.0 (Shorts loop rewatches)
are kept instead of being mistaken for a 0-1 export; the window used to attach the spoken line is an
argument; analysis is a library call with no printing.

  .venv/bin/python -m factory.lib.retention retention.csv --duration 27 --cutoff 2.5 --transcript subs.srt
"""
import argparse
import csv
import json
import re
import sys

SHORTS_CUTOFF_S = 2.5   # first-2-seconds swipe window, plus one ratio step of slack
SHORTS_END_S = 2.0      # '다음 사건도 맞혀 보세요' sign-off
LONG_CUTOFF_S = 30.0


# ---------- curve input ----------

def unit_of(header):
    h = header.casefold()
    if '%' in h or 'percent' in h or 'ratio' in h:
        return 'percent'
    if any(w in h for w in ('second', 'sec)', '(s)', 'time')):
        return 'seconds'
    return None


def clock(c):
    secs = 0.0
    for part in c.split(':'):
        secs = secs * 60 + float(part)
    return secs


def load_csv(path):
    """(position, percent still watching) rows and the position unit, from a Studio export."""
    rows, unit = [], None
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as fh:
        for r in csv.reader(fh):
            nums = []
            for c in r:
                c = c.strip().replace('%', '').replace(',', '')
                try:
                    nums.append(clock(c) if ':' in c else float(c))
                except ValueError:
                    nums.append(None)
            if any(':' in c for c in r[:1]) and unit is None:
                unit = 'seconds'
            vals = [n for n in nums if n is not None]
            if len(vals) >= 2:
                rows.append((vals[0], vals[1]))
            elif not rows and r and unit is None:
                unit = unit_of(r[0])
    if rows and max(x for x, _ in rows) <= 1.0 and max(y for _, y in rows) <= 1.5:
        rows = [(x * 100, y * 100) for x, y in rows]
        unit = 'percent'
    return rows, unit


def rows_from_api(resp):
    """Analytics API report -> ([(percent of video, percent watching)], {percent: relativeRetentionPerformance})."""
    names = [c['name'] for c in resp.get('columnHeaders', [])]
    ix = {n: i for i, n in enumerate(names)}
    if 'elapsedVideoTimeRatio' not in ix or 'audienceWatchRatio' not in ix:
        raise ValueError(f'unexpected columns {names}')
    rows, rel = [], {}
    for r in sorted(resp.get('rows', []), key=lambda r: r[ix['elapsedVideoTimeRatio']]):
        x = round(float(r[ix['elapsedVideoTimeRatio']]) * 100, 4)
        rows.append((x, float(r[ix['audienceWatchRatio']]) * 100))
        if 'relativeRetentionPerformance' in ix and r[ix['relativeRetentionPerformance']] is not None:
            rel[x] = round(float(r[ix['relativeRetentionPerformance']]), 3)
    return rows, rel


# ---------- transcript cues (SRT / VTT / whisper json) ----------

TAG = re.compile(r'<[^>]*>')
SOUND = re.compile(r'\[[^\]]*\]|\((?:music|applause|laughter|laughs|inaudible)\)', re.I)


def parse_ts(s):
    s = s.strip().replace(',', '.')
    p = s.split(':')
    return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2]) if len(p) == 3 else int(p[0]) * 60 + float(p[1])


def load_cues(path):
    """[(start_s, end_s, text)] from .srt/.vtt or whisper-style json ({segments:[{start,end,text}]}, also {asr:{...}})."""
    with open(path, encoding='utf-8-sig', errors='replace') as fh:
        raw = fh.read()
    if str(path).endswith('.json'):
        d = json.loads(raw)
        if isinstance(d, dict):
            d = d.get('asr', d)
            d = d.get('segments', [])
        segs = [(float(s['start']), float(s['end']), SOUND.sub('', s.get('text') or '').strip()) for s in d]
        return [s for s in segs if s[2]]
    cues, cur = [], None
    for line in raw.splitlines():
        m = re.match(r'\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)', line)
        if m:
            cur = [parse_ts(m.group(1)), parse_ts(m.group(2)), []]
            cues.append(cur)
        elif not line.strip():
            cur = None
        elif cur is not None:
            text = ' '.join(SOUND.sub('', TAG.sub('', line)).split())
            if text:
                cur[2].append(text)
    return [(a, b, ' '.join(t)) for a, b, t in cues if t]


def said_at(cues, t, window=0.5):
    """Text of the cues overlapping [t - window, t + window]; the cue that holds t comes first."""
    near = [c for c in cues if c[0] <= t + window and c[1] >= t - window]
    near.sort(key=lambda c: (not (c[0] <= t <= c[1]), c[0]))
    return ' / '.join(c[2] for c in near)[:160]


# ---------- analysis ----------

def analyse(rows, unit=None, dur=None, cutoff_s=LONG_CUTOFF_S, top=5, min_drop=0.8, rel=None, end_s=0.0):
    """Hook leak inside the first `cutoff_s` seconds, the `top` steepest drops (> min_drop points),
    and the mean loss rate after the cutoff. Positions in percent of the video need `dur` for seconds.
    Drops starting in the last `end_s` seconds (the sign-off; everyone leaves when it ends) are kept
    apart in `end_drop` so they do not crowd out the moments that can be fixed."""
    if len(rows) < 2:
        raise ValueError('need at least two curve points')
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    if unit not in (None, 'percent', 'seconds'):
        raise ValueError(f'unit must be percent or seconds, not {unit!r}')
    if unit is None and max(xs) <= 100.5 and (dur is None or dur <= 100.5):
        # Jakes J1 (2026-11-08): a header-less export of a video of 100 s or less cannot be told apart by its
        # numbers (seconds 0-60 look like percent 0-60); guessing percent gave a hook leak of 42 instead of 26.
        raise ValueError('position unit unknown: the CSV header names no unit and every position is <= 100; '
                         'pass --unit percent|seconds')
    pct_axis = unit == 'percent' if unit else True

    def at(x):
        return x / 100.0 * dur if (pct_axis and dur) else (None if pct_axis else x)

    start = ys[0] or 100.0
    cutoff = cutoff_s if not pct_axis else (cutoff_s / dur * 100 if dur else 10.0)
    hook_end = min((y for x, y in rows if x <= cutoff), default=start)
    drops = []
    for i in range(1, len(rows)):
        d = ys[i - 1] - ys[i]
        span = xs[i] - xs[i - 1] or 1
        drops.append((d / span, xs[i - 1], xs[i], d))
    drops.sort(reverse=True)
    tail = (100 - end_s / dur * 100) if (pct_axis and dur) else (None if pct_axis else xs[-1] - end_s)
    in_tail = [x for x in drops if end_s and tail is not None and x[1] >= tail - 1e-9]
    body = [x for x in drops if x not in in_tail]
    cliffs = []
    for _, a1, b1, d in body[:top]:
        if d <= min_drop:
            continue
        s = at(a1)
        c = dict(**{'from': round(a1, 2), 'to': round(b1, 2)}, lost=round(d, 2),
                 at_seconds=round(s, 2) if s is not None else None,
                 to_seconds=round(at(b1), 2) if s is not None else None)
        if rel and b1 in rel:
            c['relative_retention'] = rel[b1]
        cliffs.append(c)
    mid = [rate for rate, x0, _, _ in body if x0 > cutoff]
    slide = sum(mid) / len(mid) if mid else 0
    per = 'second' if not pct_axis else ('1% of the video' if not dur else f'1% of the video ({dur / 100:.2f}s)')
    return dict(points=len(rows), axis='percent' if pct_axis else 'seconds', start=round(start, 2),
                cutoff_s=cutoff_s, hook_leak=round(start - hook_end, 2), end=round(ys[-1], 2),
                cliffs=cliffs, end_drop=round(sum(x[3] for x in in_tail), 2), end_s=end_s,
                slide_per_unit=round(slide, 3), slide_unit=per)


def attach_lines(result, cues, window=0.5):
    for c in result['cliffs']:
        if c.get('at_seconds') is not None:
            # the drop happens between two points; the line under its midpoint is what viewers left on
            t = (c['at_seconds'] + c['to_seconds']) / 2
            c['said'] = said_at(cues, t, window)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('csv')
    p.add_argument('--duration', type=float)
    p.add_argument('--unit', choices=('percent', 'seconds'), help='position unit when the CSV header does not say')
    p.add_argument('--cutoff', type=float, default=LONG_CUTOFF_S, help=f'hook window seconds (Shorts {SHORTS_CUTOFF_S})')
    p.add_argument('--end', type=float, default=0.0, help='seconds of sign-off kept out of the drop list')
    p.add_argument('--transcript')
    p.add_argument('--window', type=float, default=0.5, help='seconds either side of a drop for the spoken line')
    a = p.parse_args(argv)
    rows, unit = load_csv(a.csv)
    out = analyse(rows, a.unit or unit, a.duration, a.cutoff, end_s=a.end)
    if a.transcript:
        attach_lines(out, load_cues(a.transcript), a.window)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
