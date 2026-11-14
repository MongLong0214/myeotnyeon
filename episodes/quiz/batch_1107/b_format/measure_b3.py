"""B3 cadence numbers for a rendered video: motion share, background changes per minute, longest same background,
loop difference (last vs first frame). Background change = colour-histogram jump between consecutive frames.
usage: measure_b3.py <video.mp4>  (work/.venv)"""
import sys, subprocess, json
import numpy as np
v = sys.argv[1]; w, h = 108, 192
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', v, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32); n = len(F)
diff = np.abs(F[1:] - F[:-1]).mean((1, 2, 3))
moving = float((diff > .25).mean())
def hist(f): return np.concatenate([np.histogram(f[..., k], 16, (0, 256))[0] for k in range(3)]) / (w * h)
H = np.array([hist(f) for f in F]); jump = 0.5 * np.abs(H[1:] - H[:-1]).sum(1)
cuts = [i + 1 for i in np.where(jump > .25)[0]]
segs = np.diff([0] + cuts + [n])
out = dict(frames=n, motion_pct=round(100 * moving, 1), bg_changes_per_min=round(len(cuts) / (n / 30) * 60, 1),
           longest_same_bg_s=round(float(segs.max()) / 30, 2), loop_diff=round(float(np.abs(F[-1] - F[0]).mean()), 1))
print(json.dumps(out))
