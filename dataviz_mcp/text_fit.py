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
# On-mark labels the plotting layer already centred on their mark (a stacked-bar segment value,
# a point label). Their position is fixed by the data, so - like a title - they are wrapped but
# never moved, and their own mark is never an obstacle to push them off. Only free callouts
# (role annotation/label) are de-collided.
ON_MARK_ROLES = {"data_label"}

# Placement priority: least-free text claims its spot first and becomes an obstacle for the
# freer text that follows. Fixed bands and on-mark data labels are pinned (tier 0/1); a
# category/series label is bound to a series but can slide along it (tier 2); a free annotation
# has the most room, so it fits last into what is left (tier 3). Within a tier, input order.
_PLACEMENT_TIER = {
    "title": 0, "subtitle": 0, "footer": 0, "caption": 0,
    "data_label": 1,
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
            wrapped, never moved); role ``data_label`` is an on-mark label the plotting layer
            already centred on its mark (a stacked-bar segment value) - box at the anchor, wrapped,
            never moved, never de-collided against its own mark. role ``label`` (a category/series
            name) and ``annotation`` (a free callout) are movable: the anchor is the mark, and the
            box parks beside it. ``placement`` (one of right/above/below/left) sets the preferred
            side to try first (default right). ``anchors`` is an optional list of candidate marks
            for a ``label`` - it may sit beside any of them (e.g. any point along its line), since
            adjacency, not the endpoint, is what identifies the series; the first candidate is the
            primary and the leader, if any, points there.
        obstacles: bounding boxes ``{x, y, width, height}`` of the data marks/series in canvas
            px. Movable labels are always parked clear of these, not only text-vs-text.
            Do NOT pass a segment's own bar here for its ``data_label`` - an on-mark label belongs
            inside its mark, so it is exempt from obstacle de-collision entirely.
        max_annotation_width_frac: widest an annotation box may wrap to, as a fraction of width.
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

        if not movable:
            # Fixed bands and on-mark data labels: box origin at the anchor, wrapped, nudged in,
            # never de-collided or given a leader (a data label belongs on its mark).
            avail = (width_px - 2 * margin) if role in FIXED_ROLES else max(
                char_px(font_pt, dpi) * 8,
                min(max_annotation_width_frac * width_px, width_px - ax - margin),
            )
            wrapped, box_w, box_h = _wrap(text, font_pt, dpi, avail)
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
                    "wrap_width_chars": max(1, int(avail / char_px(font_pt, dpi))),
                    "bbox": {k: round(v, 1) for k, v in bbox.items()},
                    "suggested_anchor": None,
                    "suggested_font_pt": None,
                    "suggested_wrap": None,
                    "leader_line": None,
                    "warnings": warnings,
                }
            )
            continue

        # Movable label/annotation: the anchor is the MARK; park the box beside it. A category
        # label may name several candidate marks along its series (`anchors`) - it can sit beside
        # any of them, since adjacency, not the endpoint, is what proves which series it names.
        avail = max(
            char_px(font_pt, dpi) * 8,
            min(max_annotation_width_frac * width_px, width_px - 2 * margin),
        )
        wrapped, box_w, box_h = _wrap(text, font_pt, dpi, avail)
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
                    blockers, primary, width_px, height_px, margin,
                )
                if shrunk is not None:
                    font_pt, (cx, cy), wrapped, bw, bh = shrunk
                    bbox = {"x": cx, "y": cy, "width": bw, "height": bh}
                    suggested_font_pt = round(font_pt, 1)
                    suggested_anchor = {"x": round(cx), "y": round(cy)}
                    warnings.append(f"no clear spot at full size; shrank to {font_pt:.0f}pt to fit")
                    leader_line = _leader_line(bbox, primary)
                    warnings.append(
                        "moved off its point; draw a thin leader line to keep the pairing"
                    )
                else:
                    tight, tw, th = _wrap(text, font_pt, dpi, avail * 0.6)
                    wrapped = tight
                    bbox = {"x": primary[0], "y": primary[1], "width": tw, "height": th}
                    bbox["x"], bbox["y"] = _nudge_into_canvas(bbox, width_px, height_px, margin)
                    suggested_wrap = tight
                    unresolved += 1
                    warnings.append(
                        "no clear spot even at the minimum legible size; tightened the wrap "
                        "- review placement by hand"
                    )

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
