"""Rebuild the original actor with the actual skin beneath the shirt."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import addon_utils
import bpy

source, dest = map(Path, sys.argv[sys.argv.index("--") + 1 :])
spec = importlib.util.spec_from_file_location("original_cast", source)
cast = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cast)
addon = "bl_ext.user_default.mpfb"
if addon not in bpy.context.preferences.addons:
    bpy.context.preferences.addons.new().module = addon
addon_utils.enable(addon, default_set=False)
from bl_ext.user_default.mpfb.services.humanservice import HumanService

fit = HumanService.add_mhclo_asset


def fit_over_skin(path, body, **options):
    garment = fit(path, body, **options)
    if Path(path).stem == "male_casualsuit06":
        body.modifiers.remove(body.modifiers["Delete.male_casualsuit06"])
    return garment


with patch.object(HumanService, "add_mhclo_asset", staticmethod(fit_over_skin)):
    _, body, _ = cast.make_cast()
cast.complexion(body)
body.data.name = "Intact shirt-covered skin"
body.data.materials.clear()
(dest / "skin_groups.json").write_text(json.dumps([g.name for g in body.vertex_groups]))
bpy.data.libraries.write(str(dest / "skin.blend"), {body.data})
