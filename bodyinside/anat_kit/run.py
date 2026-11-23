"""Build, preflight, render and review a local episode. See RUNBOOK.md."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT / "gates"))
from PIL import Image
from thresholds import T
import checks
import media_checks
import shot_checks
import playback

BLENDER = str(KIT / "blender/launch.py")
PY = sys.executable
TTS = os.environ.get(
    "ANAT_TTS_PY",
    (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../research/tts_bakeoff/venvs/mlx/bin/python"),
)
STAGES = [
    "build",
    "render",
    "labelpos",
    "labels",
    "compose",
    "sfx",
    "narration",
    "assemble",
    "sheet",
    "gates",
]


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1))


def stamp(paths):
    digest = hashlib.sha256()
    for path in paths:
        with path.open("rb") as stream:
            while block := stream.read(1 << 20):
                digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("tag")
    mode = parser.add_mutually_exclusive_group()
    for flag in ("preflight", "draft", "final", "final-fast"):
        mode.add_argument("--" + flag, dest="mode", action="store_const", const=flag)
    mode.add_argument(
        "--regression-from",
        type=Path,
        metavar="CERTIFIED_MOVIE",
        help="recompose certified raw frames in a private episode and rerun final gates",
    )
    parser.set_defaults(mode="draft")
    parser.add_argument("--from", dest="start", choices=STAGES, default="build")
    parser.add_argument("--prev")
    parser.add_argument(
        "--confirmed",
        help="owner-confirmed passing draft tag for a high-resolution render",
    )
    args = parser.parse_args()
    reference = args.regression_from.resolve() if args.regression_from else None
    E = args.episode.resolve()
    os.chdir(E)
    lock = (E / ".runner.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("another render or review is running in this episode directory")
    env = dict(os.environ, ANAT_KIT=str(KIT), ANAT_EPISODE=str(E))
    tag = args.tag
    if not re.fullmatch(r"[\w-]+", tag):
        parser.error("invalid tag")
    gates = E / "gates"
    gates.mkdir(exist_ok=True)
    from improvement_log import capture_run
    import atexit

    atexit.register(capture_run, E, tag)
    ep = read("episode.json")
    from episode_template import prepare, validate, TEMPLATES
    from render_ranges import render

    template = validate(E, ep)
    frames = shot_checks.keyframes(ep)
    n = round(ep["duration"] * ep["fps"])
    pre = args.mode == "preflight"
    draft = args.mode == "draft" and reference is None
    scene = E / ep.get("scene", "neck.blend")
    script = (
        TEMPLATES
        / template
        / ("assets.lock.json" if template == "neck_v3" else "build.py")
    )
    movie = E / (tag + ".mp4")
    raw = E / ("frames_" + tag + "_raw")
    labels = E / ("frames_" + tag)
    errors = []

    def stage(s):
        return STAGES.index(s) >= STAGES.index(args.start)

    def run(cmd, log=None):
        cmd = [str(x) for x in cmd]
        start = time.monotonic()
        if log:
            with open(log, "w") as stream:
                res = subprocess.run(
                    cmd, env=env, stdout=stream, stderr=subprocess.STDOUT
                )
        else:
            res = subprocess.run(cmd, env=env)
        print(
            f"{time.monotonic() - start:.1f}s {Path(cmd[0]).name} {log or ''}",
            flush=True,
        )
        if res.returncode:
            raise RuntimeError(
                f"{' '.join(cmd[:7])} exited {res.returncode}; see {log}"
            )

    def blender(blend, py, *extra):
        return [BLENDER, "-b", blend, "--python-exit-code", "1", "-P", py, *extra]

    def gate(name, cmd, emitted=False):
        output = gates / f"{tag}_{name}.json"
        try:
            if emitted:
                output.unlink(missing_ok=True)
                run(cmd + (["--", output]), gates / f"{tag}_{name}.log")
            else:
                run(cmd, output)
            data = read(output)
            if data.get("ok", data.get("pass")) is not True:
                errors.append(name)
        except (OSError, ValueError, RuntimeError) as ex:
            errors.append(f"{name}: {ex}")

    def review(extra):
        result = subprocess.run(
            [PY, KIT / "gates/review_gate.py", E, tag, *extra], env=env
        )
        if result.returncode:
            errors.append("Opus review (see review JSON)")

    def signature():
        sources = [
            E / name
            for name in (
                "episode.json",
                "SOURCES.md",
                "ABOUT_BLOCK.txt",
                "assets.json",
                "scene_dump.json",
                "pose_dump.json",
            )
        ]
        settings = [
            KIT / name
            for name in (
                "blender/rset.py",
                "gates/thresholds.json",
                "defects.yaml",
                "rubric.md",
            )
        ]
        if (E / "bp3d_provenance.json").is_file():
            sources.append(E / "bp3d_provenance.json")
        sources.extend(
            E / f
            for f in (
                "REFERENCES.txt",
                "thresholds.json",
                "neck_A.blend",
                "neck_B.blend",
                "jaw_person.blend",
                "jaw_anatomy.blend",
            )
            if (E / f).is_file()
        )
        settings.extend(
            [
                KIT / "run.py",
                KIT / "episode_template.py",
                KIT / "render_ranges.py",
                KIT / "schema/episode.schema.json",
                KIT / "gates/anchors/examples.json",
            ]
        )
        for folder in ("gates", "layout", "blender"):
            settings.extend(sorted((KIT / folder).glob("*.py")))
        settings.append(KIT / "gates/anchors/build.py")
        if template == "neck_v3":
            settings.append(KIT / "astra_human/make_human.py")
            settings.extend(
                TEMPLATES / template / file
                for file in (
                    "posture_inputs.json",
                    "posture.py",
                    "cord.py",
                    "markers.py",
                    "skin.py",
                    "markers.json",
                )
            )
        return hashlib.sha256(
            (
                stamp([*sources, script, scene, *settings])
                + repr((env.get("RS_PCT"), env.get("RS_SPP")))
            ).encode()
        ).hexdigest()

    if not draft and not pre and reference is None:
        if not args.confirmed:
            parser.error("high resolution requires --confirmed PASSING_DRAFT_TAG")
        approved = read(gates / f"{args.confirmed}_submission.json")
        if (
            not approved["pass"]
            or approved["signature"] != signature()
            or approved["movie_sha256"] != stamp([E / (args.confirmed + ".mp4")])
        ):
            parser.error("confirmed draft or its inputs changed")
        playback_file = E / "playback.json"
        if not playback_file.is_file() or not playback.checked(
            read(playback_file), approved["movie_sha256"]
        ):
            parser.error(
                "record the owner listener, phone, listened=true and confirmed movie_sha256 in playback.json"
            )
    if not pre and movie.exists() and stage("assemble"):
        parser.error("this movie exists; use a new draft tag")
    prefile = gates / "preflight.json"
    if not pre and (
        not prefile.is_file()
        or not read(prefile)["pass"]
        or read(prefile)["signature"] != signature()
    ):
        parser.error("run --preflight on these scene and episode inputs first")
    if pre:
        # Invalidate previous approval even if the rebuild fails partway.
        save(prefile, {"pass": False})
        prepare(E, ep)
        if template == "wisdom":
            from episode_template import prepare_jaw

            cache = Path(
                env.get("ANAT_FRAME_CACHE", KIT.parent / ".astra-work/frame-cache")
            ).resolve()
            save(gates / "template_scene.json", {"key": prepare_jaw(E, cache)})
        if not scene.is_file():
            raise ValueError(f"build did not produce {scene}")
    if draft:
        if not re.fullmatch(r"draft0[1-5]", tag):
            parser.error("submit measured movies as draft01 through draft05")
        number = int(tag[5:])
        if number > 1:
            previous = f"draft{number - 1:02d}"
            if args.prev != previous or not (E / (previous + ".mp4")).is_file():
                parser.error(f"submit {previous} first and supply --prev {previous}")
    render_receipt = gates / f"{tag}_render.json"
    assembly_receipt = gates / f"{tag}_assembly.json"
    input_signature = signature()
    if not pre and not stage("render"):
        render_data = read(render_receipt) if render_receipt.is_file() else {}
        if (render_data.get("signature"), render_data.get("mode")) != (
            input_signature,
            args.mode,
        ):
            parser.error(
                "the existing render belongs to different or unverified inputs"
            )
    if not pre and not stage("assemble"):
        assembly_data = read(assembly_receipt) if assembly_receipt.is_file() else {}
        if (
            assembly_data.get("signature") != input_signature
            or not movie.is_file()
            or assembly_data.get("movie_sha256") != stamp([movie])
        ):
            parser.error("the assembled movie or its inputs changed before review")
    if reference:
        source = reference.parent
        if source == E or args.start != "build":
            parser.error(
                "replay needs a fresh episode directory and the complete gate run"
            )
        certified = read(source / "gates" / (reference.stem + "_submission.json"))
        audit = read(source / "gates/final_fable_audit.json")
        renders = read(source / "gates" / (reference.stem + "_render.json"))
        original = source / ("frames_" + reference.stem + "_raw")
        if (
            certified["pass"] is not True
            or audit["pass"] is not True
            or audit["tag"] != reference.stem
            or renders["mode"] not in ("final", "final-fast")
            or certified["signature"] != renders["signature"]
            or not stamp([reference])
            == certified["movie_sha256"]
            == audit["movie_sha256"]
            or stamp(sorted(original.glob("f_*.png"))) != renders["raw_sha256"]
        ):
            parser.error("certification or original render digest does not match")
        raw.symlink_to(original)
        save(
            render_receipt,
            dict(
                mode="regression",
                raw_sha256=renders["raw_sha256"],
                signature=input_signature,
                reference=certified["movie_sha256"],
            ),
        )
    elif pre or stage("render"):
        if raw.exists() and any(raw.iterdir()):
            parser.error(f"use a new tag, existing raw frames in {raw}")
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="." + tag + "-", dir=E) as tmp:
            rendered = Path(tmp) / "frames"
            receipt = render(
                ep,
                scene,
                frames if pre else range(n),
                "draft" if pre else args.mode,
                rendered,
                Path(
                    env.get("ANAT_FRAME_CACHE", KIT.parent / ".astra-work/frame-cache")
                ).resolve(),
                E / f"render_{tag}.log",
            )
            if raw.is_dir():  # Only a previous empty directory may be replaced.
                raw.rmdir()
            rendered.replace(raw)
        save(
            render_receipt,
            dict(
                receipt,
                mode=args.mode,
                signature=input_signature,
                raw_sha256=stamp(sorted(raw.glob("f_*.png"))),
            ),
        )
    if (
        not pre
        and draft
        and read(gates / f"{tag}_render.json")["seconds"] > T["draft_render_max_s"]
    ):
        errors.append("draft render exceeded 300 seconds")
    expected = frames if pre else range(n)
    if {p.name for p in raw.glob("f_*.png")} != {f"f_{f:04d}.png" for f in expected}:
        raise ValueError("raw frames differ from required frame set")
    if (
        not pre
        and not stage("render")
        and read(render_receipt).get("raw_sha256") != stamp(sorted(raw.glob("f_*.png")))
    ):
        parser.error("raw frames changed since render")
    if ep.get("procedure") == "molar_sectioning" and not ep.get(
        "geometry_gates", {}
    ).get("disjoint"):
        raise ValueError(
            "sectioning requires an every-frame tool/nerve intersection check"
        )
    if ep.get("geometry_gates"):
        spec = gates / f"{tag}_geometry_spec.json"
        geom = gates / f"{tag}_geometry.json"
        save(spec, ep["geometry_gates"])
        geom.unlink(missing_ok=True)
        run(
            blender(scene, KIT / "gates/geo_gate.py", "--", spec, geom),
            gates / f"{tag}_geometry.log",
        )
        if read(geom).get("pass") is not True:
            errors.append("geometry")
    schedule = gates / f"{tag}_frames.json"
    save(schedule, list(expected))
    if pre or stage("labelpos"):
        run(
            blender(
                scene,
                KIT / "blender/labelpos.py",
                "--",
                E,
                *([schedule] if pre else []),
            ),
            gates / f"{tag}_projection.log",
        )
    if pre or stage("labels"):
        run([PY, "-I", KIT / "layout/labels2d.py", E, raw, labels])
    if pre or stage("compose"):
        run([PY, KIT / "layout/compose.py", E])
    run([PY, KIT / "layout/make_description.py", E])
    gate("description", [PY, KIT / "gates/description_gate.py", E])
    gate("facts", [PY, KIT / "gates/facts_gate.py", E])
    gate("defects_meta", [PY, KIT / "gates/defects_meta.py"])
    gate("provenance", blender(scene, KIT / "gates/provenance_gate.py"), emitted=True)
    gate("penetration", blender(scene, KIT / "gates/penetration_gate.py"), emitted=True)
    measured = gates / f"{tag}_shot_evidence.json"
    run(
        blender(
            scene,
            KIT / "blender/shot_evidence.py",
            "--",
            E / "episode.json",
            schedule,
            measured,
        ),
        gates / f"{tag}_evidence.log",
    )
    visual = shot_checks.inspect(ep, expected, read(measured), raw)
    save(gates / f"{tag}_shots.json", visual)
    if not visual["ok"]:
        errors.append("shot visibility / landmarks / transition")
    if pre:
        stills = gates / (tag + "_stills")
        stills.mkdir(exist_ok=True)
        layout = ep["layout"]
        for f in frames:
            base = Image.open("comp/base.png").convert("RGBA")
            bg = Image.open("comp/band_bg.png").convert("RGBA")
            fg = Image.open(labels / f"f_{f:04d}.png").convert("RGBA")
            bg.alpha_composite(fg.resize(bg.size, Image.Resampling.LANCZOS))
            base.alpha_composite(bg, (0, layout["band_y"]))
            beat = next(
                i
                for i, b in enumerate(ep["beats"])
                if round(b["t0"] * ep["fps"]) <= f < round(b["t1"] * ep["fps"])
            )
            base.alpha_composite(Image.open(f"comp/cap_{beat}.png").convert("RGBA"))
            base.convert("RGB").resize((540, 960), Image.Resampling.LANCZOS).save(
                stills / f"f_{f:04d}.jpg", quality=90
            )
        tests = {
            fn.__name__: fn(ep)
            for fn in (
                checks.no_kg_on_screen,
                checks.text_size,
                checks.labels_anchored,
                checks.label_beat_alignment,
                checks.labels_clear_of_dots,
                checks.layout_uses_height,
                media_checks.on_screen_wording,
                media_checks.caption_evidence,
                media_checks.caption_reading_speed,
            )
        }
        if "label-pops-at-handoff" in shot_checks.recurring_preflight():
            from layout.note_layers import stable_notes

            tests["stable_notes"] = stable_notes(ep)
        tests["opening_event"] = checks.opening_event(raw)
        tests["subject_size"] = checks.subject_size(
            raw, step=1, allow=ep.get("subject_size_allow", [])
        )
        tests["no_speckle"] = media_checks.speckle_frames(raw, frames)
        if ep.get("payoff_frames"):
            tests["figure_reads_human"] = media_checks.figure_reads_human(
                labels, ep["payoff_frames"]
            )
        tests["establishing_person"] = checks.establishing_person(
            read("scene_dump.json")
        )
        tests["leaders_cross"] = checks.leaders_cross(ep, read("label_pos.json"))
        tests["safe_area"] = (
            all(
                x0 >= 16 and y0 >= 180 and x1 <= 1064 and y1 <= 1500
                for x0, y0, x1, y1 in read("comp/text_boxes.json")
            ),
            {},
        )
        poses, scene_values = read("pose_dump.json"), read("scene_dump.json")
        tests.update(checks.scene_timing(ep, poses, scene_values))
        tests["caption_truth"] = checks.caption_truth(
            ep, poses, scene_values, read("label_pos.json")
        )
        save(gates / f"{tag}_stills_checks.json", tests)
        errors.extend(k for k, v in tests.items() if not v[0])
        review(["--stills", str(stills), "--draft"])
        if signature() != input_signature:
            errors.append("scene or episode inputs changed during preflight")
        save(
            prefile,
            dict(
                tag=tag,
                signature=input_signature,
                errors=errors,
                **{"pass": not errors},
            ),
        )
    else:
        if draft and stage("sfx"):
            run([PY, KIT / "layout/sfx_earshot.py", E])
        if not ep.get("narration"):
            errors.append("missing Sohee narration")
        elif draft and stage("narration"):
            keep_stem = [] if stage("sfx") else ["--keep-sfx"]
            run(
                [TTS, KIT / "layout/narration.py", E, *keep_stem],
                E / f"narration_{tag}.log",
            )
        if stage("assemble"):
            pending = E / f".{tag}.assembling.mp4"
            run(
                [PY, KIT / "layout/assemble.py", E, labels / "f_%04d.png", pending]
                + (
                    ["--draft"]
                    if draft
                    else ["--audio-from", reference or E / (args.confirmed + ".mp4")]
                )
            )
            save(
                assembly_receipt,
                {"signature": input_signature, "movie_sha256": stamp([pending])},
            )
            pending.replace(movie)
        if stage("sheet"):
            run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    movie,
                    "-vf",
                    "fps=0.5,scale=216:384,tile=11x2",
                    "-frames:v",
                    "1",
                    E / f"sheet_{tag}.png",
                ]
            )
        layout = gates / "layout.json"
        if not layout.exists():
            save(
                layout,
                dict(
                    read(KIT / "gates/layout_default.json"),
                    assets_manifest="assets.json",
                    episode_json="episode.json",
                ),
            )
        gate(
            "gates",
            [PY, KIT / "gates/video_gates.py", movie, labels, layout]
            + (["--draft"] if draft else []),
        )
        if ep.get("payoff_frames") or any(
            label["kind"] == "gap" for label in ep.get("labels", [])
        ):
            run(
                blender(
                    scene, KIT / "gates/human_gate.py", "--", gates / "human_dump.json"
                ),
                gates / f"{tag}_human.log",
            )
        gate("checks", [PY, KIT / "gates/checks.py", "all", E, tag])
        gate("audio", [PY, KIT / "gates/audio_gate.py", E, movie])
        if ep.get("narration"):
            gate("narration", [PY, KIT / "gates/narration_gate.py", E, movie])
        gate(
            "credit_ui",
            [
                PY,
                KIT / "gates/credit_ui_check.py",
                movie,
                E,
                gates / f"{tag}_credit_ui.png",
            ],
        )
        dc = (
            [PY, KIT / "gates/draft_checks.py", E, tag]
            + ([args.prev] if args.prev else [])
            + ["--blend", scene]
        )
        if subprocess.run(dc, env=env).returncode:
            errors.append("draft media checks")
        review(["--draft"] if draft else [])
        if signature() != input_signature:
            errors.append("scene or episode inputs changed during review")
        submission_path = gates / (
            tag + ("_regression.json" if reference else "_submission.json")
        )
        submission = {
            "pass": not errors and (draft or reference is not None),
            "opus_pass": not errors,
            "errors": errors,
            "signature": input_signature,
            "movie_sha256": stamp([movie]),
        }
        save(submission_path, submission)
        if not draft and not reference and not errors:
            from final_audit import audit

            outcome = audit(E, tag)
            submission["fable"] = outcome
            if not outcome.get("pass"):
                errors.append("final Fable audit: " + outcome["status"])
            submission["pass"] = not errors
            save(submission_path, submission)
    capture_run(E, tag)
    atexit.unregister(capture_run)
    print(
        json.dumps(
            {"tag": tag, "errors": errors, "pass": not errors}, ensure_ascii=False
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
