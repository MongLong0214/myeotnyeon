#!/bin/zsh
# usage: run_variant.sh TAG MODE   (build -> draft render -> nospray -> label -> assemble -> gates)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT/episodes/anat_wisdom"
TAG=$1; MODE=$2; B=/Applications/Blender.app/Contents/MacOS/Blender; PY=$ROOT/.venv/bin/python
GUMMODE=$MODE $B -b --python-exit-code 1 -P build.py > build$TAG.log 2>&1 || { echo BUILD FAIL; exit 1; }
rm -rf frames_draft${TAG}_raw frames_draft${TAG} frames_draft${TAG}_nospray; mkdir frames_draft${TAG}_raw frames_draft${TAG}_nospray
$B -b wisdom.blend -P labelpos.py >/dev/null 2>&1
$B -b wisdom.blend -P ../../anat_kit/blender/rset.py -a -- //frames_draft${TAG}_raw/f_ --draft > render$TAG.log 2>&1
$B -b wisdom.blend -P ../../anat_kit/blender/rset.py -f 110 -f 125 -f 140 -- //frames_draft${TAG}_nospray/f_ --draft --hide=Chip,Mist >/dev/null 2>&1
$B -b wisdom.blend -P ../../anat_kit/gates/geo_gate.py -- gates/geo_spec_wisdom22.json 2>&1 | grep -a GATE_JSON | sed 's/GATE_JSON //' > gates/draft${TAG}_geo.json
cp wisdom.blend wisdom_draft${TAG}.blend
$PY -I label2d.py frames_draft${TAG}_raw frames_draft${TAG} >/dev/null
$PY ../../anat_kit/layout/assemble.py . "frames_draft${TAG}/f_%04d.png" draft${TAG}.mp4 >/dev/null 2>&1
ffmpeg -v error -y -i draft${TAG}.mp4 -vf "fps=1,scale=270:480,tile=10x1" -frames:v 1 -update 1 sheet_draft${TAG}.png
$PY ../../anat_kit/gates/video_gates.py draft${TAG}.mp4 frames_draft${TAG} gates/layout_wisdom13.json --draft > gates/draft${TAG}_gates.json 2>/dev/null; echo vg $?
$PY ../../anat_kit/gates/ab_gate.py frames_draft${TAG}_raw frames_draft${TAG}_nospray 0.55,0.05,0.95,0.45 4.0 110 125 140 > gates/draft${TAG}_spray_ab.json; echo ab $?
echo DONE $TAG
