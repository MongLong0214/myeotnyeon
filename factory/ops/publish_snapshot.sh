#!/bin/bash
# Publish the current HEAD tree to the public repo branch verdict-work as one snapshot commit on top of the previous
# snapshot. Local history is never pushed: early commits hold reporter contacts and article texts that were removed
# from the tree on 2026-11-14 (7c32f53). Author is the GitHub noreply address, not the local git email.
#   factory/ops/publish_snapshot.sh            # push
#   factory/ops/publish_snapshot.sh --dry-run  # build the commit, do not push
set -euo pipefail
cd "$(dirname "$0")/../.."
URL=https://github.com/MongLong0214/myeotnyeon.git
BR=verdict-work
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean: commit first" >&2; exit 1; }
.venv/bin/python repo_check.py check >/dev/null || { echo "repo_check failed" >&2; exit 1; }
LOGIN=$(gh api user -q .login); NR="$(gh api user -q .id)+$LOGIN@users.noreply.github.com"
PARENT=$(git ls-remote "$URL" "refs/heads/$BR" | cut -f1)
[ -n "$PARENT" ] && git fetch -q "$URL" "$BR"
TREE=$(git rev-parse 'HEAD^{tree}')
[ -n "$PARENT" ] && [ "$(git rev-parse "$PARENT^{tree}")" = "$TREE" ] && { echo "no change since last snapshot"; exit 0; }
MSG="verdict-kr work repo snapshot ($(git rev-parse --short HEAD), $(date +%F))

${SESSION_LINE:-X-Claude-Session: https://claude.ai/code/session_01Ebod4g2WAyXZUEzY2Uat91}"
C=$(GIT_AUTHOR_NAME=$LOGIN GIT_AUTHOR_EMAIL=$NR GIT_COMMITTER_NAME=$LOGIN GIT_COMMITTER_EMAIL=$NR \
    git commit-tree "$TREE" ${PARENT:+-p "$PARENT"} -m "$MSG")
echo "snapshot $C (parent ${PARENT:-none})"
[ "${1:-}" = "--dry-run" ] && exit 0
git push "$URL" "$C:refs/heads/$BR"
