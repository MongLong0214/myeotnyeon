#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
SOURCE=../cartoon_v6/n18_cartoon_v6fix2_360p.mp4
for kind in training court; do
  rm -rf "n18_${kind}_frames"; mkdir "n18_${kind}_frames"
  "$BLENDER" -b --factory-startup --python-exit-code 1 --python render_representative.py -- "$kind"
done
ffmpeg -y -framerate 15 -i n18_training_frames/frame_%04d.png -i "$SOURCE" -ss 42.133333 -t 21.066667 -map 0:v:0 -map 1:a:0 -filter:v "fps=30" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest n18_training_pack_collapse_direct.mp4
ffmpeg -y -framerate 15 -i n18_court_frames/frame_%04d.png -i "$SOURCE" -ss 169.033333 -t 15.666667 -map 0:v:0 -map 1:a:0 -filter:v "fps=30" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest n18_court_request_sentence_direct.mp4
