"""Recommend whether a continuous axis should be plotted on a log scale.

A log axis is a data decision keyed to the spread and the shape of the
distribution, not a default. It earns its place when positive values span many
orders of magnitude and a linear axis would saturate on the large values and
crush the small ones into an indistinguishable baseline - and when the marks
encode *position*, not *length* (a bar or area on a log axis breaks the
proportional read a length encoding promises and has no honest zero).

The recommendation is advisory and graded: the tool returns continuous signals
and a strength, never a hard regime table. The caller (a model step in the
selector) reads it as one input and can override it - the prompt may ask for
absolute magnitudes, the audience may not read a log axis, or it may mislead.
Log-only for now: when the data has non-positive values, log10 cannot apply and
the tool says so, noting that symlog/log1p exist without recommending them.
"""

from __future__ import annotations

import math
from typing import Any, Sequence


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolated percentile (q in 0..1) of an already-sorted list."""
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def _bowley_skew(values: list[float]) -> float:
    """Quartile (Bowley) skew in -1..1; robust, needs no assumption about the tail."""
    s = sorted(values)
    q1, q2, q3 = _percentile(s, 0.25), _percentile(s, 0.5), _percentile(s, 0.75)
    spread = q3 - q1
    if spread == 0:
        return 0.0
    return (q3 + q1 - 2 * q2) / spread


def _saturating(x: float, scale: float) -> float:
    """Smooth 0..1 ramp, 0 at x=0, rising with no cliff (scale sets how fast)."""
    return 1.0 - math.exp(-max(0.0, x) / scale)


def recommend_scale_transform(
    values: Sequence[float],
    encoding: str = "position",
) -> dict[str, Any]:
    """Recommend a linear vs log10 transform for the continuous axis carrying `values`.

    Args:
        values: every numeric value that maps to the axis (raw observations for a
            boxplot/points, the plotted magnitudes for lines). Flat list across groups.
        encoding: "position" (points, lines, dot plots, box/violin - position carries
            the value) or "length" (bars, area - length carries the value and needs a
            true zero, so log is almost always wrong).

    Returns the recommendation, the ``transform`` scalar the builder branches on,
    a continuous ``strength`` and coarse ``confidence``, the computed ``signals``,
    a one-line ``rationale``, and ``caveats`` the model must weigh before it commits.
    """
    numbers = [float(v) for v in values if v is not None and math.isfinite(v)]
    base = {"encoding": encoding, "recommendation": "linear", "transform": "identity"}

    if len(numbers) < 2:
        return {**base, "strength": 0.0, "confidence": "weak", "applicable": False,
                "signals": {}, "rationale": "too few finite values to judge spread",
                "caveats": []}

    positives = [v for v in numbers if v > 0]
    n_nonpos = len(numbers) - len(positives)
    lo, hi = min(numbers), max(numbers)
    min_pos = min(positives) if positives else math.nan
    dynamic_range = (max(positives) / min_pos) if positives and min_pos > 0 else math.nan
    orders = math.log10(dynamic_range) if dynamic_range and math.isfinite(dynamic_range) else 0.0
    skew_raw = _bowley_skew(numbers)
    skew_log = _bowley_skew([math.log10(v) for v in positives]) if len(positives) >= 2 else 0.0
    skew_reduction = abs(skew_raw) - abs(skew_log)

    signals = {
        "n": len(numbers), "n_nonpositive": n_nonpos, "min": lo, "max": hi,
        "min_positive": min_pos, "dynamic_range": dynamic_range,
        "orders_of_magnitude": orders, "bowley_skew_raw": skew_raw,
        "bowley_skew_log": skew_log, "skew_reduction": skew_reduction,
    }
    common = {"encoding": encoding, "signals": signals}

    # Log10 cannot apply to non-positive data. Report, do not recommend a substitute.
    if n_nonpos > 0:
        result = {**base, **common, "strength": 0.0, "confidence": "n/a", "applicable": False,
                  "rationale": f"{n_nonpos} non-positive value(s): log10 does not apply",
                  "caveats": []}
        if positives and orders >= 2:
            result["symlog_note"] = ("data has non-positive values but the positive part is "
                                     "wide-spread; symlog/log1p exist but are not recommended here "
                                     "- decide by hand if the small values must read")
        return result

    # Length encodings (bars, area) need a true zero; a log axis breaks proportionality.
    if encoding == "length":
        return {**base, **common, "strength": 0.0, "confidence": "strong", "applicable": True,
                "rationale": "length encoding needs a true zero; a log axis breaks the "
                             "proportional read - switch to a position mark (points/dots) if "
                             "the spread genuinely needs log",
                "caveats": ["If the spread is the story, change the mark before the scale."]}

    # Position encoding: grade continuously on spread, modulated by log-symmetrisation.
    range_strength = _saturating(orders, 1.5)
    skew_bonus = _saturating(skew_reduction, 0.5)
    strength = range_strength * (0.6 + 0.4 * skew_bonus)
    recommend_log = strength >= 0.5
    confidence = "strong" if strength >= 0.65 else "moderate" if strength >= 0.4 else "weak"

    caveats = [
        "Advisory - override if the prompt wants absolute magnitudes, the audience won't "
        "read a log axis, or it would mislead.",
    ]
    if recommend_log:
        caveats += [
            "Label the axis as log and keep tick labels in untransformed units.",
            "A log axis reads equal spacing as equal ratio, not equal difference - only right "
            "when the reader should think multiplicatively.",
        ]

    rationale = (
        f"positive values span {orders:.1f} orders of magnitude"
        + (f" and logging reduces skew by {skew_reduction:.2f}" if skew_reduction > 0.05 else "")
        + (" - a linear axis would crush the small values" if recommend_log
           else " - not wide enough to need log")
    )

    return {
        "encoding": encoding, "signals": signals,
        "recommendation": "log" if recommend_log else "linear",
        "transform": "log10" if recommend_log else "identity",
        "strength": round(strength, 3), "confidence": confidence, "applicable": True,
        "rationale": rationale, "caveats": caveats,
    }
