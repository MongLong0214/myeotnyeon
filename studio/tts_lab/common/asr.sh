#!/bin/sh
# ASR runs in the existing work/.venv with the already-cached whisper model (read-only, offline).
cd "$(dirname "$0")/.." && env -u HF_HOME HF_HUB_OFFLINE=1 "$HOME/projects/verdict-kr/work/.venv/bin/python" common/asr.py "$@" 2>&1 | grep -v -i warn
