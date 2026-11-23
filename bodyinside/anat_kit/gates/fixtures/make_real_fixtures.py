#!/usr/bin/env python3
"""Builds the regression fixtures of the media_checks classes from REAL bad drafts (read-only sources under work/episodes).
Each fixture dir gets check.json {fn, args, kwargs, origin}; paths in args are relative to the fixture dir. defects_meta.py runs
the call and requires it to FAIL. Media outputs (mp4/png/flac) are gitignored and rejected by the repo hook, so they are NOT committed: defects_meta.py
runs this script when a fixture's media is missing (sources: the draft folders under work/episodes, read-only). Scene facts come from scene_facts.py runs on the saved draft blends (SCENE_FACTS env: dir with
facts_n10.json and facts_w30.json); see each origin string."""
import os, sys, json, shutil, subprocess
import numpy as np
from PIL import Image

F = os.path.dirname(os.path.abspath(__file__)); W = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../../episodes'); N = W + '/anat_neck'
SF = os.environ.get('SCENE_FACTS', '')

def _w(path):
    """Committed JSON fixtures are never rewritten from the (moving) live episode files: write only if absent."""
    return open(os.devnull if os.path.exists(path) else path, 'w')

def mk(name, fn, args, origin, kwargs=None):
    d = f'{F}/{name}'; os.makedirs(d, exist_ok=True)
    json.dump({'fn': fn, 'args': args, 'kwargs': kwargs or {}, 'origin': origin}, open(d + '/check.json', 'w'), ensure_ascii=False, indent=1); return d

def clip(src, f0, f1, out, w=270):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f"select='between(n\\,{f0}\\,{f1})',setpts=N/30/TB,scale={w}:-2", '-r', '30',
                    '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-an', out], check=True)

def frame(src, dst, w=None):
    im = Image.open(src)
    if w: im = im.resize((w, round(im.height * w / im.width)), Image.BOX)
    im.save(dst, optimize=True)

# 1 mp4 assembled from another draft's frames: draft17's picture checked against draft19's frame folder (payoff f900-f960)
d = mk('mp4-from-stale-frames', 'mp4_matches_frames', ['clip.mp4', 'frames'],
       'neck draft17.mp4 f900-f960 against frames_draft19 f900/f930/f960 (review 13: draft19 file showed draft17 picture)', {'frames': [0, 30, 60]})
clip(N + '/draft17.mp4', 900, 960, d + '/clip.mp4', 540); os.makedirs(d + '/frames', exist_ok=True)
for i, f in enumerate((900, 930, 960)): frame(f'{N}/frames_draft19/f_{f:04d}.png', f'{d}/frames/f_{i*30:04d}.png')

# 2 claimed changes not in the picture: draft19 vs draft17 at the payoff and the opening hold (review 13 'NOT IN FILE')
d = mk('claimed-change-not-in-file', 'changed_beats_differ', ['new.mp4', 'prev.mp4', [[0, 90], [100, 190]]],
       'neck draft19.mp4 vs draft17.mp4, frames f885-f975 (payoff) -> clip 0-90 and f0-f90 (opening hold) -> clip 100-190')
for tag, out in (('draft19', 'new.mp4'), ('draft17', 'prev.mp4')):
    a, b = d + '/_a.mp4', d + '/_b.mp4'; clip(f'{N}/{tag}.mp4', 885, 975, a); clip(f'{N}/{tag}.mp4', 0, 90, b)
    # pad 9 frames between the two parts so windows 0-90 and 100-190 land inside them
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a, '-i', b, '-filter_complex', '[0]tpad=stop=9:stop_mode=clone[p];[p][1]concat=n=2:v=1[v]', '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', f'{d}/{out}'], check=True)
    for x in (a, b): os.remove(x)

# 3 a fix claimed but not visible: mouth smudge draft16 vs draft15 f900 (review 11: PARTIAL, smudge still there)
d = mk('claimed-fix-not-visible', 'claimed_fixes_visible', ['new.mp4', 'prev.mp4', [{'id': 'mouth-smudge', 'frame': 0, 'box': [650, 320, 700, 350], 'claim': 'fixed'}]],
       'neck draft16.mp4 vs draft15.mp4 frame 900, box 650-700 x 320-350 (fable_review11 Mouth smudge PARTIAL)')
for tag, out in (('draft16', 'new.mp4'), ('draft15', 'prev.mp4')): clip(f'{N}/{tag}.mp4', 900, 900, f'{d}/{out}', 1080)

# 4 cortical rim too thin: scene facts of neck_draft10.blend (review 7: no cortical rim on cut vertebrae)
d = mk('rim-too-thin', 'rim_bevel', ['facts.json'], 'scene_facts.py on episodes/anat_neck/neck_draft10.blend at f630 (fable_review7 round-6 item 5)')
if SF: shutil.copy(SF + '/facts_n10.json', d + '/facts.json')   # committed; rebuilt only when SCENE_FACTS is given

# 5 3D text: wisdom_draft30.blend carries GapLabel, a 3D FONT label (wisdom 3D-label era); visibility set rendered = derived
d = mk('text-in-3d-layer', 'no_3d_text', ['facts.json'], 'DERIVED: scene_facts of anat_wisdom/wisdom_draft30.blend lists FONT object GapLabel (hidden at save); fixture marks it rendered as in the wisdom 3D-label drafts')
if SF: fx = json.load(open(SF + '/facts_w30.json')); fx['font_objects_rendered'] = ['GapLabel']; json.dump(fx, open(d + '/facts.json', 'w'), indent=1)

# 6 speckle from the fast draft preset: draft19 raw f930 (payoff ghost) and f3 (opening ghost)
d = mk('fast-preset-speckle', 'no_speckle', ['f_0930.png'], 'neck frames_draft19_raw f930 (25 % 4 spp preset; translucent ghost unreadable)')
frame(f'{N}/frames_draft19_raw/f_0930.png', d + '/f_0930.png'); frame(f'{N}/frames_draft19_raw/f_0003.png', d + '/f_0003.png')

# 7 payoff figure small: draft17 composited f900, f930 (review 12: ~250 px tall in an 880 px band, dim)
d = mk('figure-small', 'figure_reads_human', ['frames', [900, 930]], 'neck frames_draft17 f900, f930 (fable_review12 payoff beat)')
os.makedirs(d + '/frames', exist_ok=True)
for f in (900, 930): frame(f'{N}/frames_draft17/f_{f:04d}.png', f'{d}/frames/f_{f:04d}.png')

# 8 establishing shot too short: draft17 raw f0-f60 every 3rd frame at 270 px (owner: person dissolves within 0.3 s)
d = mk('establishing-too-short', 'establishing_shot', ['frames'], 'neck frames_draft17_raw f0-f60 step 3, 270 px wide (owner feedback on draft17)')
os.makedirs(d + '/frames', exist_ok=True)
for f in range(0, 61, 3): frame(f'{N}/frames_draft17_raw/f_{f:04d}.png', f'{d}/frames/f_{f:04d}.png', 270)

# 9 a caption whose only evidence is an object existing: neck episode.json (draft17-19) beat 4 muscle line
ep = json.load(open(N + '/episode.json'))
d = mk('caption-without-change-evidence', 'caption_evidence', ['episode.json'], 'neck episode.json beats as of draft19: beat 4 (뒷목 근육이 계속 버텨야 한다) declares only object_scale MuscleGlow; fable_review10-13: muscles still')
json.dump({'beats': [{'cap': b['cap'], 'evidence': b.get('evidence', [])} for b in ep['beats']]}, _w(d + '/episode.json'), ensure_ascii=False, indent=1)

# 10 narration masked by SFX: draft19 stems (review 13: recogniser failed at 4-5.5, 12.5-14, 25-27 s)
d = mk('narration-masked', 'narration_snr', ['audio'], 'neck audio/ stems written for draft19 (17:44), resampled to 16 kHz FLAC')
os.makedirs(d + '/audio', exist_ok=True); info = json.load(open(N + '/audio/narration.json'))
for ln in info:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{N}/audio/{ln["file"]}', '-ar', '16000', '-ac', '1', f'{d}/audio/{ln["file"][:-4]}.flac'], check=True); ln['file'] = ln['file'][:-4] + '.flac'
json.dump(info, _w(d + '/audio/narration.json'), ensure_ascii=False, indent=1)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', N + '/audio/sfx_only.wav', '-ar', '16000', '-ac', '1', d + '/audio/sfx_only.flac'], check=True)

# 10b silent stretches inside narrated beats: same draft19 stems, beats of the draft19 episode.json
d = mk('narration-gaps', 'narration_gaps', ['../narration-masked/audio', 'episode.json'], 'neck draft19 stems + episode.json beats (fable_review12/13: 1.4-3.3 s silences)')
json.dump({'beats': [{'t0': b['t0'], 't1': b['t1']} for b in ep['beats']]}, _w(d + '/episode.json'), indent=1)

# 10c caption too fast to read: wisdom episode_draft21.json (CEO check: 7.8 chars/s, tight)
d = mk('caption-too-fast', 'caption_reading_speed', ['episode.json'], 'anat_wisdom/episode_draft21.json beats (ceo_checks.md section 2 reading time)')
json.dump({'beats': [{k: b[k] for k in ('t0', 't1', 'cap')} for b in json.load(open(W + '/anat_wisdom/episode_draft21.json'))['beats']]}, _w(d + '/episode.json'), ensure_ascii=False, indent=1)

# 11 jargon and source qualifiers on screen: the strings on neck draft07 f620 (transcribed from the frame)
d = mk('on-screen-jargon', 'on_screen_wording', ['episode.json'], 'strings visible in neck frames_draft07 f620: note "AANS · OrthoInfo 참고 도해", legend; caption of that beat')
json.dump({'beats': [{'cap': [['밀려난 디스크가 신경을 누를 수도', [255, 255, 255]]]}], 'labels': [{'id': 'legend1', 'text': '디스크'}, {'id': 'legend3', 'text': '밀려난 디스크'}],
           'notes': ['AANS · OrthoInfo 참고 도해']}, _w(d + '/episode.json'), ensure_ascii=False, indent=1)
print('fixtures written')
