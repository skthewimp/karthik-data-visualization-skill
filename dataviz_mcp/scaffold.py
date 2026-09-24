"""Write the mechanical half of a chart's source from the plan, and check the half the model writes.

A weak build model that writes the whole chart gets the mechanical settings wrong in ways the
plan had already settled: tiny fonts, an axis title nobody asked for, a value axis the direct
labels make redundant, ``limits = c(0, 100)`` on a 1-44 line, hand-picked hues instead of the
resolved palette, 120 month ticks on a discrete axis. A gate that flags these after the render
gets ignored, and a tool that rewrites the model's code afterwards ships code that contradicts
itself. So the split is by construction instead:

* :func:`scaffold_chart` writes the source file from the plan and the outputs of the existing
  tools (``prepare_plot_data``, ``recommend_layout``, ``reserve_frame``, ``recommend_colours``,
  ``recommend_precision``): data load and typing, number format, palette, value and date scales,
  facet grid, ``labs()`` and ``theme()``. It leaves one marked slot, ``chart_marks``, for the
  model's geoms and labels. The scaffold adds its scales, labels and theme *after* the slot, so
  a stray override in the slot loses by ggplot's own ordering, not by rewriting.
* :func:`check_chart` reads the file back. Scaffold regions that were edited are restored (the
  tool wrote them, so this is safe), and the slot is checked on the built plot object, not by
  pattern-matching code: non-layers, ``geom_label``, off-palette mark colours, undersized text,
  a build error, and fewer drawn labels than the plan promised when the value axis was dropped.
  Each deviation carries a one-line fix for the model; none means the model review can be
  skipped.

The rules are computed from the plan, never from a chart-type table: the value axis goes when
the planned value labels reach the same two-label floor ``REDUNDANT_VALUE_AXIS`` uses, dates get
the renderer's own breaks with short labels, and limits appear only for a declared zero baseline.
"""

from __future__ import annotations

import colorsys
import csv
import json
import math
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from . import handoff
from .color_math import _contrast_ratio, better_ink, to_rgb
from .frame import reserve_frame
from .inspection import _REDUNDANT_AXIS_MIN_LABELS
from .layout import FONT_PT, GROUP_BREAK, PROFILES, char_px, house_font_pt, pt_to_px
from .precision import recommend_precision
from .text_metrics import TextMeasurer

MARKS_BEGIN = "# ==== marks: the build model writes geoms and labels here ===="
MARKS_END = "# ==== end marks ===="
_SCAFFOLD_BANNER = "# ==== scaffold: written by scaffold_chart from the plan - do not edit ===="

# A mark colour whose HLS saturation is below this reads as a neutral grey: context ink the
# palette does not need to own (focal-plus-grey, reference lines, muted labels).
_NEUTRAL_SATURATION = 0.12
# Text drawn smaller than this share of the planned label size reads as the tiny-font defect.
_MIN_TEXT_SHARE = 0.8
# WCAG AA for normal text; on-mark labels are judged against the fill they sit on.
_MIN_ON_MARK_CONTRAST = 4.5
# Text on the page below the large-text floor cannot be read at all (white on white).
_MIN_ON_PAGE_CONTRAST = 3.0
# Text this large reads at the large-text floor, as the render inspection judges it.
_LARGE_TEXT_PT = 14.0

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
)}


# --------------------------------------------------------------------------- #
# Plan inputs
# --------------------------------------------------------------------------- #


def _parse_date(text: str) -> date | None:
    """Read one time label as a date: ISO dates, year-month, bare years, month-year, quarters.

    Anything else - including a period range such as ``2010-14`` - is not a date, so the caller
    keeps the axis discrete rather than guessing.
    """
    try:
        return _parse_date_parts(text)
    except ValueError:  # an impossible month or day
        return None


def _parse_date_parts(text: str) -> date | None:
    raw = text.strip()
    lowered = raw.lower().replace("'", " 20").replace("’", " 20")
    if match := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw):
        return date(int(match[1]), int(match[2]), int(match[3]))
    if match := re.fullmatch(r"(\d{4})[-/](\d{1,2})", raw):
        return date(int(match[1]), int(match[2]), 1)
    if match := re.fullmatch(r"(\d{4})(?:\.0)?", raw):
        return date(int(match[1]), 1, 1)
    if match := re.fullmatch(r"([a-z]{3})[a-z]*\.?[\s-]+(\d{4})", lowered):
        if match[1] in _MONTHS:
            return date(int(match[2]), _MONTHS[match[1]], 1)
    quarter = re.fullmatch(r"q([1-4])[\s-]*(\d{4})", lowered) or re.fullmatch(r"(\d{4})[\s-]*q([1-4])", lowered)
    if quarter:
        q, year = (quarter[1], quarter[2]) if lowered.startswith("q") else (quarter[2], quarter[1])
        return date(int(year), 3 * (int(q) - 1) + 1, 1)
    return None


def _read_plot_data(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _first_seen(rows: list[dict[str, str]], column: str) -> list[str]:
    seen: list[str] = []
    for row in rows:
        if row.get(column, "") not in seen:
            seen.append(row[column])
    return seen


def _palette(colours: Any, series: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    """Resolve the colour input to (series->hex, ordered hexes, continuous stops)."""
    if isinstance(colours, dict) and colours.get("stops"):
        return {}, [], [str(c) for c in colours["stops"]]
    if isinstance(colours, dict):
        ordered = [str(c) for c in (colours.get("ordered_palette") or [])]
    else:
        ordered = [str(c) for c in (colours or [])]
    if not ordered:
        ordered = ["#1f4e79"]
    named = {name: ordered[i % len(ordered)] for i, name in enumerate(series)}
    return named, ordered, []


def _number_format(number_format: dict[str, Any] | None) -> dict[str, Any]:
    number_format = number_format or {}
    step = number_format.get("step")
    return {
        "step": float(step) if step else None,
        "decimals": int(number_format.get("decimals", 0) or 0),
        "prefix": str(number_format.get("prefix", "") or ""),
        "suffix": str(number_format.get("suffix", "") or ""),
        "signed": bool(number_format.get("signed")),
    }


def _format_number(value: float, fmt: dict[str, Any]) -> str:
    """The string fmt_value prints, for measuring label width before anything renders."""
    step = fmt["step"]
    decimals = max(0, -int(math.floor(math.log10(step)))) if step and step < 1 else 0
    if step:
        value = round(value / step) * step
    sign = "+" if fmt.get("signed") and value > 0 else ""
    return f"{sign}{fmt['prefix']}{value:,.{decimals}f}{fmt['suffix']}"


def _label_formats(rows: list[dict[str, str]], units: dict[str, Any], given: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """One number format per label measure, in its own units and at its own precision.

    A format the plan resolved is used as given; otherwise the precision comes from the
    measure's own values by the spread rule, so a growth rate never borrows the revenue format.
    """
    formats: dict[str, dict[str, Any]] = {}
    for name, unit in units.items():
        if given.get(name):
            formats[name] = _number_format({**unit, **given[name]})
            continue
        values = [float(r[name]) for r in rows if r.get(name) not in ("", None)]
        resolved = recommend_precision(values, role="label") if values else {}
        formats[name] = _number_format({**unit, "step": resolved.get("step"), "decimals": resolved.get("decimals")})
    return formats


def _region_membership(regions: list[dict[str, Any]], categories: list[str]) -> tuple[dict[str, str], str | None]:
    """Which region draws each category: the regions that name their categories claim them, and
    one region that names none takes the rest. Returns ({} , why) when the rows cannot be split."""
    if not regions:
        return {}, None
    named = [r for r in regions if r.get("categories")]
    open_regions = [r for r in regions if not r.get("categories")]
    if not named or len(open_regions) > 1:
        return {}, ("the layout has panel-group regions but they do not name their categories, so the "
                    "scaffold draws one grid; give each region its categories")
    fold = {c.strip().casefold(): c for c in categories}
    region_of: dict[str, str] = {}
    for region in named:
        for label in region["categories"]:
            category = fold.get(str(label).strip().casefold())
            if category is not None and category not in region_of:
                region_of[category] = str(region.get("role") or "")
    rest = [c for c in categories if c not in region_of]
    if rest:
        home = open_regions[0] if open_regions else named[-1]
        for category in rest:
            region_of[category] = str(home.get("role") or "")
        if not open_regions:
            return region_of, f"categories {rest[:3]} are in no region; drawn in {home.get('role')!r}"
    return region_of, None


def _region_boxes(
    regions: list[dict[str, Any]], frame: dict[str, Any], margin_px: dict[str, Any],
    width: int, height: int, facet_order: list[str], rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Place each region between the page frame's text bands, in proportion to its band height.

    The frame is reserved once for the page: the title and subtitle above, a caption below,
    the margins at the sides. Each region's axes and headings live inside its own box.
    """
    blocks = frame.get("frame_blocks") or []
    tops = [b["bbox"]["y"] + b["bbox"]["height"] for b in blocks if b.get("role") in ("title", "subtitle") and b.get("bbox")]
    bottoms = [b["bbox"]["y"] for b in blocks if b.get("role") in ("caption", "footer") and b.get("bbox")]
    gap = GROUP_BREAK / 2
    top = max(tops) + gap if tops else float(margin_px["top"])
    bottom = min(bottoms) - gap / 2 if bottoms else height - float(margin_px["bottom"])
    x = float(margin_px["left"])
    inner_w = width - x - float(margin_px["right"])
    weights = [max(1.0, float(r.get("height") or 1)) for r in regions]
    boxes, y = [], top
    for i, (region, weight) in enumerate(zip(regions, weights)):
        h = (bottom - top) * weight / sum(weights)
        role = str(region.get("role") or "")
        cats = _first_seen([r for r in rows if r["region"] == role], "category")
        facets = _first_seen([r for r in rows if r["region"] == role], "facet") if facet_order else []
        ncol = int(region.get("facet_ncol") or max(1, round(len(facets) ** 0.5))) if facets else 1
        boxes.append({
            "role": role, "categories": cats, "facets": facets,
            "x": round(x), "y": round(y), "width": round(inner_w), "height": round(h),
            "facet_ncol": ncol,
            "margin_top": gap / 2 if i else 0.0, "margin_bottom": gap / 2 if i < len(regions) - 1 else 0.0,
        })
        y += h
    return boxes


def _r_formatter(fmt: dict[str, Any]) -> str:
    return (
        "scales::label_number("
        + (f"accuracy = {fmt['step']!r}, " if fmt["step"] else "")
        + f"big.mark = \",\", prefix = {_r_str(fmt['prefix'])}, suffix = {_r_str(fmt['suffix'])}"
        + (', style_positive = "plus"' if fmt.get("signed") else "")
        + ")"
    )


def _py_formatter(name: str, fmt: dict[str, Any], doc: str) -> list[str]:
    step = fmt["step"]
    sign = "('+' if value > 0 else '')" if fmt.get("signed") else "''"
    return [
        f"def {name}(value):",
        f'    """{doc}"""',
        (f"    value = round(float(value) / {step!r}) * {step!r}" if step else "    value = float(value)"),
        f"    return {sign} + f\"{fmt['prefix']}{{value:,.{fmt['decimals']}f}}{fmt['suffix']}\"",
        "",
        "",
    ]


def _r_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _r_vec(values: list[str], names: list[str] | None = None) -> str:
    if names is None:
        return "c(" + ", ".join(_r_str(v) for v in values) + ")"
    return "c(" + ", ".join(f"{_r_str(n)} = {_r_str(v)}" for n, v in zip(names, values)) + ")"


def _pt(px: float, dpi: float) -> float:
    return round(float(px) * 72.0 / float(dpi), 2)


def _subtitle_key(subtitle: str, palette: dict[str, str]) -> str:
    """Colour each series name in the subtitle with its resolved hex (longest names first)."""
    marked = subtitle
    for name in sorted(palette, key=len, reverse=True):
        if name:
            marked = re.sub(
                rf"(?<![\w>]){re.escape(name)}(?![\w<])",
                f"<span style='color:{palette[name]}'>{name}</span>",
                marked,
                count=1,
            )
    return marked


# --------------------------------------------------------------------------- #
# ggplot2 scaffold
# --------------------------------------------------------------------------- #


_GGPLOT_BAR_VALUES = r'''
# Bar values: bar_values(aes(label = fmt_value(value), fill = series), position = <the bars' own
# position>) prints each bar's value inside its end, in the ink that reads on that fill, or just
# past the end in ink when the bar is too short to hold it - decided when drawn, from the bar's
# drawn length and the label's own glyphs. Map fill as the bars do (default: ink). A second
# reading for the same bar (a growth rate beside a revenue) goes in note = ...: it prints past the
# bar's end, after the value when the value is outside too, so the two never land on each other.
bar_value_ink <- function(fill) {
  lum <- function(col) {
    v <- grDevices::col2rgb(col) / 255
    v <- ifelse(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055)^2.4)
    colSums(v * c(0.2126, 0.7152, 0.0722))
  }
  ratio <- function(a, b) (pmax(a, b) + 0.05) / (pmin(a, b) + 0.05)
  l <- lum(fill)
  ifelse(ratio(1, l) >= ratio(lum("#1a1a1a"), l), "#ffffff", "#1a1a1a")
}
# One rule for the render and the check: along/cross are the label's extent along and across the
# value axis, lo/hi the bar's value extent and thick its cross extent (one unit, any), dir the side
# its value grows to; a stacked segment is centred, and one with another beyond it never moves out.
bar_value_place <- function(lo, hi, thick, along, cross, dir, stacked, inner, pad) {
  fits <- along + 2 * pad <= hi - lo & cross <= thick
  end <- ifelse(dir > 0, hi, lo)
  centre <- inner | (stacked & fits)
  inside <- fits | inner
  at <- ifelse(centre, (lo + hi) / 2, ifelse(fits, end - dir * pad, end + dir * pad))
  just <- ifelse(centre, 0.5, ifelse(fits, (1 + dir) / 2, (1 - dir) / 2))
  list(at = at, just = just, inside = inside)
}
# A note starts past the bar's end, or past the value when the value sits outside too.
bar_value_note <- function(place, along, dir, end, pad) {
  outside <- !place$inside
  list(at = ifelse(outside, place$at + dir * (along + 2 * pad), end + dir * pad), just = (1 - dir) / 2)
}
# Which way each bar grows, and whether it is a stacked segment with another beyond it.
bar_value_stack <- function(data) {
  dir <- ifelse(data$ymax > 0, 1, -1)
  touches <- function(r, beyond) {
    edge <- if (xor(dir[r] > 0, beyond)) data$ymax - data$ymin[r] else data$ymin - data$ymax[r]
    any(data$PANEL == data$PANEL[r] & abs(data$x - data$x[r]) < 1e-9 & seq_len(nrow(data)) != r & abs(edge) < 1e-9)
  }
  inner <- vapply(seq_len(nrow(data)), touches, TRUE, beyond = TRUE)
  list(dir = dir, inner = inner, stacked = inner | vapply(seq_len(nrow(data)), touches, TRUE, beyond = FALSE))
}
bar_value_aes <- GeomText$default_aes
bar_value_aes$fill <- "#1a1a1a"
# A segment that does not start at zero (a stacked or floating interval) gives its own ymin/ymax.
GeomBarValue <- ggproto("GeomBarValue", GeomText,
  default_aes = bar_value_aes,
  optional_aes = c("ymin", "ymax", "note"),
  extra_params = c("na.rm", "width"),
  setup_data = function(data, params) {
    if (is.null(data$width)) data$width <- if (is.null(params$width)) resolution(data$x, FALSE, TRUE) * 0.9 else params$width
    if (is.null(data$ymin)) data$ymin <- pmin(data$y, 0)
    if (is.null(data$ymax)) data$ymax <- pmax(data$y, 0)
    data$xmin <- data$x - data$width / 2
    data$xmax <- data$x + data$width / 2
    data$width <- NULL
    data
  },
  draw_panel = function(data, panel_params, coord, na.rm = FALSE) {
    flip <- inherits(coord, "CoordFlip")
    stack <- bar_value_stack(data)
    coords <- coord$transform(data, panel_params)
    grid::gTree(coords = coords, flip = flip, dir = stack$dir, stacked = stack$stacked, inner = stack$inner, cl = "dvz_bar_values")
  }
)
makeContent.dvz_bar_values <- function(x) {
  d <- x$coords
  inch <- function(v, horizontal) if (horizontal) grid::convertWidth(grid::unit(v, "npc"), "in", TRUE) else
    grid::convertHeight(grid::unit(v, "npc"), "in", TRUE)
  # flip: the value axis runs across the screen, so its extents are the x columns after transform.
  lo <- if (x$flip) d$xmin else d$ymin; hi <- if (x$flip) d$xmax else d$ymax
  c0 <- if (x$flip) d$ymin else d$xmin; c1 <- if (x$flip) d$ymax else d$xmax
  gp <- lapply(seq_len(nrow(d)), function(r) grid::gpar(fontsize = d$size[r] * .pt, fontfamily = d$family[r],
    fontface = d$fontface[r], lineheight = d$lineheight[r]))
  w <- vapply(seq_len(nrow(d)), function(r) grid::convertWidth(grid::grobWidth(grid::textGrob(d$label[r], gp = gp[[r]])), "in", TRUE), 0)
  h <- vapply(seq_len(nrow(d)), function(r) grid::convertHeight(grid::grobHeight(grid::textGrob(d$label[r], gp = gp[[r]])), "in", TRUE), 0)
  place <- bar_value_place(inch(lo, x$flip), inch(hi, x$flip), abs(inch(c1, !x$flip) - inch(c0, !x$flip)),
    if (x$flip) w else h, if (x$flip) h else w, x$dir, x$stacked, x$inner, 0.3 * d$size * .pt / 72)
  # Back to npc, the unit every other text in the panel is placed in.
  at <- grid::unit(place$at / inch(1, x$flip), "npc"); mid <- grid::unit((c0 + c1) / 2, "npc")
  ink <- ifelse(place$inside, bar_value_ink(d$fill), d$colour)
  kids <- lapply(seq_len(nrow(d)), function(r) grid::textGrob(d$label[r],
    x = if (x$flip) at[r] else mid[r], y = if (x$flip) mid[r] else at[r],
    hjust = if (x$flip) place$just[r] else 0.5, vjust = if (x$flip) 0.5 else place$just[r],
    gp = grid::gpar(col = ink[r], fontsize = d$size[r] * .pt, fontfamily = d$family[r],
                    fontface = d$fontface[r], lineheight = d$lineheight[r])))
  if (!is.null(d$note)) {
    note <- bar_value_note(place, if (x$flip) w else h, x$dir, ifelse(x$dir > 0, inch(hi, x$flip), inch(lo, x$flip)),
      0.3 * d$size * .pt / 72)
    note_at <- grid::unit(note$at / inch(1, x$flip), "npc")
    for (r in which(!is.na(d$note) & nzchar(d$note))) kids[[length(kids) + 1]] <- grid::textGrob(d$note[r],
      x = if (x$flip) note_at[r] else mid[r], y = if (x$flip) mid[r] else note_at[r],
      hjust = if (x$flip) note$just[r] else 0.5, vjust = if (x$flip) 0.5 else note$just[r],
      gp = grid::gpar(col = d$colour[r], fontsize = d$size[r] * .pt, fontfamily = d$family[r],
                      fontface = d$fontface[r], lineheight = d$lineheight[r]))
  }
  grid::setChildren(x, do.call(grid::gList, kids))
}
bar_values <- function(mapping = NULL, data = NULL, position = "identity", ..., width = NULL, size = label_size) {
  params <- list(width = width, size = size, ...)
  if (is.null(mapping$fill) && is.null(params$fill)) params$fill <- ink
  if (is.null(mapping$colour) && is.null(params$colour)) params$colour <- "#1a1a1a"
  layer(geom = GeomBarValue, stat = "identity", data = data, mapping = mapping,
        position = position, params = params, show.legend = FALSE)
}
'''.strip("\n")


_GGPLOT_END_LABELS = r'''
# Line ends: end_labels(aes(x = category, y = value, label = series, colour = series), data = <each
# line's last row>) names each line just past its last point; labels that would overlap are spread
# apart along the value axis by the least total movement and tied back to their points by short leaders.
end_label_spread <- function(y, h, lo, hi) {
  o <- order(y)
  ys <- y[o]; hs <- h[o]
  need <- c(0, cumsum((head(hs, -1) + tail(hs, -1)) / 2))
  # Least-squares positions keeping every gap: isotonic regression of y - need, then add it back.
  z <- ys - need
  blocks <- lapply(seq_along(z), function(i) c(sum = z[i], n = 1))
  k <- 1
  while (k < length(blocks)) {
    if (blocks[[k]]["sum"] / blocks[[k]]["n"] > blocks[[k + 1]]["sum"] / blocks[[k + 1]]["n"]) {
      blocks[[k]] <- blocks[[k]] + blocks[[k + 1]]
      blocks[[k + 1]] <- NULL
      k <- max(1, k - 1)
    } else k <- k + 1
  }
  fitted <- unlist(lapply(blocks, function(b) rep(b["sum"] / b["n"], b["n"])))
  out <- fitted + need
  # Keep the labels inside the panel, pushing on only the neighbours that would then overlap.
  step <- diff(need)
  out[1] <- max(out[1], lo + hs[1] / 2)
  for (i in seq_along(out)[-1]) out[i] <- max(out[i], out[i - 1] + step[i - 1])
  out[length(out)] <- min(out[length(out)], hi - hs[length(hs)] / 2)
  for (i in rev(seq_along(out))[-1]) out[i] <- min(out[i], out[i + 1] - step[i])
  out[order(o)]
}
GeomEndLabel <- ggproto("GeomEndLabel", GeomText,
  draw_panel = function(data, panel_params, coord, na.rm = FALSE) {
    grid::gTree(coords = coord$transform(data, panel_params), cl = "dvz_end_labels")
  }
)
makeContent.dvz_end_labels <- function(x) {
  d <- x$coords
  gp <- lapply(seq_len(nrow(d)), function(r) grid::gpar(col = d$colour[r], fontsize = d$size[r] * .pt,
    fontfamily = d$family[r], fontface = d$fontface[r], lineheight = d$lineheight[r]))
  h <- vapply(seq_len(nrow(d)), function(r) grid::convertHeight(grid::grobHeight(
    grid::textGrob(d$label[r], gp = gp[[r]])), "npc", TRUE), 0) * 1.15
  y <- end_label_spread(d$y, h, 0, 1)
  gap <- grid::convertWidth(grid::unit(0.3 * d$size * .pt, "points"), "npc", TRUE)
  # Once any label has moved, every label in the column takes a leader, so they align.
  moved <- rep(any(abs(y - d$y) > h / 2), nrow(d))
  lead <- ifelse(moved, 3 * gap, 0)
  kids <- lapply(seq_len(nrow(d)), function(r) grid::textGrob(d$label[r], x = d$x[r] + gap[r] + lead[r],
    y = y[r], hjust = 0, vjust = 0.5, gp = gp[[r]]))
  leaders <- lapply(which(moved), function(r) grid::segmentsGrob(d$x[r] + gap[r] / 2, d$y[r],
    d$x[r] + gap[r] + lead[r] * 0.8, y[r], gp = grid::gpar(col = d$colour[r], lwd = 0.6)))
  grid::setChildren(x, do.call(grid::gList, c(kids, leaders)))
}
end_labels <- function(mapping = NULL, data = NULL, ..., size = label_size) {
  layer(geom = GeomEndLabel, stat = "identity", data = data, mapping = mapping,
        position = "identity", params = list(size = size, ...), show.legend = FALSE)
}
'''.strip("\n")


def _ggplot_scaffold(spec: dict[str, Any]) -> tuple[str, str, str]:
    """Return (head, marks body, tail) for the ggplot2 source."""
    fonts = spec["font_pt"]
    margin = spec["plot_margin_px"]
    dpi = spec["dpi"]
    fmt = spec["number_format"]
    has_series = "series" in spec["columns"]
    has_facet = "facet" in spec["columns"]
    horizontal = spec["orientation"] == "horizontal"
    value_pos, cat_pos = ("x", "y") if horizontal else ("y", "x")
    colour_encoded = spec["value_encoding"] == "colour"

    head = [
        _SCAFFOLD_BANNER,
        "library(ggplot2)",
        "",
        f"plot_data <- read.csv({_r_str(spec['data_path'])}, stringsAsFactors = FALSE, check.names = FALSE)",
    ]
    if spec["x_kind"] == "date":
        head.append("plot_data$category <- as.Date(plot_data$category)")
    elif spec["x_kind"] == "continuous":
        head.append("plot_data$category <- as.numeric(plot_data$category)")
    else:
        head.append(f"plot_data$category <- factor(plot_data$category, levels = {_r_vec(spec['category_order'])})")
    if has_series:
        head.append(f"plot_data$series <- factor(plot_data$series, levels = {_r_vec(spec['series_order'])})")
    if has_facet:
        head.append(f"plot_data$facet <- factor(plot_data$facet, levels = {_r_vec(spec['facet_order'])})")
    head += [
        "",
        "# Colours: palette[[\"<series>\"]] by name, ink for a single-colour mark.",
        f"palette <- {_r_vec(list(spec['palette'].values()), list(spec['palette'].keys())) if spec['palette'] else _r_vec(spec['ordered'])}",
        f"ink <- {_r_str(spec['ordered'][0] if spec['ordered'] else '#1a1a1a')}",
        "# Numbers: fmt_value(x) formats any value you print, at the planned precision.",
        f"fmt_value <- {_r_formatter(fmt)}",
    ]
    if spec["label_formats"]:
        head.append("# Label measures ride beside the marks, never on a position: print each with its own formatter.")
        head += [f"fmt_{name} <- {_r_formatter(f)}" for name, f in spec["label_formats"].items()]
    head += [
        "# Text: geom_text(size = label_size) for labels and values, annotation_size for a free annotation.",
        f"label_size <- {fonts['label']} / .pt",
        f"annotation_size <- {fonts['annotation']} / .pt",
        "# Stacks: position = stack for stacked bars, stack_mid for their labels - the first",
        "# series sits at the baseline and each label on its own segment.",
        "stack <- position_stack(reverse = TRUE)",
        "stack_mid <- position_stack(reverse = TRUE, vjust = 0.5)",
        "# Text on a mark: aes(colour = on_fill_ink(series)) - the ink that reads on that fill;",
        "# on_fill_ink() for the single-colour ink. Text on the page takes ink or its series colour.",
        f"on_ink <- {_r_vec(list(spec['on_ink'].values()), list(spec['on_ink'].keys())) if spec['on_ink'] else 'c()'}",
        "on_fill_ink <- function(series = NULL) I(if (is.null(series)) "
        + f"{_r_str(better_ink(spec['ordered'][0] if spec['ordered'] else '#1a1a1a')[0])} "
        + "else unname(on_ink[as.character(series)]))",
        _GGPLOT_BAR_VALUES,
        _GGPLOT_END_LABELS,
        "",
    ]
    marks = [
        ("# Map x = category; each mark spans y = start to yend = end (the scaffold flips a horizontal chart itself)."
         if spec["interval"] else
         "# Map x = category and y = value (the scaffold flips a horizontal chart itself)."),
        "# Columns: " + ", ".join(spec["columns"]) + ". Return a list of layers only -",
        "# no scales, coords, facets, labs or theme: the scaffold owns those.",
        "chart_marks <- function(d) {",
        "  list(",
        "  )",
        "}",
    ]

    # One entry per theme element (a later rule replaces an earlier one; theme() rejects repeats).
    theme: dict[str, str] = {
        "plot.title.position": '"plot"',
        "plot.caption.position": '"plot"',
        "plot.title": f'element_text(size = {fonts["title"]}, face = "bold", colour = "#1a1a1a")',
        "plot.subtitle": (
            f'ggtext::element_markdown(size = {fonts["subtitle"]}, colour = "#4d4d4d", lineheight = 1.2)'
            if spec["identification"] == "subtitle_key"
            else f'element_text(size = {fonts["subtitle"]}, colour = "#4d4d4d")'
        ),
        "plot.caption": f'element_text(size = {fonts["caption"]}, colour = "#6b6b6b", hjust = 0)',
        "axis.text": f'element_text(size = {fonts["axis"]}, colour = "#4d4d4d")',
        "axis.title": f'element_text(size = {fonts["axis"]}, colour = "#4d4d4d")',
        "strip.text": f'element_text(size = {fonts["axis"]}, face = "bold", hjust = 0)',
        "panel.grid.minor": "element_blank()",
        f"panel.grid.major.{cat_pos}": "element_blank()",
        f"panel.grid.major.{value_pos}": 'element_line(colour = "#e5e5e5", linewidth = 0.3)',
        "plot.background": f'element_rect(fill = {_r_str(spec["background"])}, colour = NA)',
        "plot.margin": "margin({}, {}, {}, {}, unit = \"pt\")".format(
            *(_pt(margin[side], dpi) for side in ("top", "right", "bottom", "left"))
        ),
        "legend.position": '"none"',
    }
    if spec["identification"] == "legend":
        theme.update({"legend.position": '"top"', "legend.justification": '"left"', "legend.title": "element_blank()"})
    if spec["rotate_x_labels"] and not horizontal:
        theme["axis.text.x"] = "element_text(angle = 45, hjust = 1)"
    if spec["hide_value_axis"] or colour_encoded:
        theme[f"axis.text.{value_pos}"] = "element_blank()"
        theme[f"axis.title.{value_pos}"] = "element_blank()"
        theme[f"panel.grid.major.{value_pos}"] = "element_blank()"

    def plot_layers(data: str, ncol: str, page_text: bool) -> list[str]:
        layers = [f"ggplot({data})", f"chart_marks({data})"]
        if spec["stops"]:
            layers.append(f"scale_fill_gradientn(colours = {_r_vec(spec['stops'])}, labels = fmt_value)")
        elif has_series:
            layers.append('scale_colour_manual(values = palette, aesthetics = c("colour", "fill"))')
        if not colour_encoded:
            value_args = ["labels = fmt_value"]
            shared = spec.get("shared_limits") if data == "d" else None
            if shared:
                value_args.append(f"limits = c({shared[0]!r}, {shared[1]!r})")
            elif spec["zero_baseline"]:
                value_args.append("limits = c(0, NA)")
            if spec["zero_baseline"]:
                value_args.append("expand = expansion(mult = c(0, 0.05))")
            layers.append(f"scale_y_continuous({', '.join(value_args)})")
        if spec["x_kind"] == "date":
            layers.append("scale_x_date(labels = scales::label_date_short())")
        elif spec["x_kind"] == "discrete":
            # The axis runs in the planned category order whatever order the layers train it in (a
            # layer drawn from a subset would otherwise put its categories first), over the categories
            # the marks draw. A flipped axis would put the first category at the bottom; read order
            # runs top-down.
            order = _r_vec(spec["category_order"])
            drawn = f"intersect({order}, x)"
            discrete_args = [f"limits = function(x) {'rev(' + drawn + ')' if horizontal else drawn}"]
            if spec["wrap_label_chars"]:
                discrete_args.append(f"labels = scales::label_wrap({spec['wrap_label_chars']})")
            layers.append(f"scale_x_discrete({', '.join(discrete_args)})")
        # Clip off: a direct label past the panel edge draws into the margin, where the inspector
        # measures it and refit_chart grows the canvas, instead of being cut invisibly at the panel.
        layers.append('coord_flip(clip = "off")' if horizontal else 'coord_cartesian(clip = "off")')
        if has_facet:
            # A panel heading wider than its panel is cut at the panel edge; wrap it to the panel instead.
            labeller = f", labeller = label_wrap_gen(width = {spec['strip_wrap_chars']})" if spec["strip_wrap_chars"] else ""
            layers.append(f'facet_wrap(~facet, ncol = {ncol}, scales = {_r_str(spec["facet_scales"])}{labeller})')
        # Axis titles are declared by displayed position; under coord_flip the y aesthetic is drawn
        # along the bottom, so the labs() keys swap.
        shown = spec["axis_titles"]
        titles = {"x": shown.get("y"), "y": shown.get("x")} if horizontal else shown
        text = {k: spec[k] if page_text else "" for k in ("title", "subtitle", "caption")}
        labs_args = [
            f"title = {_r_str(text['title']) if text['title'] else 'NULL'}",
            f"subtitle = {_r_str(text['subtitle']) if text['subtitle'] else 'NULL'}",
            f"caption = {_r_str(text['caption']) if text['caption'] else 'NULL'}",
            f"x = {_r_str(titles['x']) if titles.get('x') else 'NULL'}",
            f"y = {_r_str(titles['y']) if titles.get('y') else 'NULL'}",
            "colour = NULL",
            "fill = NULL",
        ]
        layers.append("labs(\n      " + ",\n      ".join(labs_args) + "\n    )")
        layers.append(f"theme_minimal(base_size = {fonts['axis']})")
        return layers

    def theme_call(entries: dict[str, str]) -> str:
        return "theme(\n      " + ",\n      ".join(f"{key} = {value}" for key, value in entries.items()) + "\n    )"

    if not spec["regions"]:
        layers = plot_layers("plot_data", str(spec["facet_ncol"]), True) + [theme_call(theme)]
        tail = [
            _SCAFFOLD_BANNER,
            "build_chart <- function() {",
            "  " + " +\n    ".join(layers),
            "}",
        ]
        return "\n".join(head), "\n".join(marks), "\n".join(tail)

    # Regions: one native plot per panel group, each drawn from its own rows inside its own box,
    # and one page frame around them. A compositor places chart_regions() at the returned boxes;
    # build_chart() composes the same boxes here.
    page_keys = ("plot.title.position", "plot.caption.position", "plot.title", "plot.subtitle", "plot.caption",
                 "plot.background", "plot.margin")
    page_theme = {k: theme[k] for k in page_keys}
    region_theme = {k: v for k, v in theme.items() if k not in page_keys}
    region_theme["plot.background"] = theme["plot.background"]
    region_theme["plot.margin"] = "margin(top, 0, bottom, 0, unit = \"pt\")"
    layers = plot_layers("d", "ncol", False) + [theme_call(region_theme)]
    calls = [
        f"    {_r_str(r['role'])} = region_plot(plot_data[plot_data$region == {_r_str(r['role'])}, , drop = FALSE], "
        f"ncol = {r['facet_ncol']}, top = {_pt(r['margin_top'], dpi)}, bottom = {_pt(r['margin_bottom'], dpi)})"
        for r in spec["regions"]
    ]
    heights = ", ".join(str(r["height"]) for r in spec["regions"])
    page_labs = ", ".join(
        f"{k} = {_r_str(spec[k]) if spec[k] else 'NULL'}" for k in ("title", "subtitle", "caption")
    )
    tail = [
        _SCAFFOLD_BANNER,
        "region_plot <- function(d, ncol, top, bottom) {",
        "  " + " +\n    ".join(layers),
        "}",
        "chart_regions <- function() {",
        "  list(\n" + ",\n".join(calls) + "\n  )",
        "}",
        "build_chart <- function() {",
        f"  page <- patchwork::wrap_plots(chart_regions(), ncol = 1, heights = c({heights})) +",
        f"    patchwork::plot_annotation({page_labs}, theme = {theme_call(page_theme)})",
        "  patchwork::patchworkGrob(page)",
        "}",
    ]
    return "\n".join(head), "\n".join(marks), "\n".join(tail)


# --------------------------------------------------------------------------- #
# Matplotlib scaffold
# --------------------------------------------------------------------------- #


def _matplotlib_scaffold(spec: dict[str, Any]) -> tuple[str, str, str]:
    fonts = spec["font_pt"]
    fmt = spec["number_format"]
    width, height, dpi = spec["width_px"], spec["height_px"], spec["dpi"]
    reserved = spec["reserved_px"]
    horizontal = spec["orientation"] == "horizontal"
    numeric = (["start", "end"] if spec["interval"] else ["value"]) + list(spec["label_formats"])
    head = [
        _SCAFFOLD_BANNER,
        "import csv",
        "from datetime import date",
        "",
        "import matplotlib",
        'matplotlib.use("Agg")',
        "import matplotlib.dates as mdates",
        "import matplotlib.pyplot as plt",
        "from matplotlib.ticker import FuncFormatter",
        "",
        f"CATEGORIES = {spec['category_order']!r}",
        "# Colours: PALETTE[\"<series>\"] by name, INK for a single-colour mark.",
        f"PALETTE = {spec['palette']!r}",
        f"INK = {(spec['ordered'][0] if spec['ordered'] else '#1a1a1a')!r}",
        "# Text: fontsize=LABEL_PT for labels and values, ANNOTATION_PT for a free annotation.",
        f"LABEL_PT = {fonts['label']}",
        f"ANNOTATION_PT = {fonts['annotation']}",
        "# Text on a mark: color=ON_INK[series] - the ink that reads on that fill.",
        f"ON_INK = {spec['on_ink']!r}",
        "",
        "",
        *_py_formatter("fmt_value", fmt, "Format any value you print at the planned precision."),
        *[line for name, f in spec["label_formats"].items()
          for line in _py_formatter(f"fmt_{name}", f, f"Format {name}: a label measure, in its own units.")],
        "def pos(row):",
        '    """The x position of a row: category index, date, or number."""',
        {"date": "    return date.fromisoformat(row['category'])",
         "continuous": "    return float(row['category'])",
         "discrete": "    return CATEGORIES.index(row['category'])"}[spec["x_kind"]],
        "",
        "",
        "def _load():",
        f"    with open({spec['data_path']!r}, newline='', encoding='utf-8') as handle:",
        "        rows = list(csv.DictReader(handle))",
        "    for row in rows:",
        f"        for key in {numeric!r}:",
        "            row[key] = float(row[key]) if row.get(key) not in ('', None) else None",
        "    return rows",
        "",
        "",
        "PLOT_DATA = _load()",
        "",
        "",
        f"def stack(ax, rows, width=0.6, horizontal={horizontal}):",
        '    """Draw stacked bars in series order from the baseline; return (row, position, mid, ink) per segment."""',
        "    base, placed = {}, []",
        "    for name in list(PALETTE) or [None]:",
        "        for row in rows:",
        "            if name is not None and row.get('series') != name:",
        "                continue",
        "            x, start = pos(row), base.get(pos(row), 0.0)",
        "            colour = PALETTE.get(row.get('series'), INK)",
        "            if horizontal:",
        "                ax.barh(x, row['value'], left=start, height=width, color=colour)",
        "            else:",
        "                ax.bar(x, row['value'], bottom=start, width=width, color=colour)",
        "            placed.append((row, x, start + row['value'] / 2, ON_INK.get(row.get('series'), '#1a1a1a')))",
        "            base[x] = start + row['value']",
        "    return placed",
        "",
    ]
    marks = [
        "# Draw on ax from rows (one panel's rows). x = pos(row), y = row['value'];",
        "# stacked bars: placed = stack(ax, rows), labels at each returned mid in its ink.",
        "# For a horizontal chart use ax.barh / swap x and y. Columns: " + ", ".join(spec["columns"]) + ".",
        "# Marks and labels only - no titles, axis labels, limits, ticks or spines.",
        "def chart_marks(ax, rows):",
        "    pass",
    ]
    value_axis = "xaxis" if horizontal else "yaxis"
    cat_axis = "yaxis" if horizontal else "xaxis"
    titles = spec["axis_titles"]
    finish = [
        _SCAFFOLD_BANNER,
        "def _finish(ax, panel):",
        "    for side in ('top', 'right', 'left'):",
        "        ax.spines[side].set_visible(False)",
        "    ax.spines['bottom'].set_color('#b3b3b3')",
        f"    ax.tick_params(labelsize={fonts['axis']}, colors='#4d4d4d', length=0)",
        f"    ax.set_facecolor({spec['background']!r})",
        f"    ax.set_xlabel({(titles.get('x') or '')!r}, fontsize={fonts['axis']}, color='#4d4d4d')",
        f"    ax.set_ylabel({(titles.get('y') or '')!r}, fontsize={fonts['axis']}, color='#4d4d4d')",
        f"    ax.{value_axis}.set_major_formatter(FuncFormatter(lambda v, _: fmt_value(v)))",
        f"    ax.grid(axis={'x' if horizontal else 'y'!r}, color='#e5e5e5', linewidth=0.6)",
        "    ax.set_axisbelow(True)",
    ]
    if spec["x_kind"] == "discrete":
        # The same 0.6-slot padding ggplot gives a discrete axis, so end labels have room.
        finish += [
            f"    ax.set_{'yticks' if horizontal else 'xticks'}(range(len(CATEGORIES)), CATEGORIES"
            + (", rotation=45, ha='right'" if spec["rotate_x_labels"] and not horizontal else "") + ")",
            f"    ax.set_{'ylim' if horizontal else 'xlim'}(-0.6, len(CATEGORIES) - 0.4)",
        ]
    elif spec["x_kind"] == "date":
        finish += [
            "    locator = mdates.AutoDateLocator()",
            f"    ax.{cat_axis}.set_major_locator(locator)",
            f"    ax.{cat_axis}.set_major_formatter(mdates.ConciseDateFormatter(locator))",
        ]
    if spec["zero_baseline"]:
        finish.append(f"    ax.set_{'xlim' if horizontal else 'ylim'}(left=0)" if horizontal else "    ax.set_ylim(bottom=0)")
    if spec["hide_value_axis"]:
        finish += [f"    ax.{value_axis}.set_visible(False)", "    ax.grid(False)"]
    if spec["identification"] == "legend":
        finish.append("    ax.legend(frameon=False, loc='upper left', fontsize=%s)" % fonts["axis"])
    finish += [
        "    if panel:",
        f"        ax.set_title(panel, loc='left', fontsize={fonts['axis']}, fontweight='bold')",
        "",
        "",
        "def build_chart():",
        f"    ncol, nrow = {spec['facet_ncol']}, {spec['facet_nrow']}",
        f"    fig, axes = plt.subplots(nrow, ncol, figsize=({width} / {dpi}, {height} / {dpi}), dpi={dpi},",
        f"                             squeeze=False, sharey={spec['facet_scales'] in ('fixed', 'free_x')})",
        f"    fig.patch.set_facecolor({spec['background']!r})",
        f"    panels = {spec['facet_order']!r} or ['']",
        "    for ax, panel in zip(axes.flat, panels):",
        "        chart_marks(ax, [r for r in PLOT_DATA if not panel or r.get('facet') == panel])",
        "        _finish(ax, panel)",
        "    for ax in list(axes.flat)[len(panels):]:",
        "        ax.set_visible(False)",
        "    fig.subplots_adjust(left={:.4f}, right={:.4f}, top={:.4f}, bottom={:.4f}, hspace=0.45, wspace=0.25)".format(
            reserved["left"] / width, 1 - reserved["right"] / width,
            1 - reserved["top"] / height, reserved["bottom"] / height,
        ),
        f"    margin_x, margin_y = {spec['plot_margin_px']['left']} / {width}, {spec['plot_margin_px']['top']} / {height}",
        f"    fig.suptitle({spec['title']!r}, x=margin_x, y=1 - margin_y, ha='left', va='top',",
        f"                 fontsize={fonts['title']}, fontweight='bold', color='#1a1a1a')",
    ]
    if spec["subtitle"]:
        finish.append(
            f"    fig.text(margin_x, 1 - margin_y - {fonts['title'] * 1.6} / 72 * {dpi} / {height}, {spec['subtitle']!r},"
            f" ha='left', va='top', fontsize={fonts['subtitle']}, color='#4d4d4d')"
        )
    if spec["caption"]:
        finish.append(
            f"    fig.text(margin_x, margin_y, {spec['caption']!r}, ha='left', va='bottom',"
            f" fontsize={fonts['caption']}, color='#6b6b6b')"
        )
    finish.append("    return fig")
    return "\n".join(head), "\n".join(marks), "\n".join(finish)


# --------------------------------------------------------------------------- #
# Public tools
# --------------------------------------------------------------------------- #


def _source_parts(text: str) -> tuple[str, str, str] | None:
    if MARKS_BEGIN not in text or MARKS_END not in text:
        return None
    head, rest = text.split(MARKS_BEGIN, 1)
    body, tail = rest.split(MARKS_END, 1)
    return head, body, tail


def scaffold_chart(
    output_dir: str,
    plot_data_path: str,
    public_copy: dict[str, Any],
    layout: dict[str, Any] | None = None,
    frame: dict[str, Any] | None = None,
    colours: Any = None,
    number_format: dict[str, Any] | None = None,
    identification: str = "direct_labels",
    value_labels: int = 0,
    x_kind: str = "discrete",
    orientation: str | None = None,
    zero_baseline: bool = False,
    value_encoding: str = "position",
    background: str = "#FFFFFF",
    renderer: str = "ggplot2",
    source_name: str | None = None,
    label_formats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the chart source with every planned setting applied and one slot for the marks."""
    if renderer not in ("ggplot2", "matplotlib"):
        raise ValueError("renderer must be ggplot2 or matplotlib")
    warnings: list[str] = []
    # Routing scalars arrive as a model wrote them. Read them the way the routing block is read -
    # a near-miss spelling resolves, an unknown word takes the default - and say so, so a stray
    # word never turns the build off the scaffold.
    planned = {"identification_strategy": identification, "x_kind": x_kind, "value_encoding": value_encoding,
               "value_labels": value_labels, "zero_baseline": zero_baseline}
    read = {key: handoff._coerce_for(key, raw) for key, raw in planned.items()}
    for key, raw in planned.items():
        token = str(raw).strip().strip("`'\"").lower().replace(" ", "_").replace("-", "_")
        unread = (token not in handoff.ENUM_ROUTING_KEYS[key] if key in handoff.ENUM_ROUTING_KEYS
                  else not re.search(r"\d", token) if key in handoff.INT_ROUTING_KEYS
                  else handoff.coerce_bool(raw) is None)
        if unread:
            warnings.append(f"{key} {raw!r} is not a word the scaffold knows; read as {read[key]!r}")
    identification, x_kind, value_encoding = read["identification_strategy"], read["x_kind"], read["value_encoding"]
    value_labels, zero_baseline = int(read["value_labels"]), bool(read["zero_baseline"])
    public_copy = dict(public_copy or {})
    if not public_copy.get("title"):
        warnings.append("public_copy has no title; the chart is drawn without one")

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    data_source = Path(plot_data_path).expanduser().resolve()
    columns, rows = _read_plot_data(data_source)
    interval = {"start", "end"} <= set(columns)
    if "category" not in columns or not ("value" in columns or interval):
        raise ValueError("plot data must be the prepare_plot_data frame (category, and value or start/end)")
    roles_path = data_source.with_suffix(".json")
    roles = json.loads(roles_path.read_text(encoding="utf-8")) if roles_path.is_file() else {}
    label_units = {name: unit for name, unit in (roles.get("labels") or {}).items() if name in columns}
    layout = layout or {}
    # Panel groups the layout set apart (an overview above its detail) are drawn as one native
    # plot per region, each from its own rows, composed on one page under one frame.
    regions = [dict(r) for r in layout.get("regions") or []]
    region_of, region_warning = _region_membership(regions, _first_seen(rows, "category"))
    if region_warning:
        warnings.append(region_warning)
    if region_of and renderer != "ggplot2":
        warnings.append("panel-group regions are composed on ggplot2 only; matplotlib draws one grid")
        region_of = {}
    if region_of:
        regions = [r for r in regions if r.get("role") in set(region_of.values())]
        columns = columns + ["region"]
        for row in rows:
            row["region"] = region_of[row["category"]]

    # Type the x column. A time axis parsed to real dates gets the renderer's own breaks,
    # so a monthly series never draws one tick per month.
    if x_kind == "date":
        parsed = {row["category"]: _parse_date(row["category"]) for row in rows}
        unparsed = [label for label, value in parsed.items() if value is None]
        if unparsed:
            warnings.append(f"x_kind date: could not read {unparsed[:3]} as dates; drawn as a discrete axis")
            x_kind = "discrete"
        else:
            for row in rows:
                row["category"] = parsed[row["category"]].isoformat()
    elif x_kind == "continuous":
        try:
            [float(row["category"]) for row in rows]
        except ValueError:
            warnings.append("x_kind continuous: category is not numeric; drawn as a discrete axis")
            x_kind = "discrete"
    data_path = destination / "chart-data.csv"
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    series_order = _first_seen(rows, "series") if "series" in columns else []
    palette, ordered, stops = _palette(colours, series_order)
    if value_encoding == "colour" and not stops:
        warnings.append("value_encoding colour needs recommend_continuous_scale stops; none supplied")

    width = int(layout.get("width_px") or PROFILES["chat"]["width_px"])
    height = int(layout.get("height_px") or PROFILES["chat"]["height_px"])
    dpi = int(layout.get("dpi") or PROFILES["chat"]["dpi"])
    fonts = {**FONT_PT, **house_font_pt(width, height), **(layout.get("font_pt") or {})}
    if not frame:
        frame = reserve_frame(
            title=public_copy.get("title", ""), subtitle=public_copy.get("subtitle", ""),
            caption=public_copy.get("caption", ""), width_px=width, height_px=height, dpi=dpi,
            font_pt=fonts,
        )

    facet_order = _first_seen(rows, "facet") if "facet" in columns else []
    per_panel = [sum(1 for r in rows if r.get("facet", "") == f) for f in (facet_order or [""])]
    fewest_marks = min(per_panel) if per_panel else 0
    hide_value_axis = value_labels > 0 and value_labels >= min(_REDUNDANT_AXIS_MIN_LABELS, max(1, fewest_marks))
    horizontal = (orientation or layout.get("bar_orientation") or "vertical") == "horizontal"

    axis_titles = {k: v for k, v in dict(public_copy.get("axis_titles") or {}).items() if v}
    value_key = "x" if horizontal else "y"
    if hide_value_axis and axis_titles.pop(value_key, None):
        warnings.append("the value axis is hidden, so its declared axis title is not drawn")

    # Frame text is drawn as reserve_frame wrapped it, so the reserved bands match the pixels.
    wrapped = {b.get("role"): b.get("wrapped_text") for b in frame.get("frame_blocks") or []}
    title = str(wrapped.get("title") or public_copy["title"])
    caption = str(wrapped.get("caption") or public_copy.get("caption") or "")
    subtitle = str(wrapped.get("subtitle") or public_copy.get("subtitle") or "")
    if identification == "subtitle_key" and renderer == "ggplot2":
        subtitle = _subtitle_key(subtitle, palette).replace("\n", "<br>")
    elif identification == "subtitle_key":
        warnings.append("subtitle_key colours are drawn on ggplot2 only; matplotlib draws the subtitle plain")

    # Room for labels past the far end of the panel. Series names direct-labelled at the line
    # ends (and values at a horizontal bar's end) sit beyond the last data position; the axis's
    # own expansion holds some of that, the rest is reserved in the margin before anything draws,
    # so the model never has to pull labels back over the marks to keep them on the canvas.
    fmt = _number_format(number_format)
    geometry = ("start", "end") if interval else ("value",)
    shown = [_format_number(float(r[k]), fmt) for r in rows for k in geometry if r.get(k) not in ("", None)]
    label_fmts = _label_formats(rows, label_units, label_formats or {})
    value_chars = max((len(v) for v in shown), default=0)
    end_chars = 0
    if identification == "direct_labels" and series_order and not horizontal:
        end_chars = max(len(s) for s in series_order) + (2 + value_chars if value_labels else 0)
    elif horizontal and value_labels:
        end_chars = value_chars
    margin_px = dict(frame["plot_margin_px"])
    reserved_px = dict(frame.get("reserved_px") or margin_px)
    extra = 0.0
    if end_chars:
        need = end_chars * char_px(fonts["label"], dpi) + pt_to_px(fonts["label"], dpi) * 0.6
        panel_w = width - float((frame.get("reserved_px") or margin_px)["left"]) - float(margin_px["right"])
        n_slots = len(_first_seen(rows, "category"))
        expansion = (0.6 * panel_w / max(1.2, n_slots + 0.2)) if x_kind == "discrete" and not horizontal else 0.05 * panel_w
        extra = max(0.0, need - expansion)
        margin_px["right"] = round(float(margin_px["right"]) + extra, 1)
        reserved_px["right"] = round(float(reserved_px["right"]) + extra, 1)

    spec = {
        "data_path": str(data_path),
        "columns": columns,
        "category_order": _first_seen(rows, "category"),
        "series_order": series_order,
        "facet_order": facet_order,
        "palette": palette,
        "on_ink": {name: better_ink(hexc)[0] for name, hexc in palette.items()},
        "ordered": ordered,
        "stops": stops,
        "number_format": fmt,
        "font_pt": fonts,
        "plot_margin_px": margin_px,
        "reserved_px": reserved_px,
        "width_px": width,
        "height_px": height,
        "dpi": dpi,
        "x_kind": x_kind,
        "orientation": "horizontal" if horizontal else "vertical",
        "zero_baseline": bool(zero_baseline),
        "value_encoding": value_encoding,
        "identification": identification,
        "hide_value_axis": hide_value_axis,
        "rotate_x_labels": bool(layout.get("rotate_x_labels")),
        "wrap_label_chars": int(layout.get("wrap_y_labels_chars") or 0),
        "facet_ncol": int(layout.get("facet_ncol") or 1),
        "facet_nrow": int(layout.get("facet_nrow") or max(1, len(facet_order))),
        "facet_scales": str(layout.get("facet_scales") or "fixed"),
        "title": title,
        "subtitle": subtitle,
        "caption": caption,
        "axis_titles": axis_titles,
        "background": background,
        "interval": interval,
        "label_formats": label_fmts,
        "regions": [],
    }
    if facet_order and not layout.get("facet_ncol"):
        spec["facet_ncol"] = max(1, round(len(facet_order) ** 0.5))
        spec["facet_nrow"] = -(-len(facet_order) // spec["facet_ncol"])
    spec["strip_wrap_chars"] = _strip_wrap_chars(
        facet_order, float(frame["plot_area"]["width"]) - extra, spec["facet_ncol"], fonts["axis"], dpi,
    ) if facet_order and frame.get("plot_area") else 0

    if region_of:
        spec["regions"] = _region_boxes(regions, frame, margin_px, width, height, facet_order, rows)
        # Regions of one measure are read against each other, so they share the value range unless
        # the layout freed the value scale: an overview bar is never drawn to its own full width.
        points = [float(r[k]) for r in rows for k in geometry if r.get(k) not in ("", None)]
        if points and spec["facet_scales"] in ("fixed", "free_x"):
            spec["shared_limits"] = [min(points + [0.0]) if zero_baseline else min(points), max(points)]

    build = _ggplot_scaffold if renderer == "ggplot2" else _matplotlib_scaffold
    head, marks, tail = build(spec)
    suffix = ".R" if renderer == "ggplot2" else ".py"
    source = destination / (source_name or f"chart{suffix}")
    source.write_text(f"{head}\n{MARKS_BEGIN}\n{marks}\n{MARKS_END}\n{tail}\n", encoding="utf-8")
    sidecar = source.with_name(source.name + ".scaffold.json")
    sidecar.write_text(
        json.dumps(
            {
                "renderer": renderer,
                "head": f"{head}\n",
                "tail": f"\n{tail}\n",
                "value_labels": int(value_labels) if hide_value_axis else 0,
                "palette": ordered or stops,
                "series_palette": palette,
                "orientation": spec["orientation"],
                "value_encoding": value_encoding,
                "label_pt": fonts["label"],
                "dimensions": {"width_px": width, "height_px": height, "dpi": dpi},
                "background": background,
                "regions": [{"role": r["role"], "width_px": r["width"], "height_px": r["height"]}
                            for r in spec["regions"]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decided = [
        f"canvas {width}x{height}px at {dpi}dpi; title {fonts['title']}pt, axis {fonts['axis']}pt, labels {fonts['label']}pt, annotations {fonts['annotation']}pt",
        f"x axis {x_kind}{' (flipped horizontal)' if horizontal else ''}; value axis "
        + ("hidden - the planned value labels carry the reading" if hide_value_axis else "shown"),
        f"palette {'continuous ' + str(len(stops)) + ' stops' if stops else (palette or ordered)}",
        f"right margin {margin_px['right']}px (room for end labels)",
        "axis titles " + (", ".join(f"{k}: {v}" for k, v in spec["axis_titles"].items() if v) or "none"),
    ]
    decided += [f"label measure {name}: fmt_{name}() {_format_number(1234.5, f)}" for name, f in label_fmts.items()]
    if spec["regions"]:
        decided.append("regions " + ", ".join(f"{r['role']} {r['width']}x{r['height']}px" for r in spec["regions"]))
    # The frame as drawn: the end-label room narrows the plot area, so downstream placement and
    # the inspection contract read this, not the pre-scaffold reserve_frame result.
    drawn_frame = {**frame, "plot_margin_px": margin_px, "reserved_px": reserved_px}
    if extra and frame.get("plot_area"):
        drawn_frame["plot_area"] = {**frame["plot_area"], "width": round(float(frame["plot_area"]["width"]) - extra, 1)}
    return {
        "source_path": str(source),
        "frame": drawn_frame,
        "scaffold_path": str(sidecar),
        "chart_data_path": str(data_path),
        "renderer": renderer,
        "dimensions": {"width_px": width, "height_px": height, "dpi": dpi},
        "value_axis_hidden": hide_value_axis,
        # Each region is a native plot (chart_regions() in the source) for a compositor to place at
        # its box under the page frame; build_chart() composes the same boxes into one image.
        "regions": [
            {"role": r["role"], "function": "chart_regions", "x": r["x"], "y": r["y"],
             "width_px": r["width"], "height_px": r["height"], "categories": r["categories"]}
            for r in spec["regions"]
        ],
        "decided": decided,
        "marks_brief": _marks_brief(source.name, renderer, interval, label_fmts, len(spec["regions"]),
                                    value_labels if hide_value_axis else 0),
        "warnings": warnings,
    }


_R_CHECK = r'''
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(grid))
setup <- jsonlite::fromJSON(args[[3]])
width_px <- as.numeric(setup$width_px); height_px <- as.numeric(setup$height_px); dpi <- as.numeric(setup$dpi)
# Text is measured on the device the render uses, at the delivery size, so a label's box is its ink.
if (requireNamespace("ragg", quietly = TRUE)) {
  ragg::agg_png(tempfile(fileext = ".png"), width = width_px, height = height_px, units = "px", res = dpi)
} else {
  pdf(NULL, width = width_px / dpi, height = height_px / dpi)
}
out <- list(error = NULL, non_layers = list(), geom_label = 0L, text_rows = 0L,
            mark_colours = list(), text_sizes = list(), unmapped = list(), wrong_mark = list(),
            stack_order = FALSE, surfaces = list(), detached = list(), stretch = list(), spans = list())
as_hex <- function(x) tryCatch(grDevices::rgb(t(grDevices::col2rgb(x)), maxColorValue = 255), error = function(e) as.character(x))
flat <- function(x) if (is.list(x) && !inherits(x, "gg")) do.call(c, lapply(x, flat)) else list(x)
is_text <- function(layer) inherits(layer$geom, "GeomText") || inherits(layer$geom, "GeomLabel") ||
  grepl("Text|Label", class(layer$geom)[1])
num <- function(v, fallback) { v <- suppressWarnings(as.numeric(v)); if (!length(v) || !is.finite(v[1])) fallback else v[1] }
check_plot <- function(out, plot, width_px, height_px) {
  for (layer in plot$layers) {
    data <- if (is.data.frame(layer$data)) layer$data else if (is.function(layer$data)) {
      tryCatch(layer$data(plot$data), error = function(e) NULL)
    } else plot$data
    if (is.null(data) || !all(keys %in% names(data))) next
    mapping <- if (is.null(layer$mapping)) aes() else layer$mapping
    mapping[["dvzobs"]] <- rlang::new_quosure(as.call(c(quote(.dvz_obs), lapply(keys, as.name))), environment())
    layer$mapping <- mapping
  }
  b <- ggplot_build(plot)
  gt <- ggplotGrob(plot)
  for (i in seq_along(plot$layers)) if (is_text(plot$layers[[i]])) out$text_rows <- out$text_rows + nrow(b$data[[i]])
  # How far the marks travel along the value axis (y before any coord_flip), against the data's
  # range, both in the value scale's own space (a log axis compares logs with logs).
  span <- list(value = NULL, mark = NULL)
  if (has_geom) {
    scale_y <- b$layout$panel_scales_y[[1]]
    trans <- tryCatch(scale_y$get_transformation(), error = function(e) NULL)
    raw <- geom_values(plot$data)
    values <- if (is.null(trans)) raw else suppressWarnings(trans$transform(raw))
    values <- values[is.finite(values)]
    if (length(values)) span$value <- diff(range(values))
  }
  ys <- unlist(lapply(seq_along(plot$layers), function(i) {
    d <- b$data[[i]]
    if (is_text(plot$layers[[i]])) return(NULL)
    unlist(lapply(intersect(c("y", "ymin", "ymax", "yend"), names(d)), function(k) as.numeric(d[[k]])))
  }))
  ys <- ys[is.finite(ys)]
  if (length(ys)) span$mark <- diff(range(ys))
  out$spans[[length(out$spans) + 1]] <- span
  # A mapped colour whose values the palette does not name falls to the scale's NA grey.
  named <- names(palette)
  if (!is.null(named)) for (layer in plot$layers) for (a in c("colour", "fill")) {
    m <- layer$mapping[[a]]
    if (is.null(m)) next
    data <- if (is.data.frame(layer$data)) layer$data else plot$data
    vals <- tryCatch(rlang::eval_tidy(m, data = data), error = function(e) NULL)
    if (!inherits(vals, "AsIs") && (is.character(vals) || is.factor(vals)) && !all(as.character(vals) %in% named))
      out$unmapped[[length(out$unmapped) + 1]] <- rlang::as_label(m)
  }

  # ---- Native geometry: panels, marks and text boxes in device px (origin top-left) ----
  resolve_tracks <- function(track_units, total_px) {
    types <- unitType(track_units)
    fixed <- convertUnit(track_units, "in", valueOnly = TRUE) * dpi
    null <- types == "null"
    weights <- rep(0, length(track_units))
    if (any(null)) weights[null] <- as.numeric(track_units[null])
    remaining <- max(0, total_px - sum(fixed[!null]))
    if (sum(weights) > 0) fixed[null] <- remaining * weights[null] / sum(weights)
    fixed
  }
  widths <- resolve_tracks(gt$widths, width_px)
  heights <- resolve_tracks(gt$heights, height_px)
  x_before <- c(0, cumsum(widths)); y_before <- c(0, cumsum(heights))
  boxes <- list()
  for (i in seq_len(nrow(gt$layout))) {
    item <- gt$layout[i, ]
    if (!startsWith(item$name, "panel")) next
    boxes[[item$name]] <- c(x_before[item$l], y_before[item$t],
                            sum(widths[item$l:item$r]), sum(heights[item$t:item$b]))
  }
  lay <- b$layout$layout
  flip <- inherits(plot$coordinates, "CoordFlip")
  to_px <- list(); panel_box <- list()
  for (k in seq_len(nrow(lay))) {
    pp <- b$layout$panel_params[[k]]
    name <- if (length(boxes) == 1) names(boxes)[1] else paste0("panel-", lay$COL[k], "-", lay$ROW[k])
    box <- boxes[[name]]
    xr <- pp$x.range; yr <- pp$y.range
    if (is.null(box) || length(xr) != 2 || length(yr) != 2 || !diff(xr) || !diff(yr)) next
    panel_box[[as.character(lay$PANEL[k])]] <- box
    # coord_flip reports screen ranges: x.range runs across (data y), y.range up (data x).
    to_px[[as.character(lay$PANEL[k])]] <- local({
      bx <- box; hx <- xr; vy <- yr
      function(x, y) {
        across <- if (flip) y else x
        up <- if (flip) x else y
        list(x = bx[1] + (across - hx[1]) / diff(hx) * bx[3],
             y = bx[2] + bx[4] - (up - vy[1]) / diff(vy) * bx[4])
      }
    })
  }
  background <- as.character(setup$background)
  mix <- function(top, alpha, under) {
    a <- grDevices::col2rgb(top) / 255; u <- grDevices::col2rgb(under) / 255
    grDevices::rgb(t(alpha * a + (1 - alpha) * u))
  }
  # Filled rectangles in draw order: later layers, and later rows, paint over earlier ones.
  rects <- list()
  for (i in seq_along(plot$layers)) {
    d <- b$data[[i]]
    if (is_text(plot$layers[[i]]) || !all(c("xmin", "xmax", "ymin", "ymax", "fill") %in% names(d))) next
    for (r in seq_len(nrow(d))) {
      f <- to_px[[as.character(d$PANEL[r])]]
      if (is.null(f) || is.na(d$fill[r])) next
      a <- f(c(d$xmin[r], d$xmax[r]), c(d$ymin[r], d$ymax[r]))
      # A band drawn to -Inf/Inf spans the panel.
      box <- panel_box[[as.character(d$PANEL[r])]]
      a$x <- pmin(pmax(a$x, box[1]), box[1] + box[3]); a$y <- pmin(pmax(a$y, box[2]), box[2] + box[4])
      if (!all(is.finite(c(a$x, a$y)))) next
      fill_alpha <- grDevices::col2rgb(d$fill[r], alpha = TRUE)[4] / 255
      alpha <- num(if ("alpha" %in% names(d)) d$alpha[r] else NA, 1) * fill_alpha
      obs <- if ("dvzobs" %in% names(d)) d$dvzobs[r] else NA
      # A value mark is one whose length along the value axis is its own observation's value;
      # a band or background tile drawn behind the data is not.
      value_mark <- !is.na(obs) && has_geom &&
        isTRUE(abs(abs(d$ymax[r] - d$ymin[r]) - obs_len(obs)) <= 1e-6 * max(1, obs_len(obs)))
      rects[[length(rects) + 1]] <- list(panel = as.character(d$PANEL[r]), x0 = min(a$x), x1 = max(a$x),
        y0 = min(a$y), y1 = max(a$y), fill = as_hex(d$fill[r]), alpha = alpha, obs = obs,
        value_mark = value_mark, layer = i)
    }
  }
  # Where each observation's own marks sit along the value axis (screen px), to test attachment.
  value_px <- function(p) if (flip) p$x else p$y
  own_marks <- list()
  for (i in seq_along(plot$layers)) {
    d <- b$data[[i]]
    if (is_text(plot$layers[[i]]) || !("dvzobs" %in% names(d))) next
    for (r in seq_len(nrow(d))) {
      f <- to_px[[as.character(d$PANEL[r])]]
      if (is.null(f) || is.na(d$dvzobs[r])) next
      span <- if (all(c("ymin", "ymax", "xmin", "xmax") %in% names(d))) {
        value_px(f(c(d$xmin[r], d$xmax[r]), c(d$ymin[r], d$ymax[r])))
      } else if (all(c("x", "y") %in% names(d))) value_px(f(d$x[r], d$y[r])) else NULL
      if (is.null(span) || !all(is.finite(span))) next
      key <- paste(d$PANEL[r], d$dvzobs[r])
      own_marks[[key]] <- c(own_marks[[key]], range(span))
    }
  }
  # A layer that is not a data mark (a shaded band, a backdrop tile) must not set the value
  # range: finite extents far past what the data marks reach stretch the axis and flatten them.
  if (has_geom) {
    data_y <- c(); other <- list()
    for (i in seq_along(plot$layers)) {
      d <- b$data[[i]]
      if (is_text(plot$layers[[i]])) next
      cols <- intersect(c("y", "ymin", "ymax", "yend"), names(d))
      for (r in seq_len(nrow(d))) {
        ys_r <- unlist(lapply(cols, function(k) as.numeric(d[[k]][r])))
        ys_r <- ys_r[is.finite(ys_r)]
        if (!length(ys_r)) next
        obs <- if ("dvzobs" %in% names(d)) d$dvzobs[r] else NA
        at <- obs_at(obs)
        own <- !is.na(obs) && (any(abs(outer(ys_r, at, "-")) <= 1e-9 * max(1, abs(at), na.rm = TRUE), na.rm = TRUE) ||
          (all(c("ymin", "ymax") %in% names(d)) && isTRUE(abs(abs(d$ymax[r] - d$ymin[r]) - obs_len(obs)) <= 1e-6 * max(1, obs_len(obs)))))
        if (own) data_y <- c(data_y, ys_r) else other[[class(plot$layers[[i]]$geom)[1]]] <- c(other[[class(plot$layers[[i]]$geom)[1]]], ys_r)
      }
    }
    if (length(data_y)) {
      lo <- min(data_y, 0); hi <- max(data_y); span <- max(hi - lo, 1e-9)
      for (g in names(other)) {
        over <- max(other[[g]]) - hi; under <- lo - min(other[[g]])
        if (max(over, under) > 0.25 * span) out$stretch[[length(out$stretch) + 1]] <- list(geom = g,
          reach = signif(if (over >= under) max(other[[g]]) else min(other[[g]]), 4), lo = signif(lo, 4), hi = signif(hi, 4))
      }
    }
  }
  position_name <- function(layer) {
    p <- layer$position
    cls <- class(p)[1]
    if (inherits(p, "PositionDodge")) return(sprintf("position_dodge(width = %s)", format(num(p$width, 0.9))))
    if (inherits(p, "PositionStack")) return(if (inherits(p, "PositionFill")) "position_fill()" else "stack")
    if (inherits(p, "PositionIdentity")) return("no position adjustment")
    cls
  }
  just_value <- function(v, low_side) {
    if (is.numeric(v)) return(v)
    v <- tolower(as.character(v))
    if (v %in% c("left", "bottom")) return(0)
    if (v %in% c("right", "top")) return(1)
    if (v == "inward") return(if (low_side) 0 else 1)
    if (v == "outward") return(if (low_side) 1 else 0)
    num(v, 0.5)
  }
  describe <- function(obs) paste(vapply(keys, function(k) as.character(plot_data[[k]][obs]), ""), collapse = " / ")
  for (i in seq_along(plot$layers)) {
    if (!is_text(plot$layers[[i]])) next
    d <- b$data[[i]]
    for (r in seq_len(nrow(d))) {
      text <- as.character(d$label[r])
      f <- to_px[[as.character(d$PANEL[r])]]
      if (is.na(text) || !nzchar(text) || is.null(f)) next
      at <- f(d$x[r], d$y[r])
      if (!all(is.finite(c(at$x, at$y)))) next
      face <- if ("fontface" %in% names(d)) d$fontface[r] else 1
      gp <- gpar(fontsize = num(d$size[r], 3.87) * .pt,
                 lineheight = num(if ("lineheight" %in% names(d)) d$lineheight[r] else NA, 1.2),
                 fontface = if (is.numeric(face)) face else as.character(face))
      family <- if ("family" %in% names(d)) as.character(d$family[r]) else ""
      if (length(family) && !is.na(family) && nzchar(family)) gp$fontfamily <- family
      tg <- tryCatch(textGrob(text, gp = gp), error = function(e) textGrob(text, gp = gpar(fontsize = gp$fontsize)))
      w <- convertWidth(grobWidth(tg), "in", valueOnly = TRUE) * dpi
      h <- convertHeight(grobHeight(tg), "in", valueOnly = TRUE) * dpi
      if (abs((num(d$angle[r], 0) %% 180) - 90) < 45) { tmp <- w; w <- h; h <- tmp }
      ink <- as_hex(d$colour[r])
      if (inherits(plot$layers[[i]]$geom, "GeomBarValue")) {
        # bar_values decides inside/outside when drawn; replay that rule at the delivery size.
        stack <- bar_value_stack(d)
        bar <- f(c(d$xmin[r], d$xmax[r]), c(d$ymin[r], d$ymax[r]))
        along_px <- if (flip) bar$x else -bar$y
        cross_px <- if (flip) bar$y else bar$x
        place <- bar_value_place(min(along_px), max(along_px), diff(range(cross_px)),
          if (flip) w else h, if (flip) h else w, stack$dir[r], stack$stacked[r], stack$inner[r],
          0.3 * gp$fontsize / 72 * dpi)
        centre <- place$at + (0.5 - place$just) * (if (flip) w else h)
        cx <- if (flip) centre else mean(cross_px)
        cy <- if (flip) mean(cross_px) else -centre
        if (place$inside) ink <- as_hex(bar_value_ink(d$fill[r]))
      } else {
        box <- panel_box[[as.character(d$PANEL[r])]]
        hj <- just_value(d$hjust[r], at$x < box[1] + box[3] / 2)
        vj <- just_value(d$vjust[r], at$y > box[2] + box[4] / 2)
        cx <- at$x + (0.5 - hj) * w
        cy <- at$y - (0.5 - vj) * h
      }
      # The surface behind the text: the page, painted over by every fill under its centre.
      surface <- background
      top <- NULL
      for (m in rects) {
        if (m$panel != as.character(d$PANEL[r]) || cx < m$x0 || cx > m$x1 || cy < m$y0 || cy > m$y1) next
        surface <- mix(m$fill, m$alpha, surface)
        if (m$alpha >= 0.5) top <- m
      }
      out$surfaces[[length(out$surfaces) + 1]] <- list(text = text, ink = ink, surface = surface,
        on_mark = !is.null(top), font_pt = gp$fontsize,
        bar_values = inherits(plot$layers[[i]]$geom, "GeomBarValue"))
      # A value label sitting on a value mark must be on its own observation's mark.
      own <- if ("dvzobs" %in% names(d)) d$dvzobs[r] else NA
      # A label drawn for an observation stays within reach of that observation's own mark:
      # a label moved lines away along the value axis (a stack applied to line labels, a
      # hand offset) reads as belonging to something else.
      reach <- own_marks[[paste(d$PANEL[r], own)]]
      if (!is.na(own) && length(reach)) {
        gap <- max(0, min(reach) - value_px(at), value_px(at) - max(reach))
        if (gap > 2.5 * h) out$detached[[length(out$detached) + 1]] <- list(text = text, own = describe(own),
          gap_px = round(gap), position = position_name(plot$layers[[i]]))
      }
      if (is.null(top) || !isTRUE(top$value_mark) || is.na(own) || identical(top$obs, own)) next
      has_own <- any(vapply(rects, function(m) isTRUE(m$value_mark) && identical(m$obs, own), TRUE))
      if (!has_own) next
      out$wrong_mark[[length(out$wrong_mark) + 1]] <- list(text = text, own = describe(own),
        on = describe(top$obs), position = position_name(plot$layers[[top$layer]]))
    }
  }
  # Stacked segments read in series order outward from the baseline.
  if (!is.null(named)) {
    by_colour <- setNames(named, toupper(unname(palette)))
    for (i in seq_along(plot$layers)) {
      d <- b$data[[i]]
      if (is_text(plot$layers[[i]]) || !all(c("xmin", "xmax", "ymin", "ymax", "fill") %in% names(d))) next
      d$key <- paste(d$PANEL, round((d$xmin + d$xmax) / 2, 6))
      for (k in unique(d$key)) {
        g <- d[d$key == k, ]
        if (nrow(g) < 2 || any(pmin(g$ymin, g$ymax) < 0)) next
        g <- g[order(pmin(g$ymin, g$ymax)), ]
        seen <- unname(by_colour[toupper(as_hex(g$fill))])
        seen <- seen[!is.na(seen)]
        if (length(seen) > 1 && !identical(seen, named[named %in% seen])) out$stack_order <- TRUE
      }
    }
  }
  out
}
tryCatch({
  source(args[[1]], local = .GlobalEnv)
  for (e in flat(chart_marks(plot_data))) {
    if (!inherits(e, "LayerInstance")) {
      out$non_layers[[length(out$non_layers) + 1]] <- class(e)[1]
      next
    }
    if (inherits(e$geom, "GeomLabel")) out$geom_label <- out$geom_label + 1L
    if (is_text(e)) {
      if (!is.null(e$aes_params$size)) out$text_sizes[[length(out$text_sizes) + 1]] <- e$aes_params$size * .pt
    } else {
      for (a in c("colour", "fill")) if (!is.null(e$aes_params[[a]]) && !is.na(e$aes_params[[a]][1]))
        out$mark_colours[[length(out$mark_colours) + 1]] <- as_hex(e$aes_params[[a]][1])
    }
  }
  # Tag every layer row with the observation it draws, as a numeric aesthetic (numeric, so it
  # never changes grouping), so a label and a bar are matched by identity, not by the number printed.
  keys <- intersect(c("category", "series", "facet"), names(plot_data))
  key_of <- function(frame) do.call(paste, c(lapply(keys, function(k) as.character(frame[[k]])), sep = "\r"))
  obs_keys <- key_of(plot_data)
  .dvz_obs <- function(...) match(do.call(paste, c(lapply(list(...), as.character), sep = "\r")), obs_keys)
  # An observation's geometry: its value (a mark from zero), or its two ends (an interval).
  interval <- all(c("start", "end") %in% names(plot_data))
  has_geom <- interval || is.numeric(plot_data$value)
  obs_at <- function(obs) if (interval) c(plot_data$start[obs], plot_data$end[obs]) else plot_data$value[obs]
  obs_len <- function(obs) if (interval) abs(plot_data$end[obs] - plot_data$start[obs]) else abs(plot_data$value[obs])
  geom_values <- function(d) if (interval) c(d$start, d$end) else d$value
  # Regions are native plots checked each at its own size; a single chart is one region.
  plots <- if (exists("chart_regions", mode = "function")) chart_regions() else {
    built <- build_chart()
    list(if (inherits(built, "ggplot")) built else built$plot)
  }
  sizes <- setup$regions
  for (k in seq_along(plots)) {
    w <- if (length(sizes)) as.numeric(sizes$width_px[k]) else width_px
    h <- if (length(sizes)) as.numeric(sizes$height_px[k]) else height_px
    out <- check_plot(out, plots[[k]], w, h)
  }
}, error = function(e) out$error <<- conditionMessage(e))
jsonlite::write_json(out, args[[2]], auto_unbox = TRUE, null = "null")
'''


def _check_ggplot(source: Path, record: dict[str, Any]) -> dict[str, Any]:
    rscript = shutil.which("Rscript")
    if rscript is None:
        return {"error": "Rscript is not available; the slot could not be built"}
    # Geometry is measured at the delivery size; a sidecar written before it was recorded
    # falls back to the chat profile.
    dims = record.get("dimensions") or {k: PROFILES["chat"][k] for k in ("width_px", "height_px", "dpi")}
    setup = {**dims, "background": record.get("background") or "#FFFFFF", "regions": record.get("regions") or []}
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "check.R"
        result = Path(tmp) / "check.json"
        setup_path = Path(tmp) / "setup.json"
        script.write_text(_R_CHECK, encoding="utf-8")
        setup_path.write_text(json.dumps(setup), encoding="utf-8")
        completed = subprocess.run(
            [rscript, str(script), str(source), str(result), str(setup_path)],
            capture_output=True, text=True, timeout=120, cwd=tmp,
        )
        if not result.exists():
            return {"error": completed.stderr.strip() or f"Rscript exited {completed.returncode}"}
        return json.loads(result.read_text(encoding="utf-8"))


def _check_matplotlib(source: Path, record: dict[str, Any]) -> dict[str, Any]:
    from matplotlib.collections import Collection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Rectangle
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt

    from .rendering import _load_module, _unpack_build

    out: dict[str, Any] = {"error": None, "non_layers": [], "geom_label": 0, "text_rows": 0,
                           "mark_colours": [], "text_sizes": []}
    try:
        module = _load_module(source)
        figure, _ = _unpack_build(module.build_chart())
    except Exception as exc:  # the model's code is what failed; report it, don't raise
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    values = [float(row[k]) for row in getattr(module, "PLOT_DATA", []) for k in ("value", "start", "end")
              if row.get(k) is not None]
    span: dict[str, Any] = {"value": max(values) - min(values) if values else None, "mark": None}
    out["spans"] = [span]
    horizontal = record.get("orientation") == "horizontal"
    along: list[float] = []
    try:
        for ax in figure.axes:
            if ax.get_visible():
                along += _mpl_value_coords(ax, horizontal, Line2D, Rectangle, Collection)
        finite = [v for v in along if math.isfinite(v)]
        if finite:
            span["mark"] = max(finite) - min(finite)
        for ax in figure.axes:
            if not ax.get_visible():
                continue
            out["text_rows"] += len(ax.texts)
            out["text_sizes"] += [t.get_fontsize() for t in ax.texts]
            out["geom_label"] += sum(1 for t in ax.texts if t.get_bbox_patch() is not None)
            artists = [*ax.lines, *ax.patches, *ax.collections]
            for artist in artists:
                if isinstance(artist, Line2D):
                    colours = [artist.get_color()]
                elif isinstance(artist, Patch):
                    colours = [artist.get_facecolor()]
                elif isinstance(artist, Collection):
                    colours = list(artist.get_facecolors()[:1]) or list(artist.get_edgecolors()[:1])
                else:
                    continue
                out["mark_colours"] += [mcolors.to_hex(c) for c in colours if c is not None and len(c)]
            out["stack_order"] = out.get("stack_order") or _mpl_stack_out_of_order(ax, record, Rectangle, mcolors)
            # Text reads against the surface behind its drawn box: the page, painted over by
            # every bar under the box's centre, in draw order.
            renderer = figure.canvas.get_renderer()
            bars = [p for p in ax.patches if isinstance(p, Rectangle)]
            for text in ax.texts:
                box = text.get_window_extent(renderer)
                cx, cy = (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2
                surface, on_mark = mcolors.to_rgb(record.get("background") or "#FFFFFF"), False
                for bar in bars:
                    extent = bar.get_window_extent(renderer)
                    if extent.x0 <= cx <= extent.x1 and extent.y0 <= cy <= extent.y1:
                        *rgb, alpha = mcolors.to_rgba(bar.get_facecolor())
                        surface = tuple(alpha * c + (1 - alpha) * u for c, u in zip(rgb, surface))
                        on_mark = on_mark or alpha >= 0.5
                out.setdefault("surfaces", []).append({
                    "text": text.get_text(),
                    "ink": mcolors.to_hex(text.get_color()),
                    "surface": mcolors.to_hex(surface),
                    "on_mark": on_mark,
                })
    finally:
        plt.close(figure)
    return out


def _mpl_value_coords(ax: Any, horizontal: bool, line: Any, rectangle: Any, collection: Any) -> list[float]:
    """Every value-axis coordinate the marks on ``ax`` reach (x for a horizontal chart)."""
    axis = 0 if horizontal else 1
    coords: list[float] = []
    for artist in ax.lines:
        if isinstance(artist, line):
            data = artist.get_xdata() if horizontal else artist.get_ydata()
            coords += [float(v) for v in data if isinstance(v, (int, float)) or hasattr(v, "__float__")]
    for patch in ax.patches:
        if isinstance(patch, rectangle):
            start, extent = (patch.get_x(), patch.get_width()) if horizontal else (patch.get_y(), patch.get_height())
            coords += [float(start), float(start + extent)]
    for artist in ax.collections:
        if not isinstance(artist, collection):
            continue
        offsets = artist.get_offsets()
        if len(offsets):
            coords += [float(point[axis]) for point in offsets]
        else:
            for path in artist.get_paths():
                coords += [float(point[axis]) for point in path.vertices]
    return coords


def _mpl_stack_out_of_order(ax: Any, record: dict[str, Any], rectangle: Any, mcolors: Any) -> bool:
    """True when a stacked bar's segments do not run in series order from the baseline."""
    order = list(record.get("series_palette") or {})
    by_colour = {hexc.lower(): name for name, hexc in (record.get("series_palette") or {}).items()}
    horizontal = record.get("orientation") == "horizontal"
    groups: dict[float, list[tuple[float, str]]] = {}
    for patch in ax.patches:
        if not isinstance(patch, rectangle):
            continue
        centre = patch.get_y() + patch.get_height() / 2 if horizontal else patch.get_x() + patch.get_width() / 2
        start = patch.get_x() if horizontal else patch.get_y()
        name = by_colour.get(mcolors.to_hex(patch.get_facecolor()).lower())
        if name is not None:
            groups.setdefault(round(centre, 6), []).append((start, name))
    for segments in groups.values():
        seen = [name for _start, name in sorted(segments)]
        if len(seen) > 1 and seen != [name for name in order if name in seen]:
            return True
    return False


def _is_neutral(hex_colour: str) -> bool:
    rgb = to_rgb(hex_colour)
    if rgb is None:
        return True
    _h, _l, s = colorsys.rgb_to_hls(*(channel / 255.0 for channel in rgb))
    return s < _NEUTRAL_SATURATION


def check_chart(source_path: str) -> dict[str, Any]:
    """Restore edited scaffold regions and check the model's marks slot on the built plot."""
    source = Path(source_path).expanduser().resolve()
    sidecar = source.with_name(source.name + ".scaffold.json")
    deviations: list[dict[str, str]] = []

    def deviate(code: str, message: str, severity: str = "major") -> None:
        deviations.append({"code": code, "severity": severity, "message": message})

    if not sidecar.is_file():
        # A hand-written chart skipped the settings the plan resolved; the fix is to start over
        # from the scaffold, not to patch this file.
        deviate(
            "UNSCAFFOLDED_BUILD",
            f"{source.name} was not written by scaffold_chart, so the planned fonts, scales, palette and "
            "margins are not applied. Run scaffold_chart and move only the geoms and labels into its marks slot.",
            "fatal",
        )
        return {"ok": False, "restored_scaffold": False, "deviations": deviations,
                "fix_list": _fix_list(deviations)}
    record = json.loads(sidecar.read_text(encoding="utf-8"))

    parts = _source_parts(source.read_text(encoding="utf-8"))
    restored = False
    if parts is None:
        deviate(
            "MARKS_SLOT_MISSING",
            "The marks markers are gone. Re-run scaffold_chart and write your layers between the markers only.",
            "fatal",
        )
        return {"ok": False, "restored_scaffold": False, "deviations": deviations,
                "fix_list": _fix_list(deviations)}
    head, body, tail = parts
    if head != record["head"] or tail != record["tail"]:
        source.write_text(f"{record['head']}{MARKS_BEGIN}{body}{MARKS_END}{record['tail']}", encoding="utf-8")
        restored = True

    found = _check_ggplot(source, record) if record["renderer"] == "ggplot2" else _check_matplotlib(source, record)
    if found.get("error"):
        message = " ".join(line.strip() for line in found["error"].splitlines() if line.strip()) or "build failed"
        hint = ""
        if "continuous scale" in message.lower() or "discrete value" in message.lower():
            hint = " The value axis is continuous: map y = value and x = category (the scaffold flips horizontal charts)."
        deviate("BUILD_ERROR", f"The chart does not build: {message.rstrip('.')}.{hint}", "fatal")
    for name in found.get("non_layers") or []:
        deviate(
            "MARKS_NON_LAYER",
            f"chart_marks returns a {name}. Delete it: the scaffold owns scales, coords, facets, labs and theme.",
        )
    if found.get("geom_label"):
        deviate("GEOM_LABEL", "Replace geom_label / boxed text with plain text: labels stand free, no box.")
    allowed = {c.lower() for c in record.get("palette") or []}
    stray = sorted({c.lower() for c in found.get("mark_colours") or []} - allowed)
    stray = [c for c in stray if not _is_neutral(c)]
    if stray:
        deviate(
            "COLOUR_NOT_IN_PALETTE",
            f"Marks use {', '.join(stray)}, which is not in the resolved palette. Colour marks from palette/ink "
            "(or a neutral grey for context) - never pick a hue by hand.",
        )
    floor = float(record.get("label_pt") or FONT_PT["label"]) * _MIN_TEXT_SHARE
    small = [s for s in found.get("text_sizes") or [] if s < floor]
    if small:
        deviate(
            "TEXT_TOO_SMALL",
            f"Text drawn at {min(small):.1f}pt, below the planned {record.get('label_pt')}pt. Use size = label_size.",
        )
    for expression in found.get("unmapped") or []:
        deviate(
            "COLOUR_UNMAPPED",
            f"colour/fill = {expression} maps values the palette does not name, so they draw in the scale's "
            "NA grey. Map colour to series, or split the rows into layers with a fixed colour each.",
        )
    # Text is judged against the surface actually behind it: a fill it sits on, or the page.
    palette_inks = {c.lower() for c in record.get("palette") or []}
    on_mark, on_page, from_bar_values = set(), set(), False
    for text in found.get("surfaces") or []:
        ratio = _contrast_ratio(text.get("ink"), text.get("surface")) or 99.0
        described = f"'{text['text']}' ({text['ink']} on {text['surface']})"
        # The inspection's rule: large text reads at 3:1, normal text needs 4.5:1.
        target = _MIN_ON_PAGE_CONTRAST if float(text.get("font_pt") or 0) >= _LARGE_TEXT_PT else _MIN_ON_MARK_CONTRAST
        if text.get("on_mark") and ratio < target:
            on_mark.add(described)
            from_bar_values = from_bar_values or bool(text.get("bar_values"))
        # On the page, only ink the slot chose (not a palette colour) is its to fix.
        elif not text.get("on_mark") and ratio < _MIN_ON_PAGE_CONTRAST and str(text.get("ink")).lower() not in palette_inks:
            on_page.add(described)
    if on_mark:
        deviate(
            "LOW_CONTRAST_ON_MARK",
            f"Text on a mark does not read on its fill: {', '.join(sorted(on_mark))}. Colour it with "
            "colour = on_fill_ink(series), or on_fill_ink() for a single-colour mark "
            "(Matplotlib: ON_INK[series]); a label too long for its mark goes past the mark's end instead."
            + (" bar_values takes its ink from its own fill: give it the bars' own fill mapping, or no fill "
               "for the single ink." if from_bar_values else ""),
        )
    if on_page:
        deviate(
            "LOW_CONTRAST_ON_PAGE",
            f"Text off any mark does not read on the page: {', '.join(sorted(on_page))}. On-fill ink only "
            "reads on its fill; colour text that sits on the page with ink or its series colour.",
        )
    if found.get("stack_order"):
        deviate(
            "STACK_ORDER",
            "Stacked segments do not run in series order from the baseline. Stack bars with "
            "position = stack and their labels with position = stack_mid (Matplotlib: stack(ax, rows)).",
        )
    for wrong in found.get("wrong_mark") or []:
        # Name the bars' own position adjustment, so the fix matches the drawn form (dodged
        # bars get dodged labels), never a stack the plan did not choose.
        position = wrong.get("position") or "no position adjustment"
        used = position if position == "no position adjustment" else f"position = {position}"
        same = "position = stack_mid" if position == "stack" else used
        deviate(
            "LABEL_ON_WRONG_MARK",
            f"Label '{wrong['text']}' belongs to {wrong['own']} but sits on the {wrong['on']} mark. "
            f"Its bars use {used}; give the labels the same data, group and {same}.",
            "fatal",
        )
    for label in found.get("detached") or []:
        moved = "" if label.get("position") == "no position adjustment" else (
            f" Its position = {label['position']} moves it; drop that adjustment.")
        deviate(
            "LABEL_OFF_ITS_MARK",
            f"Label '{label['text']}' is drawn {label['gap_px']}px along the value axis from its own mark "
            f"({label['own']}).{moved} Anchor a label at its own observation's value.",
        )
    for layer in found.get("stretch") or []:
        deviate(
            "DECORATION_STRETCHES_AXIS",
            f"A {layer['geom']} layer that is not a data mark reaches {layer['reach']} on the value axis while "
            f"the data marks span {layer['lo']} to {layer['hi']}, so it stretches the axis and flattens the "
            "data. Give a band or backdrop ymin = -Inf, ymax = Inf (geom_rect, annotate('rect')): it fills "
            "the panel without setting the range.",
        )
    # Each region (or the one chart) must spread its marks the way its own data spreads.
    flat = [found.get("spans")] if isinstance(found.get("spans"), dict) else found.get("spans") or []
    flat_marks = any(
        span.get("value") and (span.get("mark") is None or span["mark"] < 0.5 * span["value"])
        for span in flat if isinstance(span, dict)
    )
    if record.get("value_encoding") != "colour" and not found.get("error") and flat_marks:
        deviate(
            "VALUE_NOT_ON_POSITION",
            "The marks do not spread along the value axis the way the data does, so the chart hides the "
            "values it plots. Map y = value on the marks (the scaffold flips a horizontal chart itself; "
            "Matplotlib: the value coordinate is row['value']).",
        )
    promised = int(record.get("value_labels") or 0)
    if promised and not found.get("error") and int(found.get("text_rows") or 0) < promised:
        deviate(
            "VALUE_LABELS_MISSING",
            f"The value axis is hidden because the plan labels {promised} marks with their values, but only "
            f"{found.get('text_rows', 0)} labels are drawn. Label the reading-carrying marks with fmt_value(value).",
        )
    return {
        "ok": not deviations,
        "restored_scaffold": restored,
        "deviations": deviations,
        "fix_list": _fix_list(deviations),
    }


def _marks_brief(name: str, renderer: str, interval: bool, label_fmts: dict[str, Any], n_regions: int,
                 promised: int) -> str:
    """What the build model reads before it writes the slot: the frame's columns and the helpers."""
    parts = [f"Write only the body of chart_marks between the markers in {name}."]
    if n_regions:
        parts.append(f"chart_marks(d) draws each of the {n_regions} regions from that region's rows.")
    if renderer != "ggplot2":
        parts.append("Draw on ax from rows with pos(row) and "
                     + ("row['start'] to row['end']" if interval else "row['value']")
                     + "; use PALETTE/INK, fmt_value() and fontsize=LABEL_PT.")
    elif interval:
        parts.append(
            "Return list(...) of ggplot layers. Each mark spans its row's start to end: bars or segments as "
            "geom_tile(aes(x = category, y = (start + end) / 2, height = end - start, fill = <fill>), width = 0.6), "
            "ranges as geom_segment(aes(x = category, xend = category, y = start, yend = end)). Use palette/ink, "
            "fmt_value() for printed numbers and size = label_size for text. Print a bar's value with "
            "bar_values(aes(x = category, y = end, ymin = start, ymax = end, label = <text>, fill = <the bars' fill>), "
            "width = <the bars' width>): it puts each value inside its segment or past the end, in ink that reads there."
        )
    else:
        parts.append(
            "Return list(...) of ggplot layers mapping x = category, y = value; use palette/ink, fmt_value() for "
            "printed numbers and size = label_size for text. Print bar values with bar_values(aes(x = category, "
            "y = value, label = fmt_value(value), fill = <the bars' fill>), position = <the bars' own position>): it "
            "puts each value inside its bar or past the end, in ink that reads there. Name lines at their ends with "
            "end_labels(aes(x = category, y = value, label = series, colour = series), data = <each line's last row>): "
            "it spreads crowded names apart with leaders. Other text keeps the position of the marks it labels."
        )
    for label in label_fmts:
        parts.append(
            f"The {label} column is a label measure: print it with fmt_{label}({label}) in its own units, never as a "
            "position, colour or series"
            + (f" - on bars through bar_values(): as its label = fmt_{label}({label}) when it is the only number the "
               f"bar prints, or as note = fmt_{label}({label}) beside the bar's value, which prints it past the bar's "
               "end after the value; elsewhere as text beside its mark." if renderer == "ggplot2" else ".")
        )
    if promised:
        parts.append(f"The value axis is hidden, so label at least {promised} marks with their values.")
    return " ".join(parts)


def _strip_wrap_chars(names: list[str], plot_w: float, ncol: int, font_pt: float, dpi: float) -> int:
    """Characters per line that keep the longest panel heading inside its panel; 0 when it fits.

    Measured in the heading's bold face against the panel width the grid leaves (ggplot's
    panel spacing and strip padding are half a line each), so a heading wraps rather than clips.
    """
    longest = max(names, key=len)
    gap = pt_to_px(font_pt / 2, dpi)
    panel_w = (plot_w - (ncol - 1) * gap) / max(1, ncol) - 2 * gap
    width = TextMeasurer(dpi, weight="bold").width(longest, font_pt)
    if width <= panel_w or not longest:
        return 0
    return max(8, int(len(longest) * panel_w / width))


def _fix_list(deviations: list[dict[str, str]]) -> str:
    """The deviations as a numbered markdown list - what the correcting model reads."""
    return "\n".join(f"{i}. {d['message']}" for i, d in enumerate(deviations, 1))
