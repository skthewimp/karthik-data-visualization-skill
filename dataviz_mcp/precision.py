"""Recommend significant digits / rounding for a column of numbers.

Precision is a data decision keyed to the spread, not to individual values: the
number of significant digits is derived from the range (max - min), and every
value in the column is rounded to one uniform decimal place so digit-length reads
as magnitude. No fabricated precision, no rounding toward rounder-sounding numbers.

Every result also carries a compact form in the largest short-scale unit (K / M / B / T)
the column's magnitude supports, at the same resolved place: $70,398MM with a spread of
6,866 reads as "70.4B", not "70,400". That is the form for a title, subtitle or annotation.
"""

from __future__ import annotations

import math
import re
from typing import Any, Optional, Sequence


def _floor_log10(value: float) -> int:
    return int(math.floor(math.log10(abs(value))))


def _format_value(value: float, place: int) -> str:
    """Round `value` to the 10**place grid and format with a thousands separator."""
    step = 10.0 ** place
    rounded = round(value / step) * step
    decimals = max(0, -place)
    return f"{rounded:,.{decimals}f}"


_COMPACT_SUFFIXES = {0: "", 3: "K", 6: "M", 9: "B", 12: "T"}


def _compact_format(value: float, base_place: int, exponent: int) -> str:
    """Round a base-unit value to 10**base_place, then show it in 10**exponent units."""
    rounded = round(value / 10.0 ** base_place) * 10.0 ** base_place
    decimals = max(0, exponent - base_place)
    return f"{rounded / 10.0 ** exponent:,.{decimals}f}{_COMPACT_SUFFIXES[exponent]}"


def _attach_compact(
    result: dict[str, Any], numbers: Sequence[float], place: int, unit_multiplier: float
) -> dict[str, Any]:
    """Add the short-scale form of every value at the already-resolved place.

    ``unit_multiplier`` is how many base units one source unit is (1e6 for a column in
    millions). The suffix is the largest power of 1,000 at or below the column's largest
    magnitude that needs at most two decimals at this place and still suits the smallest value, so every value in the column shares one unit; the decimals follow from the
    place, so no digit the spread rule dropped comes back and none it kept is lost.
    """
    shift = round(math.log10(unit_multiplier)) if unit_multiplier > 0 else 0
    base_place = place + shift
    largest = max(abs(v) for v in numbers) * 10.0 ** shift
    exponent = min(12, max(0, (_floor_log10(largest) // 3) * 3)) if largest >= 1000 else 0
    # Never trade a separator for a long decimal tail: when the place is finer than the unit
    # (a small value kept beside large ones), stay in a unit that needs at most two decimals.
    exponent = min(exponent, max(0, ((base_place + 2) // 3) * 3))
    # One unit must suit the whole column: step down while the smallest nonzero value would
    # read as a leading-zero fraction of it (11 beside 1,653 is "10", not "0.01K").
    smallest = min((abs(v) for v in numbers if v != 0), default=0.0) * 10.0 ** shift
    while exponent > 0 and smallest < 0.1 * 10.0 ** exponent:
        exponent -= 3
    for item in result["preview"]:
        item["compact"] = _compact_format(item["value"] * 10.0 ** shift, base_place, exponent)
    result["unit_multiplier"] = 10.0 ** shift
    result["compact_suffix"] = _COMPACT_SUFFIXES[exponent]
    result["compact_step"] = _compact_format(10.0 ** base_place, base_place, exponent)
    return result


def _exact_decimals(numbers: Sequence[float], cap: int = 10) -> int:
    """Smallest decimal count that shows every value without dropping a digit."""
    decimals = 0
    for value in numbers:
        needed = 0
        while needed < cap and round(value, needed) != value:
            needed += 1
        decimals = max(decimals, needed)
    return decimals


def _parses_zero(shown: str) -> bool:
    """True when a formatted value reads as plain zero after stripping money/percent/separators."""
    stripped = shown
    for token in ("$", "€", "£", "%", ",", " ", "+", "−"):
        stripped = stripped.replace(token, "")
    try:
        return float(stripped) == 0.0
    except ValueError:
        return False


def recommend_precision(
    values: Sequence[float],
    role: str = "axis",
    target_steps: int = 2,
    smallest_meaningful_difference: Optional[float] = None,
    exact: bool = False,
    unit_multiplier: float = 1.0,
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
        unit_multiplier: base units per source unit when the column is already scaled
            (1e6 for "$MM" or "in millions", 1e3 for "'000"). Only the compact form uses it.

    Returns a dict with the recommended place, significant digits, per-value preview
    (``shown`` in source units, ``compact`` in the short-scale unit for prose copy),
    ``compact_suffix``, a one-line rationale, and an ``exact_override`` flag.
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
        return _attach_compact(
            {
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
            },
            numbers,
            place,
            unit_multiplier,
        )

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

    # The source's own digits are a ceiling the spread rule can lower but never raise: integer
    # counts or shares spanning a narrow range stay integers, never "38.0".
    place = max(place, -_exact_decimals(numbers))
    step = 10.0 ** place
    largest = max(abs(lo), abs(hi))
    sig_digits = (_floor_log10(largest) - place + 1) if largest > 0 else 1
    sig_digits = max(1, sig_digits)

    preview = [{"value": value, "shown": _format_value(value, place)} for value in numbers]
    decimals = max(0, -place)

    # Zero-collapse guard: a nonzero value must never display as plain 0. This bites when a
    # value far smaller than the spread is shown (a small unit cost beside large counts, or a
    # single focal annotation); the coarse spread place would round it to "0". Refine the place
    # just enough to keep the smallest nonzero value one significant digit - never coarser than
    # the spread place, never finer than the source digits actually carry. Honest, not silent.
    zero_collapse_prevented = False
    nonzero = [value for value in numbers if value != 0]
    if nonzero and any(
        item["value"] != 0 and _parses_zero(item["shown"]) for item in preview
    ):
        smallest = min(abs(value) for value in nonzero)
        refined = max(min(place, _floor_log10(smallest)), -_exact_decimals(numbers))
        if refined < place:
            place = refined
            step = 10.0 ** place
            sig_digits = max(1, (_floor_log10(largest) - place + 1) if largest > 0 else 1)
            decimals = max(0, -place)
            preview = [{"value": value, "shown": _format_value(value, place)} for value in numbers]
            zero_collapse_prevented = True

    place_word = _place_word(place)
    rationale = (
        f"{role}: {basis} -> round every value to the {place_word} "
        f"({sig_digits} significant digit(s), {decimals} decimal place(s)). "
        "Uniform place across the column; no precision the spread cannot support."
    )
    if zero_collapse_prevented:
        rationale += (
            " Refined finer than the spread place: a nonzero value would otherwise display as 0, "
            "which is a fabricated zero - the smallest nonzero value now keeps a significant digit."
        )

    return _attach_compact(
        {
            "role": role,
            "recommended_place": place,
            "step": step,
            "significant_digits": sig_digits,
            "decimals": decimals,
            "range": spread,
            "smallest_resolved_difference": step,
            "preview": preview,
            "exact_override": False,
            "zero_collapse_prevented": zero_collapse_prevented,
            "rationale": rationale,
        },
        numbers,
        place,
        unit_multiplier,
    )


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


# A header that states its own scale ("Revenue ($MM)", "Sales, in billions", "Units '000").
# Single letters count only right after a currency sign, so "(m)" for metres is left alone.
_HEADER_SCALES = (
    (re.compile(r"\btrillions?\b|\btn\b|[$€£¥₹]\s?t\b", re.I), 1e12),
    (re.compile(r"\bbillions?\b|\bbn\b|[$€£¥₹]\s?b\b", re.I), 1e9),
    (re.compile(r"\bmillions?\b|\bmn\b|\bmm\b|[$€£¥₹]\s?m\b", re.I), 1e6),
    (re.compile(r"\bthousands?\b|'000|\b000s\b|[$€£¥₹]\s?k\b", re.I), 1e3),
)
# Columns whose numbers are names, not magnitudes: never separator-grouped or rounded.
# Judged on the whole header ("Year", "Period") or on year-like values, never on a word inside
# a longer name - "25-34 years" is a share column, not a date.
_LABEL_COLUMN = re.compile(r"^\W*(year|date|period|month|quarter|week|day|id|code)s?\W*$", re.I)


def _is_label_column(header: str, numbers: Sequence[float]) -> bool:
    if _LABEL_COLUMN.match(header):
        return True
    return all(float(n).is_integer() and 1800 <= n <= 2100 for n in numbers)


def header_unit_multiplier(header: str) -> float:
    """Base units per source unit implied by a column header; 1.0 when it states none."""
    for pattern, multiplier in _HEADER_SCALES:
        if pattern.search(header):
            return multiplier
    return 1.0


# A dedicated unit field may be a bare scale letter ("M", "bn"). Case-sensitive for one letter:
# "M" is millions, "m" is metres.
_BARE_SCALES = {"K": 1e3, "k": 1e3, "M": 1e6, "MM": 1e6, "mn": 1e6, "B": 1e9, "bn": 1e9, "T": 1e12, "tn": 1e12}


def unit_field_multiplier(unit: str) -> float:
    """Scale implied by a data table's unit field: a stated scale word, or a bare scale token."""
    stated = header_unit_multiplier(unit)
    if stated != 1.0:
        return stated
    token = re.sub(r"[\s$€£¥₹()]", "", unit)
    return _BARE_SCALES.get(token, 1.0)


def _as_number(cell: Any) -> Optional[float]:
    if isinstance(cell, bool) or cell is None:
        return None
    if isinstance(cell, (int, float)):
        return float(cell) if math.isfinite(cell) else None
    text = str(cell).strip().replace(",", "")
    for token in ("$", "€", "£", "¥", "₹", "%"):
        text = text.replace(token, "")
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def number_formats(
    columns: Sequence[str], rows: Sequence[Sequence[Any]], unit: str = ""
) -> str:
    """Markdown table of the display format for every numeric column of a data table.

    A driver runs this on the recovered or prepared table and hands it to the insight stage,
    so every number the headline and annotations quote is already rounded by the spread rule
    and scaled to a short unit - the model copies a format instead of choosing digits.
    ``unit`` is the table's stated unit ("$MM", "in millions"); a column header that states
    its own scale wins over it. Returns an empty string when no column is numeric.
    """
    lines: list[str] = []
    for index, header in enumerate(columns):
        cells = [row[index] for row in rows if index < len(row) and row[index] not in (None, "")]
        numbers = [n for n in (_as_number(cell) for cell in cells) if n is not None]
        if not numbers or 2 * len(numbers) < len(cells):
            continue
        if _is_label_column(str(header), numbers):
            continue
        multiplier = header_unit_multiplier(str(header))
        if multiplier == 1.0:
            multiplier = unit_field_multiplier(unit)
        result = recommend_precision(numbers, role="label", unit_multiplier=multiplier)
        lo = min(result["preview"], key=lambda item: item["value"])
        hi = max(result["preview"], key=lambda item: item["value"])
        lines.append(
            f"| {header} | {result['compact_step']} | {lo['compact']} to {hi['compact']} |"
        )
    if not lines:
        return ""
    return "\n".join(
        [
            "## Number formats",
            "",
            "Quote any number in the headline, subtitle or an annotation in this column's",
            "compact form (add the currency or % sign the column uses). Do not add digits.",
            "",
            "| Column | Round to | Range as written |",
            "|---|---|---|",
            *lines,
        ]
    )
