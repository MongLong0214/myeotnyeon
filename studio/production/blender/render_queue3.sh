#!/bin/bash
# Render v3 shots (shots3.py, params from shotlist3.json) one after another and encode each plate
# at its exact frame count. Waits for the other render scripts first (GPU-bound).
# usage: render_queue3.sh L05_wheel L13_outro ...
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f "render_worker2|render_queue.sh" >/dev/null; do sleep 30; done
for id in "$@"; do
  read n step nofig < <(python3 -c "import json;n,s,nf=json.load(open('shotlist3.json'))['$id'];print(n,s,int(nf))")
  extra=""; [ "$nofig" = "1" ] && extra="--nofig"
  t=$(date +%s); rm -rf renders2/$id; mkdir -p renders2/$id
  $B --background --factory-startup --python-exit-code 1 --python shots3.py -- $id $n renders2/$id --step=$step $extra > renders2/$id.log 2>&1
  rc=$?
  cnt=$(ls renders2/$id/f_*.png 2>/dev/null | wc -l | tr -d ' ')
  res=$(./encode_plate.sh $id $n $step 2>&1 | tail -1)
  echo "$id rc=$rc rendered=$cnt step=$step plate=$res secs=$(( $(date +%s)-t )) $(date +%H:%M)" >> renders2/render_times.log
done
echo "QUEUE3 DONE $* $(date)" >> renders2/render_times.log
