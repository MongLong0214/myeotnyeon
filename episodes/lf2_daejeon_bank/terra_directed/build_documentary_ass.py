#!/usr/bin/env python3
"""Build deterministic broadcast-style ASS from the locked cue files."""
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])
WIDTH = int(sys.argv[3]) if len(sys.argv) > 3 else 640
HEIGHT = int(sys.argv[4]) if len(sys.argv) > 4 else 360
FONT_SIZE = round(31 * WIDTH / 640)
MARGIN_LR = round(28 * WIDTH / 640)
MARGIN_V = round(13 * HEIGHT / 360)

HEADER = f"""[Script Info]
Title: LF2 documentary captions
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Caption,Pretendard,{FONT_SIZE},&H00F8F7F2,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,{MARGIN_LR},{MARGIN_LR},{MARGIN_V},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

def stamp(value: str) -> str:
    h, m, sec_ms = value.split(':')
    sec, ms = sec_ms.split(',')
    return f"{int(h)}:{int(m):02d}:{int(sec):02d}.{int(ms)//10:02d}"

def date_ko(text: str) -> str:
    return re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", r"\1년 \2월 \3일", text)

def linebreak(text: str) -> str:
    # Keep locked words and cue boundaries; only split long lines at a meaning-preserving space.
    text = date_ko(text)
    if len(text) <= 18 or ' ' not in text:
        return text
    # Never split a Korean date itself; after its comma is the nearest semantic break.
    comma = text.find(',')
    if re.match(r'^\d{4}년 \d{2}월 \d{2}일, ', text) and comma > 0:
        cut = comma + 1
        return text[:cut] + r'\N' + text[cut+1:]
    target = len(text) // 2
    spaces = [i for i, c in enumerate(text) if c == ' ']
    cut = min(spaces, key=lambda i: abs(i-target))
    return text[:cut] + r'\N' + text[cut+1:]

blocks = re.split(r'\n\s*\n', SRC.read_text(encoding='utf-8').strip())
events = []
for block in blocks:
    rows = block.splitlines()
    if len(rows) < 3:
        continue
    start, end = rows[1].split(' --> ')
    text = ' '.join(row.strip() for row in rows[2:])
    events.append((stamp(start), stamp(end), linebreak(text)))

if not events:
    raise SystemExit('no subtitle events')
DST.write_text(HEADER + ''.join(
    f'Dialogue: 0,{start},{end},Caption,,0,0,0,,{text}\n' for start, end, text in events
), encoding='utf-8')
print(f'{SRC.name}: {len(events)} cues -> {DST.name}')
