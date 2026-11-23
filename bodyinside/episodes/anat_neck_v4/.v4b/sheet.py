from io import BytesIO
from pathlib import Path
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
ep = json.loads((stage/'episode.json').read_text())
times = [0.75, 2.45, 4.5, 7.7, 11.12, 15.15, 17.0, 20.25, 25.40, 29.1, 31.67, 34.48]
canvas = Image.new('RGB', (920, 1232), '#1a1e24')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
for i, time in enumerate(times):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(time), '-i',
                                    'v4b_draft.mp4', '-frames:v', '1', '-vf', 'scale=216:384',
                                    '-f', 'image2pipe', '-c:v', 'png', '-'])
    im = Image.open(BytesIO(data)).convert('RGB')
    x, y = 10+228*(i%4), 8+408*(i//4)
    canvas.paste(im, (x, y))
    draw.text((x+5, y+387), f'{time:05.2f}s', fill='#f4f4f4', font=font)
canvas.save('sheet_v4b.png')
