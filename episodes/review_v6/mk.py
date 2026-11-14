import re,sys,subprocess,os
from PIL import Image,ImageDraw,ImageFont
mp4,aln,tag=sys.argv[1:4]
out=os.path.dirname(os.path.abspath(__file__))
rows=[]
for l in open(aln,encoding='utf-8'):
    c=[x.strip() for x in l.strip().strip('|').split('|')]
    if len(c)>=4 and re.match(r'^[A-Z]+\d*_?\d+$',c[0]) and re.match(r'[\d.]+\s*[–-]\s*[\d.]+',c[1]):
        a,b=[float(x) for x in re.split(r'\s*[–-]\s*',c[1])]
        rows.append((c[0],a,b,c[2]))
print(tag,len(rows),'shots')
F=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',17)
W,H=384,216
def grab(t):
    p=subprocess.run(['ffmpeg','-v','error','-ss',f'{max(t,0):.3f}','-i',mp4,'-frames:v','1','-vf',f'scale={W}:{H}','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
    import io; return Image.open(io.BytesIO(p))
per=8
for pg in range(0,len(rows),per):
    chunk=rows[pg:pg+per]
    img=Image.new('RGB',(W*3+520,(H+6)*len(chunk)),'white');d=ImageDraw.Draw(img)
    for i,(sid,a,b,txt) in enumerate(chunk):
        y=i*(H+6)
        for j,t in enumerate([a+0.07,(a+b)/2,b-0.07]):
            img.paste(grab(t),(j*W,y))
        x=W*3+8; lines=[f'{sid} {a:.2f}-{b:.2f}']; s=txt
        while s: lines.append(s[:26]); s=s[26:]
        for k,ln in enumerate(lines): d.text((x,y+4+k*22),ln,fill='black',font=F)
    img.save(f'{out}/{tag}_{pg//per+1:02d}.jpg',quality=80)
