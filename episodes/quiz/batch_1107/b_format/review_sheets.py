"""review_sheets.py <sheets_dir> <out_dir>: pairs of full contact sheets stacked at half size (every frame kept) for review."""
import sys, glob, os
from PIL import Image
fs = sorted(glob.glob(sys.argv[1] + '/sheet_*.png')); os.makedirs(sys.argv[2], exist_ok=True)
for k in range(0, len(fs), 2):
    ims = [Image.open(f) for f in fs[k:k + 2]]; ims = [i.resize((i.width // 2, i.height // 2)) for i in ims]
    out = Image.new('RGB', (ims[0].width, sum(i.height for i in ims))); y = 0
    for i in ims: out.paste(i, (0, y)); y += i.height
    out.save(f'{sys.argv[2]}/r{k // 2:02d}.png')
print(len(fs), 'sheets ->', (len(fs) + 1) // 2)
