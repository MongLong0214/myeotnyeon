#!/bin/bash
# Short CCTV re-render (only the 170 frames the edit uses), encode, then the final master render.
set -e
cd "$(dirname "$0")"
rm -rf renders2/SH15; mkdir -p renders2/SH15
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python shots2.py -- SH15 170 renders2/SH15 --step=2 > renders2/SH15.log 2>&1
./encode_plate.sh SH15 170 2
echo "SH15 short re-render done $(date +%H:%M)" >> renders2/render_times.log
cd ../../episodes/EP001
./render_final.sh > render_final.log 2>&1
echo "FINAL DONE $(date +%H:%M)" >> ../../production/blender/renders2/render_times.log
