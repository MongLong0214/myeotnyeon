"""Describe Blender's external inputs before reusing scene frames."""

import bpy
import json
import sys
from pathlib import Path

paths = sorted(set(bpy.utils.blend_paths(absolute=True, packed=False)))
Path(sys.argv[-1]).write_text(
    json.dumps(
        {
            "version": bpy.app.version_string,
            "build": bpy.app.build_hash.decode(),
            "paths": paths,
        }
    )
)
