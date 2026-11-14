from PIL import Image,ImageDraw
from pathlib import Path
import json,sys,cv2
O=Path('/Users/isaac/projects/verdict-kr/work/upload/inspect_v52/cards')
def make(q,ranges,label='trans',crop=(0,100,1080,1700),batch=12):
 fs=sorted(set(f for a,b in ranges for f in range(a,b+1)));p=O/q;paths=[]
 w=crop[2]-crop[0];h=crop[3]-crop[1]
 for j in range(0,len(fs),batch):
  frames=fs[j:j+batch];im=Image.new('RGB',(w*4,(h+28)*((len(frames)+3)//4)),(40,40,40));d=ImageDraw.Draw(im)
  for k,f in enumerate(frames):
   x=(k%4)*w;y=(k//4)*(h+28)
   
   src=p/f'f{f:05d}.png'
   if not src.exists():
    cap=cv2.VideoCapture(str(O.parent.parent/f'v52_{q}.mp4'));cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,arr=cap.read();cap.release();assert ok;cv2.imwrite(str(src),arr)
   im.paste(Image.open(src).crop(crop),(x,y+28));d.text((x+10,y+5),f'{q} f{f:05d}',fill='white')
  dest=p/f'{label}_{j//batch:03d}.png';im.save(dest);paths.append(str(dest))
 (p/f'{label}_manifest.json').write_text(json.dumps({'ranges':ranges,'frames':fs,'crop':crop,'sheets':paths},indent=2));print(q,label,len(fs),len(paths),flush=True)
if __name__=='__main__':
 q=sys.argv[1]
 if q=='q015':make(q,[(0,6),(58,103),(118,127),(133,139),(152,161),(186,195),(201,255),(273,284),(285,298),(656,663)])
