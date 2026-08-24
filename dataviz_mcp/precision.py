"""Recommend significant digits / rounding for a column of numbers.

Precision is a data decision keyed to the spread, not to individual values: the
number of significant digits is derived from the range (max - min), and every
value in the column is rounded to one uniform decimal place so digit-length reads
as magnitude. No fabricated precision, no rounding toward rounder-sounding numbers.
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence


def _floor_log10(value: float) -> int:
    return int(math.floor(math.log10(abs(value))))


def _format_value(value: float, place: int) -> str:
    """Round `value` to the 10**place grid and format with a thousands separator."""
    step = 10.0 ** place
    rounded = round(value / step) * step
    decimals = max(0, -place)
    return f"{rounded:,.{decimals}f}"


def _exact_decimals(numbers: Sequence[float], cap: int = 10) -> int:
    """Smallest decimal count that shows every value without dropping a digit."""
    decimals = 0
    for value in numbers:
        needed = 0
        while needed < cap and round(value, needed) != value:
            needed += 1
        decimals = max(decimals, needed)
    return decimals


def recommend_precision(
    values: Sequence[float],
    role: str = "axis",
    target_steps: int = 2,
    smallest_meaningful_difference: Optional[float] = None,
    exact: bool = False,
) -> dict[str, Any]:
    """Recommend a uniform rounding place and significant-digit count for `values`.

    Args:
        values: the numeric column / axis ticks / data labels to be shown together.
        role: "axis", "label", or "table_column" - reported back, shapes the rationale.
        target_steps: how many significant figures of the *range* the reader needs to
            just about resolve the information (default 2).
        smallest_meaningful_difference: if the caller knows the smallest difference that
            matters (d), the place is taken from it directly instead of from the range.
        exact: override the spread rule and preserve every source digit. Use ONLY for
            identifiers or a genuine exact-lookup requirement (account numbers, precise
            reference values a reader must read off verbatim). The result is flagged
            ``exact_override`` so the caller must record why it left the default behind.

    Returns a dict with the recommended place, significant digits, per-value preview,
    a one-line rationale, and an ``exact_override`` flag.
    """
    numbers = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not numbers:
        return {
            "role": role,
            "error": "no finite values supplied",
            "recommended_place": None,
            "significant_digits": None,
            "preview": [],
            "exact_override": exact,
            "rationale": "Nothing to format: the column has no finite values.",
        }

    if exact:
        place = -_exact_decimals(numbers)
        step = 10.0 ** place
        largest = max(abs(v) for v in numbers)
        sig_digits = max(1, (_floor_log10(largest) - place + 1) if largest > 0 else 1)
        decimals = max(0, -place)
        preview = [{"value": value, "shown": _format_value(value, place)} for value in numbers]
        rationale = (
            f"{role}: EXACT override - every source digit preserved, spread rule bypassed. "
            "Only valid for identifiers or a genuine exact-lookup requirement; record the reason."
        )
        return {
            "role": role,
            "recommended_place": place,
            "step": step,
            "significant_digits": sig_digits,
            "decimals": decimals,
            "range": max(numbers) - min(numbers),
            "smallest_resolved_difference": step,
            "preview": preview,
            "exact_override": True,
            "rationale": rationale,
        }

    lo, hi = min(numbers), max(numbers)
    spread = hi - lo

    if smallest_meaningful_difference and smallest_meaningful_difference > 0:
        place = _floor_log10(smallest_meaningful_difference)
        basis = f"smallest meaningful difference {smallest_meaningful_difference:g}"
    elif spread > 0:
        place = _floor_log10(spread) - (target_steps - 1)
        basis = f"range {spread:g} (max {hi:g} - min {lo:g})"
    else:
        # Every value identical: key precision to the value's own magnitude.
        magnitude = hi if hi != 0 else 1.0
        place = _floor_log10(magnitude) - (target_steps - 1)
        basis = f"single magnitude {hi:g} (all values equal)"

    step = 10.0 ** place
    largest = max(abs(lo), abs(hi))
    sig_digits = (_floor_log10(largest) - place + 1) if largest > 0 else 1
    sig_digits = max(1, sig_digits)

    preview = [{"value": value, "shown": _format_value(value, place)} for value in numbers]
    decimals = max(0, -place)
    place_word = _place_word(place)

    rationale = (
        f"{role}: {basis} -> round every value to the {place_word} "
        f"({sig_digits} significant digit(s), {decimals} decimal place(s)). "
        "Uniform place across the column; no precision the spread cannot support."
    )

    return {
        "role": role,
        "recommended_place": place,
        "step": step,
        "significant_digits": sig_digits,
        "decimals": decimals,
        "range": spread,
        "smallest_resolved_difference": step,
        "preview": preview,
        "exact_override": False,
        "rationale": rationale,
    }


def _place_word(place: int) -> str:
    names = {
        9: "billions",
        6: "millions",
        3: "thousands",
        2: "hundreds",
        1: "tens",
        0: "units",
    }
    if place in names:
        return names[place]
    if place > 0:
        return f"10^{place}"
    return f"{-place} decimal place(s)"
