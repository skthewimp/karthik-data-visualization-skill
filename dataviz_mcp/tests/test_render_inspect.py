from __future__ import annotations

import json
from pathlib import Path

import pytest

from dataviz_mcp.artifacts import sha256_file
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import probe_renderers, render_and_inspect_chart, render_chart


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
        ("title_subtitle_collision", "HIERARCHY_TEXT_COLLISION"),
        ("low_contrast_annotation", "LOW_TEXT_CONTRAST"),
        ("label_over_bar", "TEXT_MARK_COLLISION"),
        ("incomplete_direct_labels", "DIRECT_LABELS_INCOMPLETE"),
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


def test_bar_marks_have_deterministic_collision_geometry(
    tmp_path: Path,
) -> None:
    _, report = render(tmp_path, "unsupported_bar_marks")
    assert report["checks_complete"] is True
    assert "non-line mark" not in " ".join(report["limitations"])


def test_probe_reports_versions_and_supported_outputs() -> None:
    probe = probe_renderers()
    assert probe["renderers"]["matplotlib"]["available"] is True
    assert probe["renderers"]["matplotlib"]["version"]
    assert probe["renderers"]["matplotlib"]["supported_output_types"] == ["png"]
    ggplot = probe["renderers"]["ggplot2"]
    assert isinstance(ggplot["failure_reasons"], list)
    if ggplot["available"]:
        assert ggplot["packages"]["ggplot2"]
        assert ggplot["packages"]["ragg"]


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_auto_renderer_prefers_ggplot2_and_emits_full_contract(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "ggplot_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot"),
        renderer="auto",
        delivery_profile="chat",
        dimensions={"width_px": 900, "height_px": 506, "dpi": 120},
    )
    assert bundle["renderer"] == "ggplot2"
    assert Path(bundle["inspection_path"]).is_file()
    assert len(bundle["review_view_paths"]) >= 3
    manifest = json.loads(Path(bundle["manifest_path"]).read_text())
    assert manifest["renderer_selection"]["selected"] == "ggplot2"
    assert manifest["renderer_selection"]["fallback_reason"] is None
    assert manifest["artifact"]["width"] == 900
    assert manifest["artifact"]["height"] == 506
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    inspection = json.loads(Path(bundle["inspection_path"]).read_text())
    assert len(layout["marks"]) == 3
    assert layout["plot_areas"][0]["bbox"]["width"] > 700
    assert inspection["checks_complete"] is True
    assert inspection["passes_geometry_checks"] is True


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_adapter_captures_every_panel_and_repeated_mark_structure(
    tmp_path: Path,
) -> None:
    source = Path(__file__).parent / "fixtures" / "ggplot_multipanel_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-panels"),
        dimensions={"width_px": 1000, "height_px": 500, "dpi": 120},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert len(layout["plot_areas"]) == 2
    assert {item["axes_id"] for item in layout["series"]} == {
        item["id"] for item in layout["plot_areas"]
    }
    assert len(layout["marks"]) == 6
    assert sum("panel-" in Path(path).name for path in bundle["review_view_paths"]) == 2


def test_auto_renderer_records_ggplot_fallback_for_python_source(tmp_path: Path) -> None:
    bundle = render_and_inspect_chart(
        str(FIXTURES),
        str(tmp_path / "python"),
        renderer="auto",
        build_function="clean_chart",
        dimensions={"width_px": 900, "height_px": 700, "dpi": 100},
    )
    assert bundle["renderer"] == "matplotlib"
    assert ".py source" in bundle["renderer_selection"]["fallback_reason"]


def test_backend_neutral_renderer_requires_caller_chosen_aspect_ratio(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="delivery profiles do not choose an aspect ratio"):
        render_and_inspect_chart(
            str(FIXTURES),
            str(tmp_path / "missing-dimensions"),
            renderer="auto",
            build_function="clean_chart",
            delivery_profile="chat",
        )


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
