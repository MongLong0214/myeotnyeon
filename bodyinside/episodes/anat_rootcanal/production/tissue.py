from sections import *
from motion import bur_position
def cancellous():
    axes=[np.arange(a,b,.17,dtype='f') for a,b in [(-18,19),(-3.3,3.8),(-23,9)]]
    x,y,z=np.ix_(*axes);tooth=sdf_mesh(source(1254),axes);jaw=sdf_mesh(source(3289),axes)
    face=y-.75-.4*np.sin(.24*x)-.11*np.sin(.6*z)
    lesion=ell(x,y,z,(-1.98,-.25,-11.48),(2.03,2.1,1.72))
    g=np.random.default_rng(491);noise=ndi.gaussian_filter(g.normal(size=tooth.shape).astype('f'),[2.55,2.65,3.5])
    fine=ndi.gaussian_filter(g.normal(size=tooth.shape).astype('f'),1.35)
    lattice=.18+noise/noise.std()*.36+fine/fine.std()*.075
    wall=np.minimum.reduce([jaw,np.broadcast_to(face+1.05,tooth.shape),-tooth-.26,-lesion-.11])
    save('trabecula',np.minimum(wall,lattice),axes,.70)
def cut():
    from skimage.measure import marching_cubes
    p=np.load(CACHE/'caries.npz');m=trimesh.Trimesh(p['v'],p['f'],process=True)
    axes=[np.arange(a,b,.073,dtype='f') for a,b in [(-2.6,2.36),(-1.25,1.80),(3.58,8.45)]]
    x,y,z=np.ix_(*axes);field=sdf_mesh(m,axes)
    # Signed swept radial profile of the rotating reference bur, including flute clearance.
    removal=-np.ones_like(field)*50
    for f in range(165,242):
        x0,y0,z0=bur_position(f)
        h=(z-z0)/.82
        r=np.interp(h,[0,.18,.43,.85,1.25,1.57,1.93,6.45],[.08,.56,.79,.87,.67,.44,.36,.36])*.82+.046
        flute=np.minimum(r-np.sqrt((x-x0)**2+(y-y0)**2),z-z0+.025)
        removal=np.maximum(removal,flute)
        save('cut%03d'%f,np.minimum(field,-removal),axes,.66)
if __name__=='__main__':cancellous();cut()
