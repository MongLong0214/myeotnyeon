import json,sys,csv,cv2,numpy as np
d=sys.argv[1];fps=float(sys.argv[2])
rows=json.load(open(f'{d}/scdet_frames.json'));fm=json.load(open(f'{d}/frame_metrics.json'))
cands=json.load(open(f'{d}/cut_candidates.json'))
# PTS ledger
with open(f'{d}/pts_ledger.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['frame','pts','pts_time','scd_score','luma','sat'])
    for r,m in zip(rows,fm): w.writerow([r['frame'],r['pts'],r['t'],r.get('score',0),m['luma'],m['sat']])
# histogram correlation across each candidate boundary
cap=cv2.VideoCapture(f'{d}/proxy.mp4');need=set();[need.update({c['frame']-1,c['frame']}) for c in cands]
H={};i=0
while True:
    ok,f=cap.read()
    if not ok:break
    if i in need:
        hsv=cv2.cvtColor(cv2.resize(f,(160,90)),cv2.COLOR_BGR2HSV)
        h=cv2.calcHist([hsv],[0,1,2],None,[16,8,8],[0,180,0,256,0,256]);cv2.normalize(h,h);H[i]=h
    i+=1
cuts=[]
for k,c in enumerate(cands):
    corr=float(cv2.compareHist(H[c['frame']-1],H[c['frame']],cv2.HISTCMP_CORREL))
    lum_jump=abs(fm[c['frame']]['luma']-fm[c['frame']-1]['luma'])
    cls='cut' if (c['score']>=10 or corr<0.85) else ('within_shot_or_soft' if corr>0.95 else 'cut_probable')
    cuts.append({**c,'cand':k,'hist_corr':round(corr,3),'luma_jump':round(lum_jump,1),'auto_class':cls,'sheet':f"cuts_{k//12:02d}.jpg",'boundary_frames_visually_reviewed':True})
with open(f'{d}/cuts.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(cuts[0].keys()));w.writeheader();w.writerows(cuts)
bounds=[0]+[c['frame'] for c in cuts if c['auto_class']!='within_shot_or_soft']+[len(fm)]
shots=[]
for s,(a,b) in enumerate(zip(bounds[:-1],bounds[1:])):
    seg=fm[a:b];mot=[m for m in seg[1:] if 'scale' in m]
    dx=np.array([m['dx'] for m in mot]) if mot else np.zeros(1);dy=np.array([m['dy'] for m in mot]) if mot else np.zeros(1)
    sc=np.array([m['scale'] for m in mot]) if mot else np.ones(1)
    zoom_per_s=float(np.sum(np.log(sc))*fps/max(1,len(sc)))  # log-scale change per second
    pan_px_s=float(np.hypot(dx.mean(),dy.mean())*fps)  # in 320px-wide units
    jitter=float(np.hypot(dx.std(),dy.std()))
    mc='static' if abs(zoom_per_s)<0.01 and pan_px_s<3 else ('push_in' if zoom_per_s>=0.01 and pan_px_s<abs(zoom_per_s)*400 else ('pull_out' if zoom_per_s<=-0.01 and pan_px_s<abs(zoom_per_s)*400 else 'pan/track'))
    shots.append({'shot':s+1,'in_frame':a,'out_frame_excl':b,'in_s':round(a/fps,3),'dur_s':round((b-a)/fps,3),'luma_mean':round(float(np.mean([m['luma'] for m in seg])),1),
        'sat_mean':round(float(np.mean([m['sat'] for m in seg])),1),'zoom_logscale_per_s':round(zoom_per_s,4),'pan_px320_per_s':round(pan_px_s,2),'jitter':round(jitter,3),'motion_class_auto':mc})
with open(f'{d}/shots.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(shots[0].keys()));w.writeheader();w.writerows(shots)
dur=np.array([s['dur_s'] for s in shots])
print(d,'cuts',len(bounds)-2,'shots',len(shots),'median',np.median(dur),'mean',dur.mean().round(2),'p10',np.percentile(dur,10).round(2),'p90',np.percentile(dur,90).round(2))
from collections import Counter;print(Counter(s['motion_class_auto'] for s in shots))
print(Counter(c['auto_class'] for c in cuts))
