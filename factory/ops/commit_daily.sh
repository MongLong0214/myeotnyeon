#!/bin/bash
# Daily repo routine: stage code and docs, refuse media and big files, scan for secrets, commit.
#   factory/ops/commit_daily.sh [--dry-run] [--lf-toon] [extra paths for the work repo...]
# Stages ONLY factory-owned paths (FACTORY_PATHS below, tracked changes and new files) plus the extra paths named on the
# command line; other sessions' edits elsewhere in the tree are never swept up. Pass a shared library file you changed
# (e.g. episodes/quiz/batch_1107/b_format/render.cjs) explicitly. production/lf_toon (its own .git) is committed only
# with --lf-toon. .gitignore stays the allowlist. Secret values are never printed.
set -uo pipefail

WORK="$(cd "$(dirname "$0")/../.." && pwd)"
# Commit trailer for the running CTO session (the commitlore hook rejects a bare Claude-Session: trailer).
SESSION_LINE="${SESSION_LINE:-X-Claude-Session: https://claude.ai/code/session_01Ebod4g2WAyXZUEzY2Uat91}"
MAX_BYTES=$((5 * 1000 * 1000))
MEDIA_RE='\.(mp4|mov|mkv|webm|wav|mp3|m4a|aac|flac|ogg|png|jpe?g|webp|gif|psd|zip|npz|npy|pt|bin|onnx|safetensors|pdf)$'
DRY=0
LF=0
while [ "$#" -gt 0 ]; do
  case "$1" in --dry-run) DRY=1; shift ;; --lf-toon) LF=1; shift ;; *) break ;; esac
done

# Factory-owned paths (allowlist). Nothing outside them is staged unless named on the command line.
FACTORY_PATHS=(factory episodes/specs research/topic_radar upload/ledger.json)
WORK_ROOTS=("${FACTORY_PATHS[@]}" "$@")
WORK_EXCLUDES=(':(exclude,glob)**/cand/**' ':(exclude,glob)**/_bak/**' ':(exclude,glob)**/review_runs/**'
  ':(exclude,glob)**/__pycache__/**' ':(exclude,glob)upload/ledger_bak/**')

refuse_staged() {
  # Unstage media and files over the size limit; print path and reason only.
  local f size refused=0
  while IFS= read -r -d '' f; do
    [ -f "$f" ] || continue
    size=$(stat -f %z "$f" 2>/dev/null || stat -c %s "$f")
    if printf '%s' "$f" | grep -qiE "$MEDIA_RE"; then
      git reset -q -- "$f"; echo "refused (media): $f"; refused=1
    elif [ "$size" -gt "$MAX_BYTES" ]; then
      git reset -q -- "$f"; echo "refused (>5MB): $f"; refused=1
    fi
  done < <(git diff --cached --name-only --diff-filter=AM -z)
  return 0
}

secret_scan() {
  # Patterns plus the values of every keychain item whose service starts with myeotnyeon.
  # Values are read into memory only; output names the rule or service, never the value.
  git diff --cached -U0 --no-color | python3 -c '
import json, re, subprocess, sys
added = "\n".join(l[1:] for l in sys.stdin.read().splitlines() if l.startswith("+") and not l.startswith("+++"))
rules = {
  "private-key": r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----",
  "provider-token": r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{30,}|xox[baprs]-[A-Za-z0-9-]{16,}|ya29\.[A-Za-z0-9_-]{20,}|1//0[A-Za-z0-9_-]{20,}|GOCSPX-[A-Za-z0-9_-]{10,})",
  "bearer": r"(?i)\bBearer\s+[A-Za-z0-9._~-]{16,}",
  "jwt": r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}",
  "assignment": r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_?KEY|TOKEN|SECRET|PASSWORD|COOKIE)[A-Z0-9_]*\s*[:=]\s*[\x22\x27]?[A-Za-z0-9/+_.-]{12,}",
}
hits = [k for k, r in rules.items() if re.search(r, added)]
dump = subprocess.run(["security", "dump-keychain"], capture_output=True, text=True).stdout
services = sorted(set(re.findall(r"\"svce\"<blob>=\"(myeotnyeon\.[^\"]+)\"", dump)))
for s in services:
    r = subprocess.run(["security", "find-generic-password", "-s", s, "-w"], capture_output=True, text=True)
    v = r.stdout.strip()
    vals = [v] if len(v) >= 8 else []
    try:
        def walk(o):
            if isinstance(o, dict): [walk(x) for x in o.values()]
            elif isinstance(o, list): [walk(x) for x in o]
            elif isinstance(o, str) and len(o) >= 12 and not o.startswith("http"): vals.append(o)
        walk(json.loads(v))
    except Exception:
        pass
    if any(x in added for x in vals):
        hits.append("keychain:" + s)
print("secret-scan: %d keychain services checked" % len(services), file=sys.stderr)
if hits:
    print("BLOCKED secret-scan: " + ", ".join(hits), file=sys.stderr); sys.exit(1)
'
}

commit_repo() {
  local dir="$1" label="$2"; shift 2
  cd "$dir" || return 1
  echo "== $label"
  [ "$#" -gt 0 ] && { git add -u -- "$@" 2>/dev/null; git add -- "$@" 2>/dev/null; }
  refuse_staged
  if git diff --cached --quiet; then echo "nothing to commit"; return 0; fi
  if ! secret_scan; then git reset -q; echo "unstaged everything in $label"; return 1; fi
  if [ -f repo_check.py ] && ! python3 repo_check.py check-staged >/dev/null 2>&1; then
    # The repo's own gate (also the pre-commit hook) rejects whole files; leave those unstaged, names only.
    python3 repo_check.py check-staged 2>/dev/null | python3 -c '
import json, subprocess, sys
t = sys.stdin.read(); d = json.loads(t[t.find("{"):])
for p, r in sorted(d.get("rejected", {}).items()):
    subprocess.run(["git", "reset", "-q", "--", p]); print("refused (repo_check %s): %s" % (",".join(r), p))'
    if ! python3 repo_check.py check-staged >/dev/null 2>&1; then echo "BLOCKED repo_check.py check-staged"; git reset -q; return 1; fi
    if git diff --cached --quiet; then echo "nothing to commit"; return 0; fi
  fi
  git diff --cached --shortstat
  if [ "$DRY" = 1 ]; then git reset -q; echo "dry run: unstaged"; return 0; fi
  local n; n=$(git diff --cached --name-only | wc -l | tr -d ' ')
  git commit -q -F - <<MSG && git log --oneline -1
daily $(date +%F) $label: ${n} files of code and docs

Staged by factory/ops/commit_daily.sh: tracked changes plus new files under its roots,
media and files over 5MB refused, staged diff secret-scanned.

$SESSION_LINE
MSG
}

rc=0
existing=()
for p in "${WORK_ROOTS[@]}"; do [ -e "$WORK/$p" ] && existing+=("$p"); done
# Package text markers of factory-built packages only (make_short.py writes build.json); the rest is media.
for b in "$WORK"/upload/pkg/*_B/build.json; do
  [ -e "$b" ] || continue
  d="${b%/build.json}"; d="${d#$WORK/}"
  for m in READY.txt CTO_PASS.txt meta.txt build.json shorts_checks.md; do [ -e "$WORK/$d/$m" ] && existing+=("$d/$m"); done
done
commit_repo "$WORK" work "${existing[@]}" "${WORK_EXCLUDES[@]}" || rc=1
if [ "$LF" = 1 ] && [ -d "$WORK/production/lf_toon/.git" ]; then
  commit_repo "$WORK/production/lf_toon" lf_toon . || rc=1
fi
exit $rc
