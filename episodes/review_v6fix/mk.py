import sys,subprocess,re,io,os
from PIL import Image,ImageDraw,ImageFont
src360,src,tag=sys.argv[1:4]; out=os.path.dirname(os.path.abspath(__file__))
r=subprocess.run(['ffmpeg','-i',src360,'-vf',"select='gt(scene,0.25)',showinfo",'-an','-f','null','-'],capture_output=True,text=True).stderr
cuts=[float(x) for x in re.findall(r'pts_time:([\d.]+)',r)]
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src],capture_output=True,text=True).stdout)
b=[0]+cuts+[dur]; shots=[(b[i],b[i+1]) for i in range(len(b)-1) if b[i+1]-b[i]>0.08]
print(tag,len(shots),'shots')
F=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',18); W,H=448,252
def g(t):
    p=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',src,'-frames:v','1','-vf',f'scale={W}:{H}','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
    return Image.open(io.BytesIO(p))
per=7
for pg in range(0,len(shots),per):
    ch=shots[pg:pg+per]; img=Image.new('RGB',(W*3+150,(H+6)*len(ch)),'white'); d=ImageDraw.Draw(img)
    for i,(a,bb) in enumerate(ch):
        y=i*(H+6)
        for j,t in enumerate([a+0.05,(a+bb)/2,bb-0.08]): img.paste(g(t),(j*W,y))
        d.text((W*3+6,y+6),f'#{pg+i+1}\n{a:.2f}\n-{bb:.2f}\n({bb-a:.1f}s)',fill='black',font=F)
    img.save(f'{out}/{tag}_{pg//per+1:02d}.jpg',quality=78)
