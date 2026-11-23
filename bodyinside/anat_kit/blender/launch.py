#!/usr/bin/env python3
"""Serialize this kit's background Blender processes on the shared workstation."""
import fcntl
import os
import sys

with open(f"/tmp/verdict-anat-blender-{os.getuid()}.lock", "a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    os.set_inheritable(lock.fileno(), True)
    binary = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
    os.execv("/usr/bin/nice", ["nice", "-n", "15", binary, *sys.argv[1:]])
