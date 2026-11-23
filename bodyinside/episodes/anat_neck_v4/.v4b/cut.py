"""Assemble the v4b recut from the existing neck episode frames."""
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import ceil, floor
from pathlib import Path
import json
import shutil
import subprocess
import sys

from PIL import Image
import soundfile as sf

STAGE = Path(__file__).resolve().parent
EPISODE = STAGE.parent
KIT = EPISODE.parents[1] / 'anat_kit'
V1 = EPISODE.parent / 'anat_neck'
V3 = EPISODE.parent / 'anat_neck_v3'
V3D = V3 / '.sol_v3d'
SOURCE = {
    'v3d': V3D / 'frames_final_hq_v3d',
    'text': EPISODE / 'frames_final_hq_v4_raw',
    'disc': V1 / 'frames_finalhq_raw',
    'neutral': EPISODE / '.v4/disc_frames',
}
FPS = 30
SIZE = (540, 440)
WHITE, GOLD = [255, 255, 255], [255, 184, 28]
CUE = [
    ('v3d', 0, 59, 1, 540, 440),         # Opening is exactly the original two-second person shot.
    ('v3d', 106, 117, 1, 540, 440),      # Cervical curve shown after the two-second opening.
]
SHOT_GROUPS = [
    CUE,
    [('v3d', 118, 170, 1, 540, 440), ('v3d', 171, 230, 1.08, 540, 426),
     ('v3d', 231, 298, 1.13, 550, 438)],
    [('text', 258, 301, 1, 540, 440), ('text', 302, 319, 1.10, 554, 424),
     ('text', 346, 403, 1.02, 535, 440)],
    [('v3d', 729, 773, 1.10, 530, 441), ('v3d', 774, 825, 1, 540, 440)],
    [('neutral', 0, 42, 1, 540, 440), ('disc', 513, 546, 1, 540, 440),
     ('disc', 547, 579, 1.08, 561, 443)],
    [('disc', 550, 572, 1.05, 536, 425), ('disc', 561, 579, 1.19, 568, 435),
     ('disc', 545, 567, 1.0, 540, 440), ('disc', 565, 581, 1.13, 548, 428)],
    [('disc', 581, 614, 1.02, 540, 440), ('disc', 615, 654, 1.15, 551, 451),
     ('disc', 655, 689, 1.03, 540, 440)],
    [('v3d', 856, 888, 1, 540, 440), ('v3d', 890, 923, 1, 540, 440)],
]
CLAIMS = ['C0', 'C1', 'C2', 'C6', 'C4', 'C5', 'C3', 'C6']
ACCENTS = ['C자', '하중 증가', '각도 변화', '앞으로', '압박 ↑', '퇴행 더 심해', '신경뿌리 압박', '귀는 어깨 위에?']


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n')


def build_timeline():
    old = load(EPISODE / 'episode.json')
    lines = load(STAGE / 'lines.json')
    keeps = ['fps', 'lufs', 'title', 'brand', 'layout', 'sfx_parts', 'sfx_bed']
    ep = {key: old[key] for key in keeps}
    ep.update(id='anat_neck_v4b', beats=[], narration=[], sfx=[], labels=[], scene_cuts_declared=[])
    ep['layout']['caption_size'] = 55
    ep['sfx_bed']['curve'] = [[0, .20], [2, .29], [33, .23], [36, .16]]
    timeline, timings = [], []
    for i, ((caption, script), group) in enumerate(zip(lines, SHOT_GROUPS)):
        start = len(timeline)
        delay = .55 if i == 4 else .105
        dur = sf.info(STAGE / f'audio/narr_{i}.wav').duration
        count = ceil((dur + delay + (.24 if i == 7 else .13)) * FPS)
        durations = [round((j+1)*count/len(group)) - round(j*count/len(group)) for j in range(len(group))]
        if i == 0:
            durations = [60, count - 60]
        elif i == 4:
            durations = [40, (count-40)//2, ceil((count-40)/2)]
        assert 0 < min(durations) <= max(durations) <= 60, (i, durations)
        for j, ((kind, a, b, zoom, x, y), length) in enumerate(zip(group, durations)):
            if timeline:
                ep['scene_cuts_declared'].append(len(timeline))
            for k in range(length):
                p = k / max(1, length-1)
                drift = 0 if kind in ('v3d', 'text') else .035 * p
                timeline.append((i, kind, a + (b-a)*p, zoom + drift, x, y, j, k))
        before, after = caption.split(ACCENTS[i], 1)
        ep['beats'].append(dict(t0=start/FPS, t1=len(timeline)/FPS, tag='', cap=[
            (t, c) for t, c in ((before, WHITE), (ACCENTS[i], GOLD), (after, WHITE)) if t
        ], claim=CLAIMS[i], claims_visual=i in (0, 1, 2, 3, 6, 7)))
        ep['narration'].append(dict(beat=i, text=script))
        expected = script.replace('60도', '육십도').replace('27킬로', '이십칠 킬로').replace('45도', '사십오도').replace('2천4백', '이천사백')
        rate = sum('가' <= c <= '힣' for c in expected) / dur
        timings.append(dict(line=i, beat=i, text=script, start=start/FPS+delay, end=start/FPS+delay+dur,
                            rate=round(rate, 2), file=f'narr_{i}.wav'))
        ep['sfx'].append(dict(part='whoosh' if i in (0, 2, 4, 7) else 'tick', t=start/FPS+.018, gain=.32))
    ep['duration'] = len(timeline)/FPS
    write(STAGE / 'episode.json', ep)
    write(STAGE / 'timeline.json', timeline)
    write(STAGE / 'audio/narration.json', timings)
    return ep, timeline


@lru_cache(maxsize=24)
def source_image(kind, frame):
    with Image.open(SOURCE[kind] / f'f_{frame:04}.png') as image:
        return image.convert('RGBa')


def band_for(row):
    _, kind, src, zoom, x, y, _, _ = row
    crop_w, crop_h = 1080/zoom, 880/zoom
    crop = (x-crop_w/2, y-crop_h/2, x+crop_w/2, y+crop_h/2)
    a, b = floor(src), ceil(src)
    def sample(f):
        return source_image(kind, f).transform(SIZE, Image.Transform.EXTENT, crop, Image.Resampling.BICUBIC)
    low = sample(a)
    return low if a == b else Image.blend(low, sample(b), src-a)


def render(ep, timeline):
    comp = STAGE / 'comp'
    raw = STAGE / 'frames_v4b_raw'
    raw.mkdir(exist_ok=True)
    canvas = Image.open(comp / 'base.png').convert('RGB').resize((540, 960), Image.Resampling.LANCZOS)
    captions = []
    for i in range(len(ep['beats'])):
        label = Image.open(comp / f'cap_{i}.png').convert('RGBA').resize((540, 960), Image.Resampling.LANCZOS)
        page = canvas.copy()
        page.paste(label, (0, 0), label)
        captions.append(page)
    background = Image.open(comp / 'band_bg.png').convert('RGB').resize(SIZE, Image.Resampling.LANCZOS)
    empty = Image.new('RGBa', SIZE)
    cuts = {f: band_for(timeline[f-1]) for f in ep['scene_cuts_declared']}
    break_start = round(ep['beats'][4]['t0'] * FPS)
    ending_start = round(ep['beats'][7]['t0'] * FPS)

    def frame(f):
        i, _, _, _, _, _, j, k = timeline[f]
        shot_start = f-k
        band = band_for(timeline[f])
        # Fade through the background for the standalone anatomy chapter and the return to the person.
        for point in (break_start, ending_start):
            if point - 14 <= f < point + 14:
                t = (point - f - 1)/14 if f < point else (f - point + 1)/14
                keep = t*t*(3-2*t)
                band = Image.blend(empty, band, keep)
                break
        else:
            if shot_start in cuts and k < 14:
                t = (k+1)/15
                band = Image.blend(cuts[shot_start], band, t*t*(3-2*t))
        band = band.convert('RGBA')
        band.save(raw / f'f_{f:04}.png', compress_level=1)
        scene = background.copy()
        scene.paste(band, (0, 0), band)
        page = captions[i].copy()
        page.paste(scene, (0, ep['layout']['band_y']//2))
        return page.tobytes()

    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
           '-video_size', '540x960', '-framerate', str(FPS), '-i', 'pipe:0', '-an',
           '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '25', '-pix_fmt', 'yuv420p',
           '-maxrate', '2200k', '-bufsize', '4400k', str(STAGE / 'picture.mp4')]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process, ThreadPoolExecutor(max_workers=6) as pool:
        for base in range(0, len(timeline), 36):
            for data in pool.map(frame, range(base, min(base+36, len(timeline)))):
                process.stdin.write(data)
        process.stdin.close()
        if process.wait():
            raise SystemExit('Picture encode failed')


def project_existing_metadata(ep, timeline):
    pose_v3, pose_text, pose_v1 = [load(p) for p in (V3D/'pose_dump.json', EPISODE/'pose_dump.json', V1/'pose_dump.json')]
    scene_v3, scene_text, scene_v1 = [load(p) for p in (V3D/'scene_dump.json', EPISODE/'scene_dump.json', V1/'scene_dump.json')]
    points = load(V3D / 'label_pos.json')
    drawn = load(V3D / 'plumb_draw.json')
    pose, scene, labels, drawing = {}, {'HumanFade': {}}, {'_plumb': {}}, {}
    for f, (i, kind, src, zoom, x, y, shot, k) in enumerate(timeline):
        key = str(round(src))
        pd, sd = {'v3d': (pose_v3, scene_v3), 'text': (pose_text, scene_text),
                  'disc': (pose_v1, scene_v1), 'neutral': ({}, {})}[kind]
        if key in pd:
            pose[f] = pd[key]
        scene['HumanFade'][f] = 0 if kind == 'neutral' else sd.get('HumanFade', {}).get(key, 0)
        if i == 7 and shot == 1 and k >= 14 and key in points['_plumb'] and key in drawn:
            labels['_plumb'][f] = points['_plumb'][key]
            drawing[f] = drawn[key]
    if drawing:
        first, last = min(drawing), max(drawing)
        plumb = next(l.copy() for l in load(V3D/'episode.json')['labels'] if l['kind'] == 'plumb')
        plumb.update(f0=first-1, f1=last+1)
        ep['labels'].append(plumb)
    frames_by_beat = [[f for f, row in enumerate(timeline) if row[0] == i] for i in range(8)]
    scene['Herniation'] = {
        f: scene_v1['Herniation'][str(round(row[2]))] for f, row in enumerate(timeline) if row[1] == 'disc'
    }
    scene['TextingDotsPulse'] = {
        f: scene_text['TextingDotsPulse'][str(round(row[2]))] for f, row in enumerate(timeline) if row[1] == 'text'
    }
    for i in (0, 1, 3, 7):
        for f in frames_by_beat[i]:
            _, kind, src, zoom, x, y, _, _ = timeline[f]
            if kind == 'v3d' and str(round(src)) in points:
                labels[f] = {
                    name: [(p[0]-x/1080)*zoom+.5, (p[1]-y/880)*zoom+.5]
                    for name,p in points[str(round(src))].items()
                }
    close = max(drawing)
    load_frames = frames_by_beat[1]
    pose_compare = lambda a,b: dict(type='pose_delta', joints=list(range(8)), f0=a, f1=b, min_deg=10)
    ep['beats'][0]['evidence'] = [dict(type='dump_change', key='HumanFade', f0=12, f1=frames_by_beat[0][-1], min=.5)]
    ep['beats'][1]['evidence'] = [pose_compare(load_frames[0]+12, load_frames[-1]-4)]
    dot_frames = frames_by_beat[2]
    ep['beats'][2]['evidence'] = [dict(type='object_scale', object='TextingDotsPulse', f=dot_frames[21], radius_mm=3, min_mm=3)]
    ep['beats'][3]['evidence'] = [dict(type='anchors_visible', anchors=['A_Ear','A_Acro'], frames=[f for f in frames_by_beat[3] if f in labels and 'A_Ear' in labels[f]][-2:])]
    ep['beats'][6]['evidence'] = [dict(type='object_scale', object='Herniation', f=frames_by_beat[6][-20], radius_mm=5.5, min_mm=5)]
    ep['beats'][7]['evidence'] = [dict(type='anchors_visible', anchors=['A_Ear','A_Acro'], frames=[close])]
    write(STAGE/'episode.json', ep)
    write(STAGE/'pose_dump.json', pose)
    write(STAGE/'scene_dump.json', scene)
    write(STAGE/'label_pos.json', labels)
    write(STAGE/'plumb_draw.json', drawing)
    if not (STAGE/'frames_v4b').exists():
        (STAGE/'frames_v4b').symlink_to('frames_v4b_raw', target_is_directory=True)
    shutil.copyfile(V3D/'gates/human_dump.json', STAGE/'gates/human_dump.json')


if __name__ == '__main__':
    ep, timeline = build_timeline()
    project_existing_metadata(ep, timeline)
    if '--configure' not in sys.argv:
        subprocess.run([sys.executable, str(KIT/'layout/compose.py'), str(STAGE)], check=True)
        render(ep, timeline)
