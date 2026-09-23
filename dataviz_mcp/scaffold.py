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

from .color_math import _contrast_ratio, better_ink, to_rgb
from .frame import reserve_frame
from .inspection import _REDUNDANT_AXIS_MIN_LABELS
from .layout import FONT_PT, PROFILES, char_px, house_font_pt, pt_to_px

MARKS_BEGIN = "# ==== marks: the build model writes geoms and labels here ===="
MARKS_END = "# ==== end marks ===="
_SCAFFOLD_BANNER = "# ==== scaffold: written by scaffold_chart from the plan - do not edit ===="

_X_KINDS = ("discrete", "date", "continuous")
_IDENTIFICATION = ("direct_labels", "subtitle_key", "axis", "legend")
# A mark colour whose HLS saturation is below this reads as a neutral grey: context ink the
# palette does not need to own (focal-plus-grey, reference lines, muted labels).
_NEUTRAL_SATURATION = 0.12
# Text drawn smaller than this share of the planned label size reads as the tiny-font defect.
_MIN_TEXT_SHARE = 0.8
# WCAG AA for normal text; on-mark labels are judged against the fill they sit on.
_MIN_ON_MARK_CONTRAST = 4.5

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
    }


def _format_number(value: float, fmt: dict[str, Any]) -> str:
    """The string fmt_value prints, for measuring label width before anything renders."""
    step = fmt["step"]
    decimals = max(0, -int(math.floor(math.log10(step)))) if step and step < 1 else 0
    if step:
        value = round(value / step) * step
    return f"{fmt['prefix']}{value:,.{decimals}f}{fmt['suffix']}"


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
        "fmt_value <- scales::label_number("
        + (f"accuracy = {fmt['step']!r}, " if fmt["step"] else "")
        + f"big.mark = \",\", prefix = {_r_str(fmt['prefix'])}, suffix = {_r_str(fmt['suffix'])})",
        "# Text: geom_text(size = label_size) for labels and values, annotation_size for a free annotation.",
        f"label_size <- {fonts['label']} / .pt",
        f"annotation_size <- {fonts['annotation']} / .pt",
        "# Stacks: position = stack for stacked bars, stack_mid for their labels - the first",
        "# series sits at the baseline and each label on its own segment.",
        "stack <- position_stack(reverse = TRUE)",
        "stack_mid <- position_stack(reverse = TRUE, vjust = 0.5)",
        "# Text on a mark: aes(colour = on_fill_ink(series)) - the ink that reads on that fill.",
        f"on_ink <- {_r_vec(list(spec['on_ink'].values()), list(spec['on_ink'].keys())) if spec['on_ink'] else 'c()'}",
        "on_fill_ink <- function(series) I(unname(on_ink[as.character(series)]))",
        "",
    ]
    marks = [
        "# Map x = category and y = value (the scaffold flips a horizontal chart itself).",
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
    theme_lines = [f"{key} = {value}" for key, value in theme.items()]

    layers = ["ggplot(plot_data)", "chart_marks(plot_data)"]
    if spec["stops"]:
        layers.append(f"scale_fill_gradientn(colours = {_r_vec(spec['stops'])}, labels = fmt_value)")
    elif has_series:
        layers.append('scale_colour_manual(values = palette, aesthetics = c("colour", "fill"))')
    if not colour_encoded:
        value_args = ["labels = fmt_value"]
        if spec["zero_baseline"]:
            value_args += ["limits = c(0, NA)", "expand = expansion(mult = c(0, 0.05))"]
        layers.append(f"scale_y_continuous({', '.join(value_args)})")
    if spec["x_kind"] == "date":
        layers.append("scale_x_date(labels = scales::label_date_short())")
    elif spec["x_kind"] == "discrete":
        # A flipped axis would put the first category at the bottom; read order runs top-down.
        discrete_args = ["limits = rev"] if horizontal else []
        if spec["wrap_label_chars"]:
            discrete_args.append(f"labels = scales::label_wrap({spec['wrap_label_chars']})")
        if discrete_args:
            layers.append(f"scale_x_discrete({', '.join(discrete_args)})")
    # Clip off: a direct label past the panel edge draws into the margin, where the inspector
    # measures it and refit_chart grows the canvas, instead of being cut invisibly at the panel.
    layers.append('coord_flip(clip = "off")' if horizontal else 'coord_cartesian(clip = "off")')
    if has_facet:
        layers.append(f'facet_wrap(~facet, ncol = {spec["facet_ncol"]}, scales = {_r_str(spec["facet_scales"])})')
    # Axis titles are declared by displayed position; under coord_flip the y aesthetic is drawn
    # along the bottom, so the labs() keys swap.
    shown = spec["axis_titles"]
    titles = {"x": shown.get("y"), "y": shown.get("x")} if horizontal else shown
    labs_args = [
        f"title = {_r_str(spec['title'])}",
        f"subtitle = {_r_str(spec['subtitle']) if spec['subtitle'] else 'NULL'}",
        f"caption = {_r_str(spec['caption']) if spec['caption'] else 'NULL'}",
        f"x = {_r_str(titles['x']) if titles.get('x') else 'NULL'}",
        f"y = {_r_str(titles['y']) if titles.get('y') else 'NULL'}",
        "colour = NULL",
        "fill = NULL",
    ]
    layers.append("labs(\n      " + ",\n      ".join(labs_args) + "\n    )")
    layers.append(f"theme_minimal(base_size = {fonts['axis']})")
    layers.append("theme(\n      " + ",\n      ".join(theme_lines) + "\n    )")

    tail = [
        _SCAFFOLD_BANNER,
        "build_chart <- function() {",
        "  " + " +\n    ".join(layers),
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
    step = fmt["step"]
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
        "def fmt_value(value):",
        '    """Format any value you print at the planned precision."""',
        (f"    value = round(float(value) / {step!r}) * {step!r}" if step else "    value = float(value)"),
        f"    return f\"{fmt['prefix']}{{value:,.{fmt['decimals']}f}}{fmt['suffix']}\"",
        "",
        "",
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
        "        row['value'] = float(row['value'])",
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
) -> dict[str, Any]:
    """Write the chart source with every planned setting applied and one slot for the marks."""
    if renderer not in ("ggplot2", "matplotlib"):
        raise ValueError("renderer must be ggplot2 or matplotlib")
    if x_kind not in _X_KINDS:
        raise ValueError(f"x_kind must be one of {_X_KINDS}")
    if identification not in _IDENTIFICATION:
        raise ValueError(f"identification must be one of {_IDENTIFICATION}")
    if value_encoding not in ("position", "colour"):
        raise ValueError("value_encoding must be position or colour")
    if not (public_copy or {}).get("title"):
        raise ValueError("public_copy.title is required")

    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    columns, rows = _read_plot_data(Path(plot_data_path).expanduser().resolve())
    if not {"category", "value"} <= set(columns):
        raise ValueError("plot data must be the prepare_plot_data frame (category and value columns)")
    warnings: list[str] = []
    layout = layout or {}

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
    if layout.get("regions"):
        warnings.append("layout has panel_groups regions; the scaffold draws one grid - compose regions by hand")

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
    shown = [_format_number(float(r["value"]), fmt) for r in rows if r.get("value") not in ("", None)]
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
    }
    if facet_order and not layout.get("facet_ncol"):
        spec["facet_ncol"] = max(1, round(len(facet_order) ** 0.5))
        spec["facet_nrow"] = -(-len(facet_order) // spec["facet_ncol"])

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
                "label_pt": fonts["label"],
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
        "decided": decided,
        "marks_brief": (
            f"Write only the body of chart_marks between the markers in {source.name}. "
            + ("Return list(...) of ggplot layers mapping x = category, y = value; use palette/ink, "
               "fmt_value() for printed numbers and size = label_size for text."
               if renderer == "ggplot2" else
               "Draw on ax from rows with pos(row) and row['value']; use PALETTE/INK, fmt_value() and "
               "fontsize=LABEL_PT.")
            + (f" The value axis is hidden, so label at least {value_labels} marks with their values."
               if hide_value_axis else "")
        ),
        "warnings": warnings,
    }


_R_CHECK = r'''
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages(library(ggplot2))
pdf(NULL)
out <- list(error = NULL, non_layers = list(), geom_label = 0L, text_rows = 0L,
            mark_colours = list(), text_sizes = list(), unmapped = list(), label_mismatch = list(),
            stack_order = FALSE, on_mark = list())
as_hex <- function(x) tryCatch(grDevices::rgb(t(grDevices::col2rgb(x)), maxColorValue = 255), error = function(e) as.character(x))
flat <- function(x) if (is.list(x) && !inherits(x, "gg")) do.call(c, lapply(x, flat)) else list(x)
is_text <- function(layer) inherits(layer$geom, "GeomText") || inherits(layer$geom, "GeomLabel") ||
  grepl("Text|Label", class(layer$geom)[1])
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
  built <- build_chart()
  plot <- if (inherits(built, "ggplot")) built else built$plot
  b <- ggplot_build(plot)
  invisible(ggplotGrob(plot))
  for (i in seq_along(plot$layers)) if (is_text(plot$layers[[i]])) out$text_rows <- out$text_rows + nrow(b$data[[i]])
  # A mapped colour whose values the palette does not name falls to the scale's NA grey.
  named <- names(palette)
  if (!is.null(named)) for (layer in plot$layers) for (a in c("colour", "fill")) {
    m <- layer$mapping[[a]]
    if (is.null(m)) next
    data <- if (is.data.frame(layer$data)) layer$data else plot_data
    vals <- tryCatch(rlang::eval_tidy(m, data = data), error = function(e) NULL)
    if (!inherits(vals, "AsIs") && (is.character(vals) || is.factor(vals)) && !all(as.character(vals) %in% named))
      out$unmapped[[length(out$unmapped) + 1]] <- rlang::as_label(m)
  }
  # A printed number sitting inside a bar must be that bar's value.
  rects <- do.call(rbind, lapply(seq_along(plot$layers), function(i) {
    d <- b$data[[i]]
    if (is_text(plot$layers[[i]]) || !all(c("xmin", "xmax", "ymin", "ymax") %in% names(d))) return(NULL)
    d$fill_hex <- if ("fill" %in% names(d)) as_hex(d$fill) else NA_character_
    d[, c("PANEL", "xmin", "xmax", "ymin", "ymax", "fill_hex")]
  }))
  if (!is.null(rects)) for (i in seq_along(plot$layers)) {
    if (!is_text(plot$layers[[i]])) next
    d <- b$data[[i]]
    for (r in seq_len(nrow(d))) {
      text <- as.character(d$label[r])
      if (is.na(text) || !nzchar(text)) next
      hit <- rects[rects$PANEL == d$PANEL[r] & d$x[r] >= rects$xmin & d$x[r] <= rects$xmax &
                   d$y[r] >= pmin(rects$ymin, rects$ymax) & d$y[r] <= pmax(rects$ymin, rects$ymax), ]
      if (nrow(hit) != 1) next
      # Text on a mark reads against the mark's fill, not the page.
      out$on_mark[[length(out$on_mark) + 1]] <- list(text = text, ink = as_hex(d$colour[r]), fill = hit$fill_hex)
      if (grepl("[KMBT]\\b", text)) next
      token <- regmatches(text, regexpr("-?[0-9][0-9,]*\\.?[0-9]*", text))
      if (!length(token)) next
      shown <- as.numeric(gsub(",", "", token))
      decimals <- if (grepl("\\.", token)) nchar(sub(".*\\.", "", token)) else 0
      value <- abs(hit$ymax - hit$ymin)
      if (abs(value - shown) > 0.5 * 10^-decimals + 1e-9 && abs(value - shown) > 0.02 * abs(value))
        out$label_mismatch[[length(out$label_mismatch) + 1]] <- sprintf("'%s' sits on a bar of %s", text, format(signif(value, 4)))
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
}, error = function(e) out$error <<- conditionMessage(e))
jsonlite::write_json(out, args[[2]], auto_unbox = TRUE, null = "null")
'''


def _check_ggplot(source: Path) -> dict[str, Any]:
    rscript = shutil.which("Rscript")
    if rscript is None:
        return {"error": "Rscript is not available; the slot could not be built"}
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "check.R"
        result = Path(tmp) / "check.json"
        script.write_text(_R_CHECK, encoding="utf-8")
        completed = subprocess.run(
            [rscript, str(script), str(source), str(result)],
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
        figure, _ = _unpack_build(_load_module(source).build_chart())
    except Exception as exc:  # the model's code is what failed; report it, don't raise
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    try:
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
            # Text on a bar reads against the bar's fill, not the page.
            bars = [p for p in ax.patches if isinstance(p, Rectangle)]
            for text in ax.texts:
                x, y = text.get_position()
                for bar in bars:
                    x0, x1 = sorted((bar.get_x(), bar.get_x() + bar.get_width()))
                    y0, y1 = sorted((bar.get_y(), bar.get_y() + bar.get_height()))
                    if x0 <= float(x) <= x1 and y0 <= float(y) <= y1:
                        out.setdefault("on_mark", []).append({
                            "text": text.get_text(),
                            "ink": mcolors.to_hex(text.get_color()),
                            "fill": mcolors.to_hex(bar.get_facecolor()),
                        })
                        break
    finally:
        plt.close(figure)
    return out


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
    if not sidecar.is_file():
        raise ValueError(f"No scaffold record next to {source.name}; write the source with scaffold_chart")
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    deviations: list[dict[str, str]] = []

    def deviate(code: str, message: str, severity: str = "major") -> None:
        deviations.append({"code": code, "severity": severity, "message": message})

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

    found = _check_ggplot(source) if record["renderer"] == "ggplot2" else _check_matplotlib(source, record)
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
    faint = sorted({
        f"'{pair['text']}' ({pair['ink']} on {pair['fill']})"
        for pair in found.get("on_mark") or []
        if (_contrast_ratio(pair.get("ink"), pair.get("fill")) or 99.0) < _MIN_ON_MARK_CONTRAST
    })
    if faint:
        deviate(
            "LOW_CONTRAST_ON_MARK",
            f"Text on a mark does not read on its fill: {', '.join(faint)}. Colour it with "
            "colour = on_fill_ink(series) (Matplotlib: ON_INK[series]).",
        )
    if found.get("stack_order"):
        deviate(
            "STACK_ORDER",
            "Stacked segments do not run in series order from the baseline. Stack bars with "
            "position = stack and their labels with position = stack_mid (Matplotlib: stack(ax, rows)).",
        )
    for mismatch in found.get("label_mismatch") or []:
        deviate(
            "LABEL_ON_WRONG_MARK",
            f"Label {mismatch}. Compute label positions with the same stacking as the bars "
            "(position_stack(vjust = 0.5) on the same data and grouping), never a separate cumsum.",
            "fatal",
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


def _fix_list(deviations: list[dict[str, str]]) -> str:
    """The deviations as a numbered markdown list - what the correcting model reads."""
    return "\n".join(f"{i}. {d['message']}" for i, d in enumerate(deviations, 1))
