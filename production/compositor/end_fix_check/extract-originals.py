"""Decode only selected boundary outputs from existing videos; never encode video."""
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess, io, json
P = Path(__file__).resolve().parent
W = P.parents[2]
cases = json.loads((P/'manifest-before.json').read_text())
cases = [i for i in cases if not i.get('aligned')]
cases += [{'name': 'v3_q001', 'from': 732, 'to': 737}, {'name': 'v3_q004', 'from': 738, 'to': 743}]
for item in cases:
    name, a, b = item['name'], item['from'], item['to']
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(W/'upload'/f'{name}.mp4'),
        '-vf', f'select=between(n\\,{a}\\,{b}),scale=216:384', '-vsync', '0', '-frames:v', str(b-a+1),
        '-f', 'image2pipe', '-vcodec', 'png', '-'])
    frames = []; cur = 0
    while cur < len(data):
        start = cur; cur += 8
        while True:
            length = int.from_bytes(data[cur:cur+4], 'big'); kind = data[cur+4:cur+8]; cur += length+12
            if kind == b'IEND': break
        frames.append(Image.open(io.BytesIO(data[start:cur])).convert('RGB'))
    assert len(frames) == b-a+1
    cols = min(8, len(frames)); rows = (len(frames)+cols-1)//cols
    strip = Image.new('RGB', (216*cols, 410*rows), '#202020'); draw = ImageDraw.Draw(strip)
    for i, im in enumerate(frames):
        x, y = (i%cols)*216, (i//cols)*410
        strip.paste(im, (x,y+26)); draw.text((x+4,y+5), f'{name} ORIGINAL f{a+i}', fill='white')
    prefix = 'rejected_control' if name in ['v3_q001','v3_q004'] else 'original'
    strip.save(P/f'{prefix}_{name}.jpg', quality=95, subsampling=0)
    print(name,a,b)
