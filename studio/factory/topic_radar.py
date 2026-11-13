#!/usr/bin/env python3
"""Topic radar: real-search-demand topic selection for 몇년나옴 (court-case Shorts).

python3 factory/topic_radar.py scan --candidates FILE [--limit N]
python3 factory/topic_radar.py discover [--seeds S1,S2,...] [--days 90]
python3 factory/topic_radar.py report [--scan FILE] [--top 15] [--out FILE]

Extends factory/topic_score.py rather than duplicating it: reuses its Naver
client (owner-authorized keychain credentials, never printed), its PublicHTTP
(robots-respecting fetch with per-host delay), and its now()/read()/write()
helpers. Every new API response is cached under research/topic_radar/cache/.

Hard filters (checked before any paid-in-time API call, so excluded rows
never consume quota): sex crimes / child victims, cases without at least a
confirmed 1st-instance verdict, and cases we already published (checked
against upload/ledger.json video ids, factory.topic_score.OWN_IDS, and the
titles already uploaded to our own channel per the latest
channel/analytics/daily snapshot).

Score = a transparent weighted sum of five 0..1 normalized signals, each
min-max normalized within the batch being scanned:
  0.30 * datalab_calibrated   (Naver DataLab peak ratio / fixed anchor median)
  0.25 * youtube_demand       (median views-per-day of top YouTube results)
  0.20 * recency              (how close the verdict is to today)
  0.15 * news_count           (Naver news/blog/cafe index count, log-scaled)
  0.10 * autocomplete_present (1 if the keyword surfaces in YT autocomplete)
Missing signals are excluded from the weighted sum and the remaining weights
are renormalized to sum to 1; a row with zero available signals scores null.
This is a relative research aid, not a greenlight.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import re
import statistics as st
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parent

spec = importlib.util.spec_from_file_location('topic_score', HERE / 'topic_score.py')
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)

OUT = W / 'research/topic_radar'
CACHE = OUT / 'cache'
ANCHOR = '음주운전'  # fixed, high-volume, stable keyword shared by every DataLab call.

SEX_CHILD_BLOCKLIST = re.compile(
    r'성범죄|성폭행|성폭력|강간|몰카|불법촬영|아동학대|아동 성|미성년자 성|그루밍|'
    r'디지털\s*성범죄|청소년\s*성|아동\s*대상|'
    r'영아|신생아|여아|남아|생후\s*\d+\s*개월|'
    r'(딸|아들|아이|자녀)[가-힣\s]{0,10}(학대|사망|살해|폭행)|'
    r'(학대|사망|살해)[가-힣\s]{0,10}(딸|아들|영아|유아)',
    re.I,
)
DEFAULT_SEEDS = ['형량', '징역', '선고', '항소심', '대법원 확정', '집행유예', '무기징역',
                  '음주운전', '살인', '폭행', '사기', '스토킹']


def now():
    return ts.now()


def read_json(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else None


def write_json(p, value):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=1))


def cache_path(ns, key):
    h = hashlib.sha256(key.encode()).hexdigest()[:24]
    return CACHE / ns / (h + '.json')


def cached(ns, key, fetch):
    p = cache_path(ns, key)
    hit = read_json(p)
    if hit is not None:
        return hit['value']
    value = fetch()
    write_json(p, dict(key=key, observed_at=now(), value=value))
    return value


# ---- hard filters ---------------------------------------------------------

def norm(s):
    return ts.norm(s)


def own_channel_titles():
    """Titles already uploaded, from the most recent analytics snapshot. Cheap, no new call."""
    files = sorted((W / 'channel/analytics/daily').glob('*.json'))
    titles = []
    for f in reversed(files):
        d = read_json(f)
        vids = (d or {}).get('videos')
        if vids:
            titles = [norm(v.get('title', '')) for v in vids if v.get('title')]
            break
    return titles


def already_published(cand, titles):
    raw_tokens = (cand.get('keyword', '') + ' ' + cand.get('case_id', '')).split()
    tokens = [norm(tok) for tok in raw_tokens]
    tokens = [tok for tok in tokens if len(tok) >= 2]
    for t in titles:
        if not t:
            continue
        # Require a reasonably specific overlap, not a single short token.
        shared = [tok for tok in tokens if tok in t]
        if len(shared) >= 2:
            return True
    vid = cand.get('video_id')
    if vid and vid in ts.OWN_IDS:
        return True
    return False


def hard_exclude(cand, titles):
    text = ' '.join(str(cand.get(k, '')) for k in ('keyword', 'case_id', 'category', 'note'))
    if SEX_CHILD_BLOCKLIST.search(text):
        return 'sex_crime_or_child_victim_excluded'
    if not cand.get('verdict_date') and not cand.get('trial_stage'):
        return 'no_confirmed_verdict_or_trial_stage'
    if already_published(cand, titles):
        return 'already_published_on_own_channel'
    return None


# ---- signal 1: Naver DataLab (calibrated against a fixed anchor) ---------

def datalab_calibrated(client, keyword, window_days=120):
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=window_days)

    def fetch():
        body = dict(startDate=start.isoformat(), endDate=end.isoformat(), timeUnit='date',
                    keywordGroups=[dict(groupName='kw', keywords=[keyword]),
                                   dict(groupName='anchor', keywords=[ANCHOR])])
        return client.request('https://openapi.naver.com/v1/datalab/search', body)

    r = cached('naver_datalab', keyword, fetch)
    data = (r or {}).get('data') or {}
    results = data.get('results') or []
    if len(results) < 2:
        return None
    kw_points = results[0].get('data') or []
    anchor_points = results[1].get('data') or []
    peak = max((x['ratio'] for x in kw_points), default=None)
    anchor_median = st.median([x['ratio'] for x in anchor_points]) if anchor_points else None
    if peak is None or not anchor_median:
        return None
    return peak / anchor_median


# ---- signal 2: Naver news/blog/cafe index count ---------------------------

def news_count(client, keyword):
    def fetch():
        url = ('https://openapi.naver.com/v1/search/news.json?' +
               urllib.parse.urlencode(dict(query=keyword, display=100, start=1, sort='date')))
        return client.request(url)

    r = cached('naver_news', keyword, fetch)
    data = (r or {}).get('data') or {}
    total = data.get('total')
    items = data.get('items') or []
    recent_90 = 0
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    for it in items:
        pd = it.get('pubDate')
        if not pd:
            continue
        try:
            d = dt.datetime.strptime(pd, '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            continue
        if d >= cutoff:
            recent_90 += 1
    return dict(total=total, recent_90d_sample=recent_90)


# ---- signal 3: YouTube Data API demand (top-result views/day) ------------

class YouTubeAPI:
    def __init__(self):
        p = subprocess.run(['security', 'find-generic-password', '-s',
                             'KEYCHAIN_SERVICE_PREFIX.youtube.api_key', '-w'], capture_output=True, text=True)
        if p.returncode or not p.stdout.strip():
            raise RuntimeError('YouTube API key keychain item unavailable')
        self.key = p.stdout.strip()
        self.calls = 0

    def _get(self, url):
        self.calls += 1
        if self.calls > 80:
            raise RuntimeError('Local YouTube Data API quota safety cap reached')
        time.sleep(0.35)
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return dict(status=r.status, data=json.loads(r.read()))
        except urllib.error.HTTPError as e:
            return dict(status=e.code, data=None, error='API HTTP ' + str(e.code))
        except Exception as e:
            return dict(status='request_failed', data=None, error=type(e).__name__)

    def search_and_stats(self, keyword):
        search_url = ('https://www.googleapis.com/youtube/v3/search?' +
                       urllib.parse.urlencode(dict(part='snippet', q=keyword, type='video',
                                                    order='relevance', maxResults=5, key=self.key)))
        search = self._get(search_url)
        ids = [it['id']['videoId'] for it in (search.get('data') or {}).get('items', [])
               if it.get('id', {}).get('videoId')]
        if not ids:
            return dict(search=search, videos=[])
        stats_url = ('https://www.googleapis.com/youtube/v3/videos?' +
                     urllib.parse.urlencode(dict(part='snippet,statistics', id=','.join(ids), key=self.key)))
        stats = self._get(stats_url)
        videos = []
        for it in (stats.get('data') or {}).get('items', []):
            published = it.get('snippet', {}).get('publishedAt')
            views = it.get('statistics', {}).get('viewCount')
            if not published or views is None:
                continue
            pub = dt.datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
            days = max(1, (dt.datetime.now(dt.timezone.utc) - pub).days)
            videos.append(dict(id=it['id'], title=it.get('snippet', {}).get('title'),
                                published_at=published, view_count=int(views),
                                views_per_day=int(views) / days))
        return dict(search=search, videos=videos)


def youtube_demand(yt_api, keyword):
    def fetch():
        return yt_api.search_and_stats(keyword)

    r = cached('youtube_search', keyword, fetch)
    videos = (r or {}).get('videos') or []
    if not videos:
        return None, []
    return st.median(v['views_per_day'] for v in videos), videos


# ---- signal 4: YouTube autocomplete (do people type this?) ---------------

def autocomplete(keyword):
    def fetch():
        url = ('https://suggestqueries.google.com/complete/search?' +
               urllib.parse.urlencode(dict(client='firefox', ds='yt', q=keyword)))
        req = urllib.request.Request(url, headers={'User-Agent': ts.UA})
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode('utf-8', 'replace'))
                return data[1] if isinstance(data, list) and len(data) > 1 else []
        except Exception as e:
            return dict(error=type(e).__name__)

    return cached('autocomplete', keyword, fetch)


def autocomplete_present(keyword):
    sugg = autocomplete(keyword)
    if isinstance(sugg, dict) and sugg.get('error'):
        return None
    toks = [norm(t) for t in (sugg or [])]
    kw = norm(keyword)
    return 1.0 if any(kw in t or t in kw for t in toks) else 0.0


# ---- signal 5: Google Trends (optional, skip if blocked) -----------------

def google_trends(keyword):
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return None, 'pytrends not installed; optional secondary signal skipped'
    try:
        py = TrendReq(hl='ko-KR', tz=540)
        py.build_payload([keyword], geo='KR', timeframe='today 3-m')
        df = py.interest_over_time()
        if df is None or df.empty:
            return None, 'pytrends returned no data'
        return float(df[keyword].mean()), None
    except Exception as e:
        return None, 'pytrends blocked or failed: ' + type(e).__name__


# ---- recency ---------------------------------------------------------------

def recency_raw(verdict_date):
    if not verdict_date:
        return None
    try:
        d = dt.date.fromisoformat(verdict_date)
    except ValueError:
        return None
    days = (dt.date.today() - d).days
    if days < 0:
        return None
    return max(0.0, 1.0 - days / 180.0)


# ---- normalization + weighted score ---------------------------------------

WEIGHTS = dict(datalab=0.30, yt_demand=0.25, recency=0.20, news=0.15, autocomplete=0.10)


def minmax(values):
    present = [v for v in values if v is not None]
    if len(present) < 2 or max(present) == min(present):
        lo, hi = (0.0, 1.0) if not present else (present[0] - 1, present[0] + 1)
    else:
        lo, hi = min(present), max(present)
    return [None if v is None else (v - lo) / (hi - lo) for v in values]


def score_batch(rows):
    """rows: list of dicts with raw signal values. Adds normalized_* and score in place."""
    raw_news = [math.log1p(r['raw']['news_total']) if r['raw'].get('news_total') is not None else None
                for r in rows]
    fields = dict(datalab=[r['raw'].get('datalab') for r in rows],
                  yt_demand=[r['raw'].get('yt_demand') for r in rows],
                  recency=[r['raw'].get('recency') for r in rows],
                  news=raw_news,
                  autocomplete=[r['raw'].get('autocomplete') for r in rows])
    normalized = {k: minmax(v) for k, v in fields.items()}
    for i, r in enumerate(rows):
        r['normalized'] = {k: normalized[k][i] for k in fields}
        present = {k: v for k, v in r['normalized'].items() if v is not None}
        if not present:
            r['score'] = None
            continue
        w_sum = sum(WEIGHTS[k] for k in present)
        r['score'] = round(100 * sum(WEIGHTS[k] * v for k, v in present.items()) / w_sum, 2)
    return rows


# ---- scan -------------------------------------------------------------------

def scan(candidates_path, limit=None):
    candidates = read_json(candidates_path)
    if candidates is None:
        sys.exit('candidates file not found: ' + str(candidates_path))
    if limit:
        candidates = candidates[:limit]
    titles = own_channel_titles()
    naver = ts.Naver()
    yt_api = YouTubeAPI()
    rows = []
    for c in candidates:
        reason = hard_exclude(c, titles)
        row = dict(candidate=c, excluded=reason, raw={}, evidence={})
        if reason:
            rows.append(row)
            print('excluded', c.get('case_id') or c.get('keyword'), reason, flush=True)
            continue
        print('scan', c.get('case_id') or c.get('keyword'), flush=True)
        kw = c['keyword']
        trend_kw = c.get('trend_keyword', kw)
        row['raw']['datalab'] = datalab_calibrated(naver, trend_kw)
        nc = news_count(naver, kw)
        row['evidence']['news'] = nc
        row['raw']['news_total'] = nc.get('total')
        demand, videos = youtube_demand(yt_api, kw)
        row['raw']['yt_demand'] = demand
        row['evidence']['youtube_top'] = videos
        row['raw']['autocomplete'] = autocomplete_present(kw)
        row['raw']['recency'] = recency_raw(c.get('verdict_date'))
        gt_value, gt_note = google_trends(kw)
        row['evidence']['google_trends'] = dict(value=gt_value, note=gt_note)
        rows.append(row)
    scoreable = [r for r in rows if not r['excluded']]
    score_batch(scoreable)
    for r in rows:
        if r['excluded']:
            r['score'] = None
    # timestamped and never overwritten: two scans on the same day must not clobber each other
    out_path = _fresh(OUT / ('scan_' + dt.datetime.now().strftime('%Y-%m-%dT%H%M%S') + '.json'))
    write_json(out_path, dict(observed_at=now(), anchor=ANCHOR, weights=WEIGHTS, rows=rows))
    print('wrote', out_path, '· naver calls:', naver.calls, '· youtube calls:', yt_api.calls)
    return out_path


# ---- discover ---------------------------------------------------------------

def discover(seeds=None, days=90, out_path=None):
    seeds = seeds or DEFAULT_SEEDS
    naver = ts.Naver()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    known = {norm(c.get('query', c.get('name', ''))) for c in
             (read_json(W / 'research/topic_scores/candidates.json') or [])}
    found = {}
    for seed in seeds:
        print('discover seed', seed, flush=True)
        sugg = autocomplete(seed)
        if isinstance(sugg, list):
            for phrase in sugg:
                if SEX_CHILD_BLOCKLIST.search(phrase):
                    continue
                found.setdefault(phrase, dict(keyword=phrase, source='autocomplete', seed=seed))

        def fetch():
            url = ('https://openapi.naver.com/v1/search/news.json?' +
                   urllib.parse.urlencode(dict(query=seed, display=30, start=1, sort='date')))
            return naver.request(url)

        r = cached('naver_discover_news', seed, fetch)
        for it in ((r or {}).get('data') or {}).get('items', []):
            title = re.sub('<[^>]+>', '', it.get('title', ''))
            pd = it.get('pubDate')
            if not title or not pd:
                continue
            try:
                d = dt.datetime.strptime(pd, '%a, %d %b %Y %H:%M:%S %z')
            except ValueError:
                continue
            if d < cutoff:
                continue
            if SEX_CHILD_BLOCKLIST.search(title):
                continue
            key = title
            found.setdefault(key, dict(keyword=title, source='news_recent', seed=seed,
                                        pub_date=d.date().isoformat(), url=it.get('originallink') or it.get('link')))
    new_only = []
    for k, v in found.items():
        if norm(v['keyword']) in known or any(norm(v['keyword']) in nk or nk in norm(v['keyword']) for nk in known if nk):
            continue
        v['case_id'] = 'disc-' + hashlib.sha256(v['keyword'].encode()).hexdigest()[:8]
        v.setdefault('verdict_date', None)
        v.setdefault('trial_stage', None)
        new_only.append(v)
    out_path = out_path or (OUT / 'discovered_candidates.json')
    write_json(out_path, new_only)
    print('wrote', out_path, '·', len(new_only), 'new candidates (unmatched against existing candidates.json) ·',
          'naver calls:', naver.calls)
    print('NOTE: discovered rows need manual verdict_date/trial_stage confirmation before `scan` will score them',
          '(scan hard-excludes rows with neither field).')
    return out_path


# ---- report -----------------------------------------------------------------

def hook_line(row):
    c = row['candidate']
    if c.get('hook'):
        return c['hook']
    ev = row.get('evidence', {})
    top = (ev.get('youtube_top') or [None])[0]
    if top and top.get('title'):
        return top['title']
    return c.get('keyword', '')


def _fresh(path):
    """First non-existing variant of path (path, path-2, path-3, ...)."""
    path = Path(path)
    k = 2
    while path.exists():
        path = path.with_name(f'{path.stem.rsplit("-v", 1)[0]}-v{k}{path.suffix}')
        k += 1
    return path


def report(scan_path, top=15, out_path=None):
    doc = read_json(scan_path)
    if doc is None:
        sys.exit('scan file not found: ' + str(scan_path))
    rows = [r for r in doc['rows'] if not r['excluded'] and r['score'] is not None]
    rows.sort(key=lambda r: r['score'], reverse=True)
    rows = rows[:top]
    lines = [
        '# 토픽 레이더 — 상대 수요 순위',
        '',
        f"측정: {doc['observed_at']} · 앵커: {doc['anchor']} · 가중치: {json.dumps(doc['weights'], ensure_ascii=False)}",
        '',
        '점수는 배치 내 상대 비교용이다. 선정은 사실 원문·형량 질문 적합성을 함께 확인한다.',
        '',
        '|순위|키워드|점수|데이터랩(앵커 대비)|YT 수요(조회/일)|뉴스 건수|자동완성|선고·심급|한줄 훅|',
        '|---:|---|---:|---:|---:|---:|---:|---|---|',
    ]
    for i, r in enumerate(rows, 1):
        c = r['candidate']
        raw = r['raw']
        lines.append('|{}|{}|{}|{}|{}|{}|{}|{}|{}|'.format(
            i, c.get('keyword', ''), r['score'],
            round(raw['datalab'], 2) if raw.get('datalab') is not None else '미측정',
            round(raw['yt_demand']) if raw.get('yt_demand') is not None else '미측정',
            raw['news_total'] if raw.get('news_total') is not None else '미측정',
            '있음' if raw.get('autocomplete') else ('없음' if raw.get('autocomplete') == 0 else '미측정'),
            c.get('trial_stage') or c.get('verdict_date') or '미확인',
            hook_line(r),
        ))
    excluded = [r for r in doc['rows'] if r['excluded']]
    if excluded:
        lines += ['', '## 제외', '', '|키워드|제외 이유|', '|---|---|']
        for r in excluded:
            lines.append('|{}|{}|'.format(r['candidate'].get('keyword', ''), r['excluded']))
    text = '\n'.join(lines) + '\n'
    out_path = out_path or _fresh(OUT / ('REPORT_' + dt.datetime.now().strftime('%Y-%m-%dT%H%M%S') + '.md'))
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(text)
        print('wrote', out_path)
    except Exception as e:
        print('could not write report file (' + type(e).__name__ + '); printing instead:')
        print(text)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    sp = sub.add_parser('scan')
    sp.add_argument('--candidates', required=True)
    sp.add_argument('--limit', type=int)
    dp = sub.add_parser('discover')
    dp.add_argument('--seeds')
    dp.add_argument('--days', type=int, default=90)
    dp.add_argument('--out')
    rp = sub.add_parser('report')
    rp.add_argument('--scan', required=True)
    rp.add_argument('--top', type=int, default=15)
    rp.add_argument('--out')
    args = p.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    if args.action == 'scan':
        scan(Path(args.candidates), args.limit)
    elif args.action == 'discover':
        seeds = args.seeds.split(',') if args.seeds else None
        discover(seeds, args.days, Path(args.out) if args.out else None)
    elif args.action == 'report':
        report(Path(args.scan), args.top, Path(args.out) if args.out else None)


if __name__ == '__main__':
    main()
