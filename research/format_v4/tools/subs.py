"""Parse YouTube vtt (manual or ASR) -> clean cues; report narration pace and opening lines.
Pace = Hangul syllables (ko) or words (en) over the span between first and last cue (incl. pauses)."""
import re, json, sys, pathlib
R = pathlib.Path(__file__).resolve().parents[1]
def ts(s):
    h, m, x = s.split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
def parse(p):
    txt = p.read_text(errors='ignore'); cues = []
    for blk in re.split(r'\n\n+', txt):
        m = re.search(r'(\d\d:\d\d:\d\d\.\d+) --> (\d\d:\d\d:\d\d\.\d+)', blk)
        if not m: continue
        body = blk[m.end():].strip().split('\n')
        lines = [re.sub(r'<[^>]+>', '', l).strip() for l in body if l.strip()]
        cues.append([ts(m.group(1)), ts(m.group(2)), lines])
    # ASR rolling captions: keep only lines not already seen in the previous cue
    out = []; prev = []
    for a, b, lines in cues:
        new = [l for l in lines if l and l not in prev]
        if new: out.append((a, b, ' '.join(new)))
        prev = lines
    return out
def pick(vid, lang):
    meta = json.load(open(R / 'meta' / f'{vid}.json'))
    manual = list((meta.get('subtitles') or {}).keys())
    vl = (meta.get('language') or lang or '')[:2]
    for cand in ([f'{vid}.{vl}.vtt'] if vl in [m[:2] for m in manual] else []) + [f'{vid}.{vl}-orig.vtt', f'{vid}.{vl}.vtt', f'{vid}.ko-orig.vtt', f'{vid}.en-orig.vtt', f'{vid}.ko.vtt', f'{vid}.en.vtt']:
        p = R / 'subs' / cand
        if p.exists(): return p, vl, ('manual' if any(cand.split('.')[1] == m for m in manual) else 'asr')
    return None, vl, None
def stats(vid):
    p, vl, kind = pick(vid, None)
    if not p: return dict(id=vid, subs=None)
    cues = parse(p)
    if not cues: return dict(id=vid, subs=p.name, kind=kind, n=0)
    text = ' '.join(c[2] for c in cues)
    span = cues[-1][1] - cues[0][0]
    ko = len(re.findall(r'[가-힣]', text)); en = len(re.findall(r"[A-Za-z']+", text))
    unit = 'syl/s' if ko > en else 'words/s'
    rate = (ko if ko > en else en) / span if span else 0
    hook = re.sub(r"align:start position:0% ?", "", " ".join(c[2] for c in cues if c[0] < 3.0))[:160]
    last = cues[-1][2][:120]
    return dict(id=vid, subs=p.name, kind=kind, first_cue=round(cues[0][0], 2), span=round(span, 1), rate=round(rate, 2), unit=unit, hook=hook, last=last)
if __name__ == '__main__':
    for v in sys.argv[1:]:
        print(json.dumps(stats(v), ensure_ascii=False))
