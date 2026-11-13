"""Hand / person / head detection and Korean OCR on selected frames. Runs in research/new_refs/.venv (imgutils, RapidOCR).

  research/new_refs/.venv/bin/python factory/qa/vision_probe.py VIDEO FRAMES.json OUT.jsonl [--hands] [--ocr] [--crops DIR]

FRAMES.json: {"hands": [frame,...], "ocr": [frame,...]}. One JSON row per probed frame:
  {"f": n, "hands": [[x0,y0,x1,y1,score],...], "persons": [...], "heads": [...], "ocr": [[x0,y0,x1,y1,text,score],...]}
Coordinates are in source pixels. Candidate extraction only; never a pass/fail by itself.
Hand crops (every detected hand, frame number burned in) go to --crops as PNG for the hand contact sheets.
"""
import argparse
import json
import sys

import cv2
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('frames')
    ap.add_argument('out')
    ap.add_argument('--crops')
    a = ap.parse_args()
    want = json.load(open(a.frames))
    hands_f, ocr_f = set(want.get('hands', [])), set(want.get('ocr', []))
    allf = hands_f | ocr_f
    if hands_f:
        from imgutils.detect import detect_person, detect_heads
        from imgutils.detect.hand import detect_hands
    if ocr_f:
        from rapidocr import RapidOCR, LangRec, OCRVersion, ModelType
        eng = RapidOCR(params={'Rec.lang_type': LangRec.KOREAN, 'Rec.ocr_version': OCRVersion.PPOCRV5,
                               'Rec.model_type': ModelType.MOBILE})
    cap = cv2.VideoCapture(a.video)
    out = open(a.out, 'w')
    n, last = 0, max(allf) if allf else -1
    while n <= last:
        ok, bgr = cap.read()
        if not ok:
            break
        if n in allf:
            row = dict(f=n)
            if n in hands_f:
                im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                row['hands'] = [[*map(int, b), round(float(s), 3)] for b, _, s in detect_hands(im)]
                row['persons'] = [[*map(int, b), round(float(s), 3)] for b, _, s in detect_person(im)]
                row['heads'] = [[*map(int, b), round(float(s), 3)] for b, _, s in detect_heads(im)]
                if a.crops:
                    for k, (x0, y0, x1, y1, s) in enumerate(row['hands']):
                        pad = int(0.35 * max(x1 - x0, y1 - y0))
                        c = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))
                        c.save(f'{a.crops}/hand_f{n:05d}_{k}_{int(s * 100):02d}.png')
            if n in ocr_f:
                r = eng(bgr)
                boxes = r.boxes if r.boxes is not None else []
                row['ocr'] = []
                for t, s, b in zip(r.txts or [], r.scores or [], boxes):
                    xs, ys = [p[0] for p in b], [p[1] for p in b]
                    row['ocr'].append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), t, round(float(s), 3)])
            out.write(json.dumps(row, ensure_ascii=False) + '\n')
            out.flush()
        n += 1
    out.close()
    print('probed', len(allf), 'frames', file=sys.stderr)


if __name__ == '__main__':
    main()
