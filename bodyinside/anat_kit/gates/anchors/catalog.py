"""Index all requested Fable reports and extract crops from the reviewed edition where available."""

import argparse
import hashlib
import json
import re
from pathlib import Path

import cv2
from PIL import Image, ImageDraw


def extract(path, frames, dest):
    cap = cv2.VideoCapture(str(path))
    try:
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        selected = [f for f in frames if 0 <= f < count][:8] or [
            0,
            count // 2,
            count - 1,
        ]
        page = Image.new("RGB", (4 * 340, 300 * ((len(selected) + 3) // 4)))
        draw = ImageDraw.Draw(page)
        for i, f in enumerate(selected):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ok, frame = cap.read()
            if not ok:
                raise ValueError(f"missing {path} frame {f}")
            h, w = frame.shape[:2]
            if h > w:
                frame = frame[round(h * 0.24) : round(h * 0.71)]
            im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            im.thumbnail((340, 280))
            x, y = 340 * (i % 4), 300 * (i // 4)
            page.paste(im, (x, y + 20))
            draw.text((x + 4, y + 3), f"f{f}", fill="white")
        page.save(dest, quality=88)
        return selected
    finally:
        cap.release()


def catalog(root, out):
    records = []
    out.mkdir(parents=True, exist_ok=True)
    for region in ("anat_neck", "anat_neck_v3", "anat_wisdom"):
        directory = root / region
        reports = sorted((directory / "review").glob("fable_review*.md"))
        for report in reports:
            s = report.read_text()
            tags = re.findall(r"draft\d+b?", s.splitlines()[0])
            frames = list(dict.fromkeys(map(int, re.findall(r"\bf(\d+)", s))))
            axes = [line for line in s.splitlines() if re.match(r"^\| [1-7]\.", line)]
            method = next(
                (line for line in s.splitlines() if line.startswith("Method:")), ""
            )
            pin = re.search(r"(sha256|md5)(?: prefix)? `([0-9a-f]{8,64})", method, re.I)
            for tag in dict.fromkeys(tags or ["partial"]):
                stem = region + "_" + report.stem + "_" + tag
                row = {
                    "report": str(report.relative_to(root)),
                    "edition": tag,
                    "axes": axes,
                    "scope": "changed segments"
                    if region.endswith("v3")
                    else "partial"
                    if tag == "partial"
                    else "movie",
                }
                candidates = [directory / (tag + ".mp4")]
                if tag == "partial":
                    candidates = [directory / "review/partial_0-4.7s.mp4"]
                if pin:
                    candidates += sorted(directory.glob(tag + "_*.mp4"))
                for movie in dict.fromkeys(candidates):
                    if not movie.is_file():
                        continue
                    data = movie.read_bytes()
                    if pin and not hashlib.new(
                        pin[1].lower(), data
                    ).hexdigest().startswith(pin[2]):
                        continue
                    row.update(
                        movie=movie.name,
                        sha256=hashlib.sha256(data).hexdigest(),
                        identity="report digest" if pin else "archive filename",
                        frames=extract(movie, frames, out / (stem + ".jpg")),
                        crop=stem + ".jpg",
                    )
                    break
                else:
                    row["unavailable"] = "reviewed bytes missing or overwritten"
                records.append(row)
    (out / "catalog.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("episodes", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    catalog(args.episodes, args.output)
