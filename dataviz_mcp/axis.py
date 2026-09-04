"""Recommend a fitted value-axis range for a continuous scale.

The axis range is a data decision keyed to the plotted extent, not to the measure's
natural domain: a percentage that runs 1-44 earns an axis to ~48, never a reflexive
0-100. The upper bound sits just above the largest plotted value with small
nice-number headroom; the lower bound is 0 for a zero-based encoding (bars,
share-of-total, a compared reference) or a nice number just below the smallest value
for a movement-band line. No dead band above the data, no unit ceiling stamped on as
the maximum. The judgment - is this a continuous value axis, is it zero-based, is a
hard bound genuinely the point - is made at selection; this tool resolves the
numbers, so a weaker build model never has to guess "percentages go to 100".
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence


def _nice_num(x: float, round_: bool) -> float:
    """Nearest 1/2/5 x 10^k to ``x`` - rounded to the closest such number, or up (round_=False)."""
    if x <= 0:
        return 0.0
    exp = math.floor(math.log10(x))
    frac = x / (10.0 ** exp)
    if round_:
        nice = 1.0 if frac < 1.5 else 2.0 if frac < 3.0 else 5.0 if frac < 7.0 else 10.0
    else:
        nice = 1.0 if frac <= 1.0 else 2.0 if frac <= 2.0 else 5.0 if frac <= 5.0 else 10.0
    return nice * (10.0 ** exp)


def _clean(value: float) -> float | int:
    """Strip float noise; return an int when the value is integral."""
    rounded = round(value, 9)
    if abs(rounded - round(rounded)) < 1e-9:
        return int(round(rounded))
    return rounded


def _breaks(lo: float, hi: float, step: float) -> list[float | int]:
    """Aligned multiples of ``step`` within [lo, hi], with both endpoints always present."""
    ticks: set[float] = {round(lo, 9), round(hi, 9)}
    start = math.ceil(round(lo / step, 9)) * step
    value = start
    while value <= hi + 1e-9:
        if value >= lo - 1e-9:
            ticks.add(round(value, 9))
        value += step
    return sorted(_clean(tick) for tick in ticks)


def recommend_axis_range(
    values: Sequence[float],
    zero_based: bool = True,
    hard_min: Optional[float] = None,
    hard_max: Optional[float] = None,
    target_breaks: int = 5,
) -> dict[str, Any]:
    """Recommend a fitted [min, max] and breaks for a continuous value axis.

    Args:
        values: the plotted values the axis must contain (all of them, or just the
            extremes). The range is fitted to this extent, never to the measure's
            natural domain (a percentage is not 0-100 unless the data reaches it).
        zero_based: True (default) includes 0 - bars, share-of-total, or a line whose
            absolute level is the point. Set False for a line whose story is movement
            in a narrow band, where a zero baseline would flatten it; the low bound
            then sits just below the smallest value. The caller (select stage) owns
            this judgment; the tool only resolves the numbers.
        hard_min / hard_max: an explicit bound to honour - a genuine domain floor, or
            a full range (e.g. 0-100) when that range is genuinely the point. Applied
            exactly and flagged, so the override is never silent. Leave unset for the
            default fitted behaviour.
        target_breaks: approximate number of gridline/tick intervals to aim for.

    Returns a dict with the recommended bounds, aligned breaks, the headroom above
    the data as a fraction of the axis span, override flags, and a rationale.
    """
    numbers = [
        float(v)
        for v in values
        if v is not None and not (isinstance(v, float) and math.isnan(v))
    ]
    if not numbers:
        raise ValueError("values must contain at least one finite number")
    if target_breaks < 2:
        raise ValueError("target_breaks must be at least 2")

    data_min = min(numbers)
    data_max = max(numbers)

    lo_hard = hard_min is not None
    hi_hard = hard_max is not None
    lo_anchor = float(hard_min) if lo_hard else (min(0.0, data_min) if zero_based else data_min)
    hi_anchor = float(hard_max) if hi_hard else data_max

    # Degenerate extent (all values equal, or a single value): open a band around the value so
    # the axis is never zero-width, keyed to the value's own magnitude.
    if hi_anchor - lo_anchor <= 0:
        magnitude = abs(data_max) if data_max != 0 else 1.0
        pad = _nice_num(magnitude, True)
        if not hi_hard:
            hi_anchor = data_max + pad
        if not lo_hard:
            lo_anchor = 0.0 if (zero_based and data_min >= 0) else data_min - pad

    step = _nice_num((hi_anchor - lo_anchor) / (target_breaks - 1), True) or 1.0
    nice_min = lo_anchor if lo_hard else math.floor(lo_anchor / step) * step
    nice_max = hi_anchor if hi_hard else math.ceil(hi_anchor / step) * step
    # A ceil that lands exactly on the largest value leaves the top mark on the frame edge;
    # add one step of headroom so it breathes, matching plotting-library "expand" behaviour.
    if not hi_hard and nice_max <= data_max:
        nice_max += step

    # Re-derive the step across the final frame so the breaks divide it evenly.
    step = _nice_num((nice_max - nice_min) / (target_breaks - 1), True) or 1.0
    breaks = _breaks(nice_min, nice_max, step)

    axis_span = nice_max - nice_min
    headroom = (nice_max - data_max) / axis_span if axis_span > 0 else 0.0

    baseline = "zero baseline included" if zero_based else "movement-band (no zero baseline)"
    rationale = (
        f"axis fitted to data extent [{_clean(data_min)}, {_clean(data_max)}]: "
        f"[{_clean(nice_min)}, {_clean(nice_max)}], {baseline}. "
        f"Upper bound is a nice number just above the largest value "
        f"({headroom:.0%} headroom); the measure's natural domain is not the axis maximum."
    )
    if lo_hard or hi_hard:
        which = " and ".join(
            part for part, flag in (("min", lo_hard), ("max", hi_hard)) if flag
        )
        rationale += f" Hard {which} applied as given - override honoured, not the fitted value."
    if hi_hard and headroom > 0.35:
        rationale += (
            f" Warning: the hard max leaves {headroom:.0%} of the axis empty above the data - "
            "confirm the full range is genuinely the point rather than a reflexive unit ceiling."
        )

    return {
        "recommended_min": _clean(nice_min),
        "recommended_max": _clean(nice_max),
        "breaks": breaks,
        "step": _clean(step),
        "zero_based": zero_based,
        "data_min": _clean(data_min),
        "data_max": _clean(data_max),
        "headroom_fraction": round(headroom, 3),
        "hard_min_applied": lo_hard,
        "hard_max_applied": hi_hard,
        "rationale": rationale,
    }
