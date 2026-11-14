#!/bin/zsh
# usage: look/compare.sh <name> <stillIndex>  — builds compare/<name>_side.png, <name>_strip.mp4, review sheets
set -e
R=${0:A:h}/../../../lookdev/_render; C=${0:A:h}/../../../lookdev/compare; mkdir -p $C/review
n=$1; k=${2:-30}
ffmpeg -loglevel error -y -i $R/${n}_BEFORE.mp4 -i $R/${n}_LOOK.mp4 -filter_complex "[0][1]hstack,scale=1440:-2" -c:v libx264 -crf 16 -pix_fmt yuv420p -r 30 $C/${n}_strip.mp4
ffmpeg -loglevel error -y -i $R/${n}_BEFORE.mp4 -i $R/${n}_LOOK.mp4 -filter_complex "[0]select=eq(n\,$k)[a];[1]select=eq(n\,$k)[b];[a][b]hstack" -frames:v 1 $C/${n}_side.png
# review sheets of the LOOK frames: 3 sheets x 20 frames (5x4), 432x768 tiles, frame number burned in
for s in 0 1 2; do a=$((s*20)); ffmpeg -loglevel error -y -i $R/${n}_LOOK.mp4 -vf "select=between(n\,$a\,$((a+19))),scale=432:768,drawtext=text='%{n}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black,tile=5x4" -frames:v 1 $C/review/${n}_look_$s.png; done
