from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
video = Path(sys.argv[1]).resolve()
dest = Path(sys.argv[2]).resolve()
frame_ids = [380, 641, *range(700, 721)]
frames = stage / 'crop_frames'
frames.mkdir(exist_ok=True)
subprocess.run([
    'ffmpeg', '-v', 'error', '-y', '-i', str(video),
    '-vf', "select='eq(n,380)+eq(n,641)+between(n,700,720)'",
    '-fps_mode', 'passthrough', str(frames / '%02d.png'),
], check=True)
files = sorted(frames.glob('*.png'))
assert len(files) == len(frame_ids)

size = (2462, 1686)
sheet = Image.new('RGB', size, '#16181d')
draw = ImageDraw.Draw(sheet)
font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
title = ImageFont.truetype(font_path, 44)
subtitle = ImageFont.truetype(font_path, 30)
label = ImageFont.truetype(font_path, 25)
draw.text((24, 18), 'Neck v3b frame review', fill='#f7f7fa', font=title)
draw.text((24, 83), 'Lower spine through the dissolve', fill='#c8cad1', font=subtitle)

for i, frame in enumerate(frame_ids[2:]):
    x, y = 24 + (i % 7) * 347, 130 + (i // 7) * 183
    with Image.open(files[i+2]) as im:
        crop = im.crop((56, 803, 970, 1207)).resize((326, 144), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x, y + 30))
    draw.text((x, y), f'f{frame}', fill='#f7f7fa', font=label)

draw.text((24, 702), 'Split-screen samples', fill='#c8cad1', font=subtitle)
for i, frame in enumerate(frame_ids[:2]):
    x, y = 24 + 1208 * i, 749
    with Image.open(files[i]) as im:
        crop = im.crop((0, 470, 1080, 1350))
        sheet.paste(crop, (x, y + 31))
    draw.text((x, y), f'f{frame}', fill='#f7f7fa', font=label)

dest.parent.mkdir(exist_ok=True)
sheet.save(dest, optimize=True)
