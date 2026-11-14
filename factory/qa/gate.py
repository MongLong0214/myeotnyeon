"""Owner-correction QA gate: one runner, every render, before anyone sees it.

  .venv/bin/python factory/qa/gate.py VIDEO --srt subs.srt [--out DIR] [--shots shots.json] [--script script.(json|md)]
      [--text-measure text_measure.jsonl] [--face-measure face_measure.jsonl] [--voice voice.wav]
      [--facts facts.md] [--titles meta.txt] [--thumbnail T.jpg ...] [--review-log review_log.json]
      [--format longform|shorts] [--no-sheets]

Writes DIR/gate.json, DIR/gate.md, DIR/evidence/<check>_fNNNNN.png (frame-numbered), DIR/sheets/s_NNNN.jpg
(every frame, 4x3 tiles, frame number burned in), DIR/subtitle_breaks.md (every break, H23c) and
DIR/review_log.template.json. Item ids are the REVIEW_CHECKLIST.md ids.

Status: PASS / FAIL (automatic) / REVIEW (candidates a human must clear in the review log; uncleared = FAIL).
Overall PASS needs every automatic item PASS, every REVIEW candidate cleared, and every contact sheet signed.
Frame-level checks read ALL decoded frames (no sampling); face detection fallback runs every 3rd frame.
Limits: no real-time playback; OCR-free (render-time boxes when given, glyph heuristics otherwise).
"""
import argparse
import hashlib
import os
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from factory.lib.frame_qa import measure_audio  # noqa: E402
from factory.lib.captions import silences_from_audio  # noqa: E402
from factory.qa import subtitle_ko  # noqa: E402

FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
YUNET = Path(__file__).with_name('models') / 'face_detection_yunet_2023mar.onnx'
VISION_PY = Path(os.environ.get('GATE_VISION_PY', ROOT / 'research/new_refs/.venv/bin/python'))
AW, AH = 640, 360          # analysis decode size (landscape); set_analysis_size() flips both for vertical video
TW, TH = 426, 240          # contact-sheet tile


def set_analysis_size(info):
    """Keep the source aspect ratio: 640x360 for landscape, 360x640 for vertical (1080x1920 Shorts). One uniform
    scale k = AW / width then maps source pixels to analysis pixels on both axes."""
    global AW, AH, TW, TH
    if info['h'] > info['w']:
        AW, AH, TW, TH = 360, 640, 240, 426
    else:
        AW, AH, TW, TH = 640, 360, 426, 240
    return AW, AH


def px1080(v_src, info):
    """source-pixel length -> pixels on a frame whose short side is 1080 (the '@1080' unit of every size limit)"""
    return v_src * 1080 / min(info['w'], info['h'])
MOTION_TOP = 0.76          # motion is measured above the subtitle band

# ---------------- word lists from the owner catalogue ----------------
BANNED = {  # (regex, item, severity)
    'utc': (r'UTC|세계\s?표준시|협정\s?세계시|그리니치|GMT', 'H21c', 'FAIL'),
    'jargon': (r'핫\s?월렛|콜드\s?월렛|멀티\s?시그|프라이빗\s?키|개인\s?키|스마트\s?컨트랙트|브릿지|믹서|토네이도\s?캐시|'
               r'온체인|오프체인|디파이|DeFi|시드\s?구문|해시값|TRM|OFAC|KYC|AML', 'H19a', 'FAIL'),
    'disclaimer': (r'재구성|시간\s?압축|재연\s?장면|시각\s?비유|실제\s?영상\s?아님|연출된\s?장면', 'H9', 'REVIEW'),
    'hangul_date': (r'이천\s?[가-힣]*\s?년|[일이삼사오육칠팔구십]+\s?월\s?[일이삼사오육칠팔구십]+\s?일', 'E1', 'FAIL'),
    'iso_date': (r'\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b|\b20\d{6}\b', 'E1', 'FAIL'),
    'hangul_number': (r'(?<![가-힣])(?:[이삼사오육칠팔구]?십[일이삼사오육칠팔구]?|[이삼사오육칠팔구]?백|[이삼사오육칠팔구]?천)\s?'
                      r'(?:사단|년|명|분|초|개|억|만|원|대|번|살|층|시간)|'
                      r'(?<![가-힣])(?:두|세|네|다섯|여섯|일곱|여덟|아홉|열|스무|서른|마흔|석|넉)\s(?:명|개|번|살|시간|대|곳|권|차례|달|사람)',
                      'H16', 'FAIL'),
    'template_cta': (r'구독과?\s?좋아요|알림\s?설정|형량\s?퀴즈\s?#|정답은\s?\?', 'H4', 'REVIEW'),
}
ACRONYM_OK = {'AI', 'SNS', 'CCTV', 'PC', 'IT', 'USB', 'ID', 'FBI', 'TV', 'A', 'B', 'C', 'D', 'KST', 'PDF', 'URL', 'CEO', 'OK', 'ATM'}
OVERSTATE = [r'\d+\s?(초|분|시간|일)\s?만에', r'털렸다', r'범인\s?확정', r'확정', r'역대\s?최대', r'사상\s?최대', r'최초', r'전부',
             r'모두', r'완벽', r'결국', r'처벌\s?(못|불가)', r'처벌할\s?수\s?없', r'못\s?잡', r'절대', r'100\s?%', r'충격', r'경악',
             r'소름', r'진짜\s?이유', r'밝혀졌다', r'드러났다']
QUALIFIER = r'약|추정|대부분|가량|이상|보도|주장|의혹|혐의|분석'

MANUAL_ITEMS = {  # catalogue items that need a human with evidence (sheet numbers / frames)
    'H21a': 'hands: mittens, finger count, reversed thumb, detached wrist, hooks, size (every hand shot)',
    'H17b': 'arms not stick-straight; no arms crossed into an X; elbows bend',
    'H18': 'joints: bone length, bend direction, sitting legs, no idle limb noise',
    'H19b': 'props (laptop etc.) never overlap or pass through a body, face or hand; laptop = silver MacBook-type',
    'P-float': 'no floating or ungripped props (paper, bat, phone); held props are gripped',
    'H7': 'every face has eyes, nose, mouth and a readable expression; no blank-eye frames',
    'C4/H17d': 'acting energy: exaggerated expression/pose, comedy standard q014; no frozen smiles in grim beats',
    'C2/H13': 'boredom: would a viewer swipe away here? (first 60 s at 1 s, whole film)',
    'H21b/H15': 'back half is not a documentary/explainer: no presenter + board pattern, no repeated similar screens',
    'P-parents': 'parents/family scenes are dramatised, not static talking heads',
    'P-small': 'no small characters lost in empty frames; subject fills the frame',
    'H4/H20/H22a': 'AI look: no rounded badges/pills/ring timers, no icon calendars, no floating info boxes',
    'H22b': 'key information scenes have in-world displays with depth and light',
    'B4': 'every key prop/person reads as what the script says (no bag-for-rucksack, no barrister wig in a Korean court)',
    'D1/D2': 'cut transitions and cut-narration match for every shot',
    'E2': 'violence/death beats shown without gore close-ups, victim identification or mockery',
    'E3': 'facts gate: every claim traced to the facts table, 2+ sources',
    'T-thumb': 'thumbnail: not a reused film frame, strong face/emotion, readable at phone size, wording matches facts',
    'H23c': 'subtitle_breaks.md read cue by cue',
}
SHEET_CHECKS = ['hands', 'arms', 'props_overlap', 'floating_props', 'faces', 'acting', 'boredom', 'ai_look', 'small_in_empty',
                'subtitle_over_face_or_text', 'continuity']


def run(args, **kw):
    return subprocess.run(list(map(str, args)), capture_output=True, check=True, **kw)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def probe(video):
    d = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', video]).stdout)
    v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    return dict(fps=float(Fraction(v['avg_frame_rate'])), w=int(v['width']), h=int(v['height']),
                audio=any(s['codec_type'] == 'audio' for s in d['streams']), duration=float(d['format']['duration']))


def runs(mask, min_len):
    """Half-open [a,b) spans where mask is True for at least min_len frames."""
    out, start = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if i - start >= min_len:
                out.append([start, i])
            start = None
    return out


def glyph_mask(rgb):
    """Outlined caption-style text: near-white pixels with a near-black pixel within 2 px."""
    mn = rgb.min(-1)
    mx = rgb.max(-1)
    white = mn > 225
    dark = mx < 60
    near = np.zeros_like(dark)
    for dy in (-2, 0, 2):
        for dx in (-2, 0, 2):
            near |= np.roll(np.roll(dark, dy, 0), dx, 1)
    return white & near


def skin_mask(rgb):
    r, g, b = [rgb[..., i].astype(np.int16) for i in range(3)]
    return (r > 150) & (g > 90) & (b > 60) & (r > g + 12) & (g > b) & (r - b > 35) & (r - b < 140)


class Decoder:
    """Single pass over every frame: motion, luma, saturation, glyph boxes, signatures, contact sheets, faces."""

    def __init__(self, video, info, out, sheets=True, faces=True):
        self.video, self.info, self.out = video, info, out
        self.sheets, self.faces = sheets, faces

    def run(self, cues):
        fps = self.info['fps']
        size = AW * AH * 3
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(self.video), '-map', '0:v:0', '-vf',
                              f'scale={AW}:{AH}:flags=area', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             stdout=subprocess.PIPE)
        det = None
        if self.faces and YUNET.exists():
            import cv2
            det = cv2.FaceDetectorYN.create(str(YUNET), '', (AW, AH), 0.5, 0.3, 5000)
        cue_at = np.full(int(self.info['duration'] * fps) + 10, -1)
        for k, c in enumerate(cues):
            cue_at[int(c['start'] * fps):int(c['end'] * fps)] = k
        luma, sat, moved, diff, lag2, sig, cuts_d, hist = [], [], [], [], [], [], [], []
        spike, pf1, pf2 = [], None, None
        glyph_box, glyph_edge, faces, skin_sub = [], [], {}, {}
        prev = prev2 = None
        sheet, sheet_files, n = None, [], 0
        font = ImageFont.truetype(FONT, 18)
        top = int(AH * MOTION_TOP)
        sd = self.out / 'sheets'
        if self.sheets:
            sd.mkdir(parents=True, exist_ok=True)
        while True:
            raw = p.stdout.read(size)
            if not raw:
                break
            f = np.frombuffer(raw, np.uint8).reshape(AH, AW, 3)
            small = f[::2, ::2].astype(np.int16)
            gray = ((small.astype(np.int32) @ np.array([54, 183, 19], np.int32)) >> 8).astype(np.int16)
            luma.append(float(gray.mean()) / 255)
            mx, mnn = small.max(-1), small.min(-1)
            sat.append(float(np.where(mx > 15, (mx - mnn) / np.maximum(mx, 1), 0).mean()))
            sig.append(np.asarray(Image.fromarray(f).resize((32, 18), Image.BILINEAR), np.int16))
            hh = np.histogramdd((small // 32).reshape(-1, 3), bins=(8, 8, 8), range=((0, 8),) * 3)[0].ravel()
            hist.append((hh / hh.sum()).astype(np.float32))
            if prev is not None:
                d = np.abs(gray - prev)
                moved.append(float((d[:top // 2] > 10).mean()))
                diff.append(float(d.mean()))
                lag2.append(float((np.abs(gray - prev2)[:top // 2] > 10).mean()) if prev2 is not None else 1.0)
            gfull = ((f.astype(np.int32) @ np.array([54, 183, 19], np.int32)) >> 8).astype(np.int16)
            if pf2 is not None:
                # spike pixels of the previous frame: it differs from both neighbours, which agree with each other
                d01, d12, d02 = np.abs(pf1 - pf2), np.abs(pf1 - gfull), np.abs(pf2 - gfull)
                spike.append(float(((d01 > 24) & (d12 > 24) & (d02 < 8))[:top].mean()))
            elif pf1 is not None:
                spike.append(0.0)
            pf2, pf1 = pf1, gfull
            prev2, prev = prev, gray
            gm = glyph_mask(f)
            ys, xs = np.nonzero(gm)
            if len(xs) > 40:
                glyph_box.append([int(np.percentile(xs, 1)), int(np.percentile(ys, 1)), int(np.percentile(xs, 99)) + 1,
                                  int(np.percentile(ys, 99)) + 1, int(len(xs))])
            else:
                glyph_box.append(None)
            border = np.concatenate([gm[:3].ravel(), gm[-3:].ravel(), gm[:, :3].ravel(), gm[:, -3:].ravel()])
            glyph_edge.append(int(border.sum()))
            k = cue_at[n] if n < len(cue_at) else -1
            if k >= 0 and glyph_box[-1] is not None:
                x0, y0, x1, y1, _ = glyph_box[-1]
                if y0 > AH * 0.45:
                    reg = f[y0:y1, x0:x1]
                    sm = skin_mask(reg) & ~gm[y0:y1, x0:x1]
                    skin_sub[n] = float(sm.mean()) if sm.size else 0.0
            if det is not None and n % 3 == 0:
                _, fc = det.detect(np.ascontiguousarray(f[..., ::-1]))
                if fc is not None:
                    faces[n] = [[float(v) for v in r[:4]] + [float(r[-1])] for r in fc]
            if self.sheets:
                if n % 12 == 0:
                    sheet = Image.new('RGB', (TW * 4, TH * 3), 'black')
                    draw = ImageDraw.Draw(sheet)
                x, y = (n % 4) * TW, ((n % 12) // 4) * TH
                sheet.paste(Image.fromarray(f).resize((TW, TH)), (x, y))
                draw.rectangle((x, y, x + 150, y + 24), fill='black')
                draw.text((x + 4, y + 2), f'f{n} {n / fps:.2f}s', fill='yellow', font=font)
                if n % 12 == 11:
                    name = f's_{n // 12 + 1:04d}.jpg'
                    sheet.save(sd / name, quality=82)
                    sheet_files.append(dict(sheet=name, frames=[n - 11, n]))
            n += 1
        p.wait()
        if self.sheets and n % 12:
            name = f's_{n // 12 + 1:04d}.jpg'
            sheet.save(sd / name, quality=82)
            sheet_files.append(dict(sheet=name, frames=[n - n % 12, n - 1]))
        self.n = n
        self.luma, self.sat = np.array(luma), np.array(sat)
        self.moved, self.diff, self.lag2 = np.array(moved), np.array(diff), np.array(lag2)
        self.spike = np.array(spike + [0.0] * (n - len(spike)))
        self.sig, self.hist = np.stack(sig), np.stack(hist)
        self.glyph_box, self.glyph_edge, self.faces, self.skin_sub = glyph_box, glyph_edge, faces, skin_sub
        self.sheet_files = sheet_files
        return self


# ---------------- checks ----------------
def min_cue_for(text, a):
    """Shortest time a subtitle cue may stay on screen. fixed: a.min_cue for every cue. per_word (Beast Clash variant
    only, opt-in with --cue-rule per_word): 0.25 s per word and never under 0.35 s (1 word 0.35, 2 words 0.5, 3 words 0.75)."""
    if getattr(a, 'cue_rule', 'fixed') == 'per_word':
        return max(0.35, 0.25 * len(str(text).split()))
    return a.min_cue


class Gate:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out)
        self.ev = self.out / 'evidence'
        self.ev.mkdir(parents=True, exist_ok=True)
        self.items = []
        self.evidence_req = []   # (frame, check, boxes)

    def item(self, iid, check, status, summary, findings=(), kind='auto'):
        self.items.append(dict(id=iid, check=check, status=status, kind=kind, summary=summary, findings=list(findings)))

    def want(self, frame, check, boxes=(), note=''):
        self.evidence_req.append((int(frame), check, list(boxes), note))
        return f'evidence/{check}_f{int(frame):05d}.png'

    # ----- subtitles -----
    def subtitles(self, cues):
        if self.a.lang != 'ko':
            return self.subtitles_intl(cues)
        lm = self.a.line_max or (14 if self.a.format == 'shorts' else 18)
        rows, engine = subtitle_ko.lint_cues(cues, line_max=lm)
        fps = self.info['fps']
        fails = [r for r in rows if r['severity'] == 'FAIL']
        revs = [r for r in rows if r['severity'] == 'REVIEW']
        for r in fails + revs:
            fr = int(((r['start'] + r['end']) / 2) * fps)
            r['frame'] = fr
            r['evidence'] = self.want(fr, 'H23_subtitle_break', note=f"cue {r['cue']} {r.get('before','')} / {r.get('after','')}")
        self.item('H23a/H23b/H17a/H5', 'subtitle_linguistics', 'FAIL' if fails else ('REVIEW' if revs else 'PASS'),
                  f'{engine}: {len(fails)} FAIL, {len(revs)} REVIEW of {sum(1 for r in rows if "before" in r)} breaks',
                  fails + revs)
        md = ['# Subtitle breaks — every line and cue break (H23c: read every row)', f'engine: {engine}', '',
              '| cue | kind | time | before | after | verdict | why |', '|---|---|---|---|---|---|---|']
        for r in rows:
            if 'before' in r:
                md.append(f"| {r['cue']} | {r['kind']} | {r['start']:.2f} | {r['before']} | {r['after']} | {r['severity']} {r['code']} | {r['why']} |")
        (self.out / 'subtitle_breaks.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    def subtitles_intl(self, cues):
        # en/ja: the Korean analyser (kiwipiepy) does not apply. Check line length and line starts instead
        # (en <= 32 chars per line at word boundaries; ja <= 14 chars, no line starting with small kana / punctuation).
        lm = self.a.line_max or {'en': 32, 'ja': 14}.get(self.a.lang, 32)
        nostart = set('ゃゅょぁぃぅぇぉっャュョァィゥェォッー、。，．,.!?！？」』）)・…〜')
        fps = self.info['fps']
        bad = []
        for c in cues:
            for line in c['text'].split('\n'):
                why = (f'{len(line)} chars > {lm}' if len(line) > lm else
                       'line starts with small kana/punctuation' if self.a.lang == 'ja' and line[:1] in nostart else
                       'line starts with punctuation' if line[:1] in ',.!?;:' else None)
                if why:
                    fr = int(((c['start'] + c['end']) / 2) * fps)
                    bad.append(dict(cue=c['idx'], line=line, why=why, frame=fr,
                                    evidence=self.want(fr, 'H23_subtitle_break', note=f"cue {c['idx']} {line}")))
        self.item('H23a/H23b/H17a/H5', 'subtitle_linguistics', 'FAIL' if bad else 'PASS',
                  f'{self.a.lang}: Korean analyser skipped; {len(bad)} of {len(cues)} cues break the {self.a.lang} line rules '
                  f'(<= {lm} chars per line{", line starts" if self.a.lang == "ja" else ""})', bad)
        (self.out / 'subtitle_breaks.md').write_text('\n'.join([f'# Subtitle lines ({self.a.lang}, <= {lm} chars)', '', '| cue | line | chars |', '|---|---|---|']
            + [f"| {c['idx']} | {l} | {len(l)} |" for c in cues for l in c['text'].split('\n')]) + '\n', encoding='utf-8')

    def timing(self, cues):
        src = self.a.voice or self.a.video
        sil = silences_from_audio(src, noise=self.a.silence_db, min_dur=0.15) if (self.a.voice or self.info['audio']) else []
        onsets = [e for s, e in sil]
        offs = [s for s, e in sil]
        fps = self.info['fps']
        bad = []
        for k, c in enumerate(cues):
            dur = c['end'] - c['start']
            need = min_cue_for(c.get('text', ''), self.a)
            if dur < need - 1e-6:
                bad.append(dict(cue=c['idx'], code='min_duration', why=f'{dur:.2f}s < {need:.2f}s', start=c['start']))
            if k + 1 < len(cues) and cues[k + 1]['start'] < c['end'] - 0.01:
                bad.append(dict(cue=c['idx'], code='overlap', why=f"ends {c['end']:.2f} after next starts {cues[k + 1]['start']:.2f}",
                                start=c['start']))
            cps = len(re.sub(r'\s', '', c['text'])) / max(dur, 0.01)
            if cps > self.a.max_cps:
                bad.append(dict(cue=c['idx'], code='reading_speed', why=f'{cps:.1f} chars/s > {self.a.max_cps}', start=c['start']))
            near = [o for o in onsets if abs(o - c['start']) <= 0.6]
            if near:
                o = min(near, key=lambda o: abs(o - c['start']))
                if c['start'] < o - self.a.early or c['start'] > o + self.a.late:
                    bad.append(dict(cue=c['idx'], code='onset_offset', why=f"cue {c['start']:.2f}s vs voice onset {o:.2f}s ({c['start'] - o:+.2f}s)",
                                    start=c['start']))
            # a cue that stays on screen through a long silence after its speech ended
            gap = [(s, e) for s, e in sil if c['start'] < s and e < c['end'] and e - s > 1.2]
            if gap:
                bad.append(dict(cue=c['idx'], code='lingers_over_silence', why=f'{gap[0][1] - gap[0][0]:.2f}s silence inside cue',
                                start=c['start']))
        if self.a.voice:
            speech, t = [], 0.0
            for s, e in sil + [(self.info['duration'], self.info['duration'])]:
                if s - t > 0.5:
                    speech.append((t, s))
                t = e
            for s, e in speech:
                cov = sum(max(0, min(e, c['end']) - max(s, c['start'])) for c in cues)
                if cov < 0.5 * (e - s):
                    bad.append(dict(cue=None, code='speech_without_subtitle', why=f'{s:.2f}-{e:.2f}s speech, {cov:.2f}s covered', start=s))
        for b in bad:
            b['frame'] = int(b['start'] * fps)
            b['evidence'] = self.want(b['frame'] + 2, 'C1_subtitle_timing', note=b['why'])
        hard = [b for b in bad if b['code'] in ('overlap', 'min_duration', 'speech_without_subtitle')]
        self.item('D2/C1', 'subtitle_timing', 'FAIL' if hard else ('REVIEW' if bad else 'PASS'),
                  f"{len(onsets)} voice onsets (silencedetect {self.a.silence_db}, {'voice stem' if self.a.voice else 'final mix'}); "
                  f'{len(hard)} hard, {len(bad) - len(hard)} soft', bad)

    # ----- frame checks -----
    def frames(self, d):
        fps, n = self.info['fps'], d.n
        # cuts: big change between consecutive frames
        cut, self.content_val, cut_src = scene_cuts(self.a.video, n)
        if cut is None:
            cut = [i + 1 for i, (x, m) in enumerate(zip(d.diff, np.r_[d.moved])) if x > 22 and m > 0.25]
        if self.shots:
            cut_src = 'shots json'
            cut = sorted(set(int(s['a']) for s in self.shots if s['a'] > 0))
        self.cuts = cut
        # holds: almost no movement above the subtitle band. Ambient sway, drift and blinks stay under the limit
        # (owner: a screen where only blinks/drift move is static). 5-frame median removes single-frame blips.
        cut_set = set(cut)
        mm = np.array([np.median(d.moved[max(0, i - 2):i + 3]) for i in range(len(d.moved))])
        closed = np.array([m < self.a.still_frac and (i + 1) not in cut_set for i, m in enumerate(mm)])
        holds = runs(closed, int(self.a.hold * fps))
        f = []
        for a, b in holds:
            f.append(dict(frames=[a, b], seconds=[round(a / fps, 2), round(b / fps, 2)], dur=round((b - a) / fps, 2),
                          evidence=self.want((a + b) // 2, 'C2_static_hold', note=f'{(b - a) / fps:.1f}s hold')))
        self.item('C2/H6/H17c', 'static_holds', 'FAIL' if f else 'PASS',
                  f'{len(f)} spans > {self.a.hold}s with <{self.a.still_frac:.1%} moving pixels (all {n} frames)', f)
        # flashes / black / washed-out single frames
        L, S = d.luma, d.sat
        fl, flagged = [], set()
        for i in range(n):
            if L[i] < 0.03 and (i == 0 or L[i - 1] >= 0.03 or i - 1 in flagged):
                fl.append(dict(frame=i, kind='black', luma=round(float(L[i]), 3)))
                flagged.add(i)
        for i in range(1, n - 1):
            if i in flagged:
                continue
            dl, ds = L[i] - L[i - 1], S[i] / max(S[i - 1], 1e-3)
            if abs(dl) <= self.a.flash and ds > 0.7:
                continue
            for k in range(1, 4):   # excursion of k frames that returns to the level before it
                j = i + k
                if j >= n:
                    break
                back = abs(L[j] - L[i - 1]) < self.a.flash / 3 and 0.85 < S[j] / max(S[i - 1], 1e-3) < 1.18
                washed = dl > 0.05 and ds < 0.7 and (j in cut_set or back)
                if back or washed:
                    for q in range(i, j):
                        if q not in flagged:
                            fl.append(dict(frame=q, kind='washed_out' if ds < 0.7 else 'luma_flash', frames=k,
                                           jump=round(float(dl), 3), sat_ratio=round(float(ds), 2)))
                            flagged.add(q)
                    break
        # same-area brighten/darken pairs per second (WCAG-style flash count)
        jumps = np.abs(np.diff(L)) > 0.1
        rate = max((int(jumps[i:i + int(fps)].sum()) // 2 for i in range(max(1, n - int(fps)))), default=0)
        for x in fl:
            x['evidence'] = self.want(x['frame'], 'S1_flash_frame', note=x['kind'])
        if rate > 3:
            fl.append(dict(kind='flash_rate', per_second=rate))
        self.item('S1/F1', 'flash_black_frames', 'FAIL' if fl else 'PASS', f'{len(fl)} single-frame luma/black/desaturation anomalies; max {rate} flash pairs/s', fl)
        # single-frame pops: frame i differs from both neighbours but i-1 ~ i+1 (glitch or broken in-between)
        pops = []
        for i in range(1, n - 1):
            if i in cut_set or (i + 1) in cut_set or i in flagged:
                continue
            sp = d.spike
            if sp[i] > self.a.spike and i >= 2 and i + 2 < n and max(sp[i - 1], sp[i + 1], sp[i - 2], sp[i + 2]) < 0.4 * sp[i]:
                pops.append(dict(frame=i, spike_frac=round(float(d.spike[i]), 4),
                                 evidence=self.want(i, 'S2_single_frame', note=f'spike {d.spike[i]:.2%}')))
        self.item('S2/H7', 'single_frame_anomalies', 'REVIEW' if pops else 'PASS',
                  f'{len(pops)} frames that differ from both neighbours while the neighbours match (glitch, broken blink, pop)', pops)
        # jump cuts / punch-ins: a cut whose two sides have the same colour content
        jc = []
        for c in cut:
            if 1 <= c < n:
                inter = float(np.minimum(d.hist[c - 1], d.hist[c]).sum())
                if inter > self.a.jump_hist:
                    jc.append(dict(frame=c, hist_intersection=round(inter, 3),
                                   evidence=self.want(c, 'D3_jump_cut', note=f'same palette across cut {inter:.2f}')))
        self.item('D3', 'jump_cuts', 'REVIEW' if jc else 'PASS', f'{len(jc)} of {len(cut)} cuts keep the same picture content (punch-in / jump cut)', jc)
        # repeated compositions (H15): shot signatures
        bounds = [0] + cut + [n]
        shots = [(a, b) for a, b in zip(bounds, bounds[1:]) if b - a >= 6]
        sigs = [d.sig[(a + b) // 2].astype(np.float32) for a, b in shots]
        groups, seen = [], set()
        for i in range(len(shots)):
            if i in seen:
                continue
            g = [i] + [j for j in range(i + 1, len(shots)) if np.abs(sigs[i] - sigs[j]).mean() < self.a.repeat_dist]
            seen.update(g)
            if len(g) > 1:
                groups.append(g)
        rep = []
        for g in groups:
            ts = [shots[j][0] / fps for j in g]
            close = any(t2 - t1 < 60 for t1, t2 in zip(ts, ts[1:]))
            if close or len(g) > 3:
                rep.append(dict(shots=[[shots[j][0], shots[j][1]] for j in g], seconds=[round(t, 1) for t in ts],
                                rule='recurs within 60 s' if close else 'more than 3 times',
                                evidence=[self.want(shots[j][0] + 3, 'H15_repeat', note=f'repeat group {groups.index(g)}') for j in g[:4]]))
        self.item('H15/H21b', 'repeated_compositions', 'FAIL' if rep else 'PASS',
                  f'{len(shots)} shots, {len(groups)} near-identical groups, {len(rep)} break the 60 s / 3x rule', rep)
        # back half vs front half (documentary drift, H21b): motion and cut rate
        half = n // 2
        m1, m2 = float(np.mean(d.moved[:half])), float(np.mean(d.moved[half:]))
        c1, c2 = sum(1 for c in cut if c < half), sum(1 for c in cut if c >= half)
        drift = (m2 < 0.7 * m1) or (c2 < 0.7 * c1)
        self.item('H21b', 'back_half_energy', 'REVIEW' if drift else 'PASS',
                  f'moving-pixel mean {m1:.4f} -> {m2:.4f}, cuts {c1} -> {c2} (diagnostic only; judged on sheets)',
                  [dict(front=dict(motion=m1, cuts=c1), back=dict(motion=m2, cuts=c2))])
        self.shot_spans = shots

    # ----- faces, subtitles over faces / skin, small characters, face crop, hook over face -----
    def faces(self, d, faces_rt):
        fps, n = self.info['fps'], d.n
        sx, sy = AW / self.info['w'], AH / self.info['h']
        W, H = AW, AH
        faces = {}
        src = 'render-time face boxes' if faces_rt else ('YuNet every 3rd frame' if d.faces else 'none')
        if faces_rt:
            k = AW / self.info['w']
            for f, boxes in faces_rt.items():
                faces[f] = [[x0 * k, y0 * k, (x1 - x0) * k, (y1 - y0) * k, 1.0] for x0, y0, x1, y1 in boxes]
        else:
            faces = {f: list(v) for f, v in d.faces.items()}
            kx, ky = AW / self.info['w'], AH / self.info['h']
            for f in getattr(self, 'vis', {}):
                for x0, y0, x1, y1 in self.vis_heads(f):
                    faces.setdefault(f, []).append([x0 * kx, y0 * ky, (x1 - x0) * kx, (y1 - y0) * ky, 0.5])
            if getattr(self, 'vis', None):
                src += ' + imgutils heads'
        sub_hits, crop, hook = [], [], []
        for f, boxes in sorted(faces.items()):
            gb = self.sub_boxes.get(f) if f < n else None
            for x, y, w, h, s in boxes:
                if w < 6 or h < 6:
                    continue
                if gb:
                    for bx0, by0, bx1, by1 in gb:
                        ix = max(0, min(x + w, bx1) - max(x, bx0))
                        iy = max(0, min(y + h, by1) - max(y, by0))
                        if ix * iy > 0.12 * w * h:
                            sub_hits.append((f, [x, y, x + w, y + h], [bx0, by0, bx1, by1]))
                cut = (x < -0.5 or y < -0.5 or x + w > W + 0.5 or y + h > H + 0.5)
                if faces_rt:
                    vis_w = min(x + w, W) - max(x, 0)
                    vis_h = min(y + h, H) - max(y, 0)
                    if cut and vis_w > 0.15 * w and vis_h > 0.15 * h:
                        crop.append((f, [x, y, x + w, y + h]))
                elif x <= 1 or y <= 1 or x + w >= W - 1:
                    crop.append((f, [x, y, x + w, y + h]))
                if f < 3 * fps:
                    ob = d.glyph_box[f] if f < n else None
                    if ob and ob[1] < AH * 0.7:
                        bx0, by0, bx1, by1 = ob[:4]
                        ix = max(0, min(x + w, bx1) - max(x, bx0))
                        iy = max(0, min(y + h, by1) - max(y, by0))
                        if ix * iy > 0.12 * w * h:
                            hook.append((f, [x, y, x + w, y + h], ob[:4]))

        def spans(hits, gap=6):
            out = []
            for f, *bx in hits:
                if out and f - out[-1]['frames'][1] <= gap:
                    out[-1]['frames'][1] = f
                else:
                    out.append(dict(frames=[f, f], boxes=bx))
            return out
        def ev(sp, check):
            for s in sp:
                s['seconds'] = [round(s['frames'][0] / fps, 2), round(s['frames'][1] / fps, 2)]
                s['evidence'] = self.want((s['frames'][0] + s['frames'][1]) // 2, check, s['boxes'])
            return sp
        sh = ev(spans(sub_hits), 'H-subface')
        self.item('B2a/H5', 'subtitle_over_face', 'FAIL' if sh else 'PASS', f'{len(sh)} spans where the subtitle covers >12% of a face ({src})', sh)
        cr = ev(spans(crop), 'H-facecrop')
        self.item('P-crop', 'face_cut_by_frame_edge', ('FAIL' if faces_rt else 'REVIEW') if cr else 'PASS',
                  f'{len(cr)} spans with a face cut by the frame edge ({src})', cr)
        hk = ev(spans(hook), 'H-hookface')
        self.item('P-hook', 'hook_text_over_face', 'FAIL' if hk else 'PASS', f'{len(hk)} spans in the first 3 s where outlined text covers a face ({src})', hk)
        # subtitle over hands/skin (body): glyph box with skin-coloured background
        sk = [(f, [], []) for f, v in sorted(d.skin_sub.items()) if v > self.a.skin_frac]
        sks = ev(spans(sk), 'H-subskin')
        self.item('B2a', 'subtitle_over_hands_skin', 'REVIEW' if sks else 'PASS',
                  f'{len(sks)} spans where >{self.a.skin_frac:.0%} of the subtitle box background is skin tone (hands, faces)', sks)
        # small characters in empty frames: per shot the largest face height
        small = []
        for a, b in self.shot_spans:
            hs = [bx[3] for f in range(a, b) for bx in faces.get(f, [])]
            if hs and max(hs) < self.a.small_face * AH:
                small.append(dict(frames=[a, b], seconds=[round(a / fps, 2), round(b / fps, 2)], max_face_h=round(max(hs) / AH, 3),
                                  evidence=self.want((a + b) // 2, 'P-small')))
        self.item('P-small', 'small_characters', 'REVIEW' if small else 'PASS',
                  f'{len(small)} shots whose largest detected face is < {self.a.small_face:.0%} of frame height ({src}; shots without a detected face are not judged)', small)

    def subtitle_boxes(self, d, cues, tm):
        """Per-frame subtitle boxes in analysis coordinates: render-time lines if given, else glyph detection while a cue is on."""
        fps = self.info['fps']
        boxes = {}
        if tm:
            k = AW / self.info['w']
            for f, row in tm.items():
                for it in row['items']:
                    if it.get('sub'):
                        boxes[f] = [[l[0] * k, l[1] * k, l[2] * k, l[3] * k] for l in it.get('lines', []) if l[2] > l[0]]
        elif self.ocr_sub:
            k = AW / self.info['w']
            for c in cues:
                bx = [[v * k for v in b] for b in self.ocr_sub.get(c['idx'], [])]
                if bx:
                    for f in range(int(c['start'] * fps), min(d.n, int(c['end'] * fps))):
                        boxes[f] = bx
        else:
            for c in cues:
                for f in range(int(c['start'] * fps), min(d.n, int(c['end'] * fps))):
                    gb = d.glyph_box[f]
                    if gb and gb[1] > AH * 0.45:
                        boxes[f] = [gb[:4]]
        self.sub_boxes = boxes
        # subtitle size and clipping from what is actually drawn
        bad = []
        for c in cues:
            f = int((c['start'] + c['end']) / 2 * fps)
            bx = boxes.get(f)
            if not bx:
                if not tm and not self.ocr_sub:
                    bad.append(dict(cue=c['idx'], why='no subtitle glyphs found on screen while the cue is active', frame=f))
                continue
            for x0, y0, x1, y1 in bx:
                if x0 < AW * 0.05 or x1 > AW * 0.95 or y1 > AH * 0.97:
                    bad.append(dict(cue=c['idx'], why='subtitle outside title-safe / touches edge', frame=f, box=[x0, y0, x1, y1]))
            lines = 1 if (self.ocr_sub and not tm) else max(1, len(c['lines']))
            lh_an = min(b[3] - b[1] for b in bx) if lines == 1 else (max(b[3] for b in bx) - min(b[1] for b in bx)) / lines
            lh = px1080(lh_an / AH * self.info['h'], self.info)
            if lh < self.a.sub_min_px:
                bad.append(dict(cue=c['idx'], why=f'subtitle line height {lh:.0f}px@1080 < {self.a.sub_min_px}', frame=f))
        for b in bad:
            b['evidence'] = self.want(b['frame'], 'H5_subtitle_box', [b['box']] if 'box' in b else [])
        # box calibration (Korean OCR model, title-safe in analysis coords) is validated for ko only; other
        # languages list the candidates without judging them
        self.item('H5/H17a', 'subtitle_drawn_size_clip', 'FAIL' if bad and self.a.lang == 'ko' else 'PASS',
                  ('' if self.a.lang == 'ko' else f'n/a for lang={self.a.lang} (ko-only check; candidates not judged): ') + f"{len(bad)} cues with clipped/edge/small subtitles ({'render-time lines' if tm else 'OCR boxes' if self.ocr_sub else 'glyph detection'})", bad)

    # ----- imgutils hands/heads + RapidOCR on probe frames (separate venv) -----
    def vision(self, d, cues):
        self.vis = {}
        fps, n = self.info['fps'], d.n
        if self.a.no_vision or not VISION_PY.exists():
            self.item('H21a', 'hand_candidates', 'REVIEW', f'vision probe not run ({VISION_PY} missing or --no-vision)', kind='manual')
            return
        mids = [(a + b) // 2 for a, b in self.shot_spans]
        hands = sorted(set(range(0, n, self.a.hands_every)) | set(mids))
        ocr = sorted(set(range(0, n, self.a.ocr_every)) | set(mids) |
                     {min(n - 1, int((c['start'] + c['end']) / 2 * fps)) for c in cues} | set(range(0, min(n, int(3 * fps)), 5)))
        vd = self.out / 'vision'
        crops = vd / 'hand_crops'
        crops.mkdir(parents=True, exist_ok=True)
        fj, oj = vd / 'frames.json', vd / 'probe.jsonl'
        fj.write_text(json.dumps(dict(hands=hands, ocr=ocr)))
        if not (oj.exists() and self.a.reuse_probe):
            print(f'vision probe: {len(hands)} hand frames, {len(ocr)} OCR frames ...', flush=True)
            subprocess.run([str(VISION_PY), str(Path(__file__).with_name('vision_probe.py')), str(self.a.video), str(fj), str(oj),
                            '--crops', str(crops)], check=True, stderr=subprocess.DEVNULL)
        for ln in open(oj, encoding='utf-8'):
            r = json.loads(ln)
            self.vis[r['f']] = r
        # hands: candidates where fewer than 2 hands per visible character or a low-confidence hand
        cand = []
        for f in hands:
            r = self.vis.get(f, {})
            chars = max(len(r.get('persons', [])), len(r.get('heads', [])))
            hs = r.get('hands', [])
            low = [h for h in hs if h[4] < 0.35]
            if chars and (len(hs) < 2 * chars or low):
                cand.append(dict(frame=f, seconds=round(f / fps, 2), characters=chars, hands=len(hs), low_conf=len(low)))
        for c in cand[:self.a.max_evidence]:
            r = self.vis[c['frame']]
            c['evidence'] = self.want(c['frame'], 'H21a_hands', [[b[0] * AW / self.info['w'], b[1] * AH / self.info['h'],
                                                                  b[2] * AW / self.info['w'], b[3] * AH / self.info['h']] for b in r['hands']])
        # hand-crop contact sheets: every detected hand, frame number burned in
        files = sorted(crops.glob('hand_f*.png'))
        hs_dir = self.out / 'hand_sheets'
        hs_dir.mkdir(exist_ok=True)
        font = ImageFont.truetype(FONT, 18)
        self.hand_sheets = []
        for k in range(0, len(files), 12):
            sh = Image.new('RGB', (4 * 240, 3 * 240), 'black')
            dr = ImageDraw.Draw(sh)
            for j, p in enumerate(files[k:k + 12]):
                im = Image.open(p).convert('RGB')
                im.thumbnail((240, 240))
                x, y = (j % 4) * 240, (j // 4) * 240
                sh.paste(im, (x, y))
                m = re.match(r'hand_f(\d+)_(\d+)_(\d+)', p.stem)
                dr.rectangle((x, y, x + 150, y + 22), fill='black')
                dr.text((x + 3, y + 1), f'f{int(m[1])} c{int(m[3]) / 100:.2f}', fill='yellow', font=font)
            name = f'h_{k // 12 + 1:04d}.jpg'
            sh.save(hs_dir / name, quality=85)
            self.hand_sheets.append(dict(sheet=name, crops=[p.name for p in files[k:k + 12]]))
        self.item('H21a/H17b', 'hand_candidates', 'REVIEW' if cand else 'PASS',
                  f'imgutils detect_hands on {len(hands)} frames: {sum(len(self.vis.get(f, {}).get("hands", [])) for f in hands)} hands, '
                  f'{len(cand)} candidate frames (hands < 2x characters or conf < 0.35); {len(self.hand_sheets)} hand-crop sheets to sign',
                  cand)

    def ocr_checks(self, d, cues):
        """RapidOCR PP-OCRv5 Korean: subtitle text vs SRT, on-screen text clipping/size/overlap, hook over face."""
        self.ocr_sub = {}
        if not self.vis:
            return
        fps, W, H = self.info['fps'], self.info['w'], self.info['h']
        nospace = lambda s: re.sub(r'[\s.,!?…\'"“”‘’·]', '', s)
        active = {}
        for c in cues:
            for f in range(int(c['start'] * fps), int(c['end'] * fps)):
                active[f] = c
        self.ocr_texts, mism, clip, small, over, hook = [], [], [], [], [], []
        self.ocr_sub = {}
        for f, r in sorted(self.vis.items()):
            if 'ocr' not in r:
                continue
            c = active.get(f)
            ctext = nospace(c['text']) if c else ''
            subs, others = [], []
            for x0, y0, x1, y1, t, s in r['ocr']:
                tt = nospace(t)
                if s < 0.6 or not tt:
                    continue
                if c and y0 > H * 0.6 and (tt in ctext or sum(ch in ctext for ch in tt) >= 0.8 * len(tt)):
                    subs.append([x0, y0, x1, y1, t])
                else:
                    others.append([x0, y0, x1, y1, t, s])
            if c and f == min(int((c['start'] + c['end']) / 2 * fps), d.n - 1):
                self.ocr_sub[c['idx']] = [b[:4] for b in subs]
                got = ''.join(nospace(b[4]) for b in subs)
                hit = sum(ch in got for ch in ctext) / max(1, len(ctext))
                if hit < 0.6:
                    mism.append(dict(cue=c['idx'], frame=f, srt=c['text'].replace('\n', ' / '), ocr=got, match=round(hit, 2)))
            for x0, y0, x1, y1, t, s in others:
                self.ocr_texts.append((f, t))
                if x0 <= 2 or y0 <= 2 or x1 >= W - 2 or y1 >= H - 2:
                    clip.append(dict(frame=f, text=t, box=[x0, y0, x1, y1]))
                hpx = px1080(y1 - y0, self.info)
                if len(nospace(t)) >= 2 and hpx < self.a.ocr_min_px:
                    small.append(dict(frame=f, text=t, line_px_1080=round(hpx), box=[x0, y0, x1, y1]))
                for b in subs:
                    ix = max(0, min(x1, b[2]) - max(x0, b[0]))
                    iy = max(0, min(y1, b[3]) - max(y0, b[1]))
                    if ix * iy > 0:
                        over.append(dict(frame=f, text=t, subtitle=b[4], box=[x0, y0, x1, y1]))
                if f < 3 * fps:
                    for hb in self.vis_heads(f):
                        fx0, fy0, fx1, fy1 = hb
                        ix = max(0, min(x1, fx1) - max(x0, fx0))
                        iy = max(0, min(y1, fy1) - max(y0, fy0))
                        if ix * iy > 0.1 * (fx1 - fx0) * (fy1 - fy0):
                            hook.append(dict(frame=f, text=t, box=[x0, y0, x1, y1], face=hb))
        k = AW / W
        def ev(rows, check, cap=None):
            seen = set()
            for row in rows:
                key = (row['frame'] // 15, row.get('text'))
                if key in seen:
                    continue
                seen.add(key)
                bx = [[v * k for v in row['box']]] if 'box' in row else []
                row['evidence'] = self.want(row['frame'], check, bx, note=str(row.get('text', ''))[:30])
            return rows
        ev(mism, 'O1_sub_mismatch')
        ko = self.a.lang == 'ko'  # RapidOCR model here is Korean; en/ja candidates are listed, not judged
        na = '' if ko else f'n/a for lang={self.a.lang} (Korean OCR model; candidates not judged): '
        self.item('H5/F2', 'burned_subtitle_vs_srt', 'REVIEW' if mism and ko else 'PASS',
                  na + f'{len(mism)} cues whose burned-in text does not match the SRT (OCR <60% chars; space-insensitive)', mism)
        ev(clip, 'O2_text_clip')
        ev(small, 'O3_text_small')
        ev(over, 'O4_text_under_sub')
        bad = clip + small + over
        self.item('H22c/B2a', 'ocr_text_clip_size_overlap', 'FAIL' if bad and ko else 'PASS',
                  na + f'OCR on {sum(1 for r in self.vis.values() if "ocr" in r)} frames: {len(clip)} text boxes at frame edge, '
                  f'{len(small)} lines < {self.a.ocr_min_px}px@1080, {len(over)} on-screen texts under the subtitle', bad)
        ev(hook, 'O5_hook_face')
        self.item('P-hook', 'hook_text_over_face_ocr', 'FAIL' if hook else 'PASS',
                  f'{len(hook)} first-3s text boxes covering a detected head (imgutils heads)', hook)

    def vis_heads(self, f):
        """Face part of imgutils head boxes (lower 65 %), source pixels."""
        r = self.vis.get(f, {})
        return [[x0, y0 + 0.35 * (y1 - y0), x1, y1] for x0, y0, x1, y1, s in r.get('heads', []) if s >= 0.5]

    def onscreen_text(self, d, tm):
        fps = self.info['fps']
        found = []
        if tm:
            W, H = self.info['w'], self.info['h']
            seen = {}
            for f, row in sorted(tm.items()):
                for it in row['items']:
                    if it.get('sub') or it.get('occ', 0) >= 85:
                        continue
                    t, (x0, y0, x1, y1) = it['t'], it['r']
                    if x1 <= 0 or x0 >= W or y1 <= 0 or y0 >= H:
                        continue
                    probs = []
                    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                        probs.append('cut by frame edge')
                    if it.get('box'):
                        bx = it['box']
                        if x0 < bx[0] - 2 or y0 < bx[1] - 2 or x1 > bx[2] + 2 or y1 > bx[3] + 2:
                            probs.append('clipped by its container')
                    if it.get('panel'):
                        pn = it['panel']
                        if x0 < pn[0] - 2 or x1 > pn[2] + 2:
                            probs.append('wider than its panel')
                        elif min(x0 - pn[0], pn[2] - x1) < 0.5 * (it.get('fs') or 20):
                            probs.append('no padding inside panel (H22c)')
                    if '…' in t:
                        probs.append('truncated with ellipsis')
                    if it.get('subHit'):
                        probs.append('overlaps the subtitle')
                    if 5 <= it.get('occ', 0) < 85 and (it.get('fs') or 0) >= 18:
                        probs.append(f"partly covered by {it.get('by') or 'shape'}")
                    fs = it.get('fs') or 0
                    if len(re.sub(r'[^가-힣A-Za-z0-9]', '', t)) >= 1 and fs and fs < self.a.text_min_px:
                        probs.append(f'font {fs}px@1080 < {self.a.text_min_px}')
                    for pr in probs:
                        key = (row.get('sid'), t, pr)
                        if key not in seen:
                            seen[key] = dict(sid=row.get('sid'), text=t[:40], problem=pr, frames=[f, f], n=0)
                            found.append(seen[key])
                        seen[key]['frames'][1] = f
                        seen[key]['n'] += 1
            for x in found:
                x['evidence'] = self.want((x['frames'][0] + x['frames'][1]) // 2, 'H22c_text', note=f"{x['text']} {x['problem']}")
            src = 'render-time text boxes'
        elif getattr(self, 'vis', None):
            self.item('H22c/H17a', 'onscreen_text_clip_size', 'PASS', 'no render-time boxes; covered by ocr_text_clip_size_overlap')
            return
        else:
            # OCR-free fallback: outlined text glyphs touching the frame border
            hits = [i for i, v in enumerate(d.glyph_edge) if v > 8]
            for a, b in runs([i in set(hits) for i in range(d.n)], 3):
                found.append(dict(frames=[a, b], problem='outlined text touches frame edge',
                                  evidence=self.want((a + b) // 2, 'H22c_text')))
            src = 'glyph-at-border heuristic (no render-time boxes: panel text clipping NOT covered)'
        hard = [x for x in found if 'padding' not in x['problem']]
        self.item('H22c/H17a', 'onscreen_text_clip_size', 'FAIL' if hard else ('REVIEW' if found else 'PASS'),
                  f'{len(found)} text problems ({src})', found)

    # ----- words -----
    def words(self, cues, tm):
        if self.a.lang != 'ko':
            self.item('H19a/H21c/H16/E1/H9/H4', 'banned_words', 'PASS',
                      f'skipped for {self.a.lang}: the banned-word list is Korean (manual review of the {self.a.lang} script instead)')
            return
        texts = [('srt', c['idx'], c['start'], c['text'].replace('\n', ' ')) for c in cues]
        if tm:
            seen = set()
            for f, row in sorted(tm.items()):
                for it in row['items']:
                    if not it.get('sub') and it['t'] not in seen and it.get('occ', 0) < 85:
                        seen.add(it['t'])
                        texts.append(('screen', row.get('sid'), f / self.info['fps'], it['t']))
        for f, t in getattr(self, 'ocr_texts', []):
            texts.append(('ocr', f, f / self.info['fps'], t))
        for p in self.a.script or []:
            for i, ln in enumerate(Path(p).read_text(encoding='utf-8').splitlines()):
                if re.search(r'[가-힣]', ln):
                    texts.append(('script', f'{Path(p).name}:{i + 1}', None, ln))
        fails, revs = [], []
        for src, ref, t, txt in texts:
            for name, (rx, iid, sev) in BANNED.items():
                for m in re.finditer(rx, txt):
                    if name == 'disclaimer' and src in ('screen', 'ocr'):
                        sev = 'FAIL'
                    row = dict(source=src, ref=ref, time=t, word=m.group(0), rule=name, item=iid, text=txt[:60])
                    (fails if sev == 'FAIL' else revs).append(row)
            for m in re.finditer(r'(?<![A-Za-z])[A-Z]{2,6}(?![A-Za-z])', txt):
                if m.group(0) not in ACRONYM_OK and not re.search(r'TRM|OFAC|KYC|AML', m.group(0)):
                    revs.append(dict(source=src, ref=ref, time=t, word=m.group(0), rule='acronym', item='H19a', text=txt[:60]))
        for r in fails + revs:
            if r['time'] is not None:
                r['evidence'] = self.want(int(r['time'] * self.info['fps']) + 3, 'H19_words', note=r['word'])
        self.item('H19a/H21c/H16/E1/H9/H4', 'banned_words', 'FAIL' if fails else ('REVIEW' if revs else 'PASS'),
                  f'{len(fails)} banned, {len(revs)} to review in {len(texts)} texts (srt, on-screen, script)', fails + revs)

    def overstatement(self, cues):
        lines = [('hook_srt', c['text'].replace('\n', ' ')) for c in cues if c['start'] < 5.0]
        for p in self.a.titles or []:
            body = Path(p).read_text(encoding='utf-8')
            m = re.search(r'\[제목\]\s*\n(.+)', body)
            if m:
                lines.append((f'title:{Path(p).name}', m.group(1).strip()))
            else:
                lines += [(f'title:{Path(p).name}', ln.strip()) for ln in body.splitlines()[:5] if ln.strip()]
        facts = Path(self.a.facts).read_text(encoding='utf-8') if self.a.facts else ''
        out = []
        for src, txt in lines:
            for rx in OVERSTATE:
                for m in re.finditer(rx, txt):
                    w = m.group(0)
                    num = re.search(r'\d+', w)
                    support = []
                    if facts and num:
                        for fm in re.finditer(re.escape(num.group(0)) + r'\s?(초|분|시간|일)', facts):
                            ctx = facts[max(0, fm.start() - 40):fm.end() + 20].replace('\n', ' ')
                            support.append(ctx)
                    qualified = any(re.search(QUALIFIER, s) for s in support)
                    out.append(dict(source=src, text=txt, word=w,
                                    facts=('qualifier dropped: facts say ' + support[0][:80]) if qualified and not re.search(QUALIFIER, txt)
                                    else (support[0][:80] if support else ('no facts file' if not facts else 'not found in facts'))))
        self.item('P-overstate', 'hook_title_overstatement', 'REVIEW' if out else 'PASS',
                  f'{len(out)} strong claims in hook/title to check against the facts table (manual verdict)', out)

    def loudness(self):
        if not self.info['audio']:
            self.item('F2', 'loudness_true_peak', 'FAIL', 'no audio stream')
            return
        m = measure_audio(self.a.video)
        i, tp = m['integrated_lufs'], m['true_peak_dbtp']
        bad = []
        if i is None or abs(i - self.a.lufs) > 1.0:
            bad.append(f'integrated {i} LUFS not {self.a.lufs}±1')
        if tp is None or tp > self.a.tp:
            bad.append(f'true peak {tp} dBTP > {self.a.tp}')
        self.item('F2', 'loudness_true_peak', 'FAIL' if bad else 'PASS', f'{i} LUFS, {tp} dBTP, LRA {m["lra_lu"]}', bad)

    def thumbnails(self, d):
        if not self.a.thumbnail:
            self.item('T-thumb', 'thumbnail_reuses_frame', 'REVIEW', 'no thumbnail given: check manually', kind='manual')
            return
        res = []
        sig = d.sig.reshape(d.n, -1).astype(np.float32)
        for t in self.a.thumbnail:
            im = Image.open(t).convert('RGB')
            r = im.width / im.height
            if abs(r - 16 / 9) > 0.05:
                res.append(dict(thumbnail=t, frame=None, dist=None, why=f'aspect {r:.2f}, compared skipped'))
                continue
            s = np.asarray(im.resize((32, 18), Image.BILINEAR), np.float32).reshape(-1)
            dist = np.abs(sig - s).mean(1)
            j = int(dist.argmin())
            row = dict(thumbnail=t, nearest_frame=j, seconds=round(j / self.info['fps'], 2), dist=round(float(dist[j]), 1))
            if dist[j] < self.a.thumb_dist:
                row['why'] = 'thumbnail is a reused film frame'
                row['evidence'] = self.want(j, 'T_thumb_reuse', note=Path(t).name)
            res.append(row)
        bad = [r for r in res if r.get('why') == 'thumbnail is a reused film frame']
        self.item('T-thumb', 'thumbnail_reuses_frame', 'FAIL' if bad else 'PASS', f'{len(bad)} of {len(res)} thumbnails match a film frame (dist < {self.a.thumb_dist})', res)

    # ----- manual sign-off -----
    def manual(self, d, vsha):
        tpl = dict(video=str(self.a.video), video_sha256=vsha, reviewer='', reviewed_at='',
                   rule='Every sheet must be opened at 100 %. verdict PASS/FAIL per sheet; every check filled ok/fail/na; '
                        'frames of any problem in notes. Missing or stale (sha mismatch) = FAIL.',
                   sheets=[dict(sheet=s['sheet'], frames=s['frames'], verdict='', checks={c: '' for c in SHEET_CHECKS}, notes='')
                           for s in d.sheet_files],
                   hand_sheets=[dict(sheet=h['sheet'], verdict='', notes='') for h in getattr(self, 'hand_sheets', [])],
                   items={k: dict(question=v, verdict='', evidence='') for k, v in MANUAL_ITEMS.items()},
                   candidates={it['check']: dict(status=it['status'], cleared='', note='') for it in self.items if it['status'] == 'REVIEW'})
        (self.out / 'review_log.template.json').write_text(json.dumps(tpl, ensure_ascii=False, indent=1), encoding='utf-8')
        log = None
        if self.a.review_log and Path(self.a.review_log).exists():
            log = json.loads(Path(self.a.review_log).read_text(encoding='utf-8'))
        probs = []
        if not d.sheet_files:
            probs.append('contact sheets not generated (--no-sheets): manual review impossible')
        if log is None:
            probs.append(f'no review log signed ({len(d.sheet_files)} sheets, {len(getattr(self, "hand_sheets", []))} hand sheets, '
                         f'{len(MANUAL_ITEMS)} manual items unsigned)')
        else:
            if log.get('video_sha256') != vsha:
                probs.append('review log is for a different video (sha256 mismatch)')
            if not log.get('reviewer'):
                probs.append('review log has no reviewer')
            got = {s['sheet']: s for s in log.get('sheets', [])}
            missing = [s['sheet'] for s in d.sheet_files if s['sheet'] not in got or got[s['sheet']].get('verdict') not in ('PASS', 'FAIL')
                       or any(v not in ('ok', 'fail', 'na') for v in got[s['sheet']].get('checks', {}).values())]
            failed = [s for s, v in got.items() if v.get('verdict') == 'FAIL']
            hs = {h['sheet']: h for h in log.get('hand_sheets', [])}
            hmiss = [h['sheet'] for h in getattr(self, 'hand_sheets', []) if hs.get(h['sheet'], {}).get('verdict') not in ('PASS', 'FAIL')]
            if hmiss:
                probs.append(f'{len(hmiss)} hand-crop sheets not signed')
            if any(v.get('verdict') == 'FAIL' for v in hs.values()):
                probs.append('hand-crop sheets FAILED by the reviewer')
            if missing:
                probs.append(f'{len(missing)} sheets not signed (first {missing[:3]})')
            if failed:
                probs.append(f'{len(failed)} sheets FAILED by the reviewer')
            for k in MANUAL_ITEMS:
                v = log.get('items', {}).get(k, {})
                if v.get('verdict') not in ('PASS', 'NA') or (v.get('verdict') == 'PASS' and not v.get('evidence')):
                    probs.append(f'manual item {k} not passed with evidence')
            for it in self.items:
                if it['status'] == 'REVIEW':
                    c = log.get('candidates', {}).get(it['check'], {})
                    if c.get('cleared') != 'yes':
                        probs.append(f"candidates of {it['check']} not cleared")
                    else:
                        it['status'] = 'PASS (cleared)'
        self.item('F1/H13/H21a/manual', 'manual_signoff', 'FAIL' if probs else 'PASS',
                  f'{len(d.sheet_files)} sheets (every frame, 4x3); log: {self.a.review_log or "none"}', probs, kind='manual')

    # ----- evidence images -----
    def render_evidence(self):
        """One full-resolution decode pass; every requested frame is labelled (frame, time, check) and saved as PNG."""
        cap = self.a.max_evidence
        by_check, todo = {}, {}
        for f, check, boxes, note in self.evidence_req:
            f = min(max(0, f), self.n - 1)
            by_check.setdefault(check, set())
            if len(by_check[check]) < cap or f in by_check[check]:
                by_check[check].add(f)
                todo.setdefault(f, {})[check] = (boxes, note)
        if not todo:
            return
        w, h = self.info['w'], self.info['h']
        font = ImageFont.truetype(FONT, 26)
        sx = w / AW
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(self.a.video), '-map', '0:v:0', '-fps_mode', 'passthrough',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        last, n = max(todo), 0
        while n <= last:
            raw = p.stdout.read(w * h * 3)
            if not raw:
                break
            if n in todo:
                base = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
                for check, (boxes, note) in todo[n].items():
                    im = Image.fromarray(base)
                    dr = ImageDraw.Draw(im)
                    for b in boxes:
                        if b and len(b) >= 4:
                            dr.rectangle((b[0] * sx, b[1] * sx, b[2] * sx, b[3] * sx), outline='red', width=3)
                    label = f'f{n}  {n / self.info["fps"]:.2f}s  {check}  {note}'[:90]
                    dr.rectangle((0, 0, w, 36), fill='black')
                    dr.text((8, 4), label, fill='yellow', font=font)
                    im.save(self.ev / f'{check}_f{n:05d}.png')
            n += 1
        p.stdout.close()
        p.kill()
        p.wait()


def scene_cuts(video, n):
    """PySceneDetect (BSD-3) ContentDetector: cut frames and per-frame content_val. (None, None, why) if not installed."""
    try:
        from scenedetect import open_video, SceneManager, StatsManager
        from scenedetect.detectors import ContentDetector
    except Exception:
        return None, np.zeros(n), 'frame-diff heuristic (PySceneDetect not installed)'
    v = open_video(str(video))
    sm = StatsManager()
    scm = SceneManager(sm)
    scm.add_detector(ContentDetector(threshold=27, min_scene_len=6))
    scm.detect_scenes(v)
    cuts = [s[0].frame_num for s in scm.get_scene_list()[1:]]
    cv = np.array([(sm.get_metrics(i, ['content_val'])[0] or 0.0) if sm.metrics_exist(i, ['content_val']) else 0.0
                   for i in range(n)], float)
    return cuts, cv, 'PySceneDetect ContentDetector(27)'


def load_jsonl_frames(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        r = json.loads(ln)
        out[int(r['f'])] = r
    return out


def load_shots(path, fps):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = data if isinstance(data, list) else data.get('shots', [])
    out = []
    for s in rows:
        a = s['start_s'] * fps if 'start_s' in s else s.get('a', s.get('from', 0))
        b = s['end_s'] * fps if 'end_s' in s else s.get('b', s.get('to', a + s.get('dur', 0)))
        out.append(dict(id=s.get('id'), a=int(round(a)), b=int(round(b))))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--srt', required=True)
    ap.add_argument('--out')
    ap.add_argument('--shots')
    ap.add_argument('--script', nargs='*')
    ap.add_argument('--text-measure')
    ap.add_argument('--face-measure')
    ap.add_argument('--voice')
    ap.add_argument('--facts')
    ap.add_argument('--titles', nargs='*')
    ap.add_argument('--thumbnail', nargs='*')
    ap.add_argument('--review-log')
    ap.add_argument('--format', choices=['longform', 'shorts'], default='longform')
    ap.add_argument('--no-sheets', action='store_true')
    ap.add_argument('--no-faces', action='store_true')
    ap.add_argument('--no-vision', action='store_true', help='skip imgutils hands/heads and RapidOCR')
    ap.add_argument('--reuse-probe', action='store_true', help='reuse OUT/vision/probe.jsonl')
    ap.add_argument('--hands-every', type=int, default=30)
    ap.add_argument('--ocr-every', type=int, default=15)
    ap.add_argument('--ocr-min-px', type=float, default=30, help='min OCR line height at 1080p')
    ap.add_argument('--line-max', type=int)
    ap.add_argument('--hold', type=float, default=1.5, help='static hold limit, seconds (C2/H6)')
    ap.add_argument('--still-frac', type=float, default=0.025, help='5-frame median moving-pixel fraction below which a frame is still')
    ap.add_argument('--spike', type=float, default=0.003, help='spike-pixel fraction for a single-frame anomaly')
    ap.add_argument('--flash', type=float, default=0.06)
    ap.add_argument('--jump-hist', type=float, default=0.80)
    ap.add_argument('--repeat-dist', type=float, default=9.0)
    ap.add_argument('--small-face', type=float, default=0.10)
    ap.add_argument('--skin-frac', type=float, default=0.25)
    ap.add_argument('--sub-min-px', type=float, default=48)
    ap.add_argument('--text-min-px', type=float, default=28)
    ap.add_argument('--min-cue', type=float, default=0.8)
    ap.add_argument('--cue-rule', choices=['fixed', 'per_word'], default='fixed',
                    help='fixed: every cue >= --min-cue (default). per_word: 0.25 s per word, never under 0.35 s; Beast Clash only '
                         '(1-3 word captions at >= 3.4 words/s cannot hold 0.8 s; reference study 2026-11-14)')
    ap.add_argument('--max-cps', type=float, help='reading speed limit, chars/s (default ko 14, en 20, ja 8)')
    ap.add_argument('--lang', choices=['ko', 'en', 'ja'], default='ko', help='subtitle language; en/ja skip the Korean-only analyser')
    ap.add_argument('--early', type=float, default=0.30)
    ap.add_argument('--late', type=float, default=0.25)
    ap.add_argument('--silence-db', default='-35dB')
    ap.add_argument('--lufs', type=float, default=-14.0)
    ap.add_argument('--tp', type=float, default=-1.0)
    ap.add_argument('--thumb-dist', type=float, default=10.0)
    ap.add_argument('--max-evidence', type=int, default=40)
    a = ap.parse_args(argv)
    a.max_cps = a.max_cps or {'ko': 14.0, 'en': 20.0, 'ja': 8.0}[a.lang]
    a.out = a.out or str(Path(a.video).parent / 'gate')
    g = Gate(a)
    g.info = info = probe(a.video)
    set_analysis_size(info)
    cues = subtitle_ko.parse_srt(a.srt)
    g.shots = load_shots(a.shots, info['fps']) if a.shots else None
    tm = load_jsonl_frames(a.text_measure) if a.text_measure else None
    fm = None
    if a.face_measure:
        fm = {f: r.get('faces', []) for f, r in load_jsonl_frames(a.face_measure).items()}
    print('decoding every frame ...', flush=True)
    d = Decoder(a.video, info, g.out, sheets=not a.no_sheets, faces=not a.no_faces and fm is None).run(cues)
    g.n = d.n
    vsha = sha256(a.video)
    g.subtitles(cues)
    g.timing(cues)
    g.frames(d)
    g.vision(d, cues)
    g.ocr_checks(d, cues)
    g.subtitle_boxes(d, cues, tm)
    g.faces(d, fm)
    g.onscreen_text(d, tm)
    g.words(cues, tm)
    g.overstatement(cues)
    g.loudness()
    g.thumbnails(d)
    g.manual(d, vsha)
    g.render_evidence()
    np.savez_compressed(g.out / 'perframe.npz', spike=d.spike, moved=d.moved, lag2=d.lag2, luma=d.luma, sat=d.sat, content_val=g.content_val)
    overall = 'PASS' if all(i['status'].startswith('PASS') for i in g.items) else 'FAIL'
    rep = dict(video=str(a.video), video_sha256=vsha, frames=d.n, fps=info['fps'], overall=overall,
               inputs=dict(srt=a.srt, shots=a.shots, text_measure=a.text_measure, face_measure=a.face_measure, voice=a.voice,
                           facts=a.facts, titles=a.titles, thumbnail=a.thumbnail, review_log=a.review_log),
               limits='No real-time playback. OCR-free. Faces: render-time boxes if given, else YuNet on every 3rd frame '
                      '(cartoon recall partial). REVIEW items are candidates, not proof.',
               items=g.items)
    (g.out / 'gate.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding='utf-8')
    md = [f'# QA gate — {Path(a.video).name}: **{overall}**', f'frames {d.n} @ {info["fps"]:g} fps, sha256 {vsha[:12]}', '',
          '| id | check | status | summary |', '|---|---|---|---|']
    md += [f"| {i['id']} | {i['check']} | {i['status']} | {i['summary']} |" for i in g.items]
    (g.out / 'gate.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    return 0 if overall == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
