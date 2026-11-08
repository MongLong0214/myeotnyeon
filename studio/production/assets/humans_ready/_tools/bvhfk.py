"""Minimal numpy BVH parser + forward kinematics. fk(path) -> (names, parents, pos[F,J,3], frame_time)."""
import numpy as np, re
def parse(path):
    toks = open(path).read().split()
    i = 0; names=[]; parents=[]; offsets=[]; chans=[]; stack=[]; last=-1
    while toks[i] != 'MOTION':
        t = toks[i]
        if t in ('ROOT','JOINT'):
            names.append(toks[i+1]); parents.append(stack[-1] if stack else -1); last=len(names)-1; i+=2
        elif t == 'End':
            names.append(names[stack[-1]]+'_end'); parents.append(stack[-1]); last=len(names)-1; chans.append([]) if False else None; i+=2
            # mark as end: channels empty
            chans.append([]) ; offsets.append(None)
            # handled below by OFFSET
            continue_end=True
        elif t == '{': stack.append(last); i+=1
        elif t == '}': stack.pop(); i+=1
        elif t == 'OFFSET':
            o=[float(x) for x in toks[i+1:i+4]]
            if len(offsets) < len(names): offsets.append(o)
            else: offsets[-1]=o
            i+=4
        elif t == 'CHANNELS':
            n=int(toks[i+1]); chans.append(toks[i+2:i+2+n]); i+=2+n
        else: i+=1
    # fix chans list alignment (end sites appended [] already)
    i+=1; assert toks[i]=='Frames:'; F=int(toks[i+1]); ft=float(toks[i+4]); i+=5
    data=np.array(toks[i:], dtype=float)
    nch=sum(len(c) for c in chans); data=data[:F*nch].reshape(F, nch)
    return names, parents, np.array(offsets), chans, data, ft
def rot(axis, a):
    c, s = np.cos(a), np.sin(a); F=len(a); R=np.zeros((F,3,3)); 
    if axis=='X': R[:,0,0]=1; R[:,1,1]=c; R[:,1,2]=-s; R[:,2,1]=s; R[:,2,2]=c
    if axis=='Y': R[:,1,1]=1; R[:,0,0]=c; R[:,0,2]=s; R[:,2,0]=-s; R[:,2,2]=c
    if axis=='Z': R[:,2,2]=1; R[:,0,0]=c; R[:,0,1]=-s; R[:,1,0]=s; R[:,1,1]=c
    return R
def fk(path):
    names, parents, offs, chans, data, ft = parse(path)
    F=data.shape[0]; J=len(names); pos=np.zeros((F,J,3)); Rw=np.zeros((F,J,3,3)); k=0
    for j in range(J):
        R=np.tile(np.eye(3),(F,1,1)); t=np.tile(offs[j],(F,1))
        for c in chans[j]:
            v=data[:,k]; k+=1
            if c.endswith('position'): t[:, 'XYZ'.index(c[0])] = v if parents[j]<0 else offs[j]['XYZ'.index(c[0])]+0*v if False else v
            else: R = R @ rot(c[0], np.radians(v))
        p=parents[j]
        if p<0: pos[:,j]=t; Rw[:,j]=R
        else:
            pos[:,j]=pos[:,p]+np.einsum('fij,fj->fi',Rw[:,p],t); Rw[:,j]=Rw[:,p]@R
    return names, parents, pos, ft
