from __future__ import annotations

from pathlib import Path

from dataviz_mcp.comparison import compare_chart_artifacts
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import render_chart


FIXTURES = Path(__file__).parent / "fixtures" / "chart_fixtures.py"


def test_coffee_annotation_repair_loop_crosses_mechanical_pass_line(tmp_path: Path) -> None:
    bad_bundle = render_chart(
        str(FIXTURES), str(tmp_path / "coffee-bad"), build_function="coffee_bad"
    )
    bad = inspect_rendered_chart(
        bad_bundle["artifact"]["path"], bad_bundle["layout_metadata_path"]
    )
    assert bad["artifact"]["sha256"] == bad_bundle["artifact"]["sha256"]
    assert bad["passes_geometry_checks"] is False
    assert "ANNOTATION_SERIES_COLLISION" in {item["code"] for item in bad["defects"]}

    fixed_bundle = render_chart(
        str(FIXTURES), str(tmp_path / "coffee-fixed"), build_function="coffee_fixed"
    )
    fixed = inspect_rendered_chart(
        fixed_bundle["artifact"]["path"], fixed_bundle["layout_metadata_path"]
    )
    assert fixed["artifact"]["sha256"] == fixed_bundle["artifact"]["sha256"]
    assert fixed["passes_geometry_checks"] is True
    assert fixed["defects"] == []

    comparison = compare_chart_artifacts(
        bad["inspection_path"], fixed["inspection_path"]
    )
    assert comparison["mechanically_improved"] is True
    assert comparison["blocking_defect_count"]["after"] == 0
    assert comparison["introduced_defects"] == []
    assert comparison["passes_geometry_checks"] == {"before": False, "after": True}
