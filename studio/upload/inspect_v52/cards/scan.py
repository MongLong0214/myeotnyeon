import cv2,numpy as np,json,csv
from pathlib import Path
ROOT=Path('upload')
OUT=ROOT/'inspect_v52/cards'
SEG={'q015':[(0,85),(86,294),(659,704)],'q012':[(0,60),(61,181),(182,367),(368,438),(439,541),(917,966)],'q016':[(0,81),(82,428),(841,889)],'q017':[(0,60),(61,180),(181,267),(623,671)]}
def runs(a):
 r=[]
 for x in sorted(a):
  if r and x==r[-1][1]+1:r[-1][1]=x
  else:r.append([x,x])
 return r
for q,segs in SEG.items():
 out=OUT/q;out.mkdir(exist_ok=True)
 cap=cv2.VideoCapture(str(ROOT/f'v52_{q}.mp4')); prev=None; data=[]; i=0
 targets=set(x for a,b in segs for x in range(max(0,a-3),b+4))
 while True:
  ret,f=cap.read()
  if not ret:break
  g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
  if prev is not None:
   d=cv2.absdiff(g,prev)
   data.append({'f':i,'mad':round(float(d.mean()),4),'p20':round(float((d>20).mean()),6),'maxrow':round(float(d.mean(axis=1).max()),3),'luma':round(float(g.mean()),3),'top':round(float(d[:450].mean()),4),'mid':round(float(d[450:1450].mean()),4),'sub':round(float(d[1450:].mean()),4),'same':bool(np.array_equal(g,prev))})
  if i in targets:cv2.imwrite(str(out/f'f{i:05d}.png'),f)
  prev=g;i+=1
 cap.release()
 (out/'metrics.json').write_text(json.dumps(data))
 print(q,'frames',i,'dimensions',f'{g.shape[1]}x{g.shape[0]}')
 for a,b in segs:
  ds=[x for x in data if a<=x['f']<=min(b+3,i-1)]
  print(a,b,'mad>1',runs([x['f'] for x in ds if x['mad']>1]),'p20>.01',runs([x['f'] for x in ds if x['p20']>.01]))
  print('major',[(x['f'],x['mad'],x['top'],x['mid'],x['sub']) for x in ds if x['mad']>10])
