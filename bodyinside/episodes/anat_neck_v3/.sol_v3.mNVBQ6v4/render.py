import os
from pathlib import Path
import re
import subprocess
import sys
import time

stage = Path(__file__).resolve().parent
episode = stage.parent
blender = '/Applications/Blender.app/Contents/MacOS/Blender'
settings = episode.parent.parent / 'anat_kit/blender/rset.py'
batches = [
    ('main', 0, 149), ('main', 150, 299),
    ('main', 714, 818), ('main', 819, 923),
    ('A', 300, 437), ('A', 438, 575), ('A', 576, 713),
    ('B', 300, 437), ('B', 438, 575), ('B', 576, 713),
]
for name, start, end in batches:
    folder = stage / name
    folder.mkdir(exist_ok=True)
    stem = 'neck' if name == 'main' else f'neck_{name}'
    for attempt in range(1, 4):
        while subprocess.run(['pgrep', '-x', 'Blender'], capture_output=True).returncode == 0:
            print('Waiting for an existing Blender process', flush=True)
            time.sleep(30)
        log = stage / f'{name}_{start:04}_{end:04}_{attempt}.log'
        print(f'{name} f{start}–{end}, attempt {attempt}', flush=True)
        begun = time.monotonic()
        with log.open('w') as output:
            run = subprocess.run([
                blender, '-b', f'{stem}.blend', '--python-exit-code', '1',
                '-s', str(start), '-e', str(end), '-P', str(settings), '-a',
                '--', f'//{stage.name}/{name}/f_', '--final',
            ], cwd=episode, stdout=output, stderr=subprocess.STDOUT)
        elapsed = time.monotonic() - begun
        contents = log.read_text(errors='replace')
        saved = len(re.findall(r"Saved: '.*?/f_\d{4}\.png'", contents))
        found = sum((folder / f'f_{i:04}.png').is_file() for i in range(start, end + 1))
        ok = run.returncode == 0 and saved == found == end - start + 1 and 'RSET final 64 100' in contents
        print(f'{name} f{start}–{end} {"ok" if ok else "failed"}, {elapsed:.1f} s, {saved} written, {found} on disk, exit {run.returncode}.', flush=True)
        if ok:
            break
    else:
        sys.exit(f'{name} f{start}–{end} failed three attempts. See {log}')
