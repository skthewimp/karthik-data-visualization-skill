"""Recommend which points on a series to label directly - not how to place them.

"Keep every visible value" is a request to *preserve* every value in the data (so the chart
is reconstructable and honest), not to *print* every value as ink. Stamping a label on every
point is the fastest way to a collided, unreadable chart - the exact failure this prevents.

Given each series' values, this returns the few indices worth labelling: the endpoints (where
a series starts and ends), the extremes (its high and low), and the largest step-to-step
changes (the focal moves the reader should see), capped at a per-series budget. Values that do
not earn a label still live in the data table or a note; they are preserved, just not inked.

Mechanism only. It never invents a value and never decides the chart's form.
"""

from __future__ import annotations

from typing import Any, Sequence


def _finite(values: Sequence[Any]) -> list[tuple[int, float]]:
    """Index/value pairs for the finite numbers in ``values`` (skips None / non-numeric)."""
    pairs: list[tuple[int, float]] = []
    for index, value in enumerate(values):
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")):
            pairs.append((index, number))
    return pairs


def _pick_one_series(values: Sequence[Any], budget: int) -> dict[str, Any]:
    pairs = _finite(values)
    total = len(pairs)
    reasons: dict[int, str] = {}

    if total == 0:
        return {"label_indices": [], "reasons": {}, "labelled": 0, "total": 0}

    # A short series is read whole; label every point rather than hide any.
    if total <= budget:
        for index, _ in pairs:
            reasons[index] = "all (series short enough to read whole)"
        chosen = [index for index, _ in pairs]
        return {"label_indices": chosen, "reasons": reasons, "labelled": len(chosen), "total": total}

    def claim(index: int, reason: str) -> None:
        reasons.setdefault(index, reason)

    # Endpoints first - they are where the reader enters and leaves the line.
    claim(pairs[0][0], "endpoint (start)")
    claim(pairs[-1][0], "endpoint (end)")
    # Extremes - the high and the low carry the range.
    claim(max(pairs, key=lambda p: p[1])[0], "maximum")
    claim(min(pairs, key=lambda p: p[1])[0], "minimum")

    # Fill any remaining budget with the largest step-to-step changes - the focal moves.
    changes = sorted(
        (
            (abs(pairs[i + 1][1] - pairs[i][1]), pairs[i + 1][0])
            for i in range(len(pairs) - 1)
        ),
        reverse=True,
    )
    for _, index in changes:
        if len(reasons) >= budget:
            break
        claim(index, "focal change")

    chosen = sorted(reasons)[:budget]
    reasons = {index: reasons[index] for index in chosen}
    return {"label_indices": chosen, "reasons": reasons, "labelled": len(chosen), "total": total}


def recommend_labels(
    series: list[dict[str, Any]],
    max_labels_per_series: int = 4,
) -> dict[str, Any]:
    """Recommend the indices to label directly on each series.

    Args:
        series: one entry per series, ``{id, values:[...]}``; ``values`` is the ordered numeric
            sequence (missing / non-numeric entries are skipped, their positions preserved).
        max_labels_per_series: the per-series label budget. Endpoints and extremes are claimed
            first, then the largest changes fill what is left. A series with no more points than
            the budget is labelled in full.

    Returns per-series ``label_indices`` (which points to ink) with a ``reasons`` map, plus a
    ``principle`` line. It selects points; it does not place them - feed the chosen anchors to
    ``recommend_text_placement`` to wrap and de-collide them.
    """
    budget = max(1, int(max_labels_per_series))
    per_series: list[dict[str, Any]] = []
    for entry in series:
        picked = _pick_one_series(entry.get("values", []), budget)
        picked["id"] = entry.get("id")
        per_series.append(picked)

    return {
        "per_series": per_series,
        "max_labels_per_series": budget,
        "principle": (
            "Preserve every value in the data (table or note); print only these direct labels. "
            "Endpoints and extremes anchor the read, the largest changes show the focal moves; "
            "labelling every point collides and is not what 'keep every value' asks for."
        ),
    }
