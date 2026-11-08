#!/bin/bash
# Re-encode a rendered shot to its plate at exactly N frames.
# usage: encode_plate.sh SHOT N STEP   (STEP 2 = every 2nd frame rendered → mci interpolation to 30 fps)
# The last source frame is cloned so interpolation never leaves the plate short of N frames.
set -euo pipefail
cd "$(dirname "$0")"
id=$1; n=$2; step=$3
OUT=../compositor/public/plates/$id.mp4
if [ "$step" = "2" ]; then
  rm -rf renders2/$id/seq; mkdir -p renders2/$id/seq; i=1
  for f in $(ls renders2/$id/f_*.png | sort); do ln -sf "$(pwd)/$f" renders2/$id/seq/s_$(printf %05d $i).png; i=$((i+1)); done
  ffmpeg -hide_banner -loglevel error -y -framerate 15 -i renders2/$id/seq/s_%05d.png \
    -vf "tpad=stop_mode=clone:stop=4,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,trim=end_frame=$n,setpts=PTS-STARTPTS" \
    -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart $OUT
else
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i renders2/$id/f_%04d.png \
    -vf "tpad=stop_mode=clone:stop=4,trim=end_frame=$n,setpts=PTS-STARTPTS" -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -movflags +faststart $OUT
fi
echo "$id $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 $OUT)/$n"
