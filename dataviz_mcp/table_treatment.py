"""Resolve a table's skill-selected treatments into per-cell drawing instructions.

The skill decides *what* a table encodes - data bars, heat shading, sparklines, emphasis - and
at which comparison scope. This module does the arithmetic a weak model gets wrong: scale
domains per column/row/table group, fill colours along an ordered ramp, the text ink each fill
needs, bar extents from a baseline, and sparkline points. The constructors only draw what it
returns, so a planned treatment cannot silently disappear between plan and render.
"""
from __future__ import annotations

import re
from typing import Any

from .color_math import better_ink, to_rgb
from .palette import recommend_continuous_scale

KINDS = {"text", "emphasis", "bar", "shading", "sparkline"}
SCOPES = {"column", "row", "table"}
MAGNITUDE_KINDS = {"bar", "shading", "sparkline"}

# Default reserved graphic widths, in body em. A bar needs enough length to separate
# neighbouring magnitudes; a sparkline needs room for the shape of a short sequence.
BAR_EM = 5.0
SPARK_EM = 7.0
GAP_EM = 0.4
DEFAULT_BAR = "#8A949E"
DEFAULT_SPARK = "#3A4148"
DEFAULT_FOCUS = "#F6D776"
INK_DARK = "#222222"
HEAT_MIN = 0.06
HEAT_MAX = 0.5
TEXT_CONTRAST = 4.5

_NUMBER = re.compile(r"^\(?[-+−]?\d[\d,]*\.?\d*\)?$|^\(?[-+−]?\.\d+\)?$")


def parse_number(cell: str) -> float | None:
    """A display string's numeric value: currency, %, thousands separators and (neg) handled."""
    text = cell.strip()
    for token in ("$", "₹", "€", "£", "%", "pp", " "):
        text = text.replace(token, "")
    multiplier = 1.0
    if text[-1:] in {"K", "k", "M", "B"}:
        multiplier = {"K": 1e3, "k": 1e3, "M": 1e6, "B": 1e9}[text[-1]]
        text = text[:-1]
    if not text or not _NUMBER.match(text):
        return None
    negative = text.startswith("(") and text.endswith(")")
    value = float(text.strip("()").replace(",", "").replace("−", "-")) * multiplier
    return -value if negative else value


def column_values(column: dict[str, Any]) -> list[float | None] | None:
    """Raw values when supplied, else parsed from every non-blank display string."""
    if "values" in column:
        return [None if v is None else v for v in column["values"]]
    parsed = [parse_number(str(c)) if str(c).strip() else None for c in column["cells"]]
    filled = [str(c).strip() for c in column["cells"] if str(c).strip()]
    if not filled or any(parse_number(c) is None for c in filled):
        return None
    return parsed


def _mix(a: str, b: str, t: float) -> str:
    ra, rb = to_rgb(a), to_rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))


def _heat(scale: dict[str, Any], t: float, background: str) -> str:
    """A cell fill at position t: strength grows from the background toward a pole.

    Table cells carry text, so the ramp stops short of the pole (HEAT_MAX): the extreme
    cell still reads as the strongest while its number stays dark-on-light. A diverging
    scale fades to the background at its midpoint and strengthens toward either pole.
    """
    t = min(1.0, max(0.0, t))
    low, high = scale["stops"][0]["colour"], scale["stops"][-1]["colour"]
    if scale["scale_kind"] == "diverging":
        pole, strength = (high, 2 * t - 1) if t >= 0.5 else (low, 1 - 2 * t)
    else:
        pole, strength = high, HEAT_MIN + (1 - HEAT_MIN) * t
    return _mix(background, pole, HEAT_MAX * strength)


def _normalise(raw: Any) -> list[dict[str, Any]]:
    items = raw if isinstance(raw, list) else [raw or {"kind": "text"}]
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each treatment must be an object with a kind")
        kind, scope = item.get("kind", "text"), item.get("scope", "column")
        if kind not in KINDS:
            raise ValueError(f"Unknown treatment kind {kind!r}; use one of {sorted(KINDS)}")
        if scope not in SCOPES:
            raise ValueError("Unknown comparison scope")
        if kind == "sparkline":
            # Each sparkline shows its own row's shape unless a shared scale is asked for.
            scope = item.get("scope", "row")
            shared = scope in {"column", "table"}
        else:
            shared = scope in {"row", "table"}
        if kind in MAGNITUDE_KINDS and shared and not item.get("commensurable"):
            raise ValueError("A shared scale requires explicit commensurability")
        out.append({**item, "scope": scope})
    return out


def resolve_treatments(
    columns: list[dict[str, Any]], raw: Any, em_px: float, background: str = "#FFFFFF"
) -> dict[str, Any]:
    """Return {treatments, styles, align, visual_width_px, untreated_numeric_columns}.

    ``styles[col][row]`` holds only what differs from plain body text: ``fill``, ``ink``,
    ``bold``, ``bar`` {start, end, colour} as fractions of the graphic area, and ``spark``
    {points, colour} with points in unit coordinates. Mutates nothing it was given.
    """
    treatments = _normalise(raw)
    n_cols, n_rows = len(columns), len(columns[0]["cells"])
    styles: list[list[dict[str, Any]]] = [[{} for _ in range(n_rows)] for _ in range(n_cols)]
    visual = [float(c.get("visual_width_px", 0)) for c in columns]
    values = [column_values(c) for c in columns]
    align = [c.get("align") or ("right" if values[i] is not None and not c.get("identifier")
                                else "left") for i, c in enumerate(columns)]
    touched: set[int] = set()

    def targets(item, need_columns=True):
        cols = item.get("columns")
        if cols is None:
            if need_columns:
                raise ValueError(f"A {item['kind']} treatment must name its columns (zero-based)")
            cols = list(range(n_cols))
        rows = item.get("rows", list(range(n_rows)))
        for index in list(cols):
            if not 0 <= index < n_cols:
                raise ValueError(f"Treatment column {index} does not exist")
        for index in list(rows):
            if not 0 <= index < n_rows:
                raise ValueError(f"Treatment row {index} does not exist")
        return list(cols), list(rows)

    def groups(item, cols, rows):
        """Cells sharing one scale: per column, per row, or the whole block."""
        scope = item.get("scope", "column")
        if scope == "column":
            return [[(c, r) for r in rows] for c in cols]
        if scope == "row":
            return [[(c, r) for c in cols] for r in rows]
        return [[(c, r) for c in cols for r in rows]]

    def value(c, r):
        vals = values[c]
        if vals is None:
            raise ValueError(
                f"Column {c} has no numeric values: supply column 'values' (raw numbers) "
                "for a magnitude treatment; display strings alone could not be parsed")
        return vals[r]

    # Shading first so emphasis only tints cells the heat scale left unfilled.
    ordered = sorted(treatments, key=lambda t: ["shading", "bar", "sparkline", "emphasis", "text"]
                     .index(t.get("kind", "text")))
    for item in ordered:
        kind = item.get("kind", "text")
        if kind == "text":
            continue
        if kind == "emphasis":
            cols, rows = targets(item, need_columns=False)
            if "rows" not in item:
                raise ValueError("An emphasis treatment must name its focal rows (zero-based)")
            focus = item.get("colour", DEFAULT_FOCUS)
            tint = _mix(focus, background, 0.55)
            for c in cols:
                for r in rows:
                    style = styles[c][r]
                    style["bold"] = True
                    if "fill" not in style and item.get("fill", True):
                        style["fill"] = tint
                        style["ink"] = better_ink(tint, ink_dark=INK_DARK)[0]
            continue
        cols, rows = targets(item)
        touched.update(cols)
        higher_is_better = item.get("higher_is_better", True)
        if kind == "sparkline":
            for c in cols:
                visual[c] = visual[c] or SPARK_EM * em_px
            spark_groups = ([[(c, r)] for c in cols for r in rows] if item["scope"] == "row"
                            else groups(item, cols, rows))
            for group in spark_groups:
                series = {cell: [v for v in (value(*cell) or []) if v is not None] for cell in group}
                flat = [v for seq in series.values() for v in seq]
                if not flat:
                    continue
                lo, hi = item.get("domain", [min(flat), max(flat)])
                span = (hi - lo) or 1.0
                for (c, r), seq in series.items():
                    if len(seq) < 2:
                        continue
                    styles[c][r]["spark"] = {
                        "points": [[round(i / (len(seq) - 1), 4), round((v - lo) / span, 4)]
                                   for i, v in enumerate(seq)],
                        "colour": item.get("colour", DEFAULT_SPARK)}
            continue
        for group in groups(item, cols, rows):
            present = [(cell, value(*cell)) for cell in group if value(*cell) is not None]
            if not present:
                continue
            nums = [v for _, v in present]
            if kind == "bar":
                for c in {c for c, _ in group}:
                    visual[c] = visual[c] or BAR_EM * em_px
                base = float(item.get("baseline", 0))
                lo, hi = item.get("domain", [min(nums + [base]), max(nums + [base])])
                span = (hi - lo) or 1.0
                for (c, r), v in present:
                    styles[c][r]["bar"] = {
                        "start": round((min(base, v) - lo) / span, 4),
                        "end": round((max(base, v) - lo) / span, 4),
                        "colour": item.get("colour", DEFAULT_BAR)}
                continue
            scale = recommend_continuous_scale(
                nums, available=item.get("colours"), background=background,
                reference=item.get("midpoint"), kind=item.get("scale", "auto"))
            lo, hi = item.get("domain", scale["domain"])
            mid = scale["midpoint"]
            for (c, r), v in present:
                if scale["scale_kind"] == "diverging" and mid is not None:
                    reach = max(mid - lo, hi - mid) or 1.0
                    t = 0.5 + 0.5 * (v - mid) / reach
                else:
                    t = (v - lo) / ((hi - lo) or 1.0)
                if not higher_is_better:
                    t = 1 - t
                fill = _heat(scale, t, background)
                ink, ratio = better_ink(fill, ink_dark=INK_DARK)
                while ratio < TEXT_CONTRAST:
                    # A mid-tone neither ink clears: ease the fill toward the background.
                    fill = _mix(fill, background, 0.15)
                    ink, ratio = better_ink(fill, ink_dark=INK_DARK)
                styles[c][r]["fill"] = fill
                styles[c][r]["ink"] = ink
    for c, width in enumerate(visual):
        # Leave a gap between the number and its trailing graphic.
        if width and not columns[c].get("visual_width_px"):
            visual[c] = round(width + GAP_EM * em_px, 1)
    untreated = [i for i, v in enumerate(values)
                 if v is not None and not columns[i].get("identifier") and i not in touched
                 and sum(x is not None for x in v) >= 3]
    return {"treatments": treatments, "styles": styles, "align": align,
            "visual_width_px": visual, "untreated_numeric_columns": untreated}
