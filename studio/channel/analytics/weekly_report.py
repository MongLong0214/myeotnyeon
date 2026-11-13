"""Weekly Shorts report: regenerates the core tables from the files the daily jobs already write.

  .venv/bin/python channel/analytics/weekly_report.py            # tables from the newest files, to stdout
  .venv/bin/python channel/analytics/weekly_report.py --pull     # first pull extra_<today>.json (read-only API)
  .venv/bin/python channel/analytics/weekly_report.py --out channel/analytics/weekly_<date>.md

Inputs (newest of each):
  daily/api_*.json    api_pull.py: per_video, traffic, daily, shorts_swipe
  daily/extra_*.json  --pull: videos (Data API), per_video_day, per_video_traffic, age_gender, search_detail, comments
  retention/*.json    retention_pull.py: audienceWatchRatio curves
  ../../upload/ledger.json and retention qids map video ids to qNNN.

--pull uses the keychain items api_pull.py uses (KEYCHAIN_SERVICE_PREFIX.youtube.oauth_client_json,
KEYCHAIN_SERVICE_PREFIX.youtube.oauth_refresh_token) and, for public comment text only, KEYCHAIN_SERVICE_PREFIX.youtube.api_key.
Secrets are never printed or written. Analytics data lags 2-3 days; the last days are incomplete.
"""
import argparse
import datetime
import glob
import json
import re
import statistics as st
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly', 'https://www.googleapis.com/auth/youtube.readonly']


def kc(service):
    return subprocess.check_output(['security', 'find-generic-password', '-s', service, '-w'],
                                   stderr=subprocess.DEVNULL).decode().strip()


def redact(s):
    return re.sub(r'(ya29\.[\w.-]+|1//[\w.-]+|GOCSPX-[\w-]+|AIza[\w-]+|[\w-]{40,})', '<redacted>', str(s))


def pull(start='2026-10-20'):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.loads(kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_client_json'))
    cfg = cfg.get('installed') or cfg.get('web')
    creds = Credentials(None, refresh_token=kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_refresh_token'), token_uri=cfg['token_uri'],
                        client_id=cfg['client_id'], client_secret=cfg['client_secret'], scopes=SCOPES)
    ya = build('youtubeAnalytics', 'v2', credentials=creds, cache_discovery=False)
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    end = datetime.date.today().isoformat()

    def q(**kw):
        try:
            return ya.reports().query(ids='channel==MINE', startDate=start, endDate=end, **kw).execute()
        except Exception as e:  # noqa: BLE001 - recorded verbatim, redacted
            return {'error': redact(e)[:400]}

    out = {}
    ch = yt.channels().list(part='contentDetails,statistics', mine=True).execute()['items'][0]
    out['channel_stats'] = ch['statistics']
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part='contentDetails', playlistId=ch['contentDetails']['relatedPlaylists']['uploads'],
                                    maxResults=50, pageToken=tok).execute()
        ids += [i['contentDetails']['videoId'] for i in r['items']]
        tok = r.get('nextPageToken')
        if not tok:
            break
    vids = []
    for i in range(0, len(ids), 50):
        vids += yt.videos().list(part='snippet,statistics,contentDetails,status', id=','.join(ids[i:i + 50])).execute()['items']
    out['videos'] = [dict(id=v['id'], title=v['snippet']['title'], publishedAt=v['snippet']['publishedAt'],
                          privacy=v['status']['privacyStatus'], duration=v['contentDetails']['duration'],
                          stats=v['statistics']) for v in vids]
    pub = [v['id'] for v in vids if v['status']['privacyStatus'] == 'public']
    out['per_video_day'], out['per_video_traffic'] = {}, {}
    for vid in pub:  # dimensions=day,video is not a supported report; one query per video
        out['per_video_day'][vid] = q(metrics='views,engagedViews,likes,subscribersGained', dimensions='day',
                                      filters=f'video=={vid}', sort='day')
        out['per_video_traffic'][vid] = q(metrics='views', dimensions='insightTrafficSourceType', filters=f'video=={vid}')
    out['search_detail'] = q(metrics='views', dimensions='insightTrafficSourceDetail',
                             filters='insightTrafficSourceType==YT_SEARCH', sort='-views', maxResults=25)
    out['age_gender'] = q(metrics='viewerPercentage', dimensions='ageGroup,gender', sort='gender,ageGroup')
    out['device'] = q(metrics='views', dimensions='deviceType')
    out['country'] = q(metrics='views', dimensions='country', sort='-views', maxResults=10)
    # OAuth scope youtube.readonly cannot list commentThreads (403); public comments via the Data API key.
    cm = {}
    try:
        ytk = build('youtube', 'v3', developerKey=kc('KEYCHAIN_SERVICE_PREFIX.youtube.api_key'), cache_discovery=False)
        for vid in pub:
            try:
                r = ytk.commentThreads().list(part='snippet', videoId=vid, maxResults=100, textFormat='plainText').execute()
                cm[vid] = [dict(text=s['textDisplay'][:200], likes=s['likeCount'], at=s['publishedAt'],
                                author_is_channel=s.get('authorChannelId', {}).get('value') == ch['id'],
                                replies=i['snippet']['totalReplyCount'])
                           for i in r['items'] for s in [i['snippet']['topLevelComment']['snippet']]]
            except Exception as e:  # noqa: BLE001
                cm[vid] = {'error': redact(e)[:200]}
    except Exception as e:  # noqa: BLE001
        cm = {'error': redact(e)[:200]}
    out['comments'] = cm
    p = HERE / 'daily' / f'extra_{end}.json'
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return p


def newest(pattern):
    files = sorted(glob.glob(str(HERE / pattern)))
    return (Path(files[-1]), json.loads(Path(files[-1]).read_text())) if files else (None, None)


def table(rep):
    rows = rep.get('rows', []) if isinstance(rep, dict) else []
    cols = [c['name'] for c in rep.get('columnHeaders', [])] if isinstance(rep, dict) else []
    return [dict(zip(cols, r)) for r in rows]


def qid_map():
    m = {}
    led = ROOT / 'upload' / 'ledger.json'
    if led.exists():
        for e in json.loads(led.read_text()).get('entries', []):
            for k in ('video_id', 'replacement_video_id'):
                if e.get(k):
                    m[e[k]] = e['qid']
    for f in glob.glob(str(HERE / 'retention' / '*.json')):
        r = json.loads(Path(f).read_text())
        if r.get('qid'):
            m[r['video_id']] = r['qid']
    return m


def secs(iso):
    m = re.fullmatch(r'PT(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m else None


def pt_day(iso):
    """Analytics days are US Pacific; map a UTC publishedAt to its Pacific calendar day."""
    if not iso:
        return ''
    from zoneinfo import ZoneInfo
    t = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return t.astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def per_k(a, b):
    return round(1000 * a / b, 1) if b else None


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    if len(x) < 3:
        return None
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 2) if den else None


def md(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)]
    out += ['| ' + ' | '.join('' if c is None else str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def curve_at(raw_rows, frac):
    best = min(raw_rows, key=lambda r: abs(r[0] - frac))
    return best[1]


def build(api, extra):
    qm = qid_map()
    lines = []
    pv = {r['video']: r for r in table(api['per_video'])}
    sw = {r['video']: r for r in table(api['shorts_swipe'])}
    meta = {v['id']: v for v in (extra or {}).get('videos', [])}
    shorts = [v for v in pv if (secs(meta.get(v, {}).get('duration')) or 0) <= 180 or v not in meta]

    # 1. per-video core table
    rows, ev, vw = [], [], []
    for v in sorted(shorts, key=lambda v: -pv[v]['views']):
        p, s = pv[v], sw.get(v, {})
        er = pct(s.get('engagedViews', 0), s.get('views', 0))
        rows.append([qm.get(v, '?'), v, pt_day(meta.get(v, {}).get('publishedAt')), secs(meta.get(v, {}).get('duration')),
                     p['views'], s.get('engagedViews'), er, p['averageViewDuration'], round(p['averageViewPercentage'], 1),
                     per_k(p['likes'], p['views']), p['comments'], p['shares'],
                     p['subscribersGained'] - p['subscribersLost']])
        if er is not None:
            ev.append(er)
            vw.append(p['views'])
    tot_v = sum(pv[v]['views'] for v in shorts)
    tot = {k: sum(pv[v][k] for v in shorts) for k in ('likes', 'comments', 'shares', 'subscribersGained', 'subscribersLost')}
    lines += ['## 1. 영상별 핵심 지표', '',
              md(['q', 'video', '공개(PT)', '길이s', '조회', 'engaged', 'engaged%', '평균시청s', '평균시청%',
                  '좋아요/1k', '댓글', '공유', '순구독'], rows), '',
              f"합계 조회 {tot_v} · 좋아요 {tot['likes']} ({per_k(tot['likes'], tot_v)}/1k) · 댓글 {tot['comments']} "
              f"({per_k(tot['comments'], tot_v)}/1k) · 공유 {tot['shares']} ({per_k(tot['shares'], tot_v)}/1k) · "
              f"순구독 {tot['subscribersGained'] - tot['subscribersLost']} "
              f"({per_k(tot['subscribersGained'] - tot['subscribersLost'], tot_v)}/1k)", '',
              f"engaged% 중앙값 {st.median(ev) if ev else None} · engaged% 대 조회 Spearman ρ = {spearman(ev, vw)} (n={len(ev)})", '']

    # 2. day-by-day curves
    if extra and extra.get('per_video_day'):
        maxd = 7
        rows = []
        for v in sorted(shorts, key=lambda v: (meta.get(v, {}).get('publishedAt') or '')):
            d = table(extra['per_video_day'].get(v, {}))
            pubd = pt_day(meta.get(v, {}).get('publishedAt'))
            d = [r for r in d if r['day'] >= pubd]
            if not d:
                continue
            cum = sum(r['views'] for r in d)
            days = [r['views'] for r in d[:maxd + 1]]
            peak = max(d, key=lambda r: r['views'])
            rows.append([qm.get(v, '?'), pubd, *(days + [''] * (maxd + 1 - len(days))), cum, pct(peak['views'], cum),
                         pct(peak['engagedViews'], peak['views']), pct(cum - peak['views'], cum)])
        last_day = max((r['day'] for v in extra['per_video_day'].values() for r in table(v) if r.get('views')), default='?')
        lines += ['## 2. 공개일 기준 일별 조회 (D0 = 공개일, 미국 태평양시 일자)', '',
                  md(['q', '공개', *[f'D{i}' for i in range(maxd + 1)], '누적', '최대일 비중%', '최대일 engaged%', '최대일 외 꼬리%'], rows), '',
                  f'API 일별 데이터 마지막 집계일: {last_day} (그 뒤는 지연으로 비어 있음). publishedAt 은 업로드 시각이라 비공개→공개 전환이 늦은 영상(q003)은 D0 가 비어 있다.', '']

    # 3. retention
    rrows = []
    for f in sorted(glob.glob(str(HERE / 'retention' / '*.json'))):
        r = json.loads(Path(f).read_text())
        a, raw = r.get('analysis'), (r.get('raw') or {}).get('rows')
        if not a or not raw:
            continue
        start = a['start']
        p50 = round(100 * curve_at(raw, 0.5), 1)
        rel_end = raw[-1][2] if len(raw[-1]) > 2 else None
        rrows.append([r.get('qid'), r['video_id'], r.get('duration_s'), start, a['hook_leak'],
                      round(a['hook_leak'] / start * 100, 1), p50, a['end'], round(a['end'] / start * 100, 1),
                      a['end_drop'], round(100 * st.mean(x[1] for x in raw), 1), round(rel_end, 2) if rel_end else None])
    rrows.sort(key=lambda x: x[0] or '')
    lines += ['## 3. 유지율 곡선 (audienceWatchRatio x100)', '',
              md(['q', 'video', '길이s', '시작', '2.5초 손실pt', '손실/시작%', '50%지점', '끝', '끝/시작%', '마지막2초pt',
                  '곡선평균', '끝 rel'], rrows), '',
              '시작 >100 은 재시청(루프) 포함. 끝/시작% 는 루프 부풀림을 덜어낸 상대 유지. rel 0.5 = 비슷한 길이 영상 평균.', '']

    # 4. traffic & audience
    tr = table(api['traffic'])
    ttot = sum(r['views'] for r in tr)
    lines += ['## 4. 유입·시청자', '', md(['유입', '조회', '%'], [[r['insightTrafficSourceType'], r['views'], pct(r['views'], ttot)] for r in tr]), '']
    if extra:
        ag = table(extra.get('age_gender', {}))
        if ag:
            g = {}
            for r in ag:
                g[r['gender']] = round(g.get(r['gender'], 0) + r['viewerPercentage'], 1)
            lines += [md(['연령', '성별', '%'], [[r['ageGroup'], r['gender'], r['viewerPercentage']] for r in ag]), '',
                      f'성별 합계: {g}', '']
        sd = table(extra.get('search_detail', {}))
        if sd:
            lines += ['검색어 상위: ' + ', '.join(f"{r['insightTrafficSourceDetail']}({r['views']})" for r in sd[:12]), '']
        cm = extra.get('comments', {})
        if isinstance(cm, dict) and 'error' not in cm:
            viewer = [(v, c) for v, cs in cm.items() if isinstance(cs, list) for c in cs if not c['author_is_channel']]
            own = sum(1 for cs in cm.values() if isinstance(cs, list) for c in cs if c['author_is_channel'])
            lines += [f'댓글(공개 최상위): 시청자 {len(viewer)}개, 채널 고정 {own}개', '']
            lines += [f"- {qm.get(v, v)}: {c['text'][:60].replace(chr(10), ' ')}" for v, c in viewer]
            lines.append('')

    # 5. channel daily
    dl = table(api['daily'])
    lines += ['## 5. 채널 일별', '', md(['일', '조회', '구독+', '구독-'],
                                     [[r['day'], r['views'], r['subscribersGained'], r['subscribersLost']] for r in dl if r['views']]), '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pull', action='store_true', help='pull extra_<today>.json first (read-only API)')
    ap.add_argument('--out', help='write markdown here instead of stdout')
    a = ap.parse_args()
    if a.pull:
        print('pulled', pull())
    pa, api = newest('daily/api_*.json')
    pe, extra = newest('daily/extra_*.json')
    if not api:
        raise SystemExit('no daily/api_*.json')
    head = f'# 주간 Shorts 표 — {datetime.date.today().isoformat()}\n\n소스: {pa.name}' + (f', {pe.name}' if pe else '') + '\n\n'
    text = head + build(api, extra)
    if a.out:
        Path(a.out).write_text(text)
        print(a.out)
    else:
        print(text)


if __name__ == '__main__':
    main()
