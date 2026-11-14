#!/bin/zsh
# usage: look/compare2.sh <name> <frameIdx> — v1-look (LOOK1) vs v2-look (LOOK2): side PNG, 2 s strip, review sheets
set -e
R=${0:A:h}/../../../lookdev/_render2; C=${0:A:h}/../../../lookdev/compare_v2; mkdir -p $C/review; T=$(mktemp -d)
n=$1; k=$2
ffmpeg -loglevel error -y -i $R/${n}_LOOK1.mp4 -i $R/${n}_LOOK2.mp4 -filter_complex "[0][1]hstack,scale=1440:-2" -c:v libx264 -crf 16 -pix_fmt yuv420p -r 30 $C/${n}_strip.mp4
ffmpeg -loglevel error -y -i $R/${n}_LOOK1.mp4 -vf "select=eq(n\,$k)" -frames:v 1 $T/a.png
ffmpeg -loglevel error -y -i $R/${n}_LOOK2.mp4 -vf "select=eq(n\,$k)" -frames:v 1 $T/b.png
ffmpeg -loglevel error -y -i $T/a.png -i $T/b.png -filter_complex "[0][1]hstack" -frames:v 1 $C/${n}_side.png
for s in 0 1 2; do a=$((s*20)); ffmpeg -loglevel error -y -i $R/${n}_LOOK2.mp4 -vf "select=between(n\,$a\,$((a+19))),scale=432:768,drawtext=text='%{n}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black,tile=5x4" -frames:v 1 $C/review/${n}_look_$s.png; done
rm -rf $T
