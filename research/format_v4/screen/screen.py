"""Quick screen: list Shorts from channel /shorts tabs and Shorts searches (flat, metadata only, no media)."""
import json, subprocess, sys, concurrent.futures as cf, urllib.parse, pathlib
Y = str(pathlib.Path.home() / '.local/bin/yt-dlp')
OUT = pathlib.Path(__file__).parent

def run(src, n=30):
    if src.startswith('q:'):
        url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote_plus(src[2:]) + '&sp=EgIQCQ%3D%3D'
    elif src.startswith('http'):
        url = src
    elif src.startswith('UC'):
        url = f'https://www.youtube.com/channel/{src}/shorts'
    else:
        url = f'https://www.youtube.com/{src}/shorts'
    try:
        p = subprocess.run([Y, '--flat-playlist', '--dump-json', '--playlist-end', str(n), url], capture_output=True, text=True, timeout=150)
    except subprocess.TimeoutExpired:
        return src, [], 'timeout'
    rows = []
    for l in p.stdout.splitlines():
        try: d = json.loads(l)
        except Exception: continue
        rows.append(dict(id=d.get('id'), title=d.get('title'), views=d.get('view_count'), dur=d.get('duration'), channel=d.get('channel') or d.get('playlist_uploader'), channel_id=d.get('channel_id') or d.get('playlist_channel_id'), url=d.get('url')))
    return src, rows, p.stderr.strip().splitlines()[-1][:160] if p.returncode else ''

if __name__ == '__main__':
    srcs = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
    res = {}
    with cf.ThreadPoolExecutor(4) as ex:
        for src, rows, err in ex.map(run, srcs):
            res[src] = dict(rows=rows, err=err)
            print(f'{src[:60]:60s} n={len(rows):3d} {err}', flush=True)
    out = OUT / (pathlib.Path(sys.argv[1]).stem + '.json')
    json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
