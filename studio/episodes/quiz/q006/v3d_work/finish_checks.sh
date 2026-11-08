#!/bin/zsh
set -eu
export TMPDIR="$PWD/episodes/quiz/q006/v3d_work/tmp"
export PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export MPLCONFIGDIR="$PWD/episodes/quiz/q006/v3d_work/cache"
node episodes/quiz/q006/v3d_work/render.cjs audit > episodes/quiz/q006/v3d_work/audit_full.log 2>&1
node episodes/quiz/q006/v3d_work/render.cjs strict > episodes/quiz/q006/v3d_work/strict_full.log 2>&1
node episodes/quiz/q006/v3d_work/render.cjs after > episodes/quiz/q006/v3d_work/after.log 2>&1
.venv/bin/python episodes/quiz/q006/v3d_work/asr.py > episodes/quiz/q006/asr_final_v3d.log 2>&1
.venv/bin/python episodes/quiz/q006/v3d_work/sheets.py
.venv/bin/python episodes/quiz/q006/v3d_work/measure.py > episodes/quiz/q006/v3d_work/measure.log 2>&1
production/compositor/node_modules/.bin/tsc --project production/compositor/tsconfig.json --noEmit > episodes/quiz/q006/typecheck_v3d.log 2>&1
ffmpeg -hide_banner -loglevel error -n -i upload/v3d_q006.mp4 -vf scale=720:1280 -c:v libx264 -crf 23 -preset medium -c:a copy -movflags +faststart upload/preview/v3d_q006_preview.mp4
ffprobe -v error -show_streams -show_format -of json upload/preview/v3d_q006_preview.mp4 > episodes/quiz/q006/v3d_work/preview_probe.json
