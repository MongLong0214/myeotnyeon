"""Reconstruct the registered DBCLS section in millimetres; local z follows the occlusal axis."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'.cache/deps'))
import numpy as np
import trimesh
from scipy import ndimage as ndi
from scipy.spatial.transform import Rotation
from skimage.measure import marching_cubes
from skimage.draw import polygon
import fast_simplification
CACHE=HERE/'.cache'; ROOT=HERE.parents[2]/'research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99'
origin=np.array([22.89,-145.95,1450.42])
ex=np.array([.3154664,.94893675,0]); ey=np.array([-.94893675,.3154664,0])
basis=Rotation.from_euler('y',19,degrees=True).as_matrix()@np.array([ex,ey,[0,0,1]])
def source(part):
    m=trimesh.load_mesh(ROOT/f'FJ{part}.obj',process=True)
    m.vertices=(m.vertices-origin)@basis.T
    m=m.subdivide();trimesh.smoothing.filter_taubin(m,lamb=.38,nu=.42,iterations=6)
    if m.volume<0:m.invert()
    return m
if __name__=='__main__' and '--inspect' in sys.argv:
    m=source(1254)
    for z in np.arange(-11,10,.75):
        sl=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z]); a=sl[:,0]; print(round(z,1),np.round(a[:,:2].min(0),1) if len(a) else '', np.round(a[:,:2].max(0),1) if len(a) else '', 'section x',np.round(sorted(set(round(p[0],1) for line in sl if line[:,1].min()<.15<line[:,1].max() for p in [line[0]+(.15-line[0,1])/(line[1,1]-line[0,1])*(line[1]-line[0])])),1))
    quit()
from scipy.interpolate import PchipInterpolator
# Separate mesial pathways are shown on a curved longitudinal section.
knots=[
 ([-11.15,-9,-6,-3,0,2.4,5,8,15],[-1.93,-2.67,-3.39,-3.38,-2.55,-1.75,-.95,-.65,-.65]),
 ([-10.40,-9,-6,-3,0,2.4,5,8,15],[-1.46,-1.73,-2.12,-2.18,-1.47,-.87,-.26,-.15,-.15]),
 ([-10.7,-9,-6,-3,0,2.4,5,8,15],[3.45,3.07,2.66,2.71,2.15,1.55,.92,.56,.56])]
def path(i,z):return PchipInterpolator(*knots[i])(np.clip(z,knots[i][0][0],15.))
def section_y(x,z):
    mid=path(1,z)
    return -.98+.94*np.exp(-((x-mid)/.52)**2)*np.clip((3-z)/4,0,1)
def rad(i,z):
    u=np.clip((z-knots[i][0][0])/(2.4-knots[i][0][0]),0,1)
    return .14+.32*u if i!=2 else .16+.4*u
def ell(x,y,z,c,s):
    return (1-np.sqrt(((x-c[0])/s[0])**2+((y-c[1])/s[1])**2+((z-c[2])/s[2])**2))*min(s)
def sdf_mesh(m,axes):
    # Scan-convert intersections along x. Sorted intersections retain enclosed sockets.
    xx,yy,zz=axes
    occ=np.zeros(tuple(map(len,axes)),bool)
    for iz,z in enumerate(zz):
        seg=trimesh.intersections.mesh_plane(m,[0,0,1],[0,0,z])
        if len(seg)==0:continue
        a,b=seg[:,0],seg[:,1]
        mask=(np.minimum(a[:,1],b[:,1])[:,None]<=yy)&(yy<np.maximum(a[:,1],b[:,1])[:,None])
        lines,ys=np.where(mask)
        xs=a[lines,0]+(yy[ys]-a[lines,1])*(b[lines,0]-a[lines,0])/(b[lines,1]-a[lines,1])
        for j in np.unique(ys):
            cross=np.sort(xs[ys==j]);occ[:,j,iz]=np.searchsorted(cross,xx)%2==1
    d=ndi.distance_transform_edt(occ)-ndi.distance_transform_edt(~occ)
    return (ndi.gaussian_filter(d.astype('f'),.85)*(xx[1]-xx[0])).astype('f')
def save(name,field,axes,reduction=.68):
    h=axes[0][1]-axes[0][0]
    field=np.broadcast_to(field,tuple(map(len,axes))).copy()
    for ax in range(3):
        for idx in [0,-1]:
            sel=[slice(None)]*3;sel[ax]=idx;field[tuple(sel)]=np.minimum(field[tuple(sel)],-h)
    v,f,*_=marching_cubes(field,0,spacing=(h,h,h),allow_degenerate=False)
    v+=np.array([a[0] for a in axes]);v,f=fast_simplification.simplify(v,f,target_reduction=reduction,agg=5)
    m=trimesh.Trimesh(v,f,process=False)
    if m.volume<0:m.invert()
    np.savez_compressed(CACHE/(name+'.npz'),v=np.array(m.vertices,'f'),f=np.array(m.faces,'i'))
def hero():
    axes=[np.arange(a,b,.10,dtype='f') for a,b in [(-7,7),(-6.3,6.7),(-13.1,9.4)]]
    x,y,z=np.ix_(*axes); m=sdf_mesh(source(1254),axes)
    sy=section_y(x,z); face=y-sy
    ax=.06*np.sin(4.1*x+2*z)*np.sin(3.6*y-2.4*z)
    chamber=ell(x,y,z,(-.12,-.60,2.12),(2.82,2.22,1.68))
    horns=np.maximum(ell(x,y,z,(-1.95,-.30,3.23),(.65,1.08,1.28)),ell(x,y,z,(1.75,-.2,3.14),(.71,1.1,1.16)))
    access=1.71+.22*np.clip((z-3.6)/3.,0,1)-np.sqrt(((x+.14)/1.09)**2+((y+.60)/1.04)**2)
    access=np.minimum(access,z-2.83)
    lumen=np.maximum.reduce([chamber,horns,access])
    for i in range(3):
        cx=path(i,z);cy=section_y(cx,z)+.035
        tube=rad(i,z)-np.sqrt((x-cx)**2+(y-cy)**2)
        lumen=np.maximum(lumen,np.minimum(tube,z-knots[i][0][0]+.12))
    opened=np.minimum(np.minimum(m,face),-lumen)
    save('m1',opened,axes)
    enamel_thick=np.clip((z-.9)*.32,.012,1.45)
    # Surface coordinates for physical enamel and cut-wall pigmentation.
    save('enamel',np.minimum.reduce([opened+.016,np.broadcast_to(enamel_thick,m.shape)-m,z+np.zeros_like(m)-1.45]),axes,.65)
    pit_center=-.49+.26*np.sin(z*1.2)
    pit=.45+.19*(z-4.7)+.23*np.sin(z*2.4)+ax*1.6-np.sqrt((x-pit_center)**2+((y+.85)*1.05)**2)
    lesion=np.minimum(np.minimum(np.minimum(m,face),access+.035),-pit)
    lesion=np.minimum(lesion,z-3.75)
    save('caries',lesion,axes,.56)
    pulp=np.minimum.reduce([lumen-.06,np.broadcast_to(3.76-z,m.shape),m-.18,face-.02])
    save('pulp',pulp,axes)
    core=np.minimum.reduce([lumen+.015,m-.36,face,np.broadcast_to(z-.67,m.shape)])
    save('core',core,axes)
    prep=5.02-.25*np.maximum(z-1,0)-np.sqrt(((x+.05)/1.06)**2+((y-.02)/.99)**2)
    prep=np.maximum(1.85-z,np.minimum(prep,5.54-z+.14*np.sin(x)))
    save('stump',np.minimum(opened,prep),axes)
    crown=np.minimum.reduce([m,face,-prep-.015]);save('ceramic',crown,axes)
    save('crown_full',np.minimum(m,-prep-.015),axes)
    save('stump_full',np.minimum(m,prep),axes)
    # A narrow PDL sheath remains between the sectioned root and its socket.
    save('ligament',np.minimum.reduce([m+.25,-m+.015,face-.05,1.65-z+np.zeros_like(m)]),axes)
def surroundings():
    axes=[np.arange(a,b,.23,dtype='f') for a,b in [(-26,27),(-7,18),(-25,13)]]
    x,y,z=np.ix_(*axes);tooth=sdf_mesh(source(1254),axes)
    face=y-.75-.4*np.sin(.24*x)-.11*np.sin(.6*z)
    lesion=ell(x,y,z,(-1.98,-.25,-11.48),(2.03,2.1,1.72))
    for name,num in [('jaw',3289),('gingiva',1253)]:
        volume=sdf_mesh(source(num),axes); field=np.minimum.reduce([volume,np.broadcast_to(face,volume.shape),-tooth-.28,-lesion-.12])
        save(name,field,axes,.86)
    for num,n in [(1257,'p2'),(1256,'m2')]:
        m=source(num);np.savez_compressed(CACHE/(n+'.npz'),v=np.array(m.vertices,'f'),f=np.array(m.faces,'i'))
if __name__=='__main__':
    hero();surroundings()
