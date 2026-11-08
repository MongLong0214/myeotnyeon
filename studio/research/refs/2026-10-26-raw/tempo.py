import json,sys
from PIL import Image, ImageChops, ImageStat
def frames(vid):
    meta=json.load(open(f'meta/{vid}.json'))
    fmt=[f for f in meta['formats'] if f['format_id']=='sb0'][0]
    rows,cols,fps,w,h=fmt['rows'],fmt['columns'],fmt['fps'],fmt['width'],fmt['height']
    total=int(meta['duration']*fps)+1; fr=[]
    for k in range(len(fmt['fragments'])):
        s=Image.open(f'sb/sprites/{vid}_{k}.png').convert('L')
        for r in range(rows):
            for c in range(cols):
                if len(fr)<total and (c+1)*w<=s.size[0] and (r+1)*h<=s.size[1]:
                    fr.append(s.crop((c*w,r*h,(c+1)*w,(r+1)*h)))
    return fr,1/fps,meta['duration']
out={}
for vid in sys.argv[1:]:
    fr,dt,dur=frames(vid)
    diffs=[ImageStat.Stat(ImageChops.difference(a,b)).mean[0] for a,b in zip(fr,fr[1:])]
    ch=sum(1 for d in diffs if d>18)
    out[vid]={'sb_frames':len(fr),'interval_s':round(dt,3),'visual_changes_ge':ch,'changes_per_10s':round(ch/dur*10,1)}
    print(vid,dur,len(fr),ch,round(ch/dur*10,1))
json.dump(out,open('tempo.json','w'),indent=1)
