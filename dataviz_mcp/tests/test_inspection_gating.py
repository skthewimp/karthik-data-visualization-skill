"""Gating fixes: a blank render must block, and an unrecognised table gtable must not
manufacture false bbox-derived defects (out-of-bounds, contrast) it has no reliable bounds for.
Both exercise inspect_rendered_chart end to end with a real PNG plus hash-matched metadata,
so no R renderer is required."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from dataviz_mcp.artifacts import raster_info, sha256_file
from dataviz_mcp.inspection import BLANK_RENDER_MAX, inspect_rendered_chart


def _write_png(path: Path, width: int, height: int, colour: str = "white") -> None:
    Image.new("RGB", (width, height), colour).save(path)


def _bundle(tmp_path: Path, width: int, height: int, metadata: dict, colour: str = "white"):
    png = tmp_path / "art.png"
    _write_png(png, width, height, colour)
    info = raster_info(png)
    metadata = {
        **metadata,
        "artifact": {"sha256": info["sha256"], "width": width, "height": height},
    }
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(metadata))
    return inspect_rendered_chart(str(png), str(meta_path))


def _codes(report: dict) -> set[str]:
    return {d["code"] for d in report["defects"]}


def test_blank_render_blocks_and_cannot_pass(tmp_path: Path) -> None:
    # No elements/marks/series/legends -> occupied ratio 0.0 -> blank export.
    report = _bundle(
        tmp_path,
        400,
        300,
        {
            "canvas": {"x": 0, "y": 0, "width": 400, "height": 300},
            "plot_areas": [],
            "elements": [],
            "series": [],
            "marks": [],
            "legends": [],
            "coverage": {},
            "background": "#ffffff",
        },
    )
    assert report["occupied_utilization_ratio"] == 0.0
    assert "BLANK_RENDER" in _codes(report)
    blank = next(d for d in report["defects"] if d["code"] == "BLANK_RENDER")
    assert blank["severity"] == "high"
    assert report["passes_geometry_checks"] is False
    assert report["geometry_status"] == "fail"


def test_ratio_just_above_blank_floor_is_not_blank(tmp_path: Path) -> None:
    # An element covering ~10% of the canvas is sparse, not blank: no BLANK_RENDER.
    report = _bundle(
        tmp_path,
        400,
        300,
        {
            "canvas": {"x": 0, "y": 0, "width": 400, "height": 300},
            "plot_areas": [],
            "elements": [{"id": "t", "role": "title",
                          "bbox": {"x": 10, "y": 10, "width": 120, "height": 100}}],
            "series": [],
            "marks": [],
            "legends": [],
            "coverage": {"text_bounds": True},
            "background": "#ffffff",
        },
    )
    assert report["occupied_utilization_ratio"] > BLANK_RENDER_MAX
    assert "BLANK_RENDER" not in _codes(report)


def _table_meta(cell_bounds: bool) -> dict:
    coverage = {"table_content": True, "text_bounds": True}
    if cell_bounds:
        coverage["table_cell_bounds"] = True
    return {
        "canvas": {"x": 0, "y": 0, "width": 400, "height": 300},
        "plot_areas": [],
        # An element whose bbox leaks past the right edge (450 > 400) - a would-be OUT_OF_BOUNDS.
        "elements": [{"id": "cell", "role": "table",
                      "bbox": {"x": 50, "y": 50, "width": 400, "height": 100}}],
        "series": [],
        "marks": [],
        "legends": [],
        "coverage": coverage,
        "background": "#ffffff",
    }


def test_unrecognised_table_gtable_suppresses_false_defects(tmp_path: Path) -> None:
    # table_content with no table_cell_bounds -> element bboxes are the leaked wrapper; the
    # out-of-canvas bbox must NOT raise OUT_OF_BOUNDS, and the run degrades to incomplete.
    report = _bundle(tmp_path, 400, 300, _table_meta(cell_bounds=False))
    assert "OUT_OF_BOUNDS" not in _codes(report)
    assert report["out_of_bounds_elements"] == []
    assert report["checks_complete"] is False
    assert report["passes_geometry_checks"] is False
    assert any("tableGrob/gt" in note for note in report["limitations"])


def test_recognised_table_gtable_still_flags_out_of_bounds(tmp_path: Path) -> None:
    # With table_cell_bounds present the bboxes are trustworthy, so the same leak DOES flag.
    report = _bundle(tmp_path, 400, 300, _table_meta(cell_bounds=True))
    assert "OUT_OF_BOUNDS" in _codes(report)
    assert not any("tableGrob/gt" in note for note in report["limitations"])
