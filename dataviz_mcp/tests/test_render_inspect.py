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


def test_data_label_on_its_mark_is_not_a_collision(tmp_path: Path) -> None:
    # Same geometry as label_over_bar, but the text is a data_label on the bar it names. A value on
    # its own mark is not an accidental overlap, so it must not fire TEXT_MARK_COLLISION.
    _, report = render(tmp_path, "data_label_on_bar")
    assert "TEXT_MARK_COLLISION" not in {item["code"] for item in report["defects"]}


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
def test_ggplot_value_labels_on_marks_are_data_labels_not_collisions(tmp_path: Path) -> None:
    # ggplot cannot gid a geom_text value label as data_label, so the adapter tags in-panel data
    # text as data_label by construction. It must be exempt from the text-mark collision check even
    # when it sits on its bar, not flagged as an accidental overlap.
    source = Path(__file__).parent / "fixtures" / "ggplot_value_labels_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-values"),
        renderer="ggplot2",
        dimensions={"width_px": 800, "height_px": 500, "dpi": 144},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    inspection = json.loads(Path(bundle["inspection_path"]).read_text())
    data_labels = [e for e in layout["elements"] if e.get("role") == "data_label"]
    assert len(data_labels) == 4, [e["role"] for e in layout["elements"]]
    assert "TEXT_MARK_COLLISION" not in {d["code"] for d in inspection["defects"]}


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_vertical_bars_share_a_baseline_and_are_centred(tmp_path: Path) -> None:
    # Regression: ggplot's GeomRect anchors each bar at (xmin, ymax) with
    # just=c("left","top"). The adapter once treated that anchor as the box centre and
    # subtracted half the size, shoving each bar up by half its height (so taller bars
    # drifted higher and the tallest reported a negative top) and left by half its width.
    source = Path(__file__).parent / "fixtures" / "ggplot_bar_baseline_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-bars"),
        renderer="ggplot2",
        dimensions={"width_px": 800, "height_px": 500, "dpi": 144},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    bars = sorted(
        (m["bbox"] for m in layout["marks"] if m.get("kind") == "rect"),
        key=lambda b: b["x"],
    )
    assert len(bars) == 4
    # Every bar sits on the canvas, no negative tops.
    assert all(b["y"] >= 0 for b in bars)
    # All four share one bottom baseline (bottom = y + height).
    bottoms = [b["y"] + b["height"] for b in bars]
    assert max(bottoms) - min(bottoms) <= 3, bottoms
    # Heights track the data (10, 40, 25, 60): B and D are the tall ones.
    heights = [b["height"] for b in bars]
    assert heights[3] > heights[1] > heights[2] > heights[0]
    # Bars are evenly spaced across the panel (centres roughly equidistant).
    centres = [b["x"] + b["width"] / 2 for b in bars]
    gaps = [centres[i + 1] - centres[i] for i in range(3)]
    assert max(gaps) - min(gaps) <= 3, gaps


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_emits_a_data_to_pixel_transform_that_lands_on_a_bar(tmp_path: Path) -> None:
    # place_on_marks on R: a single-panel CoordCartesian plot emits a linear affine, and
    # projecting a bar's data coords through it must land on that bar's captured box.
    source = Path(__file__).parent / "fixtures" / "ggplot_bar_baseline_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-tf"),
        renderer="ggplot2",
        dimensions={"width_px": 800, "height_px": 500, "dpi": 144},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert layout["transforms"], "expected a data->pixel transform for a cartesian plot"
    t = layout["transforms"][0]["data_to_pixel_top_left"]
    # Categories A..D sit at positions 1..4; D is the tallest at value 60.
    px = t[0][0] * 4 + t[0][1] * 60 + t[0][2]
    py = t[1][0] * 4 + t[1][1] * 60 + t[1][2]
    bars = sorted(
        (m["bbox"] for m in layout["marks"] if m.get("kind") == "rect"),
        key=lambda b: b["x"],
    )
    tallest = bars[3]
    assert abs(px - (tallest["x"] + tallest["width"] / 2)) <= 3
    assert abs(py - tallest["y"]) <= 3


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_coord_flip_transform_is_cross_termed_and_lands_on_a_bar(tmp_path: Path) -> None:
    # Under coord_flip the value aesthetic drives the horizontal axis and the category the
    # vertical, so the affine carries cross terms (px depends on data_y, py on data_x). The
    # fixture returns list(plot=, metadata=), which must still yield a transform.
    source = Path(__file__).parent / "fixtures" / "ggplot_fixture.R"  # coord_flip, list(plot=)
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-flip"),
        renderer="ggplot2",
        dimensions={"width_px": 900, "height_px": 506, "dpi": 120},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert layout["transforms"], "coord_flip on a cartesian plot should emit a transform"
    t = layout["transforms"][0]["data_to_pixel_top_left"]
    # cross-termed: px reads y (t[0][1] != 0), py reads x (t[1][0] != 0); diagonal ~0.
    assert abs(t[0][0]) < 1e-6 and abs(t[1][1]) < 1e-6
    assert abs(t[0][1]) > 1e-6 and abs(t[1][0]) > 1e-6
    # categories C,B,A at levels -> value 7 is the longest bar; project (its position, 7).
    bars = sorted(
        (m["bbox"] for m in layout["marks"] if m.get("kind") == "rect"),
        key=lambda b: b["width"],
    )
    longest = bars[-1]  # value 7 bar
    # find its category position by matching the projected vertical to the bar's mid-y
    best = None
    for pos in (1, 2, 3):
        py = t[1][0] * pos + t[1][1] * 7 + t[1][2]
        px = t[0][0] * pos + t[0][1] * 7 + t[0][2]
        err = abs(py - (longest["y"] + longest["height"] / 2)) + abs(
            px - (longest["x"] + longest["width"])
        )
        best = err if best is None else min(best, err)
    assert best <= 4, best


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_log_scale_carries_its_transform_and_projects_onto_a_point(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "ggplot_log_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-log"),
        renderer="ggplot2",
        dimensions={"width_px": 800, "height_px": 500, "dpi": 144},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert layout["transforms"], "expected a transform for a log-scaled cartesian plot"
    entry = layout["transforms"][0]
    assert entry["x_trans"] == "identity"
    assert entry["y_trans"] in ("log-10", "log10")
    t = entry["data_to_pixel_top_left"]
    # Project the top point (x=4, y=2000): y must be log10'd before the affine.
    import math

    px = t[0][0] * 4 + t[0][1] * math.log10(2000) + t[0][2]
    py = t[1][0] * 4 + t[1][1] * math.log10(2000) + t[1][2]
    points = [m["bbox"] for m in layout["marks"]]
    rightmost = max(points, key=lambda b: b["x"] + b["width"] / 2)
    assert abs(px - (rightmost["x"] + rightmost["width"] / 2)) <= 3
    assert abs(py - (rightmost["y"] + rightmost["height"] / 2)) <= 3


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_ggplot_facets_emit_one_transform_per_panel_keyed_to_marks(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "ggplot_facet_free_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "ggplot-facets"),
        renderer="ggplot2",
        dimensions={"width_px": 1000, "height_px": 500, "dpi": 144},
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    # Three panels -> three transforms, each keyed to a panel that holds marks.
    assert len(layout["transforms"]) == 3
    tf_axes = {t["axes_id"] for t in layout["transforms"]}
    mark_axes = {m["axes_id"] for m in layout["marks"]}
    assert tf_axes == mark_axes
    # Free scales -> the panels' affines differ (distinct x offsets).
    offsets = {round(t["data_to_pixel_top_left"][0][2]) for t in layout["transforms"]}
    assert len(offsets) == 3


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


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_guide_none_does_not_emit_phantom_panel_legend(tmp_path: Path) -> None:
    # Regression: ggplot >= 3.5 lays out a guide-box-inside cell spanning the whole
    # panel. With guide="none" it holds a zeroGrob, but the adapter used to emit it as a
    # panel-sized legend, so every in-panel direct label registered a false legend
    # collision and passes_geometry_checks came back false.
    source = Path(__file__).parent / "fixtures" / "ggplot_noguide_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "noguide"),
        renderer="auto",
    )
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    inspection = json.loads(Path(bundle["inspection_path"]).read_text())
    assert layout["legends"] == []
    assert inspection["legend_collisions"] == []
    assert inspection["checks_complete"] is True
    assert inspection["passes_geometry_checks"] is True


def test_auto_renderer_records_ggplot_fallback_for_python_source(tmp_path: Path) -> None:
    bundle = render_and_inspect_chart(
        str(FIXTURES),
        str(tmp_path / "python"),
        renderer="auto",
        build_function="clean_chart",
        dimensions={"dpi": 100},
    )
    assert bundle["renderer"] == "matplotlib"
    assert ".py source" in bundle["renderer_selection"]["fallback_reason"]


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


def test_probe_reports_table_rendering_capability() -> None:
    probe = probe_renderers()
    table = probe["table_rendering"]
    assert table["backend"] == "grid/gtable via ragg"
    assert isinstance(table["failure_reasons"], list)
    assert table["available"] == probe["renderers"]["ggplot2"]["available"]


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_table_content_renders_and_captures_every_cell(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "table_fixture.R"
    bundle = render_and_inspect_chart(
        str(source),
        str(tmp_path / "table"),
        content="table",
        build_function="build_table",
    )
    assert bundle["content"] == "table"
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text(encoding="utf-8"))
    assert layout["coverage"]["table_cell_bounds"] is True
    texts = {element["text"] for element in layout["elements"]}
    # every header and body cell is captured with its text
    for expected in ("Region", "Revenue", "Share", "North", "12.5", "42%"):
        assert expected in texts
    # cell font sizes are recovered from the gtable grobs
    assert any(element.get("font_size_pt") for element in layout["elements"])
    manifest = json.loads(Path(bundle["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["content"] == "table"
    assert manifest["renderer"] == "gt-table"


def test_table_content_rejects_non_r_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="table content requires an .R source"):
        render_and_inspect_chart(
            str(FIXTURES),
            str(tmp_path / "bad-table"),
            content="table",
        )


def _codes(report: dict) -> set:
    return {defect["code"] for defect in report["defects"]}


def _emitted_codes() -> set:
    """Every defect code the module can emit, read straight from its source, so a new code that
    forgets a correction class is caught here rather than defaulting silently."""
    import ast

    source = (Path(inspect_rendered_chart.__code__.co_filename)).read_text()
    codes = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if v.isupper() and "_" in v and len(v) > 4:
                codes.add(v)
    return codes


def test_every_emitted_defect_code_has_a_correction_class() -> None:
    from dataviz_mcp.inspection import _DEFECT_CLASS

    unmapped = _emitted_codes() - set(_DEFECT_CLASS)
    assert not unmapped, f"defect codes missing a correction class: {sorted(unmapped)}"
    assert set(_DEFECT_CLASS.values()) <= {"canvas", "placement", "semantic"}


def test_defects_carry_their_class_and_the_report_routes_them(tmp_path: Path) -> None:
    _, report = render(tmp_path, "annotation_outside_canvas")
    # A canvas-edge overflow classifies as canvas and rides a real growth vector.
    oob = next(item for item in report["defects"] if item["code"] == "OUT_OF_BOUNDS")
    assert oob["defect_class"] == "canvas"
    plan = report["correction_plan"]
    assert set(plan) == {"canvas", "placement", "semantic"}
    assert oob in plan["canvas"]["defects"]
    # The canvas group's growth vector mirrors the geometry summary's, so refit reads one number.
    assert plan["canvas"]["growth_vector"] == report["geometry_summary"]["suggested_dims"]
    assert plan["canvas"]["growth_vector"] is not None


def test_placement_defect_routes_to_the_placement_group(tmp_path: Path) -> None:
    _, report = render(tmp_path, "two_annotations_overlap")
    plan = report["correction_plan"]
    placement_codes = {d["code"] for d in plan["placement"]["defects"]}
    assert "LABEL_LABEL_COLLISION" in placement_codes
    assert all(d["defect_class"] == "placement" for d in plan["placement"]["defects"])


def test_clean_chart_has_an_empty_correction_plan(tmp_path: Path) -> None:
    _, report = render(tmp_path, "clean_chart")
    plan = report["correction_plan"]
    assert plan["canvas"]["defects"] == []
    assert plan["placement"]["defects"] == []
    assert plan["semantic"]["defects"] == []
    assert plan["canvas"]["growth_vector"] is None


def test_redundant_value_axis_flagged_when_every_mark_is_labelled(tmp_path: Path) -> None:
    _, report = render(tmp_path, "all_marks_labelled")
    assert "REDUNDANT_VALUE_AXIS" in _codes(report)
    assert report["redundant_value_axis"]
    defect = next(item for item in report["defects"] if item["code"] == "REDUNDANT_VALUE_AXIS")
    assert defect["severity"] == "medium"
    assert report["passes_geometry_checks"] is False


def test_redundant_value_axis_flagged_per_panel_without_a_contract(tmp_path: Path) -> None:
    # A faceted chart that labels every bar but declares no inspection_contract must still flag
    # the redundant value axis, per panel, from geometry alone.
    _, report = render(tmp_path, "faceted_bars_all_labelled")
    assert "REDUNDANT_VALUE_AXIS" in _codes(report)
    assert report["redundant_value_axis"]
    defect = next(item for item in report["defects"] if item["code"] == "REDUNDANT_VALUE_AXIS")
    assert defect["severity"] == "medium"
    assert report["passes_geometry_checks"] is False


def test_redundant_value_axis_flagged_when_marks_are_labelled(tmp_path: Path) -> None:
    # Four of five bars labelled, no inspection_contract: the geometry fallback must flag the
    # redundant value axis without requiring every mark.
    _, report = render(tmp_path, "bars_mostly_labelled")
    assert "REDUNDANT_VALUE_AXIS" in _codes(report)
    assert report["redundant_value_axis"]
    defect = next(item for item in report["defects"] if item["code"] == "REDUNDANT_VALUE_AXIS")
    assert defect["severity"] == "medium"
    assert report["passes_geometry_checks"] is False


def test_redundant_value_axis_flagged_at_two_labelled_marks(tmp_path: Path) -> None:
    # Exactly two of five bars labelled: two labels fix the linear scale, so the flag must fire
    # even though most marks are unlabelled.
    _, report = render(tmp_path, "bars_two_labelled")
    assert "REDUNDANT_VALUE_AXIS" in _codes(report)
    assert report["redundant_value_axis"]


def test_no_redundant_axis_when_one_mark_labelled(tmp_path: Path) -> None:
    # One of five bars labelled: a single label cannot fix the scale, so the flag must stay silent.
    _, report = render(tmp_path, "bars_few_labelled")
    assert "REDUNDANT_VALUE_AXIS" not in _codes(report)
    assert report["redundant_value_axis"] == []


def test_no_redundant_axis_without_direct_labels(tmp_path: Path) -> None:
    _, report = render(tmp_path, "clean_chart")
    assert "REDUNDANT_VALUE_AXIS" not in _codes(report)
    assert report["redundant_value_axis"] == []


def test_one_series_per_facet_flags_colour_and_legend(tmp_path: Path) -> None:
    _, report = render(tmp_path, "coloured_facets_with_legend")
    codes = _codes(report)
    assert "REDUNDANT_COLOUR" in codes
    assert "EXTERNAL_LEGEND" in codes
    assert report["redundant_colour"] and report["external_legend"]
    # Eraser-test suggestions, never blocking.
    assert all(
        item["severity"] == "low"
        for item in report["defects"]
        if item["code"] in {"REDUNDANT_COLOUR", "EXTERNAL_LEGEND"}
    )


def test_rainbow_bars_flag_colour_and_legend(tmp_path: Path) -> None:
    _, report = render(tmp_path, "rainbow_bars_with_legend")
    codes = _codes(report)
    assert "REDUNDANT_COLOUR" in codes
    assert "EXTERNAL_LEGEND" in codes


def test_focal_highlight_keeps_colour_and_stays_silent(tmp_path: Path) -> None:
    _, report = render(tmp_path, "focal_bar_highlight")
    codes = _codes(report)
    assert "REDUNDANT_COLOUR" not in codes
    assert "EXTERNAL_LEGEND" not in codes


def test_clean_chart_has_no_colour_or_legend_flags(tmp_path: Path) -> None:
    _, report = render(tmp_path, "clean_chart")
    codes = _codes(report)
    assert "REDUNDANT_COLOUR" not in codes
    assert "EXTERNAL_LEGEND" not in codes


@pytest.mark.skipif(
    not probe_renderers()["renderers"]["ggplot2"]["available"],
    reason="ggplot2+ragg not installed",
)
def test_nested_table_text_and_incomplete_viewports(tmp_path: Path) -> None:
    source = tmp_path / "nested.R"
    source.write_text('''library(grid)
library(gtable)
build_table <- function() {
  children <- gTree(gp=gpar(fontsize=6), children=gList(
    textGrob("Inherited small", x=.25, y=.6),
    textGrob("Own small", x=.75, y=.4, gp=gpar(fontsize=7))))
  gtable_matrix("nested", matrix(list(children),1),
    widths=unit(5,"in"), heights=unit(2,"in"))
}
''')
    bundle = render_and_inspect_chart(str(source), str(tmp_path / "nested"),
                                    content="table", build_function="build_table")
    layout = json.loads(Path(bundle["layout_metadata_path"]).read_text())
    assert {e["font_size_pt"] for e in layout["elements"]} == {6, 7}
    assert layout["coverage"]["text_bounds"]
    assert not layout["coverage"]["table_cell_bounds"]
    report = inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"])
    assert len(report["undersized_text"]) == 2
    assert not report["passes_geometry_checks"]
    report = inspect_rendered_chart(bundle["artifact"]["path"], bundle["layout_metadata_path"],
        minimum_text_size_pt=5, display_width_px=200, minimum_text_size_px=16)
    assert len(report["undersized_text"]) == 2
    # A valid drawing with a named child viewport is not silently certified.
    source.write_text(source.read_text().replace(
        'gTree(gp=gpar(fontsize=6), children=gList(',
        'gTree(childrenvp=viewport(name="inner"), gp=gpar(fontsize=6), children=gList(').replace(
        'textGrob("Inherited small", x=.25, y=.6)',
        'textGrob("Inherited small", x=.25, y=.6, vp="inner")'))
    partial = render_and_inspect_chart(str(source), str(tmp_path / "partial"),
                                      content="table", build_function="build_table")
    report = inspect_rendered_chart(partial["artifact"]["path"], partial["layout_metadata_path"], minimum_text_size_pt=5)
    assert not report["checks_complete"]
