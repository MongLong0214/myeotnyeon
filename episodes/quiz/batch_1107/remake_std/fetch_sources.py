import requests,bs4,json,datetime,hashlib
from pathlib import Path
D=Path(__file__).parent;W=D.parents[3]
rows=[('Q004_JOONGANG','중앙일보','2025-11-27','https://www.joongang.co.kr/article/25385581'),('Q004_KOOKMIN_FINAL','국민일보','2025-12-02','https://v.daum.net/v/20251202152849665'),('Q004_KBS_FINAL','KBS','2025-12-02','https://v.daum.net/v/V9wnkYlwyo'),('Q005_HANKOOK','한국일보','2026-05-28','https://www.hankookilbo.com/news/article/A2026052807460001608')]
registry=[]
for sid,pub,date,url in rows:
 f=D/'sources'/f'{sid}.txt'
 if not f.exists():
  r=requests.get(url,timeout=40);r.raise_for_status();r.encoding=r.apparent_encoding;soup=bs4.BeautifulSoup(r.text,'html.parser')
  for x in soup(['script','style','nav','footer']):x.decompose()
  text=soup.get_text('\n',strip=True);f.write_text(f'SOURCE_URL: {url}\nFETCHED_AT: {datetime.datetime.now().astimezone().isoformat()}\nPUBLISHER: {pub}\nPUBLISHED: {date}\n\n'+text)
 registry.append(dict(id=sid,publisher=pub,date=date,url=url,file=str(f.relative_to(W)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 print(sid,len(f.read_text()),flush=True)
for num,pub in [(1,'한겨레'),(2,'노컷뉴스')]:
 f=W/f'research/raw2/V2-01_{num}.txt';text=f.read_text();url=text.split('SOURCE_URL: ')[1].split('\n')[0]
 registry.append(dict(id=f'Q005_{"HANI" if num==1 else "NOCUT"}',publisher=pub,date='2026-05-27',url=url,file=str(f.relative_to(W)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(D/'sources.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
for q,slug in [('q004','v2-11'),('q005','v2-01')]:
 data=json.loads((W/f'research/topic_scores/{slug}.json').read_text());print(q,'keys',list(data),'demand',data.get('demand_inputs'),'search',data.get('search_summary'))
 p=W/'upload/pkg'/f'{q}_std';p.mkdir(exist_ok=True);(p/'topic_evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
