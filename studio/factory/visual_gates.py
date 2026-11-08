"""Final-encode edge-fill measurements and canonical-hand review helpers.

2026-11-07: CEO caught; CTO missed (N18 B1/B2). No renderer is invoked.
"""
import json
import math
import re
import subprocess

import numpy as np


def edge_bands(rgb):
    """Find a flat edge fill separated from a multicolour scene by a straight cut.

    Work in decoded RGB, on all four edges, irrespective of fill colour. Allow
    scene lines/foreground to cross the fill. A uniform sky/ground alone is not
    evidence: the boundary must cut off multiple scene colours along its length.
    Returns conservative geometric candidates, not a semantic scene classifier.
    """
    found = []
    for edge, im in [('left', rgb), ('right', rgb[:, ::-1]),
                     ('top', rgb.transpose(1, 0, 2)),
                     ('bottom', rgb[::-1].transpose(1, 0, 2))]:
        length, depth = im.shape[:2]
        limit = max(3, depth // 4)
        strip = im[:, :limit].astype(np.int16)
        colour = np.median(strip[:, 0], axis=0)
        same = np.max(np.abs(strip - colour), axis=2) <= 10
        coverage = same.mean(axis=0)
        if coverage[0] < .70:
            continue
        # First end of the contiguous flat band. One antialiased boundary pixel
        # is allowed, but no search past an intervening piece of the scene.
        ends = np.flatnonzero(coverage < .70)
        width = int(ends[0]) if len(ends) else limit
        if width < 2 or width >= limit:
            continue
        outer = np.median(strip[:, :width], axis=1)
        # The change must be aligned at one depth, and persist into the scene.
        # A parking stripe, ceiling beam or panel outline followed by the same
        # floor/sky/wall colour is scene geometry, not missing background fill.
        inside = im[:, width+3:width+19].astype(np.int16)
        inner = np.median(inside, axis=1)
        near = im[:, max(0,width-2):width+3].astype(np.int16)
        aligned = (np.max(np.abs(np.diff(near,axis=1)),axis=2) >= 18).any(axis=1)
        persists = (np.max(np.abs(inside-colour),axis=2) >= 24).mean(axis=1) >= .75
        # A distinct ink stroke between two brighter surfaces is an authored
        # scene outline (e.g. desk edge), rather than the scene simply ending.
        low = near.mean(axis=2).min(axis=1)
        outside_luma = outer.mean(axis=1); inside_luma = inner.mean(axis=1)
        outlined = (low+18 < np.minimum(outside_luma,inside_luma)) & ((outside_luma-low) >= .5*(inside_luma-low))
        jump = (np.max(np.abs(inner - outer), axis=1) >= 24) & aligned & persists & ~outlined
        flat = np.max(np.abs(outer - colour), axis=1) <= 10
        support = jump & flat
        if support.mean() < .60:
            continue
        if sum(part.mean() >= .35 for part in np.array_split(support, 4)) < 3:
            continue
        scene = inner[support]
        if np.max(np.percentile(scene, 90, axis=0) - np.percentile(scene, 10, axis=0)) < 24:
            continue
        found.append(dict(edge=edge, width_px=width,
                          width_fraction=round(width/depth, 6),
                          flat_fraction=round(float(coverage[:width].mean()), 4),
                          boundary_fraction=round(float(support.mean()), 4),
                          fill_rgb=[int(v) for v in colour]))
    return found


def measure_edges(video, width=640):
    """Decode the entire encode; test frames at PTS gaps no larger than 0.2s.

    Use real presentation timestamps, including the first/last frame. Decode
    errors and missing timestamps cannot produce a passing coverage result.
    """
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                            '-show_streams', '-show_frames', '-show_entries',
                            'stream=width,height:frame=best_effort_timestamp_time',
                            '-of', 'json', str(video)], capture_output=True, check=True)
    meta = json.loads(probe.stdout)
    times = [float(f['best_effort_timestamp_time']) for f in meta['frames']]
    if not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Missing or non-monotonic encoded-frame timestamps')
    selected = {0, len(times)-1}
    anchor = 0
    for n in range(1, len(times)):
        if times[n]-times[anchor] > .2+1e-6:
            selected.add(n-1)
            anchor = n-1
            if times[n]-times[anchor] > .2+1e-6:
                selected.add(n)
                anchor = n
    stream = meta['streams'][0]
    height = round(stream['height']*width/stream['width']/2)*2
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(video), '-map', '0:v:0',
                             '-vf', f'scale={width}:{height}', '-fps_mode', 'passthrough',
                             '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    n = 0
    hits = []
    checked = []
    try:
        while True:
            raw = proc.stdout.read(width*height*3)
            if not raw:
                break
            if len(raw) != width*height*3:
                raise ValueError('Truncated encoded edge-fill frame')
            if n in selected:
                checked.append(n)
                rgb = np.frombuffer(raw, np.uint8).reshape(height, width, 3)
                hits += [dict(frame=n, time_s=times[n], **hit) for hit in edge_bands(rgb)]
            n += 1
        error = proc.stderr.read()
        if proc.wait():
            raise RuntimeError(error.decode())
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        proc.stdout.close()
        proc.stderr.close()
    gaps = [times[b]-times[a] for a, b in zip(checked, checked[1:])]
    return dict(hits=hits, decoded_frames=n, expected_frames=len(times),
                sampled_frames=len(checked), first_frame=checked[0] if checked else None,
                last_frame=checked[-1] if checked else None, max_sample_gap_s=max(gaps, default=0),
                complete=n == len(times) and set(checked) == selected and max(gaps, default=0) <= .2+1e-6,
                measurement_size=[width, height],
                method='All encoded frames decoded; real PTS sampling <=0.2s; four-edge flat fill / multicolour straight boundary',
                limits='Geometric detector, not semantic scene understanding; bands under 2 measurement pixels or heavily occluded may be missed.')


def edge_intervals(hits):
    """Group adjacent sampled hits by edge and shot; retain exact hits separately."""
    groups = []
    for key in sorted({(h['edge'], h.get('shot') or '') for h in hits}):
        current = None
        for h in (h for h in hits if (h['edge'], h.get('shot') or '') == key):
            if current is None or h['time_s']-current['last_hit_s'] > .20001:
                current = dict(edge=key[0], shot=key[1], first_hit_s=h['time_s'], last_hit_s=h['time_s'],
                               hits=0, min_width_px=h['width_px'], max_width_px=h['width_px'])
                groups.append(current)
            current['last_hit_s'] = h['time_s']
            current['hits'] += 1
            current['min_width_px'] = min(current['min_width_px'], h['width_px'])
            current['max_width_px'] = max(current['max_width_px'], h['width_px'])
    return sorted(groups, key=lambda g: g['first_hit_s'])


SALUTE = re.compile(r'salut[\w-]*|경례', re.I)


def canonical_actions(c):
    """Match the shot itself and only its linked/timed script, never all shots."""
    rows = []
    script_lines = c.script.splitlines()
    for s in c.shots:
        ids = set(s.get('sentence_ids', [])) | set(s.get('subtitle_source_ids', [])) | {s['id']}
        texts = [str(s)] + ([c.script] if len(c.shots)==1 else [])
        for line in script_lines:
            linked=any(re.search(r'(?<![\w])'+re.escape(i)+r'(?![\w])', line) for i in ids)
            clock=re.search(r'\[(\d+):(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+):(\d+(?:\.\d+)?)\]',line)
            timed=clock and int(clock[1])*60+float(clock[2]) < s['end_s'] and int(clock[3])*60+float(clock[4]) > s['start_s']
            if linked or timed:texts.append(line)
        for n in c.narration + c.subtitles:
            linked = n.get('id') in ids or s['id'] in n.get('shot_ids', [])
            timed = 'start_s' in n and 'end_s' in n and n['start_s'] < s['end_s'] and n['end_s'] > s['start_s']
            if linked or timed:
                texts.append(str(n))
        if any(SALUTE.search(t) for t in texts):
            rows.append(s)
    return rows


def hand_samples(s, fps):
    """Start plus declared peak; otherwise midpoint candidate and phase/end frames.

    A midpoint is not proof of a peak. The CTO must confirm the actual peak, or
    supply peak_frame on the shot and regenerate the bound evidence.
    """
    first = math.ceil(s['start_s']*fps - 1e-6)
    last = math.ceil(s['end_s']*fps - 1e-6)-1
    peak = s.get('action_peak_frame', s.get('peak_frame'))
    frames = {first: 'start'}
    if peak is not None:
        if not first <= int(peak) <= last:
            raise ValueError('Action peak outside shot '+s['id'])
        frames[int(peak)] = 'declared peak'
    else:
        frames[(first+last)//2] = 'peak candidate (CTO must confirm)'
        for phase in s.get('action_phases', []):
            n = phase.get('frame')
            if isinstance(n, int) and first < n <= last:
                frames.setdefault(n, 'action phase / peak candidate')
        frames.setdefault(last, 'end / peak coverage')
    return [dict(frame=n, time=n/fps, phase=phase) for n, phase in sorted(frames.items())]


def left_salute_calls(s):
    """Only explicit anatomical hand fields; a numeric rig index is not universal."""
    hits = []
    def walk(obj, path='', salute=False):
        if isinstance(obj, dict):
            salute = salute or any(SALUTE.search(str(obj.get(k, ''))) for k in ('rig', 'action', 'name', 'scene_mode', 'scene', 'mode'))
            for key, val in obj.items():
                p = path+'.'+key
                if (salute or SALUTE.search(key)) and re.search(r'(?:^|_)(?:arm|hand)$|^salute_side$', key, re.I) and re.fullmatch(r'left|l|왼팔|왼손|좌', str(val), re.I):
                    hits.append(dict(shot=s['id'], path=p, value=val))
                walk(val, p, salute or bool(SALUTE.search(key)))
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                walk(val, f'{path}[{i}]', salute)
    walk(s)
    return hits


def toon_salute_calls(source):
    """N18's explicit ToonRig call: front-facing hands[1] is anatomical left.

    Caller binds the named ToonRig source too. Do not generalise index semantics
    to other engines. Visual signoff still checks transforms/mirroring.
    """
    hits = []
    for branch in re.finditer(r"if\s*\(\s*mode\s*===?\s*['\"]salute['\"]\s*\)\s*\{([^{}]*)\}", source):
        for m in re.finditer(r'\b(\w+)\.hands\s*\[\s*1\s*\]\s*=\s*\[([^;]+)\];', branch[1]):
            # A left hand being released or resting is not a left-hand salute.
            # Recognise literal/linear raised-hand targets in the house rig;
            # more complex expressions remain for visual sign-off.
            y=m[2].split(',',1)[-1]
            if sum(float(v) for v in re.findall(r'-(\d+(?:\.\d+)?)',y)) < 350:
                continue
            offset = branch.start(1)+m.start()
            hits.append(dict(line=source.count('\n', 0, offset)+1, call=m[0], anatomical_hand='left'))
    return hits
