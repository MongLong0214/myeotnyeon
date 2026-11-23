"""Recheck P1 findings against native-frame crops before ranking repairs."""

import fcntl
import hashlib
import json
import subprocess

import cv2
from PIL import Image, ImageDraw

from thresholds import T

RULE = """Open every numbered evidence page with Read. Each row in the list describes a
candidate finding from the same film. Classify its effect on the episode. A confirmed
material or geometry error that prevents identifying the tooth, bone, nerve or other
named structure, changes a physical event, hides a measurement or makes a claimed
relationship false is P0. The same applies to an unreadable payoff, a clinical instrument
with no identifiable working end, an opaque/flat cutaway that destroys anatomical depth,
a graphic that measures the wrong points, a visible single-frame dropout, and an
implausible motion path. Accurate anatomy with coarse polish is P1. Confirm the specific
defect in the supplied full view and crop, and keep uncertain evidence at P1. Return
only the IDs of confirmed P0s, in decreasing educational impact, with the observed
evidence. A similar object, an imagined defect or a proposed improvement alone is
insufficient. Cite only the supplied media. Return every page filename you opened."""


def evidence(movie, findings, folder, band_y):
    cap = cv2.VideoCapture(str(movie))
    pages = []
    try:
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for start in range(0, len(findings), 6):
            group = findings[start : start + 6]
            sheet = Image.new("RGB", (1170, 255 * len(group)), "#151515")
            draw = ImageDraw.Draw(sheet)
            for i, finding in enumerate(group):
                frame = max(0, min(frames - 1, int(finding["frame"])))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                ok, data = cap.read()
                if not ok:
                    raise ValueError(f"missing movie frame {frame}")
                full = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
                w, h = full.size
                scale = w / 1080
                x0, y0, x1, y1 = finding["box"]
                x0, x1 = sorted((x0, x1))
                y0, y1 = sorted((y0, y1))
                left = max(0, min(w - 1, int((x0 - 40) * scale)))
                top = max(0, min(h - 1, int((band_y + y0 - 40) * scale)))
                right = max(left + 1, min(w, int((x1 + 40) * scale)))
                bottom = max(top + 1, min(h, int((band_y + y1 + 40) * scale)))
                crop = full.crop((left, top, right, bottom))
                crop.thumbnail((600, 230))
                band = full.crop(
                    (0, max(0, round(h * 0.23)), w, min(h, round(h * 0.74)))
                )
                band.thumbnail((520, 230))
                row = i * 255
                sheet.paste(band, (0, row + 23))
                sheet.paste(crop, (535, row + 23))
                draw.text(
                    (2, row + 2),
                    f"Candidate {start + i + 1}, frame {frame}",
                    fill="white",
                )
            path = folder / f"evidence_{start // 6:02d}.jpg"
            sheet.save(path, quality=93)
            pages.append(path.name)
    finally:
        cap.release()
    return pages


def rank_review(movie, folder, result, band_y=470):
    """Keep initial P1s in runs; publish the final severity and visual confirmation."""
    if "severity_review" in result or not result["p1"]:
        return
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "decisions.json"
    findings = result["p1"]
    model = result["_model"]
    payload = json.dumps(
        [result["_md5"], model, band_y, findings, RULE], sort_keys=True
    ).encode()
    signature = hashlib.sha256(payload).hexdigest()
    with (folder / "review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cached = json.loads(path.read_text()) if path.is_file() else {}
        if cached.get("signature") != signature:
            pages = evidence(movie, findings, folder, band_y)
            prompt = (
                RULE
                + "\n"
                + "\n".join(pages)
                + "\n"
                + "\n".join(
                    f"{i}. f{p['frame']} {p['what']}" for i, p in enumerate(findings, 1)
                )
            )
            item = {
                "type": "object",
                "required": ["id", "evidence"],
                "properties": {
                    "id": {"type": "integer", "minimum": 1, "maximum": len(findings)},
                    "evidence": {"type": "string"},
                },
            }
            schema = {
                "type": "object",
                "required": ["promote", "pages_seen"],
                "properties": {
                    "promote": {"type": "array", "items": item},
                    "pages_seen": {"type": "array", "items": {"type": "string"}},
                },
            }
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
            run = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=folder,
                timeout=cfg["timeout_s"],
                check=True,
            )
            response = json.loads(run.stdout)
            if response.get("is_error"):
                raise RuntimeError(response.get("result"))
            decisions = response.get("structured_output") or json.loads(
                response["result"]
            )
            if sorted(decisions["pages_seen"]) != sorted(pages):
                raise ValueError("missing severity evidence pages")
            cached = dict(
                decisions, signature=signature, cost=response.get("total_cost_usd", 0)
            )
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(cached, ensure_ascii=False, indent=1))
            tmp.replace(path)
    ids = [row["id"] for row in cached["promote"]]
    if len(set(ids)) != len(ids) or not all(1 <= n <= len(findings) for n in ids):
        raise ValueError("invalid severity decisions")
    promoted = [
        dict(findings[row["id"] - 1], source="severity review", confirm=row["evidence"])
        for row in cached["promote"]
    ]
    result["p0"].extend(promoted)
    result["p1"] = [p for i, p in enumerate(findings, 1) if i not in set(ids)]
    result["severity_review"] = {
        "promoted": len(promoted),
        "pages": len(cached["pages_seen"]),
        "cost": cached["cost"],
    }
    result["_cost_usd"] = round(result["_cost_usd"] + cached["cost"], 3)
    if promoted:
        result["pass"] = False
    result["findings"] = [
        dict(priority=k, **p) for k in ("p0", "p1") for p in result[k]
    ]
