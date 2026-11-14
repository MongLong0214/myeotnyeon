# Splits the converted stock SVGs into rig parts. polar: by paint-order index ranges (artist layered it part-wise).
# walrus: whole animal is one silhouette path, so parts are polygon masks (manual), spanning paths get clipped.
import re,json,sys
R='raw/vecteezy_reyyarts/'
def load(f):
    s=open(f).read(); out=[]
    for m in re.finditer(r'<path ([^>]*?)d="([^"]+)"([^>]*)/>',s):
        n=[float(x) for x in re.findall(r'-?\d+\.?\d*',m.group(2))]
        xs,ys=n[0::2],n[1::2]
        out.append(dict(svg=m.group(0),c=((min(xs)+max(xs))/2,(min(ys)+max(ys))/2)))
    return out
def inside(p,poly):
    x,y=p; r=False; n=len(poly)
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: r=not r
    return r
def rng(*a):
    o=[]
    for s,e in a: o+=list(range(s,e+1))
    return o
P=load(R+'polar/polar.svg')
polar=dict(size=2013.2,ground=1800,parts=[
 dict(name='ears',idx=rng((2,13)),pivot=[650,720],grp='head'),
 dict(name='farFront',idx=rng((14,57)),pivot=[560,1150]),
 dict(name='farLegs',idx=rng((58,76)),pivot=[1250,1400]),
 dict(name='body',idx=rng((77,85),(105,120)),pivot=[1200,1800]),
 dict(name='nearFront',idx=rng((86,104)),pivot=[1000,1150]),
 dict(name='head',idx=rng((121,179)),pivot=[650,720],grp='head'),
])
for p in polar['parts']: p['svg']=''.join(P[i]['svg'] for i in p.pop('idx')); p['clip']=None
W=load(R+'walrus/walrus.svg')
HEAD=[(1180,640),(1270,400),(1420,300),(1640,290),(1830,400),(1900,600),(1930,850),(1800,1050),(1600,1130),(1420,1130),(1280,1050),(1210,850)]
FLIP=[(1050,1640),(1150,1560),(1420,1440),(1700,1370),(1840,1420),(1880,1560),(1700,1700),(1300,1770),(1080,1750)]
TAIL=[(10,1650),(10,1250),(150,1050),(330,1000),(420,1300),(420,1640)]
SPAN=[30,101]; DROP=[0,1,2,3,4]
g=dict(head=[],flipper=[],tail=[],body=[])
for i,p in enumerate(W):
    if i in DROP or i in SPAN: continue
    k='head' if inside(p['c'],HEAD) or i in (12,13,16,17) else 'flipper' if inside(p['c'],FLIP) else 'tail' if inside(p['c'],TAIL) else 'body'
    g[k].append(p['svg'])
span=W[30]['svg'],W[101]['svg']
pts=lambda poly:' '.join('%d,%d'%q for q in poly)
walrus=dict(size=2065.13,ground=1740,clips=dict(head=pts(HEAD),flipper=pts(FLIP),tail=pts(TAIL)),parts=[
 dict(name='tail',svg=''.join(span),clip='tail',extra=''.join(g['tail']),pivot=[420,1400]),
 dict(name='body',svg=span[0],outline=span[1],clip='NOT',extra=''.join(g['body']),pivot=[1000,1740]),
 dict(name='flipper',svg=''.join(span),clip='flipper',extra=''.join(g['flipper']),pivot=[1800,1480]),
 dict(name='head',svg=''.join(span),clip='head',extra=''.join(g['head']),pivot=[1700,1050]),
])
json.dump(dict(polar=polar,walrus=walrus),open('src/art.json','w'))
print({k:len(v) for k,v in g.items()},'polar parts',[ (p['name'],len(p['svg'])) for p in polar['parts']])
