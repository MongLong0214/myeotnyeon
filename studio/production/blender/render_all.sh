#!/bin/bash
# Render every shot in shotlist.json (or the ids given) to PNG, then encode an
# H.264 plate for the compositor. Logs per-shot wall time.
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
IDS="$@"
[ -z "$IDS" ] && IDS=$(python3 -c "import json;print(' '.join(json.load(open('shotlist.json')).keys()))")
for id in $IDS; do
  read kind n < <(python3 -c "import json;k,n=json.load(open('shotlist.json'))['$id'];print(k,n)")
  t=$(date +%s)
  rm -rf renders/$id; mkdir -p renders/$id
  $B -b -P shots.py -- $kind $n renders/$id > renders/$id.log 2>&1
  cnt=$(ls renders/$id/f_*.png 2>/dev/null | wc -l | tr -d ' ')
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i renders/$id/f_%04d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart ../compositor/public/plates/$id.mp4
  echo "$id $kind frames=$cnt/$n secs=$(( $(date +%s)-t ))" >> renders/render_times.log
done
echo ALL_DONE >> renders/render_times.log
