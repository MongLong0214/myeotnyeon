import json,urllib.request,urllib.parse,concurrent.futures,time,os
c=json.load(open('search/all_candidates.json'))
todo=[e for e in c if (e['views'] or 0)>=5000]
cache={}
if os.path.exists('search/oembed.json'): cache=json.load(open('search/oembed.json'))
def f(e):
    if e['id'] in cache: return e['id'],cache[e['id']]
    u='https://www.youtube.com/oembed?format=json&url='+urllib.parse.quote('https://www.youtube.com/shorts/'+e['id'])
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:
            d=json.load(r); return e['id'],{'title':d.get('title'),'author':d.get('author_name'),'author_url':d.get('author_url')}
    except Exception as ex:
        return e['id'],{'error':repr(ex)[:100]}
with concurrent.futures.ThreadPoolExecutor(4) as ex:
    for vid,d in ex.map(f,todo): cache[vid]=d
json.dump(cache,open('search/oembed.json','w'),ensure_ascii=False)
print(len(todo),sum(1 for v in cache.values() if 'error' in v))
