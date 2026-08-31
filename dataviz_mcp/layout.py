"""Recommend a clip-safe, good-looking canvas size for one chart.

This is the forward companion to ``inspection`` - the same geometry primitives that
measure a rendered chart's overflow and squash are used here, before render, to size the
canvas so those defects do not arise. It is a *mechanical* recommendation: the model has
already chosen the chart (form, series, facets); this picks width, height, dpi, and a
facet grid that give every point, category, and panel room to be legible and reserve space
for the title/subtitle/footer bands so nothing clips.

Not a chart chooser. It never decides which form to draw - only how big to draw it.
"""

from __future__ import annotations

import math
from typing import Any, Optional


# Delivery profiles: base canvas and the ceiling a growing dimension may not exceed.
# Height ceiling is generous for "document" so a long ranked strip can breathe.
PROFILES: dict[str, dict[str, int]] = {
    "chat": {"width_px": 1200, "height_px": 675, "dpi": 144, "max_width_px": 1600, "max_height_px": 1400},
    "slide": {"width_px": 1600, "height_px": 900, "dpi": 160, "max_width_px": 1920, "max_height_px": 1200},
    "document": {"width_px": 1800, "height_px": 1200, "dpi": 180, "max_width_px": 2200, "max_height_px": 3200},
}

# House text sizes (pt), read off the corpus: base 11-12, titles 14-16.
FONT_PT: dict[str, float] = {
    "title": 16.0,
    "subtitle": 12.0,
    "footer": 10.0,
    "caption": 10.0,
    "axis": 11.0,
    "annotation": 11.0,
}

LINE_HEIGHT = 1.25          # multiplier on font size for a text line's box
AVG_CHAR_ADVANCE = 0.5      # average glyph advance as a fraction of the em, proportional face

# Legibility floors, in device px, so nothing is squashed below readability. These are two
# general properties of a slot, not a list of chart types: a slot whose mark fills its width
# (a bar, a tile, a column) needs more room to stay distinct than a slot holding a point or a
# line vertex. Everything else is derived from counts, not enumerated.
POINT_SLOT_PX = 6.0         # a point / line-vertex position needs this much separation
FILLED_SLOT_PX = 22.0       # a bar / tile / column must show its own width
MIN_PANEL_W = 240.0         # a facet panel below this reads as a thumbnail
MIN_PANEL_H = 150.0
PANEL_GUTTER = 24.0         # space between facet panels
FREE_AXIS_BAND = 42.0       # extra per-panel left width when scales are free


def pt_to_px(pt: float, dpi: float) -> float:
    """Convert a point size to device pixels at the given dpi (1 pt = 1/72 inch)."""
    return pt * dpi / 72.0


def char_px(font_pt: float, dpi: float) -> float:
    """Approximate width of one average character at ``font_pt`` and ``dpi``."""
    return pt_to_px(font_pt, dpi) * AVG_CHAR_ADVANCE


def line_px(font_pt: float, dpi: float) -> float:
    """Height of one text line's box at ``font_pt`` and ``dpi``."""
    return pt_to_px(font_pt, dpi) * LINE_HEIGHT


def boxes_overlap(a: dict[str, Any], b: dict[str, Any], tol: float = 0.5) -> bool:
    """True when two ``{x, y, width, height}`` boxes overlap by more than ``tol`` on both axes."""
    ow = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    oh = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    return ow > tol and oh > tol


def _band_px(lines: int, role: str, dpi: float) -> float:
    """Vertical space a title/subtitle/footer band of ``lines`` lines needs, with padding."""
    if lines <= 0:
        return 0.0
    pad = pt_to_px(FONT_PT[role], dpi) * 0.6
    return lines * line_px(FONT_PT[role], dpi) + pad


def _facet_grid(n_panels: int, aspect: float) -> tuple[int, int]:
    """Pick a near-square facet grid (ncol, nrow) that respects a target aspect."""
    if n_panels <= 1:
        return 1, 1
    # More columns than rows when the canvas is wider than tall.
    ncol = max(1, round(math.sqrt(n_panels * aspect)))
    nrow = math.ceil(n_panels / ncol)
    # Trim a stray empty column.
    while ncol > 1 and math.ceil(n_panels / (ncol - 1)) == nrow:
        ncol -= 1
    return ncol, nrow


def _slot_floor(filled: bool) -> float:
    """Per-slot px floor from one general property: does the mark occupy its slot's width?"""
    return FILLED_SLOT_PX if filled else POINT_SLOT_PX


def recommend_layout(
    x_slots: int = 0,
    y_slots: int = 0,
    filled_marks: bool = False,
    n_panels: int = 1,
    facet_scales: str = "fixed",
    n_direct_labels: int = 0,
    title_lines: int = 1,
    subtitle_lines: int = 0,
    footer_lines: int = 0,
    x_labels: bool = False,
    longest_x_label_chars: int = 0,
    delivery_profile: str = "chat",
) -> dict[str, Any]:
    """Recommend ``width_px x height_px x dpi``, a facet grid, and x-label rotation.

    Sizing is one rule applied to counts, not a table of chart types: each axis needs
    ``discrete_slots x per_slot_floor`` pixels; a continuous axis (0 slots) takes a pleasant
    aspect. Horizontal category labels stack cleanly down the y-axis (so ``y_slots`` grows
    height directly) but crowd across the x-axis (so ``x_slots`` grows width toward a density
    floor and, when labels still will not fit, triggers rotation) - a property of horizontal
    text, not a regime.

    Args:
        x_slots: discrete positions that must stay separable on the x-axis; 0 = continuous.
        y_slots: discrete positions on the y-axis (e.g. ranked categories); 0 = continuous.
        filled_marks: True when each slot renders a width-occupying mark (bar/tile/column),
            False for points / line vertices. The only geom property sizing needs.
        n_panels: facet count; a grid multiplies both axes.
        facet_scales: "fixed" or "free" - free reserves a per-panel axis band.
        n_direct_labels: direct labels across the chart; drives a crowding warning only.
        title_lines / subtitle_lines / footer_lines: text bands to reserve vertical room for.
        x_labels: whether the x-axis carries text tick labels (drives the rotate check).
        longest_x_label_chars: longest x tick label, for the rotate check.
        delivery_profile: chat / slide / document - base size, dpi, and the growth ceiling.

    Returns width/height/dpi, facet grid, a rotate flag, reserved bands, warnings, rationale.
    Sizes honour legibility floors; a dimension that cannot fit is warned, never squashed.
    """
    profile = PROFILES.get(delivery_profile, PROFILES["chat"])
    dpi = float(profile["dpi"])
    base_w = float(profile["width_px"])
    max_w = float(profile["max_width_px"])
    max_h = float(profile["max_height_px"])
    warnings: list[str] = []

    bands = (
        _band_px(title_lines, "title", dpi)
        + _band_px(subtitle_lines, "subtitle", dpi)
        + _band_px(footer_lines, "footer", dpi)
    )
    axis_band = pt_to_px(FONT_PT["axis"], dpi) * 3.0  # tick labels + axis title
    row_floor = line_px(FONT_PT["axis"], dpi) * 1.6   # a labelled y category needs one text row
    slot_px = _slot_floor(filled_marks)

    ncol, nrow = _facet_grid(n_panels, aspect=1.6) if n_panels > 1 else (1, 1)

    # Width comes from the x-slot demand (or a pleasant base); floored, then it fixes the aspect.
    panel_plot_w = max(MIN_PANEL_W if n_panels > 1 else base_w * 0.6, x_slots * slot_px)
    left_band = axis_band + (FREE_AXIS_BAND if (n_panels > 1 and facet_scales == "free") else 0.0)
    width = max(base_w, ncol * (panel_plot_w + left_band) + (ncol - 1) * PANEL_GUTTER)

    # Plot height: y-slot demand when the axis is discrete, else a pleasant aspect off the final
    # panel width. Bands and the axis strip are chrome added on top, so they always grow height.
    panel_w_final = (width - ncol * left_band - (ncol - 1) * PANEL_GUTTER) / ncol
    if y_slots > 0:
        panel_plot_h = max(MIN_PANEL_H if n_panels > 1 else 0.0, y_slots * max(slot_px, row_floor))
    else:
        panel_plot_h = panel_w_final / 1.6
    height_plot = nrow * panel_plot_h + (nrow - 1) * PANEL_GUTTER
    height = height_plot + bands + axis_band

    if width > max_w:
        warnings.append(
            f"content needs {width:.0f}px of width but the {delivery_profile} ceiling is "
            f"{max_w:.0f}px: {'slots' if x_slots else 'panels'} will crowd - thin them, "
            "aggregate, or split the chart."
        )
        width = max_w
    if height > max_h:
        warnings.append(
            f"content needs {height:.0f}px of height but the {delivery_profile} ceiling is "
            f"{max_h:.0f}px: rows will cramp - show a top-N, page, or split."
        )
        height = max_h

    # Horizontal x labels crowd: rotate rather than clip when they exceed their slot.
    rotate_x_labels = False
    if x_labels and longest_x_label_chars > 0 and x_slots > 0:
        slot = (width / ncol - left_band) / max(1, x_slots)
        label_w = longest_x_label_chars * char_px(FONT_PT["axis"], dpi)
        rotate_x_labels = label_w > slot
        if rotate_x_labels:
            warnings.append(
                f"x tick labels (~{longest_x_label_chars} chars) exceed their {slot:.0f}px "
                "slot: rotate or abbreviate them."
            )

    labels_per_panel = n_direct_labels / max(1, n_panels)
    if labels_per_panel >= 8:
        warnings.append(
            f"~{labels_per_panel:.0f} direct labels per panel will crowd: run "
            "recommend_text_placement, use repel, or label only the focal series."
        )

    width_i, height_i = int(round(width)), int(round(height))
    rationale = (
        f"{int(base_w)}px base @ {int(dpi)}dpi -> {width_i}x{height_i}px from "
        f"x_slots={x_slots}, y_slots={y_slots}, "
        f"{'filled' if filled_marks else 'point'} marks"
        + (f", facet {ncol}x{nrow}" if n_panels > 1 else "")
        + (f", {bands:.0f}px reserved bands" if bands else "")
        + ". Legibility floors honoured; overflow warned, not squashed."
    )

    return {
        "width_px": width_i,
        "height_px": height_i,
        "dpi": int(dpi),
        "facet_ncol": ncol,
        "facet_nrow": nrow,
        "rotate_x_labels": rotate_x_labels,
        "reserved_band_px": round(bands, 1),
        "warnings": warnings,
        "rationale": rationale,
    }


def suggest_dims_for_overflow(
    width_px: int,
    height_px: int,
    top_overflow_px: float = 0.0,
    bottom_overflow_px: float = 0.0,
    left_overflow_px: float = 0.0,
    right_overflow_px: float = 0.0,
    min_panel_height_px: Optional[float] = None,
) -> dict[str, Any]:
    """Backward companion for ``inspection``: given measured overflow on a rendered chart,
    return the smallest grown canvas that would clear it. Shared math with recommend_layout so
    "grow the top by 14px" means the same thing forward and backward.
    """
    grow_w = max(0.0, left_overflow_px) + max(0.0, right_overflow_px)
    grow_h = max(0.0, top_overflow_px) + max(0.0, bottom_overflow_px)
    new_w = int(round(width_px + grow_w))
    new_h = int(round(height_px + grow_h))
    if min_panel_height_px is not None and min_panel_height_px < MIN_PANEL_H:
        # Squashed panels: grow height proportionally to reach the floor.
        deficit = MIN_PANEL_H - min_panel_height_px
        new_h = int(round(new_h + deficit))
    return {
        "suggested_width_px": new_w,
        "suggested_height_px": new_h,
        "grow_width_px": new_w - width_px,
        "grow_height_px": new_h - height_px,
    }
