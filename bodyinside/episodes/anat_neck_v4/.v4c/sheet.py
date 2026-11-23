from io import BytesIO
from pathlib import Path
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
ep = json.loads((stage/'episode.json').read_text())
beats = ep['beats']
disc = beats[-1]
disc_cuts = [frame / ep['fps'] for frame in ep['scene_cuts_declared']
             if frame / ep['fps'] > disc['t0']]
times = [
    0.75, 2.45,
    beats[1]['t0'] + .65, beats[1]['t1'] - .3,
    beats[2]['t0'] + 2.6, beats[3]['t1'] - .35,
    beats[4]['t1'] - .2, disc['t0'],
    disc_cuts[0] + .48, disc_cuts[1] + .65, disc_cuts[2] + .65,
    disc['t1'] - 1 / ep['fps'],
]
canvas = Image.new('RGB', (920, 1232), '#1a1e24')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
for i, time in enumerate(times):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(time), '-i',
                                    'v4c_draft.mp4', '-frames:v', '1', '-vf', 'scale=216:384',
                                    '-f', 'image2pipe', '-c:v', 'png', '-'])
    im = Image.open(BytesIO(data)).convert('RGB')
    x, y = 10+228*(i%4), 8+408*(i//4)
    canvas.paste(im, (x, y))
    draw.text((x+5, y+387), f'{time:05.2f}s', fill='#f4f4f4', font=font)
canvas.save('sheet_v4c.png')
