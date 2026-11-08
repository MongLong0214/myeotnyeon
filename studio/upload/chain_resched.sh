#!/bin/bash
cd upload
for q in ${QS:-q006 q007 q008}; do
  ./aside_task.sh resched_$q p_sched_$q.txt v3_$q.mp4 v3_${q}_meta.txt | grep -E "SESSION|DONE|NO_SESSION"
  sed 's/\x1b\[[0-9;]*m//g' resched_$q.log | grep -E "youtube.com/shorts|예약|썸네일|문제점|blocked|중단" | tail -5
  sed 's/\x1b\[[0-9;]*m//g' resched_$q.log | grep -qE "예약 완료|예약했|예약:" || { echo "STOP: $q not confirmed scheduled"; exit 1; }
done
./aside_task.sh unsched_old p_unsched_old.txt | grep -E "SESSION|DONE|NO_SESSION"
sed 's/\x1b\[[0-9;]*m//g' unsched_old.log | tail -c 1500
