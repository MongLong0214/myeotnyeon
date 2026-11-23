"""Reconstruct Fable reference crops from pinned, locally installed movie bytes."""

import hashlib
import json
import os
from pathlib import Path

import cv2
from PIL import Image, ImageDraw


def examples(exclude=()):
    directory = Path(__file__).parent
    rows = json.loads((directory / "examples.json").read_text())
    finals = directory / "finals.json"
    if finals.exists():
        rows.extend(json.loads(finals.read_text()))
    return [row for row in rows if row["sha256"] not in exclude]


def write_sheet(example, dest):
    root = Path(
        os.environ.get(
            "ANAT_EPISODES", (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + "/../../../episodes")
        )
    )
    source = root / example["movie"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != example["sha256"]:
        raise ValueError(
            f"archive movie differs from Fable's reviewed edition: {source}"
        )
    frames = example["frames"]
    cap = cv2.VideoCapture(str(source))
    sheet = Image.new("RGB", (1140, 660))
    draw = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, image = cap.read()
        if not ok:
            raise ValueError((source, f))
        h = image.shape[0]
        part = Image.fromarray(
            cv2.cvtColor(image[int(0.24 * h) : int(0.71 * h)], cv2.COLOR_BGR2RGB)
        )
        part.thumbnail((380, 305))
        x, y = i % 3 * 380, i // 3 * 330
        sheet.paste(part, (x, y + 20))
        draw.text((x + 4, y + 3), f"f{f}", fill="white")
    cap.release()
    sheet.save(dest, quality=90)
    if "crop_sha256" in example and hashlib.sha256(dest.read_bytes()).hexdigest() != example["crop_sha256"]:
        raise ValueError(
            f"generated benchmark pixels or JPEG encoder differ: {dest.name}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for row in examples():
        write_sheet(row, args.output / row["sheet"])
