#!/bin/bash
# Assemble render.json, render the 480 s master with Remotion, write render_manifest.json.
set -euo pipefail
cd "$(dirname "$0")"
EP=$(pwd)
COMP=$EP/../../production/compositor
python3 build_render.py
cd "$COMP"
npx remotion render src/index.ts EP001 "$EP/${1:-final}.mp4" --port=3124 --codec=h264 --crf=17 --pixel-format=yuv420p \
  --color-space=bt709 --audio-codec=aac --audio-bitrate=320k --concurrency=6 --log=info
npx remotion still src/index.ts THUMB "$EP/thumbnail.png" --port=3124 --log=error
cd "$EP"
python3 - <<'EOF'
import json, hashlib, pathlib, subprocess, datetime
ep = pathlib.Path('.')
def h(p):
    p = pathlib.Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
comp = pathlib.Path('../../production/compositor/public')
plates = {p.name: h(p) for p in sorted((comp / 'plates').glob('*.mp4'))}
m = dict(rendered_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
         inputs={f: h(f) for f in ('script.json', 'timing.json', 'ledger.json', 'audio/mix_master.wav', '../../production/compositor/public/ep001/render.json')},
         code={f: h(f) for f in ('../../production/blender/world2.py', '../../production/blender/shots2.py', '../../production/blender/people.py',
                                 '../../production/compositor/src/Episode.tsx', '../../production/compositor/src/components/gfx.tsx', '../../production/audio/synth.py')},
         plates=plates, outputs={f: h(f) for f in ('final.mp4', 'thumbnail.png', 'subtitles.ko.srt', 'subtitles.ko.vtt')},
         tools=dict(blender='5.2.3 LTS', remotion='4.0.538', ffmpeg=subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split('\n')[0]))
json.dump(m, open('render_manifest.json', 'w'), indent=1)
print('manifest written')
EOF
