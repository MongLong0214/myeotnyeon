"""Score the pre-existing held-out movie split. Give the grader only anonymized pixels."""

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from anchored_review import score
from calibrate import population


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episodes", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        r
        for r in population(args.episodes)
        if r["split"] == "heldout" and r["movie"] and Path(r["movie"]).is_file()
    ]

    def run(row):
        movie = Path(row["movie"])
        md5 = hashlib.md5(movie.read_bytes()).hexdigest()
        if row["prefix"] and not md5.startswith(row["prefix"]):
            raise ValueError(f"review digest differs: {movie}")
        dest = out / md5
        try:
            result = score(movie, dest)
            result.update(
                region=row["region"],
                tag=row["tag"],
                fable=row["target"],
                gold=row["p0"],
            )
        except Exception as exc:
            result = dict(region=row["region"], tag=row["tag"], error=str(exc))
        (out / (md5 + ".json")).write_text(
            json.dumps(result, ensure_ascii=False, indent=2)
        )
        print(
            row["region"],
            row["tag"],
            result.get("final"),
            result.get("error", ""),
            flush=True,
        )

    with ThreadPoolExecutor(args.jobs) as pool:
        list(pool.map(run, cases))


if __name__ == "__main__":
    main()
