import cv2,numpy as np,json,sys
d=sys.argv[1]
cap=cv2.VideoCapture(f'{d}/proxy.mp4')
prev=None;out=[];i=0
lk=dict(winSize=(21,21),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,20,0.03))
while True:
    ok,f=cap.read()
    if not ok: break
    small=cv2.resize(f,(320,int(320*f.shape[0]/f.shape[1])))
    g=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
    hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
    rec={'f':i,'luma':round(float(g.mean()),2),'luma_p95':int(np.percentile(g,95)),'sat':round(float(hsv[...,1].mean()),2),
         'b':round(float(small[...,0].mean()),1),'g':round(float(small[...,1].mean()),1),'r':round(float(small[...,2].mean()),1)}
    if prev is not None:
        pts=cv2.goodFeaturesToTrack(prev,200,0.01,7)
        if pts is not None and len(pts)>=12:
            nxt,st,_=cv2.calcOpticalFlowPyrLK(prev,g,pts,None,**lk)
            good=st.ravel()==1
            if good.sum()>=12:
                M,inl=cv2.estimateAffinePartial2D(pts[good],nxt[good],method=cv2.RANSAC,ransacReprojThreshold=2.0)
                if M is not None:
                    s=float(np.hypot(M[0,0],M[1,0]));rot=float(np.degrees(np.arctan2(M[1,0],M[0,0])))
                    rec.update({'dx':round(float(M[0,2]),3),'dy':round(float(M[1,2]),3),'scale':round(s,5),'rot':round(rot,4),'inl':int(inl.sum())})
    out.append(rec);prev=g;i+=1
json.dump(out,open(f'{d}/frame_metrics.json','w'))
print(d,len(out))
