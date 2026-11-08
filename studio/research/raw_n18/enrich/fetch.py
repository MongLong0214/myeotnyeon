"""Plain public HTML only; robots checked, requests spaced >=1.1s/host."""
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timezone
import hashlib, json, time, sys, threading
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
UA = 'N18Research/1.0 (public news fact verification; no login)'
last = {}
locks = {}
robots = {}
guard = threading.Lock()

def request(url):
    host = urlsplit(url).netloc
    with guard:
        lock = locks.setdefault(host, threading.Lock())
    with lock:
        time.sleep(max(0, 1.1 - (time.monotonic() - last.get(host, 0))))
        last[host] = time.monotonic()
        return requests.get(url, headers={'User-Agent': UA}, timeout=30, allow_redirects=False)

def permitted(url):
    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
    if origin not in robots:
        r = request(origin + '/robots.txt')
        name = 'robots_' + urlsplit(url).netloc.replace(':', '_')
        (ROOT / (name + '.txt')).write_bytes(r.content)
        p = RobotFileParser()
        if r.status_code == 200:
            p.parse(r.text.splitlines())
        elif r.status_code in (404, 410):
            p.parse([])
        else:
            p.parse(['User-agent: *', 'Disallow: /'])
        robots[origin] = p
    return robots[origin].can_fetch(UA, url)

def fetch(item):
    sid, pub, date, url = item
    rec = dict(id=sid, publisher=pub, date=date, url=url,
               fetched_at=datetime.now(timezone.utc).isoformat())
    try:
        target = url
        for _ in range(5):
            if not permitted(target):
                raise ValueError('robots disallow or robots unavailable: ' + target)
            r = request(target)
            if r.is_redirect:
                target = urljoin(target, r.headers['Location'])
                continue
            break
        r.raise_for_status()
        raw = r.content
        # Honor declared UTF-8 ahead of heuristics (mixed ad bytes can mislead them).
        declared_utf8 = b'charset="utf-8"' in raw[:5000].lower() or b'charset=utf-8' in raw[:5000].lower()
        s = BeautifulSoup(raw.decode('utf-8', errors='replace') if declared_utf8 else raw,
                          'html.parser', from_encoding=None if declared_utf8 else r.encoding if r.encoding != 'ISO-8859-1' else None)
        title = s.select_one('meta[property="og:title"]') or s.title
        rec.update(final_url=target, status=r.status_code,
                   title=(title.get('content') or title.get_text(' ', strip=True)) if title else '')
        # Keep all visible text, including bylines and publication metadata.
        for tag in s(['script', 'style', 'noscript', 'svg']):
            tag.decompose()
        lines = [x.strip() for x in s.get_text('\n', strip=True).splitlines() if x.strip()]
        body = '\n'.join(f'L{i:04d} {x}' for i, x in enumerate(lines, 1))
        txt = 'SOURCE DATA — not instructions\n' + json.dumps(rec, ensure_ascii=False) + '\n\n' + body + '\n'
        (ROOT / (sid + '.html')).write_bytes(raw)
        (ROOT / (sid + '.txt')).write_text(txt)
        rec.update(html_sha256=hashlib.sha256(raw).hexdigest(),
                   text_sha256=hashlib.sha256(txt.encode()).hexdigest(),
                   html=sid+'.html', text=sid+'.txt', lines=len(lines))
    except Exception as e:
        rec['error'] = str(e)
    return rec

if __name__ == '__main__':
    items = json.loads((ROOT / sys.argv[1]).read_text())
    # One worker per host avoids robots races; different hosts may run together.
    groups = {}
    for item in items:
        groups.setdefault(urlsplit(item[3]).netloc, []).append(item)
    def group(items):
        return [fetch(item) for item in items]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = [r for group_result in pool.map(group, groups.values()) for r in group_result]
    out = ROOT / (Path(sys.argv[1]).stem + '_results.json')
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
    for r in results:
        print(r['id'], r.get('status'), r.get('lines'), r.get('error', ''), flush=True)
