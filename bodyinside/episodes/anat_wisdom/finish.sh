#!/bin/zsh
# after render: assemble final10.mp4, sheet.png, compare.png
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT/episodes/anat_wisdom"
./assemble.sh frames10/f_%04d.png final10.mp4
ffmpeg -v error -y -i final10.mp4 -vf "fps=1,scale=270:480,tile=10x1" -frames:v 1 -update 1 sheet.png
i=0
for t in 1.0 2.4 4.2 6.8 8.0 9.4; do ffmpeg -v error -y -ss $t -i final10.mp4 -frames:v 1 -vf scale=360:640 cmp/us_$i.png; i=$((i+1)); done
ins=(); fl=""; k=0
for j in 0 1 2 3 4 5; do for s in r1 r2 us; do ins+=(-i cmp/${s}_$j.png); fl="$fl[$k]"; k=$((k+1)); done; done
lay=$(python3 -c "print('|'.join(f'{c*360}_{r*640}' for r in range(6) for c in range(3)))")
ffmpeg -v error -y $ins -filter_complex "${fl}xstack=inputs=18:layout=${lay},scale=810:2160" -frames:v 1 -update 1 compare.png
echo finished
