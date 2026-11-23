"""Shot grammar and the three neck review 14 regressions, in full-resolution band pixels."""

import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from thresholds import T


def shots(ep):
    rows = ep.get("shots", [])
    end = round(ep["duration"] * ep["fps"])
    cursor = 0
    for row in rows:
        if (
            row["kind"] not in ("person", "anatomy", "dissolve")
            or row["f0"] != cursor
            or not cursor < row["f1"] <= end
        ):
            raise ValueError(f"invalid shot at frame {cursor}")
        cursor = row["f1"]
    if (
        cursor != end
        or rows[0]["kind"] != "person"
        or rows[0]["f1"] != round(ep["fps"] * T["human"]["opening_s"])
    ):
        raise ValueError(
            "cover the film without gaps; open on the person for exactly two seconds"
        )
    if (
        len(rows) < 3
        or rows[1]["kind"] != "dissolve"
        or not any(row["kind"] == "anatomy" for row in rows)
    ):
        raise ValueError("the opening person must dissolve into anatomy")
    return rows


def recurring_preflight():
    from review_classes import REGISTRY
    import yaml
    return {r["id"] for r in yaml.safe_load(REGISTRY.read_text()) if r.get("recurrence")}


def keyframes(ep):
    frames = {0, 3, 12, 15}
    for shot in shots(ep):
        a, b = shot["f0"], shot["f1"] - 1
        frames.update((a, (a + b) // 2, b))
        if shot["kind"] == "dissolve":
            frames.update(range(a, b + 1, 3))
    for beat in ep["beats"]:
        a, b = round(beat["t0"] * ep["fps"]), round(beat["t1"] * ep["fps"]) - 1
        frames.update((a, (a + b) // 2, b))
        for evidence in beat.get("evidence", []):
            frames.update(
                evidence[k] for k in ("f", "f0", "f1", "f_c", "f_rev") if k in evidence
            )
            frames.update(evidence.get("frames", []))
    for label in ep.get("labels", []):
        frames.update((label["f0"], (label["f0"] + label["f1"]) // 2, label["f1"]))
    frames.update(ep.get("payoff_frames", []))
    last = round(ep["duration"] * ep["fps"]) - 1
    if any(type(frame) is not int or not 0 <= frame <= last for frame in frames):
        raise ValueError(f"shot or evidence frame outside the movie (0–{last})")
    return sorted(frames)


def skin_clear(measurement):
    return not measurement["renderable_face_bones"]


def on_landmark(measurement):
    return (
        measurement["visible"]
        and math.dist(measurement["label_px"], measurement["landmark_px"])
        <= T["shot_checks"]["landmark_radius_px"]
    )


def transition_area(path):
    pixels = np.asarray(Image.open(path).convert("RGBA"))
    visible = (pixels[:, :, 3] > 40) & (pixels[:, :, :3].max(axis=2) > 45)
    groups, _ = ndimage.label(visible)
    counts = np.bincount(groups.ravel())[1:]
    return float(counts.max(initial=0) / visible.size)


def transition_ok(path):
    return transition_area(path) >= T["shot_checks"]["min_transition_area"]


def surface_exposed(sample):
    return (
        bool(sample["expected"])
        and sample["in_frame"]
        and sample["front"] == sample["expected"]
        and sample["distance_m"] is not None
        and sample["distance_m"] <= T["shot_checks"]["landmark_visibility_depth_m"]
    )


def cord_clipped(measurement):
    return (
        measurement.get("cord_zfade") is True
        and measurement.get("rest_floor_m", -math.inf)
        >= T["shot_checks"]["astra_neck_cord_stop_m"] - 1e-5
    )


def inspect(ep, frames, measured, frame_dir):
    errors = []
    if measured.get("_cord") is not None and not cord_clipped(measured["_cord"]):
        errors.append(["scene", "cord-rod-below-last-vertebra", measured["_cord"]])
    for shot in shots(ep):
        for f in frames:
            if not shot["f0"] <= f < shot["f1"]:
                continue
            if shot["kind"] == "person":
                sample = measured[str(f)]
                if sample["skin_alpha"] < 0.6:
                    errors.append(
                        [f, "establishing-person-opacity", sample["skin_alpha"]]
                    )
                if not skin_clear(sample):
                    errors.append(
                        [f, "skull-through-skin", sample["renderable_face_bones"]]
                    )
            for dot in measured.get(str(f), {}).get("dots", []):
                if not on_landmark(dot):
                    errors.append([f, "landmark-wrong-after-view-change", dot])
            for surface in measured.get(str(f), {}).get("surfaces", []):
                if not surface_exposed(surface):
                    errors.append([f, "callout-hidden-by-foreground-geometry", surface])
            if shot["kind"] == "dissolve":
                path = Path(frame_dir) / f"f_{f:04d}.png"
                area = transition_area(path)
                if area < T["shot_checks"]["min_transition_area"]:
                    errors.append([f, "degenerate-payoff-transition", round(area, 4)])
    return {"ok": not errors, "violations": errors, "frames": len(frames)}
