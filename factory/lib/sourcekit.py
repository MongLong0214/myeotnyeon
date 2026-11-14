"""Find your way around a long primary source (a judgment, an indictment, a press release) with
line numbers a fact checker can cite.

Portions adapted from youtube-agent-skill (MIT, © 2026 UtilLayer)
  source: research/youtube-agent-skill/src/skills/yt-research/sourcekit.py
  Copyright (c) 2026 UtilLayer, Copyright (c) 2026 Jake Schincariol. MIT License: permission is hereby
  granted, free of charge, to any person obtaining a copy of this software and associated documentation
  files, to deal in the Software without restriction, subject to the condition that the copyright notice
  and this permission notice be included in all copies or substantial portions of the Software. THE
  SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. Full text: research/youtube-agent-skill/src/LICENSE.

Changes from upstream: Korean judgment headings (주문 / 이유 / 범죄사실 / 【…】 / 1. 가. numbering) are
recognised as sections; `find` can ignore spacing (Korean sources and scripts space words differently)
and returns the matched line's own text; the index is never written next to the source unless asked.

  .venv/bin/python -m factory.lib.sourcekit index judgment.txt
  .venv/bin/python -m factory.lib.sourcekit find  judgment.txt "박치기" [--nospace]
  .venv/bin/python -m factory.lib.sourcekit show  judgment.txt 120-140
  .venv/bin/python -m factory.lib.sourcekit show  judgment.txt "이유 > 범죄사실"
"""
import argparse
import json
import os
import re
import sys

# level 0: document parts; level 1: numbered / bracketed sub-headings
KO_TOP = r'(주\s*문|이\s*유|청\s*구\s*취\s*지|결\s*론)'
KO_SUB = r'(범\s*죄\s*사\s*실|증\s*거\s*의\s*요\s*지|법\s*령\s*의\s*적\s*용|양\s*형\s*의\s*이\s*유|판\s*단|공\s*소\s*사\s*실)'
DEFAULT = (r'^\s*(?:'
           r'(?P<en>(BOOK|PART|CHAPTER|CANTO|SECTION|ACT|SCENE|CHAP\.?)\b[ .]*([IVXLCDM]+|\d+|[A-Z]+)\b.*)'
           r'|(?P<ko0>[【\[]?\s*' + KO_TOP + r'\s*[】\]]?\s*)'
           r'|(?P<ko1>[【\[]?\s*' + KO_SUB + r'\s*[】\]]?\s*|【[^】]{1,30}】|\d{1,2}\.\s*\S.{0,40}|[가-하]\.\s*\S.{0,40})'
           r')$')
LEVEL0_EN = ('BOOK', 'PART')


def read(path):
    with open(path, encoding='utf-8-sig', errors='replace') as fh:
        return fh.read().splitlines()


def _level(m, s):
    g = m.groupdict()
    if g.get('ko0'):
        return 0
    if g.get('ko1'):
        return 1
    return 0 if s.split()[0].upper().rstrip('.') in LEVEL0_EN else 1


def index(lines, heading=None):
    """[{title, level, start, end, words}] with 1-based inclusive line numbers. A section ends where the
    next heading of the same or a higher level begins."""
    rx = re.compile(heading or DEFAULT, 0 if heading else re.I)
    found = []
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if s and len(s) < 90:
            m = rx.match(s)
            if m:
                found.append((n, s, _level(m, s)))
    nonblank = [n for n, l in enumerate(lines, 1) if l.strip()]
    nxt = {a: b for a, b in zip(nonblank, nonblank[1:])}
    starts = {n for n, _, _ in found}
    heads = []
    for n, s, level in found:
        # a heading followed straight by another sub-heading is a table-of-contents line, not a section
        if level == 1 and nxt.get(n) in starts and not heading:
            continue
        heads.append({'title': s, 'level': level, 'start': n})
    for i, h in enumerate(heads):
        end = len(lines)
        for g in heads[i + 1:]:
            if g['level'] <= h['level']:
                end = g['start'] - 1
                break
        h['end'] = end
        h['words'] = sum(len(l.split()) for l in lines[h['start'] - 1:end])
    return heads


def section_of(heads, n):
    inner = [h for h in heads if h['start'] <= n <= h['end']]
    return ' / '.join(h['title'] for h in sorted(inner, key=lambda h: h['level'])) or '(before the first heading)'


def load_index(path, heading=None):
    ix = os.path.splitext(path)[0] + '.index.json'
    if os.path.exists(ix) and not heading:
        with open(ix) as fh:
            return json.load(fh)
    return index(read(path), heading)


def _norm(s, nospace):
    s = s.lower()
    return re.sub(r'\s+', '', s) if nospace else re.sub(r'\s+', ' ', s).strip()


def find(path, phrase, context=1, limit=50, nospace=False):
    """Every line a phrase starts on (a phrase wrapped onto the next line counts on its first line)."""
    lines, heads = read(path), load_index(path)
    target = _norm(phrase, nospace)
    out = []
    for n in range(1, len(lines) + 1):
        here = _norm(lines[n - 1], nospace)
        window = _norm(' '.join(lines[n - 1:n + 1]), nospace)
        nxt_only = n < len(lines) and target in _norm(lines[n], nospace)
        if (target in here or (target in window and not nxt_only)) and not (out and out[-1]['line'] == n - 1):
            lo, hi = max(1, n - context), min(len(lines), n + context)
            out.append({'line': n, 'section': section_of(heads, n), 'match': lines[n - 1].strip(),
                        'text': [f'{k}: {lines[k - 1]}' for k in range(lo, hi + 1)]})
            if len(out) >= limit:
                break
    return out


def show(path, what):
    lines = read(path)
    m = re.match(r'^(\d+)-(\d+)$', what)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
    else:
        heads = load_index(path)
        parts = [_norm(x, True) for x in what.split('>')]
        hits = []
        for h in heads:
            if parts[-1] not in _norm(h['title'], True):
                continue
            path_titles = _norm(section_of(heads, h['start']), True)
            if all(x in path_titles for x in parts):
                hits.append(h)
        if not hits:
            raise LookupError(f'no section titled like {what!r}; run `index` and look at the titles')
        a, b = hits[0]['start'], hits[0]['end']
    return [f'{k}: {lines[k - 1]}' for k in range(a, min(b, len(lines)) + 1)]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('index'); a.add_argument('source'); a.add_argument('--heading')
    a.add_argument('--write', action='store_true', help='save <source>.index.json')
    b = sub.add_parser('find'); b.add_argument('source'); b.add_argument('phrase')
    b.add_argument('--context', type=int, default=1); b.add_argument('--nospace', action='store_true')
    c = sub.add_parser('show'); c.add_argument('source'); c.add_argument('what')
    args = p.parse_args(argv)
    if not os.path.exists(args.source):
        p.error(f'no such file: {args.source}')
    if args.cmd == 'index':
        heads = index(read(args.source), args.heading)
        if args.write:
            with open(os.path.splitext(args.source)[0] + '.index.json', 'w') as fh:
                json.dump(heads, fh, ensure_ascii=False, indent=1)
        out = heads
    elif args.cmd == 'find':
        out = find(args.source, args.phrase, args.context, nospace=args.nospace)
    else:
        try:
            out = show(args.source, args.what)
        except LookupError as e:
            sys.exit(str(e))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
