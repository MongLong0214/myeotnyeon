#!/bin/zsh
# render + mix + loop check + cover + gate + delivery sheets for one episode. usage: finish.sh <id> [suffix e.g. _v2]
set -e
W=/Users/isaac/projects/verdict-kr/work; B=$W/episodes/beastclash; q=$1; S=${2:-}; P=$W/upload/pkg/${q}_B
cd $B
SUF=$S node render.cjs $q video 2>&1 | tail -1
$W/.venv/bin/python mix.py $q $S | tail -1
SUF=$S node render.cjs $q cover 2>&1 | tail -1
$W/.venv/bin/python check.py $P/video$S.mp4 stills/$q/rv$S
rm -rf $P/sheets$S; $W/.venv/bin/python $W/episodes/quiz/batch_1107/b_format/sheets.py $P/video$S.mp4 $P/sheets$S 60
cd $W; .venv/bin/python factory/qa/gate.py $P/video$S.mp4 --srt $P/subs.srt --out $P/gate$S --format shorts --lang en --voice $P/narration.wav --thumbnail $P/cover$S.jpg --max-cps 22 --line-max 28 --cue-rule per_word > $P/gate$S.log 2>&1 || true
python3 -c "
import json;g=json.load(open('$P/gate$S/gate.json'));print('overall',g['overall'])
for i in g['items']:
  if i['status']!='PASS': print(' ',i['status'],i['check'],str(i.get('summary',''))[:110])"
