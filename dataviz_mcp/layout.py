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
MAX_PANEL_ASPECT = 2.0      # a data panel wider than this (few rows, wide canvas) letterboxes:
                            #   marks flatten and category labels crowd - grow height to this cap
PANEL_GUTTER = 24.0         # space between facet panels
GROUP_BREAK = 48.0          # break between heterogeneous panel groups (a whole band apart)
FREE_AXIS_BAND = 42.0       # extra per-panel left width when scales are free


def pt_to_px(pt: float, dpi: float) -> float:
    """Convert a point size to device pixels at the given dpi (1 pt = 1/72 inch)."""
    return pt * dpi / 72.0


# Base canvas the house FONT_PT sizes are tuned for (the chat profile's plot area). Type is sized
# RELATIVE to this, never as a constant: a bigger or emptier canvas has more room and should carry
# larger type, so 11pt axis text never lands on a 1200px canvas with acres of white space.
_FONT_BASE_DIAG_PX = math.hypot(1200.0, 675.0)


def house_font_pt(
    width_px: float,
    height_px: float,
    *,
    scale_floor: float = 1.0,
    scale_ceiling: float = 1.7,
) -> dict[str, float]:
    """House per-role font sizes scaled to the actual canvas, not fixed constants.

    Sizes scale with the canvas diagonal relative to the base chat canvas, so a large or sparse
    delivery grows type instead of leaving it at the base 11/16pt. Never shrinks below the base
    (``scale_floor`` >= 1.0) - the base sizes are legibility floors - and is capped so a poster
    canvas doesn't shout. Callers merge explicit ``font_pt`` overrides on top of this.
    """
    diag = math.hypot(float(width_px), float(height_px))
    scale = max(scale_floor, min(scale_ceiling, diag / _FONT_BASE_DIAG_PX))
    return {role: round(pt * scale, 1) for role, pt in FONT_PT.items()}


def data_label_pt(slot_px: float, dpi: float, *, floor_pt: float = 12.0, ceiling_pt: float = 34.0) -> float:
    """On-mark value/data-label size derived from the room one slot actually has.

    The emphasis tier grows most when the panel is sparse: a five-bar chart on a wide canvas gives
    each bar a fat slot, so its value should be read at a glance, not set at the base 11pt. Sized to
    a fraction of the slot width, floored for legibility and capped so it stays bold-but-not-shouting
    and never overpowers the mark.
    """
    by_room = pt_to_px_inverse(slot_px * 0.28, dpi)
    return round(max(floor_pt, min(ceiling_pt, by_room)), 1)


def pt_to_px_inverse(px: float, dpi: float) -> float:
    """Point size whose device height is ``px`` at ``dpi`` - the inverse of :func:`pt_to_px`."""
    return px * 72.0 / dpi


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


def _build_fit(
    *,
    required_width_px: float,
    required_height_px: float,
    max_width_px: float,
    max_height_px: float,
    min_panel_height_px: float,
    directives: list[dict[str, Any]],
) -> dict[str, Any]:
    """A machine-branchable fit verdict, so a caller reads a boolean instead of prose.

    Nothing is ever squashed to fit a ceiling: *both* width and height are grown - the whole
    image is resized up - to keep every slot and panel at its legibility floor. So two separate
    questions:
      - *legible*: are the panels at or above ``MIN_PANEL_H`` and the marks at their slot floor?
        Because we resize instead of squash, this is always true - it is the guarantee the tool
        makes, surfaced as a boolean a weak maker cannot skip the way it skips a sentence.
      - *fits the ceiling*: does that legible size sit inside the profile's nominal box? When the
        content genuinely needs more room than the profile, the image is bigger than the ceiling
        on one or both axes; ``over_width`` / ``over_height`` say which.

    ``status`` is ``ok`` when the legible size fits the profile box, else ``over_ceiling`` (the
    image was resized up; follow a directive to split or reduce if a smaller image is wanted).
    ``directives`` are ranked, machine-readable actions the caller branches on without parsing
    text.
    """
    over_width = required_width_px > max_width_px + 0.5
    over_height = required_height_px > max_height_px + 0.5
    fits = not over_width and not over_height
    legible = min_panel_height_px >= MIN_PANEL_H - 0.5
    status = "ok" if fits else "over_ceiling"
    return {
        "status": status,
        "legible": legible,
        "required_width_px": round(required_width_px, 1),
        "required_height_px": round(required_height_px, 1),
        "ceiling_width_px": round(max_width_px, 1),
        "ceiling_height_px": round(max_height_px, 1),
        "over_width": over_width,
        "over_height": over_height,
        "min_panel_height_px": round(min_panel_height_px, 1),
        "min_panel_floor_px": MIN_PANEL_H,
        "fits_ceiling": fits,
        "directives": directives,
    }


def _normalize_facet_scales(value: Any) -> tuple[str, bool, Optional[str]]:
    """Read the ggplot ``scales=`` vocabulary tolerantly, not literally.

    The upstream model naturally emits the geom's own words - ``free``, ``free_x``,
    ``free_y``, ``free_both`` - not this tool's binary. Sizing only cares about one thing:
    is the *y* axis free, so each panel grows its own left axis band? That is true for
    ``free`` / ``free_y`` / ``free_both`` and false for ``fixed`` / ``free_x``. We return
    the canonical value alongside so the caller keeps the axis-specific choice for the
    renderer; only a genuinely unrecognised value degrades - to ``fixed`` with a warning,
    never a silent drop.

    Returns ``(canonical, y_free, warning)``.
    """
    token = str(value).strip().lower().replace("-", "_") if value is not None else ""
    canonical = {
        "": "fixed",
        "fixed": "fixed",
        "none": "fixed",
        "free": "free",
        "free_both": "free",
        "both": "free",
        "free_x": "free_x",
        "free_y": "free_y",
        "x": "free_x",
        "y": "free_y",
    }.get(token)
    if canonical is None:
        return "fixed", False, (
            f"facet_scales={value!r} is not a recognised scales value "
            "(fixed / free / free_x / free_y): treating as fixed."
        )
    return canonical, canonical in ("free", "free_y"), None


def _group_natural_width(
    ncol: int, panel_plot_w: float, left_band: float
) -> float:
    """Width a panel group's own sub-grid demands, before it is widened to the canvas."""
    return ncol * (panel_plot_w + left_band) + (ncol - 1) * PANEL_GUTTER


def _size_panel_groups(
    groups: list[dict[str, Any]],
    *,
    base_w: float,
    base_h: float,
    max_w: float,
    max_h: float,
    dpi: float,
    bands: float,
    axis_band: float,
    row_floor: float,
    slot_px_default: float,
    filled_default: bool,
    x_slots_default: int,
    y_slots_default: int,
    y_scales_free: bool,
    y_labels: bool,
    longest_y_label_chars: int,
) -> tuple[float, float, list[dict[str, Any]], float, list[str]]:
    """Size a stack of heterogeneous panel groups into one canvas.

    Each group is sized as its own facet sub-grid using the same per-slot floors and
    letterbox cap as a homogeneous chart, then laid out as a full-width horizontal band;
    an ``emphasis`` weight (>1) makes a band taller so an aggregate/overview panel is set
    apart from a detail grid instead of reading as one more equal cell. Bands stack top to
    bottom with a ``GROUP_BREAK`` between them; one shared axis band sits at the bottom.

    Returns ``(width, height, regions, data_panel_fraction, warnings, fit)`` where each region
    is a full-width ``{role, facet_ncol, facet_nrow, n_panels, x, y, width, height}`` band and
    ``fit`` is the machine-branchable verdict from :func:`_build_fit`. Nothing is scaled below
    its floor to force a ceiling fit; the honest width and height are returned (the image is
    resized up on either axis) and the overflow is reported in ``fit`` and ``warnings``.
    """
    warnings: list[str] = []
    y_tick_extra = 0.0
    if y_labels and longest_y_label_chars > 0:
        y_tick_extra = max(0.0, (longest_y_label_chars - 4) * char_px(FONT_PT["axis"], dpi))

    sized: list[dict[str, Any]] = []
    for g in groups:
        n = max(1, int(g.get("n_panels", 1)))
        filled = bool(g.get("filled_marks", filled_default))
        gx = int(g.get("x_slots", x_slots_default))
        gy = int(g.get("y_slots", y_slots_default))
        emphasis = max(0.1, float(g.get("emphasis", g.get("weight", 1.0))))
        # Honour a grid shape the caller declared (select may specify "a two-column grid");
        # otherwise pick a near-square grid. An explicit ncol fixes columns and derives rows.
        if g.get("ncol") or g.get("nrow"):
            ncol = max(1, int(g.get("ncol", 0)) or math.ceil(n / int(g["nrow"])))
            nrow = max(1, int(g.get("nrow", 0)) or math.ceil(n / ncol))
        else:
            ncol, nrow = _facet_grid(n, aspect=1.6) if n > 1 else (1, 1)
        slot = _slot_floor(filled) if "filled_marks" in g else slot_px_default
        panel_plot_w = max(MIN_PANEL_W if n > 1 else base_w * 0.6, gx * slot)
        left_band = axis_band + (FREE_AXIS_BAND if (n > 1 and y_scales_free) else 0.0) + y_tick_extra
        sized.append({
            "role": str(g.get("role", "")),
            "n": n, "ncol": ncol, "nrow": nrow, "gy": gy, "slot": slot,
            "emphasis": emphasis, "left_band": left_band,
            "group_w": _group_natural_width(ncol, panel_plot_w, left_band),
        })

    width = max(base_w, max(s["group_w"] for s in sized))

    total_panel_area = 0.0
    for s in sized:
        panel_w_final = (width - s["ncol"] * s["left_band"] - (s["ncol"] - 1) * PANEL_GUTTER) / s["ncol"]
        if s["gy"] > 0:
            panel_h = max(MIN_PANEL_H if s["n"] > 1 else 0.0, s["gy"] * max(s["slot"], row_floor))
        else:
            panel_h = panel_w_final / 1.6
        panel_h = max(panel_h, panel_w_final / MAX_PANEL_ASPECT)  # never letterbox a band
        panel_h *= s["emphasis"]
        s["band_h"] = s["nrow"] * panel_h + (s["nrow"] - 1) * PANEL_GUTTER
        s["panel_w_final"] = panel_w_final
        total_panel_area += s["ncol"] * s["nrow"] * panel_w_final * panel_h

    breaks = GROUP_BREAK * (len(sized) - 1)
    height_plot = sum(s["band_h"] for s in sized) + breaks
    height = height_plot + bands + axis_band

    # Neither dimension is squashed to fit a ceiling: the whole image is resized up so every
    # band keeps its slots and panels at their floor. When the honest size is bigger than the
    # profile box on either axis, report it and hand back ranked directives to shrink content.
    over_width = width > max_w + 0.5
    over_height = height > max_h + 0.5
    directives: list[dict[str, Any]] = []
    if over_width:
        warnings.append(
            f"content needs {width:.0f}px of width, past the {max_w:.0f}px profile ceiling: the "
            "image is widened to keep panels legible - thin slots, aggregate, or split to shrink it."
        )
        directives.append({"action": "reduce_slots"})
    if over_height:
        warnings.append(
            f"content needs {height:.0f}px of height, past the {max_h:.0f}px profile ceiling: the "
            "image is grown to keep panels legible - drop a group, reduce emphasis, or split into "
            "pages to shrink it."
        )
        tallest = max(sized, key=lambda s: s["band_h"])
        directives.append({"action": "drop_group", "role": tallest["role"] or "?"})
        directives.append({"action": "reduce_emphasis"})
        directives.append({"action": "split_pages", "pages": math.ceil(height / max_h)})

    # Panels are held at their floor throughout, so the honest per-band panel height is the
    # legibility figure we report; the smallest single panel across bands drives it.
    min_panel_h = min(s["band_h"] / s["nrow"] for s in sized)
    fit = _build_fit(
        required_width_px=width,
        required_height_px=height,
        max_width_px=max_w,
        max_height_px=max_h,
        min_panel_height_px=min_panel_h,
        directives=directives,
    )

    regions: list[dict[str, Any]] = []
    y = bands
    for s in sized:
        regions.append({
            "role": s["role"],
            "n_panels": s["n"],
            "facet_ncol": s["ncol"],
            "facet_nrow": s["nrow"],
            "x": 0,
            "y": int(round(y)),
            "width": int(round(width)),
            "height": int(round(s["band_h"])),
        })
        y += s["band_h"] + GROUP_BREAK

    data_panel_fraction = round(total_panel_area / (width * height), 3) if width and height else 0.0
    if data_panel_fraction < 0.4:
        warnings.append(
            f"the data panels are only {data_panel_fraction:.0%} of the canvas; axis labels, "
            "text bands, and group breaks dominate - abbreviate labels, drop a group, or reduce "
            "the category count so the plot area carries the ink."
        )
    return width, height, regions, data_panel_fraction, warnings, fit


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
    y_labels: bool = False,
    longest_y_label_chars: int = 0,
    delivery_profile: str = "chat",
    panel_groups: Optional[list[dict[str, Any]]] = None,
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
        facet_scales: the ggplot ``scales=`` value - fixed / free / free_x / free_y
            (free_both accepted). A free *y* axis reserves a per-panel left axis band;
            the canonical value is echoed back as ``facet_scales`` for the renderer.
        n_direct_labels: direct labels across the chart; drives a crowding warning only.
        title_lines / subtitle_lines / footer_lines: text bands to reserve vertical room for.
        x_labels: whether the x-axis carries text tick labels (drives the rotate check).
        longest_x_label_chars: longest x tick label, for the rotate check.
        delivery_profile: chat / slide / document - base size, dpi, and the growth ceiling.
        panel_groups: optional heterogeneous layout. A list of groups, each
            ``{role, n_panels, emphasis?, filled_marks?, x_slots?, y_slots?, ncol?, nrow?}``, sized as its
            own sub-grid and stacked as a full-width band; ``emphasis`` (>1) sets a group
            apart (an aggregate/overview panel above a detail grid) instead of one uniform
            grid. ``role`` is a free-text label echoed back per band, never branched on.
            When given, ``n_panels`` and the top-level facet grid describe the largest group
            and the per-band structure is returned as ``regions``.

    Returns width/height/dpi, facet grid, a rotate flag, reserved bands, warnings, rationale,
    and a structured ``fit`` verdict. Nothing is ever squashed below its floor to fit a ceiling:
    the column count is chosen so the whole image comes out near the profile's aspect given each
    panel's floored size (tall panels take more columns, wide panels fewer), and when the content
    needs more room than the profile *both* width and height are grown - the image is resized up.
    ``fit`` reports ``status`` (ok / over_ceiling), ``legible``, ``over_width`` / ``over_height``,
    the required vs ceiling dims, the achieved ``min_panel_height_px``, and ranked machine-readable
    ``directives`` (reduce_slots / reduce_panels / split_pages / drop_group) so a caller can branch
    on a boolean instead of parsing prose.
    """
    profile = PROFILES.get(delivery_profile, PROFILES["chat"])
    dpi = float(profile["dpi"])
    base_w = float(profile["width_px"])
    base_h = float(profile["height_px"])
    max_w = float(profile["max_width_px"])
    max_h = float(profile["max_height_px"])
    warnings: list[str] = []

    facet_scales_canonical, y_scales_free, scales_warning = _normalize_facet_scales(facet_scales)
    if scales_warning:
        warnings.append(scales_warning)

    bands = (
        _band_px(title_lines, "title", dpi)
        + _band_px(subtitle_lines, "subtitle", dpi)
        + _band_px(footer_lines, "footer", dpi)
    )
    axis_band = pt_to_px(FONT_PT["axis"], dpi) * 3.0  # tick labels + axis title
    row_floor = line_px(FONT_PT["axis"], dpi) * 1.6   # a labelled y category needs one text row
    slot_px = _slot_floor(filled_marks)

    # Heterogeneous layout: an aggregate/overview panel set apart from a detail grid cannot be
    # expressed as one uniform facet grid (the selector's aggregate-and-parts guardrail). When
    # the caller declares panel_groups, size each group's own band and return them as regions,
    # so Build lays out the hierarchy instead of collapsing it to equally-weighted cells.
    if panel_groups:
        width, height, regions, data_panel_fraction, group_warnings, fit = _size_panel_groups(
            panel_groups,
            base_w=base_w, base_h=base_h, max_w=max_w, max_h=max_h, dpi=dpi,
            bands=bands, axis_band=axis_band, row_floor=row_floor,
            slot_px_default=slot_px, filled_default=filled_marks,
            x_slots_default=x_slots, y_slots_default=y_slots,
            y_scales_free=y_scales_free, y_labels=y_labels,
            longest_y_label_chars=longest_y_label_chars,
        )
        warnings.extend(group_warnings)
        width_i, height_i = int(round(width)), int(round(height))
        dominant = max(regions, key=lambda r: r["n_panels"])
        rationale = (
            f"{int(base_w)}px base @ {int(dpi)}dpi -> {width_i}x{height_i}px from "
            f"{len(regions)} panel groups "
            + ", ".join(f"{r['role'] or '?'}:{r['facet_ncol']}x{r['facet_nrow']}" for r in regions)
            + f". Overview set apart from detail; legibility floors honoured, fit={fit['status']}."
        )
        return {
            "width_px": width_i,
            "height_px": height_i,
            "dpi": int(dpi),
            "facet_ncol": dominant["facet_ncol"],
            "facet_nrow": dominant["facet_nrow"],
            "facet_scales": facet_scales_canonical,
            "rotate_x_labels": False,
            "reserved_band_px": round(bands, 1),
            "reserved_left_px": round(axis_band, 1),
            "data_panel_fraction": data_panel_fraction,
            "regions": regions,
            "fit": fit,
            "warnings": warnings,
            "rationale": rationale,
        }

    # Per-panel width demand is independent of the grid: x-slot demand (or a pleasant base) plus
    # the left axis band. The grid - how many columns - is chosen afterwards to seat that demand.
    panel_plot_w = max(MIN_PANEL_W if n_panels > 1 else base_w * 0.6, x_slots * slot_px)
    left_band = axis_band + (FREE_AXIS_BAND if (n_panels > 1 and y_scales_free) else 0.0)
    # Long y-axis category labels (ranked names, model labels on a heatmap) must be budgeted
    # into the left band, or the renderer grows the margin at the panel's expense. axis_band
    # already covers a short (~4-char) tick plus the axis title; anything longer adds width.
    if y_labels and longest_y_label_chars > 0:
        y_tick_extra = max(0.0, (longest_y_label_chars - 4) * char_px(FONT_PT["axis"], dpi))
        left_band += y_tick_extra

    def _dims_for_ncol(nc: int) -> dict[str, float]:
        """Honest canvas dims for a given column count, panels held at their floors.

        Neither dimension is clamped to a ceiling: the width grows to seat ``nc`` panels at
        their width floor and the height grows to seat the rows at their height floor, so the
        image is resized up rather than any slot or panel squashed.
        """
        nr = math.ceil(n_panels / nc)
        w = max(base_w, nc * (panel_plot_w + left_band) + (nc - 1) * PANEL_GUTTER)
        pw = max(1.0, (w - nc * left_band - (nc - 1) * PANEL_GUTTER) / nc)
        if y_slots > 0:
            ph = max(MIN_PANEL_H if n_panels > 1 else 0.0, y_slots * max(slot_px, row_floor))
        else:
            ph = pw / 1.6  # continuous y: a pleasant aspect off the panel width
        # Floor to the profile's own per-row plotting height, so a sparse chart uses the base
        # height instead of collapsing to a wide strip; and never letterbox past the aspect cap.
        base_panel_h = max(0.0, base_h - bands - axis_band - (nr - 1) * PANEL_GUTTER) / nr
        ph = max(ph, base_panel_h)
        ph = max(ph, pw / MAX_PANEL_ASPECT)
        h = nr * ph + (nr - 1) * PANEL_GUTTER + bands + axis_band
        return {"ncol": nc, "nrow": nr, "width": w,
                "panel_w": pw, "panel_h": ph, "height": h}

    # Choose the column count so the *whole image* comes out near the profile's own aspect,
    # given each panel's floored size - this is the "how many columns are actually required"
    # decision. Because both dimensions resize freely, the grid is not bounded by a ceiling;
    # it is picked to balance the image: tall panels (many y-rows) take more columns so the
    # image is not a narrow tower, wide panels take fewer. Fewest columns wins a tie.
    if n_panels > 1:
        target_aspect = base_w / base_h
        best_dev: Optional[float] = None
        dims = _dims_for_ncol(1)
        for nc in range(1, n_panels + 1):
            cand = _dims_for_ncol(nc)
            dev = abs(math.log((cand["width"] / cand["height"]) / target_aspect))
            if best_dev is None or dev < best_dev - 1e-9:
                best_dev, dims = dev, cand
    else:
        dims = _dims_for_ncol(1)

    ncol, nrow = int(dims["ncol"]), int(dims["nrow"])
    width = dims["width"]
    panel_w_final = dims["panel_w"]
    panel_plot_h = dims["panel_h"]
    height = dims["height"]

    # Neither dimension is squashed to a ceiling: the whole image is resized up so every slot
    # and panel keeps its floor. When the honest size is bigger than the profile box on either
    # axis, report which and hand back ranked directives to shrink content if a smaller image is
    # wanted.
    over_width = width > max_w + 0.5
    over_height = height > max_h + 0.5
    if over_width:
        warnings.append(
            f"content needs {width:.0f}px of width, past the {delivery_profile} "
            f"ceiling of {max_w:.0f}px: the image is widened to keep "
            f"{'slots' if x_slots else 'panels'} legible - thin them, aggregate, or split to shrink it."
        )
    if over_height:
        warnings.append(
            f"content needs {height:.0f}px of height, past the {delivery_profile} ceiling of "
            f"{max_h:.0f}px: the image is grown to keep rows legible - show a top-N, page, or "
            "split the chart to shrink it."
        )

    directives: list[dict[str, Any]] = []
    if over_width and x_slots > 0:
        directives.append({"action": "reduce_slots"})
    if over_height and n_panels > 1:
        row_stride = panel_plot_h + PANEL_GUTTER
        rows_fit = max(1, int((max_h - bands - axis_band + PANEL_GUTTER) // max(1.0, row_stride)))
        panels_fit = rows_fit * ncol
        directives.append({"action": "reduce_panels", "to": panels_fit})
        directives.append({"action": "split_pages", "pages": math.ceil(n_panels / max(1, panels_fit))})
    elif over_height:
        directives.append({"action": "split_pages", "pages": math.ceil(height / max_h)})
    elif over_width and n_panels > 1:
        directives.append({"action": "split_pages", "pages": math.ceil(width / max_w)})

    fit = _build_fit(
        required_width_px=width,
        required_height_px=height,
        max_width_px=max_w,
        max_height_px=max_h,
        min_panel_height_px=panel_plot_h,
        directives=directives,
    )

    # Data-panel share of the finished canvas, measured after any ceiling clamp. A long left
    # label band or reserved text bands can starve the panel (the 29%-panel heatmap failure);
    # report the fraction so the caller sees it, and warn when the labels dominate.
    panel_w_after = max(0.0, (width - ncol * left_band - (ncol - 1) * PANEL_GUTTER) / ncol)
    panel_h_after = max(0.0, (height - bands - axis_band - (nrow - 1) * PANEL_GUTTER) / nrow)
    data_panel_area = panel_w_after * panel_h_after * ncol * nrow
    data_panel_fraction = round(data_panel_area / (width * height), 3) if width and height else 0.0
    if data_panel_fraction < 0.4:
        warnings.append(
            f"the data panel is only {data_panel_fraction:.0%} of the canvas; the axis labels "
            "and text bands dominate - shorten or abbreviate the category labels, drop a text "
            "band, or reduce the category count so the plot area carries the ink."
        )

    # Horizontal x labels crowd: the style bans slanted ticks, so never recommend rotation -
    # keep them horizontal and thin, abbreviate, or widen instead. rotate_x_labels stays False.
    rotate_x_labels = False
    # Bar orientation is a reasoned, geometry-driven call, not a default. For filled marks
    # (bars/columns) the category labels decide it: short names that sit flat under vertical
    # columns keep the bars vertical; names too wide for their slot (they would need rotation or
    # truncation) read far better as left-aligned rows, so the bars go horizontal. Advisory: the
    # tool sizes the box and reports the fit; the selector/build owns the final chart choice.
    bar_orientation: Optional[str] = None
    bar_orientation_reason: Optional[str] = None
    if x_labels and longest_x_label_chars > 0 and x_slots > 0:
        slot = (width / ncol - left_band) / max(1, x_slots)
        label_w = longest_x_label_chars * char_px(FONT_PT["axis"], dpi)
        if filled_marks:
            if label_w <= slot:
                bar_orientation = "vertical"
                bar_orientation_reason = (
                    f"longest category label (~{longest_x_label_chars} chars, {label_w:.0f}px) fits "
                    f"its {slot:.0f}px slot horizontally, so vertical columns read cleanly."
                )
            else:
                bar_orientation = "horizontal"
                bar_orientation_reason = (
                    f"longest category label (~{longest_x_label_chars} chars, {label_w:.0f}px) exceeds "
                    f"its {slot:.0f}px slot; horizontal bars turn the names into left-aligned rows."
                )
        if label_w > slot and not filled_marks:
            warnings.append(
                f"x tick labels (~{longest_x_label_chars} chars) exceed their {slot:.0f}px "
                "slot: keep them horizontal and abbreviate, thin to every-Nth tick, or widen "
                "the slot - do not rotate."
            )

    # On-mark value/data-label size, derived from the slot each filled mark actually has (sparse
    # bars → fat slots → larger values), so the build never falls back to the base 11pt on a canvas
    # with room to spare. Advisory: apply it to geom_text size unless a house/brand size overrides.
    recommended_data_label_pt: Optional[float] = None
    if filled_marks and x_slots > 0:
        slot_for_labels = (width / ncol - left_band) / max(1, x_slots)
        recommended_data_label_pt = data_label_pt(slot_for_labels, dpi)

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
        + f". Legibility floors honoured; panels never squashed below the floor; fit={fit['status']}."
    )

    return {
        "width_px": width_i,
        "height_px": height_i,
        "dpi": int(dpi),
        "facet_ncol": ncol,
        "facet_nrow": nrow,
        "facet_scales": facet_scales_canonical,
        "rotate_x_labels": rotate_x_labels,
        "bar_orientation": bar_orientation,
        "bar_orientation_reason": bar_orientation_reason,
        "recommended_data_label_pt": recommended_data_label_pt,
        "reserved_band_px": round(bands, 1),
        "reserved_left_px": round(left_band, 1),
        "data_panel_fraction": data_panel_fraction,
        "regions": None,
        "fit": fit,
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
    return a grown canvas that accounts for the measured panel-to-canvas scale.
    This assumes panels expand with the canvas; fixed-size panels still require a design change.
    """
    grow_w = max(0.0, left_overflow_px) + max(0.0, right_overflow_px)
    grow_h = max(0.0, top_overflow_px) + max(0.0, bottom_overflow_px)
    new_w = math.ceil(width_px + grow_w)
    new_h = math.ceil(height_px + grow_h)
    if min_panel_height_px is not None and min_panel_height_px < MIN_PANEL_H:
        # A panel receives only a share of canvas growth. Scale by its measured
        # share, rather than adding one panel's deficit to the whole canvas.
        # This also covers unequal panels and fractional outer margins without
        # guessing a facet count. Fixed chrome makes this estimate conservative.
        if min_panel_height_px > 0:
            new_h = math.ceil(height_px * MIN_PANEL_H / min_panel_height_px + grow_h)
        else:
            # No positive panel extent from which to infer a scale. Keep a finite
            # growth probe; refit's ceiling/no-improvement guards still apply.
            new_h = math.ceil(new_h + MIN_PANEL_H - min_panel_height_px)
    return {
        "suggested_width_px": new_w,
        "suggested_height_px": new_h,
        "grow_width_px": new_w - width_px,
        "grow_height_px": new_h - height_px,
    }
