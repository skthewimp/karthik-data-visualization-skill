from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from dataviz_mcp.server import create_server


EXPECTED_TOOLS = {
    "render_and_inspect_chart",
    "probe_renderers",
    "inspect_rendered_chart",
    "refit_chart",
    "recommend_colours",
    "recommend_continuous_scale",
    "validate_palette",
    "validate_scale",
    "extract_palette_from_image",
    "recommend_precision",
    "read_marks_from_anchors",
    "recommend_scale_transform",
}


@pytest.mark.integration
@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_server_registers_every_tool_and_returns_structured_results(tmp_path: Path) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "chart_fixtures.py"

    async def exercise() -> None:
        server = create_server()
        # The registry is the public contract - every capability is exposed under its name.
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOLS

        rendered = await server.call_tool(
            "render_and_inspect_chart",
            {
                "source_path": str(fixtures),
                "output_dir": str(tmp_path / "clean_chart"),
                "renderer": "matplotlib",
                "build_function": "clean_chart",
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
        assert inspected.structured_content["passes_geometry_checks"] is True

    asyncio.run(exercise())
