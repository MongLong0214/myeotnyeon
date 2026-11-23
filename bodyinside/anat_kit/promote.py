"""Test a visual template revision against the two legacy masters and every subsequent certified final."""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

from improvement_log import ARCHIVE, KIT, digest, finding, locked, read, records, store
from label_style import apply_style, versions as template_versions

LEGACY = {
    "anat_neck_v3": (
        "neck_v3",
        "final_hq_v3",
        "11ee8d4637cc1158a4f762615fee9406c67d44fb6b085bdff8b6509a3d992f84",
    ),
    "anat_wisdom": (
        "wisdom",
        "main_draft4",
        "081d063d4f03c28569d50d9b555e97db11be6301624ce3f4195bd2b03d1db0ef",
    ),
}
PYTHON = sys.executable


def run(cmd, cwd, log):
    with log.open("w") as out:
        return subprocess.run(
            cmd, cwd=cwd, stdout=out, stderr=subprocess.STDOUT
        ).returncode


def compare(reference, candidate, dest):
    sys.path.insert(0, str(KIT / "gates"))
    from anchored_review import pages
    from gates.anchors.build import examples, write_sheet

    pair = [reference, candidate]
    random.SystemRandom().shuffle(pair)
    packet = dest / "comparison"
    packet.mkdir()
    for letter, movie in zip("AB", pair):
        part = packet / letter
        part.mkdir()
        pages(movie, part)
    anchors = []
    for i, row in enumerate(examples(exclude={digest(m) for m in pair})):
        sheet = f"anchor_{i}.jpg"
        write_sheet(row, packet / sheet)
        anchors.append([sheet, row["axes"]])
    schema = {
        "type": "object",
        "required": ["winner", "inspected_A_and_B", "evidence"],
        "properties": {
            "winner": {"enum": ["A", "B", "tie", "unavailable"]},
            "inspected_A_and_B": {"type": "boolean"},
            "evidence": {"type": "string", "minLength": 1},
        },
    }
    prompt = (
        "Read the sequence and layout sheets in A and B and the Fable anchors. Compare the two "
        "films for visual quality, including label handoffs. Cite frames and rank A, B or tie. "
        "If either film could not be inspected return unavailable and inspected_A_and_B=false. "
        "Ignore compression-only differences. Read each of these exact file names:\n"
        + "\n".join(str(p.relative_to(packet)) for p in sorted(packet.glob("*/*.jpg")))
        + "\nAnchor scores: "
        + json.dumps(anchors, ensure_ascii=False)
    )
    proc = subprocess.run(
        [
            "claude",
            "-p",
            "--model",
            "opus",
            "--tools",
            "Read",
            "--allowedTools",
            "Read",
            "--strict-mcp-config",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--json-schema",
            json.dumps(schema),
        ],
        input=prompt,
        cwd=packet,
        capture_output=True,
        text=True,
        timeout=900,
        check=True,
    )
    envelope = json.loads(proc.stdout)
    answer = envelope["structured_output"]
    if envelope.get("is_error") or not any(
        "opus" in m.lower() for m in envelope["modelUsage"]
    ):
        raise ValueError("missing Opus comparison")
    winner = answer["winner"]
    if (
        winner not in ("A", "B", "tie")
        or answer["inspected_A_and_B"] is not True
        or not answer["evidence"].strip()
    ):
        raise ValueError("incomplete comparison: " + answer["evidence"])
    return dict(
        answer,
        candidate="AB"[pair.index(candidate)],
        reference_sha256=digest(reference),
        candidate_sha256=digest(candidate),
        passed=winner in ("tie", "AB"[pair.index(candidate)]),
    )


def copy_inputs(source, destination, names):
    for name in names:
        path = source / name
        if path.is_file():
            shutil.copy2(path, destination / name)
        elif path.is_dir():
            shutil.copytree(path, destination / name)


def wisdom(source, dest):
    # Its archived, custom compositor owns the jaw-touch opening and sectioning sequence.
    # Give the historical entry points their original directory layout in a private tree.
    work = dest / "work"
    main = work / "episodes" / "anat_wisdom" / "main"
    main.mkdir(parents=True)
    for name in ("branding", "research", ".venv", "anat_kit"):
        (work / name).symlink_to(ARCHIVE.parent / name)
    reference_sha = LEGACY["anat_wisdom"][2]
    snapshot = Path(
        os.environ.get(
            "ANAT_WISDOM_CERTIFIED_INPUTS",
            KIT.parent / ".astra-work/certified" / reference_sha,
        )
    )
    original = snapshot if snapshot.is_dir() else source / "main"
    pinned = {
        "assemble.py": "f9d5160eae05557de73e9a13f50ee9eb22234e65db4bc3664d39485fd9df4def",
        "run_gates.py": "8294e7c11589628f913221be577e251829809af0790f6a7dcee4ef07cdfb062d",
        "episode.json": "b054471c779556a6f9d6ce3ae6b04e6a1cddde4a41e8dc817e6c5c9284929310",
        "gates/geometry.json": "89570a05d7d32c7978ac2e8ebf6b7bc2abc825e3b38e65395509ccc37f7e8d64",
        "jaw.blend": "e06f9ad72bdf2735dd431b778a30819783233d331a81d9781a2b633978df1f5a",
        "opening.blend": "1fcffe29e42842400bde40a3617cfa796116f386181a744c77b0d1531e5f3ca5",
    }
    for name, sha in pinned.items():
        if digest(original / name) != sha:
            raise ValueError(
                f"restore the certified wisdom draft 4 input {name} in {snapshot}"
            )
    copy_inputs(
        original,
        main,
        [
            "assemble.py",
            "run_gates.py",
            "episode.json",
            "anchors.json",
            "audio",
            "SOURCES.md",
            "REFERENCES.txt",
            "description.txt",
            "extraction_sources.md",
        ],
    )
    for name in (
        "frames_main_draft4",
        "frames_main_draft4_raw",
        "opening.blend",
        "jaw.blend",
    ):
        (main / name).symlink_to(original / name)
    (main / "gates").mkdir()
    shutil.copy2(original / "gates/geometry.json", main / "gates/geometry.json")
    script = main / "run_gates.py"
    script.write_text(
        script.read_text().replace(
            "/Applications/Blender.app/Contents/MacOS/Blender",
            str(KIT / "blender/launch.py"),
        )
    )
    # This legacy artwork predates the versioned label layer. Reassemble its
    # numbered band frames with that edition's original layout, captions and audio.
    assembler = main / "assemble.py"
    original_draw = (
        "        plate,b=band(f)\n"
        '        plate.save(raw/f"f_{f:04}.png",compress_level=1)\n'
        '        b.save(labels/f"f_{f:04}.png",compress_level=1)'
    )
    assembler.write_text(
        assembler.read_text().replace(
            original_draw, '        b=Image.open(labels/f"f_{f:04}.png")'
        )
    )
    if run([PYTHON, assembler, "4", "--draft"], main, dest / "render.log"):
        raise ValueError("wisdom main assembly failed")
    if digest(main.parent / "main_draft4.mp4") != reference_sha:
        raise ValueError("wisdom main assembly differs from the certified numbered cut")
    code = run([PYTHON, script, "4", "--draft"], main, dest / "gates.log")
    names = [
        "audio",
        "checks",
        "credit_ui",
        "description",
        "facts",
        "geometry",
        "narration",
        "provenance_jaw",
        "provenance_opening",
        "video",
    ]
    failed = []
    for name in names:
        p = main / f"gates/main_draft4_{name}.json"
        data = read(p) if p.exists() else {}
        if data.get("pass", data.get("ok")) is not True:
            failed.append(name)
    return main.parent / "main_draft4.mp4", failed + (["wisdom runner"] if code else [])


def composite(source, tag, reference, dest, style):
    epdir = dest / source.name
    epdir.mkdir()
    stages = [
        p.parent
        for p in source.glob(".*/master.sha256")
        if p.read_text().split()[0] == digest(reference)
    ]
    if len(stages) != 1:
        raise ValueError("missing or ambiguous master source directory")
    source = stages[0]
    gates = epdir / "gates"
    gates.mkdir()
    copy_inputs(
        source,
        epdir,
        [
            "episode.json",
            "comp",
            "label_pos.json",
            "pose_dump.json",
            "scene_dump.json",
            "audio",
            "thresholds.json",
            "assets.json",
            "SOURCES.md",
            "ABOUT_BLOCK.txt",
            "REFERENCES.txt",
            "description.txt",
            "bp3d_provenance.json",
            "plumb_draw.json",
        ],
    )
    for name in ("layout.json", "human_dump.json"):
        if (source / "gates" / name).exists():
            shutil.copy2(source / "gates" / name, gates / name)
    ep = apply_style(read(epdir / "episode.json"), style)
    (epdir / "episode.json").write_text(json.dumps(ep, ensure_ascii=False))
    raw = epdir / f"frames_{tag}_raw"
    raw.symlink_to(source / raw.name)
    frames = epdir / f"frames_{tag}"
    movie = epdir / f"{tag}.mp4"
    n = round(ep["fps"] * ep["duration"])
    if not all((raw / f"f_{i:04d}.png").is_file() for i in range(n)):
        raise ValueError("certified source frames missing")
    (epdir / "draft4.mp4").symlink_to(reference)
    assembly = [
        PYTHON,
        source / "assemble_crf6.py",
        epdir,
        frames / "f_%04d.png",
        movie,
    ]
    # The certified legacy renderer has different arrow and plumb semantics.
    # Reuse those approved plates; only note-only ranges use the revised compositor.
    label_input = epdir / "changed_raw"
    label_input.mkdir()
    frames.mkdir()
    for i in range(n):
        filename = f"f_{i:04d}.png"
        active = [l for l in ep["labels"] if l["f0"] <= i <= l["f1"]]
        if style and any(l["kind"] == "note" for l in active):
            if any(l["kind"] != "note" for l in active):
                raise ValueError(
                    f"legacy layers overlap at f{i}; replay the original mixed layer"
                )
            (label_input / filename).symlink_to(raw / filename)
        else:
            (frames / filename).symlink_to(source / frames.name / filename)
    if run(
        [PYTHON, "-I", KIT / "layout/labels2d.py", epdir, label_input, frames],
        epdir,
        dest / "labels.log",
    ):
        raise ValueError("label rendering failed")
    shutil.copy2(source / "plumb_draw.json", epdir / "plumb_draw.json")
    if run(assembly, epdir, dest / "render.log"):
        raise ValueError("assembly failed")
    g = KIT / "gates"
    # Legacy episodes used the installed kit for their original facts and delivery gates.
    original_gates = ARCHIVE.parent / "anat_kit/gates"
    scene = source / ep.get("scene", "neck.blend")
    checks = {
        "video": [PYTHON, g / "video_gates.py", movie, frames, gates / "layout.json"],
        "checks": [PYTHON, original_gates / "checks.py", "all", epdir, tag],
        "facts": [PYTHON, original_gates / "facts_gate.py", epdir],
        "description": [PYTHON, original_gates / "description_gate.py", epdir],
        "audio": [PYTHON, original_gates / "audio_gate.py", epdir, movie],
        "narration": [PYTHON, original_gates / "narration_gate.py", epdir, movie],
        "credit_ui": [
            PYTHON,
            original_gates / "credit_ui_check.py",
            movie,
            epdir,
            gates / "credit.png",
        ],
        "defects_meta": [PYTHON, g / "defects_meta.py"],
    }
    for name in ("penetration", "provenance"):
        checks[name] = [
            KIT / "blender/launch.py",
            "-b",
            scene,
            "--python-exit-code",
            "1",
            "-P",
            original_gates / (name + "_gate.py"),
            "--",
            gates / (name + ".json"),
        ]
    failed = []
    for name, cmd in checks.items():
        log = dest / (name + ".log")
        code = run(cmd, epdir, log)
        output = (
            gates / (name + ".json") if name in ("penetration", "provenance") else log
        )
        try:
            result = read(output)
        except (OSError, ValueError):
            result = {}
        if code or result.get("ok", result.get("pass")) is not True:
            reasons = [
                k
                for k, v in result.items()
                if isinstance(v, dict) and v.get("ok") is False
            ]
            failed.append(name + (" (" + ", ".join(reasons) + ")" if reasons else ""))
    if style.get("note_transition"):
        from layout.note_layers import stable_notes

        passed, detail = stable_notes(ep)
        (dest / "note_handoff.json").write_text(json.dumps(detail))
        if not passed:
            failed.append("stable_notes")
    return movie, failed


def replay_current(source, tag, reference, dest, style):
    """A subsequent certified episode retains its authored copy and frozen source declarations."""
    from label_style import versioned

    kit = dest / "anat_kit"
    shutil.copytree(KIT, kit, ignore=shutil.ignore_patterns("__pycache__"))
    epdir = dest / "episodes" / source.name
    epdir.mkdir(parents=True)
    names = [
        "episode.json",
        "REFERENCES.txt",
        "SOURCES.md",
        "ABOUT_BLOCK.txt",
        "assets.json",
        "thresholds.json",
    ]
    copy_inputs(source, epdir, names)
    ep = read(epdir / "episode.json")
    family = ep["template"]
    versions = template_versions()
    versions[family]["candidate"] = style
    (kit / "templates/versions.json").write_text(json.dumps(versions))
    if "template_version" not in ep:
        versioned(ep, "v1")
    ep["template_version"] = "candidate"
    apply_style(ep, style)
    (epdir / "episode.json").write_text(json.dumps(ep, ensure_ascii=False))
    # The isolated runner writes findings and final receipts only inside this replay.
    (dest / "factory").mkdir()
    copy_inputs(source, epdir, ["audio"])
    for cmd, stage in [
        (["pf01", "--preflight"], "pf01"),
        (["regression", "--regression-from", reference], "regression"),
    ]:
        if run([PYTHON, kit / "run.py", epdir, *cmd], epdir, dest / (stage + ".log")):
            if (
                stage == "pf01"
                or not (epdir / "gates/regression_regression.json").is_file()
            ):
                return None, [stage]
    candidate = epdir / "regression.mp4"
    receipt = read(epdir / "gates/regression_regression.json")
    if receipt.get("movie_sha256") != digest(candidate):
        return None, ["regression movie checksum mismatch"]
    return candidate, [] if receipt.get("pass") is True else (
        receipt.get("errors") or ["regression gates"]
    )


def references():
    refs = [
        (ARCHIVE / name, family, tag, sha, True)
        for name, (family, tag, sha) in LEGACY.items()
    ]
    from improve_calibration import audited

    for folder, a in audited():
        if a["pass"]:
            refs.append(
                (
                    folder,
                    read(folder / "episode.json")["template"],
                    a["tag"],
                    a["movie_sha256"],
                    False,
                )
            )
    return refs


def promote(template, style, output, defect):
    import yaml

    registry = {r["id"]: r for r in yaml.safe_load((KIT / "defects.yaml").read_text())}
    if defect not in registry:
        raise ValueError("unknown defect class")
    if style is None:
        entry = registry[defect]
        if entry.get("recurrence", {}).get("template_fix") != "required":
            raise ValueError("no template fix is due for this class")
        style = entry.get("template_patch", {}).get(template)
        if not style:
            raise ValueError("this class needs an authored visual fix")
    versions = template_versions()
    base = next(reversed(versions[template]))
    merged = dict(versions[template][base], **style)
    master = read(KIT / "templates" / template / "episode.json")
    before = json.dumps(master, sort_keys=True)
    apply_style(master, merged)
    if before == json.dumps(master, sort_keys=True):
        raise ValueError("settings do not apply to any artwork in this template")
    if set(merged.get("label_layout", {})) - {
        l["id"] for l in master.get("labels", []) if l["kind"] in ("note", "callout")
    }:
        raise ValueError("layout revision names an unknown note or callout")
    if merged == versions[template][base]:
        raise ValueError("candidate is identical to current version")
    output.mkdir(parents=True, exist_ok=False)
    reports = {}
    try:
        refs = references()
    except (OSError, ValueError, KeyError) as exc:
        refs = []
        reports["certified set"] = {"error": str(exc)}
    for folder, family, tag, sha, legacy in refs:
        key = str(folder / tag)
        dest = output / f"{folder.name}-{sha[:12]}"
        try:
            dest.mkdir()
            reference = folder / (tag + ".mp4")
            if digest(reference) != sha:
                raise ValueError("certified reference checksum mismatch")
            selected = (
                merged
                if family == template
                else versions[family][next(reversed(versions[family]))]
            )
            if legacy and family == "wisdom":
                movie, failed = wisdom(folder, dest)
            elif not legacy:
                movie, failed = replay_current(folder, tag, reference, dest, selected)
            else:
                movie, failed = composite(folder, tag, reference, dest, selected)
            reports[key] = dict(
                failed=failed,
                reference_sha256=sha,
                candidate_sha256=digest(movie) if movie else None,
            )
            if movie:
                reports[key]["comparison"] = compare(reference, movie, dest)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as ex:
            reports.setdefault(key, {})["error"] = str(ex)
    passed = bool(refs) and all(
        r.get("comparison", {}).get("passed") and not r.get("failed")
        for r in reports.values()
    )
    with locked():
        try:
            current = template_versions() == versions and refs == references()
        except (OSError, ValueError, KeyError):
            current = False
        if not current:
            passed = False
            reports["state"] = {
                "error": "template version or certified set changed during replay"
            }
        version = "v" + str(int(base[1:]) + 1)
        status = "promoted" if passed else "rejected"
        event = finding(
            template,
            "promotion",
            f"{status} {template} {base} → {version}",
            "info",
            "episode",
            str(output),
            status=status,
            candidate=style,
            style=merged,
            defect=defect,
            base=base,
            version=version,
            results=reports,
        )
        store([*records(), event])
    print(json.dumps(event, ensure_ascii=False, indent=2))
    return passed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("template", choices=["neck_v3", "wisdom"])
    ap.add_argument(
        "style",
        type=json.loads,
        nargs="?",
        help="defaults to the class's proposed template fix",
    )
    ap.add_argument("output", type=Path)
    ap.add_argument("--class-id", required=True)
    args = ap.parse_args()
    sys.exit(
        not promote(args.template, args.style, args.output.resolve(), args.class_id)
    )
