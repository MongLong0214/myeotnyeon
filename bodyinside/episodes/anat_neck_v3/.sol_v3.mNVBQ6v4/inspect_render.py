from pathlib import Path
import sys
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import label

stage = Path(__file__).resolve().parent
ep = stage.parent
mode = sys.argv[1]
folders = [sys.argv[2]] if len(sys.argv) > 2 else ['main', 'A', 'B']
refs = {'main': ep / 'frames_draft4_raw', 'A': ep / 'frames_dA', 'B': ep / 'frames_dB'}
existing = {'main': ep / 'frames_hqv3_raw', 'A': ep / 'frames_hA', 'B': ep / 'frames_hB'}
expected_size = (1080, 880)

def low(path):
    with Image.open(path) as im:
        return im.convert('RGBA').resize((270, 220), Image.Resampling.LANCZOS)

def gray(im):
    bg = Image.new('RGBA', im.size, (18, 18, 18, 255))
    bg.alpha_composite(im)
    return np.asarray(bg.convert('L'), dtype=np.float32)

for folder in folders:
    out = stage / folder if mode == 'new' else existing[folder]
    frames = sorted(out.glob('f_*.png'))
    scores = []
    for frame in frames:
        f = int(frame.stem[2:])
        if folder == 'main' and 300 <= f <= 713:
            continue
        source = refs[folder] / frame.name
        saved = ep / 'frames_draft4_raw_xf_orig' / frame.name
        if folder == 'main' and saved.is_file():
            source = saved
        try:
            with Image.open(frame) as im:
                if im.size != expected_size or im.mode != 'RGBA':
                    print('Unexpected format', frame, im.size, im.mode)
            a, b = low(source), low(frame)
        except OSError as err:
            print('Incomplete or unreadable', frame, err)
            continue
        x, y = gray(a), gray(b)
        dark = (x > 65) & (y < 29) & (y < x * 0.4)
        islands, count = label(dark)
        sizes = np.bincount(islands[dark])
        black_patch = int(sizes.max()) if count else 0
        scores.append((float(abs(x-y).mean()), black_patch, int(dark.sum()), f, source, frame))
    if not scores:
        continue
    biggest_changes = sorted(scores, reverse=True)[:12]
    darkest = sorted(scores, key=lambda row: row[1], reverse=True)[:12]
    print(folder, len(scores), 'frames checked. Top (mean luma difference, largest dark patch px, total dark px, frame)')
    print('  Largest changes:', [tuple(round(x, 2) for x in row[:4]) for row in biggest_changes])
    print('  Dark areas:', [tuple(round(x, 2) for x in row[:4]) for row in darkest])
    chosen = biggest_changes[:5] + darkest[:5]
    sheet = Image.new('RGB', (5 * 270, 4 * 244), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    for i, (mae, patch, pixels, f, source, frame) in enumerate(chosen):
        for j, p in enumerate([source, frame]):
            tile = low(p)
            x, y = (i % 5) * 270, ((i // 5) * 2 + j) * 244
            sheet.paste(tile, (x, y + 24), tile)
            draw.text((x + 6, y + 4), f'{"HQ" if j else "Draft"} f{f} | difference {mae:.2f} | dark {patch}', fill='white')
    sheet.save(stage / f'inspect_{mode}_{folder}.png')
