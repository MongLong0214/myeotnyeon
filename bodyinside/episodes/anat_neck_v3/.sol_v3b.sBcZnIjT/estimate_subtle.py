from itertools import product
import cv2
import numpy as np

from plan_drift import make_gray, starts

FIRST, LAST = 301, 713
Y_CENTER = 7

def smooth(x):
    t = min(1, max(0, x))
    return t*t*(3-2*t)

def drift(f, ax, ay, period, phase):
    ramp = smooth((f - (FIRST - 1))/38) * smooth((LAST + 1 - f)/29)
    angle = 2*np.pi*(f - 335)/period + phase
    return ramp*ax*np.sin(angle), ramp*(Y_CENTER + ay*np.cos(angle))

if __name__ == '__main__':
    cv2.setNumThreads(1)
    fs = range(min(starts)-1, max(starts)+60)
    ims = [make_gray(f) for f in fs]
    ims = [im.astype(np.uint8) for im in ims]
    mins = np.array(starts) - fs.start - 1
    print('windows', starts, flush=True)
    results = []
    for ax, ay, period, phase in product([10, 16, 22, 28], [11, 17, 23, 29], [105, 125, 145, 170], np.arange(8)*np.pi/4):
        previous = None
        moves = []
        for f, im in zip(fs, ims):
            x, y = drift(f, ax, ay, period, phase)
            mat = np.float32([[1, 0, x/4], [0, 1, y/4.4]])
            moved = cv2.warpAffine(im, mat, (270, 200), flags=cv2.INTER_LINEAR, borderValue=20)
            moved[:,134:137] = im[:,134:137]
            if previous is not None:
                moves.append(cv2.mean(cv2.absdiff(moved, previous))[0])
            previous = moved
        ms = [np.mean(moves[i:i+60]) for i in mins]
        results.append([round(min(ms), 3), ax, ay, period, round(phase, 6), round(float(np.mean(ms)), 3)])
    print(*sorted(results, reverse=True)[:30], sep='\n')
    print('Slower candidates', *[v for v in sorted(results, reverse=True) if v[3]>=105][:16], sep='\n')
