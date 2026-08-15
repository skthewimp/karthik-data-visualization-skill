from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

from .artifacts import raster_info, read_json, sha256_file, write_json


SCHEMA_VERSION = 1


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


def _contains(container: dict[str, Any], inner: dict[str, Any], tolerance: float = 0.5) -> bool:
    c_left, c_top, c_right, c_bottom = _edges(container)
    i_left, i_top, i_right, i_bottom = _edges(inner)
    return (
        i_left >= c_left - tolerance
        and i_top >= c_top - tolerance
        and i_right <= c_right + tolerance
        and i_bottom <= c_bottom + tolerance
    )


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
    minimum_text_margin_px: float | None = None

    if metadata is not None:
        canvas = metadata["canvas"]
        plot_areas = {item["id"]: item["bbox"] for item in metadata.get("plot_areas", [])}
        elements = metadata.get("elements", [])
        annotations = [item for item in elements if item.get("role") == "annotation"]
        series = [item for item in metadata.get("series", []) if item.get("role") == "series"]
        margins = [_margin(canvas, item["bbox"]) for item in elements]
        minimum_text_margin_px = round(min(margins), 3) if margins else None

        for element in elements:
            bbox = element["bbox"]
            if not _contains(canvas, bbox):
                record = {
                    "id": element["id"],
                    "role": element["role"],
                    "bbox": bbox,
                    "canvas_margin_px": round(_margin(canvas, bbox), 3),
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
                if area <= 0:
                    continue
                record = {
                    "annotations": [first["id"], second["id"]],
                    "intersection_area_px2": round(area, 3),
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

    unsupported_marks = (
        metadata.get("coverage", {}).get("unsupported_non_line_mark_count", 0)
        if metadata
        else 0
    )
    checks_complete = metadata is not None and unsupported_marks == 0
    if unsupported_marks:
        limitations.append(
            f"{unsupported_marks} non-line mark collection(s), patch(es), or image(s) lack collision geometry"
        )
    blocking = [item for item in defects if item["severity"] in ("high", "medium")]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact": artifact,
        "layout_metadata": (
            {"path": str(metadata_file), "sha256": sha256_file(metadata_file)}
            if metadata_file
            else None
        ),
        "inspection_mode": "raster+layout-metadata" if metadata else "raster-only",
        "checks_complete": checks_complete,
        "passes_geometry_checks": checks_complete and not blocking,
        "width": artifact["width"],
        "height": artifact["height"],
        "text_clipped": bool(clipped_text or out_of_bounds_elements),
        "annotation_overlaps": annotation_overlaps,
        "label_label_collisions": label_label_collisions,
        "out_of_bounds_elements": out_of_bounds_elements,
        "clipped_text": clipped_text,
        "long_unwrapped_annotations": long_unwrapped_annotations,
        "minimum_text_margin_px": minimum_text_margin_px,
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
