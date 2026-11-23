#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
work="$(cd "$episode/../.." && pwd)"
kit="$work/anat_kit"
py="$work/.venv/bin/python"
approved="$episode/.sol_v3.mNVBQ6v4"
cd "$stage"

raw="$(mktemp -d fix_bands_raw.XXXXXXXX)"
fin=frames_final_hq_v3b
mkdir -p "$fin" "${fin}_raw" gates
for name in episode.json thresholds.json label_pos.json assets.json pose_dump.json scene_dump.json SOURCES.md REFERENCES.txt ABOUT_BLOCK.txt; do
    cp "$approved/$name" "$name"
done
cp "$approved/description.txt" description.txt
cp "$approved/gates/layout.json" gates/layout.json
ln -sfn ../draft4.mp4 draft4.mp4
ln -sfn ../audio audio
ln -sfn ../neck.blend1 neck.blend
ln -sfn ../.sol_v3.mNVBQ6v4/comp comp

"$py" "$approved/sidebyside_approved_size.py" A B "$raw" 301 713
# The existing crossfades retain their timing and use untouched input frames from the prior render.
for f in 0299 0300 0714 0715 0716 0717 0718 0719 0720 0721 0722 0723 0724 0725; do
    cp "$approved/frames_final_hq_v3_raw_xf_orig/f_$f.png" "$raw/"
done
"$py" "$kit/layout/xfade.py" "$stage" "$raw"
mv "$raw/f_0299.png" hold_0299.png
"$py" -I "$kit/layout/labels2d.py" "$stage" "$raw" "$fin"
cp "$approved/plumb_draw.json" plumb_draw.json

"$py" - "$approved" "$raw" "$fin" <<'PY'
from pathlib import Path
import os
import sys

approved, staged_raw, out = map(Path, sys.argv[1:])
raw_out = out.with_name(out.name + "_raw")
n = 924
for frame in range(n):
    name = f'f_{frame:04}.png'
    affected = 300 <= frame <= 725
    src = (staged_raw if affected else approved / 'frames_final_hq_v3_raw') / name
    dst = raw_out / name
    if dst.exists() and not os.path.samefile(src, dst):
        dst.unlink()
    if not dst.exists():
        os.link(src, dst)
    if not affected:
        src, dst = approved / 'frames_final_hq_v3' / name, out / name
        if not dst.exists():
            os.link(src, dst)
        else:
            assert os.path.samefile(src, dst), name
    else:
        assert (out / name).is_file(), name
frame_names = [f'f_{frame:04}.png' for frame in range(n)]
assert sorted(p.name for p in out.glob('f_*.png')) == frame_names
assert sorted(p.name for p in raw_out.glob('f_*.png')) == frame_names
PY

"$py" "$approved/assemble_crf6.py" "$stage" "$fin/f_%04d.png" final_hq_v3b.mp4
"$py" "$kit/run.py" "$stage" final_hq_v3b --final --from gates
