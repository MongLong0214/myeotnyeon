from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import label

stage=Path(__file__).parent
old=stage.parent/'.sol_v3b.sBcZnIjT/frames_final_hq_v3b_raw'
new={p.name:p for q in stage.glob('open_*_*.*') for p in q.glob('f_*.png')}
frames=[f for f in (0,6,12,18,24,30,36,42,48,54,57,58,59,60) if f'f_{f:04}.png' in new]
out=Image.new('RGB',(3*450,len(frames)*350)); d=ImageDraw.Draw(out)
for f in range(61):
 name=f'f_{f:04}.png'
 if name not in new: continue
 pre=np.asarray(Image.open(old/name).convert('RGBA')); post=np.asarray(Image.open(new[name]).convert('RGBA'))
 a=pre.astype('int16'); b=post.astype('int16'); delta=np.abs(a-b)
 # High-contrast RGB at opaque pixels with true alpha, or old opaque geometry removed from the silhouette.
 changed=(a[...,3]>150)&((b[...,3]<100)|((a[...,:3]-b[...,:3]).mean(2)>35))
 cc,n=label(changed); hist=np.bincount(cc.ravel()); hist[0]=0; largest=hist.argmax(); ys,xs=np.where(cc==largest)
 box=(xs.min(),ys.min(),xs.max(),ys.max()) if len(xs) else None
 print(f,changed.sum(),hist[largest],box, tuple(pre[round(ys.mean()),round(xs.mean())]) if len(xs) else None)
 if f not in frames: continue
 row=frames.index(f); x0=int(395+f*4.0); y0=int(max(0,f-25)*2.2); box=(x0-35,y0,x0+415,y0+333)
 def flat(p):
  im=Image.new('RGBA',(1080,880),'#13191b'); im.alpha_composite(Image.fromarray(p)); return im
 ims=[flat(pre),flat(post),Image.fromarray(np.where(changed,255,np.clip(delta.mean(2)*2,0,255)).astype('uint8'))]
 for i,im in enumerate(ims):
  out.paste(im.crop(box).convert('RGB'),(i*450,row*350+17));d.text((i*450+5,row*350),f'f{f} { ["v3c", "corrected", "high contrast delta"][i]}',fill='white')
out.save(stage/'raw_compare.png')
