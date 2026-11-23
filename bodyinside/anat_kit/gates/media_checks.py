#!/usr/bin/env python3
"""Checks for the defect classes that used to be runbook-only, and for the process failures of neck reviews 10-13.
Every function returns (ok, detail). Thresholds come from the locked gates/thresholds.json (section media_checks).
Box coordinates are band px of the full-resolution band (1080 wide); frames of any size are scaled to that.

  mp4_matches_frames     the mp4 shows THIS draft's frame folder (median diff on opaque 3D pixels, sampled frames)
  changed_beats_differ   the windows a draft says it changed differ from the previous draft's mp4 (draft19 = draft17's picture)
  claimed_fixes_visible  each item the builder marks fixed differs from the previous draft at the reviewer's frame and box; crops
                         are cut from the two mp4s (never the frame folder) and saved as a before/after sheet
  rim_bevel              every visible cut structure has a cortical rim curve with bevel >= min_bevel_mm (scene_facts.py)
  no_3d_text             no FONT object renders on any frame: labels live only in the 2D layer (scene_facts.py)
  no_speckle             translucent pixels are not salt-and-pepper (fast draft preset, draft19)
  figure_reads_human     payoff figure: visible silhouette height and brightness
  establishing_shot      the opening person (translucent skin) holds >= min_s from frame 0
  caption_evidence       every beat declares at least one evidence of a CHANGE (an object merely existing does not count)
  narration_snr          speech-to-SFX ratio per window, 300 Hz-4 kHz, while narration is active (draft19 masking)
  on_screen_wording      no jargon / source qualifiers on screen; no label that repeats its caption
"""
import os, sys, json, glob, re, subprocess
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thresholds import T
M = T['media_checks']
BAND_W = 1080

def load(p, w=BAND_W):
    """RGBA float array scaled to w px wide."""
    im = Image.open(p).convert('RGBA')
    if im.width != w: im = im.resize((w, round(im.height * w / im.width)), Image.BOX if im.width > w else Image.BILINEAR)
    return np.asarray(im).astype(np.float32)

def on_black(a): return a[..., :3] * (a[..., 3:4] / 255.0)
def luma(rgb): return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
def fpath(d, f): return os.path.join(d, 'f_%04d.png' % f)
def frames_in(d): return sorted(int(os.path.basename(p)[2:6]) for p in glob.glob(os.path.join(d, 'f_*.png')))

def mp4_frames(mp4, frames, w=270):
    """Decode the given frame numbers as grey arrays w px wide. Returns ({frame: array}, (W, H))."""
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', mp4], capture_output=True, text=True).stdout)['streams'][0]
    h = round(pr['height'] * w / pr['width']) // 2 * 2; frames = sorted(set(frames))
    sel = '+'.join(f'eq(n\\,{f})' for f in frames)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-vf', f"select='{sel}',scale={w}:{h},format=gray", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-'], capture_output=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    return dict(zip(frames, arr)), (pr['width'], pr['height'])

# ---------------- process
def mp4_matches_frames(mp4, frames_dir, frames=None, band_y=470, band_h=880):
    c = M['mp4_matches_frames']; nums = frames or frames_in(frames_dir)[::c['step']]
    dec, (W, H) = mp4_frames(mp4, nums); s = 270 / W
    y0 = round(band_y / 1920 * H * s); y1 = round((band_y + band_h) / 1920 * H * s); bad, worst = [], 0.0
    for f in nums:
        if f not in dec or not os.path.exists(fpath(frames_dir, f)): bad.append([f, 'missing']); continue
        a = np.asarray(Image.open(fpath(frames_dir, f)).convert('RGBA').resize((270, y1 - y0), Image.BOX)).astype(np.float32)
        op = a[..., 3] > 240
        if op.sum() < 200: continue
        d = float(np.median(np.abs(ndi.gaussian_filter(luma(a[..., :3]), 1) - ndi.gaussian_filter(dec[f][y0:y1], 1))[op])); worst = max(worst, d)
        if d > c['max_median_diff']: bad.append([f, round(d, 1)])
    return not bad, {'sampled': len(nums), 'worst': round(worst, 1), 'mismatch': bad[:12], 'max_median_diff': c['max_median_diff']}

def changed_beats_differ(mp4, prev_mp4, windows):
    c = M['changed_beats_differ']; out, ok = [], True
    for f0, f1 in windows:
        nums = list(range(f0, f1 + 1, max(1, (f1 - f0) // 8)))
        a, _ = mp4_frames(mp4, nums, w=135); b, _ = mp4_frames(prev_mp4, nums, w=135)
        d = float(np.mean([np.abs(ndi.gaussian_filter(a[f], 1.5) - ndi.gaussian_filter(b[f], 1.5)).mean() for f in nums if f in a and f in b]))
        out.append([f0, f1, round(d, 2)]); ok &= d >= c['min_diff']
    return ok, {'windows_[f0,f1,diff]': out, 'min_diff': c['min_diff']}

def _crop_mp4(src, f, box, band_y):
    x0, y0, x1, y1 = box
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f"select='eq(n\\,{f})',scale=1080:1920,crop={x1-x0}:{y1-y0}:{x0}:{y0+band_y},format=rgb24",
                          '-fps_mode', 'passthrough', '-frames:v', '1', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(y1 - y0, x1 - x0, 3).astype(np.float32)

def claimed_fixes_visible(mp4, prev_mp4, items, sheet=None, band_y=470):
    """items: [{id, frame, box, claim: 'fixed'|'partial'|'not_fixed'}]. A 'fixed' item whose crop barely differs from the previous
    draft is a false claim. A difference does not prove the fix: the crops go to review_gate (items.json) for the judgement."""
    c = M['claimed_fixes_visible']; res, ok, tiles = [], True, []
    for it in items:
        a, b = _crop_mp4(prev_mp4, it['frame'], it['box'], band_y), _crop_mp4(mp4, it['frame'], it['box'], band_y)
        d = float(np.abs(ndi.gaussian_filter(luma(a), 3) - ndi.gaussian_filter(luma(b), 3)).mean())
        fake = it.get('claim') == 'fixed' and d < c['min_diff']; ok &= not fake
        res.append({'id': it['id'], 'frame': it['frame'], 'diff': round(d, 2), 'claim': it.get('claim'), 'false_claim': fake}); tiles.append((a, b))
    if sheet and tiles:
        h = max(t[0].shape[0] for t in tiles); w = sum(t[0].shape[1] + 10 for t in tiles); img = Image.new('RGB', (w, 2 * h + 10)); x = 0
        for a, b in tiles:
            img.paste(Image.fromarray(a.astype('uint8')), (x, 0)); img.paste(Image.fromarray(b.astype('uint8')), (x, h + 10)); x += a.shape[1] + 10
        img.save(sheet)
    return ok, {'items': res, 'min_diff': c['min_diff'], 'sheet': sheet}

# ---------------- scene (scene_facts.py output)
def rim_bevel(facts):
    c = M['rim_bevel']; rims = {r['name'][4:]: r for r in facts['rims']}; bad = []
    for s in facts['cut_structures']:
        k = s.replace(' ', '_'); r = rims.get(k) or rims.get(s)
        if not r: bad.append([s, 'no rim'])
        elif r['bevel_mm'] < c['min_bevel_mm']: bad.append([s, r['bevel_mm']])
    return not bad, {'thin_or_missing_[structure,bevel_mm]': bad, 'min_bevel_mm': c['min_bevel_mm']}

def no_3d_text(facts):
    f = facts.get('font_objects_rendered', []); return not f, {'font_objects_rendered': f}

# ---------------- picture
def no_speckle(frame):
    """At a 270 px working width (so a 25 % draft and a final are compared alike): mean |luma - 3x3 median| / local mean on
    translucent pixels (0.05 < alpha < 0.95)."""
    c = M['no_speckle']; a = load(frame, 270); al = a[..., 3] / 255; g = luma(on_black(a))
    tr = ndi.binary_erosion((al > 0.05) & (al < 0.95), iterations=1)
    if tr.sum() < c['min_px']: return True, {'translucent_px': int(tr.sum()), 'note': 'too little translucent area to judge'}
    s = float((np.abs(g - ndi.median_filter(g, 3)) / (ndi.uniform_filter(g, 5) + 8))[tr].mean())
    return s <= c['max_rel_residual'], {'rel_residual': round(s, 3), 'translucent_px': int(tr.sum()), 'max_rel_residual': c['max_rel_residual']}

def speckle_frames(raw, frames):
    samples = [(frame, no_speckle(fpath(raw, frame))) for frame in frames]
    failures = [frame for frame, (ok, _) in samples if not ok]
    worst = max((detail.get('rel_residual', 0) for _, (_, detail) in samples), default=0)
    return bool(samples) and not failures, {'worst': worst, 'failing_frames': failures[:12]}

def figure_reads_human(frames_dir, frames):
    c = M['figure_reads_human']; res, ok = [], True
    for f in frames:
        a = load(fpath(frames_dir, f), 540); g = luma(on_black(a)); vis = ndi.binary_opening(g > c['vis_luma'], iterations=2)
        ys = np.where(vis.any(1))[0]; h = (ys[-1] - ys[0] + 1) / a.shape[0] if len(ys) else 0.0
        lum = float(g[vis].mean()) if vis.any() else 0.0; good = h >= c['min_height'] and lum >= c['min_luma']; ok &= bool(good)
        res.append({'f': f, 'height': round(float(h), 3), 'luma': round(lum, 1), 'ok': bool(good)})
    return ok, {'frames': res, 'min_height': c['min_height'], 'min_luma': c['min_luma']}

def establishing_shot(raw_dir, fps=30, person=None):
    """Frames from 0 in order (every frame or a fixed step); held = translucent-skin area >= min_area."""
    c = M['establishing_shot']; nums = [f for f in frames_in(raw_dir) if f <= fps * 4]; held = 0
    if person is not None:
        # Modern Astra skin is opaque. Measure the evaluated skin material,
        # render visibility and actual occupied pixels in each required frame.
        from thresholds import T
        need=round(T['human']['opening_s'] * fps)
        for f in range(need):
            al=load(fpath(raw_dir,f),270)[...,3]/255
            if person.get(str(f),{}).get('skin_alpha',0)<.6 or float((al>.05).mean())<c['min_area']:
                return False, {'person_held_s':f/fps,'required_frames':need}
        return True,{'person_held_s':need/fps,'required_frames':need}
    for f in nums:
        al = load(fpath(raw_dir, f), 270)[..., 3] / 255
        if float(((al > 0.05) & (al < 0.95)).mean()) < c['min_area']: break
        held = f
    return held / fps >= c['min_s'], {'person_held_s': round(held / fps, 2), 'min_s': c['min_s']}

CHANGE_EVIDENCE = {'pose_delta', 'pose_ratio', 'dump_change', 'anchors_visible', 'anchors_apart', 'anchors_aligned'}
def caption_evidence(ep):
    """Every beat carries >= 1 evidence of a change the caption claims. object_scale (an object exists at some size) is accepted
    only next to a change evidence: neck draft17 beat index 4 '계속 버텨야 한다' passed on a MuscleGlow object while the muscles held
    still (a muscle shortening keyed as a scene_dump value satisfies dump_change). Beats with claims_visual: false are exempt."""
    bad = []
    for i, b in enumerate(ep.get('beats', [])):
        if not b.get('claims_visual', True): continue
        types = {e.get('type') for e in b.get('evidence', [])}
        if not types & CHANGE_EVIDENCE: bad.append([i, sorted(types)])
    return not bad, {'beats_without_change_evidence_[beat,types]': bad, 'accepted': sorted(CHANGE_EVIDENCE)}

# ---------------- audio
def _band(x, sr, lo=300, hi=4000):
    from scipy.signal import butter, sosfiltfilt
    return sosfiltfilt(butter(4, [lo, hi], 'bandpass', fs=sr, output='sos'), x)

def narration_snr(audio_dir):
    """Voice = narr files placed at narration.json starts (x1.2, the mix gain). SFX = sfx_ducked.wav if the narration stage wrote it,
    else sfx_only.wav ducked with layout/narration.py's law. Per window with active voice, band-limited voice/SFX RMS in dB >= min_db."""
    import soundfile as sf
    c = M['narration_snr']; info = json.load(open(audio_dir + '/narration.json'))
    st = next((audio_dir + '/' + n for n in ('sfx_ducked.wav', 'sfx_ducked.flac') if os.path.exists(audio_dir + '/' + n)), None)
    src = st or next(audio_dir + '/' + n for n in ('sfx_only.wav', 'sfx_only.flac') if os.path.exists(audio_dir + '/' + n))
    sfx, sr = sf.read(src, dtype='float32', always_2d=True); sfx = sfx.mean(1); voice = np.zeros(len(sfx), np.float32)
    for ln in info:
        y, _ = sf.read(audio_dir + '/' + ln['file'], dtype='float32', always_2d=True); y = y.mean(1)
        s0 = int(round(ln['start'] * sr)); e0 = min(len(voice), s0 + len(y)); voice[s0:e0] = y[:e0 - s0]
    if not st:
        w = int(sr * 0.02); env = np.sqrt(np.convolve(voice ** 2, np.ones(w) / w, 'same')); g = (env > 0.01).astype(np.float32)
        g = np.convolve(g, np.ones(int(sr * .25)) / int(sr * .25), 'same'); sfx = sfx * (1 - 0.6 * np.clip(g, 0, 1))
    v, s = _band(voice * 1.2, sr), _band(sfx, sr); W = int(sr * c['win_s']); bad, n = [], 0
    for i in range(0, len(v) - W, W):
        rv = float(np.sqrt(np.mean(v[i:i + W] ** 2)))
        if rv < c['voice_active_rms']: continue
        n += 1; db = 20 * np.log10(rv / (float(np.sqrt(np.mean(s[i:i + W] ** 2))) + 1e-9))
        if db < c['min_db']: bad.append([round(i / sr, 2), round(db, 1)])
    return not bad, {'masked_windows_[t,db]': bad, 'voice_windows': n, 'min_db': c['min_db'], 'sfx_stem': os.path.basename(src) + ('' if st else ' + duck law')}

def narration_gaps(audio_dir, ep):
    """Silence inside a beat: beat start to first speech, last speech to beat end, measured on the voice itself (frames above
    -40 dBFS in 20 ms windows), not on file lengths (neck review 12-13: 1.4-3.3 s silent stretches over the curve, disc and
    muscle beats)."""
    import soundfile as sf
    c = M['narration_gaps']; bad = []; rows = []
    for ln in json.load(open(audio_dir + '/narration.json')):
        y, sr = sf.read(audio_dir + '/' + ln['file'], dtype='float32', always_2d=True); y = y.mean(1); w = int(sr * 0.02)
        rms = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, 'same')); on = np.where(rms > 10 ** (-40 / 20))[0]
        if not len(on): bad.append([ln['beat'], 'silent line']); continue
        s0, s1 = ln['start'] + on[0] / sr, ln['start'] + on[-1] / sr; b = ep['beats'][ln['beat']]
        gap = max(s0 - b['t0'], b['t1'] - s1); rows.append([ln['beat'], round(gap, 2)])
        if gap > c['max_gap_s']: bad.append([ln['beat'], round(gap, 2)])
    return not bad, {'gaps_[beat,s]': bad, 'all_[beat,s]': rows, 'max_gap_s': c['max_gap_s']}

# ---------------- wording
def caption_reading_speed(ep):
    """Characters (Hangul, letters, digits) per second of caption time (CEO check: 7.8 chars/s was tight)."""
    import re
    c = M['caption_reading_speed']; bad = []
    for i, b in enumerate(ep.get('beats', [])):
        t = ''.join(s[0] if isinstance(s, list) else str(s) for s in b.get('cap', [])); n = len(re.sub(r'[^가-힣A-Za-z0-9]', '', t))
        cps = n / max(1e-6, b['t1'] - b['t0'])
        if cps > c['max_cps']: bad.append([i, t, round(cps, 1)])
    return not bad, {'too_fast_[beat,caption,cps]': bad, 'max_cps': c['max_cps']}

def on_screen_wording(ep):
    def flat(value):
        return ''.join(str(value).split()).casefold()

    captions = [''.join(seg[0] if isinstance(seg, list) else str(seg) for seg in beat.get('cap', [])) for beat in ep.get('beats', [])]
    items = [('note', str(note)) for note in ep.get('notes', [])]
    for label in ep.get('labels', []):
        items.extend((label.get('id'), str(label.get(field, ''))) for field in ('text', 'sub'))
        items.extend((label.get('id'), str(item.get('text', ''))) for item in label.get('items', []))
    lines = items + [('caption', cap) for cap in captions] + [('title', line) for line in ep.get('title', [])]
    if ep.get('layout', {}).get('tags'):
        lines.extend(('tag', beat.get('tag', '')) for beat in ep.get('beats', []))
    banned = [(word, re.compile(r'\s*'.join(map(re.escape, word.split())), re.I)) for word in M['on_screen_wording']['banned']]
    bad = [[key, value, 'banned word ' + word] for key, value in lines for word, pattern in banned if pattern.search(str(value))]
    caption_text = [flat(cap) for cap in captions]
    for key, value in items:
        text = flat(value)
        if len(text) >= 4 and any(text in cap for cap in caption_text):
            bad.append([key, value, 'repeats the caption'])
    return not bad, {'violations': bad}

if __name__ == '__main__':
    fn = globals()[sys.argv[1]]
    a = [json.load(open(x)) if x.endswith('.json') and fn.__name__ in ('rim_bevel', 'no_3d_text', 'caption_evidence', 'on_screen_wording')
         else (json.loads(x) if x[:1] in '[{' or x.isdigit() else x) for x in sys.argv[2:]]
    ok, d = fn(*a); print(json.dumps({'ok': bool(ok), **d}, ensure_ascii=False, default=float)); sys.exit(0 if ok else 1)
