from pathlib import Path
from itertools import product
from math import pi, sin, cos
import cv2
import numpy as np
from PIL import Image

root = Path('.sol_v3b.sBcZnIjT/frames_final_hq_v3b_raw')
fs = range(718, 882)
ims = []
for f in fs:
    with Image.open(root / f'f_{f:04}.png') as im:
        bg = Image.new('RGBA', im.size, (20,20,20,255))
        bg.alpha_composite(im.convert('RGBA'))
        ims.append(np.uint8(bg.convert('L').resize((270,200))))
cv2.setNumThreads(1)
r = []
for ax,ay,shape in product((-16,-12,-8,0,8,12,16),(-18,-12,-8,0,8,12,18),('arc','swing')):
    motion = []
    previous = None
    for f, im in zip(fs, ims):
        if 760 < f < 819:
            t = (f-760)/(819-760)
            weight = sin(pi*t)**2
            if shape == 'swing':
                weight *= cos(pi*t)
            im = cv2.warpAffine(im, np.float32([[1,0,ax*weight/4],[0,1,ay*weight/4.4]]), (270,200), flags=cv2.INTER_LINEAR, borderValue=20)
        if previous is not None:
            motion.append(cv2.mean(cv2.absdiff(im,previous))[0])
        previous = im
    m = np.mean(motion[760-fs.start-1:820-fs.start-1])
    r.append((round(float(m),4), ax, ay, shape))
print(*sorted(r, reverse=True)[:21], sep='\n')
