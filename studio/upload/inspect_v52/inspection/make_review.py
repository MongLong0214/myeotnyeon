import cv2, json, sys
from PIL import Image,ImageDraw
from pathlib import Path
name=sys.argv[1]; out=Path('upload/inspect_v52/inspection')
c=cv2.VideoCapture('upload/'+name+'.mp4'); frames=[]
while True:
 ok,f=c.read()
 if not ok:break
 frames.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
spec=json.loads(sys.argv[2])
manifest=[]
for tag,start,end,step,box,cols,rows in spec:
 ids=list(range(start,min(end,len(frames)),step)); w,h=box[2]-box[0],box[3]-box[1]
 for k in range(0,len(ids),cols*rows):
  chunk=ids[k:k+cols*rows]; im=Image.new('RGB',(cols*w,rows*(h+20)),(25,25,25)); d=ImageDraw.Draw(im)
  for j,n in enumerate(chunk):
   x=(j%cols)*w;y=(j//cols)*(h+20)
   im.paste(Image.fromarray(frames[n]).crop(box),(x,y+20));d.text((x+3,y+2),f'{name} f{n} {n/30:.3f}s',fill='white')
  path=out/f'{name}_{tag}_{k//(cols*rows):03}.png';im.save(path)
  manifest.append(dict(path=str(path),frames=chunk,box=box,scale=1))
(out/f'{name}_manifest.json').write_text(json.dumps(manifest,indent=2))
print([(m['path'],m['frames'][0],m['frames'][-1]) for m in manifest])
