#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
work="$(cd "$episode/../.." && pwd)"
kit="$work/anat_kit"
py="$work/.venv/bin/python"
approved="$episode/.sol_v3.mNVBQ6v4"
cd "$stage"

rg -q '^Payoff f761–818 ok,' render_status.log
fin=frames_final_hq_v3b
mkdir -p payoff_labeled
cp payoff_label_pos.json label_pos.json
"$py" -I "$kit/layout/labels2d.py" "$stage" payoff payoff_labeled
cp "$approved/plumb_draw.json" plumb_draw.json
"$py" - "$kit" "$stage" <<'PY'
from pathlib import Path
import json
import os
import sys

kit, stage = map(Path, sys.argv[1:])
sys.path.insert(0, str(kit / 'gates'))
from checks import dead_time

for f in range(761, 819):
    name = f'f_{f:04}.png'
    for source_dir, target_dir in [('payoff', 'frames_final_hq_v3b_raw'),
                                   ('payoff_labeled', 'frames_final_hq_v3b')]:
        source = stage / source_dir / name
        target = stage / target_dir / name
        if not os.path.samefile(source, target):
            target.unlink()
            os.link(source, target)
episode = json.loads((stage/'episode.json').read_text())
result = dead_time(str(stage / 'frames_final_hq_v3b_raw'), episode)
print('Raw dead_time', result, flush=True)
assert result[0], result
PY
ln -sfn neck_payoff_v3b.blend neck.blend
"$py" "$approved/assemble_crf6.py" "$stage" "$fin/f_%04d.png" final_hq_v3b.mp4
"$py" "$kit/run.py" "$stage" final_hq_v3b --final --from gates
