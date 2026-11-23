#!/usr/bin/env python3
"""Runs the media_checks gates on one draft.  usage: python draft_checks.py EPISODE_DIR TAG [PREV_TAG] [--blend X.blend] [--inputs DIR] [--out DIR]
Inputs the builder writes (all in EPISODE_DIR):
  changes.json  {"TAG": {"windows": [[f0, f1], ...]}}     frames this draft claims to have changed (required from draft 2 on)
  items.json    [{"id", "frame", "box": [x0,y0,x1,y1] band px, "claim": "fixed"|"partial"|"not_fixed"}]  last review's items
  episode.json  optional "payoff_frames": [f, ...] for the figure check; "establishing": true if the clip opens on a person
Writes gates/<TAG>_media.json and verify_<TAG>.png (before/after crops cut from the two mp4s); exit 1 if any check fails."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media_checks as m, thresholds

a = [x for i, x in enumerate(sys.argv[1:]) if not x.startswith('--') and not sys.argv[i].startswith('--')]; E = os.path.abspath(a[0]); TAG = a[1]; PREV = a[2] if len(a) > 2 else None
opt = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
blend = opt('--blend'); IN = os.path.abspath(opt('--inputs', E)); OUT = os.path.abspath(opt('--out', E + '/gates'))
ep = json.load(open(E + '/episode.json')); lay = ep.get('layout', {}); by, bh = lay.get('band_y', 470), lay.get('band_h', 880)
mp4, fin, raw = f'{E}/{TAG}.mp4', f'{E}/frames_{TAG}', f'{E}/frames_{TAG}_raw'; R = {}
def run(name, fn, *args, **kw):
    try: ok, d = fn(*args, **kw)
    except Exception as ex: ok, d = False, {'error': repr(ex)}
    R[name] = {'ok': bool(ok), **d}

R['threshold_lock'] = {'ok': not thresholds.lock_errors(), 'errors': thresholds.lock_errors()}
run('mp4_matches_frames', m.mp4_matches_frames, mp4, fin, band_y=by, band_h=bh)
if PREV:
    ch = json.load(open(IN + '/changes.json')).get(TAG, {}) if os.path.exists(IN + '/changes.json') else {}
    if not ch.get('windows'): R['changed_beats_differ'] = {'ok': False, 'error': f'changes.json has no windows for {TAG}: declare what this draft changed'}
    else: run('changed_beats_differ', m.changed_beats_differ, mp4, f'{E}/{PREV}.mp4', ch['windows'])
    if not os.path.exists(IN + '/items.json'):
        R['claimed_fixes_visible']={'ok':False,'error':'missing previous review items'}
    else:
        run('claimed_fixes_visible', m.claimed_fixes_visible, mp4, f'{E}/{PREV}.mp4', json.load(open(IN + '/items.json')), sheet=f'{OUT}/verify_{TAG}.png', band_y=by)
run('no_speckle', m.speckle_frames, raw, m.frames_in(raw))
if ep.get('establishing') or ep.get('shots'):
    person_file=os.path.join(OUT,f'{TAG}_shot_evidence.json')
    person=json.load(open(person_file)) if ep.get('shots') else None
    run('establishing_shot', m.establishing_shot, raw, ep.get('fps',30),person)
if ep.get('payoff_frames'): run('figure_reads_human', m.figure_reads_human, fin, ep['payoff_frames'])
run('caption_evidence', m.caption_evidence, ep); run('caption_reading_speed', m.caption_reading_speed, ep); run('on_screen_wording', m.on_screen_wording, ep)
if ep.get('narration') and os.path.exists(E + '/audio/narration.json'):
    run('narration_snr', m.narration_snr, E + '/audio'); run('narration_gaps', m.narration_gaps, E + '/audio', ep)
if blend:
    fx = f'{OUT}/{TAG}_scene_facts.json'
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(fx): os.unlink(fx)
    result = subprocess.run([os.path.join(os.path.dirname(__file__), '../blender/launch.py'), '-b', blend, '--python-exit-code','1','-P', os.path.dirname(os.path.abspath(__file__)) + '/scene_facts.py', '--', fx, str(ep.get('rim_frame', 1))], capture_output=True)
    if result.returncode == 0 and os.path.exists(fx): f = json.load(open(fx)); run('rim_bevel', m.rim_bevel, f); run('no_3d_text', m.no_3d_text, f)
    else: R['scene_facts'] = {'ok': False, 'error': 'scene_facts.py wrote nothing'}
R['pass'] = all(v['ok'] for v in R.values() if isinstance(v, dict))
os.makedirs(OUT, exist_ok=True); json.dump(R, open(f'{OUT}/{TAG}_media.json', 'w'), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: (v['ok'] if isinstance(v, dict) else v) for k, v in R.items()})); sys.exit(0 if R['pass'] else 1)
