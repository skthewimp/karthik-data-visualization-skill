from __future__ import annotations

from pathlib import Path
from typing import Any

from .comparison import compare_chart_artifacts as compare_core
from .inspection import inspect_rendered_chart as inspect_core
from .palette import (
    extract_palette_from_image as extract_palette_core,
    recommend_colours as recommend_colours_core,
    recommend_continuous_scale as recommend_continuous_scale_core,
    validate_palette as validate_palette_core,
    validate_scale as validate_scale_core,
)
from .mark_read import read_marks_from_anchors as read_marks_from_anchors_core
from .precision import recommend_precision as recommend_precision_core
from .scale_transform import recommend_scale_transform as recommend_scale_transform_core
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
        inspection_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Render backend-neutrally (ggplot2 first for auto), inspect, and build review views.

        Set content="table" to render a gtable (tableGrob / gt::as_gtable) from an .R
        source through the grid/ragg path and gate it like a chart.
        The inspector compares text and measured bounds without inferring label roles or
        requiring ggplot text IDs.
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
            inspection_contract=inspection_contract,
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
        inspection_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Render, inspect, and grow the canvas in code until clipping/overflow/squash clears.

        Closes the render -> inspect -> resize loop deterministically, so a weak model never
        spends a model turn on pure geometry arithmetic. Each pass reads the exact overflow the
        inspector measured and grows the canvas by ``suggest_dims_for_overflow``'s amount, up to
        ``max_iterations``, honouring the delivery-profile ceiling (warned, never squashed) and
        stopping when a grow no longer reduces the residual. Scope is only what *growing* fixes -
        edge clipping, overflow, squashed panels; underfill (no exact shrink vector) is reported
        but never resized, and label collisions are left to the chart code. Returns the final
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
            inspection_contract=inspection_contract,
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
        display_width_px: float | None = None,
        minimum_text_size_px: float | None = None,
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
            display_width_px,
            minimum_text_size_px,
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
        available_source: str | None = None,
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

        Pass the colour plan's ``available_source``. Brand and prompt colours
        (``brand-skill``, ``prompt``) are used first, as supplied, and generation only covers
        a count shortage. Any other source (``source-extracted``, ``accessibility-default``, a
        proposed set) is a prior: a colour that cannot be told apart from a placed series
        (distinctness or CVD) or does not read on the background is replaced by a generated
        one that can.
        """
        return recommend_colours_core(
            available, n_series, background, focal, semantic_hints, available_source=available_source
        )

    @server.tool()
    async def recommend_continuous_scale(
        values: list[float],
        available: list[str] | None = None,
        background: str = "#FFFFFF",
        reference: float | None = None,
        kind: str = "auto",
    ) -> dict[str, Any]:
        """Recommend a CONTINUOUS colour scale for a magnitude encoding (heatmap fill,
        colour-mapped value) - NOT categorical series. Use this, not ``recommend_colours``,
        whenever colour encodes one ordered quantity; routing a magnitude through the
        categorical path collapses it to a single series colour and mis-validates the ramp.

        Returns the scale ``kind`` (sequential vs diverging), a data-derived ``domain`` and
        ``midpoint``, ordered ``stops`` to interpolate between, and a distinct off-scale
        ``missing_colour`` for NA cells. ``kind="auto"`` diverges only when the data has a
        real centre (an external ``reference`` or values straddling zero) and is otherwise
        sequential. ``kind="diverging"`` asserts that separating low/mid/high helps reading
        (e.g. a bounded-score heatmap); its midpoint is ``reference`` if given, else the data
        median - never a hardcoded constant. Poles are drawn from ``available`` (brand/context)
        when supplied, synthesised only when it is not. Pass the same list to ``validate_scale``.
        """
        return recommend_continuous_scale_core(
            values, available=available, background=background, reference=reference, kind=kind
        )

    @server.tool()
    async def validate_scale(
        stops: list[str],
        scale_kind: str = "sequential",
        background: str = "#FFFFFF",
        min_contrast_mark: float = 3.0,
    ) -> dict[str, Any]:
        """Validate a CONTINUOUS scale by its ends, not as categorical series.

        Checks that at least one stop reads on the background (mid values may fade into it)
        and that the two poles stay separated in lightness so the extremes survive grayscale
        and CVD. It deliberately does NOT flag interior stops for series-distinctness - a ramp
        is meant to have close neighbours. Use for heatmap/magnitude scales; use
        ``validate_palette`` for categorical series.
        """
        return validate_scale_core(
            stops, scale_kind=scale_kind, background=background, min_contrast_mark=min_contrast_mark
        )

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
        unit_multiplier: float = 1.0,
    ) -> dict[str, Any]:
        """Recommend significant digits / a uniform rounding place for a numeric column.

        Precision is derived from the spread (max - min), not from individual values, and
        every value is rounded to one uniform place. Set ``role`` to axis/label/table_column.
        Set ``exact`` only for identifiers or a genuine exact-lookup requirement: it
        preserves every source digit and flags ``exact_override`` so the choice is never
        silent - record why the default spread rule was overridden. Set ``unit_multiplier``
        when the column is already scaled (1e6 for "$MM"): each preview row's ``compact``
        form ("70.4B") is what a title, subtitle or annotation writes.
        """
        return recommend_precision_core(
            values, role, target_steps, smallest_meaningful_difference, exact, unit_multiplier
        )

    @server.tool()
    async def read_marks_from_anchors(
        marks: list[dict[str, Any]],
        transform: str = "linear",
    ) -> dict[str, Any]:
        """Interpolate bracketed chart-mark positions into values - the arithmetic half of a read.

        For an unlabelled cell, do not eyeball an absolute value. Name the two nearest printed
        ticks that bracket the mark and the ``fraction`` (0-1) between them, and let this tool
        interpolate. Each entry in ``marks`` is ``{key, lo, hi, fraction}`` where ``lo``/``hi`` are
        the bracketing tick VALUES; set ``transform`` to "log" for a log axis (interpolates in
        log10 space; anchors must be positive). A fraction just outside [0,1] is honoured as a
        short extrapolation (a series minimum below the lowest gridline, a peak above the top
        one), not clamped. Returns raw floats - rounding is a separate downstream decision
        (recommend_precision) - plus non-silent warnings for far-out fractions and unusable
        brackets.
        """
        return read_marks_from_anchors_core(marks, transform)

    @server.tool()
    async def recommend_scale_transform(
        values: list[float],
        encoding: str = "position",
    ) -> dict[str, Any]:
        """Recommend a linear vs log10 axis transform for a continuous axis - ADVISORY.

        A log axis earns its place when positive values span many orders of magnitude and
        a linear axis would saturate on the large values and crush the small ones, AND the
        marks encode position (points, lines, dots, box/violin) not length (bars/area, which
        need a true zero). Set ``encoding`` accordingly. Returns a graded ``strength`` and the
        ``transform`` scalar the builder branches on, plus signals, rationale, and caveats.

        The recommendation is one input to your decision, not a verdict: override it when the
        prompt wants absolute magnitudes, the audience won't read a log axis, or it would
        mislead - and record why. Log-only: with non-positive values log10 cannot apply and the
        tool says so (noting symlog/log1p exist) rather than recommending a substitute.
        """
        return recommend_scale_transform_core(values, encoding)

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
