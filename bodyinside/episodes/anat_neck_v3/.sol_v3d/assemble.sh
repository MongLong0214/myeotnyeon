#!/bin/bash
set -euo pipefail
stage="$PWD/.sol_v3d"
prior="$PWD/.sol_v3c.XmcN0Qgw"
kit="$PWD/../../anat_kit"
py="$PWD/../../.venv/bin/python"
cp episode.json "$stage/episode.json"
cp description.txt "$stage/description.txt"
for item in ABOUT_BLOCK.txt REFERENCES.txt SOURCES.md assets.json audio comp label_pos.json pose_dump.json scene_dump.json thresholds.json; do
    ln -sfn "$prior/$item" "$stage/$item"
done
# The existing CRF 6 assembler copies audio from its draft4 input. Use v3c as that input.
ln -sfn "$prior/final_hq_v3c.mp4" "$stage/draft4.mp4"
mkdir -p "$stage/gates"
fin=frames_final_hq_v3d
"$py" - "$stage" "$prior" "$fin" <<'PY'
import os
from pathlib import Path
import sys
from PIL import Image

stage, prior = map(Path, sys.argv[1:3])
final = stage / sys.argv[3]
raw = stage / 'affected_raw'
final.mkdir(exist_ok=True)
raw.mkdir(exist_ok=True)
rendered = {}
for folder in (stage/'open_batches.txt').read_text().splitlines():
    for path in Path(folder).glob('f_*.png'):
        with Image.open(path) as image:
            assert image.size == (1080, 880) and image.mode == 'RGBA', path
            image.verify()
        assert path.name not in rendered
        rendered[path.name] = path
assert len(rendered) == 61
for frame in range(924):
    name = f'f_{frame:04d}.png'
    if frame <= 60:
        source, dst = rendered[name], raw/name
    elif 332 <= frame <= 722:
        source, dst = prior/'frames_final_hq_v3c_raw'/name, raw/name
    else:
        source, dst = prior/'frames_final_hq_v3c'/name, final/name
    if not dst.exists():
        os.link(source, dst)
PY
"$py" -I "$kit/layout/labels2d.py" "$stage" "$stage/affected_raw" "$stage/$fin"
cp "$prior/plumb_draw.json" "$stage/plumb_draw.json"
[[ $(find "$stage/$fin" -name 'f_*.png' | wc -l) == 924 ]]
"$py" .sol_v3.mNVBQ6v4/assemble_crf6.py "$stage" "$stage/$fin/f_%04d.png" "$stage/final_hq_v3d.mp4"
