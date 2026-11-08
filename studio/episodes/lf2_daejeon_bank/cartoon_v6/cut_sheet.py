"""Decode the delivered MP4: every true last-before / first-after frame."""
import json,subprocess,textwrap,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,cv2
P=Path(__file__).resolve().parent;d=json.loads((P/'episode_data.json').read_text());shots=d['shots'];Q=P/'qa';F=Q/'decoded';F.mkdir(exist_ok=True)
frames=sorted(set([f for s in shots[1:] for f in [s['start']-1,s['start']]]+[s['start']+(s['end']-s['start'])//2 for s in shots]+[31,32,33,34,55,75,84,93]))
def balanced(parts):
 if len(parts)==1:return parts[0]
 m=len(parts)//2;return '('+balanced(parts[:m])+'+'+balanced(parts[m:])+')'
expr=balanced([rf'eq(n\,{f})' for f in frames])
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'lf2_cartoon_v6_1080p.mp4'),'-vf',f'select={expr},scale=640:360','-fps_mode','vfr','-q:v','2',str(F/'frame_%04d.jpg')],check=True)
lookup={f:F/f'frame_{i+1:04d}.jpg' for i,f in enumerate(frames)}
(Q/'decoded_frames.json').write_text(json.dumps({str(k):str(v.relative_to(P)) for k,v in lookup.items()},indent=2))
fontpath='/System/Library/Fonts/Supplemental/Arial Unicode.ttf';big=ImageFont.truetype(fontpath,23);small=ImageFont.truetype(fontpath,14)
def caption(f):
 cs=[c for c in d['captions'] if math.floor(c['startMs']*.03+.5)<=f<math.ceil(c['endMs']*.03)]
 if cs:return cs[0]['text']
 old=[c for c in d['captions'] if c['startMs']*.03<=f]
 return '[자막 없음]'+(' 직전: '+old[-1]['text'] if old else '')
full=Image.new('RGB',(1280,460*(len(shots)-1)),'#191724');fd=ImageDraw.Draw(full);pairs=[];scores=[];pages=[]
for i,(a,b) in enumerate(zip(shots,shots[1:])):
 before=b['start']-1;after=b['start'];im1=Image.open(lookup[before]);im2=Image.open(lookup[after]);y=i*460
 fd.text((15,y+2),f"CUT {i+1:03}  {before}/30 → {after}/30  {a['id']} → {b['id']}  [{after/30:.3f}s]",font=big,fill='white');full.paste(im1,(0,y+35));full.paste(im2,(640,y+35))
 for xx,f in [(10,before),(650,after)]:
  label=caption(f)
  for lineidx,line in enumerate(textwrap.wrap(label,width=30)):fd.text((xx,y+397+lineidx*28),line,font=big,fill='#edff56')
 # A separate compact 8-cut page supports inspection without shrinking the giant sheet.
 if i%8==0:pages.append(Image.new('RGB',(640,8*240),'#191724'))
 page=pages[-1];pd=ImageDraw.Draw(page);py=(i%8)*240
 pd.text((4,py+1),f"{i+1:03} · {after/30:.3f}s · {a['type']} → {b['type']}",font=small,fill='white');page.paste(im1.resize((320,180)),(0,py+20));page.paste(im2.resize((320,180)),(320,py+20))
 for xx,f in [(4,before),(324,after)]:
  for ln,line in enumerate(textwrap.wrap(caption(f),width=23)[:2]):pd.text((xx,py+202+ln*17),line,font=small,fill='#edff56')
 # Local SSIM in the picture region, excluding heading/subtitle bands.
 ar=cv2.cvtColor(np.asarray(im1)[45:297],cv2.COLOR_RGB2GRAY).astype(float);br=cv2.cvtColor(np.asarray(im2)[45:297],cv2.COLOR_RGB2GRAY).astype(float)
 mu1=cv2.GaussianBlur(ar,(11,11),1.5);mu2=cv2.GaussianBlur(br,(11,11),1.5);v1=cv2.GaussianBlur(ar*ar,(11,11),1.5)-mu1*mu1;v2=cv2.GaussianBlur(br*br,(11,11),1.5)-mu2*mu2;cov=cv2.GaussianBlur(ar*br,(11,11),1.5)-mu1*mu2
 ssim=float(np.mean(((2*mu1*mu2+6.5025)*(2*cov+58.5225))/((mu1**2+mu2**2+6.5025)*(v1+v2+58.5225))))
 za=a['staging']['focus']['zoom'];zb=b['staging']['focus']['zoom'];ratio=max(za,zb)/min(za,zb)
 candidate=ssim>.96 and ratio<1.15
 scores.append(dict(cut=i+1,from_shot=a['id'],to_shot=b['id'],ssim=ssim,camera_scale_ratio=ratio,near_identical_candidate=candidate))
 pairs.append(dict(cut=i+1,before_frame=before,after_frame=after,before_subtitle=caption(before),after_subtitle=caption(after),from_shot=a['id'],to_shot=b['id']))
full.save(P/'cut_sheet.jpg',quality=91)
for i,im in enumerate(pages):im.save(Q/f'cut_review_{i+1:02}.jpg',quality=93)
(Q/'cut_pairs.json').write_text(json.dumps(pairs,ensure_ascii=False,indent=2));(Q/'cut_image_scores.json').write_text(json.dumps(scores,indent=2))
print('CUTS',len(pairs),'CANDIDATES',[x for x in scores if x['near_identical_candidate']],flush=True)
