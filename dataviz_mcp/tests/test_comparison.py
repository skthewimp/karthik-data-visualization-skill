from __future__ import annotations

from pathlib import Path

from dataviz_mcp.comparison import compare_chart_artifacts
from dataviz_mcp.inspection import inspect_rendered_chart
from dataviz_mcp.rendering import render_chart


FIXTURES = Path(__file__).parent / "fixtures" / "chart_fixtures.py"


def test_comparison_reports_resolved_defect_without_judging_taste(tmp_path: Path) -> None:
    reports = []
    for function in ("annotation_over_line", "clean_chart"):
        bundle = render_chart(
            str(FIXTURES), str(tmp_path / function), build_function=function
        )
        reports.append(
            inspect_rendered_chart(
                bundle["artifact"]["path"], bundle["layout_metadata_path"]
            )
        )
    comparison = compare_chart_artifacts(
        reports[0]["inspection_path"], reports[1]["inspection_path"]
    )
    assert comparison["mechanically_improved"] is True
    assert comparison["introduced_defects"] == []
    assert {item["code"] for item in comparison["resolved_defects"]} == {
        "ANNOTATION_SERIES_COLLISION"
    }
    assert "mechanical changes only" in comparison["judgement_limit"]
    assert comparison["pixel_difference"]["changed_pixel_ratio"] > 0
