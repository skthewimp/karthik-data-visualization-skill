from __future__ import annotations

from typing import Any

from .comparison import compare_chart_artifacts as compare_core
from .inspection import inspect_rendered_chart as inspect_core
from .palette import (
    extract_palette_from_image as extract_palette_core,
    recommend_colours as recommend_colours_core,
    validate_palette as validate_palette_core,
)
from .precision import recommend_precision as recommend_precision_core
from .rendering import (
    probe_renderers as probe_core,
    render_and_inspect_chart as render_inspect_core,
    render_chart as render_core,
)


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
    async def probe_renderers() -> dict[str, Any]:
        """Report renderer availability, versions, supported outputs, and failure reasons."""
        return probe_core()

    @server.tool()
    async def render_chart(
        source_path: str,
        output_dir: str,
        artifact_name: str = "chart.png",
        build_function: str = "build_chart",
        dpi: int | None = None,
    ) -> dict[str, Any]:
        """Render trusted local Matplotlib source and emit PNG, spec, layout, and manifest."""
        return render_core(source_path, output_dir, artifact_name, build_function, dpi)

    @server.tool()
    async def render_and_inspect_chart(
        source_path: str,
        output_dir: str,
        renderer: str = "auto",
        delivery_profile: str | None = "chat",
        dimensions: dict[str, Any] | None = None,
        artifact_name: str = "chart.png",
        build_function: str = "build_chart",
        content: str = "chart",
    ) -> dict[str, Any]:
        """Render backend-neutrally (ggplot2 first for auto), inspect, and build review views.

        Set content="table" to render a gtable (tableGrob / gt::as_gtable) from an .R
        source through the grid/ragg path and gate it like a chart.
        """
        return render_inspect_core(
            source_path,
            output_dir,
            renderer,
            delivery_profile,
            dimensions,
            artifact_name,
            build_function,
            content=content,
        )

    @server.tool()
    async def inspect_rendered_chart(
        artifact_path: str,
        layout_metadata_path: str | None = None,
        output_path: str | None = None,
        series_clearance_px: float = 2.0,
        max_unwrapped_annotation_chars: int = 45,
        delivery_profile: str | None = None,
        minimum_text_size_pt: float = 8.0,
    ) -> dict[str, Any]:
        """Inspect one exact raster using matching renderer geometry when supplied."""
        return inspect_core(
            artifact_path,
            layout_metadata_path,
            output_path,
            series_clearance_px,
            max_unwrapped_annotation_chars,
            delivery_profile,
            minimum_text_size_pt,
        )

    @server.tool()
    async def compare_chart_artifacts(
        before_inspection_path: str,
        after_inspection_path: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Compare two exact inspection reports and list resolved or introduced defects."""
        return compare_core(before_inspection_path, after_inspection_path, output_path)

    @server.tool()
    async def recommend_colours(
        available: list[str] | None,
        n_series: int,
        background: str = "#FFFFFF",
        focal: str | None = None,
    ) -> dict[str, Any]:
        """Pick and assign colours for one graph from an available set (brand/context/default).

        Chooses by max-min separation and background contrast, pins ``focal`` to series 0,
        and reports any shortfall with suggested additions. Use even when colours are given -
        a specific chart still needs a which-and-how-assigned decision.
        """
        return recommend_colours_core(available, n_series, background, focal)

    @server.tool()
    async def validate_palette(
        colours: list[str],
        background: str = "#FFFFFF",
        text_colours: list[str] | None = None,
        min_contrast_text: float = 4.5,
        min_contrast_mark: float = 3.0,
    ) -> dict[str, Any]:
        """Score a palette on WCAG contrast, series distinctness, CVD, and grayscale.

        Returns a verdict plus ranked findings, each with a concrete nudge. Targets are
        soft: findings are reported, not hard-blocked.
        """
        return validate_palette_core(
            colours,
            background=background,
            text_colours=text_colours,
            min_contrast_text=min_contrast_text,
            min_contrast_mark=min_contrast_mark,
        )

    @server.tool()
    async def extract_palette_from_image(
        image_path: str,
        max_colours: int = 8,
        ignore_near_white_black: bool = True,
    ) -> dict[str, Any]:
        """Sample dominant hues from a source chart image as a repair prior (brand/WCAG may override)."""
        return extract_palette_core(image_path, max_colours, ignore_near_white_black)

    @server.tool()
    async def recommend_precision(
        values: list[float],
        role: str = "axis",
        target_steps: int = 2,
        smallest_meaningful_difference: float | None = None,
        exact: bool = False,
    ) -> dict[str, Any]:
        """Recommend significant digits / a uniform rounding place for a numeric column.

        Precision is derived from the spread (max - min), not from individual values, and
        every value is rounded to one uniform place. Set ``role`` to axis/label/table_column.
        Set ``exact`` only for identifiers or a genuine exact-lookup requirement: it
        preserves every source digit and flags ``exact_override`` so the choice is never
        silent - record why the default spread rule was overridden.
        """
        return recommend_precision_core(
            values, role, target_steps, smallest_meaningful_difference, exact
        )

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
