#!/bin/zsh
# usage: assemble.sh FRAMES_PATTERN OUT.mp4   (frames: RGBA 1080x660 PNG, 30 fps, 300 frames)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT/episodes/anat_wisdom"
FR=$1; OUT=$2
# loudness: two-pass to -14 LUFS / -1.5 dBTP
J=$(ffmpeg -hide_banner -i audio/sfx10.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
mi=$(echo $J | python3 -c "import json,sys;print(json.load(sys.stdin)['input_i'])"); mtp=$(echo $J | python3 -c "import json,sys;print(json.load(sys.stdin)['input_tp'])")
mlra=$(echo $J | python3 -c "import json,sys;print(json.load(sys.stdin)['input_lra'])"); mth=$(echo $J | python3 -c "import json,sys;print(json.load(sys.stdin)['input_thresh'])")
ffmpeg -v error -y -i audio/sfx10.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:linear=true,aresample=48000 audio/sfx10_norm.wav
ffmpeg -v error -y -framerate 30 -loop 1 -i comp/base.png -framerate 30 -loop 1 -i comp/band_bg.png -framerate 30 -start_number 0 -i $FR \
  -framerate 30 -loop 1 -i comp/cap_0.png -framerate 30 -loop 1 -i comp/cap_1.png -framerate 30 -loop 1 -i comp/cap_2.png -framerate 30 -loop 1 -i comp/cap_3.png -i audio/sfx10_norm.wav \
  -filter_complex "\
[1][2]overlay=0:0:format=auto,eq=contrast=1.04:saturation=1.05[band];\
[0][band]overlay=0:520:shortest=1[v0];\
[v0][3]overlay=0:0:enable='between(t,0,2.99)'[v1];\
[v1][4]overlay=0:0:enable='between(t,3.0,5.89)'[v2];\
[v2][5]overlay=0:0:enable='between(t,5.9,8.19)'[v3];\
[v3][6]overlay=0:0:enable='between(t,8.2,10)',format=yuv420p[v]" \
  -map "[v]" -map 7:a -t 10 -r 30 -c:v libx264 -preset slow -crf 15 -profile:v high -c:a aac -b:a 192k -movflags +faststart $OUT
echo done $OUT
