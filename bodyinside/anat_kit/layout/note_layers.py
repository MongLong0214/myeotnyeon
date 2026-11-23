"""Keep identical note artwork on one layer through a beat boundary."""


def note_layers(labels):
    # Preserve the compositing order of other artwork and the original list for legacy episodes.
    notes = [l for l in labels if l["kind"] == "note" and l.get("fade_at_size")]
    if not notes:
        return labels
    merged, last = {}, {}
    for label in sorted(notes, key=lambda l: l["f0"]):
        key = tuple(label.get(k) for k in ("text", "sub", "dx", "dy", "size"))
        prior = last.get(key)
        if prior and label["f0"] <= prior["f1"] + 1:
            if label["f1"] >= prior["f1"]:
                prior.update(
                    f1=label["f1"],
                    ramp_out=label.get("ramp_out", label.get("ramp", 14)),
                )
            merged[label["id"]] = None
        else:
            last[key] = merged[label["id"]] = dict(label)
    return [
        merged.get(l["id"], l) for l in labels if merged.get(l["id"], l) is not None
    ]


def stable_notes(ep):
    shrinking, hard_cuts = [], []
    last_frame = round(ep.get("duration", 0) * ep.get("fps", 0)) - 1
    for note in note_layers(ep.get("labels", [])):
        if note["kind"] != "note":
            continue
        entering = note.get("ramp", 14)
        leaving = note.get("ramp_out", entering)
        if not note.get("fade_at_size") and (entering or leaving):
            shrinking.append(note["id"])
        if (note["f0"] > 0 and not entering) or (
            note["f1"] != last_frame and not leaving
        ):
            hard_cuts.append(note["id"])
    return not (shrinking or hard_cuts), {
        "scaling_notes": shrinking,
        "hard_cuts": hard_cuts,
    }
