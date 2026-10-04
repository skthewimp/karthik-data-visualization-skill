"""Deterministic colour, precision, scale, and chart-reading capabilities for dataviz agents."""

from .mark_read import read_marks_from_anchors
from .palette import recommend_colours
from .precision import recommend_precision
from .scale_transform import recommend_scale_transform

__all__ = [
    "read_marks_from_anchors",
    "recommend_colours",
    "recommend_precision",
    "recommend_scale_transform",
]
