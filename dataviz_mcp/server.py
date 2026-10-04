from __future__ import annotations

from typing import Any

from .mark_read import read_marks_from_anchors as read_marks_from_anchors_core
from .palette import recommend_colours as recommend_colours_core
from .precision import recommend_precision as recommend_precision_core
from .scale_transform import recommend_scale_transform as recommend_scale_transform_core


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
            "Use these tools for colour assignment, number precision, axis transforms, and "
            "reading values off a chart image. Analytical and visual judgement remains in "
            "the dataviz skills."
        ),
    )

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
