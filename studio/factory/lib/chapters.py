"""Chapter boundaries for a long-form video from its SRT: pauses between cues plus a change of
vocabulary across them, checked against YouTube's chapter rules. Titles are left blank for a person
or agent to write; this module never invents them.

Portions adapted from youtube-agent-skill (MIT, © 2026 UtilLayer)
  source: research/youtube-agent-skill/src/skills/yt-chapters/chapters.py
  Copyright (c) 2026 UtilLayer, Copyright (c) 2026 Jake Schincariol. MIT License: permission is hereby
  granted, free of charge, to any person obtaining a copy of this software and associated documentation
  files, to deal in the Software without restriction, subject to the condition that the copyright notice
  and this permission notice be included in all copies or substantial portions of the Software. THE
  SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. Full text: research/youtube-agent-skill/src/LICENSE.

Changes from upstream: Korean tokens (particles stripped, two-syllable minimum) instead of an English
stop list; no draft titles; `validate` reports each broken rule (00:00 start, >= 3 chapters, each
>= 10 s, ascending) and also accepts hand-written chapter lists.

  .venv/bin/python -m factory.lib.chapters episodes/x/subtitles.srt [--target 6]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import load_cues  # noqa: E402  (one SRT/VTT/json parser)

MIN_S = 10.0
MIN_COUNT = 3
PARTICLES = ('으로', '에서', '에게', '까지', '부터', '은', '는', '이', '가', '을', '를', '로', '에', '의', '와', '과', '도', '만')
STOP = set('그리고 그런데 하지만 그래서 그러나 이렇게 저렇게 그렇게 정말 진짜 바로 이제 다시 그냥 지금 여기 거기 '
           '있습니다 했습니다 됩니다 합니다 있었습니다 했죠 있죠 있어요 했어요 이건 그건 저건 이것 그것 무엇 어떻게 '
           'the a an of to and is was in on for with that this'.split())


def keywords(text):
    out = set()
    for w in re.findall(r'[^\W\d_]+', text.lower()):
        for p in PARTICLES:
            if w.endswith(p) and len(w) - len(p) >= 2:
                w = w[:-len(p)]
                break
        if len(w) >= 2 and w not in STOP:
            # Korean inflects at the end; the first two syllables keep 해킹범/해킹을/해킹한 together
            out.add(w[:2] if re.match(r'[가-힣]', w) else w)
    return out


def mmss(t):
    t = int(t)
    h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'


def boundaries(cues, target=7, min_s=MIN_S, context=12):
    """Pick up to `target` chapter starts (00:00 included). Each candidate is a cue start scored by
    the pause before it (x1.6) and the Jaccard vocabulary shift across it (x3.2)."""
    if not cues:
        return []
    dur = cues[-1][1]
    cand = []
    for i in range(1, len(cues)):
        gap = max(0.0, cues[i][0] - cues[i - 1][1])
        kb = keywords(' '.join(c[2] for c in cues[max(0, i - context):i]))
        ka = keywords(' '.join(c[2] for c in cues[i:i + context]))
        shift = 1 - len(kb & ka) / len(kb | ka) if (kb | ka) else 0
        cand.append((round(gap * 1.6 + shift * 3.2, 4), cues[i][0], i, round(gap, 2), round(shift, 2)))
    cand.sort(key=lambda c: (-c[0], c[1]))
    picked = [dict(start=0.0, cue=0, pause=None, shift=None)]
    for score, t, i, gap, shift in cand:
        if len(picked) >= target:
            break
        if all(abs(t - p['start']) >= min_s for p in picked) and dur - t >= min_s:
            picked.append(dict(start=round(t, 2), cue=i, pause=gap, shift=shift, score=score))
    picked.sort(key=lambda p: p['start'])
    out = []
    for n, p in enumerate(picked):
        end = picked[n + 1]['start'] if n + 1 < len(picked) else dur
        first = cues[p['cue']][2]
        out.append(dict(start=p['start'], label=mmss(p['start']), seconds=round(end - p['start'], 2),
                        title='', first_line=first[:60], pause=p['pause'], shift=p['shift']))
    return out


def validate(chapters, duration=None, min_s=MIN_S):
    """YouTube chapter rules -> list of problems (empty = valid). Chapters need `start` seconds;
    `seconds` is derived from the next start (or `duration`) when missing."""
    errs = []
    starts = [float(c['start']) for c in chapters]
    if len(chapters) < MIN_COUNT:
        errs.append(f'needs at least {MIN_COUNT} chapters (have {len(chapters)})')
    if not starts or starts[0] != 0:
        errs.append('first chapter must start at 00:00')
    if any(b <= a for a, b in zip(starts, starts[1:])):
        errs.append('chapter starts must be in ascending order')
    for n, c in enumerate(chapters):
        end = starts[n + 1] if n + 1 < len(starts) else duration
        length = c.get('seconds', None if end is None else end - starts[n])
        if length is not None and length < min_s:
            errs.append(f'chapter {n + 1} at {mmss(starts[n])} is {length:.1f} s (min {min_s:.0f} s)')
    return errs


def description_block(chapters):
    """Paste-ready lines; refuses while any title is still blank."""
    blank = [c['label'] for c in chapters if not c.get('title', '').strip()]
    if blank:
        raise ValueError(f'chapter titles still blank at {", ".join(blank)}; write them first')
    return '\n'.join(f"{c['label']} {c['title'].strip()}" for c in chapters)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('transcript')
    p.add_argument('--target', type=int, default=7, help='chapters to aim for, 00:00 included')
    a = p.parse_args(argv)
    cues = load_cues(a.transcript)
    ch = boundaries(cues, a.target)
    print(json.dumps(dict(chapters=ch, errors=validate(ch, cues[-1][1] if cues else None),
                          note='titles are blank by design: write them, then description_block()'),
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
