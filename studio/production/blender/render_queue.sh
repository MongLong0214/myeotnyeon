#!/bin/bash
# Render the given shots one after another (params from shotlist2.json), then encode each plate
# at its exact frame count. Waits for any other render worker to finish first (GPU-bound: two
# concurrent renders are no faster than one).
# usage: render_queue.sh SH13 SH14 ...
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f "render_worker2" >/dev/null; do sleep 30; done
for id in "$@"; do
  read mod n step < <(python3 -c "import json;m,n,s=json.load(open('shotlist2.json'))['$id'];print(m,n,s)")
  t=$(date +%s); rm -rf renders2/$id; mkdir -p renders2/$id
  if [ "$mod" = "shots" ]; then
    kind=$(python3 -c "print({'SH05':'map','SH04':'ident'}['$id'])")
    $B --background --factory-startup --python-exit-code 1 --python shots.py -- $kind $n renders2/$id > renders2/$id.log 2>&1
  else
    $B --background --factory-startup --python-exit-code 1 --python shots2.py -- $id $n renders2/$id --step=$step > renders2/$id.log 2>&1
  fi
  rc=$?
  cnt=$(ls renders2/$id/f_*.png 2>/dev/null | wc -l | tr -d ' ')
  res=$(./encode_plate.sh $id $n $step 2>&1 | tail -1)
  echo "$id rc=$rc rendered=$cnt step=$step plate=$res secs=$(( $(date +%s)-t )) $(date +%H:%M)" >> renders2/render_times.log
done
echo "QUEUE DONE $* $(date)" >> renders2/render_times.log
