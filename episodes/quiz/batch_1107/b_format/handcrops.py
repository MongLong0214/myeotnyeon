"""handcrops.py <pkg_dir> : crop every visible hand in every frame (from hand_boxes.json + decoded video.mp4) into labelled sheets hands/"""
import sys,json,subprocess,math,os
import numpy as np
from PIL import Image,ImageDraw
P=sys.argv[1];B=json.load(open(f'{P}/hand_boxes.json'));os.makedirs(f'{P}/hands',exist_ok=True)
for f in os.listdir(f'{P}/hands'):os.remove(f'{P}/hands/{f}')
W,H=1080,1920;raw=subprocess.run(['ffmpeg','-v','error','-i',f'{P}/video.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
n=len(raw)//(W*H*3);fr=np.frombuffer(raw,np.uint8).reshape(n,H,W,3)
T=110;cells=[]
for i in range(n):
 for k,(x,y,w,h,pose) in enumerate(B.get(str(i),[])):
  cx,cy=x+w/2,y+h/2;r=max(w,h)*0.75+12
  box=(int(max(0,cx-r)),int(max(0,cy-r)),int(min(W,cx+r)),int(min(H,cy+r)))
  if box[2]-box[0]<4 or box[3]-box[1]<4:continue
  cells.append((i,pose,Image.fromarray(fr[i]).crop(box).resize((T,T))))
cols,rows=18,12;per=cols*rows
for s in range(math.ceil(len(cells)/per)):
 part=cells[s*per:(s+1)*per];im=Image.new('RGB',(cols*T,math.ceil(len(part)/cols)*(T+12)),'#111');d=ImageDraw.Draw(im)
 for j,(i,pose,c) in enumerate(part):
  x=j%cols*T;y=j//cols*(T+12);im.paste(c,(x,y+12));d.text((x+2,y),f'f{i} {pose}',fill='white')
 im.save(f'{P}/hands/hands_{s:02d}_f{part[0][0]:04d}-{part[-1][0]:04d}.png')
print(n,'frames',len(cells),'hand crops',math.ceil(len(cells)/per),'sheets')
