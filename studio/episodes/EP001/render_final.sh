#!/bin/bash
# v2 light cut: build render.json from edit.py, copy the mastered mix, render the master with
# Remotion, render the thumbnail, write render_manifest.json, run the v2 structural checks.
set -euo pipefail
cd "$(dirname "$0")"
EP=$(pwd)
COMP=$EP/../../production/compositor
PUB=$COMP/public
python3 edit.py
cp audio/mix_master.wav "$PUB/ep001/mix_master.wav"
python3 edit.py >/dev/null      # re-run so render.json points at the copied mix
# thumbnail background: B with both palms raised in the headlights (over-the-hood shot)
ffmpeg -hide_banner -loglevel error -y -i "$PUB/plates/L02_hood.mp4" -vf "select=eq(n\,150)" -frames:v 1 "$PUB/ep001/thumb_bg.png"
cd "$COMP"
npx remotion render src/index.ts EP001 "$EP/${1:-final}.mp4" --port=3124 --codec=h264 --crf=17 --pixel-format=yuv420p \
  --color-space=bt709 --audio-codec=aac --audio-bitrate=320k --concurrency=6 --log=info
npx remotion still src/index.ts THUMB "$EP/thumbnail.png" --port=3124 --log=error
cd "$EP"
python3 - <<'PY'
import json, hashlib, pathlib, subprocess, datetime
def h(p):
    p = pathlib.Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
comp = pathlib.Path('../../production/compositor')
blender = pathlib.Path('../../production/blender')
m = dict(rendered_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'), cut='v2-light',
         inputs={f: h(f) for f in ('script_text.json', 'script.json', 'timing.json', 'ledger.json', 'edit_fx.json', 'audio/mix_master.wav', str(comp / 'public/ep001/render.json'))},
         code={str(f): h(f) for f in (blender / 'world2.py', blender / 'shots2.py', blender / 'shots3.py', blender / 'people2.py', comp / 'src/Episode2.tsx',
                                     comp / 'src/components/gfx2.tsx', comp / 'src/components/gfx.tsx', pathlib.Path('../../production/audio/synth2.py'), pathlib.Path('edit.py'))},
         plates={p.name: h(p) for p in sorted((comp / 'public/plates').glob('*.mp4'))},
         outputs={f: h(f) for f in ('final.mp4', 'thumbnail.png', 'subtitles.ko.srt', 'subtitles.ko.vtt')},
         tools=dict(blender='5.2.3 LTS', remotion='4.0.538', ffmpeg=subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split('\n')[0]))
json.dump(m, open('render_manifest.json', 'w'), indent=1)
print('manifest written')
PY
python3 validate_v2.py --media "$EP/${1:-final}.mp4"
