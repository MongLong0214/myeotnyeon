"""Blind picture scoring on the six axes in the historical Fable reports."""

import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

import cv2
from PIL import Image, ImageDraw
from anchors.build import examples as reference_examples, write_sheet

HERE = Path(__file__).resolve().parent
AXES = ["anatomy", "materials", "lighting", "camera_motion", "composition", "hook"]
RULE = """Open each example sheet and compare the new film to the six scored Fable axes.
Open every candidate sheet. Score each axis independently in half-points. Give a frame and observable evidence for each.
Track gum attachment and boundaries, the full tool path, crown/root separation and final socket when applicable.
For the person, follow the silhouette, transitions and landmarks during camera changes. Inspect hook and payoff at phone size.
Return localized P0s even in highly rated pictures. A P0 needs the visible failure, frame and repair; identify each part of compound defects.
Audio listening and sources cannot be verified from these pictures. Do not infer absent frames or penalize draft resolution alone.
The six candidate ratings will be combined in code. 7 is EBS reference quality."""
AXIS = {
    "type": "object",
    "required": ["score", "evidence"],
    "properties": {
        "score": {"type": "number", "minimum": 1, "maximum": 10, "multipleOf": 0.5},
        "evidence": {"type": "string", "minLength": 1},
    },
}
SCHEMA = {
    "type": "object",
    "required": ["axes", "p0"],
    "properties": {
        "axes": {
            "type": "object",
            "required": AXES,
            "properties": dict.fromkeys(AXES, AXIS),
        },
        "p0": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["frame", "what", "box"],
                "properties": {
                    "frame": {"type": "integer", "minimum": 0},
                    "what": {"type": "string"},
                    "box": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "description": "Normalized x0, y0, x1, y1 within the candidate sequence crop, measured from its top-left.",
                        "items": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
        },
    },
}


def band_box(box, band_y, band_h):
    """Map a normalized sequence-crop box to the native before/after verification band."""
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"invalid sequence-crop box: {box}")
    top, bottom = round(0.24 * 1920), round(0.72 * 1920)
    left = math.floor(x0 * 1080)
    right = math.ceil(x1 * 1080)
    y0 = max(0, min(band_h - 1, math.floor(top + y0 * (bottom - top) - band_y)))
    y1 = max(y0 + 1, min(band_h, math.ceil(top + y1 * (bottom - top) - band_y)))
    return [left, y0, right, y1]


def pages(movie, out):
    cap = cv2.VideoCapture(str(movie))
    try:
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if n < 2 or fps <= 0:
            raise ValueError("unreadable review film")
        for name, frames, full in [
            ("layout", [round(i * (n - 1) / 7) for i in range(8)], True),
            ("sequence", list(range(0, n, max(1, round(fps / 2)))) + [n - 1], False),
        ]:
            for offset in range(0, len(frames), 16):
                batch = frames[offset : offset + 16]
                w, h = (235, 425) if full else (385, 310)
                sheet = Image.new(
                    "RGB", (4 * w, math.ceil(len(batch) / 4) * (h + 20)), "#131313"
                )
                draw = ImageDraw.Draw(sheet)
                for i, f in enumerate(batch):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                    ok, a = cap.read()
                    if not ok:
                        raise ValueError(f"missing candidate frame {f}")
                    if not full:
                        a = a[round(0.24 * len(a)) : round(0.72 * len(a))]
                    im = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
                    im.thumbnail((w, h))
                    x, y = i % 4 * w, i // 4 * (h + 20)
                    sheet.paste(im, (x, y + 20))
                    draw.text((x + 4, y + 3), f"f{f}", fill="white")
                sheet.save(out / f"candidate_{name}_{offset:03}.jpg", quality=90)
    finally:
        cap.release()


def score(movie, out, model="opus"):
    out.mkdir(parents=True, exist_ok=True)
    historical = json.loads((HERE / "anchors/examples.json").read_text())
    digest = hashlib.sha256(movie.read_bytes()).hexdigest()
    if digest in {row["sha256"] for row in historical}:
        raise ValueError("this movie is a calibration anchor")
    with tempfile.TemporaryDirectory(dir=out) as name:
        packet = Path(name)
        pages(movie, packet)
        descriptions = []
        for i, row in enumerate(reference_examples(exclude={digest})):
            sheet = f"example_{i + 1}.jpg"
            write_sheet(row, packet / sheet)
            descriptions.append([sheet, row["axes"], row.get("scope", "")])
        prompt = (
            RULE
            + "\nExample sheets, axis scores and evidence:\n"
            + json.dumps(descriptions, ensure_ascii=False)
        )
        prompt += "\nCandidate sheets (use Read): " + ", ".join(
            p.name for p in sorted(packet.glob("candidate_*"))
        )
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                model,
                "--output-format",
                "json",
                "--strict-mcp-config",
                "--tools",
                "Read",
                "--allowedTools",
                "Read",
                "--no-session-persistence",
                "--disable-slash-commands",
                "--json-schema",
                json.dumps(SCHEMA),
            ],
            cwd=packet,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=900,
        )
        if result.returncode:
            raise RuntimeError((result.stdout or result.stderr)[-1500:])
        envelope = json.loads(result.stdout)
        if envelope.get("is_error"):
            raise RuntimeError(envelope.get("result"))
        r = envelope["structured_output"]
        scores = [r["axes"][key]["score"] for key in AXES]
        if any(v * 2 != int(v * 2) or not 1 <= v <= 10 for v in scores):
            raise ValueError("invalid axis scores")
        # Median historical (overall - six-axis mean) on the even development reports.
        combined = min(10, math.floor(2 * (sum(scores) / len(scores) + 0.25) + 0.5) / 2)
        return dict(
            r,
            final=combined,
            sha256=digest,
            models=list(envelope.get("modelUsage", {})),
            cost_usd=envelope.get("total_cost_usd"),
        )
