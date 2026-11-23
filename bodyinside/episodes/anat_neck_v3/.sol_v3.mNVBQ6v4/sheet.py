from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
master = Path(sys.argv[1])
destination = Path(sys.argv[2])
destination.mkdir(parents=True, exist_ok=True)
frames = (3, 150, 400, 600, 800, 920)
tile_w, tile_h, gap, label_h = 270, 480, 12, 36
sheet = Image.new('RGB', (len(frames) * (tile_w + gap) + gap, 2 * (tile_h + label_h + gap) + gap), (21, 23, 27))
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=19)
for row, (clip, label) in enumerate([(stage / 'draft4.mp4', 'Draft4'), (master, 'Final HQ v3')]):
    cache = stage / f'sheet_frames_{row}'
    cache.mkdir(exist_ok=True)
    select = '+'.join('eq(n\\,' + str(frame) + ')' for frame in frames)
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(clip), '-map', '0:v:0', '-vf', 'select=' + select, '-fps_mode', 'passthrough',
        '-frames:v', str(len(frames)), str(cache / '%02d.png'),
    ], check=True)
    for column, frame in enumerate(frames):
        with Image.open(cache / f'{column + 1:02d}.png') as source:
            assert source.size == (1080, 1920)
            tile = source.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        x = gap + column * (tile_w + gap)
        y = gap + row * (tile_h + label_h + gap)
        draw.text((x, y + 4), f'{label}  ·  f{frame}', font=font, fill=(232, 236, 241))
        sheet.paste(tile, (x, y + label_h))
sheet.save(destination / 'v3_sheet.png')
