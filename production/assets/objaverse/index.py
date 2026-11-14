import gzip, json, glob
rows = []
for f in sorted(glob.glob('meta/*.json.gz')):
    for uid, m in json.load(gzip.open(f)).items():
        lic = m.get('license') or ''
        rows.append(dict(uid=uid, name=m.get('name', ''), lic=lic, likes=m.get('likeCount', 0), views=m.get('viewCount', 0),
                         faces=m.get('faceCount'), verts=m.get('vertexCount'), anim=m.get('animationCount', 0),
                         tags=[t['name'] for t in m.get('tags', [])], cats=[c.get('name') for c in m.get('categories', [])],
                         user=(m.get('user') or {}).get('username'), url=m.get('viewerUrl'), desc=(m.get('description') or '')[:300]))
json.dump(rows, open('index.json', 'w'))
from collections import Counter
print(len(rows)); print(Counter(r['lic'] for r in rows).most_common(12))
