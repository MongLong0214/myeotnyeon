#!/bin/bash
# Render shots in shotlist2.json: PNG frames (optionally every 2nd frame), then encode a 30 fps plate.
# step 2 → motion-compensated interpolation (ffmpeg minterpolate, mci) back to 30 fps.
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
OUT=../compositor/public/plates
mkdir -p renders2/locks $OUT
for id in $(python3 -c "import json;print(' '.join(json.load(open('shotlist2.json')).keys()))"); do
  [ -f $OUT/$id.mp4 ] && continue
  mkdir renders2/locks/$id 2>/dev/null || continue
  read mod n step < <(python3 -c "import json;m,n,s=json.load(open('shotlist2.json'))['$id'];print(m,n,s)")
  t=$(date +%s); rm -rf renders2/$id; mkdir -p renders2/$id
  if [ "$mod" = "shots" ]; then kind=$(python3 -c "print({'SH05':'map'}['$id'])"); $B --background --factory-startup --python-exit-code 1 --python shots.py -- $kind $n renders2/$id > renders2/$id.log 2>&1
  else $B --background --factory-startup --python-exit-code 1 --python shots2.py -- $id $n renders2/$id --step=$step > renders2/$id.log 2>&1; fi
  rc=$?
  cnt=$(ls renders2/$id/f_*.png 2>/dev/null | wc -l | tr -d ' ')
  if [ "$step" = "2" ]; then
    # frames are f_0001, f_0003, ... → renumber to a contiguous 15 fps sequence, interpolate to 30
    mkdir -p renders2/$id/seq; i=1; for f in $(ls renders2/$id/f_*.png | sort); do ln -sf "$(pwd)/$f" renders2/$id/seq/s_$(printf %05d $i).png; i=$((i+1)); done
    ffmpeg -hide_banner -loglevel error -y -framerate 15 -i renders2/$id/seq/s_%05d.png -vf "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,trim=end_frame=$n,setpts=PTS-STARTPTS" -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart $OUT/$id.mp4
  else
    ffmpeg -hide_banner -loglevel error -y -framerate 30 -i renders2/$id/f_%04d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart $OUT/$id.mp4
  fi
  nf=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 $OUT/$id.mp4 2>/dev/null)
  echo "$id rc=$rc rendered=$cnt step=$step plate_frames=$nf/$n secs=$(( $(date +%s)-t ))" >> renders2/render_times.log
done
echo "DONE $(date)" >> renders2/render_times.log
