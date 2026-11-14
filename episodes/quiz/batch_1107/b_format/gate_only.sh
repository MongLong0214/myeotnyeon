#!/bin/zsh
W=/Users/isaac/projects/verdict-kr/work; P=$W/upload/pkg/${1}_B; rm -rf $P/gate
cd $W && .venv/bin/python factory/qa/gate.py $P/video.mp4 --srt $P/subs.srt --format shorts --lang ${1:0:2} --thumbnail $P/cover.jpg --out $P/gate > $P/gate.log 2>&1; grep "^|" $P/gate.log | grep -v "| PASS" | cut -c1-150
