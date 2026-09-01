from __future__ import annotations

from typing import Any

from .comparison import compare_chart_artifacts as compare_core
from .inspection import inspect_rendered_chart as inspect_core
from .labels import recommend_labels as recommend_labels_core
from .layout import recommend_layout as recommend_layout_core
from .text_fit import recommend_text_placement as recommend_text_placement_core
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
        semantic_hints: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Pick and assign colours for one graph from an available set (brand/context/default).

        Chooses by max-min separation and background contrast, pins ``focal`` to series 0,
        and reports any shortfall with suggested additions. Use even when colours are given -
        a specific chart still needs a which-and-how-assigned decision.

        Pass ``semantic_hints`` to bind series to a colour intent the model has judged
        appropriate: a list of ``{"series_index": i, "colour": "#hex"}`` (hard pin) or
        ``{"series_index": i, "hue_family": "blue"}`` (soft family - nearest in-family
        colour is used), each with an optional ``"alternates"`` list of away-kit colours or
        family words. Priority: series stay distinguishable (hard), meaning outranks
        contrast/CVD (a soft family may take a low-contrast in-family colour), and a home
        colour that clashes with a placed series moves to its first clearing away-kit - or,
        with none, is kept and flagged (``semantic_collision``), never silently reskinned.
        Unmet and collided hints are reported in ``semantic_findings``.
        """
        return recommend_colours_core(available, n_series, background, focal, semantic_hints)

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

    @server.tool()
    async def recommend_layout(
        x_slots: int = 0,
        y_slots: int = 0,
        filled_marks: bool = False,
        n_panels: int = 1,
        facet_scales: str = "fixed",
        n_direct_labels: int = 0,
        title_lines: int = 1,
        subtitle_lines: int = 0,
        footer_lines: int = 0,
        x_labels: bool = False,
        longest_x_label_chars: int = 0,
        delivery_profile: str = "chat",
    ) -> dict[str, Any]:
        """Size a clip-safe canvas (width/height/dpi), facet grid, and x-label rotation.

        Sizing is one rule over counts, not a table of chart types: each axis needs
        ``discrete_slots x per_slot_floor`` px; a continuous axis (0 slots) takes a pleasant
        aspect. ``y_slots`` grows height directly (labels stack); ``x_slots`` grows width and,
        when labels still won't fit, triggers rotation. Faceting multiplies via a grid. Set
        ``filled_marks`` for bar/tile/column slots. ``facet_scales`` takes the ggplot
        ``scales=`` value directly (fixed / free / free_x / free_y); a free y-axis reserves
        a per-panel band and the canonical value is echoed back. Overflow past the profile
        ceiling is warned, never squashed. Call at select, before build; feed the dims into the renderer
        and into ``recommend_text_placement``. It sizes the box, never picks the chart.
        """
        return recommend_layout_core(
            x_slots,
            y_slots,
            filled_marks,
            n_panels,
            facet_scales,
            n_direct_labels,
            title_lines,
            subtitle_lines,
            footer_lines,
            x_labels,
            longest_x_label_chars,
            delivery_profile,
        )

    @server.tool()
    async def recommend_labels(
        series: list[dict[str, Any]],
        max_labels_per_series: int = 4,
    ) -> dict[str, Any]:
        """Recommend which points on each series to label directly, within a budget.

        "Keep every visible value" means preserve every value in the data (table/note), not
        print every value as ink - stamping all of them collides and is unreadable. Pass one
        entry per series ``{id, values:[...]}`` in order; it claims endpoints and extremes
        first, then fills the budget with the largest step-to-step changes. Returns per-series
        ``label_indices`` and ``reasons``. It selects points, not placement - feed the chosen
        anchors to ``recommend_text_placement`` to wrap and de-collide them.
        """
        return recommend_labels_core(series, max_labels_per_series)

    @server.tool()
    async def recommend_text_placement(
        width_px: int,
        height_px: int,
        dpi: int,
        blocks: list[dict[str, Any]],
        obstacles: list[dict[str, Any]] | None = None,
        max_annotation_width_frac: float = 0.32,
        edge_margin_px: float | None = None,
        min_font_pt: float = 8.0,
    ) -> dict[str, Any]:
        """Wrap a chart's text to fit and move colliding annotations to the nearest clear spot.

        Call inside build after the title/subtitle/caption/annotations are written and the
        canvas is fixed. Each ``blocks`` item is ``{id, text, role, font_pt?, anchor:{x,y}}``
        in canvas px; title/subtitle/footer/caption are wrapped but never moved, annotations
        are movable. Role ``data_label`` is an on-mark label the plotting layer already centred
        on its mark (a stacked-bar segment value, a point label): wrapped, never moved, and
        exempt from obstacle de-collision - do NOT pass its own bar as an obstacle, or it will be
        shoved off the segment it belongs on. ``obstacles`` are the data marks' bounding boxes in
        canvas px - movable annotations are always de-collided against them, not only against
        other text. A movable block with
        no clear spot at full size is shrunk toward ``min_font_pt`` (the legibility floor) before
        the wrap is tightened. Returns each block's wrapped text, predicted bbox, and a moved
        ``suggested_anchor`` / smaller ``suggested_font_pt`` / tighter ``suggested_wrap`` where
        needed. A movable block that ends up off its original anchor also gets a ``leader_line``
        (``{from, to}`` in canvas px) to draw as a thin connector so the label still pairs with
        its mark. Plus a canvas-level ``suggested_orientation`` / ``suggested_canvas`` when a
        landscape canvas stays too cramped and a portrait flip would help. It fits the
        annotations already chosen; it invents none.
        """
        return recommend_text_placement_core(
            width_px,
            height_px,
            dpi,
            blocks,
            obstacles,
            max_annotation_width_frac,
            edge_margin_px,
            min_font_pt,
        )

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
