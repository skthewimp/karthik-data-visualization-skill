"""Real glyph widths for the text placer, read from the font the renderer will resolve.

The placer used to size every text box with ``layout.char_px`` - a flat 0.5-em advance for
every character, blind to font family, weight, and the fact that ``i`` and ``W`` are nothing
alike. Rendered text then overran its assumed box and manufactured (or hid) clips and
collisions. This module replaces the width estimate with advances read from the actual
``.ttf`` the renderer will resolve.

The family is never guessed. It is carried from the render context - a matplotlib artist's
``FontProperties`` or a ggplot theme's ``text$family`` - into the block, resolved to a font
file with matplotlib's font manager, and measured with Pillow, which reads the same ``hmtx``
advances any renderer using that file gets. So a font substitution cannot bite: we measure
the file the renderer resolves, not a name we hoped matched. With no family declared we
resolve matplotlib's own default (DejaVu Sans), which is also the default renderer's real
face - so even an unlabelled chart gets real per-glyph advances instead of the flat estimate.

Only the WIDTH is measured here; line height stays ``layout.line_px`` (the reported defect is
horizontal overrun, and line height is close to font-independent). When a font cannot be
resolved or measured - offline, missing face, a bad size - every path falls back to the
proportional estimate, so placement degrades to the old behaviour rather than hard-failing.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from .layout import char_px, pt_to_px


@lru_cache(maxsize=256)
def _resolve_font_path(family: Optional[str], weight: str, style: str) -> Optional[str]:
    """Resolve a (family, weight, style) to a concrete font file via matplotlib's font manager.

    Returns the path of the closest installed face, or ``None`` when matplotlib is unavailable.
    matplotlib always falls back to its bundled default rather than raising, so a miss returns a
    real (if generic) face, never nothing - the caller only sees ``None`` if the import fails.
    """
    try:
        from matplotlib.font_manager import FontProperties, findfont
    except Exception:
        return None
    try:
        prop = FontProperties(
            family=family or None, weight=weight or "normal", style=style or "normal"
        )
        return findfont(prop, fallback_to_default=True)
    except Exception:
        return None


@lru_cache(maxsize=256)
def _pil_font(path: str, size_px: int):
    """A Pillow font handle for ``path`` at an integer pixel size, or ``None`` if it will not load."""
    try:
        from PIL import ImageFont
    except Exception:
        return None
    try:
        return ImageFont.truetype(path, size_px)
    except Exception:
        return None


class TextMeasurer:
    """Measure the pixel width of a string in the font a block will actually be drawn in.

    Built once per block from its ``font_family`` / ``font_weight`` / ``font_style`` and reused
    across the wrap and shrink loops (the font size varies, so ``width`` takes ``font_pt``). When
    the font cannot be loaded, every call returns the proportional ``char_px`` estimate, so a
    measurer is always safe to construct and call.
    """

    def __init__(
        self,
        dpi: float,
        family: Optional[str] = None,
        weight: str = "normal",
        style: str = "normal",
    ) -> None:
        self.dpi = float(dpi)
        self._path = _resolve_font_path(family, weight or "normal", style or "normal")

    def width(self, text: str, font_pt: float) -> float:
        """Rendered width of ``text`` at ``font_pt``, in device px. Falls back to the estimate."""
        if not text:
            return 0.0
        estimate = len(text) * char_px(font_pt, self.dpi)
        if self._path is None:
            return estimate
        size_px = max(1, round(pt_to_px(font_pt, self.dpi)))
        font = _pil_font(self._path, size_px)
        if font is None:
            return estimate
        try:
            return float(font.getlength(text))
        except Exception:
            return estimate
