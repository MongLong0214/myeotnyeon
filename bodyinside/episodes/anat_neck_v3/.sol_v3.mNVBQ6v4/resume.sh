#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
cd "$episode"
py=../../.venv/bin/python
blender=/Applications/Blender.app/Contents/MacOS/Blender
rset=../../anat_kit/blender/rset.py
while [[ "$(ps -p 23293 -o stat=)" =~ ^[[:space:]]*[^Z[:space:]] ]]; do sleep 12; done
case "$(ps -p 12025 -o command=)" in
  *"/render.py") kill -TERM 12025; kill -CONT 12025 ;;
esac
"$py" - "$stage" <<'PY'
from pathlib import Path
import re, sys
p=Path(sys.argv[1])
s=(p/'main_0000_0149_1.log').read_text()
rows=re.findall(r"([0-9:.]+)\s+render\s+\| Saved: .*?f_(\d{4})\.png", s)
if {int(row[1]) for row in rows} != set(range(150)) or 'Blender quit' not in s:
    sys.exit('Opening batch did not complete. Inspect its log before resuming.')
t=0
for x in rows[-1][0].split(':'):
    t=t*60+float(x)
print(f'main f0–149 ok, {t:.1f} s, {len(rows)} written. Recovered elapsed time from Blender log.', flush=True)
PY
"$blender" -b neck.blend1 --python-exit-code 1 -P "$rset" -f 3,65,100,150,210,275,299,714,720,800,829,843,878,920 -- "//${stage##*/}/probe/f_" --draft > "$stage/draft_probes.log" 2>&1
"$py" - "$stage" <<'PY'
from pathlib import Path
import sys
from PIL import Image
import numpy as np
stage=Path(sys.argv[1]); ep=stage.parent
for f in [3,65,100,150,210,275,299,714,720,800,829,843,878,920]:
    name=f'f_{f:04}.png'
    ref=ep/'frames_draft4_raw_xf_orig'/name
    if not ref.exists():
        ref=ep/'frames_draft4_raw'/name
    a,b=(np.array(Image.open(p).convert('RGBA'),dtype=float) for p in [ref,stage/'probe'/name])
    aa,bb=[v[:,:,:3]*v[:,:,3:4]/255 for v in [a,b]]
    print(f'Approved source f{f}: premultiplied RGB average pixel delta {np.abs(aa-bb).mean():.3f}',flush=True)
PY
exec "$py" -u "$stage/render_approved.py"
