"""Drive the opening and payoff with the same sampled standing-phone performance."""
import os
import runpy
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(os.environ["ANAT_KIT"]) / "blender"))
import kit
import kit_astra
import kit_spine
from asset_paths import asset

# The archived builder imports these modules and loads its studio map from KIT.
kit.KIT = kit_spine.KIT = str(Path(asset("assets/studio_small_09_2k.exr")).parents[1])
# (Episode frame, captured action frame). The held pose is repeated without progression.
KEYS = ((0, 119), (57, 91), (828, 91), (869, 119), (923, 119))


def record(self, frame):
    for (start, first), (end, last) in zip(KEYS, KEYS[1:]):
        if frame <= end:
            sample = first + (last - first) * (frame - start) / (end - start)
            return self.A_pay[round(sample)]
    return self.A_pay[KEYS[-1][1]]


def retime(self):
    for ob in (self.rig, bpy.data.objects["Phone | animated contact frame"]):
        suffix = "" if ob == self.rig else " | handset"
        action = bpy.data.actions["Payoff | return to neutral" + suffix]
        animation = ob.animation_data
        for track in list(animation.nla_tracks):
            animation.nla_tracks.remove(track)
        animation.action = None
        strip = animation.nla_tracks.new().strips.new("Standing handset motion", 0, action)
        strip.frame_end = KEYS[-1][0] + 1
        strip.use_animated_time = True
        for frame, sample in KEYS:
            strip.strip_time = sample
            strip.keyframe_insert("strip_time", frame=frame)
        for curve in strip.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"


# The registered builder derives the anatomical chain, shoulder, dots and dumps from
# Astra.rec and the skin/handset from Astra.retime. Both must use the same capture.
kit_astra.Astra.rec = record
kit_astra.Astra.retime = retime
bpy.ops.file.make_paths_absolute()
bpy.context.preferences.filepaths.use_relative_paths = False
bpy.context.preferences.filepaths.save_version = 0
runpy.run_path(str(Path(bpy.data.filepath).with_name("build.py")), run_name="__main__")
bpy.ops.file.make_paths_absolute()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, relative_remap=False)
