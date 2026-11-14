#!/usr/bin/env python3
"""Place narration sentences on the 30 fps grid and build subtitles.

Rules: ACT bounds are locked; a cue's narration may run past its own cue only
inside the same ACT; Q28 ends with 18 frames of silence before Q29 (05:30).
Writes timing.json and subtitles.ko.srt / .vtt.
"""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
FPS = 30
ACT_OUT = {'A': 720, 'B': 1200, 'C': 2100, 'D': 4200, 'E': 5250, 'F': 6150, 'G': 8250, 'H': 9300, 'I': 9900, 'J': 10950, 'K': 13200, 'L': 14400}
LEAD = {'Q01': 18, 'Q14': 48, 'Q17': 50, 'Q32': 46, 'Q29': 30, 'Q05': 14}
SENT_GAP = 9      # 0.3 s between sentences in a cue
CUE_GAP = 12      # min 0.4 s when crossing a cue boundary
TAIL = 8          # keep this many frames clear before ACT out


def chunks(text, maxline=22):
    """Split a sentence into subtitle chunks of ≤2 lines."""
    parts = [p.strip() for p in re.split(r'(?<=[,.?])\s+', text) if p.strip()]
    out = []
    for p in parts:
        if len(p) <= maxline * 2 - 2:
            out.append(p)
        else:
            words = p.split(' ')
            cur = ''
            for w in words:
                if len(cur) + len(w) + 1 > maxline * 2 - 4 and cur:
                    out.append(cur.strip()); cur = w
                else:
                    cur = (cur + ' ' + w).strip()
            if cur:
                out.append(cur)
    # merge very short tails into previous
    merged = []
    for c in out:
        if merged and len(c) < 7 and len(merged[-1]) + len(c) < maxline * 2:
            merged[-1] = merged[-1] + ' ' + c
        else:
            merged.append(c)
    return [wrap(c, maxline) for c in merged]


def wrap(c, maxline):
    if len(c) <= maxline:
        return c
    mid = len(c) // 2
    sp = [i for i, ch in enumerate(c) if ch == ' ']
    if not sp:
        return c
    i = min(sp, key=lambda k: abs(k - mid))
    return c[:i] + '\n' + c[i + 1:]


def weight(s):
    return len(re.sub(r'\s', '', s)) + 3 * len(re.findall(r'[,.?]', s))


def tc(f):
    s = f / FPS
    return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    script = json.load(open(HERE / 'script.json'))
    idx = {x['id']: x for x in json.load(open(HERE / 'audio/na/index.json'))['items']}
    t = 0
    items, subs, report = [], [], []
    for c in script['cues']:
        cin, cout, act = c['in_frame'], c['out_frame_exclusive'], c['act']
        if not c['narration']:
            report.append((c['cue_id'], None, None, cout - cin, 0)); continue
        start = max(cin + LEAD.get(c['cue_id'], 8), t + CUE_GAP)
        first = start
        for i, s in enumerate(c['narration']):
            it = idx[f"{c['cue_id']}_{i+1}"]
            d = round(it['dur'] * FPS)
            if i:
                start = t + SENT_GAP
            end = start + d
            items.append(dict(id=it['id'], cue=c['cue_id'], act=act, start=start, end=end, file=it['file'], text=s))
            # subtitles: proportional to weighted characters
            ch = chunks(s)
            tot = sum(weight(x) for x in ch)
            acc = start
            for k, x in enumerate(ch):
                dd = round(d * weight(x) / tot) if k < len(ch) - 1 else end - acc
                subs.append(dict(from_=acc, to=acc + dd, text=x, cue=c['cue_id']))
                acc += dd
            t = end
        limit = ACT_OUT[act] - TAIL - (24 if c['cue_id'] == 'Q28' else 0)
        report.append((c['cue_id'], first, t, cout, limit))
        if t > limit:
            print(f"!! {c['cue_id']} narration ends {t} > ACT {act} limit {limit} (over by {t-limit}f)")
    # extend subtitle display to bridge tiny gaps (≤ 8f) for reading comfort, never across ACTs
    for a, b in zip(subs, subs[1:]):
        if 0 < b['from_'] - a['to'] <= 8:
            a['to'] = b['from_']
    json.dump(dict(fps=FPS, items=items, subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text'], cue=s['cue']) for s in subs]),
              open(HERE / 'timing.json', 'w'), ensure_ascii=False, indent=1)
    with open(HERE / 'subtitles.ko.srt', 'w') as f:
        for i, s in enumerate(subs, 1):
            f.write(f"{i}\n{tc(s['from_'])} --> {tc(s['to'])}\n{s['text']}\n\n")
    with open(HERE / 'subtitles.ko.vtt', 'w') as f:
        f.write('WEBVTT\nKind: captions\nLanguage: ko\n\n')
        for i, s in enumerate(subs, 1):
            f.write(f"{tc(s['from_']).replace(',', '.')} --> {tc(s['to']).replace(',', '.')}\n{s['text']}\n\n")
    print(f"{'cue':5}{'na_in':>7}{'na_out':>8}{'cue_out':>8}{'slack':>7}")
    for cid, a, b, cout, lim in report:
        if a is None:
            continue
        print(f"{cid:5}{a:7d}{b:8d}{cout:8d}{cout-b:7d}")
    total = sum(i['end'] - i['start'] for i in items) / FPS
    print('narration seconds', round(total, 1), '| subtitles', len(subs), '| max chunk chars', max(len(s['text'].replace('\n', '')) for s in subs))


if __name__ == '__main__':
    main()
