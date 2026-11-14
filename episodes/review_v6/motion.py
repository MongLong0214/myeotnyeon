import re,sys,subprocess,numpy as np,json
mp4,aln=sys.argv[1:3]
rows=[]
for l in open(aln,encoding='utf-8'):
    c=[x.strip() for x in l.strip().strip('|').split('|')]
    if len(c)>=4 and re.match(r'^[A-Z]+\d*_?\d+$',c[0]) and re.match(r'[\d.]+\s*[–-]\s*[\d.]+',c[1]):
        a,b=[float(x) for x in re.split(r'\s*[–-]\s*',c[1])]; rows.append((c[0],a,b,c[3]))
def fr(t):
    # mask subtitle band (bottom 18%) and top label bar (8%)
    r=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',mp4,'-frames:v','1','-vf','scale=160:90,format=gray','-f','rawvideo','-'],capture_output=True).stdout
    return np.frombuffer(r,np.uint8).reshape(90,160)[8:74].astype(float)
static=[];tot=0;st=0
for sid,a,b,desc in rows:
    ts=np.arange(a+0.05,b-0.03,0.25)
    fs=[fr(t) for t in ts]
    m=max(np.abs(fs[i+1]-fs[i]).mean() for i in range(len(fs)-1)) if len(fs)>1 else 0
    tot+=b-a
    if m<0.6: static.append((sid,round(b-a,2),round(m,2),desc[:40])); st+=b-a
print(json.dumps({'shots':len(rows),'dur':round(tot,1),'static_shots':len(static),'static_sec':round(st,1),'static_gt1_5':[s for s in static if s[1]>1.5]},ensure_ascii=False))
