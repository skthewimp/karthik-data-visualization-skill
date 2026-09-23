from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from dataviz_mcp.server import create_server


EXPECTED_TOOLS = {
    "render_chart",
    "render_and_inspect_chart",
    "probe_renderers",
    "inspect_rendered_chart",
    "refit_chart",
    "compare_chart_artifacts",
    "recommend_colours",
    "recommend_continuous_scale",
    "validate_palette",
    "validate_scale",
    "extract_palette_from_image",
    "prepare_plot_data",
    "recommend_precision",
    "read_marks_from_anchors",
    "recommend_scale_transform",
    "recommend_labels",
    "recommend_layout",
    "recommend_table_layout",
    "render_table_from_plan",
    "recommend_text_placement",
    "reserve_frame",
    "place_on_marks",
    "place_bar_value_labels",
    "scaffold_chart",
    "check_chart",
}


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_server_registers_every_tool_and_returns_structured_results(tmp_path: Path) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "chart_fixtures.py"

    async def exercise() -> None:
        server = create_server()
        # The registry is the public contract - every capability is exposed under its name.
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOLS

        inspections = []
        for function in ("annotation_over_line", "clean_chart"):
            rendered = await server.call_tool(
                "render_chart",
                {
                    "source_path": str(fixtures),
                    "output_dir": str(tmp_path / function),
                    "build_function": function,
                },
            )
            assert rendered.is_error is False
            bundle = rendered.structured_content
            inspected = await server.call_tool(
                "inspect_rendered_chart",
                {
                    "artifact_path": bundle["artifact"]["path"],
                    "layout_metadata_path": bundle["layout_metadata_path"],
                },
            )
            assert inspected.is_error is False
            inspections.append(inspected.structured_content)
        compared = await server.call_tool(
            "compare_chart_artifacts",
            {
                "before_inspection_path": inspections[0]["inspection_path"],
                "after_inspection_path": inspections[1]["inspection_path"],
            },
        )
        assert compared.is_error is False
        assert compared.structured_content["mechanically_improved"] is True

    asyncio.run(exercise())
