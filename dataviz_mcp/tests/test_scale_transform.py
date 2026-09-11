import math

from dataviz_mcp.scale_transform import recommend_scale_transform


def test_wide_positive_spread_on_position_marks_recommends_log():
    # Six orders of magnitude, right-skewed - the classic income/wealth shape.
    values = [1, 3, 8, 20, 60, 200, 900, 5000, 40000, 800000]
    result = recommend_scale_transform(values, encoding="position")
    assert result["recommendation"] == "log"
    assert result["transform"] == "log10"
    assert result["applicable"] is True
    assert result["signals"]["orders_of_magnitude"] > 2
    assert result["strength"] >= 0.5


def test_narrow_spread_stays_linear():
    values = [42, 45, 47, 44, 46, 43, 48, 45]
    result = recommend_scale_transform(values, encoding="position")
    assert result["recommendation"] == "linear"
    assert result["transform"] == "identity"
    assert result["strength"] < 0.5


def test_length_encoding_never_gets_log_even_on_wide_spread():
    values = [1, 10, 100, 1000, 10000, 100000]
    result = recommend_scale_transform(values, encoding="length")
    assert result["recommendation"] == "linear"
    assert result["confidence"] == "strong"
    # The spread is still reported so the model can switch the mark instead.
    assert result["signals"]["orders_of_magnitude"] > 2


def test_non_positive_values_make_log_inapplicable():
    values = [-5, 0, 10, 100, 5000, 90000]
    result = recommend_scale_transform(values, encoding="position")
    assert result["applicable"] is False
    assert result["recommendation"] == "linear"
    assert result["signals"]["n_nonpositive"] == 2
    # symlog is noted, never recommended.
    assert "recommendation" in result and result["transform"] == "identity"
    assert "symlog_note" in result


def test_log_recommendation_carries_axis_labelling_caveats():
    values = [1, 5, 30, 200, 1500, 12000, 90000]
    result = recommend_scale_transform(values, encoding="position")
    assert result["recommendation"] == "log"
    joined = " ".join(result["caveats"]).lower()
    assert "log" in joined and "override" in joined


def test_too_few_values_is_weak_and_linear():
    result = recommend_scale_transform([100], encoding="position")
    assert result["applicable"] is False
    assert result["recommendation"] == "linear"
    assert result["strength"] == 0.0


def test_strength_rises_with_spread():
    narrow = recommend_scale_transform([10, 20, 30, 40, 50], encoding="position")["strength"]
    wide = recommend_scale_transform([1, 100, 10000, 1000000], encoding="position")["strength"]
    assert wide > narrow
