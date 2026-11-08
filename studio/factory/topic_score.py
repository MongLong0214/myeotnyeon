#!/usr/bin/env python3
"""Free topic research with public YouTube/news and owner-authorized Naver APIs.

python3 factory/topic_score.py collect [--slug SLUG] [--limit N]
python3 factory/topic_score.py naver
python3 factory/topic_score.py sources
python3 factory/topic_score.py enrich [--slug SLUG] [--limit N]
python3 factory/topic_score.py shorts
python3 factory/topic_score.py gap [--comments]
python3 factory/topic_score.py rank

The manifest is research/topic_scores/candidates.json. Only the naver command
reads the two owner-authorized keychain items; it never persists them. The gap
command adds sourced sentencing facts and optional bounded public comment samples.
Missing observations stay null. A score is a relative editorial aid, not a pass line.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import statistics as st
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

W = Path(__file__).resolve().parents[1]
OUT = W / 'research/topic_scores'
UA = 'TopicScore/1.0 (public-interest research; keyless; no login)'
OWN_IDS = {'ozKvg2XFA0Y','-g-ubPCtVGw','zwgKEbvbxsU','oxZUrYF8Chg',
           'g6IHdEbtJoE','1niGnkTw6BA','IKjz8gGErMk','Z2bRWBdK7bQ',
           'E4zk6oCIbjA','_AYRzLJaFLo','0eo5o8u5EMM','P33g73Z2c0g',
           '2Bs_T3OZFlk','MYjtxd25BhU','EomEdxcqfsU'}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

class Naver:
    """Owner-authorized free APIs. Secrets never leave request headers/memory."""
    def __init__(self):
        self.headers={}
        for name, header in [('client_id','X-Naver-Client-Id'),('client_secret','X-Naver-Client-Secret')]:
            p=subprocess.run(['security','find-generic-password','-s','KEYCHAIN_SERVICE_PREFIX.naver.'+name,'-w'],capture_output=True,text=True)
            if p.returncode or not p.stdout.strip():raise RuntimeError('Naver keychain item unavailable: '+name)
            self.headers[header]=p.stdout.strip()
        self.calls=0

    def request(self,url,body=None):
        self.calls+=1
        if self.calls>600:raise RuntimeError('Local free-quota safety cap reached')
        time.sleep(1.2)
        headers=dict(self.headers)
        if body is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,headers=headers)
        result=dict(url=url,query=body,observed_at=now())
        try:
            with urllib.request.urlopen(req,timeout=25) as r:
                return dict(result,status=r.status,data=json.loads(r.read()))
        except urllib.error.HTTPError as e:
            return dict(result,status=e.code,data=None,error='API HTTP '+str(e.code))
        except Exception as e:
            return dict(result,status='request_failed',data=None,error=type(e).__name__)

def naver_collect(c,client):
    p=OUT/(c['slug']+'.json');d=read(p) if p.exists() else dict(candidate=c,schema_version=1)
    if c.get('hard_exclusion'):return
    n=d.setdefault('naver',{})
    n.setdefault('search',{})
    for kind in ['news','blog','cafearticle']:
        if kind in n['search']:continue
        query=c.get('news_query',c['query'])
        url='https://openapi.naver.com/v1/search/'+kind+'.json?'+urllib.parse.urlencode(dict(query=query,display=100,start=1,sort='sim'))
        r=client.request(url);r['query']=query;n['search'][kind]=r
        save_fields(p,dict(candidate=c,naver=n))
    if not n.get('datalab'):
        end=dt.date.today()-dt.timedelta(days=1)
        # Common anchor makes within-call relative ratios interpretable across cases.
        # DataLab omits no-volume dates; omitted days remain missing, never zero-filled.
        terms=c.get('trend_keywords') or [c['query']]
        body=dict(startDate='2023-11-06',endDate=end.isoformat(),timeUnit='date',
            keywordGroups=[dict(groupName=c['slug'],keywords=terms[:20]),dict(groupName='anchor',keywords=['집행유예'])])
        n['datalab']=client.request('https://openapi.naver.com/v1/datalab/search',body)
        save_fields(p,dict(candidate=c,naver=n))
    n['note']='Search total is an index count, not people or searches. DataLab ratio is normalized, not absolute volume. Missing days are not filled.'
    save_fields(p,dict(candidate=c,naver=n))

def naver_context(c,client):
    p=OUT/(c['slug']+'.json');d=read(p);n=d.setdefault('naver',{})
    recent=n.get('datalab',{});recent_data=recent.get('data') or {}
    contexts=[]
    for kind,key in [('incident','incident_date'),('disclosure','disclosure_date'),('judgment','sentence_date')]:
        if kind=='judgment' and c.get('sentence_date_kind') in ('confirmation_report_date','confirmation_report_date (not necessarily actual judgment day)'):
            kind='judgment_confirmation_report'
        value=c.get(key)
        if not value:
            contexts.append(dict(kind=kind,date=None,measurement=None,reason='Exact event date not verified.'));continue
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(value)):
            contexts.append(dict(kind=kind,date=value,measurement=None,reason='Only year/month verified; no day invented.'));continue
        day=dt.date.fromisoformat(value);start=day-dt.timedelta(days=14);end=min(day+dt.timedelta(days=14),dt.date.today()-dt.timedelta(days=1))
        if end<start or start<dt.date(2016,1,1):
            contexts.append(dict(kind=kind,date=value,measurement=None,reason='Outside DataLab historical availability (from 2016).'));continue
        if recent_data and str(start)>=recent_data.get('startDate','9999') and str(end)<=recent_data.get('endDate','0000'):
            response=recent;scope='slice of common recent window'
        else:
            body=dict(startDate=str(start),endDate=str(end),timeUnit='date',keywordGroups=[dict(groupName=c['slug'],keywords=c.get('trend_keywords') or [c['query']]),dict(groupName='anchor',keywords=['집행유예'])])
            ck=hashlib.sha256(json.dumps(body,ensure_ascii=False).encode()).hexdigest()[:16];cache=OUT/'trend_windows'/(ck+'.json')
            response=read(cache) if cache.exists() else client.request('https://openapi.naver.com/v1/datalab/search',body)
            if not cache.exists():write(cache,response)
            scope='separate event-window API request'
        results=(response.get('data') or {}).get('results',[])
        points=[x for x in (results[0].get('data',[]) if results else []) if str(start)<=x['period']<=str(end)]
        anchors=[x['ratio'] for x in (results[1].get('data',[]) if len(results)>1 else []) if str(start)<=x['period']<=str(end)]
        peak=max((x['ratio'] for x in points),default=None);median=st.median(anchors) if anchors else None
        contexts.append(dict(kind=kind,date=value,start=str(start),end=str(end),scope=scope,
            observed_at=response.get('observed_at'),query=response.get('query'),status=response.get('status'),
            peak_ratio=peak,anchor_median=median,peak_over_anchor_median=peak/median if peak is not None and median else None,
            returned_days=len(points),points=points,reason=None if points else 'No returned case series; absent days remain missing.'))
    n['event_windows']=contexts;save_fields(p,dict(naver=n))

def fetch_sources(d,http):
    c=d['candidate'];slug=c['slug'];news=(d.get('naver',{}).get('search',{}).get('news',{}).get('data') or {}).get('items',[])
    matched=[x for x in news if matches(html.unescape(re.sub('<[^>]+>','',x['title'])),c)]
    d.setdefault('news',{})
    if d['news'] is None:d['news']={}
    d['news'].update(article_count=len({x.get('originallink') or x['link'] for x in matched}),
        article_count_scope='Unique case-title-matched original URLs in first ≤100 Naver results; not total case coverage.',
        query=c.get('news_query',c['query']),observed_at=d.get('naver',{}).get('search',{}).get('news',{}).get('observed_at'),matched_articles=matched,
        api_index_total=(d.get('naver',{}).get('search',{}).get('news',{}).get('data') or {}).get('total'))
    originals=d.setdefault('original_sources',[])
    candidates=[s for s in c.get('sources',[]) if isinstance(s,dict) and s.get('url')]
    candidates += [dict(url=x.get('originallink') or x['link'],title=html.unescape(re.sub('<[^>]+>','',x['title'])),date=x.get('pubDate')) for x in matched if re.search(r'선고|확정|징역|벌금|무죄|집유|집행유예',x['title']) and '구형' not in x['title']]
    known={x['url'] for x in originals};hosts=set()
    for src in candidates:
        u=src['url'];host=urllib.parse.urlsplit(u).netloc
        if host in hosts or 'naver.com' in host or u in known:continue
        hosts.add(host)
        p=OUT/'sources'/(slug+'_'+hashlib.sha256(u.encode()).hexdigest()[:10]+'.json')
        result=read(p) if p.exists() else http.get(u)
        if not p.exists():write(p,result)
        body=result.get('body') or ''
        plain=html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>',' ',body)))
        plain=re.sub(r'\s+',' ',plain)
        # No parser automatically turns a scraped sentence into a verified fact.
        record=dict(src,status=result.get('status'),observed_at=result['observed_at'],sha256=result.get('sha256'),raw_path=str(p.relative_to(W)),
            sentence_excerpts=[plain[max(0,m.start()-80):m.end()+160] for m in list(re.finditer(r'징역\s*\d|금고\s*\d|벌금\s*\d|무죄|집행유예',plain))[:8]],
            public_comments=None,public_reactions=None,
            missing_reason='No unambiguous public comment/reaction total parsed; dynamic counters not inferred.')
        originals.append(record);known.add(u)
        save_fields(OUT/(slug+'.json'),dict(news=d['news'],original_sources=d['original_sources']))
        if len(hosts)>=3:break
    save_fields(OUT/(slug+'.json'),dict(news=d['news'],original_sources=d['original_sources']))
    refresh_public_counters(read(OUT/(slug+'.json')))

def public_counters(plain):
    comments=None;evidence=None
    for m in re.finditer(r'댓글\s*([0-9][0-9,]*)\b|([0-9][0-9,]*)\s*개의\s*댓글',plain):
        if re.match(r'\s*/\s*\d',plain[m.end():]):continue  # textarea character limit
        comments=int((m[1] or m[2]).replace(',',''))
        evidence=re.sub(r'\s+',' ',plain[max(0,m.start()-40):m.end()+50]);break
    reactions={}
    for m in re.finditer(r'(추천해요|좋아요|감동이에요|화나요|슬퍼요)\s*([0-9][0-9,]*)\b',plain):
        reactions[m[1]]=int(m[2].replace(',',''))
    return comments,reactions or None,evidence

def refresh_public_counters(d):
    signals=[]
    for src in d.get('original_sources',[]):
        p=W/src['raw_path']
        raw=read(p).get('body') or ''
        plain=html.unescape(re.sub('<[^>]+>',' ',re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>',' ',raw)))
        comments,reactions,evidence=public_counters(plain)
        src.update(public_comments=comments,public_reactions=reactions,counter_evidence=evidence)
        if comments is not None or reactions is not None:
            src['missing_reason']=None
            signals.append(dict(kind='news_public_reaction',url=src['url'],query=d['candidate']['query'],observed_at=src['observed_at'],comments=comments,reactions=reactions,evidence=evidence))
    save_fields(OUT/(d['candidate']['slug']+'.json'),dict(original_sources=d.get('original_sources',[]),independent_signals=signals))

def read(p):
    return json.loads(Path(p).read_text())

def write(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp.' + str(os.getpid()))
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(p)

def save_fields(p,fields):
    """Long collection stages preserve fields written by another collection stage."""
    with (OUT/'.write.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        d=read(p) if Path(p).exists() else {}
        d.update(fields);write(p,d)
        fcntl.flock(lock,fcntl.LOCK_UN)

def norm(s):
    return re.sub(r'[^가-힣a-z0-9]', '', (s or '').lower())

def measured_number(value):
    if isinstance(value,(int,float)) and not isinstance(value,bool):return value
    if isinstance(value,str) and re.fullmatch(r'\d[\d,]*',value.strip()):return int(value.replace(',',''))
    return None

def matches(title, candidate):
    t = norm(title)
    return bool(candidate.get('match_groups')) and all(
        any(norm(term) in t for term in group) for group in candidate['match_groups']
    ) and not any(norm(term) in t for term in candidate.get('negative_terms', []))

def yt(args, timeout=75):
    """Use requested binary; recover from its obsolete Homebrew shebang."""
    binary = '/opt/homebrew/bin/yt-dlp'
    runner = [binary]
    if Path(binary).exists():
        first = Path(binary).read_text().splitlines()[0]
        if first.startswith('#!') and not Path(first[2:]).exists():
            runner = [sys.executable, binary]
    cmd = runner + ['--ignore-config', '--socket-timeout', '15', '--retries', '0'] + args
    started = now()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        data = json.loads(p.stdout) if p.stdout.strip() else None
        return dict(observed_at=started, command=cmd, returncode=p.returncode,
                    data=data, error=p.stderr[-2500:] or None)
    except (subprocess.TimeoutExpired, ValueError, OSError) as e:
        return dict(observed_at=started, command=cmd, data=None, error=str(e))

class PublicHTTP:
    """Per-host delay, robots cache, fail closed on an unreadable robots file."""
    def __init__(self, delay=2.0):
        self.delay, self.last, self.robots = delay, {}, {}

    def raw(self, url, method='GET'):
        host = urllib.parse.urlsplit(url).netloc
        time.sleep(max(0, self.last.get(host, 0) + self.delay - time.monotonic()))
        self.last[host] = time.monotonic()
        req = urllib.request.Request(url, headers={'User-Agent': UA},method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, r.read(), r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get('Location',url)

    def get(self, url, seen=None, method='GET'):
        seen=seen or set()
        if url in seen or len(seen)>5:return dict(url=url,observed_at=now(),status='redirect_loop',body=None)
        seen.add(url)
        base = urllib.parse.urlsplit(url)
        origin = base.scheme + '://' + base.netloc
        if origin not in self.robots:
            ru = origin + '/robots.txt'
            try:
                status, body, _ = self.raw(ru)
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(body.decode('utf-8', 'replace').splitlines() if status == 200 else [])
                allowed = status == 200 or status in (404, 410)
                self.robots[origin] = (rp, allowed, dict(url=ru, status=status,
                    observed_at=now(), body=body.decode('utf-8','replace')))
            except Exception as e:
                self.robots[origin] = (None, False, dict(url=ru,error=str(e),observed_at=now()))
        rp, readable, evidence = self.robots[origin]
        result = dict(url=url, observed_at=now(), robots=evidence)
        if not readable or not rp.can_fetch(UA, url):
            return dict(result, status='robots_disallowed_or_unavailable', body=None)
        try:
            status, body, final = self.raw(url) if method=='GET' else self.raw(url,method)
            # Never follow an HTTP redirect onto a host whose robots were not checked.
            # urllib redirects are disabled below; redirects are checked recursively.
            if status in (301,302,303,307,308):
                target=urllib.parse.urljoin(url,final)
                followed=self.get(target,seen,method)
                followed['redirects']=[dict(url=url,status=status,robots=evidence)]+followed.get('redirects',[])
                followed['requested_url']=url
                return followed
            return dict(result, status=status, final_url=final,
                        sha256=hashlib.sha256(body).hexdigest(), body=body.decode('utf-8','replace'))
        except Exception as e:
            return dict(result,status='request_failed',error=str(e),body=None)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

urllib.request.install_opener(urllib.request.build_opener(NoRedirect))

def canonical_sample(entries, candidate, limit=3):
    """A conservative sample: one original per publisher, no compilation/reupload.

    Retain every decision; title-only matching cannot prove footage independence.
    Manual excluded_video_ids are supported for the final editorial review.
    """
    accepted, decisions, families, ids, title_keys = [], [], set(), set(), []
    for e in sorted(entries, key=lambda x: x.get('view_count') or -1, reverse=True):
        title, vid = e.get('title',''), e.get('id')
        channel = e.get('channel') or e.get('uploader') or ''
        family = candidate.get('publisher_families',{}).get(e.get('channel_id'),norm(channel))
        if any(brand in norm(channel) for brand in ('비디오머그','videomug','그것이알고싶다')):family='sbs'
        for brand in ('sbs','mbc','kbs','jtbc','ytn','채널a','연합뉴스','tvn'):
            if brand in norm(channel):
                family = brand
                break
        reason = None
        if vid in OWN_IDS or '몇년나옴' in norm(channel): reason = 'own_channel'
        elif not matches(title,candidate): reason = 'case_title_mismatch'
        elif vid in candidate.get('excluded_video_ids',{}): reason = candidate['excluded_video_ids'][vid]
        elif vid in ids: reason = 'duplicate_video_id'
        elif re.search(r'재업|재편집|몰아보기|모아보는|사건모음|에디터픽|\[이슈\]|#히든아이|실화Pick|웨이브 오리지널|#천개의눈|하이라이트|#highlight|클립|요약',title,re.I): reason = 'clip_compilation_or_reupload'
        elif (e.get('duration') or 0)>1800 and re.search(r'LIVE|다시보기|풀영상|생중계|🔴',title,re.I):reason='long_live_news_stream_case_viewing_not_isolated'
        elif re.search(r'지존파.*막가파|막가파.*지존파|1994년 막가파',title): reason='mixed_case_compilation_or_wrong_incident_year'
        elif re.search(r'성폭력|성폭행|성범죄|강간|아동학대',title): reason='excluded_sex_or_child_case_content'
        elif family in families: reason = 'same_editorial_publisher_keep_one'
        elif any(norm(title) == t for t in title_keys): reason = 'duplicate_title'
        elif len(accepted) >= limit: reason = 'outside_declared_canonical_sample'
        if not reason:
            accepted.append(e); families.add(family); ids.add(vid); title_keys.append(norm(title))
        decisions.append(dict(id=vid,title=title,url=e.get('url'),view_count=e.get('view_count'),
                              channel=channel,publisher_family=family,included=reason is None,reason=reason))
    return accepted, decisions

def summary(videos):
    views = [v['view_count'] for v in videos if v.get('view_count') is not None]
    dates = [v['upload_date'] for v in videos if v.get('upload_date')]
    shorts = [v.get('is_short') for v in videos]
    return dict(n=len(videos),view_sum=sum(views) if views else None,
                view_max=max(views) if views else None,view_median=st.median(views) if views else None,
                publication_start=min(dates) if dates else None,publication_end=max(dates) if dates else None,
                contains_shorts=True if True in shorts else (False if shorts and None not in shorts else None))

def collect(c, http):
    path = OUT / (c['slug']+'.json')
    old = read(path) if path.exists() else {}
    if (old.get('youtube') or {}).get('search',{}).get('data'):
        old['candidate']=c
        sample,decisions=canonical_sample(old['youtube']['search']['data'].get('entries') or [],c)
        enriched={v['id']:v for v in old['youtube'].get('videos',[])}
        old['youtube'].update(videos=[enriched.get(v['id'],v) for v in sample],filter_decisions=decisions)
        old['youtube']['summary']=summary(old['youtube']['videos'])
        save_fields(path,dict(candidate=c,youtube=old['youtube']))
        return old
    d = dict(old,schema_version=1,candidate=c,collection_started_at=now())
    if c.get('hard_exclusion'):
        d.update(youtube=None,news=None,search_interest=None,score=None,
                 exclusion=c['hard_exclusion'])
        write(path,d); return d
    query = c['query']
    search = yt(['ytsearch30:'+query,'--flat-playlist','-J'])
    entries = (search.get('data') or {}).get('entries') or []
    sample, decisions = canonical_sample(entries,c)
    d['youtube'] = dict(query=query,search=search,canonical_sample_limit=3,
        filter_decisions=decisions,videos=sample,summary=summary(sample),
        limitations=['Title matching and publisher grouping only; no footage fingerprinting.',
                      'Sample of at most three independent editorial publishers; not all search views.',
                      'Shorts status unknown until an explicit Shorts route is observed.'])
    d['news'] = dict(article_count=None,article_count_scope='Matched unique URLs from saved public search results, never total coverage.',
                     reactions=[],sources=c.get('sources',[]))
    d['search_interest'] = read(OUT/'access.json') if (OUT/'access.json').exists() else None
    d['historical_signals'] = c.get('historical_signals',[])
    write(path,d)
    return d

def baseline(video,c):
    channel = video.get('channel_url')
    if not channel: return dict(median_views=None,ratio=None,reason='channel_url_missing')
    # Same publisher, same broad crime/court genre. Raw results permit manual audit.
    genre = c.get('baseline_query','사건 판결')
    url = channel+'/search?query='+urllib.parse.quote(genre)
    key = hashlib.sha256((url).encode()).hexdigest()[:20]
    p = OUT/'channels'/(key+'.json')
    if p.exists(): r=read(p)
    else:
        r=yt([url,'--flat-playlist','--playlist-end','30','-J']);write(p,r)
    entries = (r.get('data') or {}).get('entries') or []
    kept=[]; rejected=[]; seen=set()
    focal_duration = video.get('duration')
    for e in entries:
        reason=None; title=e.get('title',''); duration=e.get('duration')
        if e.get('id') == video.get('id'): reason='focal_video'
        elif e.get('id') in seen: reason='duplicate'
        elif matches(title,c): reason='same_case_not_comparator'
        elif not re.search(r'살인|폭행|사기|횡령|방화|강도|사건|판결|징역|집행유예|법원|선고|검찰|경찰|범죄|murder|assault|case|crime|court|prison|sentenc|police|fraud|arson|convict|theft|robber',title,re.I): reason='genre_mismatch'
        elif re.search(r'재업|몰아보기|모아보는|사건모음|에디터픽|\[이슈\]|#히든아이|실화Pick|하이라이트|클립|요약',title,re.I): reason='clip_compilation'
        elif duration is None or focal_duration is None: reason='duration_missing'
        elif (duration >= 480) != (focal_duration >= 480): reason='different_duration_band'
        elif (duration < 60) != (focal_duration < 60): reason='different_short_duration_band'
        elif e.get('view_count') is None: reason='view_count_missing'
        if reason: rejected.append(dict(id=e.get('id'),title=title,reason=reason))
        else: kept.append(e);seen.add(e.get('id'))
    vals=[e['view_count'] for e in kept]
    median=st.median(vals) if vals else None
    return dict(query=genre,url=url,observed_at=r['observed_at'],raw_path=str(p.relative_to(W)),
                n=len(kept),comparators=kept,rejected=rejected,median_views=median,
                ratio=video['view_count']/median if median and video.get('view_count') is not None else None,
                limitations='Channel search relevance sample; same crime/court genre and <8m/≥8m band, not age-matched. Historical subscriber counts unavailable.')

def enrich(d,http):
    if not d.get('youtube'): return d
    c=d['candidate']; updated=[]
    for e in d['youtube']['videos']:
        v=dict(e); p=OUT/'videos'/(e['id']+'.json')
        if p.exists(): r=read(p)
        else:
            r=yt([e['url'],'--skip-download','--ignore-no-formats-error',
                  '--extractor-args','youtube:player_skip=js,configs;player_client=web','-J'])
            write(p,r); time.sleep(2)
        meta=r.get('data') or {}
        for k in ['upload_date','timestamp','channel_follower_count','view_count','comment_count','duration','channel_id','channel_url','channel','title']:
            v[k]=meta.get(k)
        v['metadata_observed_at']=r['observed_at']; v['metadata_raw_path']=str(p.relative_to(W))
        v['days_since_posting']=None
        if v.get('upload_date'):
            day=dt.datetime.strptime(v['upload_date'],'%Y%m%d').date()
            v['days_since_posting']=(dt.datetime.fromisoformat(r['observed_at']).date()-day).days
        v['views_per_day']=(v['view_count']/max(v['days_since_posting'],1)
                            if v.get('view_count') is not None and v['days_since_posting'] is not None else None)
        # Short duration is not proof of Shorts format.
        v['is_short']=True if '/shorts/' in str(meta.get('original_url','')) else (e.get('is_short') if e.get('shorts_evidence') else None)
        v['shorts_missing_reason']='Watch URL/duration alone cannot establish Shorts format.' if v['is_short'] is None else None
        v['baseline']=baseline(v,c)
        updated.append(v)
        d['youtube']['videos']=updated+[x for x in d['youtube']['videos'][len(updated):]]
        save_fields(OUT/(c['slug']+'.json'),dict(youtube=d['youtube']))
    d['youtube']['videos']=updated;d['youtube']['summary']=summary(updated)
    d['enriched_at']=now();save_fields(OUT/(c['slug']+'.json'),dict(youtube=d['youtube'],enriched_at=d['enriched_at']));return d

def shorts_routes(d,http):
    """YouTube redirects non-Shorts /shorts/ID to /watch; measure, don't infer from duration."""
    y=d.get('youtube') or {}
    for v in y.get('videos',[]):
        p=OUT/'shorts_routes'/(v['id']+'.json')
        if p.exists():r=read(p)
        else:
            r=http.get('https://www.youtube.com/shorts/'+v['id'],method='HEAD');write(p,r)
        final=r.get('final_url','');status=r.get('status')
        v['is_short']=(True if status==200 and '/shorts/'+v['id'] in final else
                       False if status==200 and '/watch?' in final else None)
        v['shorts_evidence']=dict(url=r['url'],final_url=final,status=status,observed_at=r['observed_at'],raw_path=str(p.relative_to(W)))
        v['shorts_missing_reason']=None if v['is_short'] is not None else 'Shorts route unavailable or ambiguous.'
    y['summary']=summary(y.get('videos',[]));save_fields(OUT/(d['candidate']['slug']+'.json'),dict(youtube=y))

def rank_pct(values, value):
    if value is None or not values: return None
    return (sum(x < value for x in values) + .5*sum(x == value for x in values))/len(values)

def corr(x,y):
    if len(x)<3: return None
    a=st.mean(x);b=st.mean(y);den=math.sqrt(sum((v-a)**2 for v in x)*sum((v-b)**2 for v in y))
    return sum((u-a)*(v-b) for u,v in zip(x,y))/den if den else None

def rank():
    docs=[read(p) for p in OUT.glob('*.json') if isinstance(read(p),dict) and 'candidate' in read(p)]
    manifest={c['slug']:c for c in read(OUT/'candidates.json')}
    for d in docs:
        d['candidate']=manifest.get(d['candidate']['slug'],d['candidate'])
        if (OUT/'access.json').exists():d['search_interest']=read(OUT/'access.json')
        videos=(d.get('youtube') or {}).get('videos',[])
        complete=[v for v in videos if v.get('days_since_posting') is not None
                  and v.get('channel_follower_count') is not None and (v.get('baseline') or {}).get('ratio') is not None]
        ratios=[v['baseline']['ratio'] for v in complete]
        rates=[v['views_per_day'] for v in complete if v.get('views_per_day') is not None]
        d['demand_inputs']=dict(complete_videos=len(complete),relative_performance_median=st.median(ratios) if ratios else None,
                               views_per_day_median=st.median(rates) if rates else None)
        # Search interest is independent of YouTube. Use the same anchor and window.
        trend=(d.get('naver',{}).get('datalab',{}).get('data') or {}).get('results',[])
        case_series=trend[0].get('data',[]) if trend else []
        anchor_series=trend[1].get('data',[]) if len(trend)>1 else []
        peak=max((x['ratio'] for x in case_series),default=None)
        anchor=st.median([x['ratio'] for x in anchor_series]) if anchor_series else None
        search_interest=peak/anchor if peak is not None and anchor else None
        d['search_summary']=dict(case_peak_ratio=peak,anchor_daily_median=anchor,peak_over_anchor_median=search_interest,
            returned_days=len(case_series),peak_days=[x for x in case_series if x['ratio']==peak],
            query=d.get('naver',{}).get('datalab',{}).get('query'),observed_at=d.get('naver',{}).get('datalab',{}).get('observed_at'),
            note='Normalized relative volume, not absolute searches. Absent days are missing; broad keywords may include follow-up news.')
        recent_start=(dt.date.today()-dt.timedelta(days=90)).isoformat()
        recent_points=[x for x in case_series if x['period']>=recent_start]
        d['search_summary']['recent_90d']=dict(start=recent_start,returned_days=len(recent_points),
            mean_returned_ratio=st.mean(x['ratio'] for x in recent_points) if recent_points else None,
            peak_ratio=max((x['ratio'] for x in recent_points),default=None),
            latest_returned_point=recent_points[-1] if recent_points else None)
        # Engagement rate is an observable proxy for outrage; no sentiment is invented.
        comment_rates=[1000*v['comment_count']/v['view_count'] for v in complete if v.get('comment_count') is not None and v.get('view_count')]
        signals=d.get('independent_signals',[])
        hist=[x for x in d.get('historical_signals',[]) if x.get('kind')=='community' and x.get('comments') is not None]
        reactions=[measured_number(x.get('comments')) for x in signals+hist if measured_number(x.get('comments')) is not None]
        d['independent_reaction_comments_max']=max(reactions) if reactions else None
        d['outrage_input']=st.median(comment_rates) if comment_rates else None
        d['demand_signal_kinds']=(['youtube_performance'] if complete else []) + (['naver_search_volume'] if search_interest is not None and search_interest>0 else []) + (['public_community_or_news_reaction'] if any(x>0 for x in reactions) else [])
        d['missing']=[]
        if not complete:d['missing'].append('YT 게시일·구독자·유사영상 대비 성과의 완전한 표본')
        if search_interest is None and not reactions:d['missing'].append('독립 수요 신호(검색량/뉴스·커뮤니티 반응)')
        if search_interest is None:d['missing'].append('데이터랩 시계열(합성 점수 입력)')
        if not comment_rates:d['missing'].append('영상 댓글 참여율')
        if not d['candidate'].get('factual_verified'):d['missing'].append('신뢰할 원문으로 심급·결과 재확인')
        if any(v.get('is_short') is None for v in videos):d['missing'].append('Shorts 형식 명시 확인')
        if len(complete)<len(videos):d['missing'].append(f'원본 {len(videos)}편 중 성과 비교 완전 표본 {len(complete)}편')
        if not signals:d['missing'].append('이번 뉴스 공개 반응 수(미노출)')
        if '미확인' in str(d['candidate'].get('sentence')) or d['candidate'].get('finality_unknown'):d['missing'].append('최종 확정 여부(해당 심급까지만 사용)')
    reference=[d for d in docs if not d['candidate'].get('hard_exclusion') and not d['candidate'].get('supplement_only')]
    rs=[d['demand_inputs']['relative_performance_median'] for d in reference if d['demand_inputs']['relative_performance_median'] is not None]
    vs=[d['demand_inputs']['views_per_day_median'] for d in reference if d['demand_inputs']['views_per_day_median'] is not None]
    os_=[d['outrage_input'] for d in reference if d['outrage_input'] is not None]
    ss=[d['search_summary']['peak_over_anchor_median'] for d in reference if d['search_summary']['peak_over_anchor_median'] is not None]
    for d in docs:
        a=rank_pct(rs,d['demand_inputs']['relative_performance_median']);b=rank_pct(vs,d['demand_inputs']['views_per_day_median']);o=rank_pct(os_,d['outrage_input'])
        search_pct=rank_pct(ss,d['search_summary']['peak_over_anchor_median'])
        demand=(a*b*search_pct)**(1/3) if None not in (a,b,search_pct) else None
        judgment=1 if d['candidate'].get('factual_verified') else None
        score=100*demand*o*judgment if None not in (demand,o,judgment) else None
        d['score']=dict(value=round(score,3) if score is not None else None,demand=demand,outrage=o,confirmed_judgment=judgment,
            formula='100 × cbrt(percentile(YT relative median) × percentile(YT views/day median) × percentile(Naver peak/anchor median)) × percentile(YT comments/1000 views median) × verified judgment(1)',
            note='Heuristic, relative within this run; comments proxy engagement, not measured anger. No absolute pass line; null is never imputed.')
        c=d['candidate']
        d['selection_status']='excluded' if c.get('hard_exclusion') or c.get('used_as') else ('relative_candidate' if score is not None and c.get('channel_fit') else 'evidence_pending')
    # Format-specific demand: a short news report does not demonstrate long-video demand.
    for d in docs:
        lv=[v for v in (d.get('youtube') or {}).get('videos',[]) if (v.get('duration') or 0)>=480
            and v.get('days_since_posting') is not None and v.get('channel_follower_count') is not None
            and (v.get('baseline') or {}).get('ratio') is not None]
        rates=[1000*v['comment_count']/v['view_count'] for v in lv if v.get('comment_count') is not None and v.get('view_count')]
        d['longform_inputs']=dict(summary=summary(lv),video_ids=[v['id'] for v in lv],
            relative_median=st.median(v['baseline']['ratio'] for v in lv) if lv else None,
            daily_median=st.median(v['views_per_day'] for v in lv) if lv else None,
            comment_rate_median=st.median(rates) if rates else None)
    lfref=[d for d in reference if d['candidate'].get('longform') and d['longform_inputs']['relative_median'] is not None]
    lfr=[d['longform_inputs']['relative_median'] for d in lfref]
    lfv=[d['longform_inputs']['daily_median'] for d in lfref]
    lfo=[d['longform_inputs']['comment_rate_median'] for d in lfref if d['longform_inputs']['comment_rate_median'] is not None]
    lfs=[d['search_summary']['peak_over_anchor_median'] for d in lfref if d['search_summary']['peak_over_anchor_median'] is not None]
    for d in docs:
        l=d['longform_inputs'];a=rank_pct(lfr,l['relative_median']);b=rank_pct(lfv,l['daily_median']);o=rank_pct(lfo,l['comment_rate_median']);s=rank_pct(lfs,d['search_summary']['peak_over_anchor_median'])
        g=d['score']['confirmed_judgment'];val=100*(a*b*s)**(1/3)*o*g if None not in (a,b,o,s,g) else None
        d['longform_score']=dict(value=round(val,3) if val is not None else None,
            formula=d['score']['formula'],scope='Same formula, restricted to original ≥8-minute videos and the long-form comparison cohort.')
        write(OUT/(d['candidate']['slug']+'.json'),d)
    ordered=sorted(docs,key=lambda d:(d['score']['value'] is not None,d['score']['value'] or -1,(d.get('youtube') or {}).get('summary',{}).get('view_median') or -1),reverse=True)
    eligible=[d for d in ordered if d['selection_status']!='excluded' and not d['candidate'].get('supplement_only')]
    lines=['# 데이터 기반 소재 비교', '', '측정·생성: '+now(), '',
        '**점수는 상대 비교용이다. 선정은 사실 원문·서로 독립인 수요 2종·첫 장면과 형량 질문 적합성을 함께 확인한다. 미측정은 `null`; 기사 수와 조회 합계만으로 선정하지 않는다.**','',
        'YouTube: 사건별 ytsearch30에서 제목을 대조하고 재업·요약·합본·동일 방송사 파생 채널을 제거해 최대 3개 독립 편집 주체의 원본 표본. 공식 채널의 독립 보도는 포함하고, 방송 재편집 표식이 있는 클립은 제외했다. 영상 지문 대조는 하지 않아 타사 간 동일 CCTV 사용까지 중복 시청자로 분리할 수는 없다. 전체 검색 결과와 제외 이유는 JSON에 보존. 구독자는 측정 시점 값이며 게시 당시 값이 아니다. 유사 영상은 같은 채널의 범죄·판결 검색 결과, 60초 미만/60초~8분/8분 이상 길이군으로 비교한다. 게시 경과 차이를 완전히 통제하지 못한다.','',
        '점수 = 100 × ∛(채널 대비 조회 배수 중앙값 백분위 × 일평균 조회 중앙값 백분위 × 데이터랩 정점/공통 기준어 일중앙값 백분위) × 영상 댓글/1천뷰 중앙값 백분위 × 판결 원문 확인(1). 댓글 참여율은 공분의 대용값이며 감정 측정값이 아니다. 어느 입력이든 없으면 점수도 미측정이다. 정량 통과선은 없다.','',
        '독립 수요 2종은 YouTube 성과와 네이버 데이터랩 검색량이다. 뉴스·블로그·카페 API total은 색인 결과 수여서 검색량이나 사람 수로 해석하지 않는다. Google Trends 429는 결측으로 보존한다. 공통 비교창은 2023-11-06부터이며, 확인된 사건·재판 날짜 전후 14일은 별도 조회 또는 공통 시계열에서 추출해 JSON `naver.event_windows`에 보존했다. 날짜가 연·월까지만 확인되면 일자를 만들지 않았다. 사건 당시 관심과 최근 90일 관심은 다르다.','',
        '확인된 선고·약식명령과 최종 확정을 구분했다. 상고 중이거나 확정 여부를 확인하지 못한 사건은 해당 심급 결과까지만 답해야 한다. 점수 산출 비교집단은 편집·안전 제외를 뺀 조사 후보이며, 사용한 소재도 교정 참고 점수는 산출하되 제작 순위에서는 제외한다.','']
    lines += [f"조사 목록 {len(docs)}개 레코드에는 별칭·중복 사건과 제외 이력이 포함된다. 신규 발견 표기는 {sum(d['candidate'].get('origin')=='new' for d in docs)}건이며, 이 중 최근 선고 원문을 확인한 미제외 후보는 {sum(d['candidate'].get('origin')=='new' and d['candidate'].get('factual_verified') and not d['candidate'].get('hard_exclusion') for d in docs)}건이다.", '',
        'Shorts 표는 사건 전체 수요 점수, 장편 표는 **8분 이상 원본 표본만의 별도 점수**다. 장편은 같은 산식을 장편 비교집단 안에서 다시 계산하므로 두 표의 점수를 서로 비교하지 않는다. 상위 순위도 상대 후보이며 편당 완성 대본의 사실 검토를 대신하지 않는다.','']
    long_pool=sorted([d for d in eligible if d['candidate'].get('longform')],key=lambda d:(d['longform_score']['value'] is not None,d['longform_score']['value'] or -1),reverse=True)
    for label, pool, limit in [('Shorts',eligible,15),('장편',long_pool,6)]:
        lines += ['## '+label+' 상대 비교 TOP '+str(limit),'',
            '점수가 없는 행은 **조사 우선순위 참고**이며 선정 승인이 아니다. 순위 안에서도 근거와 결측을 함께 판단한다.','',
            '|순위|후보·원자료|점수·상태|수요 근거|확인한 선고·심급|첫 장면·자극 포인트|결측|',
            '|---:|---|---|---|---|---|---|']
        for i,d in enumerate(pool[:limit],1):
            c=d['candidate'];s=(d.get('youtube') or {}).get('summary',{});x=d['demand_inputs']
            if label=='장편':
                l=d['longform_inputs'];s=l['summary'];x=dict(relative_performance_median=l['relative_median'])
            evidence='타 채널 원본 표본 합계 '+(f"{s['view_sum']:,}회" if s.get('view_sum') is not None else '미측정')
            ratio=x['relative_performance_median'];trend=d['search_summary']['peak_over_anchor_median'];comments=d['longform_inputs']['comment_rate_median'] if label=='장편' else d['outrage_input']
            evidence+=f"; 채널 대비 {round(ratio,2) if ratio is not None else '미측정'}배; 검색 정점/기준 {round(trend,2) if trend is not None else '미측정'}배; 댓글/천뷰 {round(comments,2) if comments is not None else '미측정'}"
            state='상대 후보' if d['selection_status']=='relative_candidate' else '근거 보완'
            value=(d['longform_score'] if label=='장편' else d['score'])['value'];value=str(round(value,2)) if value is not None else '미측정'
            esc=lambda t:str(t).replace('|','/').replace('\n',' ')
            source=next((s['url'] for s in c.get('sources',[]) if isinstance(s,dict) and s.get('url')),None)
            sentence=(c.get('sentence') or '미확인')+(f' [근거]({source})' if source else '')
            if isinstance(c.get('trial_stage'),str):sentence=c['trial_stage']+' · '+sentence
            lines.append('|'+ '|'.join(map(esc,[i,f"[{c['name']}]({c['slug']}.json)",value+' · '+state,evidence,sentence,c.get('channel_fit','미확인'),' · '.join(d['missing']) or '없음']))+'|')
    lines += ['','## 후보별 영상·검색 증거와 결측','', '게시 경과일·현재 구독자·채널 유사 영상 중앙값과 배수는 아래에 표시한다. 원시 30개와 전체 비교 영상 URL은 각 JSON에 있다. 유사 영상 수가 적거나 수집 채널이 대형 뉴스사이면 순위를 보수적으로 읽는다.','']
    for d in eligible:
        c=d['candidate'];lines += ['### '+c['name']+' · '+c['slug'],'',
            '|원본 영상|조회|게시 경과일|현재 구독자|유사 표본 n·조회 중앙값|성과 배수|',
            '|---|---:|---:|---:|---|---:|']
        for v in (d.get('youtube') or {}).get('videos',[]):
            bl=v.get('baseline') or {};rr=bl.get('ratio');title=v.get('title') or v['id']
            lines.append(f"|[{title.replace('|','/')} ]({v.get('url')})|{v.get('view_count')}|{v.get('days_since_posting')}|{v.get('channel_follower_count')}|{bl.get('n')} · {bl.get('median_views')}|{round(rr,3) if rr is not None else '미측정'}|")
        ns=d.get('naver',{}).get('search',{});counts={k:(v.get('data') or {}).get('total') for k,v in ns.items()}
        sy=(d.get('youtube') or {}).get('summary',{});search=d['search_summary']
        lines += ['',f"YT 질의: `{(d.get('youtube') or {}).get('query')}` · 측정 {(d.get('youtube') or {}).get('search',{}).get('observed_at')} · 게시 기간 {sy.get('publication_start')}~{sy.get('publication_end')} · Shorts 포함 {sy.get('contains_shorts')}. 합계는 고유 시청자 수가 아니다.",
            f"데이터랩 질의: `{c.get('trend_keywords')}` · 측정 {search['observed_at']} · 최근 90일 반환일 {search['recent_90d']['returned_days']}일, 반환값 평균 {search['recent_90d']['mean_returned_ratio']}, 정점 {search['recent_90d']['peak_ratio']}. 정점/기준 배수는 원시 검색 건수가 아니다.",
            f"검색 API 질의: `{c.get('news_query',c['query'])}` · 뉴스/블로그/카페 색인 수 {counts} · 사건 제목 대조 기사 표본 {(d.get('news') or {}).get('article_count')}건 · 측정 {ns.get('news',{}).get('observed_at')}.",
            f"뉴스 공개 댓글 최대 {d.get('independent_reaction_comments_max')}개(표시된 페이지 표본; 미노출은 결측). 출처·시각·질의는 JSON `independent_signals`와 `historical_signals`에 있다.",
            f"판결: {c.get('sentence')} · 제작 중: {c.get('running_lane','아님')} · 결측: {' / '.join(d['missing']) or '없음'}.",
            '판결 근거: '+' · '.join(f"[{s.get('publisher') or s.get('title') or '원문'}]({s['url']})" for s in c.get('sources',[]) if isinstance(s,dict) and s.get('url')),'']
        if c.get('legacy_source_caveats'):
            lines += ['기존 원문 조사 주의사항(당시 기준): '+' / '.join(str(x) for x in c['legacy_source_caveats']),'']
    lines += ['','## 전체 후보·제외·제작 중 중복','', '|후보|구분|처리·이유|', '|---|---|---|']
    for d in sorted(docs,key=lambda x:x['candidate']['slug']):
        c=d['candidate'];why=c.get('hard_exclusion') or ('기존 사용 '+str(c['used_as']) if c.get('used_as') else d['selection_status'])
        lines.append(f"|[{c['name']}]({c['slug']}.json)|{c.get('origin')}|{why}|")
    calibration=[]
    for d in docs:
        for pub in d['candidate'].get('published',[]):
            calibration.append(dict(slug=d['candidate']['slug'],**pub,score=d['score']['value'],
                youtube_relative=d['demand_inputs']['relative_performance_median'],youtube_daily=d['demand_inputs']['views_per_day_median'],missing=d['missing']))
    paired=[x for x in calibration if x['score'] is not None]
    xs=[x['score'] for x in paired];ys=[x['views'] for x in paired]
    rank_values=lambda vs:[sum(a<v for a in vs)+.5*sum(a==v for a in vs) for v in vs]
    cal=dict(source='channel/analytics/snapshot_2026-11-06.md',observed_at=now(),rows=calibration,n_total=len(calibration),n_complete=len(paired),
             pearson=corr(xs,ys),spearman=corr(rank_values(xs),rank_values(ys)),
             limitations=['Small observational sample; accumulated views differ in exposure age and distribution.',
                          'Scores are measured after publication and are not a prospective validation.',
                          'Incomplete score rows are omitted pairwise, never set to zero.'])
    write(OUT/'calibration.json',cal)
    lines+=['','## 발행 영상 15편 교정 참고','',f"총 {len(calibration)}편, 완전한 점수 쌍 {len(paired)}편. Pearson={round(cal['pearson'],4) if cal['pearson'] is not None else None}, Spearman={round(cal['spearman'],4) if cal['spearman'] is not None else None}. [영상별 원자료](calibration.json)", '',
        '작은 표본·게시 경과·노출량·제목과 연출 차이가 섞여 있으며, 발행 후 측정이라 예측력 입증이 아니다. 점수 결측 영상은 상관계수에서 제외하며 0으로 넣지 않는다. 이 결과로 채널 조회수 예측력을 검증했다고 볼 수 없다.','',
        '|발행 영상 사건|자체 조회수(스냅샷)|사건 수요 점수|결측|','|---|---:|---:|---|']
    for row in calibration:
        lines.append(f"|[{row['slug']}](https://www.youtube.com/watch?v={row['video_id']})|{row['views']}|{row['score']}|{' · '.join(row['missing']) or '없음'}|")
    lines+=['',
        '## 재실행','', '아래 명령은 캐시를 재사용한다. 키는 `naver` 단계에서만 키체인으로 읽으며 요청 헤더 외에 저장하지 않는다. 원자료를 새로 측정하려면 해당 후보/영상/채널 캐시를 별도로 보관한 뒤 재수집한다.','',
        '```sh','python3 factory/topic_score.py collect','python3 factory/topic_score.py naver','python3 factory/topic_score.py sources','python3 factory/topic_score.py enrich','python3 factory/topic_score.py shorts','python3 factory/topic_score.py rank','```','',
        '## 접근 제한','', 'Google Trends: HTTP 429로 건너뜀. 네이버 뉴스 댓글은 robots 제한으로 접근하지 않았다. 뉴스 원문은 robots를 확인하고 호스트별 2초 이상 간격으로 수집했다. 노출된 댓글만 숫자로 보존했으며 동적·로그인 카운터는 결측이다. 네이버 API는 소유자 추가 지시로 무료 키 사용이 허용됐다. [접근 상세](access.json)','']
    if (OUT/'sentence_gap_facts.json').exists():
        import topic_gap
        topic_gap.update(sys.modules[__name__])
        lines += topic_gap.render(sys.modules[__name__])
    (OUT/'RANKED.md').write_text('\n'.join(lines).replace('None','미측정'))
    print(json.dumps(dict(candidates=len(docs),new=sum(c.get('origin')=='new' for c in [d['candidate'] for d in docs]),complete_scores=sum(d['score']['value'] is not None for d in docs),calibration=cal['n_complete']),ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['collect','enrich','naver','sources','shorts','rank','gap']);p.add_argument('--slug');p.add_argument('--limit',type=int);p.add_argument('--comments',action='store_true')
    args=p.parse_args();OUT.mkdir(exist_ok=True,parents=True)
    if args.action=='rank':rank();return
    if args.action=='gap':
        import topic_gap
        topic_gap.update(sys.modules[__name__],comments=args.comments);return
    candidates=read(OUT/'candidates.json');http=PublicHTTP()
    selected=[c for c in candidates if not args.slug or c['slug']==args.slug]
    if args.limit:selected=selected[:args.limit]
    if args.action=='naver':
        client=Naver()
        for c in selected:
            print('naver',c['slug'],flush=True)
            if not c.get('hard_exclusion'):
                naver_collect(c,client);naver_context(c,client)
        print('API calls this process:',client.calls)
        return
    if args.action=='sources':
        for c in selected:
            path=OUT/(c['slug']+'.json')
            if path.exists() and not c.get('hard_exclusion'):
                print('sources',c['slug'],flush=True)
                d=read(path);d['candidate']=c;fetch_sources(d,http)
        return
    if args.action=='shorts':
        for c in selected:
            path=OUT/(c['slug']+'.json')
            if path.exists() and not c.get('hard_exclusion'):
                print('shorts',c['slug'],flush=True);shorts_routes(read(path),http)
        return
    for c in selected:
        print(args.action,c['slug'],flush=True)
        d=collect(c,http)
        if args.action=='enrich':enrich(d,http)
        time.sleep(2)

if __name__=='__main__':main()
