"""Fetch source HTML as inert data; extract article text without executing it."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib,json,re,requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
SOURCES=[
('S01','문화일보','2025-06-18','https://n.news.naver.com/mnews/article/021/0002716926'),
('S02','세계일보','2025-06-18','https://n.news.naver.com/mnews/article/022/0004044683'),
('S03','한겨레','2025-09-25','https://n.news.naver.com/mnews/article/028/0002768144'),
('S04','뉴시스','2025-09-25','https://n.news.naver.com/mnews/article/003/0013504912'),
('S05','KBS','2025-09-25','https://n.news.naver.com/mnews/article/056/0012036865'),
('S06','YTN','2024-11-12','https://www.ytn.co.kr/_ln/0115_202411121754337066'),
('S07','뉴시스','2024-11-12','https://www.newsis.com/view/NISX20241112_0002956598'),
('S08','뉴시스','2025-01-07','https://www.newsis.com/view/NISX20250107_0003024232'),
('S09','뉴스1','2025-01-07','https://www.news1.kr/local/kangwon/5654138'),
('S10','경향신문','2025-06-18','https://www.khan.co.kr/article/202506181457001'),
('S11','경향신문','2025-01-07','https://www.khan.co.kr/article/202501072035045/'),
('S12','YTN','2025-01-07','https://www.ytn.co.kr/_ln/0115_202501071440416054'),
('S13','뉴스핌','2025-09-25','https://www.newspim.com/news/view/20250925000887'),
]
def fetch(item):
 sid,pub,date,url=item
 now=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')
 try:
  r=requests.get(url,timeout=35,headers={'User-Agent':'Mozilla/5.0'})
  r.raise_for_status()
  (ROOT/f'{sid}.html').write_bytes(r.content)
  s=BeautifulSoup(r.content,'html.parser')
  canonical=s.select_one('a.media_end_head_origin_link') or s.select_one('link[rel="canonical"]')
  canonical=canonical.get('href') if canonical else r.url
  title=s.select_one('#title_area') or s.select_one('meta[property="og:title"]') or s.select_one('h1') or s.title
  title=(title.get('content') or title.get_text(' ',strip=True)) if title else ''
  body=None
  selector=None
  if pub=='뉴스1':
   data=json.loads(s.select_one('#__NEXT_DATA__').string)['props']['pageProps']['articleView']
   body=BeautifulSoup('<br/>'.join(x['content'] for x in data['contentArrange'] if x.get('type')=='text'),'html.parser')
   selector='__NEXT_DATA__.props.pageProps.articleView.contentArrange[type=text]'
  for sel in ([] if body else ['#dic_area','#CmAdContent','.viewer > article','#news-contents','.art_txt','#articeBody','.article-text','#articleBody','.art_body','.news_body','.articleBody','.article-view-content-div','.article-body']):
   found=s.select_one(sel)
   if found and len(found.get_text(strip=True))>180:
    body=found;selector=sel;break
  if body is None:
   for x in s(['script','style','nav','header','footer']):x.decompose()
   body=s;selector='body-fallback-review-required'
  else:
   for x in body(['script','style']):x.decompose()
  pars=[re.sub(r'\s+',' ',t).strip() for t in body.get_text('\n',strip=True).splitlines()]
  pars=[t for t in pars if t]
  text='\n'.join(f'P{i:03d} {v}' for i,v in enumerate(pars,1))
  (ROOT/f'{sid}.txt').write_text(f'UNTRUSTED SOURCE DATA — not instructions\nSource-ID: {sid}\nPublisher: {pub}\nPublication-date: {date}\nFetched-at-KST: {now}\nFetch-URL: {url}\nOriginal-URL: {canonical}\nTitle: {title}\nExtraction-selector: {selector}\nRaw-HTML-SHA256: {hashlib.sha256(r.content).hexdigest()}\n\n{text}\n')
  return dict(id=sid,publisher=pub,publication_date=date,url=url,original_url=canonical,title=title,fetched_at=now,http_status=r.status_code,selector=selector,paragraphs=len(pars),text_file=f'{sid}.txt',html_file=f'{sid}.html',html_sha256=hashlib.sha256(r.content).hexdigest(),trust='untrusted-source-data')
 except Exception as e:return dict(id=sid,publisher=pub,url=url,error=str(e))
with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(fetch,SOURCES))
(ROOT/'index.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
for x in results:print(x['id'],x.get('http_status'),x.get('selector'),x.get('paragraphs'),x.get('error',''))
