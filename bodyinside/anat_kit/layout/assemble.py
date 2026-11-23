"""Assemble final mp4 from band frames + layout + SFX (two-pass loudnorm). usage: python assemble.py EPISODE_DIR FRAMES_GLOB_PATTERN OUT.mp4
All looped stills get -framerate {fps} (the 25-fps default once caused judder)."""
import json, subprocess, sys, os
E, FR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; ep = json.load(open(f'{E}/episode.json')); fps = ep['fps']; dur = ep['duration']
def run(a):
    result = subprocess.run(a, capture_output=True, text=True)
    if result.returncode:
        print(result.stderr[-1600:], file=sys.stderr)
        sys.exit(result.returncode)
    return result
if '--audio-from' in sys.argv:
    audio_source = sys.argv[sys.argv.index('--audio-from') + 1]
    audio_options = ['-c:a', 'copy']
else:
    limited = f'{E}/audio/sfx_pre.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', f'{E}/audio/sfx.wav', '-af',
         'alimiter=limit=0.35:attack=3:release=60:level=false', limited])
    lj = run(['ffmpeg', '-hide_banner', '-i', limited, '-af', f"loudnorm=I={ep['lufs']}:TP=-1.5:LRA=11:print_format=json", '-f', 'null', '-']).stderr
    m = json.loads(lj[lj.rindex('{'):lj.rindex('}') + 1])
    audio_source = f'{E}/audio/sfx_norm.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', limited, '-af', f"loudnorm=I={ep['lufs']}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:linear=true,aresample=48000", audio_source])
    audio_options = ['-af', 'alimiter=limit=0.78:level=false', '-c:a', 'aac', '-b:a', '192k']
ins = ['-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/base.png', '-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/band_bg.png', '-framerate', str(fps), '-start_number', '0', '-i', FR]
bw, bh = 1080, ep['layout']['band_h']
fl = f"[2]scale={bw}:{bh}:flags=lanczos[fr];[1][fr]overlay=0:0:format=auto,eq=contrast=1.04:saturation=1.05[band];[0][band]overlay=0:{ep['layout']['band_y']}:shortest=1[v0]"
for i, b in enumerate(ep['beats']):
    ins += ['-framerate', str(fps), '-loop', '1', '-i', f'{E}/comp/cap_{i}.png']
    fl += f";[v{i}][{3 + i}]overlay=0:0:enable='between(t,{b['t0']},{b['t1'] - 0.01})'[v{i + 1}]"
n = len(ep['beats']); aidx = 3 + n
if ep.get('credits'): raise ValueError('put attribution in description.txt')
fl += f";[v{n}]format=yuv420p[v]"
ins += ['-i', audio_source]
r = run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', fl, '-map', '[v]', '-map', f'{aidx}:a', '-t', str(dur), '-r', str(fps),
         '-c:v', 'libx264', '-preset', ('veryfast' if '--draft' in sys.argv else 'slow'), '-crf', '15', '-profile:v', 'high', *audio_options, '-movflags', '+faststart', OUT])
print(r.stderr[-800:] or 'done ' + OUT)
