from analyze import *
for k in sys.argv[1:] or ['ours','ours_fast']:
 d=R/k;cs=json.load(open(d/'candidates.json'));cap=cv2.VideoCapture(str(VIDEOS[k]));rows=[]
 if (d/'extra_candidates.json').exists():cs+=json.load(open(d/'extra_candidates.json'))
 for c in cs:
  f=c['frame'];pairs=[]
  for off in [0,1,2]:
   cap.set(cv2.CAP_PROP_POS_FRAMES,f+off-1);o,im=cap.read();cap.set(cv2.CAP_PROP_POS_FRAMES,f+off);o2,im2=cap.read()
   if not o or not o2:continue
   a=cv2.cvtColor(cv2.resize(im,(320,180)),cv2.COLOR_BGR2GRAY)[40:145];b=cv2.cvtColor(cv2.resize(im2,(320,180)),cv2.COLOR_BGR2GRAY)[40:145]
   pts=cv2.goodFeaturesToTrack(a,300,.01,5)
   scale=0;dx=dy=0;good=0
   if pts is not None and len(pts)>8:
    p1,st,err=cv2.calcOpticalFlowPyrLK(a,b,pts,None);q=st.ravel()==1
    if q.sum()>8:
     mat,ins=cv2.estimateAffinePartial2D(pts[q],p1[q],method=cv2.RANSAC,ransacReprojThreshold=.75)
     if mat is not None:scale=(math.hypot(mat[0,0],mat[1,0])-1)*100;dx=float(mat[0,2]);dy=float(mat[1,2]);good=float(ins.mean())
   mad=float(np.abs(a.astype(float)-b).mean());pairs.append({'off':off,'scale':round(scale,3),'dx':round(dx,3),'dy':round(dy,3),'mad':round(mad,3),'inliers':round(good,3)})
  rows.append({**c,'pairs':pairs})
 dump(d/'boundary_jumps.json',rows);cap.release()
 print(k,flush=True)
