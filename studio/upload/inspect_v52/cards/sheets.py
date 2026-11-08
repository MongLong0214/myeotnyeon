from PIL import Image,ImageDraw
from pathlib import Path
import json,sys
O=Path('upload/inspect_v52/cards')
def sheet(q,frames,label,batch=6):
 out=O/q;paths=[]
 for j in range(0,len(frames),batch):
  fs=frames[j:j+batch];im=Image.new('RGB',(1080*3,1952*((len(fs)+2)//3)),(40,40,40));d=ImageDraw.Draw(im)
  for k,f in enumerate(fs):
   x=(k%3)*1080;y=(k//3)*1952
   im.paste(Image.open(out/f'f{f:05d}.png'),(x,y+32));d.text((x+12,y+7),f'{q} f{f:05d} {f/30:.3f}s',fill='white')
  p=out/f'{label}_{j//batch:03d}.png';im.save(p);paths.append(str(p))
 (out/f'{label}_manifest.json').write_text(json.dumps({'frames':frames,'sheets':paths},indent=2));print(label,len(frames),len(paths))
if __name__=='__main__':
 q=sys.argv[1]
 segs={'q015':[(0,85),(86,294),(659,704)],'q012':[(0,60),(61,181),(182,367),(368,438),(439,541),(917,966)],'q016':[(0,81),(82,428),(841,889)],'q017':[(0,60),(61,180),(181,267),(623,671)]}[q]
 frames=[f for a,b in segs for f in list(range(a,b+1,6))+([b] if (b-a)%6 else [])]
 sheet(q,frames,'sample')
