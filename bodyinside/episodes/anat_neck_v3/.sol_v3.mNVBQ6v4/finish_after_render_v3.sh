#!/bin/bash
set -euo pipefail
stage="$(cd "$(dirname "$0")" && pwd)"
episode="$(dirname "$stage")"
work="$(cd "$episode/../.." && pwd)"
kit="$work/anat_kit"
py="$work/.venv/bin/python"
blender=/Applications/Blender.app/Contents/MacOS/Blender
cd "$stage"
while [[ "$(ps -p "$1" -o command=)" == *"/render_remaining_v3.py" ]]; do sleep 20; done
rg -q '^B f576–713 ok,' render_status.log
while pgrep -x Blender >/dev/null; do sleep 20; done
mkdir -p probe_restored
"$blender" -b opening_draft4.blend --python-exit-code 1 -P "$kit/blender/rset.py" -f 211,222,235,250,275,285,295,299 -- //probe_restored/f_ --draft > probe_restored.log 2>&1
"$py" - "$stage" <<'PY'
from PIL import Image
from pathlib import Path
import sys
import numpy as np
stage=Path(sys.argv[1])
def premultiplied(p):
    array=np.asarray(Image.open(p).convert('RGBA'),dtype=float)
    return array[:,:,:3] * array[:,:,3:4] / 255
rows=[]
for path in sorted((stage/'probe_restored').glob('f_*.png')):
    ref=stage.parent/'frames_draft4_raw'/path.name
    mean=float(np.abs(premultiplied(ref)-premultiplied(path)).mean())
    rows.append((path.name,mean))
    print(f'Restored draft camera {path.stem}: premultiplied RGB average pixel delta {mean:.4f}')
assert len(rows)==8 and max(row[1] for row in rows)<0.5, 'Restored camera requires inspection'
PY
printf '%s\n' 'main f211–299, approved camera' >> render_status.log
for attempt in 1 2 3; do
    while pgrep -x Blender >/dev/null; do sleep 20; done
    log="main_0211_0299_${attempt}.log"
    t0=$(date +%s)
    if "$blender" -b opening_draft4.blend --python-exit-code 1 -s 211 -e 299 -P "$kit/blender/rset.py" -a -- //main/f_ --final > "$log" 2>&1 &&
       rg -q 'RSET final 64 100' "$log" && [[ "$(rg -c 'Saved:' "$log")" == 89 ]]; then
        printf 'main f211–299 ok, %s s, 89 written.\n' "$(( $(date +%s) - t0 ))" >> render_status.log
        break
    fi
    printf 'main f211–299 failed, %s s, attempt %s.\n' "$(( $(date +%s) - t0 ))" "$attempt" >> render_status.log
    if [[ "$attempt" == 3 ]]; then exit 1; fi
done
"$py" inspect_render.py new > render_image_checks.log
bash compose_master.sh > compose_master.log 2>&1
"$py" "$kit/run.py" "$stage" final_hq_v3 --final --from gates > gate_run.log 2>&1
ffprobe -v error -show_entries stream=index,codec_name,codec_type,nb_frames,start_time,duration,r_frame_rate,width,height,sample_rate -of json final_hq_v3.mp4 > master_probe.json
ffmpeg -v error -i final_hq_v3.mp4 -map 0:a:0 -c:a copy -f streamhash -hash sha256 - > master_audio.sha256
ffmpeg -hide_banner -nostats -i final_hq_v3.mp4 -map 0:a:0 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2> master_loudness.log
shasum -a 256 final_hq_v3.mp4 > master.sha256
