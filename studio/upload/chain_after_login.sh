#!/bin/bash
cd upload
./aside_task.sh del_v3_12 p_delete_v3_12.txt | grep -E "SESSION|DONE|NO_SESSION"
sed 's/\x1b\[[0-9;]*m//g' del_v3_12.log | tail -c 1600
echo "=== chain_now"
./chain_now.sh
