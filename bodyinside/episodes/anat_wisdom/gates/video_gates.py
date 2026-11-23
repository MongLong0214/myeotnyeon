"""Video gates for a finished short. usage: python video_gates.py final.mp4 band_frames_dir layout.json -> JSON report, exit 1 on fail.
Checks: fps/duplicate-frame cadence, frozen stretches >= 0.5 s, single highlight hue in the CG band, noise/firefly metric,
hook readability at 0.5 s, text boxes inside Shorts safe area."""
import sys, json, subprocess, re, glob, os
import numpy as np
from PIL import Image
mp4, fdir, layout = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
R = {}
def ff(args): return subprocess.run(['ffmpeg', '-hide_banner', '-nostats'] + args, capture_output=True, text=True).stderr
# 1 fps + cadence: duplicates in a 30 fps file mean a resample bug
pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=r_frame_rate,nb_frames', '-of', 'json', mp4], capture_output=True, text=True).stdout
st = json.loads(pr)['streams'][0]; num, den = map(int, st['r_frame_rate'].split('/'))
d = ff(['-i', mp4, '-vf', 'mpdecimate=hi=64*2:lo=64:frac=0.33,showinfo', '-f', 'null', '-'])
kept = len(re.findall(r'n:\s*\d+', d)); total = int(st.get('nb_frames') or 0)
dup_ratio = 1 - kept / total if total else 0
R['fps'] = {'fps': num / den, 'dup_ratio': round(dup_ratio, 3), 'ok': abs(num / den - layout['fps']) < 0.01 and dup_ratio < 0.05}
# 2 frozen stretches (>= 0.5 s)
fz = ff(['-i', mp4, '-vf', 'freezedetect=n=0.002:d=0.5', '-map', '0:v', '-f', 'null', '-'])
R['freeze'] = {'events': re.findall(r'freeze_start: ([\d.]+)', fz), 'ok': 'freeze_start' not in fz}
# 3 single highlight hue in the band (saturated warm/other clusters)
frames = sorted(glob.glob(os.path.join(fdir, '*.png')))[::10]
hues = []
for f in frames:
    a = np.asarray(Image.open(f).convert('RGBA').resize((270, 200))).astype(float) / 255
    rgb, al = a[..., :3], a[..., 3]
    mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / (mx + 1e-6)
    m = (sat > 0.55) & (mx > 0.45) & (al > 0.5)
    if m.sum() < 30: continue
    im = Image.fromarray((rgb * 255).astype('uint8')).convert('HSV'); h = np.asarray(im)[..., 0][m].astype(float) * 360 / 255
    hues += list(h)
hist = np.histogram(hues, bins=12, range=(0, 360))[0] if hues else np.zeros(12)
allowed = layout.get('allowed_hue_bins', [])  # e.g. nerve yellow + highlight amber
clusters = [i for i, c in enumerate(hist) if c > 0.08 * max(1, sum(hist)) and i not in allowed]
R['highlight'] = {'hue_hist': hist.tolist(), 'unexpected_bins': clusters, 'ok': len(clusters) <= layout.get('max_highlight_clusters', 1)}
# 4 noise / fireflies: high-pass energy on dark flat areas + isolated bright pixels
nz, ffly = [], []
for f in frames:
    g = np.asarray(Image.open(f).convert('L')).astype(float)
    hp = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    flat = (np.abs(g[1:-1, 1:-1] - np.median(g)) < 25)
    nz.append(float(np.std(hp[flat])) if flat.any() else 0); ffly.append(int(((hp > 120) & (g[1:-1, 1:-1] > 200)).sum()))
R['noise'] = {'hp_std': round(float(np.median(nz)), 2), 'fireflies_max': int(max(ffly) if ffly else 0),
              'ok': np.median(nz) < layout.get('noise_max', 6.0) and (max(ffly) if ffly else 0) < layout.get('firefly_max', 40)}
# 5 hook at 0.5 s: subject (highlight) visible and contrast present in the band
h = sorted(glob.glob(os.path.join(fdir, '*.png')))[int(0.5 * layout['fps'])]
a = np.asarray(Image.open(h).convert('RGBA')).astype(float) / 255
mx, mn = a[..., :3].max(-1), a[..., :3].min(-1); sat = (mx - mn) / (mx + 1e-6)
subj = ((sat > 0.35) & (mx > 0.4) & (a[..., 3] > 0.5)).mean()
lum = a[..., :3].mean(-1); contrast = float(np.percentile(lum, 95) - np.percentile(lum, 5))
R['hook'] = {'subject_frac': round(float(subj), 4), 'contrast': round(contrast, 3), 'ok': subj > layout.get('hook_subject_min', 0.01) and contrast > 0.35}
# 6 text safe area (Shorts: keep text inside x 60..1020, y 180..1500 by default)
sa = layout['safe']; bad = [b for b in layout['text_boxes'] if b[0] < sa[0] or b[1] < sa[1] or b[2] > sa[2] or b[3] > sa[3]]
R['safe_area'] = {'violations': bad, 'ok': not bad}
R['pass'] = all(v['ok'] for v in R.values() if isinstance(v, dict))
print(json.dumps(R, ensure_ascii=False, indent=1)); sys.exit(0 if R['pass'] else 1)
