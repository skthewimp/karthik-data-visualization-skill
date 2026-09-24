"""Deterministic colour maths shared by inspection and palette tools.

WCAG relative-luminance and contrast live here so a single implementation backs
both the geometry inspector (text-vs-background) and the palette tools
(series distinctness, CVD, grayscale).
"""

from __future__ import annotations

import colorsys
from typing import Optional

from PIL import ImageColor


def to_rgb(colour: str) -> Optional[tuple[int, int, int]]:
    """Parse a hex/named/rgb() colour string to an 0-255 RGB triple, or None."""
    try:
        red, green, blue, _ = ImageColor.getcolor(colour, "RGBA")
    except (ValueError, TypeError):
        return None
    return red, green, blue


def _relative_luminance(colour: str) -> Optional[float]:
    rgb = to_rgb(colour)
    if rgb is None:
        return None
    channels = []
    for value in rgb:
        scaled = value / 255
        channels.append(scaled / 12.92 if scaled <= 0.04045 else ((scaled + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(first: Optional[str], second: Optional[str]) -> Optional[float]:
    if not first or not second:
        return None
    a = _relative_luminance(first)
    b = _relative_luminance(second)
    if a is None or b is None:
        return None
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_ratio_rgb(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    """Contrast ratio between two already-parsed RGB triples."""

    def lum(rgb: tuple[int, int, int]) -> float:
        channels = []
        for value in rgb:
            scaled = value / 255
            channels.append(
                scaled / 12.92 if scaled <= 0.04045 else ((scaled + 0.055) / 1.055) ** 2.4
            )
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    a, b = lum(first), lum(second)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def hue_lightness(colour: str) -> Optional[tuple[float, float]]:
    """Return (hue in [0,360), lightness in [0,1]) via HLS, or None if unparseable."""
    rgb = to_rgb(colour)
    if rgb is None:
        return None
    r, g, b = (value / 255 for value in rgb)
    hue, lightness, _ = colorsys.rgb_to_hls(r, g, b)
    return hue * 360.0, lightness


def hue_delta(first: str, second: str) -> Optional[float]:
    """Smallest circular hue distance in degrees [0,180], or None."""
    a = hue_lightness(first)
    b = hue_lightness(second)
    if a is None or b is None:
        return None
    diff = abs(a[0] - b[0]) % 360.0
    return min(diff, 360.0 - diff)


def lightness_delta(first: str, second: str) -> Optional[float]:
    """Absolute lightness difference in [0,1], or None."""
    a = hue_lightness(first)
    b = hue_lightness(second)
    if a is None or b is None:
        return None
    return abs(a[1] - b[1])


# Colour-vision-deficiency simulation. Machado et al. (2009) severity-1.0 matrices
# applied in linear-ish sRGB; adequate for the "do two series still separate?" check.
_CVD_MATRICES = {
    "deuteranope": (
        (0.367, 0.861, -0.228),
        (0.280, 0.673, 0.047),
        (-0.012, 0.043, 0.969),
    ),
    "protanope": (
        (0.152, 1.053, -0.205),
        (0.115, 0.786, 0.099),
        (-0.004, -0.048, 1.052),
    ),
    "tritanope": (
        (1.256, -0.077, -0.179),
        (-0.078, 0.931, 0.148),
        (0.005, 0.691, 0.304),
    ),
}


def simulate_cvd(colour: str, kind: str) -> Optional[tuple[int, int, int]]:
    """Simulate how `colour` looks under a colour-vision deficiency, as RGB 0-255."""
    rgb = to_rgb(colour)
    if rgb is None or kind not in _CVD_MATRICES:
        return None
    matrix = _CVD_MATRICES[kind]
    out = []
    for row in matrix:
        value = sum(component * channel for component, channel in zip(row, rgb))
        out.append(int(max(0, min(255, round(value)))))
    return tuple(out)  # type: ignore[return-value]


def grayscale_value(colour: str) -> Optional[float]:
    """Perceptual grayscale (relative luminance scaled to 0-255), or None."""
    lum = _relative_luminance(colour)
    if lum is None:
        return None
    return lum * 255.0


def better_ink(surface: str, ink_light: str = "#ffffff", ink_dark: str = "#1a1a1a") -> tuple[str, float]:
    """The text ink (light or dark) with the higher WCAG contrast against ``surface``, and that ratio.

    Text on a mark takes its legibility from the mark's fill, not the page. An unparseable
    surface defaults to dark ink with contrast unknown (0.0).
    """
    light_c = _contrast_ratio(ink_light, surface)
    dark_c = _contrast_ratio(ink_dark, surface)
    if light_c is None or dark_c is None:
        return ink_dark, 0.0
    return (ink_light, light_c) if light_c >= dark_c else (ink_dark, dark_c)


def text_ink(colour: str, background: str = "#ffffff", target: float = 4.5) -> str:
    """The colour as text on ``background``: same hue and saturation, lightness moved away from the
    background until it reads at ``target``. A series colour light enough for a bar is often too
    light for the words that name it; the words keep the hue so the key still matches the marks.
    """
    rgb, back = to_rgb(colour), _relative_luminance(background)
    if rgb is None or back is None or (_contrast_ratio(colour, background) or 0) >= target:
        return colour
    import colorsys

    h, l, s = colorsys.rgb_to_hls(*(c / 255.0 for c in rgb))
    step = -0.01 if back > 0.18 else 0.01
    candidate = colour
    while 0.0 <= l <= 1.0 and (_contrast_ratio(candidate, background) or 0) < target:
        l += step
        r, g, b = colorsys.hls_to_rgb(h, min(1.0, max(0.0, l)), s)
        candidate = "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))
    return candidate
