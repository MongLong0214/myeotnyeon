from analyze import *
from scipy.ndimage import uniform_filter1d
for k in VIDEOS:
 d=R/k;m=meta(k);fps=m['fps'];cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));bound=sorted([x for x in json.load(open(d/'reviewed.json')) if x['keep']],key=lambda c:c['frame']);pages=[]
 for start in range(0,len(bound),12):
  group=bound[start:start+12];sheet=Image.new('RGB',(1200,len(group)*136));dr=ImageDraw.Draw(sheet)
  for j,c in enumerate(group):
   y=j*136;dr.text((5,y+2),f"B{start+j+1:03} C{c['candidate']} f{c['frame']} = {c['frame']/fps:.3f}s  {c['transition_type']} / {c['boundary_kind']}   [-3 -2 -1 | 0 +1 +2]",font=ImageFont.truetype(FONT,12),fill='white')
   for off in range(-3,3):sheet.paste(imageframe(cap,c['frame']+off,(200,112)),((off+3)*200,y+23))
  p=d/f'final_boundaries_{start//12+1:02}.jpg';sheet.save(p,quality=90);pages.append(p.name)
 sel=[c for c in bound if c['candidate'] in [2,4,7,12,15,73,105,159,334,337,382,393]] if k=='ref' else [bound[round(i*(len(bound)-1)/11)] for i in range(12)]
 sheet=Image.new('RGB',(1200,136*12));dr=ImageDraw.Draw(sheet)
 for j,c in enumerate(sel):
  y=j*136;dr.text((5,y+2),f"C{c['candidate']} f{c['frame']} {c['frame']/fps:.3f}s / {c['transition_type']} / {c['boundary_kind']}  [-3 -2 -1 | 0 +1 +2]",font=ImageFont.truetype(FONT,13),fill='white')
  for off in range(-3,3):sheet.paste(imageframe(cap,c['frame']+off,(200,112)),((off+3)*200,y+23))
 sheet.save(R/f'{k}_transitions.jpg',quality=90);cap.release();dump(d/'final_strip_pages.json',pages)
 arr=np.load(d/'frame_curves.npz')['data'];tt=np.arange(0,m['duration'],.01);dd=np.interp(tt,arr[:,1],arr[:,2]);smooth=uniform_filter1d(dd,50,mode='nearest')
 csvwrite(d/'frame_diff_0_5s.csv',[{'time_s':float(t),'interpolated_native_mad':float(v),'rolling_0_5s_mean_mad':float(s)} for t,v,s in zip(tt,dd,smooth)])
 # Min_scene_len=1 prevents a 5-fps detector's 4-frame default from hiding sub-second cards.
 if fps<10:
  from scenedetect import FrameTimecode
  from scenedetect.detectors import ContentDetector,AdaptiveDetector
  det={'content':ContentDetector(threshold=20,min_scene_len=1),'adaptive':AdaptiveDetector(adaptive_threshold=2.5,min_scene_len=1,min_content_val=9)};votes={x:[] for x in det};cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));f=0
  while True:
   ok,im=cap.read()
   if not ok:break
   tc=FrameTimecode(f,fps=fps)
   for name,de in det.items():votes[name]+=[t.frame_num for t in de.process_frame(tc,im)]
   f+=1
  cap.release();dump(d/'native_detector_votes.json',votes)
 print(k,'EVIDENCE DONE',flush=True)
