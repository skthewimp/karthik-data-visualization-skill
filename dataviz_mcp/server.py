from __future__ import annotations

from typing import Any

from .comparison import compare_chart_artifacts as compare_core
from .inspection import inspect_rendered_chart as inspect_core
from .rendering import render_chart as render_core


def create_server() -> Any:
    """Create the stdio MCP server while keeping the core package SDK-independent."""
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "The MCP SDK is not installed. Install this project with its 'mcp' dependency."
        ) from exc

    server = MCPServer(
        "Karthik dataviz mechanical capabilities",
        instructions=(
            "Use these tools for deterministic rendering and exact-artifact geometry checks. "
            "Analytical and visual judgement remains in the dataviz skills."
        ),
    )

    @server.tool()
    def render_chart(
        source_path: str,
        output_dir: str,
        artifact_name: str = "chart.png",
        build_function: str = "build_chart",
        dpi: int | None = None,
    ) -> dict[str, Any]:
        """Render trusted local Matplotlib source and emit PNG, spec, layout, and manifest."""
        return render_core(source_path, output_dir, artifact_name, build_function, dpi)

    @server.tool()
    def inspect_rendered_chart(
        artifact_path: str,
        layout_metadata_path: str | None = None,
        output_path: str | None = None,
        series_clearance_px: float = 2.0,
        max_unwrapped_annotation_chars: int = 45,
    ) -> dict[str, Any]:
        """Inspect one exact raster using matching renderer geometry when supplied."""
        return inspect_core(
            artifact_path,
            layout_metadata_path,
            output_path,
            series_clearance_px,
            max_unwrapped_annotation_chars,
        )

    @server.tool()
    def compare_chart_artifacts(
        before_inspection_path: str,
        after_inspection_path: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Compare two exact inspection reports and list resolved or introduced defects."""
        return compare_core(before_inspection_path, after_inspection_path, output_path)

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
