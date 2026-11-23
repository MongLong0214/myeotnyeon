#!/bin/bash
mkdir -p "$(dirname "$0")/.cache"
# Resume after the base draft plates, or run this file directly on an idle render slot.
set -euo pipefail
cd "$(dirname "$0")/.."
cache=production/.cache
blender="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
python=../../.venv/bin/python
run_blender() {
    # Another local production may be using the render slot when a stage ends.
    /usr/bin/python3 - <<'PYWAIT'
from contextlib import closing
import os, re
import select
import subprocess

pattern=re.compile(r'^\s*(\d+)\s+'+re.escape(os.environ.get('BLENDER','/Applications/Blender.app/Contents/MacOS/Blender'))+r' (?:.* )?(?:-b|--background)(?: |$)')
while True:
    listing=subprocess.check_output(['ps','-axo','pid=,args='],text=True)
    jobs=[int(m[1]) for line in listing.splitlines() if (m:=pattern.search(line))]
    if not jobs:break
    with closing(select.kqueue()) as queue:
        notices=[select.kevent(pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ONESHOT,fflags=select.KQ_NOTE_EXIT) for pid in jobs]
        try:queue.control(notices,1,50)
        except ProcessLookupError:pass
PYWAIT
    nice -n 10 "$blender" -b --factory-startup rootcanal.blend --python-exit-code 1 "$@"
}
case "${1:-draft}" in
    draft)
        if ! "$python" -c 'from pathlib import Path; import sys; sys.exit(not all((Path("production/.cache/draft")/f"{i:04}.jpg").is_file() for i in range(930)))'; then
            DRAFT=1 run_blender -P production/render.py >> "$cache/render-draft.log" 2>&1
        fi
        DRAFT=1 SECTION_REVEAL=1 run_blender -P production/tracks.py -P production/contact.py -P production/render.py > "$cache/draft-reveal.log" 2>&1
        "$python" -c 'import json; assert json.load(open("penetration_report.json"))["ok"]'
        nice -n 10 "$python" production/compose.py draft
        nice -n 10 "$python" production/check_edit.py draft
        "$python" production/report.py
        ;;
    final)
        test -s "$cache/draft-verification.json"
        DRAFT=0 FRAMES=0,1,2,200,388,554,784,929 run_blender -P production/tracks.py -P production/render.py >> "$cache/final-look.log" 2>&1
        DRAFT=0 run_blender -P production/render.py >> "$cache/render-final.log" 2>&1
        DRAFT=0 SECTION_REVEAL=1 run_blender -P production/render.py >> "$cache/final-reveal.log" 2>&1
        nice -n 10 "$python" production/compose.py final
        nice -n 10 "$python" production/check_edit.py final
        "$python" production/report.py
        ;;
    *) exit 2 ;;
esac
