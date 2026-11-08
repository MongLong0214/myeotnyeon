#!/bin/bash
# 2026-10-27: daily upload limit reset → schedule fixed #7 (replacing the old #7 schedule), then #8–#10. One episode per day at 19:00 KST.
cd upload
run() {  # $1 = name, $2 = prompt, rest = files
  ./aside_task.sh "$@" | grep -E "SESSION|DONE|NO_SESSION"
  sed 's/\x1b\[[0-9;]*m//g' "$1.log" | grep -E "youtube.com/shorts|예약|썸네일|문제점|blocked|중단|한도" | tail -6
}
run t_sched_q007 p_sched_q007.txt v3_q007.mp4 v3_q007_meta.txt cover_q007.jpg
sed 's/\x1b\[[0-9;]*m//g' t_sched_q007.log | grep -qE "예약 완료|예약했" || { echo "STOP: new #7 not scheduled — old #7 left in place"; exit 1; }
run t_unsched_old7 p_unsched_old7.txt
for q in q008 q009 q010; do
  run t_sched_$q p_sched_$q.txt v3_$q.mp4 v3_${q}_meta.txt cover_$q.jpg
  sed 's/\x1b\[[0-9;]*m//g' t_sched_$q.log | grep -qE "예약 완료|예약했" || { echo "STOP: $q not scheduled"; exit 1; }
done
echo CHAIN_OK
