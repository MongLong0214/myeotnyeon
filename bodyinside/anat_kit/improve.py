"""Capture one anatomy finding or run the nightly classify, escalate and calibrate loop."""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from improvement_log import (
    ARCHIVE,
    FACTORY,
    KIT,
    append,
    atomic,
    digest,
    finding,
    locked,
    read,
    records,
    store,
)

REGISTRY = KIT / "defects.yaml"
FIXTURES = KIT / "gates/fixtures"
FIXTURE_ARCHIVE = Path(
    os.environ.get("ANAT_FIXTURE_ARCHIVE", ARCHIVE.parent / "fixture_media/anat_kit")
)
STOP = set(
    "a an the at by in out over from of on or and with to as it is when this has too appears frame frames still shot shows visible the fix".split()
)


def words(s):
    return set(re.findall(r"[^\W\d_]{3,}", s.lower())) - STOP


def match(row, classes, known):
    if row.get("classes"):
        if any(c not in classes for c in row["classes"]):
            raise ValueError(f"unknown class for {row['ref']}: {row['classes']}")
        return row["classes"]
    description = row["description"].lower().strip()
    if description in known:
        return known[description]
    for key, entry in classes.items():
        if (
            key in description
            or entry.get("enforcement", {}).get("check") == description.split(" ", 1)[0]
        ):
            return [key]
        if any(phrase in description for phrase in entry.get("match", [])):
            return [key]
    description_words = words(description)
    overlaps = []
    for key, entry in classes.items():
        title = words(key)
        if len(title & description_words) >= 2 and title <= description_words:
            overlaps.append((len(title), key))
    if overlaps:
        return [max(overlaps)[1]]
    return []


def evidence(row, key, still_only=False, expected=None):
    """Cut the cited bad still, sequence or audio directly from its reviewed edition."""
    if not row.get("media"):
        return None
    src = ARCHIVE / row["media"]
    if row["media"].startswith(".astra-work/"):
        src = KIT.parent / row["media"]
    if not src.is_file() or (
        row.get("media_sha256") and digest(src) != row["media_sha256"]
    ):
        return None
    directory = FIXTURES / key
    directory.mkdir(exist_ok=True)
    loc = row["location"]
    frame = re.search(r"\bf(\d+)(?:\s*[-–]\s*f?(\d+))?", loc)
    seconds = re.search(r"(\d+(?:\.\d+)?)(?:\s*[-–]\s*(\d+(?:\.\d+)?))?\s*s\b", loc)
    sound = row.get("medium") == "audio" or re.search(
        r"audio|narration|speech|pronunciation", key
    )
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
            output = Path(tmp) / ("bad" + src.suffix.lower())
            shutil.copyfile(src, output)
        else:
            fps_text = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=r_frame_rate",
                    "-of",
                    "csv=p=0",
                    src,
                ],
                text=True,
            ).strip()
            fps = 1
            if fps_text:
                n, d = map(int, fps_text.split("/"))
                fps = n / d
            elif frame:
                spec = (
                    Path(row.get("folder") or ARCHIVE / row["episode"]) / "episode.json"
                )
                if not spec.is_file():
                    raise ValueError(
                        "an audio-only source needs timestamps or its episode frame rate"
                    )
                fps = read(spec)["fps"]
            start = (
                int(frame[1]) / fps if frame else float(seconds[1]) if seconds else 0
            )
            duration = (
                max(1 / fps, (int(frame[2]) - int(frame[1]) + 1) / fps)
                if frame and frame[2]
                else (
                    max(0.01, float(seconds[2]) - start)
                    if seconds and seconds[2]
                    else None
                )
            )
            cmd = ["ffmpeg", "-v", "error", "-nostdin"]
            if sound or not frame:
                cmd += ["-ss", f"{start:.8f}"]
            cmd += ["-i", src]
            trim = (
                f"trim=start_frame={frame[1]}"
                + (f":end_frame={int(frame[2]) + 1}" if frame[2] else "")
                + ",setpts=PTS-STARTPTS,"
                if frame
                else ""
            )
            if sound:
                output = Path(tmp) / "bad.flac"
                if duration or frame or seconds:
                    cmd += ["-t", str(max(duration or 2, 1))]
                cmd += ["-vn", "-ac", "1", "-ar", "16000"]
            elif not still_only and (duration or not (frame or seconds)):
                output = Path(tmp) / "bad.mp4"
                if duration:
                    cmd += ["-t", str(duration)]
                cmd += [
                    "-an",
                    "-vf",
                    trim + "scale=-2:min(480\\,ih)",
                    "-c:v",
                    "libx264",
                    "-crf",
                    "22",
                ]
            else:
                output = Path(tmp) / "bad.jpg"
                cmd += [
                    "-vf",
                    trim + "scale=-2:min(640\\,ih)",
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                ]
            subprocess.run(cmd + [output], check=True, capture_output=True)
        if not output.is_file() or not output.stat().st_size:
            raise ValueError(f"no evidence at {row['ref']} {loc}")
        if expected and digest(output) != expected:
            raise ValueError(
                "recovered fixture differs from the reviewed pixels or audio"
            )
        target = directory / output.name
        output.replace(target)
    return dict(
        file=str(target.relative_to(FIXTURES)),
        finding=row["id"],
        sha256=digest(target),
        source_sha256=row.get("media_sha256") or digest(src),
        location=loc,
    )


def classify(rows, classes):
    known = {
        r["description"].lower().strip(): r["classes"] for r in rows if r.get("classes")
    }
    for row in rows:
        if row.get("kind") in ("directive", "observation") or row["source"] not in (
            "owner",
            "ceo",
            "opus",
            "fable",
            "gate",
        ):
            continue
        ids = match(row, classes, known)
        if not ids:
            slug = (
                "-".join(re.findall(r"[^\W_]+", row["description"].lower())[:7])[
                    :65
                ].strip("-")
                or "finding"
            )
            key = f"{slug}-{row['id'][:6]}"
            classes[key] = dict(
                id=key,
                description=row["description"],
                sources=[row["ref"]],
                enforcement={"type": "unenforced"},
            )
            ids = [key]
        row["classes"] = known[row["description"].lower().strip()] = ids
    by_class = defaultdict(list)
    for row in rows:
        if row.get("kind") not in ("directive", "observation"):
            for key in row.get("classes", []):
                alias = classes[key].get("enforcement", {})
                by_class[alias.get("of", key)].append(row)
    return by_class


def escalate(groups, classes):
    for key, entry in classes.items():
        rows = groups.get(key, [])
        episodes = list(dict.fromkeys(r["episode"] for r in rows))
        if len(episodes) < 2:
            entry.pop("recurrence", None)
        if (
            "evidence" in entry
            and rows
            and entry["evidence"]["finding"] not in {r["id"] for r in rows}
        ):
            entry.pop("evidence")
        mode = entry["enforcement"]["type"]
        if sample := entry.get("evidence"):
            target = FIXTURES / sample["file"]
            if not target.is_file():
                archived = FIXTURE_ARCHIVE / sample["file"]
                target.parent.mkdir(parents=True, exist_ok=True)
                if archived.is_file() and digest(archived) == sample["sha256"]:
                    shutil.copyfile(archived, target)
                else:
                    source = next(
                        (r for r in rows if r["id"] == sample["finding"]), None
                    )
                    if source:
                        evidence(
                            source,
                            key,
                            still_only=target.suffix == ".jpg",
                            expected=sample["sha256"],
                        )
        if (
            mode == "unenforced" or len(episodes) >= 2 and mode == "review"
        ) and not entry.get("evidence"):
            located = sorted(
                rows,
                key=lambda r: (
                    not r.get("media"),
                    r["location"] == "episode",
                    not r.get("location", "").startswith("f"),
                ),
            )
            for r in located:
                try:
                    sample = evidence(r, key, still_only=mode == "review")
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    print(f"Pending fixture for {key}: {exc}", file=sys.stderr)
                    continue
                if sample:
                    entry["evidence"] = sample
                    break
        if len(episodes) >= 2:
            entry["recurrence"] = dict(
                episodes=episodes,
                preflight=entry["enforcement"].get("check") or "visual_review",
                template_fix="required" if len(episodes) >= 3 else "not due",
            )


def save_registry(original, classes):
    # Retain hand-written comments, citations, quoting and unrelated formatting.
    blocks = re.split(r"(?m)(?=^- id: )", original)
    existing = set()
    for i, block in enumerate(blocks[1:], 1):
        current = yaml.safe_load(block)[0]
        key = current["id"]
        existing.add(key)
        row = classes[key]
        if row == current:
            continue
        body = re.sub(
            r"(?ms)^  (recurrence|evidence):.*?(?=^  [^ \n]|^#|\Z)", "", block
        )
        extras = {k: row[k] for k in ("evidence", "recurrence") if k in row}
        insert = (
            "".join(
                "  " + line + "\n"
                for line in yaml.safe_dump(
                    extras, sort_keys=False, allow_unicode=True
                ).splitlines()
            )
            if extras
            else ""
        )
        head, sep, tail = body.partition("\n#")
        blocks[i] = head.rstrip() + "\n" + insert + (sep + tail if sep else "")
    new = [row for key, row in classes.items() if key not in existing]
    if new:
        blocks.append(
            yaml.safe_dump(new, allow_unicode=True, sort_keys=False, width=120)
        )
    atomic(REGISTRY, "".join(blocks))


def nightly():
    from improve_calibration import update
    from improve_metrics import ingest, experiment

    metric_error = ""
    try:
        subprocess.run(
            [
                sys.executable,
                KIT.parent / "channel/analytics/api_pull.py",
                "--anatomy-48h",
            ],
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as ex:
        metric_error = f" Pull pending ({ex})."
    try:
        append(ingest())
    except (OSError, ValueError, KeyError) as ex:
        metric_error += f" Join pending ({ex})."
    with locked():
        rows = records()
        original = REGISTRY.read_text()
        classes = {r["id"]: r for r in yaml.safe_load(original)}
        groups = classify(rows, classes)
        escalate(groups, classes)
        for r in rows:
            if r["source"] == "promotion" and r.get("defect") in classes:
                entry = classes[r["defect"]].get("recurrence")
                if entry is not None:
                    entry["last_promotion"] = {
                        "status": r["status"],
                        "finding": r["id"],
                        "template": r["episode"],
                    }
                    if r["status"] == "promoted":
                        entry["template_fix"] = r["episode"] + "/" + r["version"]
        save_registry(original, classes)
        store(rows)
        try:
            finals, correct, total, recalibrate = update()
            calibration = (
                f"{finals} final audits added to the historical anchors. Rolling agreement {correct}/{total}. "
                + (
                    "Recalibration required."
                    if recalibrate
                    else "At or above baseline."
                )
            )
        except (OSError, ValueError, KeyError) as ex:
            calibration = f"Calibration pending: {ex}".replace("\n", " ")

        pending = [
            r for r in classes.values() if r["enforcement"]["type"] == "unenforced"
        ]
        repeat = [r["recurrence"] for r in classes.values() if "recurrence" in r]
        promotions = [r for r in rows if r["source"] == "promotion"]
        metrics = [r for r in rows if r["source"] == "metric"]
        lines = [
            f"# Anatomy factory · {datetime.now().astimezone():%Y-%m-%d}",
            f"{len(rows)} records in findings.jsonl.",
            f"{len(groups)} defect classes observed across {len({r['episode'] for v in groups.values() for r in v})} episodes.",
            f"{len(pending)} unenforced classes. {sum(not (FIXTURES / r.get('evidence', {}).get('file', '')).is_file() for r in pending)} await reviewed media.",
            f"{len(repeat)} classes reached the second episode.",
            f"{sum(len(r['episodes']) >= 3 for r in repeat)} classes reached the template-fix step.",
            "Latest promotion decision — "
            + (promotions[-1]["description"] if promotions else "none."),
            calibration,
            f"{len(metrics)} published episode measurements." + metric_error,
            experiment(metrics),
        ]
        atomic(FACTORY / "IMPROVE_LOG.md", "\n".join(lines) + "\n")
    print("\n".join(lines))


def install():
    """Install this worktree's nightly job in the current macOS login session."""
    import plistlib

    label = "kr.verdict.anatomy-improve"
    domain = f"gui/{os.getuid()}"
    target = Path.home() / "Library/LaunchAgents" / (label + ".plist")
    target.parent.mkdir(parents=True, exist_ok=True)
    config = dict(
        Label=label,
        ProgramArguments=[sys.executable, str(KIT / "improve.py"), "nightly"],
        WorkingDirectory=str(KIT.parent),
        StartCalendarInterval=dict(Hour=2, Minute=15),
        Nice=15,
        EnvironmentVariables=dict(
            PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            PYTHONPATH=str(KIT.parent / ".astra-work/factory/deps"),
        ),
        StandardErrorPath=str(Path.home() / "Library/Logs/anatomy-improve.log"),
    )
    active = (
        subprocess.run(
            ["launchctl", "print", domain + "/" + label], capture_output=True
        ).returncode
        == 0
    )
    if target.exists() and plistlib.loads(target.read_bytes()) == config and active:
        print(f"Already installed at {target}")
        return
    atomic(target, plistlib.dumps(config).decode())
    if active:
        subprocess.run(["launchctl", "bootout", domain + "/" + label], check=True)
    subprocess.run(["launchctl", "bootstrap", domain, target], check=True)
    print(target)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="cmd", required=True)
    subs.add_parser("nightly")
    subs.add_parser("install")
    c = subs.add_parser("capture")
    c.add_argument("episode")
    c.add_argument("source", choices=["owner", "ceo", "opus", "fable", "gate"])
    c.add_argument("location", help="f123, f123-f130, 2.4-3.0s, or episode")
    c.add_argument("severity")
    c.add_argument("description")
    c.add_argument("--media", type=Path)
    c.add_argument("--audio", action="store_true")
    c.add_argument("--directive", action="store_true")
    c.add_argument("--class-id")
    a = p.parse_args()
    if a.cmd == "nightly":
        nightly()
    elif a.cmd == "install":
        install()
    else:
        extra = {}
        if a.directive:
            extra["kind"] = "directive"
        if a.media:
            extra.update(media=str(a.media.resolve()), media_sha256=digest(a.media))
        if a.class_id:
            if a.class_id not in {
                r["id"] for r in yaml.safe_load(REGISTRY.read_text())
            }:
                p.error("unknown class id")
            extra["classes"] = [a.class_id]
        if a.audio:
            extra["medium"] = "audio"
        append(
            [
                finding(
                    a.episode,
                    a.source,
                    a.description,
                    a.severity,
                    a.location,
                    "manual " + a.location,
                    **extra,
                )
            ]
        )
