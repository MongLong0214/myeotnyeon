from pathlib import Path
import os
import re
import subprocess
import sys
import time

from PIL import Image

stage = Path(__file__).resolve().parent
episode = stage.parent
kit = episode.parent.parent / 'anat_kit'
blender = '/Applications/Blender.app/Contents/MacOS/Blender'
audit = stage / 'render_status.log'
batches = [(700, 713)] if sys.argv[1] == 'pilot' else [(301, 404), (405, 508), (509, 612), (613, 699)]

def status(message):
    with audit.open('a') as out:
        print(message, file=out)
    print(message, flush=True)

for start, end in batches:
    for side in ('A', 'B'):
        assert end - start + 1 <= 150
        directory = stage / side
        directory.mkdir(exist_ok=True)
        frames = [directory / f'f_{f:04}.png' for f in range(start, end + 1)]
        for attempt in range(1, 4):
            log = stage / f'{side}_{start:04}_{end:04}_{attempt}.log'
            status(f'{side} f{start}–{end} starting (attempt {attempt})')
            t0 = time.monotonic()
            with log.open('w') as output:
                run = subprocess.run([
                    'nice', '-n', '15', blender, '-b', str(stage / f'neck_{side}_v3b.blend'),
                    '--python-exit-code', '1', '-s', str(start), '-e', str(end),
                    '-P', str(kit / 'blender/rset.py'), '-a', '--',
                    f'//{side}/f_', '--final',
                ], cwd=episode, stdout=output, stderr=subprocess.STDOUT)
            contents = log.read_text(errors='replace')
            saved = len(re.findall(r"Saved: '.*?/f_\d{4}\.png'", contents))
            try:
                for frame in frames:
                    with Image.open(frame) as im:
                        assert im.size == (1080, 880) and im.mode == 'RGBA'
                        im.verify()
                verified = True
            except (OSError, ValueError, AssertionError) as error:
                status(f'Invalid render {frame.name}: {error}')
                verified = False
            ok = verified and run.returncode == 0 and saved == len(frames) and 'RSET final 64 100' in contents
            status(f'{side} f{start}–{end} {"ok" if ok else "failed"}, {time.monotonic()-t0:.1f} s, {saved} frames')
            if ok:
                break
        else:
            sys.exit(f'{side} f{start}–{end} failed three attempts: {log}')
