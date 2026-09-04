"""Wrap and de-collide a chart's text once the canvas is fixed.

The forward companion to the collision and clip checks in ``inspection``: given the decided
canvas and the text the build has written (title, subtitle, caption, labels, annotations) plus
the data marks each label points at, this wraps every block to fit its room and parks every
movable label just beside the mark it names - the anchor is the mark, not the box corner.
Text is placed by priority (data labels, then category/series labels, then free annotations),
so the least-free text claims its spot first. A label sits adjacent to its mark with no leader;
only when no adjacent spot exists does it travel to the nearest clear area and grow a leader
line back to its point. It reports the wrap and the parked position; the model still owns which
label to show and what it says.

Mechanism only. It never invents an annotation - it fits the ones already chosen.
"""

from __future__ import annotations

import math
import re
from typing import Any, Optional

from .layout import FONT_PT, boxes_overlap, char_px, line_px


_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[float]:
    """Every numeric token in ``text`` as a float - `42%`, `$0.05`, `1,650`, `340` all parse."""
    out: set[float] = set()
    for token in _NUMBER_RE.findall(text or ""):
        try:
            out.add(float(token.replace(",", "")))
        except ValueError:
            continue
    return out


def _is_yearlike(value: float) -> bool:
    """A four-digit integer in a plausible calendar range - a coordinate, not a measured value."""
    return float(value).is_integer() and 1500 <= value <= 2200


FIXED_ROLES = {"title", "subtitle", "footer", "caption"}
# On-mark labels and axis labels the plotting layer already positioned. Their position is fixed,
# so - like a title - they are wrapped but never moved. A data label's own mark is never an
# obstacle to push it off. Only free callouts (role annotation/label) are de-collided.
ON_MARK_ROLES = {"data_label", "axis_label"}
LABEL_ROLES = {"label"} | ON_MARK_ROLES

# Placement priority: least-free text claims its spot first and becomes an obstacle for the
# freer text that follows. Fixed bands and on-mark data labels are pinned (tier 0/1); a
# category/series label is bound to a series but can slide along it (tier 2); a free annotation
# has the most room, so it fits last into what is left (tier 3). Within a tier, input order.
_PLACEMENT_TIER = {
    "title": 0, "subtitle": 0, "footer": 0, "caption": 0,
    "data_label": 1,
    "axis_label": 1,
    "label": 2,
    "annotation": 3,
}


def _tier(role: str) -> int:
    return _PLACEMENT_TIER.get(role, 3)


def _direction_order(hint: Optional[str]) -> list[str]:
    """The order to try parking a label around its mark. An explicit hint goes first, then the
    default right -> above -> below -> left (right is the standard direct-label position)."""
    base = ["right", "above", "below", "left"]
    if hint in base:
        return [hint] + [d for d in base if d != hint]
    return base


def _park(mark: tuple[float, float], direction: str, gap: float, w: float, h: float) -> tuple[float, float]:
    """Top-left of a box sitting one ``gap`` beside ``mark`` in ``direction``, centred on the
    mark along the perpendicular axis. The anchor is the mark; the label sits next to it."""
    mx, my = mark
    if direction == "right":
        return mx + gap, my - h / 2
    if direction == "left":
        return mx - gap - w, my - h / 2
    if direction == "above":
        return mx - w / 2, my - gap - h
    return mx - w / 2, my + gap  # below


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


def _wrap_to_line_budget(
    text: str,
    font_pt: float,
    dpi: float,
    avail_px: float,
    max_lines: int | None = None,
    allow_curtail: bool = False,
) -> tuple[str, float, float, bool, bool]:
    """Wrap to a chosen measure; curtail only when the caller explicitly permits it."""
    wrapped, box_w, box_h = _wrap(text, font_pt, dpi, avail_px)
    lines = wrapped.split("\n")
    if max_lines is None or len(lines) <= max_lines:
        return wrapped, box_w, box_h, False, False

    if not allow_curtail:
        return wrapped, box_w, box_h, False, True

    cpl = max(1, int(avail_px / char_px(font_pt, dpi)))
    kept = lines[:max_lines]
    if cpl == 1:
        kept[-1] = "…"
    else:
        kept[-1] = kept[-1][: cpl - 1].rstrip() + "…"
    longest = max(len(line) for line in kept)
    return (
        "\n".join(kept),
        longest * char_px(font_pt, dpi),
        len(kept) * line_px(font_pt, dpi),
        True,
        True,
    )


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


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    """Centre point of a bbox."""
    return bbox["x"] + bbox["width"] / 2, bbox["y"] + bbox["height"] / 2


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _segments_cross(
    a: tuple[float, float], b: tuple[float, float],
    c: tuple[float, float], d: tuple[float, float],
) -> bool:
    """True if open segment a-b properly crosses open segment c-d (shared endpoints don't count)."""
    def orient(p, q, r) -> float:
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])

    d1, d2 = orient(c, d, a), orient(c, d, b)
    d3, d4 = orient(a, b, c), orient(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _leader_endpoints(leader: dict[str, dict[str, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    """The (from, to) points of a leader line as tuples."""
    return (leader["from"]["x"], leader["from"]["y"]), (leader["to"]["x"], leader["to"]["y"])


def _uncross_leaders(results: list[dict[str, Any]], obstacles: list[dict[str, Any]]) -> None:
    """Swap positions of movable labels whose leader lines cross, when the swap is collision-free.

    Each label is de-collided independently to its own nearest clear spot, so two labels naming
    marks on opposite sides can land swapped - their leaders cross. Here we look at every pair of
    displaced movable labels whose leaders cross and try trading their box positions: label A takes
    B's spot and B takes A's. Each label keeps the mark it names, so the swap sends each back toward
    its own point and uncrosses the pair - accepted only if both boxes stay clear of the obstacles
    and every other placed box. Greedy, repeated to a fixed point; a swap that cannot be made clean
    is left as-is."""
    movers = [
        r for r in results
        if r.get("leader_line") and r["role"] not in (FIXED_ROLES | ON_MARK_ROLES)
    ]
    if len(movers) < 2:
        return

    def clear_at(box: dict[str, float], ignore: tuple[dict, dict]) -> bool:
        others = [r["bbox"] for r in results if r not in ignore] + obstacles
        return not _hits_any(box, others)

    changed = True
    guard = len(movers) ** 2 + 1
    while changed and guard > 0:
        changed = False
        guard -= 1
        for i in range(len(movers)):
            for j in range(i + 1, len(movers)):
                a, b = movers[i], movers[j]
                a_from, a_to = _leader_endpoints(a["leader_line"])
                b_from, b_to = _leader_endpoints(b["leader_line"])
                if not _segments_cross(a_from, a_to, b_from, b_to):
                    continue
                a_box = {**a["bbox"], "x": b["bbox"]["x"], "y": b["bbox"]["y"]}
                b_box = {**b["bbox"], "x": a["bbox"]["x"], "y": a["bbox"]["y"]}
                if boxes_overlap(a_box, b_box):
                    continue
                if not (clear_at(a_box, (a, b)) and clear_at(b_box, (a, b))):
                    continue
                new_a_leader = _leader_line(a_box, a_to)
                new_b_leader = _leader_line(b_box, b_to)
                if _segments_cross(*_leader_endpoints(new_a_leader), *_leader_endpoints(new_b_leader)):
                    continue  # swap did not actually uncross them
                for block, box, leader in ((a, a_box, new_a_leader), (b, b_box, new_b_leader)):
                    block["bbox"] = {k: round(v, 1) for k, v in box.items()}
                    block["leader_line"] = leader
                    block["suggested_anchor"] = {"x": round(box["x"]), "y": round(box["y"])}
                    if not any("uncross" in w for w in block["warnings"]):
                        block["warnings"].append(
                            "swapped position with another label to uncross their leader lines"
                        )
                changed = True


def _search_clear(
    bbox: dict[str, float],
    blockers: list[dict[str, Any]],
    width: float,
    height: float,
    margin: float,
    step: float,
) -> Optional[tuple[float, float]]:
    """Ring-search outward from the anchor for the nearest position clear of every blocker.

    Steps in fine (quarter-``step``) increments and, at the first ring that has any clear spot,
    returns the candidate closest to the anchor - so a label moves the least distance that clears
    instead of jumping a whole line-height in the first compass direction that happens to be free.
    Reach is unchanged (finer steps, proportionally more rings)."""
    ox, oy = bbox["x"], bbox["y"]
    directions = [
        (0, -1), (1, 0), (0, 1), (-1, 0),
        (1, -1), (1, 1), (-1, 1), (-1, -1),
    ]
    fine = max(2.0, step / 4)
    rings = int(step * 12 / fine) + 1
    for ring in range(1, rings + 1):
        clear: list[tuple[float, float]] = []
        for dx, dy in directions:
            candidate = {
                "x": ox + dx * fine * ring, "y": oy + dy * fine * ring,
                "width": bbox["width"], "height": bbox["height"],
            }
            cx, cy = _nudge_into_canvas(candidate, width, height, margin)
            candidate["x"], candidate["y"] = cx, cy
            if not _hits_any(candidate, blockers):
                clear.append((cx, cy))
        if clear:
            return min(clear, key=lambda c: _distance(c, (ox, oy)))
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
    max_lines: int | None = None,
    allow_curtail: bool = False,
) -> Optional[tuple[float, tuple[float, float], str, float, float, bool, bool]]:
    """Step the font down toward ``min_font_pt`` (largest first) until the block finds a clear
    spot - at its anchor if the smaller box now fits, else at the nearest clear position. Returns
    ``(font_pt, (x, y), wrapped, box_w, box_h, curtailed, over_budget)`` for the least
    shrink that fits, or ``None``."""
    ax, ay = anchor
    candidate = font_pt - 1.0
    while candidate >= min_font_pt:
        wrapped, box_w, box_h, curtailed, over_budget = _wrap_to_line_budget(
            text, candidate, dpi, avail, max_lines, allow_curtail
        )
        bbox = {"x": ax, "y": ay, "width": box_w, "height": box_h}
        if not _hits_any(bbox, blockers):
            return candidate, (ax, ay), wrapped, box_w, box_h, curtailed, over_budget
        found = _search_clear(bbox, blockers, width, height, margin, step=line_px(candidate, dpi))
        if found is not None:
            return candidate, found, wrapped, box_w, box_h, curtailed, over_budget
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
    plot_area: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Wrap every text block to fit and park each movable label beside the mark it names.

    Text is placed in priority order - data labels first, then category/series labels, then
    free annotations - so the least-free text claims its spot and the freer text fits around it.
    A movable label's ``anchor`` is the MARK it names: the box is parked one small gap beside the
    mark (preferred side first), with no leader line. Only when no adjacent spot exists at any of
    the label's marks does it travel to the nearest clear area and grow a leader back to its point.

    Args:
        width_px / height_px / dpi: the fixed canvas from ``recommend_layout``.
        blocks: text blocks, each ``{id, text, role, font_pt?, anchor:{x,y}, placement?, anchors?}``
            in canvas px. role in {title, subtitle, footer, caption} is fixed (box at the anchor,
            wrapped, never moved); role ``data_label`` is a value the plotting layer has already
            positioned on its mark or at a deliberate fixed offset from it - box at the anchor,
            wrapped, never moved, never de-collided against its own mark. role ``axis_label`` is likewise
            positioned by the plotting layer and wrapped without moving. role ``label`` (a category/series
            name) and ``annotation`` (a free callout) are movable: the anchor is the mark, and the
            box parks beside it. ``placement`` (one of right/above/below/left) sets the preferred
            side to try first (default right). ``anchors`` is an optional list of candidate marks
            for a ``label`` - it may sit beside any of them (e.g. any point along its line), since
            adjacency, not the endpoint, is what identifies the series; the first candidate is the
            primary and the leader, if any, points there.
        obstacles: bounding boxes ``{x, y, width, height}`` of the data marks/series in canvas
            px. Movable labels are always parked clear of these, not only text-vs-text.
            Do NOT pass a data label's own mark here - its fixed on-mark or adjacent placement is
            exempt from obstacle de-collision entirely.
        max_annotation_width_frac: widest a free annotation box may wrap to, as a fraction of width.
        For each category/series, on-mark data, or axis label, the block must also carry the
            builder's readability judgment: ``max_width_px`` and ``max_lines``. The tool enforces
            those physical limits; it does not invent a universal character count. Set
            ``allow_curtail: true`` only when an ellipsis is acceptable and the intact name will
            be supplied in a key or footnote. Otherwise an over-budget label stays intact and is
            reported for redesign.
        edge_margin_px: canvas margin; defaults to 3% of width.
        min_font_pt: legibility floor a movable block may shrink to when no clear spot is found
            at full size; never smaller, so a shrink can never create an undersized-text defect.

    Returns per-block ``wrapped_text``, ``wrap_width_chars``, and the final ``bbox`` (the box the
    builder should draw - authoritative, since the anchor was the mark, not the box). A label
    parked on its preferred side carries no ``suggested_anchor``, no ``leader_line`` and no
    warning; one parked on an alternate side or mark carries ``suggested_anchor`` and a warning.
    Only a label that found no adjacent spot and travelled to the nearest clear area (or shrank to
    fit) gets a ``leader_line`` (``{from, to}`` in canvas px) for the builder to draw as a thin
    connector back to its point, plus ``suggested_anchor`` / ``suggested_font_pt`` / ``suggested_wrap``
    and a warning. After all labels are placed, any pair of movable labels whose leader lines cross
    is swapped back - each label trades position with the other so both point at their own mark
    again - whenever the swap keeps both boxes clear of every mark and label; the swapped blocks
    carry an updated anchor, leader, and a warning.

    Returns a top-level ``redundant_annotations`` list (``{id, restated_value, data_label_id}``):
    a free annotation whose single data value a nearby ``data_label`` already prints is clutter -
    the value is on the chart twice - so it is recommended for removal, and the block also carries
    a warning. A comparison naming two values or a computed delta whose number is on no label is
    never flagged. When landscape text stays unresolvable, a canvas-level
    ``suggested_orientation: "portrait"`` and swapped ``suggested_canvas`` recommend a flip for a
    later build stage to apply and re-run against.
    """
    obstacles = list(obstacles or [])
    margin = float(edge_margin_px) if edge_margin_px is not None else round(0.03 * width_px)
    placed: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    unresolved = 0

    pinned = FIXED_ROLES | ON_MARK_ROLES
    # Place by priority: data labels first, then category/series labels, then free annotations,
    # so each tier becomes an obstacle the freer tier below it fits around.
    ordered = sorted(blocks, key=lambda b: _tier(b.get("role", "annotation")))
    for block in ordered:
        role = block.get("role", "annotation")
        font_pt = float(block.get("font_pt") or FONT_PT.get(role, FONT_PT["annotation"]))
        movable = role not in pinned
        anchor = block.get("anchor") or {"x": margin, "y": margin}
        ax, ay = float(anchor.get("x", margin)), float(anchor.get("y", margin))
        warnings: list[str] = []
        suggested_anchor: Optional[dict[str, int]] = None
        suggested_wrap: Optional[str] = None
        suggested_font_pt: Optional[float] = None
        leader_line: Optional[dict[str, dict[str, float]]] = None
        text = block.get("text", "")
        is_compact_label = role in LABEL_ROLES
        max_lines: int | None = None
        label_width: float | None = None
        allow_curtail = False
        if is_compact_label:
            if "max_width_px" not in block or "max_lines" not in block:
                raise ValueError(
                    f"{role} block {block.get('id')!r} must declare max_width_px and max_lines"
                )
            label_width = float(block["max_width_px"])
            max_lines = int(block["max_lines"])
            if label_width <= 0 or max_lines < 1:
                raise ValueError("label max_width_px and max_lines must be greater than zero")
            allow_curtail = bool(block.get("allow_curtail", False))

        if not movable:
            # Fixed bands and on-mark data labels: box origin at the anchor, wrapped, nudged in,
            # never de-collided or given a leader (a data label belongs on its mark).
            avail = (width_px - 2 * margin) if role in FIXED_ROLES else min(
                label_width or (width_px - 2 * margin),
                max(char_px(font_pt, dpi) * 8, width_px - ax - margin),
            )
            wrapped, box_w, box_h, curtailed, over_budget = _wrap_to_line_budget(
                text, font_pt, dpi, avail, max_lines, allow_curtail
            )
            bbox = {"x": ax, "y": ay, "width": box_w, "height": box_h}
            nx, ny = _nudge_into_canvas(bbox, width_px, height_px, margin)
            if (round(nx), round(ny)) != (round(ax), round(ay)):
                warnings.append("would clip the canvas edge; nudged inward")
                bbox["x"], bbox["y"] = nx, ny
            if role in FIXED_ROLES and _hits_any(bbox, placed):
                warnings.append(
                    "overlaps another fixed text block; widen its band or shorten the text"
                )
            placed.append(dict(bbox))
            results.append(
                {
                    "id": block.get("id"),
                    "role": role,
                    "wrapped_text": wrapped,
                    "full_text": text,
                    "curtailed": curtailed,
                    "over_line_budget": over_budget,
                    "wrap_width_chars": max(1, int(avail / char_px(font_pt, dpi))),
                    "bbox": {k: round(v, 1) for k, v in bbox.items()},
                    "suggested_anchor": None,
                    "suggested_font_pt": None,
                    "suggested_wrap": None,
                    "leader_line": None,
                    "plot_boundary_correction": None,
                    "warnings": warnings + ([
                        "label exceeds the readable line budget; use the returned full_text in "
                        "a key or footnote"
                    ] if curtailed else []) + ([
                        "label exceeds the chosen line budget; keep the full text and revise the "
                        "layout, wording, or form"
                    ] if over_budget and not curtailed else []),
                }
            )
            continue

        # Movable label/annotation: the anchor is the MARK; park the box beside it. A category
        # label may name several candidate marks along its series (`anchors`) - it can sit beside
        # any of them, since adjacency, not the endpoint, is what proves which series it names.
        plot_boundary_correction: Optional[dict[str, float]] = None
        avail = max(
            char_px(font_pt, dpi) * 8,
            min(max_annotation_width_frac * width_px, width_px - 2 * margin),
        )
        if label_width is not None:
            avail = min(avail, label_width)
        wrapped, box_w, box_h, curtailed, over_budget = _wrap_to_line_budget(
            text, font_pt, dpi, avail, max_lines, allow_curtail
        )
        if curtailed:
            warnings.append(
                "label exceeds the readable line budget; use the returned full_text in a key or footnote"
            )
        raw_marks = block.get("anchors") or [anchor]
        marks = [(float(m.get("x", ax)), float(m.get("y", ay))) for m in raw_marks]
        primary = marks[0]
        directions = _direction_order(block.get("placement"))
        gap = max(4.0, round(0.3 * line_px(font_pt, dpi)))
        blockers = obstacles + placed

        # 1. Adjacency: try each mark x each direction; the first clear spot wins, no leader.
        chosen: Optional[tuple[float, float, bool]] = None
        for mi, mark in enumerate(marks):
            for di, direction in enumerate(directions):
                px, py = _park(mark, direction, gap, box_w, box_h)
                cand = {"x": px, "y": py, "width": box_w, "height": box_h}
                cx, cy = _nudge_into_canvas(cand, width_px, height_px, margin)
                cand["x"], cand["y"] = cx, cy
                if not _hits_any(cand, blockers):
                    chosen = (cx, cy, mi == 0 and di == 0)
                    break
            if chosen is not None:
                break

        if chosen is not None:
            cx, cy, is_home = chosen
            bbox = {"x": cx, "y": cy, "width": box_w, "height": box_h}
            if not is_home:
                suggested_anchor = {"x": round(cx), "y": round(cy)}
                warnings.append("parked beside its mark to clear other marks and labels")
        else:
            # 2. No adjacent spot at any mark: search farther from the primary mark and, when it
            #    lands away from the mark, draw a leader so the pairing survives.
            start = _park(primary, directions[0], gap, box_w, box_h)
            bbox = {"x": start[0], "y": start[1], "width": box_w, "height": box_h}
            found = _search_clear(
                bbox, blockers, width_px, height_px, margin, step=line_px(font_pt, dpi)
            )
            if found is not None:
                bbox["x"], bbox["y"] = found
                suggested_anchor = {"x": round(found[0]), "y": round(found[1])}
                warnings.append("no adjacent spot; moved to the nearest clear area")
                leader_line = _leader_line(bbox, primary)
                warnings.append("moved off its point; draw a thin leader line to keep the pairing")
            else:
                # 3. Shrink toward the legibility floor, else tighten the wrap and flag for review.
                shrunk = _shrink_to_fit(
                    text, font_pt, dpi, avail, min_font_pt,
                    blockers, primary, width_px, height_px, margin, max_lines, allow_curtail,
                )
                if shrunk is not None:
                    font_pt, (cx, cy), wrapped, bw, bh, curtailed, over_budget = shrunk
                    bbox = {"x": cx, "y": cy, "width": bw, "height": bh}
                    suggested_font_pt = round(font_pt, 1)
                    suggested_anchor = {"x": round(cx), "y": round(cy)}
                    warnings.append(f"no clear spot at full size; shrank to {font_pt:.0f}pt to fit")
                    leader_line = _leader_line(bbox, primary)
                    warnings.append(
                        "moved off its point; draw a thin leader line to keep the pairing"
                    )
                else:
                    tight, tw, th, curtailed, over_budget = _wrap_to_line_budget(
                        text, font_pt, dpi, avail * 0.6, max_lines, allow_curtail
                    )
                    wrapped = tight
                    bbox = {"x": primary[0], "y": primary[1], "width": tw, "height": th}
                    bbox["x"], bbox["y"] = _nudge_into_canvas(bbox, width_px, height_px, margin)
                    suggested_wrap = tight
                    unresolved += 1
                    warnings.append(
                        "no clear spot even at the minimum legible size; tightened the wrap "
                        "- review placement by hand"
                    )

        if curtailed and not any("readable line budget" in warning for warning in warnings):
            warnings.append(
                "label exceeds the readable line budget; use the returned full_text in a key or footnote"
            )
        if over_budget and not curtailed:
            warnings.append(
                "label exceeds the chosen line budget; keep the full text and revise the layout, "
                "wording, or form"
            )
        # Local plot-boundary correction: a movable label left straddling the plot edge is clipped,
        # and canvas growth cannot fix it (the box is inside the canvas, across the *plot* boundary).
        # Nudge it wholly inside and report the exact move, so the driver applies one delta, not a
        # broad "re-place everything".
        if plot_area is not None:
            correction = _plot_boundary_correction(bbox, plot_area, obstacles + placed, margin)
            if correction is not None:
                bbox["x"] += correction["dx"]
                bbox["y"] += correction["dy"]
                plot_boundary_correction = correction
                suggested_anchor = {"x": round(bbox["x"]), "y": round(bbox["y"])}
                if leader_line is not None:
                    leader_line = _leader_line(bbox, primary)
                warnings.append("crossed the plot boundary; moved wholly inside the plot area")

        placed.append(dict(bbox))
        results.append(
            {
                "id": block.get("id"),
                "role": role,
                "wrapped_text": wrapped,
                "full_text": text,
                "curtailed": curtailed,
                "over_line_budget": over_budget,
                "wrap_width_chars": max(1, int(avail / char_px(font_pt, dpi))),
                "bbox": {k: round(v, 1) for k, v in bbox.items()},
                "suggested_anchor": suggested_anchor,
                "suggested_font_pt": suggested_font_pt,
                "suggested_wrap": suggested_wrap,
                "leader_line": leader_line,
                "plot_boundary_correction": plot_boundary_correction,
                "warnings": warnings,
            }
        )

    # Un-cross leaders: labels are de-collided one at a time, so two can land on each other's side
    # with crossing leader lines. Swap any such pair back when the swap stays clear of every mark
    # and box - a pass over the final geometry, after all labels are placed.
    _uncross_leaders(results, obstacles)

    # Redundant-annotation check: a free annotation that only restates the value a data label
    # already prints on the mark beside it is clutter - the value is on the chart twice. When an
    # annotation carries a single data value (years/coordinates ignored) and a nearby data_label
    # already shows that value, recommend dropping the annotation. A comparison that names two
    # values ("from 51% to 26%") or a computed delta ("up 9 points", whose number is on no label)
    # carries its own numbers and is never flagged - it adds what the labels do not.
    redundant_annotations: list[dict[str, Any]] = []
    data_labels = [
        (_center(r["bbox"]), _numbers(r["wrapped_text"]), r["id"], r["wrapped_text"])
        for r in results
        if r["role"] in ON_MARK_ROLES
    ]
    if data_labels:
        near = 0.2 * (width_px**2 + height_px**2) ** 0.5
        for r in results:
            if r["role"] in FIXED_ROLES or r["role"] in ON_MARK_ROLES:
                continue
            values = {n for n in _numbers(r["wrapped_text"]) if not _is_yearlike(n)}
            if len(values) != 1:
                continue
            value = next(iter(values))
            centre = _center(r["bbox"])
            for dl_centre, dl_values, dl_id, dl_text in data_labels:
                if value in dl_values and _distance(centre, dl_centre) <= near:
                    r["warnings"].append(
                        f"restates the data label '{dl_text.strip()}' beside it; drop the "
                        "annotation - the value is already on the chart"
                    )
                    redundant_annotations.append(
                        {"id": r["id"], "restated_value": value, "data_label_id": dl_id}
                    )
                    break

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
        "redundant_annotations": redundant_annotations,
        "suggested_orientation": suggested_orientation,
        "suggested_canvas": suggested_canvas,
    }


def _scale_trans(name: str, value: float) -> float:
    """Apply a ggplot scale transform's forward function, matching the space the panel
    ranges (and so the affine) live in. Only the reproducible numeric transforms; anything
    else never reaches here because the adapter emits no transform for it."""
    v = float(value)
    if name in ("identity", "", None):
        return v
    if name in ("log-10", "log10"):
        return math.log10(v)
    if name in ("log-2", "log2"):
        return math.log2(v)
    if name == "log":
        return math.log(v)
    if name == "sqrt":
        return math.sqrt(v)
    if name == "reverse":
        return -v
    raise ValueError(f"unsupported scale transform {name!r}")


def _project(
    transform: list[list[float]],
    x: float,
    y: float,
    x_trans: str = "identity",
    y_trans: str = "identity",
) -> tuple[float, float]:
    """Map a data ``(x, y)`` to canvas pixels: apply each axis' scale transform, then the
    top-left affine (row-major 3x3). The affine may carry cross terms (a flipped chart maps
    x to the vertical axis and y to the horizontal), so both rows read both coordinates."""
    tx = _scale_trans(x_trans, x)
    ty = _scale_trans(y_trans, y)
    r0, r1 = transform[0], transform[1]
    px = r0[0] * tx + r0[1] * ty + r0[2]
    py = r1[0] * tx + r1[1] * ty + r1[2]
    return round(px, 1), round(py, 1)


def _scale_trans_inverse(name: str, value: float) -> float:
    """Undo ``_scale_trans``: map a scale-transformed coordinate back to a data value."""
    v = float(value)
    if name in ("identity", "", None):
        return v
    if name in ("log-10", "log10"):
        return 10.0**v
    if name in ("log-2", "log2"):
        return 2.0**v
    if name == "log":
        return math.exp(v)
    if name == "sqrt":
        return v * v
    if name == "reverse":
        return -v
    raise ValueError(f"unsupported scale transform {name!r}")


def _project_inverse(
    transform: list[list[float]],
    px: float,
    py: float,
    x_trans: str = "identity",
    y_trans: str = "identity",
) -> Optional[tuple[float, float]]:
    """Map a canvas pixel back to a data ``(x, y)``: invert the top-left affine, then undo each
    axis' scale transform. Returns ``None`` for a singular (non-invertible) affine, so a caller
    emits no data-coordinate leader rather than a fabricated one."""
    r0, r1 = transform[0], transform[1]
    a, b = r0[0], r0[1]
    d, e = r1[0], r1[1]
    det = a * e - b * d
    if abs(det) < 1e-9:
        return None
    rx = px - r0[2]
    ry = py - r1[2]
    tx = (e * rx - b * ry) / det
    ty = (-d * rx + a * ry) / det
    x = _scale_trans_inverse(x_trans, tx)
    y = _scale_trans_inverse(y_trans, ty)
    return round(x, 6), round(y, 6)


def _plot_boundary_correction(
    bbox: dict[str, float],
    plot_area: dict[str, float],
    blockers: list[dict[str, Any]],
    margin: float,
) -> Optional[dict[str, float]]:
    """If ``bbox`` straddles the plot-area boundary (partly inside, partly out), return the exact
    shift {dx, dy} that brings it fully inside, preferring the smaller move. Returns ``None`` when
    the box is already wholly inside, wholly outside (a deliberate margin annotation), or when the
    corrected box would collide - those escalate, they are not silently shoved."""
    bx0, by0 = bbox["x"], bbox["y"]
    bx1, by1 = bx0 + bbox["width"], by0 + bbox["height"]
    px0, py0 = plot_area["x"], plot_area["y"]
    px1, py1 = px0 + plot_area["width"], py0 + plot_area["height"]
    inside = bx0 >= px0 and by0 >= py0 and bx1 <= px1 and by1 <= py1
    outside = bx1 <= px0 or bx0 >= px1 or by1 <= py0 or by0 >= py1
    if inside or outside:
        return None
    # Straddles an edge: clamp the origin so the whole box sits inside the plot rectangle.
    nx = min(max(bx0, px0), px1 - bbox["width"])
    ny = min(max(by0, py0), py1 - bbox["height"])
    dx, dy = round(nx - bx0, 1), round(ny - by0, 1)
    if dx == 0 and dy == 0:
        return None
    moved = {**bbox, "x": nx, "y": ny}
    if _hits_any(moved, blockers):
        return None
    return {"dx": dx, "dy": dy}


def place_on_marks(
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
    edge_margin_px: Optional[float] = None,
    min_font_pt: float = 8.0,
    plot_area: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Place labels glued to data marks using their real pixel positions, not a guess.

    The gap ``recommend_text_placement`` cannot close on its own: its anchors are canvas
    pixels, but a builder thinks in data coordinates. After one measure render, the layout
    metadata carries the exact data->pixel ``transform`` and the marks' bounding boxes. This
    projects each label's ``(data_x, data_y)`` through that transform, hands the marks in as
    obstacles, and delegates to ``recommend_text_placement`` - so labels are de-collided
    against where the marks *actually* landed, killing text-mark and text-text overlaps on the
    first delivered chart instead of after a revision loop.

    Args:
        width_px / height_px / dpi: the fixed canvas the measure render used.
        transform: the ``data_to_pixel_top_left`` affine for the label's axes, straight from
            the render's layout metadata (``transforms[i]``).
        labels: movable labels/annotations and on-mark data labels, each
            ``{id, text, role, data_x, data_y, placement?, max_width_px?, max_lines?, font_pt?,
            anchors_data?}``. ``anchors_data`` is an optional list of ``{data_x, data_y}``
            candidate marks for a category ``label`` (it may sit beside any of them). Roles
            follow ``recommend_text_placement``: ``label`` / ``annotation`` move, ``data_label``
            / ``axis_label`` stay on their projected spot.
        marks: the render's mark boxes (``layout['marks']`` and/or ``['series']``); their
            ``bbox`` values become the obstacles movable labels dodge.
        fixed_blocks: frame blocks from ``reserve_frame`` (already in px), passed through so
            data labels also clear the title/subtitle/caption.
        x_trans / y_trans: the axes' scale-transform names from the same layout-metadata
            transform entry (``identity`` / ``log-10`` / ``log-2`` / ``log`` / ``sqrt`` /
            ``reverse``). Applied to each data coordinate before the affine, because the affine
            lives in the scale-transformed space. Default identity (matplotlib and linear
            ggplot axes).
        max_annotation_width_frac / edge_margin_px / min_font_pt: forwarded verbatim.
        plot_area: the panel's plot rectangle ``{x, y, width, height}`` in canvas px (from
            ``reserve_frame``). When given, a movable label left straddling the plot boundary is
            nudged wholly inside and its exact move is reported - a clip that canvas growth cannot fix.

    Returns everything ``recommend_text_placement`` returns, plus ``projected_anchors``
    (``{label_id: {x, y}}``) so the caller can see where each mark landed. Every movable label
    also carries **native data coordinates** the builder draws from directly, so no data-space
    ``geom_segment``/``annotate`` has to be improvised (and pass through a neighbour): ``placed_data``
    (``{x, y}`` of the label box's **top-left** corner - draw the label left/top-anchored, e.g. ggplot
    ``hjust=0, vjust=1`` or matplotlib ``ha="left", va="top"``, so the drawn box matches the one the
    tool placed and the leader meets its edge), ``anchor_data`` (``{x, y}`` of the mark it names),
    and, when a leader is drawn, ``leader_line_data`` (``{from, to}`` - the box-edge end and the
    mark end, in data coords). These are the inverse of the same affine used to project, so the
    leader terminates exactly at the label's bounding-box edge and at the mark. A singular affine
    yields no data coordinates (they are omitted) rather than a fabricated one.
    """
    if not transform or len(transform) < 2 or len(transform[0]) < 3 or len(transform[1]) < 3:
        raise ValueError(
            "place_on_marks needs a data->pixel transform (the render's "
            "transforms[i].data_to_pixel_top_left). Every CoordCartesian ggplot emits one - "
            "coord_flip, log/sqrt/reverse scales, and facets (one transform per panel, keyed "
            "by axes_id) included. The render emits none only for a non-Cartesian coord "
            "(coord_trans/polar/sf) or an unreproducible scale transform (date/logit/custom); "
            "place those labels with the renderer's own repel (e.g. ggrepel) and verify with "
            "inspect_rendered_chart instead."
        )
    blocks: list[dict[str, Any]] = list(fixed_blocks or [])
    projected: dict[str, dict[str, float]] = {}
    for label in labels:
        px, py = _project(transform, label["data_x"], label["data_y"], x_trans, y_trans)
        projected[label["id"]] = {"x": px, "y": py}
        block = {
            key: value
            for key, value in label.items()
            if key not in ("data_x", "data_y", "anchors_data")
        }
        block["anchor"] = {"x": px, "y": py}
        anchors_data = label.get("anchors_data")
        if anchors_data:
            block["anchors"] = [
                dict(zip(("x", "y"),
                         _project(transform, m["data_x"], m["data_y"], x_trans, y_trans)))
                for m in anchors_data
            ]
        blocks.append(block)

    obstacles = [m["bbox"] for m in (marks or []) if "bbox" in m]
    result = recommend_text_placement(
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
    result["projected_anchors"] = projected

    # Hand the builder exact native coordinates for every movable label, so leaders and label
    # positions are drawn from the inverse of the projection - never improvised in data space.
    mark_data = {label["id"]: {"x": label["data_x"], "y": label["data_y"]} for label in labels}
    for placement in result.get("placements", []):
        if placement["role"] in (FIXED_ROLES | ON_MARK_ROLES):
            continue
        bbox = placement["bbox"]
        placed_data = _project_inverse(transform, bbox["x"], bbox["y"], x_trans, y_trans)
        if placed_data is not None:
            placement["placed_data"] = {"x": placed_data[0], "y": placed_data[1]}
        if placement["id"] in mark_data:
            placement["anchor_data"] = mark_data[placement["id"]]
        leader = placement.get("leader_line")
        if leader is not None:
            src = _project_inverse(transform, leader["from"]["x"], leader["from"]["y"], x_trans, y_trans)
            dst = _project_inverse(transform, leader["to"]["x"], leader["to"]["y"], x_trans, y_trans)
            if src is not None and dst is not None:
                placement["leader_line_data"] = {
                    "from": {"x": src[0], "y": src[1]},
                    "to": {"x": dst[0], "y": dst[1]},
                }
    return result
