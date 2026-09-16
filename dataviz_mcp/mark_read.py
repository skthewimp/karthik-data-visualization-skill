"""Convert bracketed chart-mark positions into values - the deterministic half of a read.

Reading a value off a chart splits into a perception step and an arithmetic step.
The model does the perception it is good at: for a mark with no printed label, it
names the two nearest printed reference ticks that bracket the mark and the fraction
(0-1) of the way from the lower tick to the upper one. This tool does the arithmetic
the model is bad at - interpolating that bracket, linearly or in log space - so an
eyeballed absolute magnitude (biased toward round numbers, worse on a log axis) never
enters the table. The perception stays with the reader; only the scale math is here.

No precision is fabricated: the raw interpolated float is returned and rounding is a
separate downstream decision (``recommend_precision``).
"""

from __future__ import annotations

import math
from typing import Any, Sequence


def _interpolate(lo: float, hi: float, fraction: float, transform: str) -> float:
    if transform == "log":
        return 10.0 ** (math.log10(lo) + fraction * (math.log10(hi) - math.log10(lo)))
    return lo + fraction * (hi - lo)


def read_marks_from_anchors(
    marks: Sequence[dict[str, Any]],
    transform: str = "linear",
) -> dict[str, Any]:
    """Interpolate each bracketed mark position into a value.

    Args:
        marks: one entry per unlabelled cell, each a dict with:
            ``key`` - an identifier carried through to the result (e.g. "2019|series 3");
            ``lo`` / ``hi`` - the two bracketing printed tick VALUES the mark sits between;
            ``fraction`` - the mark's position from ``lo`` to ``hi``, 0-1.
        transform: "linear" (default) or "log" - the axis's own scale. Log interpolates
            between the ticks in log10 space; both anchors must be strictly positive.

    Returns a dict with ``transform``, a ``results`` list of ``{key, value, ...}`` (value
    is ``None`` for a mark that could not be interpolated), and a ``warnings`` list. Order
    and count of results match the input. ``fraction`` runs from ``lo`` to ``hi`` as named,
    so a descending bracket (``hi < lo``, a reversed axis) reads correctly with no special
    handling. Guards, none silent:
      * equal anchors cannot define a bracket and yield a ``None`` value.
      * ``fraction`` outside [0,1] is honoured, not clamped: a mark just past the nearest
        tick (a series minimum below the lowest gridline, a labelled peak above the top one)
        is a legitimate short extrapolation, so the value is computed from the fraction as
        given. Only a fraction far outside the bracket (< -1 or > 2) is flagged as a probable
        wrong-bracket choice - and even then the extrapolated value is still returned, never
        dropped.
      * log with a non-positive anchor yields a ``None`` value (with a warning).
    """
    if transform not in ("linear", "log"):
        raise ValueError(f"transform must be 'linear' or 'log', got {transform!r}")

    results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for index, mark in enumerate(marks):
        key = mark.get("key", index)
        try:
            lo = float(mark["lo"])
            hi = float(mark["hi"])
            fraction = float(mark["fraction"])
        except (KeyError, TypeError, ValueError):
            warnings.append(f"{key}: missing or non-numeric lo/hi/fraction; skipped.")
            results.append({"key": key, "value": None})
            continue

        if lo == hi:
            warnings.append(f"{key}: equal anchors ({lo}) cannot define a bracket; skipped.")
            results.append({"key": key, "value": None})
            continue

        if fraction < -1.0 or fraction > 2.0:
            warnings.append(
                f"{key}: fraction {fraction} far outside the bracket (likely wrong ticks chosen); "
                "extrapolated value returned - check the anchors."
            )

        if transform == "log" and (lo <= 0.0 or hi <= 0.0):
            warnings.append(f"{key}: log transform needs positive anchors (lo={lo}, hi={hi}); skipped.")
            results.append({"key": key, "value": None})
            continue

        value = _interpolate(lo, hi, fraction, transform)
        results.append({"key": key, "value": value, "lo": lo, "hi": hi, "fraction": fraction})

    return {"transform": transform, "results": results, "warnings": warnings}
