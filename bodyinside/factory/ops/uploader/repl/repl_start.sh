#!/bin/bash
# Start one persistent `aside repl` on the owner profile, fed through a FIFO. Prints the session dir.
# Files for setInputFiles must sit inside that session dir (Aside refuses paths outside it).
set -u
W=$(cd "$(dirname "$0")" && pwd); export PATH="$HOME/.local/bin:$PATH"
rm -f "$W/in"; mkfifo "$W/in"; : > "$W/out.log"
: "${ASIDE_BODYINSIDE_PROFILE:?set ASIDE_BODYINSIDE_PROFILE to the local Aside profile ID of the Body Inside identity}"
(tail -f "$W/in" | aside repl --profile "$ASIDE_BODYINSIDE_PROFILE" > "$W/out.log" 2>&1 &)
for i in $(seq 1 30); do grep -q '^sessionDir:' "$W/out.log" && break; sleep 0.5; done
SD=$(sed -n 's/^sessionDir: //p' "$W/out.log" | head -1)
[ -n "$SD" ] || { echo "repl_start.sh: Aside printed no sessionDir; see $W/out.log" >&2; exit 1; }
printf '%s\n' "$SD"
