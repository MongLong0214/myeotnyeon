#!/bin/zsh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT/episodes/anat_wisdom"
tag=$1; shift
ins=(); fl=""; i=0
for f in "$@"; do ins+=(-i stills/${tag}_$(printf %04d $f).png); fl="$fl[$i]"; i=$((i+1)); done
n=$#
ffmpeg -v error -y $ins -filter_complex "${fl}xstack=inputs=${n}:layout=$(python3 -c "
n=$n;c=4;w=540;h=330
print('|'.join(f'{(i%c)*w}_{(i//c)*h}' for i in range(n)))"):fill=0x202830[s];[s]format=rgb24" -frames:v 1 -update 1 stills/${tag}_grid.png
