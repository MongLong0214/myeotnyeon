#!/bin/bash
# Exit status matters: run it as `out=$(./send.sh ...); rc=$?` (a trailing `| grep` hides exit 5).
# send.sh '<one line of JS>' [wait-seconds]. Aside closes a REPL session after 30 min idle (REPL_SESSION_IDLE_TTL_MS)
# and deletes its session dir. On "REPL session not found": recover ONCE via restart_all.sh (writes ./session_dir),
# re-stage REPL_STAGE="src dst ..." into <session_dir>/files/, and for channel commands switch to REPL_HANDLE and
# require #entity-name == REPL_CHANNEL_NAME (else exit 3, no re-send). Second loss -> exit 4. No keepalive.
W=$(cd "$(dirname "$0")" && pwd)
# raw JS SECS: send one line, then wait until the REPL prints its completion line ("[ok | Nms]" or "[error | Nms]")
# or "REPL session not found". Waits at least max(SECS, SEND_TIMEOUT=300) seconds. No completion line in time = UNKNOWN.
raw() {
  local L0 T i N; L0=$(wc -l < "$W/out.log"); T=${SEND_TIMEOUT:-300}; [ "${2:-0}" -gt "$T" ] 2>/dev/null && T=$2
  printf '%s\n' "$1" > "$W/in"
  for ((i = 0; i < T * 2; i++)); do
    N=$(sed 's/\x1b\[[0-9;]*m//g' "$W/out.log" | tail -n +$((L0 + 1)))
    if grep -qE '^(repl > )?\[(ok|error) \| [0-9]+ms\]|REPL session not found' <<<"$N"; then printf '%s\n' "$N"; return 0; fi
    sleep 0.5
  done
  printf '%s\n' "$N"; return 5
}
unknown() {
  echo "send.sh: RESULT UNKNOWN: no completion line within the timeout. The command may still be running or may have run." >&2
  echo "send.sh: check the remote state (channel video list / slot readback) before any retry; never re-send an upload blindly." >&2
  exit 5
}
OUT=$(raw "$1" "${2:-4}") || { printf '%s\n' "$OUT"; unknown; }
if [ -n "${REPL_NO_RECOVER:-}" ] || ! grep -q "REPL session not found" <<<"$OUT"; then
  printf '%s\n' "$OUT"; grep -qE '^(repl > )?\[error \| ' <<<"$OUT" && exit 2; exit 0; fi
echo "send.sh: REPL session not found; recovering once" >&2
REPL_NO_RECOVER=1 "$W/restart_all.sh" > "$W/restart.out" 2>&1
SD=$(cat "$W/session_dir" 2>/dev/null); [ -d "$SD/files" ] || { echo "send.sh: recovery failed" >&2; exit 4; }
grep -q '\./files/' <<<"$1" && [ -z "${REPL_STAGE:-}" ] && { echo "send.sh: ./files/ used but REPL_STAGE unset" >&2; exit 3; }
CMD=$1; WAIT=${2:-4}; set -- ${REPL_STAGE:-}
while [ $# -ge 2 ]; do cp "$1" "$SD/files/$2" || exit 3; shift 2; done
if grep -qE 'upM\(|up\(|setPrivate\(|studio\.youtube' <<<"$CMD" || [ -n "${REPL_CHANNEL_NAME:-}" ]; then
  [ -n "${REPL_HANDLE:-}" ] && [ -n "${REPL_CHANNEL_ID:-}" ] && [ -n "${REPL_CHANNEL_NAME:-}" ] || { echo "send.sh: need REPL_HANDLE/REPL_CHANNEL_ID/REPL_CHANNEL_NAME" >&2; exit 3; }
  # Identity = the Studio channel dashboard after an explicit goto: URL channel id AND #entity-name must both match.
  # Never read #entity-name on whatever page is open (on a video edit page it is the video title).
  CH=$(set -o pipefail; raw "var __ok = await switchTo(\"$REPL_HANDLE\"); await st.goto(\"https://studio.youtube.com/channel/$REPL_CHANNEL_ID\"); await new Promise(r=>setTimeout(r,8000)); console.log(\"RCH=\"+await st.evaluate(()=>((location.pathname.match(/^\\/channel\\/(UC[\\w-]{22})/)||[])[1]||'')+'|'+(document.querySelector('#entity-name')?.innerText?.trim()||'')))" 30 | sed -n 's/.*RCH=//p' | head -1) || unknown
  [ "$CH" = "$REPL_CHANNEL_ID|$REPL_CHANNEL_NAME" ] || { echo "send.sh: identity '$CH' != '$REPL_CHANNEL_ID|$REPL_CHANNEL_NAME'; not re-sending" >&2; exit 3; }
fi
OUT=$(raw "$CMD" "$WAIT") || { printf '%s\n' "$OUT"; unknown; }
printf '%s\n' "$OUT"
grep -q "REPL session not found" <<<"$OUT" && exit 4
grep -qE '^(repl > )?\[error \| ' <<<"$OUT" && exit 2; exit 0
