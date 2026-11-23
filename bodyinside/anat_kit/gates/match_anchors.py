"""Strict post-score matching. Include archived blind P0s only for matching movie bytes."""

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RULE = """For each gold P0 identify predicted P0 indices with the same observable defect,
anatomical feature and time. Match all headline parts of a compound defect. Generic criticism,
other defects nearby and an overall rejection do not count. Mark ambiguous matches missed.
Indices start at one. Give a short reason. Never change the predictions or their severity."""
SCHEMA = {
    "type": "object",
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["gold", "predictions", "reason"],
                "properties": {
                    "gold": {"type": "integer"},
                    "predictions": {"type": "array", "items": {"type": "integer"}},
                    "reason": {"type": "string"},
                },
            },
        }
    },
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("old_evidence", type=Path)
    args = parser.parse_args()

    def match(path):
        row = json.loads(path.read_text())
        if not row.get("gold"):
            return
        base = json.loads(
            (
                args.old_evidence / ("clip_" + path.stem[:12] + "_review_opus.json")
            ).read_text()
        )
        if base["_md5"] != path.stem or base.get("error"):
            raise ValueError(f"mismatched base review {path}")
        predictions = row["p0"] + base["p0"]
        prompt = (
            RULE
            + "\nGold:\n"
            + json.dumps(row["gold"], ensure_ascii=False)
            + "\nPredicted:\n"
            + json.dumps(predictions, ensure_ascii=False)
        )
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                "opus",
                "--tools",
                "",
                "--strict-mcp-config",
                "--no-session-persistence",
                "--disable-slash-commands",
                "--output-format",
                "json",
                "--json-schema",
                json.dumps(SCHEMA),
            ],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=500,
        )
        env = json.loads(result.stdout)
        if env.get("is_error"):
            raise RuntimeError(env["result"])
        matches = env["structured_output"]["items"]
        if sorted(m["gold"] for m in matches) != list(
            range(1, len(row["gold"]) + 1)
        ) or any(
            not 1 <= i <= len(predictions) for m in matches for i in m["predictions"]
        ):
            raise ValueError("invalid match indices")
        evidence = dict(
            md5=path.stem,
            gold=row["gold"],
            predictions=predictions,
            new_count=len(row["p0"]),
            matches=matches,
        )
        (args.replay / "matches" / path.name).write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2)
        )

    (args.replay / "matches").mkdir(exist_ok=True)
    with ThreadPoolExecutor(3) as pool:
        list(pool.map(match, sorted(args.replay.glob("*.json"))))


if __name__ == "__main__":
    main()
