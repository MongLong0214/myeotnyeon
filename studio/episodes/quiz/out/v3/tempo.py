#!/usr/bin/env python3
"""Structure gates from public/<id>/render.json (owner H2/H3 2026-10-26):
  duration 25–35 s (hard 22–40) · reveal (answer on screen) at ≥ 75 % of runtime · a panel change at least every
  1.5 s (45 frames). Panel changes counted: cue cuts, actors/props/tags/stamps/bursts/sfx appearing or leaving,
  lever/hand moves, zoom beats, weigh cards and badges, reveal hit/stamp/steps/tags, outro pops, header answer swap.
  Captions are not counted. usage: tempo.py q011 [...]"""
import json, pathlib, sys
PUB = pathlib.Path(__file__).resolve().parents[4] / 'production' / 'compositor' / 'public'
GAP = 45


def events(doc):
    ev = []
    for c in doc['cues']:
        f0, a, p, s1 = c['from'], c['a'], c['p'], c['a'].get('s1', 0)
        add = lambda t, what: ev.append((round(f0 + t), f"{c['id']} {what}")) if 0 <= t < c['dur'] else None
        add(0, 'cut ' + c['scene'])
        rel = lambda v: s1 + v
        if c['scene'] == 'incident':
            for k in ('actors', 'props', 'tags', 'stamps', 'sfx'):
                for i, q in enumerate(p.get(k, [])):
                    if 'at' in q and q['at'] > -50:
                        add(rel(q['at']), f'{k}[{i}] in')
                    if 'until' in q:
                        add(rel(q['until']), f'{k}[{i}] out')
                    if 'liftAt' in q:
                        add(rel(q['liftAt'][0]), f'{k}[{i}] lift')
            for k in ('stamp', 'burst'):
                if k in p:
                    add(rel(p[k].get('at', 10)), k)
            if p.get('set') == 'cabin':
                for k in ('leverAt', 'handAt'):
                    if isinstance(p.get(k), (int, float)) and p[k] > -50:
                        add(rel(p[k]), k)
            if p.get('set') == 'bigtext':
                add(rel(p.get('bigAt', 0)), 'bigtext')
            if p.get('set') == 'money':
                add(rel(p.get('moneyAt', 4)), 'money')
        if c['scene'] == 'weigh':
            add(2, 'title')
            k0 = p.get('cardFrom', 2)
            for i in range(len(p['cards'])):
                t = a.get(f's{k0 + i}')
                if t is not None:
                    add(t, f'card{i}'); add(t + 14, f'badge{i}')
        if c['scene'] == 'reveal':
            add(s1 + 2, 'hit'); add(s1 + 8, 'stamp')
            for st in p.get('steps', []):
                if f"s{st['s']}" in a:
                    add(a[f"s{st['s']}"], f"step s{st['s']}")
            for i, g in enumerate(p.get('tags', [])):
                add(rel(g.get('at', 30)), f'tag{i}')
        if c['scene'] == 'outro':
            add(s1, 'card')
            if p.get('staged'):
                add(s1 + p.get('logoAt', 14), 'logo')
        for b in p.get('punch', []) or []:
            add(rel(b), 'zoom')
        if c['scene'] in ('reason', 'quiz', 'remorse', 'hurt', 'record', 'confiscate', 'cling', 'push2'):
            add(s1 + 4, c['scene'] + ' anim')
    return sorted(set(ev))


def check(q):
    doc = json.load(open(PUB / q / 'render.json'))
    n = doc['durationInFrames']; ev = events(doc)
    times = sorted({t for t, _ in ev} | {n})
    gaps = [(b - a, a, b) for a, b in zip(times, times[1:])]
    worst = max(gaps)
    rv = next(c for c in doc['cues'] if c['scene'] == 'reveal')
    hit = rv['from'] + rv['a']['s1'] + 2
    out = dict(episode=q, frames=n, seconds=round(n / 30, 2), duration_ok=25 * 30 <= n <= 35 * 30, duration_hard_ok=22 * 30 <= n <= 40 * 30,
               reveal_frame=hit, reveal_ratio=round(hit / n, 3), reveal_ok=hit / n >= 0.75,
               max_gap_frames=worst[0], max_gap_at=[worst[1], worst[2]], tempo_ok=worst[0] <= GAP,
               changes_per_10s=round(len(times) / (n / 300), 1),
               over_gap=[(g, a, b) for g, a, b in gaps if g > GAP])
    return out, ev


if __name__ == '__main__':
    for q in [a for a in sys.argv[1:] if not a.startswith('-')]:
        out, ev = check(q)
        print(json.dumps(out, ensure_ascii=False))
        if '-v' in sys.argv:
            for t, w in ev:
                print('   ', t, w)
