import email, json, sys, io, os, glob
from PIL import Image, ImageDraw
def frames_for(vid):
    meta=json.load(open(f'meta/{vid}.json'))
    fmt=[f for f in meta['formats'] if f['format_id']=='sb0'][0]
    rows,cols,fps=fmt['rows'],fmt['columns'],fmt['fps']
    msg=email.message_from_binary_file(open(f'sb/{vid}.mhtml','rb'))
    sprites=[]
    for k,p in enumerate([p for p in msg.walk() if p.get_content_type().startswith('image/')]):
        b=p.get_payload(decode=True)
        if b[:4]==b'RIFF':
            need=int.from_bytes(b[4:8],'little')+8
            if len(b)<need: b=b+b'\n'*(need-len(b))
        try:
            im=Image.open(io.BytesIO(b)); im.load()
        except Exception:
            import subprocess,tempfile
            src=tempfile.mktemp(suffix='.webp'); dst=src[:-5]+'.png'
            open(src,'wb').write(b); subprocess.run(['sips','-s','format','png',src,'--out',dst],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            im=Image.open(dst); im.load()
        sprites.append(im.convert('RGB'))
    w,h=fmt['width'],fmt['height']
    out=[]
    n_total=int(round(meta['duration']*fps))+1
    for s in sprites:
        for r in range(rows):
            for c in range(cols):
                if len(out)>=n_total: break
                fr=s.crop((c*w,r*h,(c+1)*w,(r+1)*h))
                if fr.getbbox() is None: continue
                out.append(fr)
    return out,1/fps,meta['duration']
def sheet(vid,scale=2,ncol=10):
    fr,dt,dur=frames_for(vid)
    w,h=fr[0].size; W,H=w*scale,h*scale
    nrow=(len(fr)+ncol-1)//ncol
    img=Image.new('RGB',(ncol*W,nrow*(H+14)),'white'); d=ImageDraw.Draw(img)
    for i,f in enumerate(fr):
        x,y=(i%ncol)*W,(i//ncol)*(H+14)
        img.paste(f.resize((W,H)),(x,y+14)); d.text((x+2,y+1),f't={i*dt:.1f}s',fill='black')
    img.save(f'sb/{vid}_sheet.jpg',quality=85)
    return len(fr),dt,dur
for vid in sys.argv[1:]:
    try: print(vid,*sheet(vid))
    except Exception as e: print(vid,'ERR',e)
