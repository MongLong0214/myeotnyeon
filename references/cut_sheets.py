import cv2,json,sys,numpy as np
from PIL import Image,ImageDraw,ImageFont
d=sys.argv[1];fps=float(sys.argv[2])
rows=json.load(open(f'{d}/scdet_frames.json'))
sc=np.array([r.get('score',0) for r in rows])
cand=[i for i in range(1,len(sc)) if sc[i]>=5 and sc[i]==sc[max(0,i-4):i+5].max()]
json.dump([{'frame':i,'t':rows[i]['t'],'pts':rows[i]['pts'],'score':sc[i]} for i in cand],open(f'{d}/cut_candidates.json','w'))
print(d,'candidates',len(cand))
cap=cv2.VideoCapture(f'{d}/proxy.mp4')
need=set();[need.update({c-1,c}) for c in cand]
frames={};i=0
while True:
    ok,f=cap.read()
    if not ok:break
    if i in need: frames[i]=cv2.cvtColor(cv2.resize(f,(300,int(300*f.shape[0]/f.shape[1]))),cv2.COLOR_BGR2RGB)
    i+=1
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
per=12;cols=3
import os;os.makedirs(f'{d}/sheets',exist_ok=True)
H=frames[cand[0]].shape[0]
for s in range(0,len(cand),per):
    chunk=cand[s:s+per];rws=(len(chunk)+cols-1)//cols
    sheet=Image.new('RGB',(cols*620,rws*(H+24)),(30,30,30));dr=ImageDraw.Draw(sheet)
    for k,c in enumerate(chunk):
        x=(k%cols)*620;y=(k//cols)*(H+24)
        sheet.paste(Image.fromarray(frames[c-1]),(x,y+20));sheet.paste(Image.fromarray(frames[c]),(x+305,y+20))
        t=c/fps;dr.text((x+2,y+2),f'#{s+k:03d} f{c} {int(t//60):02d}:{t%60:05.2f} sc{sc[c]:.1f}',fill=(255,230,0),font=font)
    sheet.save(f'{d}/sheets/cuts_{s//per:02d}.jpg',quality=82)
print('sheets',(len(cand)+per-1)//per)
