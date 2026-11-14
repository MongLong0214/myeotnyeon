#!/bin/bash
# After phone verification (2026-10-26): thumbnails + pins on #3–#6, then fixed #7 (replaces old #7 schedule) and #8–#10, one per day 19:00 KST.
cd /Users/isaac/projects/verdict-kr/work/upload
run() { ./aside_task.sh "$@" | grep -E "SESSION|DONE|NO_SESSION"; sed 's/\x1b\[[0-9;]*m//g' "$1.log" | grep -E "youtube.com/shorts|예약|썸네일|고정|자격|문제점|blocked|중단|한도" | tail -10; }
run n_thumbs_pins p_thumbs_pins.txt cover_q003.jpg cover_q004.jpg cover_q005.jpg cover_q006.jpg
run n_sched_q007 p_sched_q007.txt v3_q007.mp4 v3_q007_meta.txt cover_q007.jpg
sed 's/\x1b\[[0-9;]*m//g' n_sched_q007.log | grep -qE "예약 완료|예약했" || { echo "STOP: new #7 not scheduled — old #7 left in place"; exit 1; }
run n_unsched_old7 p_unsched_old7.txt
for q in q008 q009 q010; do
  run n_sched_$q p_sched_$q.txt v3_$q.mp4 v3_${q}_meta.txt cover_$q.jpg
  sed 's/\x1b\[[0-9;]*m//g' n_sched_$q.log | grep -qE "예약 완료|예약했" || { echo "STOP: $q not scheduled"; exit 1; }
done
echo CHAIN_OK
