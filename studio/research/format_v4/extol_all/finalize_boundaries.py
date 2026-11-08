import json,csv,sys,math
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import measure_all as a
C=json.loads((R/'manual_visual.json').read_text());inv=json.loads((R/'inventory.json').read_text())
def read(p):return list(csv.DictReader(p.open()))
for vid in inv['long']:
 d=R/vid
 if not (d/'boundaries.csv').exists():continue
 m=json.loads((d/'media.json').read_text());fps=m['fps'];old=read(d/'boundaries.csv');byframe={int(x['frame']):dict(x) for x in old}
 if vid=='E_DrBRjGAQI':
  for t in [196.68,327.28]:byframe[round(t*fps)]={'frame':round(t*fps),'time_s':t,'boundary_method':'manually recovered chapter transition from ASR pause sheet and frame-difference curve','confidence':.9}
 if vid=='_qQK1LZpyJI':byframe.pop(round(152.24*fps),None)
 prior={}
 if vid=='w_LJ_GQObic':
  src=read(R.parent/'ref_extol/ref/shots.csv')
  for x in src[1:]:prior[int(x['start_frame'])]={'type':x['transition_type'],'frames':None if x['transition_type']=='other' else 0}
 elif vid=='OwQm8ZIZfiQ':
  for x in read(R.parent/'ref_extol2/cuts.csv'):prior[int(x['frame'])]={'type':{'hardcut':'hard','embedded-footage-hardcut':'hard','cross-dissolve':'dissolve'}.get(x['transition_type'],x['transition_type']),'frames':int(x['transition_duration_frames'])}
 override=C.get(vid,{}).get('transition_overrides',[])
 if vid=='_qQK1LZpyJI':override=[dict(time_s=t,type='zoom-through',duration_frames=8,duration_status='visual sample estimate ±3 frames; masked radial blur into black chapter card') for t in [160.68,273.24]]
 bounds=[]
 for fr,row in sorted(byframe.items()):
  typ=prior.get(fr,{}).get('type','hard');nf=prior.get(fr,{}).get('frames',0);review='prior full native-boundary visual review' if vid in ['w_LJ_GQObic','OwQm8ZIZfiQ'] else 'hard family visually confirmed on sampled strips; unviewed individual boundaries remain detector estimates';stat='hard jump 0 blended frames, onset resolution 1 native frame' if nf==0 else 'prior visual estimate' if nf is not None else 'other effect; duration not isolated'
  for x in override:
   if abs(fr/fps-x['time_s'])<.08:typ=x['type'];nf=x['duration_frames'];stat=x['duration_status'];review='transition family confirmed by visual sample'
  bounds.append({'index':len(bounds)+1,'frame':fr,'time_s':fr/fps,'transition_type':typ,'transition_duration_frames':nf,'transition_duration_s':None if nf is None else nf/fps,'duration_status':stat,'confidence':row.get('confidence',.75),'boundary_method':row.get('boundary_method','detector ensemble'),'visual_confirmation':review})
 a.csvout(d/'boundaries.csv',bounds);frames=[0]+[x['frame'] for x in bounds];ends=frames[1:]+[m['frames']]
 cuts=[{'index':i+1,'start_frame':st,'end_frame':en,'start_s':st/fps,'end_s':en/fps,'duration_s':(en-st)/fps,'transition_type':'start' if i==0 else bounds[i-1]['transition_type'],'transition_duration_frames':None if i==0 else bounds[i-1]['transition_duration_frames'],'confidence':1 if i==0 else bounds[i-1]['confidence']} for i,(st,en) in enumerate(zip(frames,ends))];a.csvout(d/'cuts.csv',cuts);a.dump(d/'reviewed.json',[{'frame':f,'keep':True} for f in frames[1:]])
 if vid in ['E_DrBRjGAQI','_qQK1LZpyJI'] and (d/'flow.csv').exists():(d/'flow.csv').unlink()
 # Re-label strips after visual review so automatic false dissolve/fade labels are not delivered as truth.
 for p in d.glob('boundaries_*.jpg'):p.unlink()
 cap=cv2.VideoCapture(str(d/'analysis_proxy.mp4'))
 for st in range(0,len(bounds),12):
  group=bounds[st:st+12];canvas=Image.new('RGB',(1440,124*len(group)));dr=ImageDraw.Draw(canvas)
  for i,c in enumerate(group):
   y=i*124;dr.text((3,y+2),f"B{c['index']:03} {c['time_s']:.3f}s {c['transition_type']}",font=ImageFont.truetype(a.FONT,12),fill='white')
   for j,off in enumerate([-round(.3*fps),-3,-2,-1,0,1,2,round(.3*fps)]):canvas.paste(a.frame(cap,c['frame']+off,(180,102)),(j*180,y+22))
  canvas.save(d/f'boundaries_{st//12+1:02}.jpg',quality=86)
 if vid in C:
  a.sheet_frames(cap,C[vid]['key_times_s'],fps,d/'frames_key.jpg',4,(320,180))
  keydir=d/'key_frames';keydir.mkdir(exist_ok=True)
  for i,t in enumerate(C[vid]['key_times_s']):a.frame(cap,t*fps,(480,270)).save(keydir/f'{i+1:02}_{t:.2f}s.jpg',quality=86)
 if vid in ['E_DrBRjGAQI','_qQK1LZpyJI']:
  for p in d.glob('shots_*.jpg'):p.unlink()
  for st in range(0,len(cuts),36):
   cs=cuts[st:st+36];a.sheet_frames(cap,[(x['start_s']+x['end_s'])/2 for x in cs],fps,d/f'shots_{st//36+1:02}.jpg',6,(240,135),[f"S{x['index']:03} {x['start_s']:.2f}-{x['end_s']:.2f}" for x in cs])
 cap.release();print(vid,len(cuts),flush=True)
