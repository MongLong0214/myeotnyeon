#!/bin/zsh
# usage: stills.sh tag spp pct frames...
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT/episodes/anat_wisdom"
tag=$1; spp=$2; pct=$3; shift 3
args=(); for f in "$@"; do args+=(-f $f); done
/Applications/Blender.app/Contents/MacOS/Blender -b wisdom.blend -P rset.py $args -- //stills/${tag}_ $spp $pct 2>&1 | grep -E "Time:|Error|rror" | grep -v "^$" | tail -3
ins=(); fl=""; i=0
for f in "$@"; do ins+=(-i stills/${tag}_$(printf %04d $f).png); fl="$fl[$i]"; i=$((i+1)); done
cols=4; n=$#
ffmpeg -v error -y $ins -filter_complex "${fl}xstack=inputs=${n}:layout=$(python3 -c "
n=$n;c=$cols;w=540;h=330
print('|'.join(f'{(i%c)*w}_{(i//c)*h}' for i in range(n)))"):fill=0x202830[s];[s]format=rgb24" -frames:v 1 -update 1 stills/${tag}_grid.png
