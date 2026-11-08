import json,re,collections,sys
def views(t):
    m=re.search(r'조회수 ([\d.,]+)(천|만|억)?회',t or '')
    if not m: return None
    n=float(m.group(1).replace(',',''));u={'천':1e3,'만':1e4,'억':1e8}.get(m.group(2),1)
    return int(n*u)
rows={}
for l in open('search/shorts_results.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['kind']!='short' or r.get('own_channel'): continue
    v=views(r['a11y'])
    e=rows.setdefault(r['id'],{'id':r['id'],'views':v,'title':re.sub(r', 조회수.*$','',r['a11y']),'queries':[]})
    e['queries'].append(r['query'])
out=sorted(rows.values(),key=lambda x:-(x['views'] or 0))
json.dump(out,open('search/shorts_agg.json','w'),ensure_ascii=False,indent=0)
print(len(out))
for e in out[:int(sys.argv[1]) if len(sys.argv)>1 else 120]:
    print(e['id'],e['views'],e['title'][:80],'|',','.join(e['queries'])[:40],sep='\t')
