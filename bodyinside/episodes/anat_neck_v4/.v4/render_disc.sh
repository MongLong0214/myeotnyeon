#!/bin/bash
set -euo pipefail
stage="$PWD/.v4"
blender=/Applications/Blender.app/Contents/MacOS/Blender
nice -n 15 "$blender" -b ../anat_neck/neck.blend --python-exit-code 1 -P "$stage/prepare_disc.py" > "$stage/prepare_disc.log" 2>&1
mkdir -p "$stage/disc_frames"
for start in 0 64 128 192 256 320; do
    end=$((start + 63))
    if ((end > 336)); then end=336; fi
    output=$(mktemp -d "$stage/disc_${start}_${end}.XXXXXXXX")
    nice -n 15 "$blender" -b "$stage/disc.blend" --python-exit-code 1 -s "$start" -e "$end" -P ../../anat_kit/blender/rset.py -a -- "//${output##*/}/f_" --final > "$output/render.log" 2>&1
    rg -q 'RSET final 64 100' "$output/render.log"
    [[ $(rg -c 'Saved:' "$output/render.log") == "$((end - start + 1))" ]]
    ln "$output"/f_*.png "$stage/disc_frames/"
    printf 'Verified final render f%s–%s (%s)\n' "$start" "$end" "$output"
done
