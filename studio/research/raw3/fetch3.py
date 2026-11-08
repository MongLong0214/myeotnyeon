#!/usr/bin/env python3
"""Robots-checked fetch. Usage: fetch3.py ID URL [grep-regex]. Saves raw3/ID.txt (text only) + fetch_log.jsonl.
Skips the URL if robots.txt disallows it for *, ClaudeBot, Claude-User, anthropic-ai or Claude-Web."""
import sys,hashlib,re,html,urllib.request,urllib.robotparser,urllib.parse,json,datetime,pathlib,ssl
sid,url=sys.argv[1],sys.argv[2]; rx=re.compile(sys.argv[3]) if len(sys.argv)>3 else None
out=pathlib.Path(__file__).parent
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
ctx=ssl.create_default_context()
p=urllib.parse.urlparse(url)
try:
    rb=urllib.request.urlopen(urllib.request.Request(f'{p.scheme}://{p.netloc}/robots.txt',headers={'User-Agent':UA}),timeout=15,context=ctx).read().decode('utf-8','ignore')
    rp=urllib.robotparser.RobotFileParser(); rp.parse(rb.splitlines())
    bad=[u for u in ('*','ClaudeBot','Claude-User','anthropic-ai','Claude-Web') if not rp.can_fetch(u,url)]
except urllib.error.HTTPError as e:
    bad=[] if e.code in (404,410) else [f'robots-http-{e.code}']
if bad: print('SKIP robots', bad, url); sys.exit(2)
req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'ko-KR,ko;q=0.9'})
b=urllib.request.urlopen(req,timeout=25,context=ctx).read()
for enc in ('utf-8','cp949','euc-kr'):
    try: t=b.decode(enc); break
    except UnicodeDecodeError: continue
scr=[]
for blk in re.findall(r'(?is)<script[^>]*>(.*?)</script>',t):
    for m in re.findall(r'"((?:[^"\\]|\\.){30,})"',blk):
        if re.search(r'[가-힣]{4}',m):
            try: m=json.loads('"'+m+'"')
            except Exception: pass
            scr.append(re.sub(r'<[^>]+>',' ',html.unescape(m)))
meta_desc=' '.join(html.unescape(x) for x in re.findall(r'(?i)<meta[^>]+(?:name|property)="(?:og:description|description)"[^>]+content="([^"]*)"',t))
t=re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>',' ',t)
t=re.sub(r'(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>','\n',t)
t=html.unescape(re.sub(r'<[^>]+>',' ',t))
t='\n'.join(re.sub(r'\s+',' ',l).strip() for l in t.splitlines() if l.strip())
seen=set(); extra=[x for x in scr if not (x in seen or seen.add(x)) and x[:60] not in t]
t=t+'\n\n[META] '+meta_desc+('\n\n[SCRIPT-TEXT]\n'+'\n'.join(extra) if extra else '')
(out/f'{sid}.txt').write_text(f'URL: {url}\n\n'+t)
meta={'source_id':sid,'url':url,'fetched_at':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
with open(out/'fetch_log.jsonl','a') as f: f.write(json.dumps(meta,ensure_ascii=False)+'\n')
print('OK',sid,len(t),'chars')
if rx:
    for l in t.splitlines():
        if rx.search(l) and len(l)>25: print('  >',l[:400])
