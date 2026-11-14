import cv2,csv,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
W=Path('.');O=W/'research/format_v4/missing_axes_work';R=W/'research/format_v4/extol_all'
# collect the 160 saved representative frames as individual OCR inputs
for v in ['H_GaGKQp17k','w_LJ_GQObic','C1eXfwC7uAw','_qQK1LZpyJI']:
 d=O/v;d.mkdir(exist_ok=True)
 for r in json.load(open(O/f'{v}_sample.json')):
  i=r['shot']-1;im=Image.open(R/v/f'shots_{i//36+1:02}.jpg');x=i%6*240;y=i%36//6*157+22;im.crop((x,y,x+240,y+135)).resize((1280,720)).save(d/f'{r["sample"]:02}.jpg',quality=95)
cap=cv2.VideoCapture('episodes/v4/n18/out/n18_v3_full_720p.mp4');fps=cap.get(cv2.CAP_PROP_FPS);n=cap.get(cv2.CAP_PROP_FRAME_COUNT)
import re
pts=[float(t) for t in re.findall(r'pts_time:([0-9.]+)',open(O/'n18_native_cuts.txt').read())]
starts=[0]+[round(t*fps) for t in pts if 0<t*fps<n-1];ends=starts[1:]+[n]

# use the saved boundaries, with native N18 frame pairs inside each sampled shot
idx=np.linspace(0,len(starts)-1,40).round().astype(int);rows=[];canvas=Image.new('RGB',(1200,8*159));draw=ImageDraw.Draw(canvas);(O/'N18').mkdir(exist_ok=True)
for j,i in enumerate(idx):
 a=starts[i];z=ends[i];mid=(a+z)/2
 cap.set(0 if False else cv2.CAP_PROP_POS_FRAMES,int(mid));ok,im=cap.read();assert ok
 Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).save(O/'N18'/f'{j+1:02}.jpg',quality=95)
 tile=Image.fromarray(cv2.cvtColor(cv2.resize(im,(240,135)),cv2.COLOR_BGR2RGB));canvas.paste(tile,((j%5)*240,(j//5)*159+22));draw.text(((j%5)*240+3,(j//5)*159+3),f'{j+1:02} S{i+1} {a/fps:.1f}s',fill='white')
 flows=[]
 for t in np.linspace(a+min(4,(z-a)/10),max(a+1,z-min(4,(z-a)/10)-max(2,round(fps*.25))),6):
  pair=[]
  for fr in [t,t+max(2,round(fps*.25))]:
   cap.set(cv2.CAP_PROP_POS_FRAMES,int(fr));ok,x=cap.read()
   if ok:pair.append(cv2.cvtColor(cv2.resize(x,(320,180)),cv2.COLOR_BGR2GRAY)[:133])
  if len(pair)==2:
   f=cv2.calcOpticalFlowFarneback(*pair,None,.5,3,21,3,5,1.2,0);flows.append(float(np.linalg.norm(f,axis=2).mean())/(max(2,round(fps*.25))/fps))
 rows.append(dict(sample=j+1,shot=int(i+1),start_s=a/fps,end_s=z/fps,duration_s=(z-a)/fps,flow=float(np.mean(flows))))
canvas.save(O/'N18_40.jpg',quality=92);(O/'N18_sample.json').write_text(json.dumps(rows,indent=2));print('N18',fps,n,len(starts))
