"""Conservative local cartoon silhouettes. A negative detection remains unknown."""
import cv2
import numpy as np

def _silhouettes(path,threshold):
    im=cv2.imread(str(path));h,w=im.shape[:2]
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    dark=cv2.inRange(gray,0,threshold)
    dark[:round(h*.18)]=0;dark[round(h*.82):]=0
    contours,_=cv2.findContours(dark,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    hits=[]
    for cnt in contours:
        x,y,bw,bh=cv2.boundingRect(cnt);area=cv2.contourArea(cnt)
        if not (w*.04<=bw<=w*.18 and h*.035<=bh<=h*.24 and .65<=bw/bh<=1.5 and .5<=area/(bw*bh)<=.95):continue
        # Heads are rounded/polygonal; text rectangles/windows are not heads.
        poly=cv2.approxPolyDP(cnt,cv2.arcLength(cnt,True)*.025,True)
        if len(poly)<6:continue
        # A torso must extend below the head, followed by two separate legs.
        cx=x+bw/2;bottom=min(round(h*.82),round(y+bh*3.4))
        if bottom<y+bh*2:continue
        roi=dark[y+bh:bottom,max(0,round(cx-bw*.65)):min(w,round(cx+bw*.65))]
        if roi.size==0:continue
        rows=(roi>0).mean(axis=1)
        if (rows>.035).mean()<.6:continue
        # Dark outlines at two feet, with a lighter gap between them.
        legs=False
        for yy in range(round(y+bh*1.9),bottom):
            r=dark[yy,max(0,round(cx-bw*.5)):min(w,round(cx+bw*.5))]>0
            edges=np.diff(np.r_[False,r,False].astype(int));runs=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))
            if 2<=len(runs)<=4 and any(a[1]<len(r)*.6 and b[0]>len(r)*.35 for a,b in zip(runs,runs[1:])):legs=True;break
        if legs:hits.append(dict(x=x/w,y=y/h,w=bw/w,h=(bottom-y)/h,head=[x/w,y/h,bw/w,bh/h]))
    unique=[]
    for box in sorted(hits,key=lambda b:-b['w']):
        if not any(abs(box['x']-b['x'])<box['w']*.5 and abs(box['y']-b['y'])<box['w']*.5 for b in unique):unique.append(box)
    return unique


def silhouettes(path):
    # Two ink thresholds cover dark masks and light-skinned outlined faces.
    hits=_silhouettes(path,30)+_silhouettes(path,45)
    unique=[]
    for box in hits:
        if not any(abs(box['x']-b['x'])<box['w']*.5 and abs(box['y']-b['y'])<box['w']*.5 for b in unique):unique.append(box)
    return unique
