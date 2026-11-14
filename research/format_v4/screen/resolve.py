import json, subprocess, sys, urllib.parse, pathlib, concurrent.futures as cf
Y = str(pathlib.Path.home() / '.local/bin/yt-dlp')
def res(q):
    url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote_plus(q) + '&sp=EgIQAg%3D%3D'
    p = subprocess.run([Y, '--flat-playlist', '--dump-json', '--playlist-end', '3', url], capture_output=True, text=True, timeout=120)
    out = []
    for l in p.stdout.splitlines():
        d = json.loads(l); out.append((d.get('channel') or d.get('title'), d.get('id'), d.get('channel_follower_count'), d.get('url')))
    return q, out
qs = [l.strip() for l in open(sys.argv[1]) if l.strip()]
with cf.ThreadPoolExecutor(4) as ex:
    for q, out in ex.map(res, qs):
        print('##', q)
        for o in out: print('   ', o)
