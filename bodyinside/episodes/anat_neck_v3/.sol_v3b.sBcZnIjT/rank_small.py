import cv2
import numpy as np
from estimate_subtle import drift
from plan_drift import make_gray, starts

cv2.setNumThreads(1)
fs = range(min(starts) - 1, max(starts) + 60)
images = [np.uint8(make_gray(f)) for f in fs]
for params in [(12,14,145,0), (16,17,145,0), (16,17,145,np.pi), (16,17,125,0), (16,17,125,np.pi), (19,18,145,np.pi/2), (19,18,145,0), (18,19,145,np.pi), (18,20,130,np.pi/2), (16,20,130,np.pi)]:
    prev = None
    motion = []
    for f, im in zip(fs, images):
        x, y = drift(f, *params)
        moved = cv2.warpAffine(im, np.float32([[1, 0, x/4], [0, 1, y/4.4]]), (270, 200), flags=cv2.INTER_LINEAR, borderValue=20)
        moved[:,134:137] = im[:,134:137]
        if prev is not None:
            motion.append(cv2.mean(cv2.absdiff(moved, prev))[0])
        prev = moved
    avg = [np.mean(motion[f-fs.start-1:f-fs.start-1+60]) for f in starts]
    print(params, round(min(avg),3), round(np.mean(avg),3), [round(x,2) for x in avg], flush=True)
