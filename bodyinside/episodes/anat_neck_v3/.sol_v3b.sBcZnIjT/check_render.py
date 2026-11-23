"""Compare used portions against the approved render after accounting for the camera shift."""
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parent))
from split_screen import drift_pixels

master = stage.parent / '.sol_v3.mNVBQ6v4'
cv2.setNumThreads(1)
W, H = 270, 220

def gray(path):
    with Image.open(path) as im:
        im = im.convert('RGBA').resize((W, H), Image.Resampling.LANCZOS)
        bg = Image.new('RGBA', im.size, (20, 20, 20, 255))
        bg.alpha_composite(im)
        return np.asarray(bg.convert('L'))

all_rows = []
for side, cols in [('A', slice(0, W//2)), ('B', slice(W//2, W))]:
    rows = []
    for path in sorted((stage / side).glob('f_*.png')):
        frame = int(path.stem[2:])
        baseline = master / side / path.name
        x, y = drift_pixels(frame)
        before = cv2.warpAffine(gray(baseline), np.float32([[1, 0, x/4], [0, 1, y/4]]),
                                (W, H), flags=cv2.INTER_LINEAR, borderValue=20)[:, cols].astype(np.float32)
        after = gray(path)[:, cols].astype(np.float32)
        dark = (before > 65) & (after < 29) & (after < before * 0.4)
        # Current candidate should have the same lower subject coverage until f709;
        # through f713 the old frame lacks the thoracic vertebrae.
        islands, count = label(dark)
        largest = int(np.bincount(islands[dark]).max()) if count else 0
        rows.append((largest, float(np.abs(before-after).mean()), frame, side))
    rows.sort(reverse=True)
    all_rows.extend(rows)
    print(side, len(rows), 'frames', rows[:12], flush=True)

flagged = [row for row in all_rows if row[0] >= 32]
print('dark region candidates', flagged, flush=True)
if flagged:
    chosen = flagged[:18]
    sheet = Image.new('RGB', (270 * 3, 242 * ((len(chosen) + 2) // 3)), (22, 22, 22))
    draw = ImageDraw.Draw(sheet)
    for i, (patch, delta, frame, side) in enumerate(chosen):
        s = slice(0, W//2) if side == 'A' else slice(W//2, W)
        for j, directory in enumerate([master, stage]):
            im = gray(directory / side / f'f_{frame:04}.png')[:, s]
            sheet.paste(Image.fromarray(im), (270 * (i % 3) + W//2 * j, 242 * (i//3) + 22))
        draw.text((270 * (i % 3) + 7, 242 * (i//3) + 3), f'{side} f{frame}  dark patch {patch} px', fill='white')
    sheet.save(stage / 'dark_review.png')
