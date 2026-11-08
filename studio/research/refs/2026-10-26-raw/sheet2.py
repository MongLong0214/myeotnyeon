import json, sys, glob, os
from PIL import Image, ImageDraw
def sheet(vid,scale=2,ncol=10):
    meta=json.load(open(f'meta/{vid}.json'))
    fmt=[f for f in meta['formats'] if f['format_id']=='sb0'][0]
    rows,cols,fps,w,h=fmt['rows'],fmt['columns'],fmt['fps'],fmt['width'],fmt['height']
    n=len(fmt['fragments']); fr=[]
    total=int(meta['duration']*fps)+1
    for k in range(n):
        s=Image.open(f'sb/sprites/{vid}_{k}.png').convert('RGB')
        for r in range(rows):
            for c in range(cols):
                if len(fr)>=total: break
                if (c+1)*w>s.size[0] or (r+1)*h>s.size[1]: continue
                fr.append(s.crop((c*w,r*h,(c+1)*w,(r+1)*h)))
    dt=1/fps; W,H=w*scale,h*scale
    nrow=(len(fr)+ncol-1)//ncol
    img=Image.new('RGB',(ncol*W,nrow*(H+14)),'white'); d=ImageDraw.Draw(img)
    for i,f in enumerate(fr):
        x,y=(i%ncol)*W,(i//ncol)*(H+14)
        img.paste(f.resize((W,H)),(x,y+14)); d.text((x+2,y+1),f't={i*dt:.1f}s',fill='black')
    img.save(f'sb/{vid}_sheet.jpg',quality=82)
    return len(fr),round(dt,3),meta['duration']
for vid in sys.argv[1:]:
    try: print(vid,*sheet(vid))
    except Exception as e: print(vid,'ERR',e)
