#!/bin/bash
# Worker: claims shots from shotlist.json via mkdir locks, renders and encodes them.
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
W=$1
mkdir -p renders/locks
for id in $(python3 -c "import json;print(' '.join(json.load(open('shotlist.json')).keys()))"); do
  [ -f ../compositor/public/plates/$id.mp4 ] && continue
  mkdir renders/locks/$id 2>/dev/null || continue
  read kind n < <(python3 -c "import json;k,n=json.load(open('shotlist.json'))['$id'];print(k,n)")
  t=$(date +%s)
  rm -rf renders/$id; mkdir -p renders/$id
  $B -b -P shots.py -- $kind $n renders/$id > renders/$id.log 2>&1
  cnt=$(ls renders/$id/f_*.png 2>/dev/null | wc -l | tr -d ' ')
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i renders/$id/f_%04d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart ../compositor/public/plates/$id.mp4
  echo "w$W $id $kind frames=$cnt/$n secs=$(( $(date +%s)-t ))" >> renders/render_times.log
done
echo "w$W DONE" >> renders/render_times.log
