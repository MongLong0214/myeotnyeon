"""Add digest-matched final audits to the production Opus examples and rolling agreement."""

import json
from pathlib import Path

import cv2

from improvement_log import ARCHIVE, KIT, atomic, digest, read, records

DYNAMIC = KIT / "gates/anchors/finals.json"


def audited():
    roots = {
        path.parent.parent for path in ARCHIVE.glob("*/gates/final_fable_audit.json")
    }
    roots.update(Path(r["folder"]) for r in records() if r["source"] == "audit")
    # Diagnostic terminal cuts contribute scored picture anchors without
    # becoming approved production submissions or numerical Opus scores.
    measurements = {Path(r["ref"]) for r in records() if r["source"] == "operative_measurement"}
    for path in sorted(measurements):
        audit = read(path)
        if audit["status"] == "measured":
            yield path.parent.parent, dict(audit, reviewed_at=path.stat().st_mtime,
                                          scope="Operative terminal measurement")
    for folder in sorted(roots):
        path = folder / "gates/final_fable_audit.json"
        audit = read(path)
        if audit["status"] == "reviewed":
            yield folder, audit


def update():
    rows = read(DYNAMIC) if DYNAMIC.is_file() else []
    for folder, audit in audited():
        tag = audit["tag"]
        movie = folder / (tag + ".mp4")
        sha = digest(movie)
        if sha != audit["movie_sha256"]:
            raise ValueError(f"final audit movie changed: {movie}")
        gates = folder / "gates"
        fable = read(gates / (tag + "_review_fable.json"))
        pair = gates / (tag + "_review_opus.json")
        opus = read(pair) if pair.is_file() else {}
        import hashlib

        with movie.open("rb") as stream:
            md5 = hashlib.file_digest(stream, "md5").hexdigest()
        if (
            fable.get("_md5") != md5
            or fable.get("error")
            or audit["score"] != fable.get("final")
        ):
            raise ValueError(f"review/movie mismatch: {movie}")
        cap = cv2.VideoCapture(str(movie))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        if n < 2:
            raise ValueError(f"unreadable final: {movie}")
        frames = list(
            dict.fromkeys(
                [
                    int(p["frame"])
                    for p in fable.get("p0", []) + fable.get("p1", [])
                    if 0 <= p["frame"] < n
                ]
                + [round(i * (n - 1) / 5) for i in range(6)]
            )
        )[:6]
        picture = fable.get("picture_axes", {})
        axes = [
            (name, item["score"], item["evidence"]) for name, item in picture.items()
        ]
        if not axes:
            axes = [
                (name, fable["scores"][field])
                for name, field in [
                    ("anatomy", "anatomy"),
                    ("camera_motion", "motion"),
                    ("hook", "hook"),
                ]
            ]
        rows = [r for r in rows if r["sha256"] != sha]
        rows.append(
            dict(
                movie=str(movie),
                sha256=sha,
                sheet="final_" + sha + ".jpg",
                frames=frames,
                axes=axes,
                scope=audit.get("scope","Fable final; only the listed picture axes were scored"),
                opus=opus.get("final")
                if opus.get("_md5") == md5 and not opus.get("error")
                else None,
                fable=fable["final"],
                audited_at=audit.get("reviewed_at")
                or (gates / "final_fable_audit.json").stat().st_mtime,
            )
        )
    rows.sort(key=lambda r: (r["audited_at"], r["sha256"]))
    unique = {r["sha256"]: r for r in rows}
    atomic(
        DYNAMIC, json.dumps(list(unique.values()), indent=2, ensure_ascii=False) + "\n"
    )
    # The previous blind holdout contained 14 films, seven within half a point.
    # Replace its oldest observations as new audited pairs enter the same window.
    baseline = [r["within_half"] for r in read(KIT / "gates/anchors/agreement.json")]
    scores = baseline + [
        abs(r["opus"] - r["fable"]) <= 0.5
        for r in unique.values()
        if r["opus"] is not None
    ]
    window = len(baseline)
    current = sum(scores[-window:]) / window
    prior = max(sum(baseline), sum(scores[-window - 1 : -1])) / window
    return len(unique), sum(scores[-window:]), window, current < prior
