"""Initialize a new episode and validate the fields Sonnet can author."""

import argparse
import copy
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

from render_ranges import KIT, digest
from label_style import versioned

TEMPLATES = KIT / "templates"
NAMES = ("neck_v3", "wisdom")
SIDECARS = ["REFERENCES.txt", "SOURCES.md", "ABOUT_BLOCK.txt", "assets.json"]


def read(path):
    return json.loads(path.read_text())


def frozen_view(ep):
    ep = copy.deepcopy(ep)
    for k in ("title", "id"):
        ep.pop(k)
    for b in ep["beats"]:
        b.pop("cap")
    for row in ep["narration"]:
        row.pop("text")
    for label in ep["labels"]:
        # The diagram retains its actual landmarks, values, scale and timing.
        if label["kind"] == "callout":
            label.pop("text")
            label.pop("dx")
            label.pop("dy")
    return ep


def validate(folder, ep):
    schema = read(KIT / "schema/episode.schema.json")
    Draft202012Validator(schema).validate(ep)
    name = ep.get("template")
    if name not in NAMES:
        raise ValueError("new episodes require a registered neck_v3 or wisdom template")
    master = TEMPLATES / name
    base = read(master / "episode.json")
    if "template_version" in ep:
        versioned(base, ep["template_version"])
    if ep["id"] != folder.name:
        raise ValueError("episode id must match its directory")
    if frozen_view(ep) != frozen_view(base):
        raise ValueError(
            "shot, study condition, geometry or evidence differs from the template"
        )
    text_fields = [*ep["title"], *(row["text"] for row in ep["narration"])]
    for b in ep["beats"]:
        segments = b["cap"]
        if any(not isinstance(text, str) for text, _ in segments):
            raise ValueError("caption segments must contain text")
        text_fields.append("".join(text for text, _ in segments))
        for _, rgb in segments:
            if not isinstance(rgb, list) or len(rgb) != 3 or any(
                type(c) != int or not 0 <= c <= 255 for c in rgb
            ):
                raise ValueError("a caption needs RGB values between 0 and 255")
    for label in ep["labels"]:
        if label["kind"] != "callout":
            continue
        text_fields.append(label["text"])
        if any(
            type(label[k]) != int or abs(label[k]) > 1080 for k in ("dx", "dy")
        ):
            raise ValueError("invalid label offset in band pixels")
    if any(not isinstance(text, str) or not text.strip() for text in text_fields):
        raise ValueError("titles, captions, narration and callouts need visible text")
    for f in SIDECARS:
        if (folder / f).read_bytes() != (master / f).read_bytes():
            raise ValueError(f"unreviewed template source or attribution: {f}")
    return name


def prepare(folder, ep):
    name = validate(folder, ep)
    master = TEMPLATES / name
    if name == "neck_v3":
        assets = (
            Path(
                os.environ.get(
                    "ANAT_EPISODES", (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../episodes")
                )
            )
            / "anat_neck_v3"
        )
        locked = read(master / "assets.lock.json")
        if folder.name == "anat_neck_v3":
            pose, hashes = assets, locked
        else:
            pose, hashes = prepare_neck_pose(master, assets)
        for filename in ("pose_dump.json", "scene_dump.json"):
            copy_pinned(pose / filename, folder / filename, hashes[filename])
        scenes = {"neck.blend": (pose / "neck.blend", hashes["neck.blend"])}
        for filename in ("neck_A.blend", "neck_B.blend"):
            scenes[filename] = (assets / filename, locked[filename])
        clipped, clips = prepare_cord(master, scenes)
        for filename in ("neck_A.blend", "neck_B.blend"):
            copy_pinned(clipped / filename, folder / filename, clips[filename])
        prepare_markers(folder, master, clipped / "neck.blend", assets, locked)
    return name


def initialize(folder, name):
    folder = folder.resolve()
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("initialize an empty episode directory")
    folder.mkdir(parents=True, exist_ok=True)
    master = TEMPLATES / name
    for f in SIDECARS + ["episode.json"]:
        shutil.copyfile(master / f, folder / f)
    ep = versioned(read(folder / "episode.json"))
    ep["id"] = folder.name
    (folder / "episode.json").write_text(
        json.dumps(ep, ensure_ascii=False, indent=2) + "\n"
    )
    if name == "neck_v3" and folder.name == "anat_neck_v3":
        shutil.copyfile(master / "thresholds.json", folder / "thresholds.json")
    validate(folder, ep)


def copy_pinned(source, target, expected):
    if target.is_file() and digest(target) == expected:
        return
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        pending = Path(stream.name)
    try:
        shutil.copyfile(source, pending)
        if digest(pending) != expected:
            raise ValueError(f"source differs from locked {source.name}")
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)


def cache_root():
    return Path(
        os.environ.get("ANAT_FRAME_CACHE", KIT.parent / ".astra-work/frame-cache")
    ).resolve()


def build_pack(cache, inputs, outputs, build, settings=None):
    fingerprint = hashlib.sha256("".join(digest(p) for p in inputs).encode())
    if settings is not None:
        fingerprint.update(json.dumps(settings, sort_keys=True).encode())
    key = fingerprint.hexdigest()
    pack = cache / "templates" / key
    pack.mkdir(parents=True, exist_ok=True)
    with (pack / "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        receipt = pack / "files.json"
        hashes = read(receipt) if receipt.is_file() else {}
        if not all(
            (pack / f).is_file() and hashes.get(f) == digest(pack / f) for f in outputs
        ):
            with tempfile.TemporaryDirectory(dir=pack) as tmp:
                dest = Path(tmp)
                with (pack / "build.log").open("w") as log:
                    build(dest, log)
                hashes = {f: digest(dest / f) for f in outputs}
                for f in outputs:
                    (dest / f).replace(pack / f)
                (dest / "files.json").write_text(json.dumps(hashes))
                (dest / "files.json").replace(receipt)
    return pack, hashes


def install_build(folder, cache, inputs, outputs, build, settings=None):
    pack, hashes = build_pack(cache, inputs, outputs, build, settings)
    for name in outputs:
        copy_pinned(pack / name, folder / name, hashes[name])
    return pack.name


def prepare_neck_pose(master, archive):
    from asset_paths import asset

    locked = read(master / "posture_inputs.json")
    episode = read(master / "episode.json")
    settings = {key: episode[key] for key in ("fps", "duration", "render")}
    inputs = [
        master / "posture.py",
        master / "posture_inputs.json",
        KIT / "asset_paths.py",
        KIT / "blender/kit.py",
        KIT / "blender/kit_spine.py",
        KIT / "blender/kit_astra.py",
    ]
    inputs.extend(
        Path(asset(name))
        for name in (
            "astra_human/anchors.json",
            "astra_human/human_final.blend",
            "assets/studio_small_09_2k.exr",
            "assets/mocap/Texting While Standing.fbx",
            "assets/mocap/Looking Down.fbx",
        )
    )

    def build(dest, log):
        for name, sha in locked.items():
            copy_pinned(archive / name, dest / name, sha)
        (dest / "episode.json").write_text(json.dumps(settings))
        subprocess.run(
            [
                KIT / "blender/launch.py",
                "-b",
                dest / "neck_solids.blend",
                "--python-exit-code",
                "1",
                "-P",
                master / "posture.py",
            ],
            cwd=dest,
            env=dict(
                os.environ, ANAT_KIT=str(KIT), BUILD_OUT="neck.blend", BEAT_VARIANT=""
            ),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    return build_pack(
        cache_root(), inputs, ["neck.blend", "pose_dump.json", "scene_dump.json"], build, settings
    )


def prepare_cord(master, scenes):
    def clip(dest, log):
        source = dest / "inputs"
        source.mkdir()
        for name, (path, sha) in scenes.items():
            copy_pinned(path, source / name, sha)
        subprocess.run(
            [
                KIT / "blender/launch.py",
                "-b",
                "--factory-startup",
                "--python-exit-code",
                "1",
                "-P",
                master / "cord.py",
                "--",
                source,
                dest,
            ],
            cwd=dest,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    clip_inputs = [
        master / "cord.py",
        master / "assets.lock.json",
        *(path for path, _ in scenes.values()),
    ]
    return build_pack(cache_root(), clip_inputs, list(scenes), clip)


def prepare_markers(folder, master, clipped, archive, hashes):
    cast = KIT / "astra_human/make_human.py"
    root = Path(
        os.environ.get(
            "BP3D_ROOT",
            (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../research/anatomy3d/bodyparts3d_4.0"),
        )
    )
    obj_dir = root / "obj/isa_BP3D_4.0_obj_99"
    parts = {
        p["file"] + ".obj": p["sha256"] for p in read(master / "markers.json").values()
    }
    provenance = "bp3d_provenance.json"
    episode = read(master / "episode.json")
    settings = {
        "closing": episode["shots"][-2],
        "marker_start": min(l["f0"] for l in episode["labels"] if l["kind"] in ("gap", "plumb")),
    }

    def build_skin(dest, log):
        subprocess.run(
            [
                KIT / "blender/launch.py",
                "-b", "--factory-startup", "--python-exit-code", "1",
                "-P", master / "skin.py", "--", cast, dest,
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    skin, _ = build_pack(
        cache_root(), [cast, master / "skin.py"], ["skin.blend", "skin_groups.json"], build_skin
    )

    def build(dest, log):
        copy_pinned(archive / provenance, dest / provenance, hashes[provenance])
        (dest / "marker_settings.json").write_text(json.dumps(settings))
        for filename, sha in parts.items():
            copy_pinned(obj_dir / filename, dest / filename, sha)
        subprocess.run(
            [
                KIT / "blender/launch.py",
                "-b",
                clipped,
                "--python-exit-code",
                "1",
                "-P",
                master / "markers.py",
                "--",
                dest,
                dest,
                dest / "marker_settings.json",
                skin,
            ],
            env=dict(os.environ, ANAT_KIT=str(KIT)),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    inputs = [
        clipped,
        master / "markers.py",
        skin / "skin.blend",
        skin / "skin_groups.json",
        master / "markers.json",
        master / "assets.lock.json",
        KIT / "blender/kit.py",
        *(obj_dir / f for f in parts),
    ]
    return install_build(
        folder, cache_root(), inputs, ["neck.blend", provenance], build, settings
    )


def prepare_jaw(folder, cache):
    """Build the shared rig from the immutable recipe and install verified local copies."""
    import csv
    from asset_paths import asset

    master = TEMPLATES / "wisdom"
    db = Path(
        os.environ.get(
            "BP3D_ROOT",
            (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../research/anatomy3d/bodyparts3d_4.0"),
        )
    )
    index = db / "isa_element_parts.txt"
    inputs = [
        master / "build.py",
        master / "episode.json",
        KIT / "blender/kit.py",
        KIT / "blender/kit_astra.py",
        KIT / "asset_paths.py",
        index,
        Path(asset("astra_human/anchors.json")),
        Path(asset("astra_human/human_final.blend")),
        Path(asset("assets/studio_small_09_2k.exr")),
        Path(asset("assets/mocap/Texting While Standing.fbx")),
        Path(asset("assets/mocap/Looking Down.fbx")),
    ]
    with index.open() as stream:
        for _, name, file_id, *_ in csv.reader(stream, delimiter="\t"):
            if name in ("mandible", "gingiva of lower jaw") or (
                name.startswith(("left lower", "right lower"))
                and name.endswith("tooth")
            ):
                inputs.append(db / "obj/isa_BP3D_4.0_obj_99" / (file_id + ".obj"))
    files = [
        "jaw.blend",
        "jaw_person.blend",
        "jaw_anatomy.blend",
        "pose_dump.json",
        "scene_dump.json",
        "bp3d_provenance.json",
    ]

    def build(dest, log):
        shutil.copyfile(master / "episode.json", dest / "episode.json")
        subprocess.run(
            [
                KIT / "blender/launch.py",
                "-b",
                "--factory-startup",
                "--python-exit-code",
                "1",
                "-P",
                master / "build.py",
            ],
            cwd=dest,
            env=dict(os.environ, ANAT_EPISODE=str(dest), ANAT_KIT=str(KIT)),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

    return install_build(folder, cache, inputs, files, build)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", choices=NAMES)
    parser.add_argument("folder", type=Path)
    parser.add_argument(
        "--prime",
        action="store_true",
        help="build and render the shared draft frames before assigning a topic",
    )
    args = parser.parse_args()
    initialize(args.folder, args.template)
    if args.prime:
        import time
        from render_ranges import render

        started = time.monotonic()
        folder = args.folder.resolve()
        ep = read(folder / "episode.json")
        cache = Path(
            os.environ.get("ANAT_FRAME_CACHE", KIT.parent / ".astra-work/frame-cache")
        ).resolve()
        prepare(folder, ep)
        if args.template == "wisdom":
            prepare_jaw(folder, cache)
        with tempfile.TemporaryDirectory(dir=folder) as tmp:
            receipt = render(
                ep,
                folder / ep["scene"],
                range(round(ep["duration"] * ep["fps"])),
                "draft",
                Path(tmp) / "frames",
                cache,
                folder / "prime.log",
            )
            from sys import path

            path.insert(0, str(KIT / "gates"))
            from media_checks import speckle_frames

            receipt["speckle"] = speckle_frames(
                str(Path(tmp) / "frames"), range(receipt["frames"])
            )
        receipt["preparation_s"] = round(time.monotonic() - started, 2)
        (folder / "prime.json").write_text(json.dumps(receipt, indent=2))
        if not receipt["speckle"][0]:
            raise SystemExit("template draft failed the noise gate; see prime.json")
