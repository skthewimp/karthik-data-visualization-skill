"""Canvas constants and the overflow-to-canvas arithmetic shared by inspection and refit."""

from __future__ import annotations

import math
from typing import Any, Optional


# Delivery profiles: base canvas and the ceiling a growing dimension may not exceed.
# Height ceiling is generous for "document" so a long ranked strip can breathe.
PROFILES: dict[str, dict[str, int]] = {
    "chat": {"width_px": 1200, "height_px": 675, "dpi": 144, "max_width_px": 1600, "max_height_px": 1400},
    "slide": {"width_px": 1600, "height_px": 900, "dpi": 160, "max_width_px": 1920, "max_height_px": 1200},
    "document": {"width_px": 1800, "height_px": 1200, "dpi": 180, "max_width_px": 2200, "max_height_px": 3200},
}

MIN_PANEL_H = 150.0  # a facet panel shorter than this reads as a thumbnail


def suggest_dims_for_overflow(
    width_px: int,
    height_px: int,
    top_overflow_px: float = 0.0,
    bottom_overflow_px: float = 0.0,
    left_overflow_px: float = 0.0,
    right_overflow_px: float = 0.0,
    min_panel_height_px: Optional[float] = None,
) -> dict[str, Any]:
    """Backward companion for ``inspection``: given measured overflow on a rendered chart,
    return a grown canvas that accounts for the measured panel-to-canvas scale.
    This assumes panels expand with the canvas; fixed-size panels still require a design change.
    """
    grow_w = max(0.0, left_overflow_px) + max(0.0, right_overflow_px)
    grow_h = max(0.0, top_overflow_px) + max(0.0, bottom_overflow_px)
    new_w = math.ceil(width_px + grow_w)
    new_h = math.ceil(height_px + grow_h)
    if min_panel_height_px is not None and min_panel_height_px < MIN_PANEL_H:
        # A panel receives only a share of canvas growth. Scale by its measured
        # share, rather than adding one panel's deficit to the whole canvas.
        # This also covers unequal panels and fractional outer margins without
        # guessing a facet count. Fixed chrome makes this estimate conservative.
        if min_panel_height_px > 0:
            new_h = math.ceil(height_px * MIN_PANEL_H / min_panel_height_px + grow_h)
        else:
            # No positive panel extent from which to infer a scale. Keep a finite
            # growth probe; refit's ceiling/no-improvement guards still apply.
            new_h = math.ceil(new_h + MIN_PANEL_H - min_panel_height_px)
    return {
        "suggested_width_px": new_w,
        "suggested_height_px": new_h,
        "grow_width_px": new_w - width_px,
        "grow_height_px": new_h - height_px,
    }
