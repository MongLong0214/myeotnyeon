import sys,re,json
d=sys.argv[1]; fps=float(sys.argv[2])
rows=[];cur={}
for line in open(f'{d}/scdet.txt'):
    m=re.match(r'frame:(\d+)\s+pts:(\d+)\s+pts_time:([\d.]+)',line)
    if m: cur={'frame':int(m[1]),'pts':int(m[2]),'t':float(m[3])}; rows.append(cur); continue
    m=re.match(r'lavfi\.scd\.score=([\d.]+)',line)
    if m: cur['score']=float(m[1])
print(d,'frames scored',len(rows))
import statistics
sc=[r.get('score',0) for r in rows]
for th in (6,8,10,15,20):
    print(' threshold',th,'cuts',sum(1 for s in sc if s>=th))
json.dump(rows,open(f'{d}/scdet_frames.json','w'))
