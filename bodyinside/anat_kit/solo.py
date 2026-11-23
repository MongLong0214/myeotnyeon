"""Time a template-only Sonnet build with the production preflight and movie gates."""

import argparse
import copy
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from episode_template import KIT, NAMES, initialize, read, validate

sys.path.insert(0, str(KIT / "gates"))
from media_checks import on_screen_wording

STRING = {"type": "string", "minLength": 1}
PATCH = {
    "type": "object",
    "required": ["status", "reason", "title", "beats", "offsets"],
    "properties": {
        "status": {"enum": ["revise", "blocked"]},
        "reason": STRING,
        "title": {"type": "array", "items": STRING, "minItems": 2, "maxItems": 2},
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["caption", "spoken"],
                "properties": {"caption": STRING, "spoken": STRING},
            },
        },
        "offsets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "dx", "dy"],
                "properties": {
                    "label": STRING,
                    "text": STRING,
                    "dx": {"type": "integer", "minimum": -1080, "maximum": 1080},
                    "dy": {"type": "integer", "minimum": -1080, "maximum": 1080},
                },
            },
        },
    },
}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def timed_command(cmd, seconds, **kwargs):
    # The deadline covers the entire process tree of this run, including a pending grader.
    with subprocess.Popen(cmd, start_new_session=True, **kwargs) as child:
        try:
            out, err = child.communicate(input=None, timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
            raise
    return subprocess.CompletedProcess(cmd, child.returncode, out, err)


def feedback(folder, tag):
    result = {}
    for p in sorted((folder / "gates").glob(tag + "_*.json")):
        data = read(p)
        if p.name.endswith("review_opus.json"):
            result["opus"] = {
                k: data.get(k) for k in ["final", "p0", "p1", "class_failures", "error"]
            }
        elif isinstance(data, dict) and (
            "errors" in data or data.get("ok") is False or data.get("pass") is False
        ):
            result[p.stem] = data
        elif p.name.endswith("stills_checks.json"):
            result["stills_checks"] = {k: v for k, v in data.items() if not v[0]}
    if "opus" in result:
        result["previous_items"] = [
            dict(id=str(i), **f)
            for i, f in enumerate(
                (result["opus"].get("p0") or []) + (result["opus"].get("p1") or [])
            )
        ]
    return result


def changed_windows(before, ep):
    if before["title"] != ep["title"]:
        return [[0, round(ep["duration"] * ep["fps"]) - 1]]
    windows = [
        [round(b["t0"] * ep["fps"]), round(b["t1"] * ep["fps"]) - 1]
        for previous, b in zip(before["beats"], ep["beats"], strict=True)
        if previous["cap"] != b["cap"]
    ]
    windows.extend(
        [label["f0"], label["f1"]]
        for old, label in zip(before["labels"], ep["labels"], strict=True)
        if old != label
    )
    return sorted(map(list, {tuple(w) for w in windows}))


def trial(folder, name, topic):
    start_unix = time.time()
    started = time.monotonic()
    folder.mkdir(parents=True, exist_ok=False)
    initialize(folder, name)
    history = []
    instructions = """You are the sole Korean anatomy episode author. Write the requested neighbouring topic on the supplied immutable shots.
Write fresh Korean title, one short caption and one Sohee spoken line for each beat. Keep the subject of the frame and assigned source.
Aim at 6.4 spoken syllables/sec, and match captions to visible evidence. You may change the wording or pixel offset of dental callouts while keeping their assigned claim and anatomical landmark.
Use each caption to describe what the viewer sees. Read the callouts active during that beat and avoid repeating their text.
For movie revisions, use repairs to classify each previous_items ID as fixed, partial, or not_fixed. Address all findings together. If a blocking defect requires changing frozen geometry or tools, explain exactly why and return blocked.
Do not stop for a fix you can make with these fields. The controller performs the render, locked checks and Opus grading."""
    patch_schema = dict(
        PATCH,
        properties=dict(
            copy.deepcopy(PATCH["properties"]),
            repairs={
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "status"],
                    "properties": {
                        "id": STRING,
                        "status": {"enum": ["fixed", "partial", "not_fixed"]},
                    },
                },
            },
        ),
    )
    base = read(folder / "episode.json")
    label_ids = [l["id"] for l in base["labels"] if l["kind"] == "callout"]
    offsets = patch_schema["properties"]["offsets"]
    if label_ids:
        offsets["items"]["properties"]["label"] = {"enum": label_ids}
    else:
        offsets["maxItems"] = 0
    patch_schema["properties"]["beats"].update(
        minItems=len(base["beats"]), maxItems=len(base["beats"])
    )
    report = {
        "topic": topic,
        "template": name,
        "start_unix": start_unix,
        "attempts": history,
    }

    def save(status):
        report.update(status=status, elapsed_s=round(time.monotonic() - started, 2))
        write(folder / "trial.json", report)

    def remaining():
        seconds = 7200 - (time.monotonic() - started)
        if seconds <= 0:
            raise TimeoutError("two-hour episode deadline")
        return seconds

    def run(tag, flags):
        with (folder / (tag + ".log")).open("w") as log:
            proc = timed_command(
                [sys.executable, KIT / "run.py", folder, tag, *flags],
                remaining(),
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        report_file = (
            folder
            / "gates"
            / ("preflight.json" if "--preflight" in flags else tag + "_submission.json")
        )
        data = read(report_file) if report_file.is_file() else {}
        if "errors" not in data:
            raise RuntimeError((folder / (tag + ".log")).read_text()[-2200:])
        review = read(folder / "gates" / (tag + "_review_opus.json"))
        history.append(
            dict(
                tag=tag,
                score=review.get("final"),
                p0=len(review["p0"]) if "p0" in review else None,
                errors=data["errors"],
                elapsed_s=round(time.monotonic() - started, 1),
            )
        )
        save("running")
        if review.get("error"):
            raise RuntimeError(review["error"])
        return data.get("pass") is True and proc.returncode == 0

    save("building")
    try:
        iteration = 0
        number = 1
        previous = {}
        while number <= 5:
            iteration += 1
            ep = read(folder / "episode.json")
            prompt = (
                instructions
                + "\nTopic: "
                + topic
                + "\n"
                + (folder / "SOURCES.md").read_text()
                + "\n"
                + json.dumps(ep, ensure_ascii=False)
            )
            if previous:
                prompt += "\nLatest grade and repairs:\n" + json.dumps(
                    previous, ensure_ascii=False
                )
            res = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--model",
                    "sonnet",
                    "--output-format",
                    "json",
                    "--tools",
                    "",
                    "--strict-mcp-config",
                    "--disable-slash-commands",
                    "--no-session-persistence",
                    "--json-schema",
                    json.dumps(patch_schema),
                ],
                input=prompt,
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=remaining(),
            )
            if res.returncode:
                raise RuntimeError((res.stderr or res.stdout)[-1400:])
            envelope = json.loads(res.stdout)
            if envelope.get("is_error"):
                raise RuntimeError(envelope.get("result"))
            patch = envelope["structured_output"]
            write(
                folder / f"sonnet{iteration:02}.json",
                dict(patch, models=list(envelope.get("modelUsage", {}))),
            )
            if patch["status"] == "blocked":
                save("Sonnet blocked: " + patch["reason"])
                return
            ep["title"] = patch["title"]
            if len(patch["beats"]) != len(ep["beats"]):
                previous = {
                    "schema_error": "Supply exactly one caption and spoken line for every frozen beat."
                }
                continue
            for b, l, change in zip(
                ep["beats"], ep["narration"], patch["beats"], strict=True
            ):
                b["cap"] = [[change["caption"], [255, 255, 255]]]
                l["text"] = change["spoken"]
            for change in patch["offsets"]:
                label = next(
                    l
                    for l in ep["labels"]
                    if l["id"] == change["label"] and l["kind"] == "callout"
                )
                if change.get("text"):
                    label["text"] = change["text"]
                label.update(dx=change["dx"], dy=change["dy"])
            validate(folder, ep)
            write(folder / "episode.json", ep)
            ok, wording = on_screen_wording(ep)
            if not ok:
                previous["wording_to_revise_before_render"] = wording
                history.append(
                    dict(
                        tag=f"copy{iteration:02}",
                        wording=wording,
                        elapsed_s=round(time.monotonic() - started, 1),
                    )
                )
                save("revising wording")
                continue
            pf = f"pf{iteration:02}"
            if not run(pf, ["--preflight"]):
                previous = feedback(folder, pf)
                continue
            tag = f"draft{number:02}"
            flags = ["--draft"]
            if number > 1:
                prev = f"draft{number - 1:02}"
                before = read(folder / (prev + "_episode.json"))
                windows = changed_windows(before, ep)
                changes_file = folder / "changes.json"
                changes = read(changes_file) if changes_file.is_file() else {}
                changes[tag] = {"windows": windows}
                write(changes_file, changes)
                findings = read(folder / "gates" / (prev + "_review_opus.json"))[
                    "findings"
                ]
                claims = {c["id"]: c["status"] for c in patch.get("repairs", [])}
                write(
                    folder / "items.json",
                    [
                        dict(
                            id=str(i),
                            frame=f["frame"],
                            box=f["box"],
                            claim=claims.get(str(i), "not_fixed"),
                        )
                        for i, f in enumerate(findings)
                    ],
                )
                flags.extend(["--prev", prev])
            write(folder / (tag + "_episode.json"), ep)
            if run(tag, flags):
                save("passing draft awaiting owner confirmation")
                return
            previous = feedback(folder, tag)
            number += 1
        save("five drafts submitted")
    except Exception as exc:
        save("stopped: " + str(exc))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", choices=NAMES)
    parser.add_argument("folder", type=Path)
    parser.add_argument("topic")
    args = parser.parse_args()
    trial(args.folder.resolve(), args.template, args.topic)
