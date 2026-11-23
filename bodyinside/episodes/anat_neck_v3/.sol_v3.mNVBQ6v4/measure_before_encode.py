"""Assemble final mp4 from band frames + layout + SFX (two-pass loudnorm). usage: python assemble.py EPISODE_DIR FRAMES_GLOB_PATTERN OUT.mp4
All looped stills get -framerate {fps} (the 25-fps default once caused judder)."""
import json, subprocess, sys, os
E, FR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; ep = json.load(open(f'{E}/episode.json')); fps = ep['fps']; dur = ep['duration']
def run(a): return subprocess.run(a, capture_output=True, text=True)
ins = ['-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/base.png', '-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/band_bg.png', '-framerate', str(fps), '-start_number', '0', '-i', FR]
bw, bh = 1080, ep['layout']['band_h']
fl = f"[2]scale={bw}:{bh}:flags=lanczos[fr];[1][fr]overlay=0:0:format=auto,eq=contrast=1.04:saturation=1.05[band];[0][band]overlay=0:{ep['layout']['band_y']}:shortest=1[v0]"
for i, b in enumerate(ep['beats']):
    ins += ['-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/cap_{i}.png']
    fl += f";[v{i}][{3 + i}]overlay=0:0:enable='between(t,{b['t0']},{b['t1'] - 0.01})'[v{i + 1}]"
n = len(ep['beats']); cr = ep.get('credits'); aidx = 3 + n
if cr:
    t0 = dur - cr.get('last_s', 1.2); ins += ['-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/credit.png']
    fl += f";[{aidx}]format=rgba,fade=t=in:st={t0}:d={6 / fps}:alpha=1[cr];[v{n}][cr]overlay=0:0:enable='gte(t,{t0})'[v{n + 1}]"; n += 1; aidx += 1
fl += f";[v{n}]format=yuv420p[v]"
ins += ['-i', f'{E}/draft4.mp4']
r = run(['ffmpeg', '-hide_banner', '-nostats'] + ins + [
    '-filter_complex', fl + ';[v]freezedetect=n=0.002:d=0.5[probe]',
    '-map', '[probe]', '-an', '-t', str(dur), '-f', 'null', '-'])
print(r.stderr); sys.exit(r.returncode)
