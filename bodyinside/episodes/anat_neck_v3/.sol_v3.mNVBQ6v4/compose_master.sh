#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
work="$(cd "$episode/../.." && pwd)"
kit="$work/anat_kit"
py="$work/.venv/bin/python"
blender=/Applications/Blender.app/Contents/MacOS/Blender
cd "$stage"
raw=frames_final_hq_v3_raw
labels=frames_final_hq_v3
mkdir -p "$raw"
cp main/f_*.png "$raw/"
"$py" "$stage/sidebyside_approved_size.py" A B "$raw" 300 713
"$py" "$kit/layout/xfade.py" "$stage" "$raw"
"$blender" -b neck.blend --python-exit-code 1 -P "$kit/blender/labelpos.py" -- "$stage"
"$py" -I "$kit/layout/labels2d.py" "$stage" "$raw" "$labels"
"$py" "$kit/layout/compose.py" "$stage"
"$py" "$stage/assemble_approved.py" "$stage" "$labels/f_%04d.png" final_hq_v3.mp4
"$py" "$stage/sheet.py" "$stage/final_hq_v3.mp4" "$stage/crops_final"
