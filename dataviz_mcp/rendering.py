from __future__ import annotations

import importlib.util
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.path import Path as MatplotlibPath
from matplotlib.text import Annotation, Text

from .artifacts import raster_info, sha256_file, write_json


SCHEMA_VERSION = 1
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
        if text is axes.title:
            return "title"
        if text is axes.xaxis.label or text is axes.yaxis.label:
            return "axis_label"
        if text in axes.get_xticklabels() or text in axes.get_yticklabels():
            return "tick_label"
    if text in figure.texts:
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

    unsupported_marks = sum(
        len(axes.collections) + len(axes.patches) + len(axes.images)
        for axes in figure.axes
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "coordinate_system": "pixels; origin top-left",
        "artifact": artifact,
        "canvas": {"x": 0.0, "y": 0.0, "width": width, "height": height},
        "plot_areas": plot_areas,
        "transforms": transforms,
        "elements": elements,
        "series": series,
        "legends": legends,
        "coverage": {
            "text_bounds": True,
            "line_series_paths": True,
            "unsupported_non_line_mark_count": unsupported_marks,
        },
    }


def render_chart(
    source_path: str,
    output_dir: str,
    artifact_name: str = "chart.png",
    build_function: str = "build_chart",
    dpi: int | None = None,
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
        "spec": user_spec,
    }
    write_json(spec_path, spec)
    write_json(layout_path, layout)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_iso(),
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
