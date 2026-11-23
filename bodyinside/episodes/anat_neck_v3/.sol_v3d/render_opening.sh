#!/bin/bash
set -euo pipefail
blender=/Applications/Blender.app/Contents/MacOS/Blender
stage="$PWD/.sol_v3d"
nice -n 15 "$blender" -b .sol_v3b.sBcZnIjT/neck_payoff_v3b.blend --python-exit-code 1 -P "$stage/prepare_opening.py" > "$stage/prepare_opening.log" 2>&1
for batch in 0:29 30:60; do
    start=${batch%:*}
    end=${batch#*:}
    output=$(mktemp -d "$stage/open_${start}_${end}.XXXXXXXX")
    nice -n 15 "$blender" -b "$stage/neck.blend" --python-exit-code 1 -s "$start" -e "$end" -P ../../anat_kit/blender/rset.py -a -- "//${output##*/}/f_" --final > "$output/render.log" 2>&1
    rg -q 'RSET final 64 100' "$output/render.log"
    [[ $(rg -c 'Saved:' "$output/render.log") == "$((end - start + 1))" ]]
    printf '%s\n' "$output" >> "$stage/open_batches.txt"
    printf 'Verified final render f%s–%s\n' "$start" "$end"
done
