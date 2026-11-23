"""Video gates for a finished short. usage: python video_gates.py final.mp4 band_frames_dir layout.json -> JSON report, exit 1 on fail.
Checks: fps/duplicate-frame cadence, frozen stretches >= 0.5 s, single highlight hue in the CG band, noise/firefly metric,
hook readability at 0.5 s, text boxes inside Shorts safe area,
flash frames (per-frame luma delta > 3x the local median on ALL band frames: a single-frame check missed f135/138/149 strobes)."""
from noise_metric import frame_metrics
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
kept = len([l for l in d.splitlines() if 'Parsed_showinfo' in l and ' n:' in l]); total = int(st.get('nb_frames') or 0)
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
# 4 noise / fireflies (noise_metric.py): high-pass energy on flat untextured areas + isolated hot pixels
nz, ffly = [], []
bgp = os.path.join(os.path.dirname(os.path.abspath(fdir)), 'comp', 'band_bg.png')
for f in frames:
    im_ = Image.open(f).convert('RGBA')
    if os.path.exists(bgp):
        b_ = Image.open(bgp).convert('RGBA').resize(im_.size); b_.alpha_composite(im_); im_ = b_
    g = np.asarray(im_.convert('L')).astype(float)
    _hs, _ff = frame_metrics(g); nz.append(_hs); ffly.append(_ff)
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
sa = layout['safe']; tb = layout.get('text_boxes') or json.load(open(layout['text_boxes_file']))
bad = [b for b in tb if b[0] < sa[0] or b[1] < sa[1] or b[2] > sa[2] or b[3] > sa[3]]
R['safe_area'] = {'violations': bad, 'ok': not bad}
# 7 flash frames: mean |luma(i) - luma(i-1)| on every band frame; flag spikes over 3x the median of +-7 frames
allf = sorted(glob.glob(os.path.join(fdir, '*.png')))
prev = None; dl = []
for f in allf:
    _im = Image.open(f).convert('RGBA'); _bg = Image.new('RGBA', _im.size, (20, 20, 20, 255)); _bg.alpha_composite(_im)   # composite: straight-alpha RGB of faint layers is not what the viewer sees
    g = np.asarray(_bg.convert('L').resize((270, 200))).astype(float)
    if prev is not None: dl.append(float(np.abs(g - prev).mean()))
    prev = g
spikes = []
for i, d_ in enumerate(dl):
    loc = dl[max(0, i - 7):i] + dl[i + 1:i + 8]
    med = float(np.median(loc)) if loc else 0.0
    if d_ > 3 * max(med, 0.3) and d_ > layout.get('flash_floor', 1.5): spikes.append({'frame': i + 1, 'delta': round(d_, 2), 'local_median': round(med, 2)})
R['flash'] = {'spikes': spikes, 'max_delta': round(max(dl), 2) if dl else 0, 'ok': not spikes}
# 8 visible events, measured in the rendered band frames (a scene key is not proof): layout["event_checks"] =
# [{"name":"nudge","a":0,"b":8,"roi":[x0,y0,x1,y1] (fractions),"metric":"luma_delta"|"bright_gain","min":v}]
def _roi(i, roi):
    im = Image.open(os.path.join(fdir, sorted(os.listdir(fdir))[i])).convert('L'); w_, h_ = im.size
    return np.asarray(im.crop((int(roi[0] * w_), int(roi[1] * h_), int(roi[2] * w_), int(roi[3] * h_)))).astype(float)
ev = []
for c in layout.get('event_checks', []):
    A, B = _roi(c['a'], c['roi']), _roi(c['b'], c['roi'])
    if c['metric'] == 'specks':   # point-like bright blobs (particles): luma 30+ above the 9x9 local mean
        from scipy.ndimage import uniform_filter
        sp = lambda X: int(((X - uniform_filter(X, 9)) > 30).sum())
        ev.append({'name': c['name'], 'value': sp(B) - sp(A), 'min': c['min'], 'ok': sp(B) - sp(A) >= c['min']}); continue
    v_ = float(np.abs(B - A).mean()) if c['metric'] == 'luma_delta' else float(((B > 215).mean() - (A > 215).mean()) * 100) if c['metric'] == 'bright_gain' else float(B.mean() - A.mean())
    ev.append({'name': c['name'], 'value': round(v_, 2), 'min': c['min'], 'ok': v_ >= c['min']})
R['events'] = {'checks': ev, 'ok': all(e['ok'] for e in ev)}
# 9 clipped whites: layout["clip_checks"] = [{"frame":140,"roi":[fractions],"max_frac":0.02}] -> share of pixels with any channel >= 250
cl = []
for c in layout.get('clip_checks', []):
    im = Image.open(os.path.join(fdir, sorted(os.listdir(fdir))[c['frame']])).convert('RGB'); w_, h_ = im.size; r_ = c['roi']
    a_ = np.asarray(im.crop((int(r_[0] * w_), int(r_[1] * h_), int(r_[2] * w_), int(r_[3] * h_))))
    fr = float((a_.max(-1) >= 250).mean()); cl.append({'frame': c['frame'], 'clipped_frac': round(fr, 4), 'max': c['max_frac'], 'ok': fr <= c['max_frac']})
R['clip'] = {'checks': cl, 'ok': all(x['ok'] for x in cl)}
# 10 holes to the background: layout["black_checks"] = [{"frame":240,"roi":[fractions],"max_frac":0.01}] -> share of near-black (max channel < 14) pixels
bk = []
for c in layout.get('black_checks', []):
    im = Image.open(os.path.join(fdir, sorted(os.listdir(fdir))[c['frame']])).convert('RGBA'); w_, h_ = im.size; r_ = c['roi']
    a_ = np.asarray(im.crop((int(r_[0] * w_), int(r_[1] * h_), int(r_[2] * w_), int(r_[3] * h_)))).astype(float)
    blk = ((a_[..., :3].max(-1) < 14) | (a_[..., 3] < 20)).mean(); bk.append({'frame': c['frame'], 'black_frac': round(float(blk), 4), 'max': c['max_frac'], 'ok': blk <= c['max_frac']})
R['black'] = {'checks': bk, 'ok': all(x['ok'] for x in bk)}
# CC BY attribution belongs in the episode description.
if layout.get('assets_manifest'):
    from description_gate import check_description
    manifest = json.load(open(layout['assets_manifest']))
    ep_path = os.path.abspath(layout['episode_json'])
    credit_declared = bool(json.load(open(ep_path)).get('credits'))
    need = [a['name'] for a in manifest if re.search(r'CC[ -]BY', a.get('licence',''))]
    description_ok, detail = check_description(os.path.join(os.path.dirname(ep_path),'description.txt'))
    R['credits'] = {'attribution_assets': need, 'in_video_credit': credit_declared,
                    'description': detail, 'ok': not credit_declared and (not need or description_ok)}
for v in R.values():
    if isinstance(v, dict): v['ok'] = bool(v['ok'])
R['noise']['blocking'] = '--draft' not in sys.argv
R['pass'] = all(v['ok'] for k, v in R.items() if isinstance(v, dict) and (k != 'noise' or v['blocking']))
print(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))); sys.exit(0 if R['pass'] else 1)
