#!/usr/bin/env python3
"""Automated strict review. usage: python fable_gate.py EPISODE_DIR TAG [--dry-run]
Builds the material (sheet + 12 full-frame stills + SOURCES.md + episode.json) and asks `claude -p --model fable` to apply anat_kit/rubric.md VERBATIM.
Writes EPISODE_DIR/gates/<TAG>_fable.json; exit 0 only if pass (final >= 9 and no P0). Fable only reviews: it never edits.
The builder logs the FIRST score of a locked file and the final score; no best-of re-scoring (see RUNBOOK 'Proof rules')."""
import sys, os, json, subprocess, re
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); E = os.path.abspath(sys.argv[1]); TAG = sys.argv[2]; dry = '--dry-run' in sys.argv
PY = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../.venv/bin/python'); ep = json.load(open(E + '/episode.json')); dur = ep['duration']
os.makedirs(E + '/gates/review', exist_ok=True); stills = []
for i in range(12):
    t = (i + 0.5) * dur / 12; out = f'{E}/gates/review/{TAG}_s{i:02d}_t{t:.1f}.png'
    if not dry: subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', f'{E}/{TAG}.mp4', '-frames:v', '1', out]); stills.append(out)
prompt = open(KIT + '/rubric.md').read() + f"""

## Material (read every file with the Read tool before scoring)
- sheet: {E}/sheet_{TAG}.png
- stills (full 1080x1920 frames at the listed seconds): {', '.join(stills)}
- facts: {E}/SOURCES.md ; shot list and captions: {E}/episode.json ; duration {dur} s, 30 fps
Frame numbers in your answer are video frames (t x 30). Answer with the JSON object only."""
if dry: print(prompt[:1500]); sys.exit(0)
r = subprocess.run(['claude', '-p', '--model', 'fable', '--allowedTools', 'Read', '--output-format', 'text', prompt], capture_output=True, text=True, timeout=1800)
m = re.search(r'\{.*\}', r.stdout, re.S); res = json.loads(m.group(0)) if m else {'error': r.stdout[-500:] + r.stderr[-300:], 'pass': False}
json.dump(res, open(f'{E}/gates/{TAG}_fable.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False)[:800]); sys.exit(0 if res.get('pass') else 1)
