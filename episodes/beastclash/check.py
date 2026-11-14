"""loop match (first vs last decoded frame, mean abs diff /255) + duration + review sheets (all frames, small)."""
import sys, subprocess, numpy as np, glob, tempfile, math
from PIL import Image, ImageDraw
v = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
tmp = tempfile.mkdtemp(); subprocess.run(['ffmpeg', '-v', 'error', '-i', v, '-vf', 'scale=108:192', '-vsync', '0', f'{tmp}/%05d.png'], check=True)
fs = sorted(glob.glob(f'{tmp}/*.png')); a = np.asarray(Image.open(fs[0]), float); b = np.asarray(Image.open(fs[-1]), float)
print('frames', len(fs), 'sec', round(len(fs) / 30, 2), 'loop diff', round(np.abs(a - b).mean(), 2), '/255')
if out:
    per, cols = 120, 15
    for k in range(math.ceil(len(fs) / per)):
        part = fs[k * per:(k + 1) * per]; im = Image.new('RGB', (cols * 108, math.ceil(len(part) / cols) * 204), '#111'); d = ImageDraw.Draw(im)
        for i, f in enumerate(part):
            n = k * per + i; x = i % cols * 108; y = i // cols * 204; im.paste(Image.open(f), (x, y + 12)); d.text((x + 2, y), str(n), fill='white')
        im.save(f'{out}_{k}.png')
