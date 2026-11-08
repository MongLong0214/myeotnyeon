import json,csv,cv2,numpy as np
from pathlib import Path
from PIL import Image
O=Path('research/format_v4/missing_axes_work');R=Path('research/format_v4/extol_all');cv2.setNumThreads(1)
for v in ['H_GaGKQp17k','w_LJ_GQObic','C1eXfwC7uAw','_qQK1LZpyJI','N18']:
 rows=json.load(open(O/f'{v}_sample.json'));res=[]
 if v=='N18':cap=cv2.VideoCapture('episodes/v4/n18/out/n18_v3_full_720p.mp4')
 for r in rows:
  i=r['shot']-1;dt=8/30
  if v=='N18':
   pair=[]
   for t in [r['end_s']-.3,r['end_s']-1/30]:
    cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*30));ok,im=cap.read();assert ok;pair.append(cv2.resize(im,(180,102)))
  else:
   sh=np.array(Image.open(R/v/f'boundaries_{i//12+1:02}.jpg'));y=i%12*124+22;cols=[0,540] if float(r['duration_s'])>=.3 else [180,540];dt=8/30 if cols[0]==0 else 2/30;pair=[cv2.cvtColor(sh[y:y+102,x:x+180],cv2.COLOR_RGB2BGR) for x in cols]
  a,b=[cv2.cvtColor(cv2.resize(im,(320,180)),cv2.COLOR_BGR2GRAY)[:133] for im in pair]
  f=cv2.calcOpticalFlowFarneback(a,b,None,.5,3,15,3,5,1.2,0);speed=float(np.linalg.norm(f,axis=2).mean()/dt)
  res.append(dict(sample=r['sample'],shot=r['shot'],end_pair_flow_px_per_s_320w=speed,visible_motion_proxy=speed>=2))
 (O/f'{v}_motion.json').write_text(json.dumps(res,indent=2));print(v,sum(x['visible_motion_proxy'] for x in res),[(x['sample'],round(x['end_pair_flow_px_per_s_320w'],1)) for x in res])
