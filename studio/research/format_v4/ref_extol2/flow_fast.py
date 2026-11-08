from analyze import *
from collections import defaultdict
d=R/'ref';m=meta('ref');fps=m['fps'];shots=list(csv.DictReader((R/'shots.csv').open()));wanted={};groups=defaultdict(list)
for s in shots:
 i=int(s['shot_id']);a=int(s['start_frame']);b=int(s['end_frame_exclusive']);pairs=[]
 for pos in np.linspace(a+max(2,round(.15*fps)),b-1-max(2,round(.15*fps)),min(12,max(1,int((b-a)/fps*3)))):
  f0=int(pos);f1=min(b-2,f0+max(1,round(.2*fps)))
  if f1<=f0:continue
  pairs.append((f0,f1));wanted[f0]=None;wanted[f1]=None
 groups[i]=pairs
p=subprocess.Popen(['ffmpeg','-v','error','-i',str(R/'tmp/ref_proxy.mp4'),'-vf','scale=320:180','-an','-f','rawvideo','-pix_fmt','gray','-'],stdout=subprocess.PIPE)
fr=0
while True:
 b=p.stdout.read(320*180)
 if len(b)<320*180:break
 if fr in wanted:wanted[fr]=np.frombuffer(b,np.uint8).reshape(180,320)[:150].copy()
 fr+=1
p.wait();out=[]
for s in shots:
 si=int(s['shot_id']);vals=[];dxs=[];dys=[];scales=[];inliers=[]
 for f0,f1 in groups[si]:
  g0,g1=wanted[f0],wanted[f1];dt=(f1-f0)/fps;fl=cv2.calcOpticalFlowFarneback(g0,g1,None,.5,3,15,3,5,1.2,0);vals.append(float(np.linalg.norm(fl,axis=2).mean()/dt));dxs.append(float(np.median(fl[:,:,0])/dt));dys.append(float(np.median(fl[:,:,1])/dt));pts=cv2.goodFeaturesToTrack(g0,500,.01,6)
  if pts is not None and len(pts)>8:
   p1,st,err=cv2.calcOpticalFlowPyrLK(g0,g1,pts,None);q=st.ravel()==1
   if q.sum()>8:
    mat,ins=cv2.estimateAffinePartial2D(pts[q],p1[q],method=cv2.RANSAC,ransacReprojThreshold=1.5)
    if mat is not None:scales.append((math.hypot(mat[0,0],mat[1,0])-1)/dt*100);inliers.append(float(ins.mean()))
 mean=float(np.mean(vals)) if vals else 0;dx=float(np.median(dxs)) if dxs else 0;dy=float(np.median(dys)) if dys else 0;scale=float(np.median(scales)) if scales else 0
 move=('push-in' if scale>0 else 'pull-out') if abs(scale)>.25 else ('pan' if abs(dx)>abs(dy) else 'tilt') if math.hypot(dx,dy)>.7 else 'parallax' if mean>3 else 'static'
 row={**s,'camera_move':move,'flow_mean_px_per_s_at_320w':mean,'flow_median_dx_px_per_s':dx,'flow_median_dy_px_per_s':dy,'flow_direction_degrees':math.degrees(math.atan2(dy,dx)),'scale_change_pct_per_s':scale,'affine_inlier_fraction':float(np.mean(inliers)) if inliers else None,'flow_pair_count':len(vals)};out.append(row)
csvwrite(R/'shots.csv',out);csvwrite(d/'flow.csv',out)
dump(R/'flow_summary.json',{'counts':dict(__import__('collections').Counter(x['camera_move'] for x in out)),'median_mean_flow_px_s_at_320w':float(np.median([x['flow_mean_px_per_s_at_320w'] for x in out])),'abs_scale_pct_s_median':float(np.median([abs(x['scale_change_pct_per_s']) for x in out])),'method':'Same ref1 Farneback + LK/RANSAC affine, top150 of180px, dt~0.2s, <=12 pairs/shot. Single sequential decode replaces random seeks; image motion proxy, not proof of actual camera trajectory.'})
print('done',len(out))
