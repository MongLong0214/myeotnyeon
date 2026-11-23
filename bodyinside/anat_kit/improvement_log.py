"""Local anatomy findings. Each writer merges under the same advisory lock."""

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

KIT = Path(__file__).resolve().parent
FACTORY = KIT.parent / "factory"
LOG = FACTORY / "findings.jsonl"
ARCHIVE = Path(
    os.environ.get("ANAT_EPISODES", (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../episodes"))
)


def read(path):
    return json.loads(path.read_text())


def atomic(path, content):
    if path.exists() and path.read_text() == content:
        return
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
        out.write(content)
        name = out.name
    os.replace(name, path)


@contextmanager
def locked():
    # Lock the directory inode: replacing the JSONL must not replace its lock.
    fd = os.open(FACTORY, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def records():
    return [json.loads(s) for s in LOG.read_text().splitlines()] if LOG.exists() else []


def store(rows):
    atomic(LOG, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def finding(episode, source, description, severity, location, ref, **extra):
    key = json.dumps([episode, source, ref, description], ensure_ascii=False)
    return dict(
        id=hashlib.sha256(key.encode()).hexdigest()[:24],
        episode=episode,
        source=source,
        description=description,
        severity=severity,
        location=location,
        ref=ref,
        **extra,
    )


def append(batch):
    if not batch:
        return
    with locked():
        rows = records()
        positions = {r["id"]: i for i, r in enumerate(rows)}
        for r in batch:
            if r["source"] == "metric" and r["id"] in positions:
                rows[positions[r["id"]]] = r
            elif r["id"] not in positions:
                positions[r["id"]] = len(rows)
                rows.append(r)
        store(rows)


def capture_run(folder, tag):
    """Collect the exact numbered review items and individual failed measurements."""
    gates = folder / "gates"
    batch = []
    movie = folder / (tag + ".mp4")
    paths = sorted(gates.glob(tag + "_*.json"))
    preflight = gates / "preflight.json"
    if preflight.is_file() and read(preflight).get("tag") == tag:
        paths.append(preflight)
    for path in paths:
        name = path.name[len(tag) + 1 : -5]
        if path.name == "final_fable_audit.json":
            continue
        if path == preflight:
            name = "preflight"
        if name in (
            "shot_evidence",
            "frames",
            "render",
            "assembly",
            "scene_facts",
            "regression",
        ):
            continue
        try:
            data = read(path)
        except ValueError:
            batch.append(
                finding(
                    folder.name,
                    "gate",
                    f"{name}: unreadable gate result",
                    "blocking",
                    "episode",
                    str(path),
                )
            )
            continue
        if not isinstance(data, dict):
            continue
        base = dict(episode=folder.name, ref=str(path), folder=str(folder), edition=tag)
        if movie.is_file():
            base["media"] = str(movie)
        if name == "defects_meta" and data.get("errors"):
            for key, reason in data["errors"]:
                batch.append(
                    finding(
                        **base,
                        source="gate",
                        description=f"{key}: {reason}",
                        severity="blocking",
                        location="episode",
                        kind="observation",
                    )
                )
        elif name.startswith("review_") and not data.get("error"):
            source = name.removeprefix("review_")
            if source not in ("opus", "fable"):
                continue
            base.pop("media", None)
            reviewed = Path(data.get("_mp4") or movie)
            if data.get("stage") != "stills" and reviewed.is_file():
                with reviewed.open("rb") as stream:
                    matching = (
                        data.get("_md5")
                        == hashlib.file_digest(stream, "md5").hexdigest()
                    )
                if matching:
                    base["media"] = str(reviewed)
            for severity in ("p0", "p1"):
                for i, item in enumerate(data.get(severity, [])):
                    frame = item["frame"]
                    evidence = dict(base, ref=f"{path}#{severity}-{i + 1}")
                    still = gates / (tag + "_stills") / f"f_{frame:04d}.jpg"
                    if data.get("stage") == "stills" and still.is_file():
                        evidence["media"] = str(still)
                    batch.append(
                        finding(
                            **evidence,
                            source=source,
                            description=item["what"],
                            severity=severity.upper(),
                            location=f"f{frame}",
                            item=f"{severity}-{i + 1}",
                        )
                    )
            for key, state in data.get("class_failures", {}).items():
                if state in ("defects", "unseen"):
                    batch.append(
                        finding(
                            **base,
                            source=source,
                            description=key
                            if state == "defects"
                            else f"review could not verify {key}",
                            severity="blocking",
                            location="episode",
                            classes=[key],
                            **({"kind": "observation"} if state == "unseen" else {}),
                        )
                    )
        elif name == "submission" or name == "preflight":
            for msg in data.get("errors", []):
                # The detailed receipt owns the individual findings. A global registry
                # failure does not mean its historical defects appeared in this episode.
                check_name = msg.split(":", 1)[0]
                receipt = gates / f"{tag}_{check_name}.json"
                summary = receipt.exists() or msg.startswith("Opus review (")
                batch.append(
                    finding(
                        **base,
                        source="gate",
                        description=msg,
                        severity="blocking",
                        location="episode",
                        **({"kind": "observation"} if summary else {}),
                    )
                )
        elif data.get("pass", data.get("ok")) is False or name == "stills_checks":
            failures = [
                (k, v)
                for k, v in data.items()
                if (isinstance(v, dict) and v.get("ok") is False)
                or (isinstance(v, list) and v and v[0] is False)
            ]
            if name == "stills_checks" and not failures:
                continue
            for k, v in failures or [(name, data.get("errors", data))]:
                classes = {
                    "flash": "single-frame-pop-or-flash",
                    "dead_time": "dead-time-no-event",
                    "stable_notes": "label-pops-at-handoff",
                    "threshold_lock": "gate-threshold-moved-to-pass",
                    "provenance": "credit-rights-provenance-paperwork",
                    "narration_wer": "narration-misheard",
                }
                frames = []
                if isinstance(v, dict):
                    frames = [s["frame"] for s in v.get("spikes", []) if "frame" in s]
                    frames += v.get("dead_windows_start_frames", [])
                detail = dict(base)
                if key := classes.get(k) or classes.get(name.split("_")[0]):
                    detail["classes"] = [key]
                batch.append(
                    finding(
                        **detail,
                        source="gate",
                        description=k + " " + json.dumps(v, ensure_ascii=False),
                        severity="blocking",
                        location=", ".join(f"f{f}" for f in frames) or "episode",
                    )
                )
    if (gates / "final_fable_audit.json").exists():
        a = read(gates / "final_fable_audit.json")
        if a["tag"] == tag and a["status"] == "reviewed":
            batch.append(
                finding(
                    folder.name,
                    "audit",
                    a["movie_sha256"],
                    "info",
                    "episode",
                    str(gates / "final_fable_audit.json"),
                    folder=str(folder),
                )
            )
    hashes = {}
    for row in batch:
        if media := row.get("media"):
            if media not in hashes:
                hashes[media] = digest(Path(media))
            row["media_sha256"] = hashes[media]
    append(batch)
