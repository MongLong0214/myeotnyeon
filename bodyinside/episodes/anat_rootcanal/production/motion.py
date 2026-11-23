import math
import numpy as np
def bur_position(f):
    zs=np.interp(f,[157,164,168,178,201,215,231,238,244,253],[14.5,9.4,7.05,6.15,4.84,3.79,3.23,3.46,7.2,15.5])
    q=np.clip((f-164)/7,0,1);angle=(f-168)*.177
    return (-.12+.82*q*math.cos(angle),-.55+.49*q*math.sin(angle),float(zs))
