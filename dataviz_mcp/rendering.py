from __future__ import annotations

import importlib.util
import csv
import json
import math
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib import colors as mpl_colors
from matplotlib.collections import Collection, PathCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.path import Path as MatplotlibPath
from matplotlib.text import Annotation, Text

from .artifacts import raster_info, sha256_file, write_json
from .inspection import inspect_rendered_chart
from .review_views import build_review_views


SCHEMA_VERSION = 2
ROLE_ID = re.compile(r"^(?P<role>[a-z][a-z0-9_-]*):(?P<id>.+)$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _round(value: float) -> float:
    return round(float(value), 3)


def _bbox_dict(bounds: tuple[float, float, float, float], height: int) -> dict[str, float]:
    x0, y0, width, box_height = bounds
    return {
        "x": _round(x0),
        "y": _round(height - (y0 + box_height)),
        "width": _round(width),
        "height": _round(box_height),
    }


def _colour(value: Any) -> str | None:
    try:
        return mpl_colors.to_hex(value, keep_alpha=True)
    except (TypeError, ValueError):
        return None


def _artist_identity(artist: Any, role: str, fallback: str) -> tuple[str, str]:
    gid = artist.get_gid() if hasattr(artist, "get_gid") else None
    if isinstance(gid, str):
        match = ROLE_ID.fullmatch(gid.strip())
        if match:
            return match.group("role"), match.group("id")
        if gid.strip():
            return role, gid.strip()
    return role, fallback


def _load_module(source_path: Path) -> ModuleType:
    name = f"dataviz_chart_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, source_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load chart source: {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unpack_build(value: Any) -> tuple[Figure, dict[str, Any]]:
    if isinstance(value, Figure):
        return value, {}
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], Figure)
        and isinstance(value[1], dict)
    ):
        return value[0], value[1]
    raise TypeError(
        "Chart build function must return a matplotlib Figure or (Figure, chart_spec_dict)"
    )


def _infer_text_role(text: Text, figure: Figure) -> str:
    if isinstance(text, Annotation):
        return "annotation"
    for axes in figure.axes:
        legend = axes.get_legend()
        if legend is not None and text in legend.get_texts():
            return "legend_text"
        if text is axes.title:
            return "panel_heading" if len(figure.axes) > 1 else "title"
        if text is axes.xaxis.label or text is axes.yaxis.label:
            return "axis_label"
        if text in axes.get_xticklabels() or text in axes.get_yticklabels():
            return "tick_label"
    if text in figure.texts:
        if text is getattr(figure, "_suptitle", None):
            return "title"
        y = float(text.get_position()[1])
        if y >= 0.88:
            return "subtitle"
        if y <= 0.12:
            return "footer"
        return "figure_text"
    return "label"


def _axes_id(artist: Any, axes_ids: dict[Any, str]) -> str | None:
    axes = getattr(artist, "axes", None)
    return axes_ids.get(axes)


def _collect_layout(figure: Figure, artifact: dict[str, Any]) -> dict[str, Any]:
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    width, height = figure.canvas.get_width_height()
    if (width, height) != (artifact["width"], artifact["height"]):
        raise ValueError(
            "Rendered canvas dimensions do not match the saved artifact: "
            f"canvas={width}x{height}, artifact={artifact['width']}x{artifact['height']}"
        )

    axes_ids = {axes: f"axes-{index + 1}" for index, axes in enumerate(figure.axes)}
    plot_areas: list[dict[str, Any]] = []
    transforms: list[dict[str, Any]] = []
    for axes, axes_id in axes_ids.items():
        plot_areas.append(
            {
                "id": axes_id,
                "bbox": _bbox_dict(axes.get_window_extent(renderer).bounds, height),
            }
        )
        a, b, c, d, e, f = axes.transData.get_affine().to_values()
        transforms.append(
            {
                "axes_id": axes_id,
                "data_to_pixel_top_left": [
                    [_round(a), _round(c), _round(e)],
                    [_round(-b), _round(-d), _round(height - f)],
                    [0.0, 0.0, 1.0],
                ],
            }
        )

    elements: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
    for text in figure.findobj(match=Text):
        content = text.get_text()
        if not text.get_visible() or not isinstance(content, str) or not content.strip():
            continue
        inferred_role = _infer_text_role(text, figure)
        role_counts[inferred_role] = role_counts.get(inferred_role, 0) + 1
        role, element_id = _artist_identity(
            text,
            inferred_role,
            f"{inferred_role}-{role_counts[inferred_role]}",
        )
        bbox = text.get_window_extent(renderer)
        elements.append(
            {
                "id": element_id,
                "role": role,
                "text": content,
                "bbox": _bbox_dict(bbox.bounds, height),
                "axes_id": _axes_id(text, axes_ids),
                "clip_on": bool(text.get_clip_on()),
                "font_size_pt": _round(text.get_fontsize()),
                "colour": _colour(text.get_color()),
                "horizontal_alignment": text.get_horizontalalignment(),
                "vertical_alignment": text.get_verticalalignment(),
            }
        )

    series: list[dict[str, Any]] = []
    series_count = 0
    for axes in figure.axes:
        for line in axes.lines:
            if not isinstance(line, Line2D) or not line.get_visible():
                continue
            vertices = line.get_path().vertices
            if len(vertices) < 2:
                continue
            path = line.get_path()
            transformed = line.get_transform().transform(vertices)
            codes = path.codes
            segments: list[list[list[float]]] = []
            current: list[list[float]] = []
            for index, (x, y) in enumerate(transformed):
                code = codes[index] if codes is not None else None
                if (
                    not math.isfinite(float(x))
                    or not math.isfinite(float(y))
                    or code == MatplotlibPath.MOVETO
                ):
                    if len(current) >= 2:
                        segments.append(current)
                    current = []
                    if not math.isfinite(float(x)) or not math.isfinite(float(y)):
                        continue
                current.append([_round(x), _round(height - y)])
            if len(current) >= 2:
                segments.append(current)
            points = [point for segment in segments for point in segment]
            if len(points) < 2:
                continue
            series_count += 1
            role, series_id = _artist_identity(line, "series", f"series-{series_count}")
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            series.append(
                {
                    "id": series_id,
                    "role": role,
                    "axes_id": axes_ids[axes],
                    "bbox": {
                        "x": min(xs),
                        "y": min(ys),
                        "width": _round(max(xs) - min(xs)),
                        "height": _round(max(ys) - min(ys)),
                    },
                    "points": points,
                    "segments": segments,
                    "stroke_width_pt": _round(line.get_linewidth()),
                }
            )

    legends: list[dict[str, Any]] = []
    for axes, axes_id in axes_ids.items():
        legend = axes.get_legend()
        if legend is not None and legend.get_visible():
            legends.append(
                {
                    "id": f"legend-{len(legends) + 1}",
                    "axes_id": axes_id,
                    "bbox": _bbox_dict(legend.get_window_extent(renderer).bounds, height),
                }
            )

    marks: list[dict[str, Any]] = []
    unsupported_marks = 0
    mark_count = 0
    for axes, axes_id in axes_ids.items():
        for patch in axes.patches:
            if not isinstance(patch, Patch) or not patch.get_visible():
                continue
            try:
                bbox = patch.get_window_extent(renderer)
                if not all(math.isfinite(float(value)) for value in bbox.bounds):
                    raise ValueError("non-finite patch bounds")
            except (AttributeError, TypeError, ValueError):
                unsupported_marks += 1
                continue
            mark_count += 1
            role, mark_id = _artist_identity(patch, "mark", f"mark-{mark_count}")
            marks.append(
                {
                    "id": mark_id,
                    "role": role,
                    "kind": type(patch).__name__,
                    "axes_id": axes_id,
                    "bbox": _bbox_dict(bbox.bounds, height),
                    "fill": _colour(patch.get_facecolor()),
                    "stroke": _colour(patch.get_edgecolor()),
                }
            )
        for collection in axes.collections:
            if not isinstance(collection, Collection) or not collection.get_visible():
                continue
            bbox_value: tuple[float, float, float, float] | None = None
            if isinstance(collection, PathCollection):
                offsets = collection.get_offsets()
                if len(offsets):
                    transformed = collection.get_offset_transform().transform(offsets)
                    finite = [
                        (float(x), float(y))
                        for x, y in transformed
                        if math.isfinite(float(x)) and math.isfinite(float(y))
                    ]
                    if finite:
                        sizes = collection.get_sizes()
                        radius = math.sqrt(float(max(sizes))) * figure.dpi / 72 / 2 if len(sizes) else 2.0
                        for point_index, (x, y) in enumerate(finite, start=1):
                            mark_count += 1
                            role, base_id = _artist_identity(
                                collection, "mark", f"mark-{mark_count}"
                            )
                            facecolours = collection.get_facecolors()
                            edgecolours = collection.get_edgecolors()
                            marks.append(
                                {
                                    "id": f"{base_id}-point-{point_index}",
                                    "role": role,
                                    "kind": type(collection).__name__,
                                    "axes_id": axes_id,
                                    "bbox": _bbox_dict(
                                        (x - radius, y - radius, 2 * radius, 2 * radius),
                                        height,
                                    ),
                                    "fill": _colour(facecolours[0]) if len(facecolours) else None,
                                    "stroke": _colour(edgecolours[0]) if len(edgecolours) else None,
                                }
                            )
                        continue
            if bbox_value is None:
                try:
                    bbox = collection.get_window_extent(renderer)
                    if all(math.isfinite(float(value)) for value in bbox.bounds) and bbox.width >= 0 and bbox.height >= 0:
                        bbox_value = tuple(float(value) for value in bbox.bounds)
                except (AttributeError, TypeError, ValueError):
                    bbox_value = None
            if bbox_value is None:
                unsupported_marks += 1
                continue
            mark_count += 1
            role, mark_id = _artist_identity(
                collection, "mark", f"mark-{mark_count}"
            )
            facecolours = collection.get_facecolors()
            edgecolours = collection.get_edgecolors()
            marks.append(
                {
                    "id": mark_id,
                    "role": role,
                    "kind": type(collection).__name__,
                    "axes_id": axes_id,
                    "bbox": _bbox_dict(bbox_value, height),
                    "fill": _colour(facecolours[0]) if len(facecolours) else None,
                    "stroke": _colour(edgecolours[0]) if len(edgecolours) else None,
                }
            )
        unsupported_marks += len(axes.images)
    return {
        "schema_version": SCHEMA_VERSION,
        "coordinate_system": "pixels; origin top-left",
        "artifact": artifact,
        "canvas": {"x": 0.0, "y": 0.0, "width": width, "height": height},
        "plot_areas": plot_areas,
        "transforms": transforms,
        "elements": elements,
        "series": series,
        "marks": marks,
        "legends": legends,
        "background": _colour(figure.get_facecolor()),
        "coverage": {
            "text_bounds": True,
            "line_series_paths": True,
            "patch_and_common_collection_bounds": True,
            "unsupported_non_line_mark_count": unsupported_marks,
        },
    }


def render_chart(
    source_path: str,
    output_dir: str,
    artifact_name: str = "chart.png",
    build_function: str = "build_chart",
    dpi: int | None = None,
    width_px: int | None = None,
    height_px: int | None = None,
) -> dict[str, Any]:
    """Render one trusted local Matplotlib builder into a versioned artifact bundle."""
    source = Path(source_path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".py":
        raise ValueError(f"Chart source must be an existing Python file: {source}")
    if Path(artifact_name).name != artifact_name or not artifact_name.lower().endswith(".png"):
        raise ValueError("artifact_name must be a plain PNG filename")
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    module = _load_module(source)
    builder = getattr(module, build_function, None)
    if not callable(builder):
        raise ValueError(f"Chart source does not define callable {build_function}()")
    figure, user_spec = _unpack_build(builder())
    try:
        if dpi is not None:
            if dpi <= 0:
                raise ValueError("dpi must be greater than zero")
            figure.set_dpi(dpi)
        render_dpi = int(round(figure.dpi))
        if width_px is not None or height_px is not None:
            if not width_px or not height_px or width_px <= 0 or height_px <= 0:
                raise ValueError("width_px and height_px must both be greater than zero")
            figure.set_size_inches(width_px / render_dpi, height_px / render_dpi, forward=True)
        artifact_path = destination / artifact_name
        figure.canvas.draw()
        figure.savefig(
            artifact_path,
            format="png",
            dpi=render_dpi,
            facecolor=figure.get_facecolor(),
            edgecolor="none",
            bbox_inches=None,
        )
        artifact = raster_info(artifact_path)
        layout = _collect_layout(figure, artifact)
        if isinstance(user_spec.get("inspection_contract"), dict):
            layout["inspection_contract"] = user_spec["inspection_contract"]
    finally:
        plt.close(figure)

    spec_path = destination / "chart-spec.json"
    layout_path = destination / "layout-metadata.json"
    manifest_path = destination / "manifest.json"
    spec = {
        "schema_version": SCHEMA_VERSION,
        "renderer": "matplotlib",
        "source": {"path": str(source), "sha256": sha256_file(source)},
        "build_function": build_function,
        "dpi": render_dpi,
        "dimensions": {"width_px": artifact["width"], "height_px": artifact["height"]},
        "spec": user_spec,
    }
    write_json(spec_path, spec)
    write_json(layout_path, layout)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_iso(),
        "renderer": "matplotlib",
        "artifact": artifact,
        "chart_spec": {"path": str(spec_path), "sha256": sha256_file(spec_path)},
        "layout_metadata": {
            "path": str(layout_path),
            "sha256": sha256_file(layout_path),
        },
    }
    write_json(manifest_path, manifest)
    return {
        "artifact": artifact,
        "chart_spec_path": str(spec_path),
        "layout_metadata_path": str(layout_path),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
    }


def probe_renderers() -> dict[str, Any]:
    """Report deterministic static-renderer availability without changing the host."""
    matplotlib_probe = {
        "available": True,
        "version": matplotlib.__version__,
        "supported_output_types": ["png"],
        "supported_source_types": [".py"],
        "failure_reasons": [],
    }
    rscript = shutil.which("Rscript")
    ggplot_probe: dict[str, Any] = {
        "available": False,
        "rscript": rscript,
        "r_version": None,
        "packages": {"ggplot2": None, "ragg": None, "gridExtra": None},
        "supported_output_types": [],
        "supported_source_types": [".r"],
        "failure_reasons": [],
    }
    if rscript is None:
        ggplot_probe["failure_reasons"].append("Rscript is not executable")
    else:
        expression = (
            'cat("R\\t", paste(R.version$major, R.version$minor, sep="."), "\\n", sep=""); '
            'for (p in c("ggplot2", "ragg", "gridExtra")) {'
            ' if (requireNamespace(p, quietly=TRUE)) '
            'cat(p, "\\t", as.character(packageVersion(p)), "\\n", sep="") '
            'else cat(p, "\\tMISSING\\n", sep="") }'
        )
        try:
            completed = subprocess.run(
                [rscript, "--vanilla", "-e", expression],
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            ggplot_probe["failure_reasons"].append(f"Rscript probe failed: {exc}")
        else:
            if completed.returncode != 0:
                reason = completed.stderr.strip() or f"Rscript exited {completed.returncode}"
                ggplot_probe["failure_reasons"].append(reason)
            else:
                values: dict[str, str] = {}
                for line in completed.stdout.splitlines():
                    name, separator, value = line.partition("\t")
                    if separator:
                        values[name] = value.strip()
                ggplot_probe["r_version"] = values.get("R")
                for package in ("ggplot2", "ragg"):
                    version = values.get(package)
                    if version and version != "MISSING":
                        ggplot_probe["packages"][package] = version
                    else:
                        ggplot_probe["failure_reasons"].append(
                            f"R package {package} is not installed"
                        )
                gridextra_version = values.get("gridExtra")
                if gridextra_version and gridextra_version != "MISSING":
                    ggplot_probe["packages"]["gridExtra"] = gridextra_version
    ggplot_probe["available"] = not ggplot_probe["failure_reasons"]
    if ggplot_probe["available"]:
        ggplot_probe["supported_output_types"] = ["png"]
    table_reasons = list(ggplot_probe["failure_reasons"])
    if ggplot_probe["packages"].get("gridExtra") is None:
        table_reasons.append(
            "R package gridExtra is not installed (recommended for tableGrob tables)"
        )
    table_rendering = {
        "available": ggplot_probe["available"],
        "backend": "grid/gtable via ragg",
        "recommends": "gridExtra::tableGrob or gt::as_gtable",
        "content": "table",
        "failure_reasons": table_reasons,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "probed_at": _now_iso(),
        "renderer_precedence": ["explicit user requirement", "ggplot2", "matplotlib"],
        "renderers": {"ggplot2": ggplot_probe, "matplotlib": matplotlib_probe},
        "table_rendering": table_rendering,
    }


GGPLOT_RUNNER = r'''
args <- commandArgs(trailingOnly=TRUE)
source_path <- args[[1]]
artifact_path <- args[[2]]
layout_path <- args[[3]]
metadata_path <- args[[4]]
width_px <- as.integer(args[[5]])
height_px <- as.integer(args[[6]])
dpi <- as.numeric(args[[7]])
build_function <- args[[8]]
content_kind <- if (length(args) >= 9) args[[9]] else "chart"
is_table_content <- identical(content_kind, "table")
table_margin_in <- 0.12
table_x_offset <- 0
table_y_offset <- 0

suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(ragg))
suppressPackageStartupMessages(library(grid))
source(source_path, local=.GlobalEnv)
builder <- get(build_function, mode="function", inherits=TRUE)
built <- builder()
if (inherits(built, "ggplot")) {
  metadata <- list()
  gt <- ggplotGrob(built)
} else if (is.list(built) && inherits(built$plot, "ggplot")) {
  metadata <- built$metadata
  if (is.null(metadata)) metadata <- list()
  gt <- ggplotGrob(built$plot)
} else if (inherits(built, "gtable")) {
  metadata <- list()
  gt <- built
} else if (is.list(built) && inherits(built$table, "gtable")) {
  metadata <- built$metadata
  if (is.null(metadata)) metadata <- list()
  gt <- built$table
} else {
  stop("build must return a ggplot, a gtable (tableGrob/gt::as_gtable), or list(plot=/table=, metadata=)")
}

if (is_table_content) {
  # Shrink-wrap the canvas to the table's natural size instead of centering a
  # small table in a fixed frame. Font-dependent (grobwidth) tracks need an open
  # device with real metrics to resolve, so measure on a scratch device first.
  measure_path <- tempfile(fileext=".png")
  ragg::agg_png(measure_path, width=width_px, height=height_px, units="px", res=dpi)
  grid.newpage()
  natural_w_in <- convertWidth(sum(gt$widths), "inches", valueOnly=TRUE)
  natural_h_in <- convertHeight(sum(gt$heights), "inches", valueOnly=TRUE)
  dev.off()
  unlink(measure_path)
  margin_px <- round(table_margin_in * dpi)
  if (is.finite(natural_w_in) && natural_w_in > 0) {
    natural_w_px <- natural_w_in * dpi
    width_px <- as.integer(max(1, round(natural_w_px + 2 * margin_px)))
    table_x_offset <- (width_px - natural_w_px) / 2
  }
  if (is.finite(natural_h_in) && natural_h_in > 0) {
    natural_h_px <- natural_h_in * dpi
    height_px <- as.integer(max(1, round(natural_h_px + 2 * margin_px)))
    table_y_offset <- (height_px - natural_h_px) / 2
  }
}

ragg::agg_png(artifact_path, width=width_px, height=height_px, units="px", res=dpi)
grid.newpage()
grid.draw(gt)
grid.force()

resolve_tracks <- function(track_units, total_px) {
  types <- unitType(track_units)
  fixed <- convertUnit(track_units, "in", valueOnly=TRUE) * dpi
  null <- types == "null"
  weights <- rep(0, length(track_units))
  if (any(null)) weights[null] <- as.numeric(track_units[null])
  remaining <- max(0, total_px - sum(fixed[!null]))
  if (sum(weights) > 0) fixed[null] <- remaining * weights[null] / sum(weights)
  fixed
}

widths <- resolve_tracks(gt$widths, width_px)
heights <- resolve_tracks(gt$heights, height_px)
x_before <- table_x_offset + c(0, cumsum(widths))
y_before <- table_y_offset + c(0, cumsum(heights))

extract_label <- function(g) {
  if (inherits(g, "text") && !is.null(g$label)) return(paste(g$label, collapse=" | "))
  if (inherits(g, "gTree") && length(g$children)) {
    labels <- unlist(lapply(g$children, extract_label), use.names=FALSE)
    return(paste(labels[nzchar(labels)], collapse=" | "))
  }
  ""
}

extract_gp <- function(g, field) {
  if (!is.null(g$gp) && !is.null(g$gp[[field]])) {
    value <- suppressWarnings(as.numeric(g$gp[[field]][1]))
    if (length(value) && is.finite(value)) return(value)
  }
  if (inherits(g, "gTree") && length(g$children)) {
    for (child in g$children) {
      value <- extract_gp(child, field)
      if (!is.na(value)) return(value)
    }
  }
  NA_real_
}

extract_fill <- function(g) {
  if (!is.null(g$gp) && !is.null(g$gp$fill)) {
    value <- g$gp$fill[1]
    if (!is.na(value)) return(as.character(value))
  }
  if (inherits(g, "gTree") && length(g$children)) {
    for (child in g$children) {
      value <- extract_fill(child)
      if (nzchar(value)) return(value)
    }
  }
  ""
}

row_frame <- function(id, name, text, x, y, width, height, kind="zone",
                      colour="", fill="", font_size="", x_points="", y_points="") {
  data.frame(
    id=id, name=name, text=text, x=x, y=y, width=width, height=height,
    kind=kind, colour=colour, fill=fill, font_size=font_size,
    x_points=x_points, y_points=y_points, stringsAsFactors=FALSE
  )
}

gp_value <- function(gp, field, index, fallback="") {
  values <- gp[[field]]
  if (is.null(values) || !length(values)) return(fallback)
  as.character(values[((index - 1) %% length(values)) + 1])
}

unit_values <- function(value) {
  if (is.null(value)) return(numeric())
  suppressWarnings(as.numeric(value))
}

panel_rows <- list()
capture_panel_grob <- function(g, prefix, px, py, pw, ph) {
  captured <- list()
  if (inherits(g, "gTree") && length(g$children)) {
    for (child_name in names(g$children)) {
      child_rows <- capture_panel_grob(
        g$children[[child_name]], paste(prefix, child_name, sep="/"), px, py, pw, ph
      )
      captured <- c(captured, child_rows)
    }
    return(captured)
  }
  if (inherits(g, c("zeroGrob", "nullGrob"))) return(captured)
  xs <- unit_values(g$x)
  ys <- unit_values(g$y)
  if (!length(xs) || !length(ys) || any(!is.finite(c(xs, ys)))) return(captured)
  absolute_x <- px + xs * pw
  absolute_y <- py + (1 - ys) * ph
  gp <- g$gp

  if (inherits(g, "rect")) {
    ws <- unit_values(g$width)
    hs <- unit_values(g$height)
    count <- min(length(xs), length(ys), length(ws), length(hs))
    for (j in seq_len(count)) {
      captured[[length(captured) + 1]] <- row_frame(
        paste0(prefix, "-", j), prefix, "",
        absolute_x[j] - ws[j] * pw / 2,
        absolute_y[j] - hs[j] * ph / 2,
        ws[j] * pw, hs[j] * ph, "rect",
        gp_value(gp, "col", j), gp_value(gp, "fill", j)
      )
    }
  } else if (inherits(g, "points")) {
    for (j in seq_along(absolute_x)) {
      size_pt <- suppressWarnings(as.numeric(gp_value(gp, "fontsize", j, "5")))
      if (!is.finite(size_pt)) size_pt <- 5
      diameter <- max(2, size_pt * dpi / 72)
      captured[[length(captured) + 1]] <- row_frame(
        paste0(prefix, "-", j), prefix, "",
        absolute_x[j] - diameter / 2, absolute_y[j] - diameter / 2,
        diameter, diameter, "point",
        gp_value(gp, "col", j), gp_value(gp, "fill", j)
      )
    }
  } else if (inherits(g, c("polyline", "lines", "segments"))) {
    captured[[1]] <- row_frame(
      prefix, prefix, "", min(absolute_x), min(absolute_y),
      diff(range(absolute_x)), diff(range(absolute_y)), "polyline",
      gp_value(gp, "col", 1), "", "",
      paste(absolute_x, collapse=";"), paste(absolute_y, collapse=";")
    )
  } else if (inherits(g, "polygon")) {
    captured[[1]] <- row_frame(
      prefix, prefix, "", min(absolute_x), min(absolute_y),
      diff(range(absolute_x)), diff(range(absolute_y)), "polygon",
      gp_value(gp, "col", 1), gp_value(gp, "fill", 1)
    )
  } else if (inherits(g, "text")) {
    labels <- as.character(g$label)
    count <- min(length(labels), length(absolute_x), length(absolute_y))
    for (j in seq_len(count)) {
      size_pt <- suppressWarnings(as.numeric(gp_value(gp, "fontsize", j, "11")))
      if (!is.finite(size_pt)) size_pt <- 11
      label_width <- max(1, nchar(labels[j], type="width") * size_pt * dpi / 72 * 0.55)
      label_height <- max(1, size_pt * dpi / 72 * 1.2)
      hjust <- if (length(g$hjust)) as.numeric(g$hjust[((j - 1) %% length(g$hjust)) + 1]) else 0.5
      vjust <- if (length(g$vjust)) as.numeric(g$vjust[((j - 1) %% length(g$vjust)) + 1]) else 0.5
      captured[[length(captured) + 1]] <- row_frame(
        paste0(prefix, "-", j), prefix, labels[j],
        absolute_x[j] - hjust * label_width,
        absolute_y[j] - (1 - vjust) * label_height,
        label_width, label_height, "text",
        gp_value(gp, "col", j), "", size_pt
      )
    }
  } else {
    captured[[1]] <- row_frame(
      prefix, prefix, "", px, py, pw, ph, "unsupported"
    )
  }
  captured
}

rows <- vector("list", nrow(gt$layout))
for (i in seq_len(nrow(gt$layout))) {
  item <- gt$layout[i,]
  grob <- gt$grobs[[i]]
  px <- x_before[item$l]
  py <- y_before[item$t]
  pw <- sum(widths[item$l:item$r])
  ph <- sum(heights[item$t:item$b])
  if (is_table_content) {
    cell_text <- extract_label(grob)
    if (nzchar(cell_text)) {
      font_size <- extract_gp(grob, "fontsize")
      colour <- extract_fill(grob)
      rows[[i]] <- row_frame(
        paste0("gg-", i), as.character(item$name), cell_text,
        px, py, pw, ph, "text", "", "",
        if (is.na(font_size)) "" else as.character(font_size)
      )
    } else {
      fill <- extract_fill(grob)
      kind <- if (nzchar(fill)) "rect" else "zone"
      rows[[i]] <- row_frame(
        paste0("gg-", i), as.character(item$name), "",
        px, py, pw, ph, kind, "", fill
      )
    }
    next
  }
  rows[[i]] <- row_frame(
    paste0("gg-", i), as.character(item$name), extract_label(grob),
    px, py, pw, ph
  )
  if (startsWith(as.character(item$name), "panel") && inherits(grob, "gTree")) {
    for (child_name in names(grob$children)) {
      if (grepl("^(grill|panel\\.border|NULL)", child_name)) next
      child_rows <- capture_panel_grob(
        grob$children[[child_name]], paste0("gg-", i, "/", child_name), px, py, pw, ph
      )
      panel_rows <- c(panel_rows, child_rows)
    }
  }
}
layout_rows <- do.call(rbind, c(rows, panel_rows))
write.csv(layout_rows, layout_path, row.names=FALSE, na="")
capture.output(dput(metadata), file=metadata_path)
dev.off()
'''


def _ggplot_role(name: str) -> str:
    clean = name.lower()
    if clean == "title":
        return "title"
    if clean == "subtitle":
        return "subtitle"
    if clean == "caption":
        return "footer"
    if clean.startswith("strip-"):
        return "panel_heading"
    if clean.startswith("axis.title"):
        return "axis_label"
    if clean.startswith("axis-"):
        return "tick_label"
    if clean.startswith("guide-box"):
        return "legend"
    return "layout_zone"


def _render_ggplot2(
    source: Path,
    destination: Path,
    artifact_name: str,
    build_function: str,
    dimensions: dict[str, Any],
    probe: dict[str, Any],
    render_kind: str = "chart",
) -> dict[str, Any]:
    if source.suffix.lower() != ".r":
        raise ValueError("The ggplot2 adapter requires an .R chart source")
    if not probe["renderers"]["ggplot2"]["available"]:
        reasons = "; ".join(probe["renderers"]["ggplot2"]["failure_reasons"])
        raise RuntimeError(f"ggplot2 renderer is unavailable: {reasons}")
    width = int(dimensions.get("width_px", 1200))
    height = int(dimensions.get("height_px", 675))
    dpi = int(dimensions.get("dpi", 144))
    if min(width, height, dpi) <= 0:
        raise ValueError("width_px, height_px, and dpi must be greater than zero")
    artifact_path = destination / artifact_name
    with tempfile.TemporaryDirectory(prefix="dataviz-ggplot-") as temporary:
        temporary_path = Path(temporary)
        runner = temporary_path / "render.R"
        layout_csv = temporary_path / "layout.csv"
        metadata_text = temporary_path / "metadata.R"
        runner.write_text(GGPLOT_RUNNER, encoding="utf-8")
        completed = subprocess.run(
            [
                probe["renderers"]["ggplot2"]["rscript"],
                "--vanilla",
                str(runner),
                str(source),
                str(artifact_path),
                str(layout_csv),
                str(metadata_text),
                str(width),
                str(height),
                str(dpi),
                build_function,
                render_kind,
            ],
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            reason = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"ggplot2 render failed: {reason}")
        artifact = raster_info(artifact_path)
        # A table shrink-wraps its canvas to the gtable's natural size, so the
        # exact artifact - not the requested profile - defines the coordinate
        # space the layout and inspection share.
        width = artifact["width"]
        height = artifact["height"]
        rows: list[dict[str, str]] = []
        with layout_csv.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        metadata_repr = metadata_text.read_text(encoding="utf-8").strip()

    elements: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    marks: list[dict[str, Any]] = []
    plot_areas: list[dict[str, Any]] = []
    legends: list[dict[str, Any]] = []
    unsupported_marks = 0
    panel_ids = {
        row["id"]: row["id"]
        for row in rows
        if row.get("kind") == "zone" and row.get("name", "").startswith("panel")
    }
    for row in rows:
        bbox = {
            key: _round(float(row[key])) for key in ("x", "y", "width", "height")
        }
        name = row["name"]
        kind = row.get("kind", "zone")
        axes_id = next(
            (panel_id for panel_id in panel_ids if row["id"].startswith(panel_id + "/")),
            None,
        )
        if kind in ("rect", "point", "polygon"):
            marks.append(
                {
                    "id": row["id"],
                    "role": "mark",
                    "kind": kind,
                    "axes_id": axes_id,
                    "bbox": bbox,
                    "fill": row.get("fill") or None,
                    "stroke": row.get("colour") or None,
                }
            )
            continue
        if kind == "polyline":
            xs = [float(value) for value in row.get("x_points", "").split(";") if value]
            ys = [float(value) for value in row.get("y_points", "").split(";") if value]
            points = [[_round(x), _round(y)] for x, y in zip(xs, ys)]
            if len(points) >= 2:
                series.append(
                    {
                        "id": row["id"],
                        "role": "series",
                        "axes_id": axes_id,
                        "bbox": bbox,
                        "points": points,
                        "segments": [points],
                        "stroke_width_pt": None,
                    }
                )
            else:
                unsupported_marks += 1
            continue
        if kind == "unsupported":
            unsupported_marks += 1
            continue
        if kind == "text":
            lower_name = name.lower()
            child_role = "annotation" if "annot" in lower_name else "label"
            elements.append(
                {
                    "id": row["id"],
                    "role": child_role,
                    "text": row.get("text", ""),
                    "bbox": bbox,
                    "axes_id": axes_id,
                    "clip_on": True,
                    "font_size_pt": float(row["font_size"]) if row.get("font_size") else None,
                    "colour": row.get("colour") or None,
                }
            )
            continue
        role = _ggplot_role(name)
        if name.startswith("panel"):
            plot_areas.append({"id": row["id"], "bbox": bbox})
        if role == "legend" and bbox["width"] > 0 and bbox["height"] > 0:
            legends.append({"id": row["id"], "axes_id": None, "bbox": bbox})
        if role != "layout_zone" and row.get("text", "").strip():
            elements.append(
                {
                    "id": row["id"],
                    "role": role,
                    "text": row["text"],
                    "bbox": bbox,
                    "axes_id": None,
                    "clip_on": False,
                    "font_size_pt": None,
                    "colour": None,
                }
            )
    layout = {
        "schema_version": SCHEMA_VERSION,
        "coordinate_system": "pixels; origin top-left",
        "artifact": artifact,
        "canvas": {"x": 0.0, "y": 0.0, "width": width, "height": height},
        "plot_areas": plot_areas,
        "transforms": [],
        "elements": elements,
        "series": series,
        "marks": marks,
        "legends": legends,
        "background": "#ffffffff",
        "coverage": {
            "text_bounds": True,
            "gtable_hierarchy_zones": True,
            "line_series_paths": True,
            "patch_and_common_collection_bounds": True,
            "table_cell_bounds": render_kind == "table",
            "unsupported_non_line_mark_count": unsupported_marks,
            "limitations": (
                [
                    "Table cell bounding boxes, text, and fills are exact from the gtable"
                    " tracks; decimal-point alignment and wrap/overflow within a cell are"
                    " not automatically verified and must be read from the rendered raster."
                ]
                if render_kind == "table"
                else ["Some ggplot2 panel grobs could not be normalized"]
                if unsupported_marks
                else ["ggplot2 text glyph bounds are deterministic font-metric estimates"]
            ),
        },
    }
    renderer_label = "gt-table" if render_kind == "table" else "ggplot2"
    spec_path = destination / "chart-spec.json"
    layout_path = destination / "layout-metadata.json"
    manifest_path = destination / "manifest.json"
    spec = {
        "schema_version": SCHEMA_VERSION,
        "renderer": renderer_label,
        "content_kind": render_kind,
        "source": {"path": str(source), "sha256": sha256_file(source)},
        "build_function": build_function,
        "dimensions": {"width_px": width, "height_px": height, "dpi": dpi},
        "chart_metadata_r": metadata_repr,
    }
    write_json(spec_path, spec)
    write_json(layout_path, layout)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_iso(),
        "renderer": renderer_label,
        "content_kind": render_kind,
        "artifact": artifact,
        "chart_spec": {"path": str(spec_path), "sha256": sha256_file(spec_path)},
        "layout_metadata": {"path": str(layout_path), "sha256": sha256_file(layout_path)},
    }
    write_json(manifest_path, manifest)
    return {
        "artifact": artifact,
        "chart_spec_path": str(spec_path),
        "layout_metadata_path": str(layout_path),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
    }


def _delivery_dimensions(
    delivery_profile: str | None, dimensions: dict[str, Any] | None
) -> dict[str, Any]:
    profiles = {
        "chat": {"width_px": 1200, "height_px": 675, "dpi": 144},
        "slide": {"width_px": 1600, "height_px": 900, "dpi": 160},
        "document": {"width_px": 1800, "height_px": 1200, "dpi": 180},
    }
    values = dict(profiles.get(delivery_profile or "chat", profiles["chat"]))
    if dimensions:
        values.update(dimensions)
    return values


def render_and_inspect_chart(
    source_path: str,
    output_dir: str,
    renderer: str = "auto",
    delivery_profile: str | None = "chat",
    dimensions: dict[str, Any] | None = None,
    artifact_name: str = "chart.png",
    build_function: str = "build_chart",
    content: str = "chart",
) -> dict[str, Any]:
    """Render with explicit precedence, inspect the exact PNG, and emit review views."""
    if renderer not in ("auto", "ggplot2", "matplotlib"):
        raise ValueError("renderer must be auto, ggplot2, or matplotlib")
    if content not in ("chart", "table"):
        raise ValueError("content must be chart or table")
    source = Path(source_path).expanduser().resolve()
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    probe = probe_renderers()
    requested = renderer
    fallback_reason: str | None = None
    if content == "table":
        if renderer == "matplotlib":
            raise ValueError("table content renders through the R/grid path, not matplotlib")
        if source.suffix.lower() != ".r":
            raise ValueError("table content requires an .R source that returns a gtable")
        if not probe["renderers"]["ggplot2"]["available"]:
            reasons = "; ".join(probe["renderers"]["ggplot2"]["failure_reasons"])
            raise RuntimeError(f"table rendering is unavailable: {reasons}")
        selected = "ggplot2"
        fallback_reason = None
    elif renderer == "auto":
        ggplot_available = probe["renderers"]["ggplot2"]["available"]
        if ggplot_available and source.suffix.lower() == ".r":
            selected = "ggplot2"
        else:
            selected = "matplotlib"
            if not ggplot_available:
                fallback_reason = "; ".join(
                    probe["renderers"]["ggplot2"]["failure_reasons"]
                )
            else:
                fallback_reason = (
                    f"ggplot2 adapter does not support {source.suffix or 'extensionless'} source"
                )
    else:
        selected = renderer
        fallback_reason = f"explicit renderer requirement: {renderer}"

    delivery_dimensions = _delivery_dimensions(delivery_profile, dimensions)
    if selected == "ggplot2":
        bundle = _render_ggplot2(
            source,
            destination,
            artifact_name,
            build_function,
            delivery_dimensions,
            probe,
            render_kind=content,
        )
    else:
        dpi = int(delivery_dimensions.get("dpi", 144))
        bundle = render_chart(
            str(source),
            str(destination),
            artifact_name=artifact_name,
            build_function=build_function,
            dpi=dpi,
            width_px=int(delivery_dimensions["width_px"]),
            height_px=int(delivery_dimensions["height_px"]),
        )

    inspection = inspect_rendered_chart(
        bundle["artifact"]["path"],
        bundle["layout_metadata_path"],
        str(destination / "inspection.json"),
        delivery_profile=delivery_profile,
    )
    view_paths = build_review_views(
        Path(bundle["artifact"]["path"]),
        destination,
        "review",
        Path(bundle["layout_metadata_path"]),
    )
    inspection["review_views"] = [
        {"path": str(path), "sha256": sha256_file(path)} for path in view_paths
    ]
    inspection_path = Path(inspection["inspection_path"])
    inspection.pop("inspection_sha256", None)
    write_json(inspection_path, inspection)
    inspection["inspection_sha256"] = sha256_file(inspection_path)
    manifest_path = Path(bundle["manifest_path"])
    manifest = {
        **json.loads(manifest_path.read_text(encoding="utf-8")),
        "renderer_selection": {
            "requested": requested,
            "selected": selected,
            "fallback_reason": fallback_reason,
            "probe": probe,
        },
        "delivery_profile": delivery_profile,
        "dimensions": delivery_dimensions,
        "content": content,
        "inspection": {
            "path": inspection["inspection_path"],
            "sha256": inspection["inspection_sha256"],
        },
        "review_views": [
            {"path": str(path), "sha256": sha256_file(path)} for path in view_paths
        ],
    }
    write_json(manifest_path, manifest)
    bundle["manifest_sha256"] = sha256_file(manifest_path)
    bundle["renderer"] = selected
    bundle["content"] = content
    bundle["renderer_selection"] = manifest["renderer_selection"]
    bundle["inspection_path"] = inspection["inspection_path"]
    bundle["review_view_paths"] = [str(path) for path in view_paths]
    return bundle
