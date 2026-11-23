"""Detect a localized flash that returns to its previous appearance one frame later."""

from collections import deque

import cv2
import numpy as np
from thresholds import T


def measure(previous, current, following):
    rule = T["visibility_pop"]
    forward, reverse = current - previous, current - following
    excess = np.maximum(0, np.minimum(forward, reverse)) + np.maximum(
        0, np.minimum(-forward, -reverse)
    )
    excess = np.maximum(0, excess - 0.5 * np.abs(previous - following))
    mask = (excess > rule["pixel_excursion"]).astype("uint8")
    _, groups, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    sums = np.bincount(groups.ravel(), weights=excess.ravel(), minlength=len(stats))
    if len(sums) <= 1:
        return 0.0, 0.0, [0, 0, 0, 0]
    index = 1 + int(np.argmax(sums[1:]))
    x, y, w, h, area = map(int, stats[index])
    return float(sums[index]), area / mask.size, [x, y, x + w, y + h]


def scan(movie):
    rule = T["visibility_pop"]
    cap = cv2.VideoCapture(str(movie))
    frames = deque(maxlen=3)
    rows = []
    try:
        while True:
            ok, data = cap.read()
            if not ok:
                break
            h, w = data.shape[:2]
            top, bottom = round(0.26 * h), round(0.72 * h)
            gray = cv2.cvtColor(
                cv2.resize(data[top:bottom], (320, 220), interpolation=cv2.INTER_AREA),
                cv2.COLOR_BGR2GRAY,
            )
            frames.append(cv2.GaussianBlur(gray, (5, 5), 1.2).astype("float32"))
            if len(frames) == 3:
                rows.append(measure(*frames))
        if not rows:
            raise ValueError("too few readable frames for a flash check")
    finally:
        cap.release()
    found = []
    for i in range(2, len(rows) - 2):
        energy, area, box = rows[i]
        neighbours = [rows[i + k][0] for k in (-2, -1, 1, 2)]
        if (
            area < rule["min_area_fraction"]
            or energy < max(neighbours) * rule["isolation_ratio"]
        ):
            continue
        left, up, right, down = box
        scale = 1080 / w
        full_box = [
            round(left / 320 * 1080),
            round((top + up / 220 * (bottom - top)) * scale),
            round(right / 320 * 1080),
            round((top + down / 220 * (bottom - top)) * scale),
        ]
        found.append(
            dict(
                frame=i + 1,
                full_box=full_box,
                area_fraction=round(area, 4),
                energy=round(energy, 1),
            )
        )
    return found


def apply(movie, result, band_y=470):
    if "visibility_pops" in result:
        return
    found = scan(movie)
    result["visibility_pops"] = found
    for row in found:
        x0, y0, x1, y1 = row["full_box"]
        result["p0"].append(
            dict(
                frame=row["frame"],
                box=[x0, y0 - band_y, x1, y1 - band_y],
                source="measured single-frame flash",
                what=f"A localized region flashes and returns on the next frame at f{row['frame']} "
                f"({row['area_fraction']:.1%} of the anatomy band). Compare this box with the preceding and following frame. "
                "Repair the isolated visibility, shading or compositing change and verify the three-frame sequence.",
            )
        )
    if found:
        result["pass"] = False
        result["findings"] = [
            dict(priority=k, **p) for k in ("p0", "p1") for p in result[k]
        ]
