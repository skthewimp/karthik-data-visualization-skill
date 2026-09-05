from __future__ import annotations

from typing import Any

from .comparison import compare_chart_artifacts as compare_core
from .inspection import inspect_rendered_chart as inspect_core
from .labels import recommend_labels as recommend_labels_core
from .frame import reserve_frame as reserve_frame_core
from .layout import recommend_layout as recommend_layout_core
from .text_fit import (
    place_on_marks as place_on_marks_core,
    recommend_text_placement as recommend_text_placement_core,
)
from .palette import (
    extract_palette_from_image as extract_palette_core,
    recommend_colours as recommend_colours_core,
    validate_palette as validate_palette_core,
)
from .precision import recommend_precision as recommend_precision_core
from .refit import refit_chart as refit_core
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
    async def refit_chart(
        source_path: str,
        output_dir: str,
        renderer: str = "auto",
        delivery_profile: str = "chat",
        dimensions: dict[str, Any] | None = None,
        max_iterations: int = 3,
        content: str = "chart",
        artifact_name: str = "chart.png",
        build_function: str = "build_chart",
    ) -> dict[str, Any]:
        """Render, inspect, and grow the canvas in code until clipping/overflow/squash clears.

        Closes the render -> inspect -> resize loop deterministically, so a weak model never
        spends a model turn on pure geometry arithmetic. Each pass reads the exact overflow the
        inspector measured and grows the canvas by ``suggest_dims_for_overflow``'s amount, up to
        ``max_iterations``, honouring the delivery-profile ceiling (warned, never squashed) and
        stopping when a grow no longer reduces the residual. Scope is only what *growing* fixes -
        edge clipping, overflow, squashed panels; underfill (no exact shrink vector) is reported
        but never resized, and label collisions stay ``place_on_marks``' job. Returns the final
        artifact, inspection path, ``final_dimensions``, a per-pass ``history``, ``warnings``, a
        ``resolved`` flag, and ``underfilled``. Run it FIRST at the execution gate, then escalate
        only the residual (non-resize) defects to a model revision.
        """
        return refit_core(
            source_path,
            output_dir,
            renderer,
            delivery_profile,
            dimensions,
            max_iterations,
            content,
            artifact_name,
            build_function,
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

        Returns one distinct colour per series (the hard constraint), pinning ``focal`` to
        series 0. Selection is lexicographic: contrast WITH THE BACKGROUND first (a colour
        must read against the background - this outranks separation from other series), then
        diversity (farthest-first), then higher contrast as tiebreak. Contrast is soft:
        colours are never dropped for it, only spent last. The default pool is Okabe-Ito,
        extended with vetted Paul Tol hues past eight series - and these named palettes are
        recommendations, not a ceiling: a genuine shortage (more series than distinct pool
        colours) is topped up with algorithmically generated background-aware colours
        (``generated_additions``) so the count is always met. Use even when colours are given.
        ``resolved`` is false only in the pathological case where even generation cannot clear
        the background bar; then ``route_to`` is "select" - change the background or drop a
        series.

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
    async def reserve_frame(
        title: str = "",
        subtitle: str = "",
        caption: str = "",
        footer: str = "",
        x_axis_title: str = "",
        y_axis_title: str = "",
        longest_x_tick: str = "",
        longest_y_tick: str = "",
        legend_side: str = "none",
        longest_legend_label: str = "",
        width_px: int | None = None,
        height_px: int | None = None,
        dpi: int | None = None,
        delivery_profile: str = "chat",
        font_pt: dict[str, float] | None = None,
        edge_margin_px: float | None = None,
    ) -> dict[str, Any]:
        """Reserve the frame (title/subtitle/caption/footer/axes/legend) blind, before any draw.

        Chart chrome lives in the margins; its position does not depend on the data, so it is
        placed with text-measuring arithmetic - wrap each block to the canvas width, count the
        lines, reserve a pixel band - with no render. Returns the plot rectangle the marks may
        fill, so the title never clips and the canvas never sits half-empty, without a revision
        loop. Canvas size, dpi, and per-role font sizes are all inputs (``font_pt`` overrides
        the house sizes, e.g. ``{"title": 20}``); a frame too big for the canvas is warned,
        never squashed. Call at build, before the first render; feed ``plot_area`` to the
        renderer and pass ``frame_blocks`` on to ``place_on_marks`` as fixed obstacles.
        """
        return reserve_frame_core(
            title,
            subtitle,
            caption,
            footer,
            x_axis_title,
            y_axis_title,
            longest_x_tick,
            longest_y_tick,
            legend_side,
            longest_legend_label,
            width_px,
            height_px,
            dpi,
            delivery_profile,
            font_pt,
            edge_margin_px,
        )

    @server.tool()
    async def place_on_marks(
        width_px: int,
        height_px: int,
        dpi: int,
        transform: list[list[float]],
        labels: list[dict[str, Any]],
        marks: list[dict[str, Any]] | None = None,
        fixed_blocks: list[dict[str, Any]] | None = None,
        x_trans: str = "identity",
        y_trans: str = "identity",
        max_annotation_width_frac: float = 0.32,
        edge_margin_px: float | None = None,
        min_font_pt: float = 8.0,
        plot_area: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Place labels glued to data marks using their real pixel positions, not a guess.

        After one measure render, the layout metadata carries the exact ``data_to_pixel``
        transform and every mark's bounding box. This projects each label's ``(data_x,
        data_y)`` through that transform, hands the marks in as obstacles, and delegates to
        ``recommend_text_placement`` - so on-mark and category labels are de-collided against
        where the marks actually landed, killing text-mark and text-text overlaps on the first
        delivered chart instead of after a revision loop. Pass ``transform`` and ``marks``
        straight from the render's layout metadata, and ``fixed_blocks`` from ``reserve_frame``
        so labels also clear the title. When the transform entry carries ``x_trans`` / ``y_trans``
        (a log/sqrt/reverse ggplot axis), pass them through so the data coords are transformed
        before the affine. Canvas size, dpi, and per-block ``font_pt`` are inputs.

        Pass ``plot_area`` (the panel rectangle from ``reserve_frame``) to correct a movable label
        left straddling the plot boundary - a clip canvas growth cannot fix. Every movable label
        comes back with native data coordinates (``placed_data``, ``anchor_data``, and
        ``leader_line_data`` when a leader is drawn) so the builder draws leaders and label
        positions from exact coordinates instead of improvising a ``geom_segment`` that may run
        through a neighbour. The leader terminates at the label's bounding-box edge and the mark.
        """
        return place_on_marks_core(
            width_px,
            height_px,
            dpi,
            transform,
            labels,
            marks,
            fixed_blocks,
            x_trans=x_trans,
            y_trans=y_trans,
            max_annotation_width_frac=max_annotation_width_frac,
            edge_margin_px=edge_margin_px,
            min_font_pt=min_font_pt,
            plot_area=plot_area,
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
        plot_area: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Wrap a chart's text to fit and park each movable label beside the mark it names.

        Call inside build after the title/subtitle/caption/labels/annotations are written and the
        canvas is fixed. Each ``blocks`` item is
        ``{id, text, role, font_pt?, anchor:{x,y}, placement?, anchors?}`` in canvas px. Text is
        placed in priority order so the least-free claims its spot first: data labels, then
        category/series labels, then free annotations. title/subtitle/footer/caption sit at their
        anchor, wrapped, never moved. Role ``axis_label`` is a plotting-layer-positioned tick or
        category label: wrapped, never moved. Role ``data_label`` is a value the plotting layer has
        already positioned on its mark or at a deliberate fixed offset from it: wrapped, never
        moved, and exempt from obstacle de-collision - do NOT pass its own mark as an obstacle, or
        it will be shoved away from the placement it belongs on. Role ``label`` (a category/series
        name) and ``annotation``
        (a free callout) are movable, and their ``anchor`` is the MARK they name: the box parks one
        small gap beside the mark - preferred side first (``placement`` = right/above/below/left,
        default right) - with no leader line. A ``label`` may pass ``anchors``, a list of candidate
        marks (e.g. several points along its line); it sits beside whichever is clear, since
        adjacency identifies the series, not the endpoint. ``obstacles`` are the data marks'
        bounding boxes in canvas px - movable labels are always parked clear of them, not only of
        other text. Only when no adjacent spot exists at any of a label's marks does it travel to
        the nearest clear area (shrinking toward ``min_font_pt``, the legibility floor, if needed)
        and grow a ``leader_line`` (``{from, to}`` in canvas px) back to its point. Series/category
        and on-mark data labels, plus axis labels, must carry the builder's judgment as
        ``max_width_px`` and ``max_lines`` on the block. Set ``allow_curtail: true`` only when an
        ellipsis is acceptable and the intact name will appear in a key or footnote; otherwise an
        over-budget label stays intact and is reported for redesign. Returns each
        block's wrapped text and final ``bbox`` (authoritative - the anchor was the mark), plus
        ``suggested_anchor`` / ``suggested_font_pt`` / ``suggested_wrap`` when it changed side, mark,
        or size. A label parked on its preferred side has none of those and no leader. When two
        moved labels land on each other's side so their leaders cross, they are swapped back toward
        their own marks whenever the swap stays clear of every mark and label. A top-level
        ``redundant_annotations`` list flags any free annotation whose one data value a nearby
        ``data_label`` already prints (a "Peak: 42%" beside a mark already labelled 42%) and
        recommends dropping it - the value is on the chart twice; a comparison naming two values or
        a delta whose number is on no label is never flagged. Plus a canvas-level
        ``suggested_orientation`` / ``suggested_canvas`` when a landscape canvas stays too cramped
        and a portrait flip would help. It fits the labels already chosen; it invents none. Pass
        ``plot_area`` (the panel rectangle from ``reserve_frame``) to correct a movable label left
        straddling the plot boundary; the label carries the exact ``plot_boundary_correction``
        ``{dx, dy}`` applied.
        """
        return recommend_text_placement_core(
            width_px,
            height_px,
            dpi,
            blocks,
            obstacles,
            max_annotation_width_frac=max_annotation_width_frac,
            edge_margin_px=edge_margin_px,
            min_font_pt=min_font_pt,
            plot_area=plot_area,
        )

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
