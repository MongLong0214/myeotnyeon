"""Render the requested comparison; uses only Python's standard library and existing CLIs."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parents[1] / 'research/format_v4/spike'
ENV = {**os.environ, 'npm_config_cache': '/tmp/v4spike-npm-cache'}
COMMON = ['--browser-executable=src/v4spike/chromium.sh', '--port=3145', '--log=verbose']
METRICS = []


def run(label, arguments):
    command = ['npx', '--no-install', 'remotion', *arguments, *COMMON]
    started = time.monotonic()
    with (OUT / 'logs' / f'{label}.log').open('w') as log:
        log.write('$ ' + shlex.join(command) + '\n')
        log.flush()
        subprocess.run(command, cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT, check=True)
    content = (OUT / 'logs' / f'{label}.log').read_text()
    match = re.search(r'Rendering frames done in (\d+)ms', content)
    frames = 75 if '-75' in label else 90
    metric = {'run': label, 'wall_seconds': round(time.monotonic() - started, 3)}
    if match:
        metric.update(frames=frames, render_ms=int(match[1]), ms_per_frame=round(int(match[1])/frames, 3))
    METRICS.append(metric)
    (OUT / 'logs/metrics.json').write_text(json.dumps(METRICS, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(metric), flush=True)


if __name__ == '__main__':
    for path in ['A', 'B']:
        for mode in ['c1', 'default']:
            run(f'{path}-{mode}-75', ['render', 'src/index.ts', f'V4SPIKE-{path}', str(OUT/f'qa/{path}-{mode}-75.mp4'),
                '--frames=0-74', *(['--concurrency=1'] if mode=='c1' else []),
                '--codec=h264', '--crf=18', '--pixel-format=yuv420p', '--color-space=bt709'])
        run(f'{path}-clip-90', ['render', 'src/index.ts', f'V4SPIKE-{path}', str(OUT/f'{path}.mp4'),
            '--concurrency=1', '--codec=h264', '--crf=18', '--pixel-format=yuv420p', '--color-space=bt709'])
    for path in ['A', 'B']:
        for frame in [6, 36, 69, 40]:
            destination = OUT/f'{path}.png' if frame==69 else OUT/f'qa/{path}-f{frame:02}.png'
            run(f'{path}-still-{frame}', ['still', 'src/index.ts', f'V4SPIKE-{path}', str(destination), f'--frame={frame}'])
        run(f'{path}-repeat-40', ['still', 'src/index.ts', f'V4SPIKE-{path}', str(OUT/f'qa/{path}-f40-repeat.png'), '--frame=40'])
        run(f'{path}-landscape', ['still', 'src/index.ts', f'V4SPIKE-{path}', str(OUT/f'{path}-landscape.png'), '--frame=69', '--props={"landscape":true}'])
