"""Prefer a local asset, otherwise read it from the installed anatomy kit."""

import os
from pathlib import Path

KIT = Path(__file__).resolve().parent
SHARED = Path(
    os.environ.get("ANAT_SHARED_KIT", (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../anat_kit"))
)


def asset(name):
    local = KIT / name
    return str(local if local.is_file() else SHARED / name)
