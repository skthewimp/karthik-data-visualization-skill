from __future__ import annotations

import asyncio
import importlib.util

import pytest

from dataviz_mcp.server import create_server


EXPECTED_TOOLS = {
    "recommend_colours",
    "recommend_precision",
    "read_marks_from_anchors",
    "recommend_scale_transform",
}


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_server_registers_every_tool_and_returns_structured_results() -> None:
    async def exercise() -> None:
        server = create_server()
        # The registry is the public contract - every capability is exposed under its name.
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == EXPECTED_TOOLS

        coloured = await server.call_tool("recommend_colours", {"available": None, "n_series": 3})
        assert coloured.is_error is False
        assert len(coloured.structured_content["ordered_palette"]) == 3

    asyncio.run(exercise())
