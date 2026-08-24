from dataviz_mcp.color_math import (
    _contrast_ratio,
    grayscale_value,
    hue_delta,
    lightness_delta,
    simulate_cvd,
)


def test_contrast_ratio_black_on_white_is_21():
    assert round(_contrast_ratio("#000000", "#FFFFFF"), 1) == 21.0


def test_contrast_ratio_unparseable_returns_none():
    assert _contrast_ratio("not-a-colour", "#FFFFFF") is None


def test_hue_and_lightness_deltas():
    assert hue_delta("#FF0000", "#00FF00") > 100  # red vs green far apart in hue
    assert lightness_delta("#000000", "#FFFFFF") > 0.9


def test_simulate_cvd_returns_rgb_triple():
    out = simulate_cvd("#D55E00", "deuteranope")
    assert out is not None and len(out) == 3
    assert all(0 <= channel <= 255 for channel in out)


def test_grayscale_orders_by_luminance():
    assert grayscale_value("#FFFFFF") > grayscale_value("#000000")
