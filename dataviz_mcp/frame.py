"""Reserve the frame - title, subtitle, caption, footer, axis and legend bands - blind.

The chrome of a chart (its title and axis labels) sits in the margins; where it goes does
not depend on where the data landed. So it can be placed with text-measuring arithmetic
*before* anything is drawn: wrap each block to the canvas width, count the lines, reserve a
pixel band, and hand back the rectangle the marks get to fill. No render needed.

This is the forward companion to ``recommend_layout``: layout sizes the whole box from the
data's shape; this carves the frame off the top/bottom/sides so the plot area is known before
the first draw. Together they kill clipped titles and empty canvases without a revision loop.

Not a chart chooser and not a data-label placer: it only measures the frame text the caller
already wrote. On-mark labels glued to specific marks are ``place_on_marks``' job, after a
measure render.
"""

from __future__ import annotations

from typing import Any, Optional

from .layout import FONT_PT, PROFILES, char_px, line_px, pt_to_px
from .text_fit import _wrap


def _band(lines: int, font_pt: float, dpi: float) -> float:
    """Vertical room a text band of ``lines`` lines needs at ``font_pt``, with padding."""
    if lines <= 0:
        return 0.0
    return lines * line_px(font_pt, dpi) + pt_to_px(font_pt, dpi) * 0.6


def _wrap_block(
    block_id: str,
    role: str,
    text: str,
    font_pt: float,
    dpi: float,
    avail_px: float,
) -> Optional[dict[str, Any]]:
    """Wrap one full-width frame block and return a placement-ready record, or None if empty."""
    if not text or not text.strip():
        return None
    wrapped, box_w, box_h = _wrap(text, font_pt, dpi, avail_px)
    return {
        "id": block_id,
        "role": role,
        "text": text,
        "wrapped_text": wrapped,
        "font_pt": font_pt,
        "lines": wrapped.count("\n") + 1,
        "box_w": box_w,
        "box_h": box_h,
    }


def reserve_frame(
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
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
    dpi: Optional[int] = None,
    delivery_profile: str = "chat",
    font_pt: Optional[dict[str, float]] = None,
    edge_margin_px: Optional[float] = None,
) -> dict[str, Any]:
    """Reserve the frame blind and return the plot rectangle the marks may fill.

    Wraps each frame block to the canvas width with text metrics (no render), reserves a
    pixel band for it, and subtracts the bands from the canvas to leave the plot area. The
    title/subtitle/caption/footer come back as placement-ready ``frame_blocks`` (roles that
    ``recommend_text_placement`` / ``place_on_marks`` treat as fixed) so the same boxes can be
    drawn and passed on as obstacles. Axis and legend bands are reserved but not emitted as
    blocks - the plotting layer draws those itself.

    Canvas size, dpi, and per-role font sizes are all inputs: pass ``width_px`` / ``height_px``
    / ``dpi`` to fix the canvas (else the ``delivery_profile`` default) and ``font_pt`` to
    override any house size, e.g. ``{"title": 20}``. A frame that cannot fit even wrapped is
    warned, never squashed.

    Args:
        title / subtitle / caption / footer: full-width frame text (raw, unwrapped).
        x_axis_title / y_axis_title: axis titles, for the bottom/left band reservation.
        longest_x_tick / longest_y_tick: the widest tick label string, to size the axis bands.
        legend_side: none / right / bottom - reserves a legend band on that side.
        longest_legend_label: widest legend entry, to size a right/bottom legend band.
        width_px / height_px / dpi: fix the canvas; default to the delivery profile.
        delivery_profile: chat / slide / document - the default canvas and dpi.
        font_pt: per-role point-size overrides merged over the house sizes.
        edge_margin_px: outer margin; defaults to 3% of width.

    Returns ``canvas``, ``plot_area`` (x/y/width/height), ``reserved_px`` (top/bottom/left/
    right), ``frame_blocks`` (each with wrapped_text, font_pt, anchor, bbox), ``warnings`` and
    a ``rationale``.
    """
    profile = PROFILES.get(delivery_profile, PROFILES["chat"])
    width = float(width_px if width_px is not None else profile["width_px"])
    height = float(height_px if height_px is not None else profile["height_px"])
    resolved_dpi = int(dpi if dpi is not None else profile["dpi"])
    dpi_f = float(resolved_dpi)
    fonts = {**FONT_PT, **(font_pt or {})}
    margin = float(edge_margin_px) if edge_margin_px is not None else round(0.03 * width)
    avail_w = width - 2 * margin
    warnings: list[str] = []

    # Top stack: title then subtitle, from the top margin down.
    top_specs = [("title", "title", title), ("subtitle", "subtitle", subtitle)]
    # Bottom stack: caption then footer, sitting above the bottom margin.
    bottom_specs = [("caption", "caption", caption), ("footer", "footer", footer)]

    frame_blocks: list[dict[str, Any]] = []

    top_cursor = margin
    for block_id, role, text in top_specs:
        rec = _wrap_block(block_id, role, text, fonts[role], dpi_f, avail_w)
        if rec is None:
            continue
        bbox = {"x": margin, "y": top_cursor, "width": rec["box_w"], "height": rec["box_h"]}
        _emit(frame_blocks, rec, bbox)
        if rec["box_w"] > avail_w + 0.5:
            warnings.append(f"{role} is wider than the canvas even wrapped; shorten it")
        top_cursor += rec["box_h"] + _band(0, fonts[role], dpi_f)
        top_cursor += pt_to_px(fonts[role], dpi_f) * 0.4  # inter-band gap
    top = top_cursor if frame_blocks else margin

    # Bottom bands: axis strip closest to the plot, then caption, then footer at the very edge.
    x_axis_lines = (1 if longest_x_tick.strip() else 0) + (1 if x_axis_title.strip() else 0)
    x_axis_band = _band(x_axis_lines, fonts["axis"], dpi_f)

    bottom_records: list[tuple[dict[str, Any], dict[str, Any]]] = []
    footer_cursor = height - margin
    for block_id, role, text in reversed(bottom_specs):  # footer lowest, caption above it
        rec = _wrap_block(block_id, role, text, fonts[role], dpi_f, avail_w)
        if rec is None:
            continue
        footer_cursor -= rec["box_h"]
        bbox = {"x": margin, "y": footer_cursor, "width": rec["box_w"], "height": rec["box_h"]}
        bottom_records.append((rec, bbox))
        footer_cursor -= pt_to_px(fonts[role], dpi_f) * 0.4
        if rec["box_w"] > avail_w + 0.5:
            warnings.append(f"{role} is wider than the canvas even wrapped; shorten it")
    for rec, bbox in bottom_records:
        _emit(frame_blocks, rec, bbox)
    bottom_text = (height - margin) - footer_cursor if bottom_records else 0.0
    bottom = margin + x_axis_band + bottom_text

    # Left band: widest y tick + a rotated y-axis title (its line height becomes width).
    left_band = 0.0
    if longest_y_tick.strip():
        left_band += len(longest_y_tick) * char_px(fonts["axis"], dpi_f)
    if y_axis_title.strip():
        left_band += line_px(fonts["axis"], dpi_f)
    if left_band:
        left_band += pt_to_px(fonts["axis"], dpi_f) * 0.6
    left = margin + left_band

    # Right band: a right-side legend column (else nothing).
    right_band = 0.0
    if legend_side == "right":
        swatch = pt_to_px(fonts["axis"], dpi_f) * 1.4
        right_band = swatch + len(longest_legend_label or "series") * char_px(fonts["axis"], dpi_f)
        right_band += pt_to_px(fonts["axis"], dpi_f) * 0.6
    elif legend_side == "bottom":
        bottom += line_px(fonts["axis"], dpi_f) * 1.6
    right = margin + right_band

    plot_area = {
        "x": round(left, 1),
        "y": round(top, 1),
        "width": round(width - left - right, 1),
        "height": round(height - top - bottom, 1),
    }
    floor = 80.0
    if plot_area["width"] < floor or plot_area["height"] < floor:
        warnings.append(
            "the frame reserves almost the whole canvas; the plot area is too small - "
            "enlarge the canvas, shorten the text, or drop a frame element"
        )

    rationale = (
        f"{int(width)}x{int(height)}px @ {resolved_dpi}dpi: reserved top {top - margin:.0f}px, "
        f"bottom {bottom - margin:.0f}px, left {left_band:.0f}px, right {right_band:.0f}px "
        f"-> plot {plot_area['width']:.0f}x{plot_area['height']:.0f}px."
    )
    return {
        "canvas": {"width_px": int(width), "height_px": int(height), "dpi": resolved_dpi},
        "plot_area": plot_area,
        "reserved_px": {
            "top": round(top, 1),
            "bottom": round(bottom, 1),
            "left": round(left, 1),
            "right": round(right, 1),
        },
        "frame_blocks": frame_blocks,
        "warnings": warnings,
        "rationale": rationale,
    }


def _emit(frame_blocks: list[dict[str, Any]], rec: dict[str, Any], bbox: dict[str, Any]) -> None:
    frame_blocks.append(
        {
            "id": rec["id"],
            "role": rec["role"],
            "text": rec["text"],
            "wrapped_text": rec["wrapped_text"],
            "font_pt": rec["font_pt"],
            "anchor": {"x": round(bbox["x"], 1), "y": round(bbox["y"], 1)},
            "bbox": {k: round(v, 1) for k, v in bbox.items()},
        }
    )
