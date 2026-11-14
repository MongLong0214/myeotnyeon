"""H15/H16 measurements on existing media; no render, models or network."""
from pathlib import Path
import json
import re
import unicodedata

import cv2
import numpy as np
from PIL import Image


# Whole words only: never suppress a numeral because an ordinary word occurs
# elsewhere in the caption. In particular 구조 is 구 + 조 to a naive regex.
WORD_ALLOWLIST = frozenset({'일단', '이상', '삼촌', '사실', '오늘', '구조', '한번에',
                            '일반', '일부', '한동안', '세상', '세대', '이해', '사고',
                            '이번', '사건', '사회', '이유', '이곳', '이대로', '일대',
                            '이달', '이쪽', '사원'})
PARTICLES = r'(?:으로부터|으로|에서|에게|까지|부터|처럼|보다|동안|마다|조차|밖에|뿐|이라|이고|입니다|이었다|이다|에|의|은|는|이|가|을|를|와|과|도|만|씩|로)*'
COUNTERS = ('퍼센트', '킬로미터', '센티미터', '밀리미터', '킬로그램', '제곱미터',
            '사단', '여단', '대대', '소대', '중대', '개월', '시간', '주일', '주년',
            '달러', '유로', '미터', '그램', '배럴', '차례', '가지', '번째',
            '명', '개', '번', '분', '초', '년', '월', '일', '원', '억', '조',
            '살', '세', '시', '주', '달', '배', '대', '건', '곳', '차', '층',
            '장', '권', '병', '잔', '대', '마리', '톤', '팀', '쪽', '회', '단')
SINO = r'[일이삼사오육칠팔구십백천만]+?'
NATIVE = (r'(?:스물|서른|마흔|쉰|예순|일흔|여든|아흔)(?:한|두|세|네|다섯|여섯|일곱|여덟|아홉)?'
          r'|열(?:한|두|세|네|다섯|여섯|일곱|여덟|아홉)?|한|하나|두|둘|세|셋|네|넷|다섯|여섯|일곱|여덟|아홉|스무')
NUMERAL = re.compile(r'(?<![가-힣A-Za-z0-9])(?:제\s*)?(?P<number>' + SINO + '|' + NATIVE +
                     r')\s*(?P<unit>' + '|'.join(sorted(set(COUNTERS), key=len, reverse=True)) +
                     r')(?=' + PARTICLES + r'(?:$|[^가-힣]))')


def word_numerals(text):
    text = unicodedata.normalize('NFC', text)
    hits = []
    for match in NUMERAL.finditer(text):
        # Include the complete following eojeol for allowlist matching.
        tail = re.match(r'[가-힣]*', text[match.end():])[0]
        word = text[match.start():match.end()] + tail
        if any(re.fullmatch(re.escape(allowed) + PARTICLES, word) for allowed in WORD_ALLOWLIST):
            continue
        hits.append(dict(text=match[0], numeral=match['number'], unit=match['unit'],
                         offset=match.start(), context=text))
    return hits


def script_subtitles(text):
    """Only explicitly labelled subtitle fields, never the spoken narration."""
    rows = []
    headers = None
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r'^\s*(?:[-*]\s*)?(?:\*\*)?(?:자막|subtitle|caption)(?:\*\*)?\s*[:：]\s*(.+)', line, re.I)
        if m:
            rows.append(dict(text=m[1], line=n))
        elif line.strip().startswith('|'):
            cells = [s.strip() for s in line.strip().strip('|').split('|')]
            if any(re.fullmatch(r'자막|subtitles?|captions?', s, re.I) for s in cells):
                headers = [i for i, s in enumerate(cells) if re.fullmatch(r'자막|subtitles?|captions?', s, re.I)]
            elif headers:
                rows.extend(dict(text=cells[i], line=n) for i in headers if i < len(cells) and not re.fullmatch(r'[-: ]+', cells[i]))
        elif line.strip():
            headers = None
    return rows


def subtitle_file(path):
    """Read SRT, a subtitle JSON/timeline, or labelled script fields."""
    path = Path(path)
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.srt':
        rows = []
        for block in re.split(r'\n\s*\n', text.strip()):
            lines = block.splitlines()
            index = next((i for i, line in enumerate(lines) if '-->' in line), None)
            if index is not None:
                def timestamp(value):
                    h, m, s = map(float, value.strip().split()[0].replace(',', '.').split(':'))
                    return h*3600 + m*60 + s
                a, b = lines[index].split('-->')
                rows.append(dict(text=' '.join(lines[index + 1:]), cue=lines[index],
                                 start_s=timestamp(a), end_s=timestamp(b)))
        return rows
    if path.suffix.lower() == '.json':
        obj = json.loads(text)
        if isinstance(obj, list):
            return [dict(r) for r in obj if isinstance(r, dict) and 'text' in r]
        return [dict(r) for key in ('subtitles', 'captions', 'subtitle_cues') for r in obj.get(key, [])]
    return script_subtitles(text)


def numeral_evidence(c):
    sources = [dict(source='timeline', **s) for s in c.subtitles]
    groups = [c.subtitles]
    sources += [dict(source='script subtitle', **s) for s in script_subtitles(c.script)]
    for path in c.config.get('subtitle_files', []):
        c.bind(path)
        rows = subtitle_file(path)
        groups.append(rows)
        sources += [dict(source=str(path), **s) for s in rows]
    primary = sum(bool(s.get('text', '').strip()) for s in sources)
    for row in c.media.get('ocr', []):
        # OCR boxes use normalized top-left coordinates. A box whose geometry
        # is unavailable remains eligible rather than silently losing evidence.
        boxes = [b for b in row['boxes'] if b.get('y', 1) + b.get('h', 0) >= .70]
        boxes.sort(key=lambda b: (round(b.get('y', 0), 1), b.get('x', 0)))
        if boxes:
            sources.append(dict(source='OCR subtitle band', frame=row['frame'],
                                text=' '.join(b['text'] for b in boxes)))
    hits = []
    for source in sources:
        hits.extend(dict(source=source['source'], frame=source.get('frame'),
                         cue=source.get('cue'), start_s=source.get('start_s'),
                         line=source.get('line'), **hit) for hit in word_numerals(source.get('text', '')))
    # Consecutive subtitle cues can split numeral / counter at the cut.
    def cue_time(row, edge):
        for key, scale in [(edge+'_s', 1), (edge+'Ms', .001), (edge+'_frame', 1/c.fps),
                           ('from_' if edge == 'start' else 'to', 1/c.fps)]:
            if key in row:
                return float(row[key])*scale
        return None
    for group in groups:
        for left, right in zip(group, group[1:]):
            end, start = cue_time(left, 'end'), cue_time(right, 'start')
            if end is None or start is None or abs(start-end) > .25:
                continue
            a, b = left.get('text', ''), right.get('text', '')
            for hit in word_numerals(a + ' ' + b):
                if hit['offset'] < len(a) and hit['offset'] + len(hit['text']) > len(a):
                    hits.append(dict(source='adjacent subtitle cues', start_s=left.get('start_s'), **hit))
    # Keep repeated OCR hits compact while retaining every observed frame.
    unique = {}
    for hit in hits:
        key = (hit['source'], hit['text'], hit['context'], hit.get('start_s'), hit.get('line'))
        if key not in unique:
            unique[key] = dict(hit, frames=[])
        if hit.get('frame') is not None:
            unique[key]['frames'].append(hit['frame'])
    return dict(hits=list(unique.values()), primary_subtitle_rows=primary,
                ocr_engine=c.media.get('ocr_engine'), ocr_complete=c.media.get('ocr_complete', False),
                text_available=bool(primary or c.media.get('ocr_korean') and c.media.get('ocr_complete')),
                allowlist=sorted(WORD_ALLOWLIST), units=sorted(set(COUNTERS)),
                method='Explicit subtitle fields/SRT plus OCR in bottom 30%; narration excluded')


HASH_LIMIT = 14
COLOR_LIMIT = .015


def signature(image):
    """64-bit DCT pHash and 3×3 HSV histograms, excluding bottom 30%."""
    rgb = np.asarray(image.convert('RGB'))
    rgb = rgb[:round(len(rgb) * .70)]
    small = cv2.resize(rgb, (96, 64), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    dct = cv2.dct(cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32))[:8, :8].ravel()
    bits = dct > np.median(dct[1:]); bits[0] = False
    value = sum(int(bit) << i for i, bit in enumerate(bits))
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    cells = []
    def soft_hist(values, bins, high, weights=None, circular=False):
        # Interpolate bins: a +/-1 codec error near a bin edge must not move
        # an entire flat background into a different histogram bucket.
        pos = values.ravel().astype(float) * (bins/high if circular else (bins-1)/(high-1))
        low = np.floor(pos).astype(int)
        fraction = pos-low
        weights = np.ones_like(pos) if weights is None else weights.ravel()
        hist = np.bincount(low % bins, weights=weights*(1-fraction), minlength=bins)
        hist += np.bincount((low+1) % bins if circular else np.minimum(low+1, bins-1),
                            weights=weights*fraction, minlength=bins)
        return hist/len(pos)
    for row in np.array_split(hsv, 3, axis=0):
        for cell in np.array_split(row, 3, axis=1):
            # Marginal channel histograms retain layout without making tiny
            # antialiasing/lighting changes separate colors in a joint cube.
            cells.extend(soft_hist(cell[:, :, channel], bins, high,
                                  cell[:, :, 1].astype(float)/255 if channel == 0 else None,
                                  circular=channel == 0)
                         for channel, bins, high in [(0, 12, 180), (1, 4, 256), (2, 4, 256)])
    return dict(phash=f'{value:016x}', color=np.concatenate(cells).tolist())


def distance(a, b):
    return ((int(a['phash'], 16) ^ int(b['phash'], 16)).bit_count(),
            float(np.abs(np.array(a['color']) - b['color']).sum() / 54))


def cluster_samples(samples):
    """Prototype clustering avoids transitive chains of increasingly different sets."""
    prototypes = []
    for sample in samples:
        matches = []
        for i, proto in enumerate(prototypes):
            h, color = distance(sample['signature'], proto)
            if h <= HASH_LIMIT and color <= COLOR_LIMIT:
                matches.append((h / HASH_LIMIT + color / COLOR_LIMIT, i))
        if matches:
            sample['cluster'] = min(matches)[1]
        else:
            sample['cluster'] = len(prototypes)
            prototypes.append(sample['signature'])
    segments = []
    for i, sample in enumerate(samples):
        if segments and segments[-1]['cluster'] == sample['cluster']:
            segments[-1]['end_s'] = sample['end_s']
            segments[-1]['sample_indices'].append(i)
        else:
            segments.append(dict(cluster=sample['cluster'], start_s=sample['start_s'],
                                 end_s=sample['end_s'], sample_indices=[i]))
    clusters = []
    for i in range(len(prototypes)):
        runs = [s for s in segments if s['cluster'] == i]
        recurrences = [dict(previous_end_s=a['end_s'], return_s=b['start_s'],
                            break_s=round(b['start_s'] - a['end_s'], 6))
                       for a, b in zip(runs, runs[1:]) if b['start_s'] - a['end_s'] <= 60 + 1e-8]
        clusters.append(dict(cluster=i, segments=runs, segment_count=len(runs),
                             recurrences_within_60s=recurrences,
                             fail=bool(recurrences) or len(runs) > 3))
    return clusters


def presenter_regions(images):
    """Conservative cartoon candidate: one tall silhouette, separate static prop.

    No semantic PASS/FAIL is claimed. The reviewer sees all three frames and
    region/motion measurements, including missed or ambiguous silhouettes.
    """
    from figure_shapes import silhouettes
    boxes = [b for b in silhouettes(images[1]) if b['h'] >= .28 and b['w'] * b['h'] >= .025 and b['y'] < .65]
    # Inner face contours can produce nested heads for the same person. They
    # must not turn a single presenter into two apparent figures.
    unique = []
    for box in sorted(boxes, key=lambda b: -b['w']*b['h']):
        def contained(other):
            overlap = max(0, min(box['x']+box['w'], other['x']+other['w']) - max(box['x'], other['x']))
            overlap *= max(0, min(box['y']+box['h'], other['y']+other['h']) - max(box['y'], other['y']))
            return overlap / (box['w']*box['h']) > .8
        if not any(contained(b) for b in unique):
            unique.append(box)
    boxes = unique
    if len(boxes) != 1:
        return None
    arrays = [np.asarray(Image.open(p).convert('RGB').resize((320, 180)))[:126] for p in images]
    first, mid, last = arrays
    # Compensate a dominant camera translation/zoom before measuring the
    # figure and prop. A moving camera alone does not make a presenter act.
    target_gray = cv2.cvtColor(mid, cv2.COLOR_RGB2GRAY)
    residuals = []
    transforms = []
    for source in (first, last):
        source_gray = cv2.cvtColor(source, cv2.COLOR_RGB2GRAY)
        corners = cv2.goodFeaturesToTrack(source_gray, maxCorners=200, qualityLevel=.01, minDistance=5)
        matrix = None
        if corners is not None and len(corners) >= 8:
            tracked, valid, _ = cv2.calcOpticalFlowPyrLK(source_gray, target_gray, corners, None)
            if tracked is not None and valid is not None and int(valid.sum()) >= 8:
                keep = valid.ravel() == 1
                matrix, inliers = cv2.estimateAffinePartial2D(corners[keep], tracked[keep],
                                                             method=cv2.RANSAC, ransacReprojThreshold=1.5)
                if matrix is not None and (inliers.sum() < 8 or inliers.mean() < .5):
                    matrix = None
        aligned = source
        valid_pixels = np.ones(source.shape[:2], bool)
        if matrix is not None:
            h, w = source.shape[:2]
            scale = float(np.hypot(matrix[0, 0], matrix[0, 1]))
            if .8 <= scale <= 1.25:
                aligned = cv2.warpAffine(source, matrix, (w, h))
                valid_pixels = cv2.warpAffine(np.ones((h, w), np.uint8), matrix, (w, h)) == 1
            else:
                matrix = None
        delta = np.abs(aligned.astype(float)-mid).mean(axis=2)
        delta[~valid_pixels] = 0
        residuals.append(delta)
        transforms.append(matrix.tolist() if matrix is not None else None)
    diff = np.maximum(*residuals)
    figure = boxes[0]; h, w = diff.shape
    x0, x1 = max(0, round(figure['x'] * w)), min(w, round((figure['x'] + figure['w']) * w))
    y0, y1 = max(0, round(figure['y'] * 180)), min(h, round((figure['y'] + figure['h']) * 180))
    if x1 <= x0 or y1 <= y0:
        return None
    figure_motion = float(diff[y0:y1, x0:x1].mean())
    gray = cv2.cvtColor(mid, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 100)
    edges[max(0, y0-5):min(h, y1+5), max(0, x0-5):min(w, x1+5)] = 0
    joined = cv2.dilate(edges, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(joined, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    props = []
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if .025 <= bw * bh / (w * h) <= .30 and bw >= w * .10 and bh >= h * .18 and (x + bw < x0 or x > x1):
            motion = float(diff[y:y+bh, x:x+bw].mean())
            if motion <= 3:
                props.append(dict(x=x/w, y=y/180, w=bw/w, h=bh/180, motion_mae=motion))
    whole_motion = float(diff.mean())
    if props and figure_motion <= 3 and whole_motion <= 4:
        return dict(figure=figure, figure_motion_mae=figure_motion, props=props,
                    shot_motion_mae=whole_motion, frames=[str(p) for p in images],
                    camera_transforms=transforms,
                    status='NEEDS_REVIEW')
    return None


def composition_evidence(c):
    if not c.duration or not c.frames:
        raise ValueError('No measured film duration/frames')
    if c.shots:
        spans = [dict(shot=s['id'], start_s=s['start_s'], end_s=s['end_s']) for s in c.shots]
        valid = (abs(spans[0]['start_s']) <= 1/c.fps and
                 abs(spans[-1]['end_s'] - c.duration) <= 1/c.fps and
                 all(0 <= s['start_s'] < s['end_s'] <= c.duration + 1/c.fps for s in spans) and
                 all(abs(a['end_s'] - b['start_s']) <= 1/c.fps for a, b in zip(spans, spans[1:])))
        if not valid:
            raise ValueError('Shot timeline does not cover film; cannot measure recurrence')
        method = 'One midpoint per shot'
    else:
        spans = [dict(shot=None, start_s=float(t), end_s=min(t+1., c.duration))
                 for t in range(int(np.ceil(c.duration)))]
        method = 'Every 1 s (midpoint of each one-second interval)'
    samples = []
    presenters = []
    for span in spans:
        t = (span['start_s'] + span['end_s']) / 2
        path = c.frame(t)
        with Image.open(path) as im:
            sig = signature(im)
        samples.append(dict(span, time_s=t, frame=round(t*c.fps), image=str(path), signature=sig))
        # Compare quarter/middle/three-quarter positions within each real shot.
        # Without shot metadata use one-second windows; never cross a cut.
        times = [span['start_s'] + (span['end_s'] - span['start_s']) * q for q in (.2, .5, .8)]
        frames = [c.frame(t) for t in times]
        candidate = presenter_regions(frames)
        if candidate:
            presenters.append(dict(span, **candidate, times_s=times))
    clusters = cluster_samples(samples)
    return dict(samples=samples, clusters=clusters, presenter_candidates=presenters,
                repetition_fail=any(c['fail'] for c in clusters), complete=True,
                sample_method=method, subtitle_mask='Bottom 30% excluded before all signatures/motion',
                thresholds=dict(phash_hamming_max=HASH_LIMIT, color_layout_distance_max=COLOR_LIMIT,
                                recurrence_s=60, separate_segments_max=3),
                signature_method='32x32 DCT / 64-bit pHash + 3x3 HSV marginal color histograms',
                limitations='Presenter heuristic is a candidate detector, not a semantic classifier; CTO must inspect overview and frames')
