"""Close the render -> inspect -> resize loop in code, so a weak model never spends a
model turn on pure geometry arithmetic.

When a first render clips the canvas edge or squashes its facet panels, the fix is not a
judgement call - the inspector already reports the exact overflow in pixels, and
``suggest_dims_for_overflow`` already turns that into a grown canvas. ``refit_chart`` runs
that loop: render, inspect, and while a *resize-fixable* defect remains, grow the canvas by
the measured amount and re-render - up to a budget, honouring the delivery-profile ceiling,
and guarding against a loop that stops improving.

Scope: refit only fixes what *growing* fixes - edge clipping, overflow, squashed panels -
because those carry an exact read-back px vector. Underfill (a canvas too empty for its ink)
has no exact shrink vector - clearing it is a design call (denser layout, bigger marks, or a
table), so refit *detects and reports* it but never guesses a shrink. Label-vs-label and
label-vs-mark collisions are ``place_on_marks``' job; refit does not touch them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import read_json
from .layout import MIN_PANEL_H, PROFILES
from .rendering import render_and_inspect_chart

_DIM_KEYS = ("width_px", "height_px", "dpi")


def _grow_residual(geometry_summary: dict[str, Any]) -> float:
    """Total px a resize must add to clear the render: overflow on every edge plus any
    squashed-panel deficit. Zero means nothing is growable - the exact read-back scalar that
    ``suggest_dims_for_overflow`` grows the canvas by, so it falls monotonically as refit works.
    """
    edge = geometry_summary.get("edge_overflow_px") or {}
    overflow = sum(max(0.0, float(value)) for value in edge.values())
    squash = 0.0
    min_panel = geometry_summary.get("min_panel_height_px")
    if geometry_summary.get("panels_squashed") and min_panel is not None:
        squash = max(0.0, MIN_PANEL_H - float(min_panel))
    return round(overflow + squash, 2)


def _propose_dims(
    geometry_summary: dict[str, Any],
    dims: dict[str, int],
    max_w: float,
    max_h: float,
) -> dict[str, int]:
    """The grown canvas to render next: ``suggested_dims`` from the inspection, clamped to the
    delivery ceiling but never below the current size (an explicit oversize start is respected).
    """
    suggested = geometry_summary.get("suggested_dims")
    if not suggested:
        return dict(dims)
    new_w = min(
        max(int(suggested["suggested_width_px"]), dims["width_px"]),
        max(int(max_w), dims["width_px"]),
    )
    new_h = min(
        max(int(suggested["suggested_height_px"]), dims["height_px"]),
        max(int(max_h), dims["height_px"]),
    )
    return {"width_px": new_w, "height_px": new_h, "dpi": dims["dpi"]}


def _starting_dims(
    delivery_profile: str, dimensions: dict[str, Any] | None
) -> dict[str, int]:
    profile = PROFILES.get(delivery_profile, PROFILES["chat"])
    dims = {key: int(profile[key]) for key in _DIM_KEYS}
    if dimensions:
        dims.update({key: int(value) for key, value in dimensions.items() if key in _DIM_KEYS})
    return dims


def refit_chart(
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
    """Render, inspect, and grow the canvas until clipping/overflow/squash is cleared.

    Each pass renders at the current dimensions through ``render_and_inspect_chart`` and reads
    the exact fix vectors the inspection already computed. While a resize-fixable defect
    remains, the canvas is grown by the measured overflow and re-rendered. The loop exits when
    geometry is clean, the delivery-profile ceiling is reached (warned, never squashed),
    ``max_iterations`` grows have run, or a grow stopped reducing the residual.

    ``dimensions``/``delivery_profile``/``max_iterations`` are inputs with profile defaults, not
    baked constants. Underfill is reported (``underfilled`` + a warning) but never auto-resized.

    Returns the final artifact, inspection path, ``final_dimensions``, a per-pass ``history``,
    ``warnings``, a ``resolved`` flag (no resize-fixable defect left), and ``underfilled``.
    """
    if max_iterations < 1:
        raise ValueError("max_iterations must be one or greater")
    profile = delivery_profile or "chat"
    ceiling = PROFILES.get(profile, PROFILES["chat"])
    max_w = float(ceiling["max_width_px"])
    max_h = float(ceiling["max_height_px"])

    dims = _starting_dims(profile, dimensions)
    warnings: list[str] = []
    history: list[dict[str, Any]] = []
    previous_residual: float | None = None
    bundle: dict[str, Any] = {}
    inspection: dict[str, Any] = {}
    resolved = False

    for pass_index in range(max_iterations + 1):
        bundle = render_and_inspect_chart(
            source_path,
            output_dir,
            renderer=renderer,
            delivery_profile=profile,
            dimensions=dims,
            artifact_name=artifact_name,
            build_function=build_function,
            content=content,
        )
        inspection = read_json(Path(bundle["inspection_path"]))
        geometry_summary = inspection.get("geometry_summary", {})
        residual = _grow_residual(geometry_summary)
        underfilled = any(
            defect.get("code") == "UNDERFILLED_CANVAS"
            for defect in inspection.get("defects", [])
        )
        entry: dict[str, Any] = {
            "pass": pass_index,
            "dimensions": dict(dims),
            "clip_px_max": geometry_summary.get("clip_px_max", 0.0),
            "edge_overflow_px": geometry_summary.get("edge_overflow_px"),
            "panels_squashed": geometry_summary.get("panels_squashed", False),
            "min_panel_height_px": geometry_summary.get("min_panel_height_px"),
            "grow_residual_px": residual,
            "underfilled": underfilled,
            "action": None,
        }
        history.append(entry)

        if residual <= 0.0:
            entry["action"] = "resolved"
            resolved = True
            break

        proposed = _propose_dims(geometry_summary, dims, max_w, max_h)
        if proposed == dims:
            entry["action"] = "ceiling_reached"
            warnings.append(
                f"{residual:.0f}px of clip/overflow remains but the {profile} ceiling "
                f"({int(max_w)}x{int(max_h)}px) is reached - not squashing; thin the content, "
                "aggregate, or split the chart."
            )
            break
        if previous_residual is not None and residual >= previous_residual:
            entry["action"] = "no_improvement"
            warnings.append(
                f"resize stopped improving ({residual:.0f}px residual did not fall below the "
                f"previous {previous_residual:.0f}px) - delivering the best effort."
            )
            break
        if pass_index == max_iterations:
            entry["action"] = "max_iterations"
            warnings.append(
                f"max_iterations ({max_iterations}) reached with {residual:.0f}px of "
                "clip/overflow remaining."
            )
            break

        entry["action"] = "grow"
        previous_residual = residual
        dims = proposed

    final_underfilled = bool(history[-1]["underfilled"])
    if final_underfilled:
        warnings.append(
            "Canvas is underfilled (too little ink for its size); refit does not resize for "
            "this - use a denser layout, size marks/text to the space, or the requested table."
        )

    return {
        "resolved": resolved,
        "underfilled": final_underfilled,
        "passes": len(history),
        "final_dimensions": dict(dims),
        "renderer": bundle.get("renderer"),
        "content": content,
        "delivery_profile": profile,
        "artifact": bundle.get("artifact"),
        "inspection_path": bundle.get("inspection_path"),
        "layout_metadata_path": bundle.get("layout_metadata_path"),
        "manifest_path": bundle.get("manifest_path"),
        "review_view_paths": bundle.get("review_view_paths", []),
        "passes_geometry_checks": inspection.get("passes_geometry_checks"),
        "history": history,
        "warnings": warnings,
    }
