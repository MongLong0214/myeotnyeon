import sys,subprocess,io,os
from PIL import Image,ImageDraw,ImageFont
src,tag,step=sys.argv[1],sys.argv[2],float(sys.argv[3]); out=os.path.dirname(os.path.abspath(__file__))
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src],capture_output=True,text=True).stdout)
W,H,C,R=480,270,4,5; F=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',22)
ts=[i*step+0.5 for i in range(int((dur-0.5)/step)+1)]
tmp=f'/tmp/_{tag}'; os.makedirs(tmp,exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-y','-ss','0.5','-i',src,'-vf',f'fps=1/{step},scale={W}:{H}',f'{tmp}/%04d.png'])
fs=sorted(os.listdir(tmp))
for p in range(0,len(fs),C*R):
    img=Image.new('RGB',(W*C,H*R),'black'); d=ImageDraw.Draw(img)
    for k,f in enumerate(fs[p:p+C*R]):
        x,y=(k%C)*W,(k//C)*H; img.paste(Image.open(f'{tmp}/{f}'),(x,y))
        t=0.5+(p+k)*step; d.rectangle([x,y,x+78,y+28],fill='red'); d.text((x+4,y+2),f'{int(t//60)}:{t%60:04.1f}',fill='white',font=F)
    img.save(f'{out}/{tag}_g{p//(C*R)+1:02d}.jpg',quality=80)
print(tag,len(fs))
