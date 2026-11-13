"""Thumbnail at phone size (x-nowlovepan idea; no licence, idea only, written anew). Report-only.

  .venv/bin/python factory/lib/thumb_check.py THUMB.png OUT_DIR [--text-px 120]

Writes OUT_DIR/thumb_sheet.png with the thumbnail at 160 and 320 px wide, side by side, and reports how tall a
`text_px` line (measured at 1280 px wide) becomes at each width; warns when it is under 12 px at 160 px.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

WIDTHS = (160, 320)
MIN_PX_160 = 12


def check(png, out_dir, text_px=None):
    im = Image.open(png).convert('RGB')
    smalls = [im.resize((w, max(1, round(im.height * w / im.width))), Image.LANCZOS) for w in WIDTHS]
    pad = 16
    sheet = Image.new('RGB', (sum(s.width for s in smalls) + pad * (len(smalls) + 1), max(s.height for s in smalls) + 2 * pad), 'white')
    x = pad
    for s in smalls:
        sheet.paste(s, (x, pad))
        x += s.width + pad
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sheet_path = out / 'thumb_sheet.png'
    sheet.save(sheet_path)
    report = dict(status='ADVISORY', sheet=str(sheet_path), source_width=im.width, warnings=[])
    if text_px:
        report['text_px'] = {str(w): round(text_px * w / 1280, 1) for w in WIDTHS}
        if text_px * 160 / 1280 < MIN_PX_160:
            report['warnings'].append(f'text {text_px} px at 1280 is {text_px * 160 / 1280:.1f} px at 160 wide (< {MIN_PX_160})')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('png')
    ap.add_argument('out_dir')
    ap.add_argument('--text-px', type=float)
    a = ap.parse_args()
    print(json.dumps(check(a.png, a.out_dir, a.text_px), indent=1))
    sys.exit(0)
