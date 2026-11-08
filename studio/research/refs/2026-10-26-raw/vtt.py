import re,sys,os
def parse(path):
    txt=open(path,encoding='utf-8').read()
    cues=[]
    for block in re.split(r'\n\n+',txt):
        m=re.search(r'(\d+):(\d+):(\d+\.\d+) --> (\d+):(\d+):(\d+\.\d+)',block)
        if not m: continue
        t=int(m[1])*3600+int(m[2])*60+float(m[3])
        lines=[re.sub(r'<[^>]+>','',l).strip() for l in block.split('\n')[1:]]
        lines=[l for l in lines if l and '-->' not in l]
        if lines: cues.append((t,lines))
    out=[];seen=set()
    for t,lines in cues:
        for l in lines:
            if l in seen: continue
            seen.add(l); out.append((t,l))
    return out
for vid in sys.argv[1:]:
    p=f'subs/{vid}.ko-orig.vtt'
    if not os.path.exists(p): p=f'subs/{vid}.ko.vtt'
    if not os.path.exists(p): print(vid,'NO SUBS'); continue
    print('##',vid)
    print(' | '.join(f'{t:.1f} {l}' for t,l in parse(p)))
