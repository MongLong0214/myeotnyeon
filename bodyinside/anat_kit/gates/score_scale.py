"""Map blind Opus ratings to the historical editorial scale."""

import math
from collections import defaultdict

import numpy as np
from scipy.optimize import lsq_linear

AREAS = ("anatomy", "cutaway", "motion", "labels", "hook", "facts", "audio")


def predict(raw, coefficients, scores=None):
    """Use the fitted range; taper to the original scale at the rubric endpoints."""
    if not coefficients:
        adjusted = raw
    else:
        estimate = raw * coefficients["slope"] + coefficients["intercept"]
        for area, coefficient in coefficients.get("areas", {}).items():
            estimate += scores[area] * coefficient
        low, high = coefficients["raw_support"]
        weight = 1
        if raw < low:
            weight = max(0, (raw - 1) / (low - 1)) if low > 1 else 0
        elif raw > high:
            anchor = coefficients["upper_anchor"]
            weight = max(0, (anchor - raw) / (anchor - high)) if high < anchor else 0
        adjusted = raw + weight * (estimate - raw)
    return max(1.0, min(10.0, math.floor(2 * adjusted + 1e-10) / 2))


def _fit(rows, penalty):
    raw = np.array([r["raw"] for r in rows])
    target = np.array([r["target"] for r in rows])
    areas = AREAS if penalty else ()
    features = np.asarray(
        [[r["raw"], *[r["scores"][key] for key in areas]] for r in rows]
    )
    xbar = features.mean(axis=0)
    centered = features - xbar
    y = target - target.mean()
    if penalty:
        # Regularize towards the original Opus editorial scale, retaining
        # nonnegative coefficients for every quality axis.
        prior = np.zeros(len(areas) + 1)
        prior[0] = 1
        centered = np.vstack([centered, math.sqrt(penalty) * np.eye(len(prior))])
        y = np.concatenate([y, math.sqrt(penalty) * prior])
    coeff = lsq_linear(centered, y, bounds=(0, np.inf)).x
    return {
        "slope": float(coeff[0]),
        "intercept": float(target.mean() - xbar @ coeff),
        "areas": {key: float(c) for key, c in zip(areas, coeff[1:])},
        "raw_support": [float(raw.min()), float(raw.max())],
        "upper_anchor": 9.5,
    }


def fit(rows):
    """Choose the model by leave-one-review-out MAE within the development set."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["review"]].append(row)
    if len(groups) < 3:
        return _fit(rows, 0)
    errors = {}
    for penalty in (0, 16, 4, 1):
        residual = []
        for review, validation in groups.items():
            params = _fit(
                [r for key, group in groups.items() if key != review for r in group],
                penalty,
            )
            residual.extend(
                abs(predict(r["raw"], params, r["scores"]) - r["target"])
                for r in validation
            )
        errors[penalty] = sum(residual) / len(residual)
    best = min(errors, key=errors.get)
    return dict(_fit(rows, best), development_cv_mae=errors, ridge_penalty=best)


def metrics(errors):
    return {
        "n": len(errors),
        "within_half": sum(abs(e) <= 0.5 for e in errors),
        "mae": round(sum(map(abs, errors)) / len(errors), 3) if errors else None,
        "max_error": max(map(abs, errors), default=None),
    }
