"""Render missing frames for each scene, then compose the two-posture comparison."""

import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image

KIT = Path(__file__).resolve().parent


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ranges(frames):
    result = []
    for f in sorted(frames):
        if result and f == result[-1][1] + 1:
            result[-1][1] = f
        else:
            result.append([f, f])
    return result


def frame(f):
    return f"f_{f:04}.png"


def render_scene(scene, frames, mode, cache, work, log, samples=None):
    launch = [KIT / "blender/launch.py", "-b", scene, "--python-exit-code", "1"]
    env = dict(os.environ)
    if samples is not None:
        env["RS_SPP"] = str(max(samples, int(env.get("RS_SPP", 0))))

    def run(args):
        subprocess.run(
            launch + args, stdout=log, stderr=subprocess.STDOUT, env=env, check=True
        )

    deps = work / "external.json"
    run(["-P", KIT / "blender/render_inputs.py", "--", deps])
    inputs = json.loads(deps.read_text())
    inputs["paths"] = [(p, digest(Path(p))) for p in inputs["paths"]]
    inputs.update(
        scene=digest(scene),
        preset=digest(KIT / "blender/rset.py"),
        mode=mode,
        pct=env.get("RS_PCT"),
        spp=env.get("RS_SPP"),
    )
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    folder = cache / key
    folder.mkdir(parents=True, exist_ok=True)
    receipt = folder / "frames.json"
    with (folder / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = json.loads(receipt.read_text()) if receipt.exists() else {}
        missing = [
            f
            for f in sorted(frames)
            if not (folder / frame(f)).is_file()
            or previous.get(str(f)) != digest(folder / frame(f))
        ]
        # A fresh process per 180 frames avoids intermittent black blocks on Metal.
        for start in range(0, len(missing), 180):
            batch = missing[start : start + 180]
            selection = ",".join(
                str(a) if a == b else f"{a}..{b}" for a, b in ranges(batch)
            )
            run(
                [
                    "-P",
                    KIT / "blender/rset.py",
                    "-o",
                    work / "f_",
                    "-f",
                    selection,
                    "--",
                    "unused",
                    "--" + mode,
                ]
            )
            if digest(scene) != inputs["scene"] or any(
                digest(Path(p)) != sha for p, sha in inputs["paths"]
            ):
                raise ValueError(
                    "scene or external render assets changed during the batch"
                )
            for f in batch:
                path = work / frame(f)
                with Image.open(path) as image:
                    image.verify()
                previous[str(f)] = digest(path)
                shutil.move(path, folder / frame(f))
            pending = folder / "frames.tmp"
            pending.write_text(json.dumps(previous))
            pending.replace(receipt)
    return folder, {
        "scene": scene.name,
        "key": key,
        "rendered": ranges(missing),
        "reused": len(frames) - len(missing),
    }


def split(a, b):
    left = Image.open(a).convert("RGBA")
    right = Image.open(b).convert("RGBA")
    w, h = left.size
    right.paste(left.crop((0, 0, w // 2, h)), (0, 0))
    px = np.array(right)
    divider = px[int(h * 0.12) : int(h * 0.88), w // 2 - 1 : w // 2 + 1]
    divider[:, :, :3] = [170, 175, 185]
    divider[:, :, 3] = np.maximum(divider[:, :, 3], 70)
    return Image.fromarray(px)


def blend(hold, incoming, t):
    # Interpolate premultiplied RGBA to avoid dark fringes on the skin.
    arrays = []
    for path in [hold, incoming]:
        a = np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255
        a[:, :, :3] *= a[:, :, 3:4]
        arrays.append(a)
    a = arrays[0] * (1 - t) + arrays[1] * t
    a[:, :, :3] /= np.maximum(a[:, :, 3:4], 1e-6)
    return Image.fromarray(np.rint(np.clip(a, 0, 1) * 255).astype(np.uint8))


def render(ep, scene, selected, mode, out, cache, log_path):
    start = time.monotonic()
    wanted = set(selected)
    needed = set(wanted)
    for xf in ep.get("xfades", []):
        if any(xf["at"] <= f < xf["at"] + xf["n"] for f in wanted):
            needed.add(xf["hold"])
    compare = {f for f in needed if ep.get("template") == "neck_v3" and 300 <= f < 714}
    dissolve = set()
    if ep.get("dental_dissolve"):
        a, b = ep["dental_dissolve"]
        dissolve = {f for f in needed if a <= f <= b}
    receipts = []
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp, log_path.open("w") as log:
        work = Path(tmp)
        groups = {}
        for f in needed - compare - dissolve:
            floors = [
                v
                for a, b, v in ep.get("draft_sample_windows", [])
                if a <= f <= b and mode == "draft"
            ]
            groups.setdefault(max(floors, default=None), set()).add(f)
        for samples, group in groups.items():
            main, receipt = render_scene(scene, group, mode, cache, work, log, samples)
            receipts.append(receipt)
            for f in group:
                shutil.copyfile(main / frame(f), work / frame(f))
        if compare:
            halves = []
            for name in ["neck_A.blend", "neck_B.blend"]:
                half, receipt = render_scene(
                    scene.with_name(name), compare, mode, cache, work, log
                )
                halves.append(half)
                receipts.append(receipt)
            for f in compare:
                split(*(half / frame(f) for half in halves)).save(work / frame(f))
        if dissolve:
            layers = []
            for name in ("jaw_person.blend", "jaw_anatomy.blend"):
                layer, receipt = render_scene(
                    scene.with_name(name), dissolve, mode, cache, work, log
                )
                layers.append(layer)
                receipts.append(receipt)
            fade = json.loads(scene.with_name("scene_dump.json").read_text())[
                "HumanFade"
            ]
            for f in dissolve:
                blend(
                    layers[0] / frame(f), layers[1] / frame(f), 1 - fade[str(f)]
                ).save(work / frame(f))
        for f in wanted:
            xf = next(
                (
                    row
                    for row in ep.get("xfades", [])
                    if row["at"] <= f < row["at"] + row["n"]
                ),
                None,
            )
            if xf:
                t = (f - xf["at"]) / xf["n"]
                t = (
                    t + 1 / xf["n"]
                    if xf.get("ease") == "linear"
                    else t * t * (3 - 2 * t)
                )
                blend(work / frame(xf["hold"]), work / frame(f), t).save(out / frame(f))
            else:
                shutil.copyfile(work / frame(f), out / frame(f))
    return {
        "seconds": round(time.monotonic() - start, 2),
        "frames": len(wanted),
        "scenes": receipts,
    }
