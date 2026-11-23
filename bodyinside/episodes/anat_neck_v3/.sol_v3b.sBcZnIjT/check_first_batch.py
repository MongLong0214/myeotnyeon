import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

stage = Path(__file__).resolve().parent
master = stage.parent / '.sol_v3.mNVBQ6v4'
def motion(directory, start, end):
    previous = None
    result = {}
    for f in range(start - 1, end + 1):
        with Image.open(directory / f'f_{f:04}.png') as image:
            im = image.convert('RGBA')
            bg = Image.new('RGBA', im.size, (20,20,20,255))
            bg.alpha_composite(im)
            gray = np.array(bg.convert('L').resize((270,200)), dtype=np.float32)
        if previous is not None:
            result[f] = float(np.abs(gray-previous).mean())
        previous = gray
    return result

candidate = stage / sys.argv[1]
start, end = map(int, sys.argv[2:4])
ref = motion(master / 'frames_final_hq_v3', start, end)
new = motion(candidate, start, end)
for f in range((start + 9) // 10 * 10, end-58, 10):
    old_delta = float(np.mean([ref[i] for i in range(f, f + 60)]))
    new_delta = float(np.mean([new[i] for i in range(f, f + 60)]))
    print(f'{f}–{f+59}: {old_delta:.3f} -> {new_delta:.3f}')
