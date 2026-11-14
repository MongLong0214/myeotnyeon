import re,sys
s=open(sys.argv[1]).read()
print('transforms',s.count('transform='),'clips',s.count('clip-path='),'use',s.count('<use'))
for i,m in enumerate(re.finditer(r'<path ([^>]*?)d="([^"]+)"([^>]*)/>',s)):
    attrs=m.group(1)+m.group(3); d=m.group(2)
    n=[float(x) for x in re.findall(r'-?\d+\.?\d*',d)]
    xs=n[0::2]; ys=n[1::2]
    f=re.search(r'fill="([^"]+)"',attrs); st=re.search(r'stroke="([^"]+)"',attrs)
    def hx(c):
        if not c: return '-'
        p=re.findall(r'[\d.]+',c.group(1)); 
        return '#'+''.join('%02x'%round(float(v)*2.55) for v in p[:3]) if len(p)>=3 else c.group(1)
    if i<int(sys.argv[2]) : print(i,hx(f),hx(st),'bbox %d,%d-%d,%d'%(min(xs),min(ys),max(xs),max(ys)),len(d))
