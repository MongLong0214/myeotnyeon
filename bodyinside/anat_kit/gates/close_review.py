"""Inspect close views of the actual film for short-lived, local P0s.

The frame schedule is independent of episode names, Fable labels and prior findings.
A frame is labelled with its zero-based index and shows the central anatomy band.
"""

import hashlib
import fcntl
import json
import math
from pathlib import Path
import subprocess

import cv2
from PIL import Image, ImageDraw
from thresholds import T


def contact_pages(movie, folder):
    cap = cv2.VideoCapture(str(movie))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if n < 2 or fps <= 0:
            raise ValueError("unreadable movie")
        # The opening and payoff contain very short face/landmark changes.
        # Sample the middle evenly regardless of shot plan or subject.
        frames = sorted(
            set(range(0, min(n, round(fps)), 3))
            | set(range(0, n, max(1, round(fps / 2))))
            | set(range(3 * n // 4, n, max(1, round(fps / 5))))
            | {n - 1}
        )
        paths = []
        for start in range(0, len(frames), 9):
            batch = frames[start : start + 9]
            page = Image.new(
                "RGB", (1620, 455 * math.ceil(len(batch) / 3)), (20, 20, 20)
            )
            draw = ImageDraw.Draw(page)
            for tile, f in enumerate(batch):
                cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                ok, bgr = cap.read()
                if not ok:
                    raise ValueError(f"missing video frame {f}")
                h, w = bgr.shape[:2]
                band = Image.fromarray(
                    cv2.cvtColor(
                        bgr[round(h * 0.24) : round(h * 0.73)], cv2.COLOR_BGR2RGB
                    )
                )
                band.thumbnail((540, 430))
                x, y = tile % 3 * 540, tile // 3 * 455
                page.paste(band, (x, y + 22))
                draw.text((x + 4, y + 2), f"f{f}", fill="white")
            path = folder / f"close_{start:03d}.jpg"
            page.save(path, quality=92)
            paths.append(path)
        return paths
    finally:
        cap.release()


def audit(movie, folder, model="opus"):
    folder.mkdir(parents=True, exist_ok=True)
    pages = contact_pages(movie, folder)
    item = {
        "type": "object",
        "required": ["frame", "box", "what"],
        "properties": {
            "frame": {"type": "integer", "minimum": 0},
            "box": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 4,
                "maxItems": 4,
            },
            "what": {"type": "string"},
        },
    }
    schema = {
        "type": "object",
        "required": ["p0", "pages_seen"],
        "properties": {
            "p0": {"type": "array", "items": item},
            "pages_seen": {"type": "array", "items": {"type": "string"}},
        },
    }
    prompt = """Independently inspect the labelled close views of this Korean anatomy film. Open every listed JPEG using Read.
Inspect the earliest opaque face silhouette in profile: trace the forehead, nose, chin against the background. Look for a thin protruding bone-white skull contour.
Follow each transition through to the next settled subject. Does the skeleton shrink to an isolated skewer or leave a floating fragment? In the payoff inspect the chin and jaw for a second bone contour; locate each ear and shoulder dot on the near surface in EACH camera view. The shoulder tip is lateral; in a rear view a dot on the upper back is wrong.
For a dental film inspect in anatomical order: contact of impacted tooth with neighbour, encasing bone and gums, cortical rim, crown cusps and roots, instrument/nerve clearance, sectioning, crown and root removal path, empty socket, canal and measurement bracket. Look for broken anatomy, transparencies, leftover tooth, tools entering nerve, labels occluded at viewpoint changes, impossible geometry or a completely obscured clinical event. Inspect highlight, exposure, hook, crop and single-frame changes. Report ALL observed P0 defects; a different anatomy or an inapplicable test is normal. Use only the supplied frames. State the first confirming frame, the exact anatomy, defect, concrete repair and 1080-wide anatomy-band box. Never infer that a particular defect is present just because this instruction names it. Record the filenames you actually saw.
"""
    prompt += "\n".join(p.name for p in pages)
    cfg = T["review_gate"].get(model, T["review_gate"]["opus"])
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        "--tools",
        "Read",
        "--allowedTools",
        "Read",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--max-budget-usd",
        str(cfg["max_usd"]),
        "--json-schema",
        json.dumps(schema),
    ]
    r = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=folder,
        timeout=cfg["timeout_s"],
        check=True,
    )
    env = json.loads(r.stdout)
    if env.get("is_error"):
        raise ValueError(env.get("result"))
    result = env.get("structured_output") or json.loads(env["result"])
    if sorted(result["pages_seen"]) != sorted(p.name for p in pages):
        raise ValueError("close review omitted evidence pages")
    return {
        "p0": result["p0"],
        "pages": len(pages),
        "cost": env.get("total_cost_usd", 0),
    }


def cached_audit(movie, folder, model="opus"):
    """Serialize concurrent requests for the same cut and reject stale cached evidence."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "findings.json"

    def digest():
        return hashlib.md5(Path(movie).read_bytes()).hexdigest()

    initial = digest()
    with (folder / "review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.is_file():
            result = json.loads(path.read_text())
            if result.get("md5") == initial and result.get("model") == model:
                return result
        result = audit(Path(movie), folder, model)
        if digest() != initial:
            raise ValueError("movie changed during close review")
        result.update(md5=initial, model=model)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=1))
        tmp.replace(path)
        return result


def attach(result, close):
    if result["_md5"] != close["md5"]:
        raise ValueError("close-review digest mismatch")
    if "close_review" not in result:
        result["close_review"] = {
            "pages": close["pages"],
            "cost": close["cost"],
            "p0": close["p0"],
        }
        result["p0"] += [dict(p, source="close review") for p in close["p0"]]
        result["_cost_usd"] = round(result["_cost_usd"] + close["cost"], 3)
    if result["p0"]:
        result["pass"] = False
    result["findings"] = [
        dict(priority=priority, **p)
        for priority in ("p0", "p1")
        for p in result[priority]
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("movie", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cached_audit(args.movie, args.output)
