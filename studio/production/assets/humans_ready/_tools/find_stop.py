import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
from bvhfk import fk
def J(n,*c):
    for x in c:
        if x in n: return n.index(x)
for path in sys.argv[1:]:
    n,p,pos,ft=fk(path)
    H=J(n,'Head'); lu=J(n,'LeftUpLeg','LeftHip'); ru=J(n,'RightUpLeg','RightHip')
    lf=J(n,'LeftFoot','LeftAnkle'); rf=J(n,'RightFoot','RightAnkle')
    ground=np.percentile(np.minimum(pos[1:,lf,1],pos[1:,rf,1]),5); h=np.percentile(pos[1:,H,1],95)-ground
    up=np.array([0,1,0.])
    left=pos[:,lu]-pos[:,ru]; left[:,1]=0; left/= np.linalg.norm(left,axis=1,keepdims=True)+1e-9
    fwd=np.cross(left,up)
    res=[]
    for side,hn,en,sn,fn in (('R',('RightHand','RightWrist'),('RightForeArm','RightElbow'),('RightArm','RightShoulder'),('RightFingerBase','RightHand_end','RightWrist_end')),('L',('LeftHand','LeftWrist'),('LeftForeArm','LeftElbow'),('LeftArm','LeftShoulder'),('LeftFingerBase','LeftHand_end','LeftWrist_end'))):
        hd,el,sh=J(n,*hn),J(n,*en),J(n,*sn)
        ext=np.einsum('fi,fi->f',pos[:,hd]-pos[:,sh],fwd)/h
        lat=np.abs(np.einsum('fi,fi->f',pos[:,hd]-pos[:,sh],left))/h
        hy=(pos[:,hd,1]-pos[:,sh,1])/h
        fore=(pos[:,hd,1]-pos[:,el,1])/h
        ok=(ext>0.22)&(hy>-0.06)&(hy<0.16)&(fore>0.0)&(lat<0.2)
        # segments
        f=1; F=len(ok)
        while f<F:
            if ok[f]:
                g=f
                while g<F and ok[g]: g+=1
                if (g-f)*ft>=0.4: res.append((side,round(f*ft,2),round(g*ft,2),round(float(ext[f:g].mean()),2)))
                f=g
            else: f+=1
    print(path.split('/')[-1], 'h=%.1f'%h, res)
