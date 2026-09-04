from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dataviz_mcp.server import create_server


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_stdio_server_exposes_renderer_probe_and_backend_neutral_workflow() -> None:
    server = create_server()
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {
        "render_chart",
        "render_and_inspect_chart",
        "probe_renderers",
        "inspect_rendered_chart",
        "refit_chart",
        "compare_chart_artifacts",
        "recommend_colours",
        "validate_palette",
        "extract_palette_from_image",
        "recommend_precision",
        "recommend_labels",
        "recommend_layout",
        "recommend_text_placement",
        "reserve_frame",
        "place_on_marks",
    }


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_all_capabilities_return_structured_results_through_mcp(tmp_path: Path) -> None:
    fixtures = Path(__file__).parent / "fixtures" / "chart_fixtures.py"

    async def exercise() -> None:
        server = create_server()
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


@pytest.mark.skipif(importlib.util.find_spec("mcp") is None, reason="MCP SDK not installed")
def test_installed_module_serves_tools_over_real_stdio(tmp_path: Path) -> None:
    script = """
import asyncio
import json
import os
import sys
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "dataviz_mcp"],
        env=os.environ.copy(),
        cwd=os.getcwd(),
    )
    async with Client(stdio_client(parameters)) as client:
        result = await client.list_tools()
        print(json.dumps(sorted(tool.name for tool in result.tools)))

asyncio.run(main())
"""
    environment = os.environ.copy()
    environment.setdefault("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)) == {
        "render_chart",
        "render_and_inspect_chart",
        "probe_renderers",
        "inspect_rendered_chart",
        "refit_chart",
        "compare_chart_artifacts",
        "recommend_colours",
        "validate_palette",
        "extract_palette_from_image",
        "recommend_precision",
        "recommend_labels",
        "recommend_layout",
        "recommend_text_placement",
        "reserve_frame",
        "place_on_marks",
    }
