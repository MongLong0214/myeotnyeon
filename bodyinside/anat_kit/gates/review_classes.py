"""The same class-specific checklist is used to request and validate an Opus inspection."""

from pathlib import Path
import yaml

REGISTRY = Path(__file__).resolve().parents[1] / "defects.yaml"


def checklist(registry=REGISTRY, historical=False):
    return {
        row["id"]: row["description"]
        for row in yaml.safe_load(registry.read_text())
        if (
            row.get("enforcement") == {"type": "review", "check": "visual_review"}
            or (not historical and row.get("recurrence", {}).get("preflight") == "visual_review")
            or row.get("enforcement", {}).get("check")
            in (
                "skin_clear",
                "transition_ok",
                "on_landmark",
                "visibility_pop",
                "cord_clipped",
                "tool_contact",
            )
            or historical
            and row.get("enforcement", {}).get("check") == "phone_playback"
        )
    }


def review_failures(expected, result):
    """Every requested class needs exactly one disposition. Unseen and visible defects block."""
    states = {}
    for state in ("clear", "absent", "unseen", "defects"):
        for key in result.get(state, []):
            if key in states:
                raise ValueError(f"duplicate disposition for {key}")
            states[key] = state
    if set(states) != set(expected):
        raise ValueError(
            f"unexpected or missing classes: {sorted(set(expected) ^ set(states))}"
        )
    return {
        key: state for key, state in states.items() if state in ("defects", "unseen")
    }


# These require continuous playback or a soundtrack; they are checked on the movie.
MOVIE_ONLY = {
    "pose-step-at-caption-change",
    "transition-whips-through-figure",
    "sfx-without-matching-visual-event",
    "graphic-lags-caption",
    "single-frame-pop-or-flash",
    "camera-move-snaps-no-ease",
    "assembly-framerate-judder",
    "muscle-picture-ends-before-narration",
}
