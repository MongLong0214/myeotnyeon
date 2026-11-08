import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
from bvhfk import fk
def J(n, *c):
    for x in c:
        if x in n: return n.index(x)
    raise KeyError(c)
def timeline(path, step=0.5):
    n,p,pos,ft=fk(path)
    H=J(n,'Head'); hip=J(n,'Hips'); lh=J(n,'LeftHand','LeftWrist'); rh=J(n,'RightHand','RightWrist')
    la=J(n,'LeftArm','LeftShoulder'); ra=J(n,'RightArm','RightShoulder'); lu=J(n,'LeftUpLeg','LeftHip'); ru=J(n,'RightUpLeg','RightHip')
    s=1 if 'Hips' in n and pos[0,hip,1]!=0 else 0
    s=1  # skip T-pose frame 0 for CMU-ish data
    h=np.percentile(pos[s:,H,1],95)-np.percentile(np.minimum(pos[s:,J(n,'LeftFoot','LeftAnkle'),1],pos[s:,J(n,'RightFoot','RightAnkle'),1]),5)
    ground=np.percentile(np.minimum(pos[s:,J(n,'LeftFoot','LeftAnkle'),1],pos[s:,J(n,'RightFoot','RightAnkle'),1]),5)
    k=max(1,int(round(step/ft))); out=[]
    up=np.array([0,1,0.])
    prev=None
    for f in range(s,pos.shape[0],k):
        left=pos[f,lu]-pos[f,ru]; left[1]=0; left/=np.linalg.norm(left)+1e-9; fwd=np.cross(left,up)
        hh=(pos[f,H,1]-ground)/h; ph=(pos[f,hip,1]-ground)/h
        flag=''
        for nm,hd,sh in (('R',rh,ra),('L',lh,la)):
            rel=pos[f,hd]-pos[f,sh]; ext=np.dot(rel,fwd)/h
            if pos[f,hd,1]>pos[f,sh,1]: flag+=nm+('*' if ext>0.2 else '')
        mv=''
        if prev is not None:
            d=pos[f,hip]-pos[prev,hip]; d[1]=0; v=np.dot(d,fwd)/h/(k*ft)
            mv='f' if v>0.15 else ('b' if v<-0.15 else '.')
        prev=f
        out.append('%5.1f:%2d/%2d%s%s'%(f*ft, round(hh*100)%100 if hh<1 else 99, round(ph*100), mv, flag))
    return n, h, ft, pos.shape[0], out
if __name__=='__main__':
    for path in sys.argv[1:]:
        n,h,ft,F,out=timeline(path)
        print('==',path.split('/')[-1],'F=%d fps=%d dur=%.1fs height_units=%.1f'%(F,round(1/ft),F*ft,h))
        print(' '.join(out))
