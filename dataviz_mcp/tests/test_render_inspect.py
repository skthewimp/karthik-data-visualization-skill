from __future__ import annotations

import json
from pathlib import Path

import pytest

from dataviz_mcp.artifacts import sha256_file
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import render_chart


FIXTURES = Path(__file__).parent / "fixtures" / "chart_fixtures.py"


def render(tmp_path: Path, function: str) -> tuple[dict, dict]:
    bundle_dir = tmp_path / function
    bundle = render_chart(str(FIXTURES), str(bundle_dir), build_function=function)
    report = inspect_rendered_chart(
        bundle["artifact"]["path"],
        bundle["layout_metadata_path"],
    )
    return bundle, report


def test_render_emits_versioned_bundle_with_matching_hashes(tmp_path: Path) -> None:
    bundle, report = render(tmp_path, "clean_chart")
    for name in (
        "artifact",
        "chart_spec_path",
        "layout_metadata_path",
        "manifest_path",
    ):
        value = bundle[name]
        path = Path(value["path"] if isinstance(value, dict) else value)
        assert path.is_file()
    manifest = json.loads(Path(bundle["manifest_path"]).read_text())
    assert manifest["artifact"]["sha256"] == sha256_file(Path(bundle["artifact"]["path"]))
    assert manifest["layout_metadata"]["sha256"] == sha256_file(
        Path(bundle["layout_metadata_path"])
    )
    assert report["artifact"]["sha256"] == manifest["artifact"]["sha256"]
    assert report["width"] == 800
    assert report["height"] == 450
    assert report["passes_geometry_checks"] is True


@pytest.mark.parametrize(
    ("function", "code"),
    (
        ("annotation_over_line", "ANNOTATION_SERIES_COLLISION"),
        ("two_annotations_overlap", "LABEL_LABEL_COLLISION"),
        ("annotation_outside_canvas", "OUT_OF_BOUNDS"),
        ("clipped_annotation", "TEXT_CLIPPED"),
        ("long_unwrapped_annotation", "LONG_UNWRAPPED_ANNOTATION"),
    ),
)
def test_fixture_reports_expected_geometry_defect(
    tmp_path: Path, function: str, code: str
) -> None:
    _, report = render(tmp_path, function)
    assert code in {item["code"] for item in report["defects"]}
    assert report["passes_geometry_checks"] is False


def test_clean_chart_passes_all_geometry_checks(tmp_path: Path) -> None:
    _, report = render(tmp_path, "clean_chart")
    assert report["defects"] == []
    assert report["annotation_overlaps"] == []
    assert report["label_label_collisions"] == []
    assert report["out_of_bounds_elements"] == []
    assert report["text_clipped"] is False
    assert report["minimum_text_margin_px"] > 0


def test_missing_line_segment_does_not_create_a_false_collision(tmp_path: Path) -> None:
    _, report = render(tmp_path, "line_with_gap")
    assert report["annotation_overlaps"] == []
    assert report["passes_geometry_checks"] is True


def test_unsupported_non_line_marks_leave_collision_coverage_incomplete(
    tmp_path: Path,
) -> None:
    _, report = render(tmp_path, "unsupported_bar_marks")
    assert report["checks_complete"] is False
    assert report["passes_geometry_checks"] is False
    assert "non-line mark" in report["limitations"][0]


def test_raster_only_inspection_is_honestly_incomplete(tmp_path: Path) -> None:
    bundle = render_chart(str(FIXTURES), str(tmp_path), build_function="clean_chart")
    report = inspect_rendered_chart(bundle["artifact"]["path"])
    assert report["inspection_mode"] == "raster-only"
    assert report["checks_complete"] is False
    assert report["passes_geometry_checks"] is False
    assert report["limitations"]


def test_mismatched_metadata_is_rejected(tmp_path: Path) -> None:
    clean = render_chart(str(FIXTURES), str(tmp_path / "clean"), build_function="clean_chart")
    bad = render_chart(
        str(FIXTURES), str(tmp_path / "bad"), build_function="annotation_over_line"
    )
    with pytest.raises(ValueError, match="hash does not match"):
        inspect_rendered_chart(clean["artifact"]["path"], bad["layout_metadata_path"])
