"""Versioned visual settings. Only the renderer's supported presentation fields can change."""

import json
from pathlib import Path

VERSIONS = Path(__file__).with_name("templates") / "versions.json"


def versions():
    from improvement_log import records

    result = json.loads(VERSIONS.read_text())
    for event in records():
        if event["source"] == "promotion" and event.get("status") == "promoted":
            result[event["episode"]][event["version"]] = event["style"]
    return result


def apply_style(ep, style):
    if set(style) - {"note_transition", "label_layout"}:
        raise ValueError(
            "a visual revision may change note transitions and artwork placement"
        )
    if "note_transition" in style and style["note_transition"] != "fade_at_size":
        raise ValueError("unknown note transition")
    changes = style.get("label_layout", {})
    for label_id, props in changes.items():
        if (
            not props
            or set(props) - {"size", "dx", "dy"}
            or any(type(v) != int for v in props.values())
        ):
            raise ValueError(f"invalid note artwork settings for {label_id}")
        if "size" in props and props["size"] <= 0:
            raise ValueError("font size must be positive")
    for label in ep.get("labels", []):
        if label["kind"] == "note" and style.get("note_transition"):
            label["fade_at_size"] = True
        if label["kind"] in ("note", "callout"):
            label.update(changes.get(label["id"], {}))
    return ep


def versioned(ep, version=None):
    available = versions()[ep["template"]]
    version = version or next(reversed(available))
    ep["hook_type"] = {"neck_v3": "standing_phone", "wisdom": "jaw_touch"}[
        ep["template"]
    ]
    ep["template_version"] = version
    return apply_style(ep, available[version])
