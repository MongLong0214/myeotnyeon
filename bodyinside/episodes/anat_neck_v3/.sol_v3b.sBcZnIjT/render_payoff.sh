#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
work="$(cd "$episode/../.." && pwd)"
kit="$work/anat_kit"
py="$work/.venv/bin/python"
blender=/Applications/Blender.app/Contents/MacOS/Blender
cd "$episode"
nice -n 15 "$blender" -b neck.blend1 --python-exit-code 1 -P "$stage/prepare_payoff.py" > "$stage/prepare_payoff.log" 2>&1
mkdir -p "$stage/payoff"
for attempt in 1 2 3; do
    log="$stage/payoff_0761_0818_${attempt}.log"
    printf '%s\n' "Payoff f761–818 starting (attempt $attempt)" >> "$stage/render_status.log"
    t0=$(date +%s)
    if nice -n 15 "$blender" -b "$stage/neck_payoff_v3b.blend" --python-exit-code 1 -s 761 -e 818 -P "$kit/blender/rset.py" -a -- //payoff/f_ --final > "$log" 2>&1 &&
       rg -q 'RSET final 64 100' "$log" && [[ "$(rg -c 'Saved:' "$log")" == 58 ]]; then
        "$py" - "$stage/payoff" <<'PY'
from pathlib import Path
import sys
from PIL import Image
path = Path(sys.argv[1])
for f in range(761, 819):
    with Image.open(path / f'f_{f:04}.png') as image:
        assert image.size == (1080,880) and image.mode == 'RGBA'
        image.verify()
PY
        printf '%s\n' "Payoff f761–818 ok, $(( $(date +%s) - t0 )) s, 58 frames" >> "$stage/render_status.log"
        exit 0
    fi
    printf '%s\n' "Payoff f761–818 failed (attempt $attempt)" >> "$stage/render_status.log"
done
exit 1
