"""Evidence fetch without downloading video or audio: metadata JSON, auto/manual subtitles (vtt),
storyboard sprite images (sb0, fallback sb1) and the thumbnail. Then a timestamped contact sheet.
usage: fetch.py ID [ID ...]"""
import json, subprocess, sys, pathlib, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont
Y = str(pathlib.Path.home() / '.local/bin/yt-dlp')
R = pathlib.Path(__file__).resolve().parents[1]
UA = {'User-Agent': 'Mozilla/5.0'}

def get(url, path):
    if path.exists() and path.stat().st_size > 0: return
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        path.write_bytes(r.read())

def fetch(vid):
    mdir = R / 'meta'; fdir = R / 'frames' / vid; sdir = R / 'subs'
    for d in (mdir, fdir, sdir): d.mkdir(parents=True, exist_ok=True)
    mp = mdir / f'{vid}.json'
    if not mp.exists():
        p = subprocess.run([Y, '--skip-download', '--dump-json', f'https://www.youtube.com/watch?v={vid}'], capture_output=True, text=True, timeout=180)
        if p.returncode: return vid, 'meta-fail ' + p.stderr.strip()[-200:]
        mp.write_text(p.stdout)
    d = json.loads(mp.read_text())
    # subtitles (text only)
    subprocess.run([Y, '--skip-download', '--write-subs', '--write-auto-subs', '--sub-langs', 'ko,en,ko-orig,en-orig', '--sub-format', 'vtt',
                    '-o', str(sdir / '%(id)s.%(ext)s'), f'https://www.youtube.com/watch?v={vid}'], capture_output=True, text=True, timeout=180)
    sb = {f['format_id']: f for f in d.get('formats', []) if f['format_id'].startswith('sb')}
    f = sb.get('sb0') or sb.get('sb1')
    tiles = []
    if f:
        t0 = 0.0
        for i, fr in enumerate(f.get('fragments', [])):
            ip = fdir / f"{f['format_id']}_{i:02d}.jpg"
            get(fr['url'], ip)
            n = f['rows'] * f['columns']; dur = fr.get('duration') or 0
            tiles.append((ip, t0, dur, n)); t0 += dur
    th = max((t for t in d.get('thumbnails', []) if t.get('url', '').endswith(('.jpg', '.webp')) and t.get('width')), key=lambda t: t['width'] * t['height'], default=None)
    if th:
        try: get(th['url'], fdir / ('thumb' + pathlib.Path(th['url'].split('?')[0]).suffix))
        except Exception as e: pass
    for name in ('oardefault.jpg', 'oar2.jpg', 'frame0.jpg'):
        try: get(f'https://i.ytimg.com/vi/{vid}/{name}', fdir / f'thumb_{name}')
        except Exception: pass
    if f: sheet(vid, f, tiles, d.get('duration') or 0)
    return vid, f"ok sb={f['format_id'] if f else None} {f['width'] if f else ''}x{f['height'] if f else ''} frames={sum(t[3] for t in tiles)} dur={d.get('duration')}"

def sheet(vid, f, tiles, total, cols=10, scale=2):
    w, h = f['width'], f['height']
    cells = []
    for ip, t0, dur, n in tiles:
        im = Image.open(ip)
        per = dur / n if n else 0
        for k in range(n):
            t = t0 + k * per
            if t > total + 0.01: break
            r, c = divmod(k, f['columns'])
            box = (c * w, r * h, c * w + w, r * h + h)
            if box[2] > im.width or box[3] > im.height: continue
            cells.append((t, im.crop(box)))
    if not cells: return
    W, H = w * scale, h * scale
    rows = (len(cells) + cols - 1) // cols
    out = Image.new('RGB', (cols * W, rows * (H + 18)), (255, 255, 255))
    dr = ImageDraw.Draw(out)
    try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    except Exception: font = ImageFont.load_default()
    for i, (t, c) in enumerate(cells):
        r, cc = divmod(i, cols)
        out.paste(c.resize((W, H), Image.LANCZOS), (cc * W, r * (H + 18) + 18))
        dr.text((cc * W + 3, r * (H + 18) + 1), f'{t:5.1f}s', fill=(200, 0, 0), font=font)
    out.save(R / 'frames' / vid / 'sheet.jpg', quality=88)

if __name__ == '__main__':
    with cf.ThreadPoolExecutor(4) as ex:
        for vid, msg in ex.map(fetch, sys.argv[1:]):
            print(vid, msg, flush=True)
