"""Wrap and de-collide a chart's text once the canvas is fixed.

The forward companion to the collision and clip checks in ``inspection``: given the decided
canvas and the text the build has written (title, subtitle, caption, annotations) plus the
data marks each annotation points at, this wraps every block to fit its room and moves any
annotation that would collide with another text block, the canvas edge, or a data mark to the
nearest clear spot. It reports the wrap and the moved anchor; the model still owns which
annotation to show and what it says.

Mechanism only. It never invents an annotation - it fits the ones already chosen.
"""

from __future__ import annotations

from typing import Any, Optional

from .layout import FONT_PT, boxes_overlap, char_px, line_px


FIXED_ROLES = {"title", "subtitle", "footer", "caption"}


def _wrap(text: str, font_pt: float, dpi: float, avail_px: float) -> tuple[str, float, float]:
    """Greedy word-wrap ``text`` to ``avail_px`` wide; return wrapped text and its box size."""
    cpl = max(1, int(avail_px / char_px(font_pt, dpi)))
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= cpl or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines or [""]
    longest = max(len(line) for line in lines)
    box_w = longest * char_px(font_pt, dpi)
    box_h = len(lines) * line_px(font_pt, dpi)
    return "\n".join(lines), box_w, box_h


def _nudge_into_canvas(
    bbox: dict[str, float], width: float, height: float, margin: float
) -> tuple[float, float]:
    """Return an (x, y) that keeps ``bbox`` inside the canvas margins."""
    x = min(max(bbox["x"], margin), max(margin, width - margin - bbox["width"]))
    y = min(max(bbox["y"], margin), max(margin, height - margin - bbox["height"]))
    return x, y


def _hits_any(bbox: dict[str, float], blockers: list[dict[str, Any]]) -> bool:
    return any(boxes_overlap(bbox, other) for other in blockers)


def _leader_line(bbox: dict[str, float], anchor: tuple[float, float]) -> dict[str, dict[str, float]]:
    """A thin connector from the label box back to the point it names.

    Starts at the point on the box perimeter nearest the anchor (clamp the anchor onto the
    box), ends at the anchor. Drawn by the builder so a displaced label still pairs with its
    mark - ggrepel's segment.
    """
    ax, ay = anchor
    fx = min(max(ax, bbox["x"]), bbox["x"] + bbox["width"])
    fy = min(max(ay, bbox["y"]), bbox["y"] + bbox["height"])
    return {"from": {"x": round(fx, 1), "y": round(fy, 1)}, "to": {"x": round(ax, 1), "y": round(ay, 1)}}


def _search_clear(
    bbox: dict[str, float],
    blockers: list[dict[str, Any]],
    width: float,
    height: float,
    margin: float,
    step: float,
) -> Optional[tuple[float, float]]:
    """Ring-search outward from the anchor for the nearest position clear of every blocker."""
    ox, oy = bbox["x"], bbox["y"]
    directions = [
        (0, -1), (1, 0), (0, 1), (-1, 0),
        (1, -1), (1, 1), (-1, 1), (-1, -1),
    ]
    for ring in range(1, 13):
        for dx, dy in directions:
            cx = ox + dx * step * ring
            cy = oy + dy * step * ring
            candidate = {"x": cx, "y": cy, "width": bbox["width"], "height": bbox["height"]}
            cx, cy = _nudge_into_canvas(candidate, width, height, margin)
            candidate["x"], candidate["y"] = cx, cy
            if not _hits_any(candidate, blockers):
                return cx, cy
    return None


def _shrink_to_fit(
    text: str,
    font_pt: float,
    dpi: float,
    avail: float,
    min_font_pt: float,
    blockers: list[dict[str, Any]],
    anchor: tuple[float, float],
    width: float,
    height: float,
    margin: float,
) -> Optional[tuple[float, tuple[float, float], str, float, float]]:
    """Step the font down toward ``min_font_pt`` (largest first) until the block finds a clear
    spot - at its anchor if the smaller box now fits, else at the nearest clear position. Returns
    ``(font_pt, (x, y), wrapped, box_w, box_h)`` for the least shrink that fits, or ``None``."""
    ax, ay = anchor
    candidate = font_pt - 1.0
    while candidate >= min_font_pt:
        wrapped, box_w, box_h = _wrap(text, candidate, dpi, avail)
        bbox = {"x": ax, "y": ay, "width": box_w, "height": box_h}
        if not _hits_any(bbox, blockers):
            return candidate, (ax, ay), wrapped, box_w, box_h
        found = _search_clear(bbox, blockers, width, height, margin, step=line_px(candidate, dpi))
        if found is not None:
            return candidate, found, wrapped, box_w, box_h
        candidate -= 1.0
    return None


def recommend_text_placement(
    width_px: int,
    height_px: int,
    dpi: int,
    blocks: list[dict[str, Any]],
    obstacles: list[dict[str, Any]] | None = None,
    max_annotation_width_frac: float = 0.32,
    edge_margin_px: Optional[float] = None,
    min_font_pt: float = 8.0,
) -> dict[str, Any]:
    """Wrap every text block to fit and move colliding annotations to the nearest clear spot.

    Args:
        width_px / height_px / dpi: the fixed canvas from ``recommend_layout``.
        blocks: text blocks, each ``{id, text, role, font_pt?, anchor:{x,y}}`` in canvas px.
            role in {title, subtitle, footer, caption} is fixed (wrapped, never moved);
            role annotation/label is movable.
        obstacles: bounding boxes ``{x, y, width, height}`` of the data marks/series in canvas
            px. Annotations are always de-collided against these, not only text-vs-text.
        max_annotation_width_frac: widest an annotation box may wrap to, as a fraction of width.
        edge_margin_px: canvas margin; defaults to 3% of width.
        min_font_pt: legibility floor a movable block may shrink to when no clear spot is found
            at full size; never smaller, so a shrink can never create an undersized-text defect.

    Returns per-block ``wrapped_text``, ``wrap_width_chars``, predicted ``bbox``, and, when it
    moved, shrank, or re-wrapped a block, ``suggested_anchor`` / ``suggested_font_pt`` /
    ``suggested_wrap`` plus a warning. A movable block that ends up off its original anchor also
    gets a ``leader_line`` (``{from, to}`` in canvas px) for the builder to draw as a thin
    connector, so a de-collided label still pairs with the mark it names. When landscape text
    stays unresolvable, a canvas-level
    ``suggested_orientation: "portrait"`` and swapped ``suggested_canvas`` recommend a flip for a
    later build stage to apply and re-run against.
    """
    obstacles = list(obstacles or [])
    margin = float(edge_margin_px) if edge_margin_px is not None else round(0.03 * width_px)
    placed: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    unresolved = 0

    ordered = sorted(blocks, key=lambda b: 0 if b.get("role") in FIXED_ROLES else 1)
    for block in ordered:
        role = block.get("role", "annotation")
        font_pt = float(block.get("font_pt") or FONT_PT.get(role, FONT_PT["annotation"]))
        movable = role not in FIXED_ROLES
        anchor = block.get("anchor") or {"x": margin, "y": margin}
        ax, ay = float(anchor.get("x", margin)), float(anchor.get("y", margin))
        orig_ax, orig_ay = ax, ay
        warnings: list[str] = []
        suggested_anchor: Optional[dict[str, int]] = None
        suggested_wrap: Optional[str] = None
        suggested_font_pt: Optional[float] = None

        if movable:
            avail = min(max_annotation_width_frac * width_px, width_px - ax - margin)
            avail = max(avail, char_px(font_pt, dpi) * 8)
        else:
            avail = width_px - 2 * margin

        wrapped, box_w, box_h = _wrap(block.get("text", ""), font_pt, dpi, avail)
        bbox = {"x": ax, "y": ay, "width": box_w, "height": box_h}

        nx, ny = _nudge_into_canvas(bbox, width_px, height_px, margin)
        if (round(nx), round(ny)) != (round(ax), round(ay)):
            warnings.append("would clip the canvas edge; nudged inward")
            ax, ay = nx, ny
            bbox["x"], bbox["y"] = ax, ay
            if movable:
                suggested_anchor = {"x": round(ax), "y": round(ay)}

        if movable:
            blockers = obstacles + placed
            if _hits_any(bbox, blockers):
                found = _search_clear(
                    bbox, blockers, width_px, height_px, margin, step=line_px(font_pt, dpi)
                )
                if found is not None:
                    ax, ay = found
                    bbox["x"], bbox["y"] = ax, ay
                    suggested_anchor = {"x": round(ax), "y": round(ay)}
                    warnings.append(
                        "overlapped a data mark or another label; moved to the nearest clear spot"
                    )
                else:
                    shrunk = _shrink_to_fit(
                        block.get("text", ""), font_pt, dpi, avail, min_font_pt,
                        blockers, (ax, ay), width_px, height_px, margin,
                    )
                    if shrunk is not None:
                        font_pt, (ax, ay), wrapped, bw, bh = shrunk
                        bbox = {"x": ax, "y": ay, "width": bw, "height": bh}
                        suggested_font_pt = round(font_pt, 1)
                        if (round(ax), round(ay)) != (round(orig_ax), round(orig_ay)):
                            suggested_anchor = {"x": round(ax), "y": round(ay)}
                        warnings.append(
                            f"no clear spot at full size; shrank to {font_pt:.0f}pt to fit"
                        )
                    else:
                        tight, tw, th = _wrap(block.get("text", ""), font_pt, dpi, avail * 0.6)
                        wrapped, bbox["width"], bbox["height"] = tight, tw, th
                        suggested_wrap = tight
                        unresolved += 1
                        warnings.append(
                            "no clear spot even at the minimum legible size; tightened the wrap "
                            "- review placement by hand"
                        )
        elif _hits_any(bbox, placed):
            warnings.append(
                "overlaps another fixed text block; widen its band or shorten the text"
            )

        leader_line: Optional[dict[str, dict[str, float]]] = None
        if movable and (round(ax), round(ay)) != (round(orig_ax), round(orig_ay)):
            leader_line = _leader_line(bbox, (orig_ax, orig_ay))
            warnings.append("moved off its point; draw a thin leader line to keep the pairing")

        placed.append(dict(bbox))
        results.append(
            {
                "id": block.get("id"),
                "role": role,
                "wrapped_text": wrapped,
                "wrap_width_chars": max(1, int(avail / char_px(font_pt, dpi))),
                "bbox": {k: round(v, 1) for k, v in bbox.items()},
                "suggested_anchor": suggested_anchor,
                "suggested_font_pt": suggested_font_pt,
                "suggested_wrap": suggested_wrap,
                "leader_line": leader_line,
                "warnings": warnings,
            }
        )

    # Portrait recommendation: if text stayed unresolvable on a landscape canvas even after
    # moving and shrinking, more height than width would likely place it. Advisory only - the
    # tool cannot move the data marks, so a later build stage flips the canvas, re-renders, and
    # re-runs this against the new obstacle geometry.
    suggested_orientation: Optional[str] = None
    suggested_canvas: Optional[dict[str, int]] = None
    if unresolved and width_px > height_px:
        suggested_orientation = "portrait"
        suggested_canvas = {"width_px": height_px, "height_px": width_px, "dpi": dpi}

    return {
        "canvas": {"width_px": width_px, "height_px": height_px, "dpi": dpi},
        "placements": results,
        "suggested_orientation": suggested_orientation,
        "suggested_canvas": suggested_canvas,
    }
