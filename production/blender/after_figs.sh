#!/bin/bash
# Wait for the figure-shot queue (PID given) to finish, then re-render the CCTV shot.
cd "$(dirname "$0")"
while kill -0 "$1" 2>/dev/null; do sleep 30; done
exec ./render_queue.sh SH15
