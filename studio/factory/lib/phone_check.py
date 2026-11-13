"""Phone-size review sheet: every frame scaled to 360 px wide, as seen on a phone. A tool, not a gate.

  .venv/bin/python factory/lib/phone_check.py VIDEO [--subtitles captions.json] [--out DIR]
        [--first 3] [--every 0.2] [--columns 4]

Samples the first `--first` seconds every `--every` seconds, plus one frame just after every subtitle change
(cue start + 2 frames). Subtitles: long-form {start,end,text} seconds, Shorts {from_,to,text} frames, or
{start_s,end_s,text}. Writes phone_sheet_NN.jpg pages and phone_sheet.json (frame list) into --out.
Idea from ClaudeAnimationBase (MIT) render.mjs --strip / the "360 px phone test"; no code copied.
Look at it at 100 %: if a subtitle, face or prop does not read here, it does not read on a phone.
"""
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

LABEL_FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'


def probe(video):
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,avg_frame_rate,nb_frames:format=duration', '-of', 'json', str(video)],
                       capture_output=True, check=True)
    d = json.loads(p.stdout)
    v = d['streams'][0]
    a, b = map(float, v['avg_frame_rate'].split('/'))
    fps = a / b
    frames = int(v.get('nb_frames') or round(float(d['format']['duration']) * fps))
    return fps, frames, int(v['width']), int(v['height'])


def cue_starts(subtitles, fps):
    out = []
    for s in subtitles:
        if 'from_' in s:
            t = s['from_'] / fps
        else:
            t = float(s.get('start_s', s.get('start', s.get('from', 0))))
        out.append((t, s.get('text', '')))
    return sorted(out)


def plan(fps, frames, subtitles=(), first=3.0, every=0.2):
    """[(frame, reason)] sorted, unique."""
    rows = {}
    t = 0.0
    while t < first - 1e-9:
        n = round(t * fps)
        if n < frames:
            rows.setdefault(n, 'first %.1fs' % t)
        t += every
    for t, text in cue_starts(subtitles, fps):
        n = min(frames - 1, round(t * fps) + 2)
        if n >= 0:
            rows[n] = 'cue: ' + text.replace('\n', ' / ')
    return sorted(rows.items())


def extract(video, numbers, out, width=360):
    """One decode pass at phone width; keep only the planned frames (f_000000.png)."""
    _, _, vw, vh = probe(video)
    h = round(vh * width / vw / 2) * 2
    tmp = out / 'phone_frames'
    tmp.mkdir(parents=True, exist_ok=True)
    want, paths = set(numbers), {}
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'scale={width}:{h}:flags=area',
                             '-fps_mode', 'passthrough', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
                            stdout=subprocess.PIPE)
    try:
        n, size = 0, width * h * 3
        while len(paths) < len(want):
            raw = proc.stdout.read(size)
            if len(raw) < size:
                break
            if n in want:
                q = tmp / f'f_{n:06}.png'
                Image.frombytes('RGB', (width, h), raw).save(q)
                paths[n] = q
            n += 1
    finally:
        proc.kill()
        proc.wait()
        proc.stdout.close()
    if len(paths) != len(want):
        raise RuntimeError(f'decoded {len(paths)} of {len(want)} requested frames')
    return [paths[n] for n in numbers]


def sheet(video, out, subtitles=(), first=3.0, every=0.2, columns=4, per_page=24, width=360):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fps, frames, vw, vh = probe(video)
    rows = plan(fps, frames, subtitles, first, every)
    paths = extract(video, [n for n, _ in rows], out, width)
    th = round(vh * width / vw / 2) * 2
    font = ImageFont.truetype(LABEL_FONT, 13)
    label_h, gap = 36, 8
    pages = []
    for k in range(0, len(rows), per_page):
        chunk = list(zip(rows[k:k + per_page], paths[k:k + per_page]))
        nrows = (len(chunk) + columns - 1) // columns
        page = Image.new('RGB', (columns * (width + gap) + gap, nrows * (th + label_h + gap) + gap), (24, 24, 28))
        draw = ImageDraw.Draw(page)
        for i, ((n, why), p) in enumerate(chunk):
            x, y = gap + i % columns * (width + gap), gap + i // columns * (th + label_h + gap)
            page.paste(Image.open(p).convert('RGB'), (x, y + label_h))
            draw.text((x + 2, y + 2), f'f{n}  {n / fps:.2f}s', fill='white', font=font)
            draw.text((x + 2, y + 18), why[:30], fill=(250, 210, 90), font=font)
        p = out / f'phone_sheet_{k // per_page:02}.jpg'
        page.save(p, quality=90)
        pages.append(str(p))
    (out / 'phone_sheet.json').write_text(json.dumps(dict(video=str(video), width=width, fps=fps, pages=pages,
                                                          frames=[dict(frame=n, reason=w) for n, w in rows]),
                                                     ensure_ascii=False, indent=1) + '\n')
    return pages


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--subtitles')
    ap.add_argument('--out')
    ap.add_argument('--first', type=float, default=3.0)
    ap.add_argument('--every', type=float, default=0.2)
    ap.add_argument('--columns', type=int, default=4)
    a = ap.parse_args()
    subs = json.loads(Path(a.subtitles).read_text()) if a.subtitles else []
    if isinstance(subs, dict):
        subs = subs.get('captions', subs.get('subtitles', []))
    out = Path(a.out) if a.out else Path(a.video).with_name(Path(a.video).stem + '_phone')
    for p in sheet(a.video, out, subs, a.first, a.every, a.columns):
        print(p)


if __name__ == '__main__':
    main()
