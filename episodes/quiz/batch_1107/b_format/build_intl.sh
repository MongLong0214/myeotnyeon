#!/bin/zsh
# en/ja B3 build after synth: pace -> subtitle cues -> lip -> render -> mix -> cues.md -> sheets -> srt -> gate (background-safe)
# usage: build_intl.sh <qid> [stills f1,f2,...]   (stills mode stops after the stills)
set -e
cd "$(dirname $0)"; q=$1; W=/Users/isaac/projects/verdict-kr/work; K=$W/research/tts_kokoro/.venv/bin/python; V=$W/.venv/bin/python; P=$W/upload/pkg/${q}_B
$K pace.py $q 2>&1 | grep -E "RETAKE|DONE" | cut -c1-160
$K b3post.py $q 2>&1 | grep "B3 cues"; (( ${pipestatus[1]} == 0 )) || exit 1
python3 look/v2/lipdata.py $q >/dev/null && python3 lip_case.py $q >/dev/null
if [[ "$2" == stills ]]; then B3_BUNDLE=bundle_$q node render.cjs $q stills $3 | tail -1; exit 0; fi
B3_BUNDLE=bundle_$q node render.cjs $q video > /private/tmp/claude-501/render_$q.log 2>&1 || { echo "RENDER FAILED $q"; tail -3 /private/tmp/claude-501/render_$q.log; exit 1; }; grep -E "DONE" /private/tmp/claude-501/render_$q.log
B3_BUNDLE=bundle_$q node render.cjs $q cover 2>&1 | tail -1
$V mix.py $q | tail -1
$V cues.py $q > /dev/null; python3 cues_pops.py $q
rm -rf $P/sheets; $V sheets.py $P/video.mp4 $P/sheets | tail -1
$V -c "
import json
P='$P/';c=json.load(open(P+'case.json'))
def ts(x):h=int(x//3600);m=int(x%3600//60);s=x%60;return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}'
open(P+'subs.srt','w').write('\n'.join(f\"{i}\n{ts(s['start_s'])} --> {ts(s['end_s'])}\n{s['text']}\n\" for i,s in enumerate(c['subtitles'],1)))"
$V measure_b3.py $P/video.mp4 | tee $P/measure.json
rm -rf $P/gate; (cd $W && $V factory/qa/gate.py $P/video.mp4 --srt $P/subs.srt --format shorts --lang ${q:0:2} --thumbnail $P/cover.jpg --out $P/gate > $P/gate.log 2>&1; true)
grep "^|" $P/gate.log | grep -vc "| PASS" | xargs echo "gate non-pass rows (incl header 2):"
