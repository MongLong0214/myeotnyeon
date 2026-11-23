"""Assemble the v4 cut and remap the reused shot measurements to its frame clock."""
import json
import math
import os
from pathlib import Path
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / '.v4'
V3 = ROOT.parent / 'anat_neck_v3'
V3D = V3 / '.sol_v3d'
TEXTING = V3 / '.sol_v3b.sBcZnIjT' / 'B'
RAW = V3D / 'frames_final_hq_v3d_raw'
FINAL = V3D / 'frames_final_hq_v3d'
DISC = STAGE / 'disc_frames'
FPS = 30
LOAD, SEGMENT, PAYOFF, ANATOMY, CONTACT, CONTEXT, QUESTION, END = 84, 243, 418, 525, 638, 754, 862, 930
WIDTH, HEIGHT = SIZE = (1080, 880)
WHITE, GOLD = [255, 255, 255], [255, 184, 28]


def load(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')


def source_at(f):
    if f < LOAD:
        return 'v3d', f
    if f < SEGMENT:
        return 'v3d', LOAD + (f - LOAD) * (299 - LOAD) / (SEGMENT - LOAD - 1)
    if f < PAYOFF:
        return 'texting', 327 + f - SEGMENT
    if f < ANATOMY:
        return 'v3d', 729 + f - PAYOFF
    if f < QUESTION:
        return 'disc', f - ANATOMY
    return 'v3d', 856 + f - QUESTION


def configure():
    ep = load(V3D / 'episode.json')
    ep['id'] = 'anat_neck_v4'
    ep['duration'] = END / FPS
    ep.pop('build', None)
    ep['scene_cuts_declared'] = [SEGMENT, PAYOFF, ANATOMY, QUESTION]
    ep['xfades'] = []
    caps = [
        [('목뼈는 원래 ', WHITE), ('C자', GOLD), (' 곡선', WHITE)],
        [('고개 숙일수록 ', WHITE), ('하중 증가', GOLD)],
        [('문자 입력 중, ', WHITE), ('목뼈 마디 각도 변화', GOLD)],
        [('머리가 몸통보다 ', WHITE), ('앞으로', GOLD)],
        [('목 디스크 탈출', GOLD)],
        [('디스크가 ', WHITE), ('신경뿌리', GOLD), ('를 누를 수 있어요', WHITE)],
        [('자세가 원인이라는 뜻은 아니에요', WHITE)],
        [('지금 내 ', WHITE), ('귀', GOLD), ('는 어깨 위에?', WHITE)],
    ]
    desc = [
        'Texting person and the opening dissolve into the cervical curve',
        'Head flexion and the modelled load arrow',
        'One texting skeleton with three dots at C1-C2, C3-C4 and C4-C5',
        'One texting posture, with ear and acromion landmarks',
        'Dip to the neutral cervical section, then move in toward C5-C6',
        'C5-C6 protrudes toward the adjacent nerve root on the neutral model',
        'Continue the same stand-alone anatomy chapter',
        'The ear and shoulder landmarks in the v3d closing view',
    ]
    def change(key, a, b, amount):
        return dict(type='dump_change', key=key, f0=a, f1=b, min=amount)

    def visible(frames):
        return dict(type='anchors_visible', anchors=['A_Ear', 'A_Acro'], frames=frames)

    evidence = [
        [change('VertebraTint', 84, 99, 0.5)],
        [dict(type='pose_delta', joints=list(range(8)), f0=110, f1=237, min_deg=30)],
        [change('TextingDotsPulse', 310, 334, 0.7)],
        [visible([450, 480, 513]),
         dict(type='anchors_apart', a='A_Ear', b='A_Acro', frames=[510, 513], min_dy=0.2)],
        [],
        [dict(type='object_scale', object='Herniation', f=725, radius_mm=5.5, min_mm=9)],
        [],
        [visible([915, 924]),
         dict(type='anchors_apart', a='A_Ear', b='A_Acro', frames=[915, 924], min_dy=0.2),
         dict(type='anchors_aligned', a='A_Ear', b='A_Acro', frames=[915, 924], max_dx=0.04)],
    ]
    edges = [0, LOAD, SEGMENT, PAYOFF, ANATOMY, CONTACT, CONTEXT, QUESTION, END]
    ep['beats'] = [dict(t0=a/FPS, t1=b/FPS, tag='', cap=cap, action=action, evidence=ev,
                        claims_visual=bool(ev), claim=claim)
                   for a,b,cap,action,ev,claim in zip(edges, edges[1:], caps, desc, evidence,
                                                      ['C0','C1','C2','C6','C3','C3','C3','C6'])]
    segment_text = load(STAGE / 'line_0.json')[0]
    disc_text = load(STAGE / 'line_1.json')[0]
    old_lines = [line['text'] for line in ep['narration']]
    ep['narration'] = [dict(beat=i, text=t) for i, t in enumerate([
        old_lines[0], old_lines[1], segment_text, old_lines[4],
        *[s.strip() + '.' for s in disc_text.rstrip('.').split('.')], old_lines[5],
    ])]
    ep['narration'][0]['spoken'] = '목뼈는 원래 앞으로 살짝 휜 씨짜예요.'
    ep['narration'][1]['spoken'] = old_lines[1].replace('하중', '하-중')
    labels = {label['id']: label for label in ep['labels'] if 'split_half' not in label}
    for label_id in ('kg0', 'kg15', 'kg30', 'kg60'):
        label = labels[label_id]
        for key in ('f0', 'f1'):
            label[key] = LOAD + round((label[key]-LOAD)*(SEGMENT-LOAD-1)/(299-LOAD))
    labels['gap'].update(f0=439, f1=523, ramp_out=9, hold_end=False)
    labels['plumb'].update(f0=QUESTION+9, f1=END-1, ramp=4)
    # Anatomic callouts are timed to the disc and nerve-root words and track their 3D anchors.
    for label_id, text, anchor, f0, f1, dx, dy in (
        ('disc_normal', '디스크', 'A_C56', 561, 627, 260, -80),
        ('disc_bulge', '튀어나온 디스크', 'A_C56', 660, 709, 264, -73),
        ('nerve_root', '신경뿌리', 'A_Contact', 702, 748, -260, -125),
        ('disc_context', '디스크', 'A_C56', 772, 820, 264, -73),
    ):
        labels[label_id] = dict(id=label_id, kind='callout', text=text, anchor=anchor,
                                 f0=f0, f1=f1, dx=dx, dy=dy, size=48, ramp=9, claim='C3')
    # Only one callout is present at a time to keep leaders clear during the close-up.
    labels['disc_bulge']['f1'] = labels['nerve_root']['f0'] - 1
    ep['labels'] = list(labels.values())
    ep['rigid_bend_check']['frames'] = [180, 210, 237, 282, 340, 400]
    ep['subject_size_allow'] = [[0,16], [84,97], [SEGMENT, SEGMENT+10],
                                [PAYOFF, PAYOFF+10], [ANATOMY-8, ANATOMY+10],
                                [QUESTION-7, QUESTION+10], [QUESTION+25, QUESTION+42]]
    ep['scene_visibility'] = {
        'CurveLine': [[84, 131], [233, 250]],
        'Shoulder': [[QUESTION, END-1]],
        'SkinRender': [[0, 116], [PAYOFF, ANATOMY-1], [QUESTION, END-1]],
        'Herniation': [[ANATOMY+120, QUESTION-1]],
        'TextingDotsPulse': [[SEGMENT, PAYOFF-1]],
        'MuscleGlow': [],
    }
    ep['contact_color_check'] = dict(f0=716, f1=743, min_px=150)
    events = [
        ('whoosh', .20, .6), ('pulse', .45, .55), ('tick', 1., .60),
        ('tick', 4.13, .65), ('creak', 4.35, .94), ('tick', 5.71, .67),
        ('creak', 5.95, .94), ('tick', 7.3, .65), ('creak', 7.46, .94),
        ('whoosh', 8.08, .75), ('tick', 10.11, .64), ('tick', 11.28, .75),
        ('whoosh', 13.91, .65), ('tick', 14.72, .80), ('whoosh', 15.71, .49),
        ('whoosh', 17.52, .9), ('tick', 19.08, .55), ('tick', 21.32, .64),
        ('pulse', 23.83, .55), ('tick', 25.42, .55), ('whoosh', 27.17, .47),
        ('whoosh', 28.78, .68), ('tick', 29.10, .55),
    ]
    ep['sfx'] = [dict(part=n, t=t, gain=g) for n,t,g in events]
    used = {n for n, _, _ in events} | {'bed'}
    ep['sfx_parts'] = [part for part in ep['sfx_parts'] if part['id'] in used]
    ep['sfx_bed']['curve'] = [[0,.4], [4,.55], [16.8,.55], [17.5,.16],
                             [17.85,.58], [28.75,.5], [30.5,.4]]
    for key, val in zip(('assets.json', 'thresholds.json'), (V3D/'assets.json', V3D/'thresholds.json')):
        shutil.copyfile(val, ROOT/key)
    assets = load(ROOT/'assets.json')
    assets[0]['name'] = assets[0]['name'].replace(', neck muscles', '')
    save(ROOT/'assets.json', assets)
    save(ROOT/'episode.json', ep)
    return ep


def frame_path(directory, f):
    return directory / f'f_{f:04}.png'


def read(directory, f):
    with Image.open(frame_path(directory, f)) as im:
        return im.convert('RGBA')


def blend(im1, im2, k):
    return Image.blend(im1.convert('RGBa'), im2.convert('RGBa'), k).convert('RGBA')


def ease(t):
    t = max(0, min(1, t))
    return t*t*(3-2*t)


def reframe(im, scale, center):
    scale_x = 1 / scale
    return im.transform(SIZE, Image.Transform.AFFINE, (
        scale_x, 0, center[0]-WIDTH*scale_x/2,
        0, scale_x, center[1]-HEIGHT*scale_x/2,
    ), Image.Resampling.BICUBIC)


def texting(f):
    k = f - SEGMENT
    im = read(TEXTING, 327+k)
    center_x = 786 + 85*math.sin(math.pi * k / 176)**2
    center_y = 422 + 41*math.sin(math.pi * k / 176)**2
    zoom_in = ease((k-44)/13) * (1-ease((k-101)/12))
    zoom = 1.45 + .24 * zoom_in + .006 * math.sin(k/8)
    return reframe(im, zoom, (center_x, center_y-31*zoom_in))


def payoff_reframe(f):
    progress = ease((f-469)/15)
    return 1 + .11*progress, (540+50*progress, 440-17*progress)


def payoff(f):
    im = read(RAW, 729+f-PAYOFF)
    scale, center = payoff_reframe(f)
    return reframe(im, scale, center) if scale != 1 else im


def render_frame(f, kind, src):
    empty = Image.new('RGBA', SIZE)
    if kind == 'texting':
        im = texting(f)
        if f < SEGMENT+11:
            im = blend(read(RAW,299), im, (f-SEGMENT+1)/11)
        return im
    if PAYOFF <= f < ANATOMY:
        im = payoff(f)
        if f < PAYOFF+10:
            im = blend(texting(PAYOFF-1), im, (f-PAYOFF+1)/10)
        if f >= ANATOMY-6:
            im = blend(im, empty, (f-(ANATOMY-7))/7)
        return im
    if kind == 'disc':
        im = read(DISC, src)
        if f < ANATOMY+8:
            im = blend(empty, im, (f-ANATOMY+1)/8)
        if f >= QUESTION-6:
            im = blend(im, empty, (f-(QUESTION-7))/7)
        return im
    if kind == 'v3d':
        if f >= QUESTION and f < QUESTION+8:
            return blend(empty, read(RAW,int(src)), (f-QUESTION+1)/8)
        a, b = math.floor(src), math.ceil(src)
        if a == b:
            return None
        return blend(read(RAW,a), read(RAW,b), src-a)
    raise ValueError(kind)


def frames(lo=0, hi=END):
    dst = ROOT/'frames_final_hq_v4_raw'
    dst.mkdir(exist_ok=True)
    for f in range(lo,hi):
        out = frame_path(dst,f)
        if out.exists():
            continue
        kind, src = source_at(f)
        if kind == 'disc' and ANATOMY+8 <= f < QUESTION-6:
            os.link(frame_path(DISC,src),out)
            continue
        im = render_frame(f,kind,src)
        if im is None:
            os.link(frame_path(RAW,int(src)),out)
        else:
            im.save(out, compress_level=2)


def remap():
    old_pose = load(V3D/'pose_dump.json')
    texting_pose = load(V3/'pose_dump_var.json')
    old_scene = load(V3D/'scene_dump.json')
    old_labels = load(V3D/'label_pos.json')
    disc_proj = load(STAGE/'disc_projection.json')
    disc_scale = load(STAGE/'disc_scale.json')
    plumb = old_labels['_plumb']
    pose, labels = {}, {'_plumb': {}}
    scene = {k: {} for k in ('EarShoulderGapCm','SkinRender','HumanFade','VertebraTint',
                              'CurveLine','Shoulder','Herniation','TextingDotsPulse','MuscleGlow')}
    neutral = [-4,-5,-6,-5,-4,-3,10,17]
    for f in range(END):
        kind, src = source_at(f)
        key = str(round(src))
        pose[f] = (old_pose[key] if kind == 'v3d' else texting_pose[key] if kind == 'texting' else neutral)
        for name in scene:
            scene[name][f] = old_scene[name][key] if kind == 'v3d' and name in old_scene and name != 'MuscleGlow' else 0
        if kind == 'texting':
            # The three source dots share this single, baked pulse centered at source f418.
            scene['TextingDotsPulse'][f] = 1 + .9*ease((src-404)/14)*ease((432-src)/14)
        if kind == 'disc':
            scene['Herniation'][f] = disc_scale[key]
            labels[f] = disc_proj[key]
        elif kind == 'v3d' and key in old_labels:
            entries = old_labels[key]
            if PAYOFF <= f < ANATOMY:
                scale, center = payoff_reframe(f)
                entries = {name: [(p[0]-center[0]/WIDTH)*scale + .5,
                                  (p[1]-center[1]/HEIGHT)*scale + .5] for name,p in entries.items()}
            labels[f] = entries
        if f >= QUESTION and key in plumb:
            labels['_plumb'][f] = plumb[key]
    save(ROOT/'pose_dump.json',pose)
    save(ROOT/'scene_dump.json',scene)
    save(ROOT/'label_pos.json',labels)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'configure':
        configure()
    elif cmd == 'frames':
        frames(*(map(int,sys.argv[2:]) if len(sys.argv)>2 else ()))
    elif cmd == 'remap':
        remap()
