from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

from .artifacts import raster_info, read_json, sha256_file, write_json
from .color_math import _contrast_ratio
from .layout import MIN_PANEL_H, suggest_dims_for_overflow


SCHEMA_VERSION = 3


def _edges(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    left = float(bbox["x"])
    top = float(bbox["y"])
    return left, top, left + float(bbox["width"]), top + float(bbox["height"])


def _intersection_area(first: dict[str, Any], second: dict[str, Any]) -> float:
    a_left, a_top, a_right, a_bottom = _edges(first)
    b_left, b_top, b_right, b_bottom = _edges(second)
    width = min(a_right, b_right) - max(a_left, b_left)
    height = min(a_bottom, b_bottom) - max(a_top, b_top)
    return max(0.0, width) * max(0.0, height)


def _meaningful_box_overlap(
    first: dict[str, Any], second: dict[str, Any], tolerance_px: float = 0.5
) -> bool:
    first_left, first_top, first_right, first_bottom = _edges(first)
    second_left, second_top, second_right, second_bottom = _edges(second)
    overlap_width = min(first_right, second_right) - max(first_left, second_left)
    overlap_height = min(first_bottom, second_bottom) - max(first_top, second_top)
    return overlap_width > tolerance_px and overlap_height > tolerance_px


def _union_area(boxes: list[dict[str, Any]]) -> float:
    if not boxes:
        return 0.0
    xs = sorted({edge for box in boxes for edge in (_edges(box)[0], _edges(box)[2])})
    area = 0.0
    for left, right in zip(xs, xs[1:]):
        intervals = sorted(
            (_edges(box)[1], _edges(box)[3])
            for box in boxes
            if _edges(box)[0] < right and _edges(box)[2] > left
        )
        if not intervals:
            continue
        covered = 0.0
        start, end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start > end:
                covered += end - start
                start, end = next_start, next_end
            else:
                end = max(end, next_end)
        covered += end - start
        area += (right - left) * covered
    return area


def _contains(container: dict[str, Any], inner: dict[str, Any], tolerance: float = 0.5) -> bool:
    c_left, c_top, c_right, c_bottom = _edges(container)
    i_left, i_top, i_right, i_bottom = _edges(inner)
    return (
        i_left >= c_left - tolerance
        and i_top >= c_top - tolerance
        and i_right <= c_right + tolerance
        and i_bottom <= c_bottom + tolerance
    )


def _overflow(container: dict[str, Any], inner: dict[str, Any]) -> dict[str, float]:
    """Per-edge overflow (px) of ``inner`` past ``container`` - the fix vector for a clip."""
    c_left, c_top, c_right, c_bottom = _edges(container)
    i_left, i_top, i_right, i_bottom = _edges(inner)
    return {
        "left": round(max(0.0, c_left - i_left), 2),
        "top": round(max(0.0, c_top - i_top), 2),
        "right": round(max(0.0, i_right - c_right), 2),
        "bottom": round(max(0.0, i_bottom - c_bottom), 2),
    }


def _separation_needed(first: dict[str, Any], second: dict[str, Any]) -> float:
    """Smallest px move that clears an overlap between two boxes (least-penetration axis)."""
    a_left, a_top, a_right, a_bottom = _edges(first)
    b_left, b_top, b_right, b_bottom = _edges(second)
    overlap_w = min(a_right, b_right) - max(a_left, b_left)
    overlap_h = min(a_bottom, b_bottom) - max(a_top, b_top)
    return round(max(0.0, min(overlap_w, overlap_h)), 2)


def _margin(container: dict[str, Any], inner: dict[str, Any]) -> float:
    c_left, c_top, c_right, c_bottom = _edges(container)
    i_left, i_top, i_right, i_bottom = _edges(inner)
    return min(i_left - c_left, i_top - c_top, c_right - i_right, c_bottom - i_bottom)


def _point_in_rect(point: list[float], bbox: dict[str, Any], padding: float) -> bool:
    left, top, right, bottom = _edges(bbox)
    x, y = point
    return left - padding <= x <= right + padding and top - padding <= y <= bottom + padding


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if math.isclose(value, 0.0, abs_tol=1e-9):
        return 0
    return 1 if value > 0 else 2


def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (
        (o1 == 0 and _on_segment(a, c, b))
        or (o2 == 0 and _on_segment(a, d, b))
        or (o3 == 0 and _on_segment(c, a, d))
        or (o4 == 0 and _on_segment(c, b, d))
    )


def _segment_hits_bbox(
    first: list[float], second: list[float], bbox: dict[str, Any], padding: float
) -> bool:
    if _point_in_rect(first, bbox, padding) or _point_in_rect(second, bbox, padding):
        return True
    left, top, right, bottom = _edges(bbox)
    left -= padding
    top -= padding
    right += padding
    bottom += padding
    edges = (
        ((left, top), (right, top)),
        ((right, top), (right, bottom)),
        ((right, bottom), (left, bottom)),
        ((left, bottom), (left, top)),
    )
    a = (float(first[0]), float(first[1]))
    b = (float(second[0]), float(second[1]))
    return any(_segments_intersect(a, b, edge[0], edge[1]) for edge in edges)


def _series_hits_bbox(series: dict[str, Any], bbox: dict[str, Any], padding: float) -> bool:
    segments = series.get("segments") or [series.get("points", [])]
    return any(
        _segment_hits_bbox(first, second, bbox, padding)
        for points in segments
        for first, second in zip(points, points[1:])
    )


def _looks_numeric(text: str) -> bool:
    """True when a tick label reads as a number (so it duplicates a direct value label).

    Category tick labels (names) are never redundant; only the numeric value axis is. Strips
    the usual money/percent/thousands decoration before testing.
    """
    stripped = text.strip()
    if not stripped:
        return False
    for token in ("$", "€", "£", "%", ",", " ", "+", "−"):
        stripped = stripped.replace(token, "")
    stripped = stripped.lstrip("-")
    if stripped.endswith(("k", "K", "m", "M", "b", "B")):
        stripped = stripped[:-1]
    try:
        float(stripped)
        return True
    except ValueError:
        return False


def _underfill_defect(
    occupied_ratio: float | None,
    has_undersized_text: bool,
    threshold: float = 0.30,
) -> dict[str, Any] | None:
    """Flag a canvas that carries too little ink for its size - the "empty dot panels" failure.

    Keyed to ``occupied_utilization_ratio`` (already measured): the fraction of the canvas any
    element, mark, series, or legend actually covers. Below ``threshold`` the layout is mostly
    empty. It escalates to ``medium`` when text is also undersized - empty *and* tiny is the
    mobile-table redesign case, where the answer is a denser layout or the requested table; on
    its own it is a ``low`` suggestion, since a single big number can legitimately be sparse.
    """
    if occupied_ratio is None or occupied_ratio >= threshold:
        return None
    severity = "medium" if has_undersized_text else "low"
    return _defect(
        "UNDERFILLED_CANVAS",
        severity,
        [],
        f"Only {occupied_ratio:.0%} of the canvas carries ink; the layout is mostly empty - "
        "size marks and text to the space, use a denser layout, or the requested table.",
        {"occupied_utilization_ratio": occupied_ratio, "threshold": threshold},
    )


def _defect(
    code: str,
    severity: str,
    element_ids: Iterable[str],
    message: str,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "element_ids": list(element_ids),
        "message": message,
    }
    if geometry:
        value["geometry"] = geometry
    return value


def inspect_rendered_chart(
    artifact_path: str,
    layout_metadata_path: str | None = None,
    output_path: str | None = None,
    series_clearance_px: float = 2.0,
    max_unwrapped_annotation_chars: int = 45,
    delivery_profile: str | None = None,
    minimum_text_size_pt: float = 8.0,
) -> dict[str, Any]:
    """Inspect the exact raster plus matching deterministic layout metadata."""
    artifact_file = Path(artifact_path).expanduser().resolve()
    if not artifact_file.is_file():
        raise ValueError(f"Artifact not found: {artifact_file}")
    artifact = raster_info(artifact_file)
    if series_clearance_px < 0:
        raise ValueError("series_clearance_px must be zero or greater")
    if max_unwrapped_annotation_chars < 1:
        raise ValueError("max_unwrapped_annotation_chars must be greater than zero")
    if minimum_text_size_pt <= 0:
        raise ValueError("minimum_text_size_pt must be greater than zero")

    metadata: dict[str, Any] | None = None
    metadata_file: Path | None = None
    limitations: list[str] = []
    if layout_metadata_path:
        metadata_file = Path(layout_metadata_path).expanduser().resolve()
        metadata = read_json(metadata_file)
        metadata_artifact = metadata.get("artifact", {})
        if metadata_artifact.get("sha256") != artifact["sha256"]:
            raise ValueError(
                "Layout metadata artifact hash does not match the exact artifact being inspected"
            )
        if (metadata_artifact.get("width"), metadata_artifact.get("height")) != (
            artifact["width"],
            artifact["height"],
        ):
            raise ValueError("Layout metadata dimensions do not match the exact artifact")
    else:
        limitations.append(
            "No layout metadata supplied; collision, clipping, overflow, and text-margin checks are unknown"
        )

    defects: list[dict[str, Any]] = []
    annotation_overlaps: list[dict[str, Any]] = []
    label_label_collisions: list[dict[str, Any]] = []
    out_of_bounds_elements: list[dict[str, Any]] = []
    clipped_text: list[dict[str, Any]] = []
    long_unwrapped_annotations: list[dict[str, Any]] = []
    text_text_collisions: list[dict[str, Any]] = []
    text_mark_collisions: list[dict[str, Any]] = []
    legend_collisions: list[dict[str, Any]] = []
    low_contrast_elements: list[dict[str, Any]] = []
    undersized_text: list[dict[str, Any]] = []
    direct_label_coverage: list[dict[str, Any]] = []
    redundant_value_axis: list[dict[str, Any]] = []
    external_legend: list[dict[str, Any]] = []
    redundant_colour: list[dict[str, Any]] = []
    minimum_text_margin_px: float | None = None
    plot_utilization_ratio: float | None = None
    occupied_utilization_ratio: float | None = None
    panel_heights_px: list[float] = []
    min_panel_height_px: float | None = None

    if metadata is not None:
        canvas = metadata["canvas"]
        plot_areas = {item["id"]: item["bbox"] for item in metadata.get("plot_areas", [])}
        panel_heights_px = [round(float(bbox["height"]), 1) for bbox in plot_areas.values()]
        min_panel_height_px = min(panel_heights_px) if panel_heights_px else None
        elements = metadata.get("elements", [])
        annotations = [item for item in elements if item.get("role") == "annotation"]
        series = [item for item in metadata.get("series", []) if item.get("role") == "series"]
        marks = metadata.get("marks", [])
        legends = metadata.get("legends", [])
        margins = [_margin(canvas, item["bbox"]) for item in elements]
        minimum_text_margin_px = round(min(margins), 3) if margins else None
        canvas_area = float(canvas["width"]) * float(canvas["height"])
        plot_utilization_ratio = round(
            _union_area(list(plot_areas.values())) / canvas_area, 6
        ) if canvas_area else None
        occupied_boxes = [item["bbox"] for item in elements + marks + series + legends]
        occupied_utilization_ratio = round(
            _union_area(occupied_boxes) / canvas_area, 6
        ) if canvas_area else None

        for element in elements:
            bbox = element["bbox"]
            if not _contains(canvas, bbox):
                overflow = _overflow(canvas, bbox)
                record = {
                    "id": element["id"],
                    "role": element["role"],
                    "bbox": bbox,
                    "canvas_margin_px": round(_margin(canvas, bbox), 3),
                    "overflow_px": overflow,
                    "grow_margin_px": {
                        "width": round(overflow["left"] + overflow["right"], 2),
                        "height": round(overflow["top"] + overflow["bottom"], 2),
                    },
                }
                out_of_bounds_elements.append(record)
                defects.append(
                    _defect(
                        "OUT_OF_BOUNDS",
                        "high",
                        [element["id"]],
                        f"{element['role']} {element['id']} extends beyond the canvas",
                        {"bbox": bbox},
                    )
                )
            font_size = element.get("font_size_pt")
            if isinstance(font_size, (int, float)) and font_size < minimum_text_size_pt:
                record = {
                    "id": element["id"],
                    "role": element["role"],
                    "font_size_pt": font_size,
                    "minimum_text_size_pt": minimum_text_size_pt,
                }
                undersized_text.append(record)
                defects.append(
                    _defect(
                        "DELIVERY_TEXT_TOO_SMALL",
                        "medium",
                        [element["id"]],
                        f"{element['role']} {element['id']} is {font_size} pt at delivery scale",
                    )
                )
            ratio = _contrast_ratio(element.get("colour"), metadata.get("background"))
            if ratio is not None:
                target = 3.0 if isinstance(font_size, (int, float)) and font_size >= 14 else 4.5
                if ratio < target:
                    record = {
                        "id": element["id"],
                        "role": element["role"],
                        "contrast_ratio": round(ratio, 3),
                        "target": target,
                    }
                    low_contrast_elements.append(record)
                    defects.append(
                        _defect(
                            "LOW_TEXT_CONTRAST",
                            "medium",
                            [element["id"]],
                            f"{element['role']} {element['id']} contrast is {ratio:.2f}:1",
                        )
                    )
            axes_id = element.get("axes_id")
            if (
                element.get("role") in ("annotation", "label")
                and element.get("clip_on")
                and axes_id in plot_areas
                and not _contains(plot_areas[axes_id], bbox)
            ):
                record = {
                    "id": element["id"],
                    "role": element["role"],
                    "bbox": bbox,
                    "plot_area": plot_areas[axes_id],
                }
                clipped_text.append(record)
                defects.append(
                    _defect(
                        "TEXT_CLIPPED",
                        "high",
                        [element["id"]],
                        f"Text {element['id']} crosses a clipping plot boundary",
                        {"bbox": bbox, "plot_area": plot_areas[axes_id]},
                    )
                )

        for index, first in enumerate(annotations):
            text = first.get("text", "")
            if "\n" not in text and len(text) > max_unwrapped_annotation_chars:
                record = {
                    "id": first["id"],
                    "text": text,
                    "characters": len(text),
                    "limit": max_unwrapped_annotation_chars,
                }
                long_unwrapped_annotations.append(record)
                defects.append(
                    _defect(
                        "LONG_UNWRAPPED_ANNOTATION",
                        "medium",
                        [first["id"]],
                        f"Annotation {first['id']} has {len(text)} unwrapped characters",
                    )
                )
            for second in annotations[index + 1 :]:
                area = _intersection_area(first["bbox"], second["bbox"])
                if not _meaningful_box_overlap(first["bbox"], second["bbox"]):
                    continue
                record = {
                    "annotations": [first["id"], second["id"]],
                    "intersection_area_px2": round(area, 3),
                    "separation_needed_px": _separation_needed(first["bbox"], second["bbox"]),
                }
                label_label_collisions.append(record)
                defects.append(
                    _defect(
                        "LABEL_LABEL_COLLISION",
                        "high",
                        [first["id"], second["id"]],
                        f"Annotations {first['id']} and {second['id']} overlap",
                        {"intersection_area_px2": round(area, 3)},
                    )
                )
            for line in series:
                if first.get("axes_id") != line.get("axes_id"):
                    continue
                if not _series_hits_bbox(line, first["bbox"], series_clearance_px):
                    continue
                record = {
                    "annotation": first["id"],
                    "intersects": line["id"],
                    "severity": "high",
                    "clearance_px": series_clearance_px,
                }
                annotation_overlaps.append(record)
                defects.append(
                    _defect(
                        "ANNOTATION_SERIES_COLLISION",
                        "high",
                        [first["id"], line["id"]],
                        f"Annotation {first['id']} intersects series {line['id']}",
                        {"annotation_bbox": first["bbox"]},
                    )
                )

        hierarchy_roles = {"title", "subtitle", "panel_heading", "footer"}
        ignored_text_roles = {"legend_text"}
        for index, first in enumerate(elements):
            for second in elements[index + 1 :]:
                if first.get("role") in ignored_text_roles and second.get("role") in ignored_text_roles:
                    continue
                area = _intersection_area(first["bbox"], second["bbox"])
                if not _meaningful_box_overlap(first["bbox"], second["bbox"]):
                    continue
                if first.get("role") == "annotation" and second.get("role") == "annotation":
                    continue
                roles = {first.get("role"), second.get("role")}
                code = (
                    "HIERARCHY_TEXT_COLLISION"
                    if roles & hierarchy_roles
                    else "TEXT_TEXT_COLLISION"
                )
                record = {
                    "elements": [first["id"], second["id"]],
                    "roles": [first.get("role"), second.get("role")],
                    "intersection_area_px2": round(area, 3),
                    "separation_needed_px": _separation_needed(first["bbox"], second["bbox"]),
                }
                text_text_collisions.append(record)
                defects.append(
                    _defect(
                        code,
                        "high",
                        [first["id"], second["id"]],
                        f"{first.get('role')} {first['id']} overlaps {second.get('role')} {second['id']}",
                        {"intersection_area_px2": round(area, 3)},
                    )
                )

        collision_text_roles = {"annotation", "label", "figure_text"}
        for element in elements:
            if element.get("role") not in collision_text_roles:
                continue
            for mark in marks:
                if element.get("axes_id") and mark.get("axes_id") != element.get("axes_id"):
                    continue
                area = _intersection_area(element["bbox"], mark["bbox"])
                if not _meaningful_box_overlap(element["bbox"], mark["bbox"]):
                    continue
                record = {
                    "text": element["id"],
                    "mark": mark["id"],
                    "intersection_area_px2": round(area, 3),
                }
                text_mark_collisions.append(record)
                defects.append(
                    _defect(
                        "TEXT_MARK_COLLISION",
                        "high",
                        [element["id"], mark["id"]],
                        f"Text {element['id']} overlaps mark {mark['id']} without an inside-label declaration",
                        {"intersection_area_px2": round(area, 3)},
                    )
                )

        for legend in legends:
            for element in elements:
                if element.get("role") == "legend_text":
                    continue
                area = _intersection_area(legend["bbox"], element["bbox"])
                if not _meaningful_box_overlap(legend["bbox"], element["bbox"]):
                    continue
                record = {
                    "legend": legend["id"],
                    "element": element["id"],
                    "intersection_area_px2": round(area, 3),
                }
                legend_collisions.append(record)
                defects.append(
                    _defect(
                        "LEGEND_TEXT_COLLISION",
                        "high",
                        [legend["id"], element["id"]],
                        f"Legend {legend['id']} overlaps {element.get('role')} {element['id']}",
                    )
                )

        contract = metadata.get("inspection_contract", {})
        expectations = contract.get("direct_labels", []) if isinstance(contract, dict) else []
        for expectation in expectations:
            if not isinstance(expectation, dict):
                continue
            axes_id = expectation.get("axes_id")
            role = expectation.get("role", "label")
            expected = int(expectation.get("expected_count", 0))
            observed = sum(
                item.get("role") == role and (axes_id is None or item.get("axes_id") == axes_id)
                for item in elements
            )
            result = {
                "axes_id": axes_id,
                "role": role,
                "expected_count": expected,
                "observed_count": observed,
                "complete": observed >= expected,
            }
            direct_label_coverage.append(result)
            if observed < expected:
                defects.append(
                    _defect(
                        "DIRECT_LABELS_INCOMPLETE",
                        "high",
                        [],
                        f"{axes_id or 'shared chart'} has {observed} of {expected} required {role}s",
                    )
                )
    if metadata is not None:
        # Redundant value axis: when every mark carries its own value label, the numeric axis
        # ticks duplicate that ink. Category ticks (non-numeric) still name marks, so only
        # numeric ticks flag - and it is a suggestion (low), not a blocking defect.
        labels_complete = any(
            item.get("complete") and item.get("expected_count", 0) > 0
            for item in direct_label_coverage
        )
        if labels_complete:
            numeric_ticks = [
                element
                for element in metadata.get("elements", [])
                if element.get("role") == "tick_label" and _looks_numeric(element.get("text", ""))
            ]
            if numeric_ticks:
                ids = [element["id"] for element in numeric_ticks]
                redundant_value_axis.append({"element_ids": ids, "tick_count": len(ids)})
                defects.append(
                    _defect(
                        "REDUNDANT_VALUE_AXIS",
                        "low",
                        ids,
                        "Every mark is directly labelled; the numeric value axis duplicates the "
                        "labels - consider dropping its ticks and gridlines (eraser test).",
                    )
                )

    if metadata is not None:
        # Redundant colour and external legend: colour or a legend that only restates a
        # grouping the plot already encodes another way - a facet title, a category-axis tick,
        # or a direct label. Both are fine when they carry what no other channel does (several
        # series sharing one panel with no direct labels); they are duplicate ink once every
        # series or bar is already named on the plot. Direct labelling of a series always makes
        # its legend redundant, however many series share the panel. Both are eraser-test
        # suggestions (low), never blocking - the precise trigger, not the severity, keeps
        # legitimate charts (many crossing lines with no labels; a focal-plus-grey highlight)
        # silent.
        all_elements = metadata.get("elements", [])
        all_series = [s for s in metadata.get("series", []) if s.get("role") == "series"]
        bar_marks = [m for m in metadata.get("marks", []) if m.get("fill")]
        legends_meta = [lg for lg in metadata.get("legends", []) if lg.get("bbox")]

        axes_with_direct_label = {
            el.get("axes_id")
            for el in all_elements
            if el.get("role") == "label" and el.get("axes_id")
        }
        series_axes = [s.get("axes_id") for s in all_series if s.get("axes_id")]
        distinct_series_axes = set(series_axes)
        one_series_per_facet = (
            len(distinct_series_axes) > 1
            and len(all_series) > 1
            and all(series_axes.count(axes_id) == 1 for axes_id in distinct_series_axes)
        )
        series_colours = {s.get("colour") for s in all_series if s.get("colour")}
        series_axes_labelled = bool(series_axes) and distinct_series_axes <= axes_with_direct_label

        # Bars: colour restates the category axis when every bar carries its own fill and the
        # axis already ticks each one by name. A focal-plus-grey highlight (fewer fills than
        # bars) is meaningful emphasis and stays silent. Tick labels are not tagged per-axes, so
        # count the category (non-numeric) ticks across the chart.
        category_tick_count = sum(
            el.get("role") == "tick_label" and not _looks_numeric(el.get("text", ""))
            for el in all_elements
        )
        bar_colour_redundant_axes: list[str] = []
        for axes_id in {m.get("axes_id") for m in bar_marks if m.get("axes_id")}:
            axes_bars = [m for m in bar_marks if m.get("axes_id") == axes_id]
            fills = {m.get("fill") for m in axes_bars}
            if (
                len(fills) >= 2
                and len(fills) == len(axes_bars)
                and category_tick_count >= len(fills)
            ):
                bar_colour_redundant_axes.append(axes_id)

        colour_redundant = (
            (one_series_per_facet and len(series_colours) >= 2)
            or bool(bar_colour_redundant_axes)
            or (len(all_series) > 1 and len(series_colours) >= 2 and series_axes_labelled)
        )
        if colour_redundant:
            ids = [s["id"] for s in all_series] + [
                m["id"] for m in bar_marks if m.get("axes_id") in bar_colour_redundant_axes
            ]
            redundant_colour.append({"element_ids": ids})
            defects.append(
                _defect(
                    "REDUNDANT_COLOUR",
                    "low",
                    ids,
                    "Colour only restates a grouping the facet, category axis, or direct labels "
                    "already show - drop it (or reserve it for one focal series) (eraser test).",
                )
            )

        legend_redundant = (
            one_series_per_facet
            or bool(bar_colour_redundant_axes)
            or series_axes_labelled
        )
        if legends_meta and legend_redundant:
            ids = [lg["id"] for lg in legends_meta]
            external_legend.append({"element_ids": ids})
            defects.append(
                _defect(
                    "EXTERNAL_LEGEND",
                    "low",
                    ids,
                    "The series are already named on the plot (direct labels, facet titles, or "
                    "category ticks); the external legend is a round-trip - label them in place "
                    "and drop it (eraser test).",
                )
            )

    if metadata is not None:
        underfill = _underfill_defect(occupied_utilization_ratio, bool(undersized_text))
        if underfill is not None:
            defects.append(underfill)

    coverage = metadata.get("coverage", {}) if metadata else {}
    unsupported_marks = coverage.get("unsupported_non_line_mark_count", 0)
    coverage_limitations = coverage.get("limitations", [])
    checks_complete = (
        metadata is not None
        and unsupported_marks == 0
        and bool(coverage.get("text_bounds"))
        and bool(coverage.get("line_series_paths"))
        and bool(coverage.get("patch_and_common_collection_bounds"))
    )
    if unsupported_marks:
        limitations.append(
            f"{unsupported_marks} non-line mark collection(s), patch(es), or image(s) lack collision geometry"
        )
    limitations.extend(str(item) for item in coverage_limitations)
    if metadata is not None and not checks_complete and not unsupported_marks and coverage_limitations:
        limitations.append("Renderer geometry coverage is incomplete for a full mechanical pass")
    blocking = [item for item in defects if item["severity"] in ("high", "medium")]

    # Turn the measured overflow and squash into a single fix vector the caller can apply.
    edge_overflow = {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}
    for element in out_of_bounds_elements:
        for edge, value in element["overflow_px"].items():
            edge_overflow[edge] = max(edge_overflow[edge], value)
    squashed = (
        min_panel_height_px is not None and min_panel_height_px < MIN_PANEL_H
    )
    suggested_dims = None
    if any(edge_overflow.values()) or squashed:
        suggested_dims = suggest_dims_for_overflow(
            artifact["width"],
            artifact["height"],
            top_overflow_px=edge_overflow["top"],
            bottom_overflow_px=edge_overflow["bottom"],
            left_overflow_px=edge_overflow["left"],
            right_overflow_px=edge_overflow["right"],
            min_panel_height_px=min_panel_height_px,
        )
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    worst_offenders = [
        {"code": item["code"], "severity": item["severity"], "element_ids": item["element_ids"]}
        for item in sorted(defects, key=lambda d: severity_rank.get(d["severity"], 3))[:3]
    ]
    geometry_summary = {
        "clip_px_max": round(max(edge_overflow.values()), 2) if out_of_bounds_elements else 0.0,
        "edge_overflow_px": edge_overflow,
        "min_panel_height_px": min_panel_height_px,
        "panels_squashed": squashed,
        "worst_offenders": worst_offenders,
        "suggested_dims": suggested_dims,
    }

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact": artifact,
        "layout_metadata": (
            {"path": str(metadata_file), "sha256": sha256_file(metadata_file)}
            if metadata_file
            else None
        ),
        "inspection_mode": "raster+layout-metadata" if metadata else "raster-only",
        "delivery_profile": delivery_profile,
        "checks_complete": checks_complete,
        "passes_geometry_checks": checks_complete and not blocking,
        "width": artifact["width"],
        "height": artifact["height"],
        "text_clipped": bool(clipped_text or out_of_bounds_elements),
        "annotation_overlaps": annotation_overlaps,
        "label_label_collisions": label_label_collisions,
        "text_text_collisions": text_text_collisions,
        "text_mark_collisions": text_mark_collisions,
        "legend_collisions": legend_collisions,
        "out_of_bounds_elements": out_of_bounds_elements,
        "clipped_text": clipped_text,
        "long_unwrapped_annotations": long_unwrapped_annotations,
        "undersized_text": undersized_text,
        "low_contrast_elements": low_contrast_elements,
        "direct_label_coverage": direct_label_coverage,
        "redundant_value_axis": redundant_value_axis,
        "external_legend": external_legend,
        "redundant_colour": redundant_colour,
        "minimum_text_margin_px": minimum_text_margin_px,
        "plot_utilization_ratio": plot_utilization_ratio,
        "occupied_utilization_ratio": occupied_utilization_ratio,
        "panel_heights_px": panel_heights_px,
        "min_panel_height_px": min_panel_height_px,
        "geometry_summary": geometry_summary,
        "defects": defects,
        "limitations": limitations,
    }
    destination = (
        Path(output_path).expanduser().resolve()
        if output_path
        else artifact_file.parent / "inspection.json"
    )
    write_json(destination, report)
    report["inspection_path"] = str(destination)
    report["inspection_sha256"] = sha256_file(destination)
    return report
