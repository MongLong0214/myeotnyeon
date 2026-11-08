#!/usr/bin/env python3
"""Fetch a URL, store raw bytes + extracted text + sha256. Usage: fetch.py ID URL"""
import sys,hashlib,re,html,urllib.request,json,datetime,pathlib,ssl
sid,url=sys.argv[1],sys.argv[2]
out=pathlib.Path(__file__).parent/'raw'
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36','Accept-Language':'ko-KR,ko;q=0.9'})
b=urllib.request.urlopen(req,timeout=25,context=ctx).read()
for enc in ('utf-8','cp949','euc-kr'):
    try: t=b.decode(enc); break
    except UnicodeDecodeError: continue
(out/f'{sid}.html').write_bytes(b)
t=re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>',' ',t)
t=re.sub(r'(?i)<br\s*/?>|</p>|</div>','\n',t)
t=html.unescape(re.sub(r'<[^>]+>',' ',t))
t='\n'.join(l.strip() for l in t.splitlines() if l.strip())
(out/f'{sid}.txt').write_text(t)
meta={'source_id':sid,'url':url,'fetched_at':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
with open(out/'fetch_log.jsonl','a') as f: f.write(json.dumps(meta,ensure_ascii=False)+'\n')
print(json.dumps(meta,ensure_ascii=False))
