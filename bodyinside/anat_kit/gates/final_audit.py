"""Request the one Fable audit for an approved final movie, recording the first outcome."""

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def audit(folder, tag):
    gates = folder / "gates"
    path = gates / "final_fable_audit.json"
    movie = folder / (tag + ".mp4")
    with movie.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    receipt = json.loads((gates / (tag + "_submission.json")).read_text())
    render = json.loads((gates / (tag + "_render.json")).read_text())
    if (
        render["mode"] not in ("final", "final-fast")
        or not receipt.get("opus_pass", receipt["pass"])
        or receipt["movie_sha256"] != sha
    ):
        raise ValueError(
            "Fable audit requires the passing final and its matching digest"
        )

    def save(data):
        pending = path.with_suffix(".tmp")
        pending.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        pending.replace(path)

    with (gates / "final_fable.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.is_file():
            previous = json.loads(path.read_text())
            if previous["movie_sha256"] != sha:
                raise ValueError(
                    "another cut already received this episode's final audit"
                )
            return previous
        model = os.environ.get("ANAT_FABLE_MODEL", "fable")
        if "fable" not in model.lower():
            raise ValueError("use a Fable model identifier")
        record = {
            "tag": tag,
            "movie_sha256": sha,
            "model": model,
            "status": "started",
            "pass": False,
        }
        save(record)
        result_file = gates / (tag + "_review_fable.json")
        if result_file.exists():
            raise ValueError("a Fable review already exists for this cut")
        proc = subprocess.run(
            [
                sys.executable,
                Path(__file__).with_name("review_gate.py"),
                folder,
                tag,
                "--model",
                model,
                "--runs",
                "1",
                "--single-audit",
            ]
        )
        if result_file.is_file():
            result = json.loads(result_file.read_text())
            if result.get("_md5") != hashlib.md5(movie.read_bytes()).hexdigest():
                raise ValueError("Fable review refers to different movie bytes")
            record.update(
                status="error" if result.get("error") else "reviewed",
                score=result.get("final"),
                p0=len(result["p0"]) if "p0" in result else None,
                error=result.get("error"),
                **{"pass": proc.returncode == 0 and result.get("pass") is True},
            )
        else:
            record.update(status="error", error=f"reviewer exited {proc.returncode}")
        import time
        record["reviewed_at"] = time.time()
        save(record)
        if record["status"] == "reviewed":
            sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
            from improvement_log import capture_run
            capture_run(folder, tag)
        return record


if __name__ == "__main__":
    result = audit(Path(sys.argv[1]).resolve(), sys.argv[2])
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)
