"""Replay Fable-labelled films, keeping answers outside the reviewer's evidence packet.

Usage: python calibrate.py EPISODES_ROOT OUTPUT [--jobs N]
A failed or incomplete review is counted separately. Each row points back to its Fable report.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from close_review import attach, cached_audit
from severity import rank_review
from score_scale import fit, metrics, predict

HERE = Path(__file__).resolve().parent


def population(root):
    for region in ("neck", "wisdom"):
        episode = root / ("anat_" + region)
        for number in range(1, (14 if region == "neck" else 21) + 1):
            if region == "neck" and number < 6:
                continue
            suffix = "" if region == "wisdom" and number == 1 else str(number)
            review = episode / "review" / f"fable_review{suffix}.md"
            report = review.read_text()
            title = report.splitlines()[0]
            tags = re.findall(r"draft\d+b?", title)
            scores = re.search(r"^\| 7\. Overall\s*\|([^\n]+)", report, re.M)
            values = (
                [
                    float(v.strip())
                    for v in scores[1].split("|")
                    if re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", v)
                ]
                if scores
                else []
            )
            if not values:
                values = [float(re.search(r"[Oo]verall (\d+(?:\.\d+)?)", report)[1])]
            section = re.search(
                r"^## P0\b[^\n]*\n(.*?)(?=^## |\Z)", report, re.M | re.S
            )
            p0 = re.findall(r"^\d+\.\s+(.+)", section[1], re.M) if section else []
            if region == "neck" and number == 6:
                p0 = [
                    "The closing plumb line ends in empty air rather than on the anatomical endpoints."
                ]
            prefix = re.search(r"md5 `([0-9a-f]{8,32})", report)
            for tag, score in zip(
                tags or ["partial"], values[-max(len(tags), 1) :], strict=True
            ):
                yield dict(
                    region=region,
                    tag=tag,
                    review=str(review),
                    target=score,
                    p0=p0,
                    number=number,
                    split=("development" if number % 2 == 0 else "heldout"),
                    prefix=prefix[1] if prefix else None,
                    movie=str(episode / (tag + ".mp4")) if tags else None,
                )


def score(row, output):
    if not row["movie"] or not Path(row["movie"]).is_file():
        return dict(row, status="reviewed movie missing or only partially rendered")
    digest = hashlib.md5(Path(row["movie"]).read_bytes()).hexdigest()
    if row["prefix"] and not digest.startswith(row["prefix"]):
        return dict(row, status="file differs from reviewed digest")
    tag = "clip_" + digest[:12]
    where = output / "evidence"
    where.mkdir(exist_ok=True)
    path = where / (tag + "_review_opus.json")

    def cached():
        try:
            result = json.loads(path.read_text())
        except (OSError, ValueError):
            return {}
        return result if result.get("_md5") == digest else {}

    result = cached()
    if "final" not in result or result.get("error"):
        if path.exists():
            path.rename(path.with_suffix(".previous.json"))
        with (output / (tag + ".log")).open("w") as log:
            subprocess.run(
                [
                    sys.executable,
                    str(HERE / "review_gate.py"),
                    str(where),
                    tag,
                    "--mp4",
                    row["movie"],
                    "--draft",
                    "--historical",
                    "--out",
                    str(where),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        result = cached()
    if "final" not in result or result.get("error"):
        return dict(
            row, status="review error", detail=result.get("error"), result=str(path)
        )
    if "close_review" not in result:
        try:
            close = cached_audit(Path(row["movie"]), where / ("close_" + digest))
            attach(result, close)
        except Exception as exc:
            return dict(
                row, status="close review error", detail=str(exc), result=str(path)
            )
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    if "severity_review" not in result and result.get("p1"):
        try:
            rank_review(Path(row["movie"]), where / ("severity_" + digest), result)
        except Exception as exc:
            return dict(
                row, status="severity review error", detail=str(exc), result=str(path)
            )
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    if "visibility_pops" not in result:
        from transients import apply

        apply(Path(row["movie"]), result)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    raw = sum(result["run_finals"]) / len(result["run_finals"])
    return dict(
        row,
        status="scored",
        raw=raw,
        scores=result["scores"],
        result=str(path),
        predicted_p0=result["p0"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episodes", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    population_rows = list(population(args.episodes.resolve()))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda row: score(row, output), population_rows))
    scored = [r for r in rows if r["status"] == "scored"]
    training = [r for r in scored if r["split"] == "development"]
    scale = fit(training) if training else {}
    for row in scored:
        row["prediction"] = predict(row["raw"], scale, row["scores"])
        row["error"] = row["prediction"] - row["target"]
    groups = {
        "all": scored,
        "development": training,
        "heldout": [r for r in scored if r["split"] == "heldout"],
    }
    summary = {"labelled": len(rows), "scored": len(scored), "scale": scale}
    for name, group in groups.items():
        summary[name] = {
            "calibrated": metrics([r["error"] for r in group]),
            "raw": metrics([predict(r["raw"], {}) - r["target"] for r in group]),
        }
    (output / "agreement.json").write_text(
        json.dumps(dict(summary=summary, rows=rows), ensure_ascii=False, indent=2)
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
