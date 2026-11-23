#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
exec "${ANAT_PYTHON:-python3}" "$root/scripts/fetch_assets.py" "$@"
