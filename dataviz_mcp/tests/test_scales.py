from __future__ import annotations

import pytest

from dataviz_mcp.mark_read import read_marks_from_anchors
from dataviz_mcp.precision import recommend_precision
from dataviz_mcp.scale_transform import recommend_scale_transform


# ---- scale transform ----


def test_wide_positive_spread_on_position_marks_recommends_log():
    # Six orders of magnitude, right-skewed - the classic income/wealth shape.
    values = [1, 3, 8, 20, 60, 200, 900, 5000, 40000, 800000]
    result = recommend_scale_transform(values, encoding="position")
    assert result["recommendation"] == "log"
    assert result["transform"] == "log10"
    assert result["applicable"] is True
    assert result["signals"]["orders_of_magnitude"] > 2
    assert result["strength"] >= 0.5

    assert result["caveats"]


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


def test_too_few_values_is_weak_and_linear():
    result = recommend_scale_transform([100], encoding="position")
    assert result["applicable"] is False
    assert result["recommendation"] == "linear"
    assert result["strength"] == 0.0


def test_strength_rises_with_spread():
    narrow = recommend_scale_transform([10, 20, 30, 40, 50], encoding="position")["strength"]
    wide = recommend_scale_transform([1, 100, 10000, 1000000], encoding="position")["strength"]
    assert wide > narrow

# ---- precision ----


def test_nonzero_value_never_collapses_to_zero():
    # A small unit cost beside large counts: the spread place would round it to "0".
    result = recommend_precision([1653, 0.019], role="label")
    shown = {p["value"]: p["shown"] for p in result["preview"]}
    assert float(shown[0.019].replace(",", "")) != 0.0
    assert result["zero_collapse_prevented"] is True

    assert [p["compact"] for p in result["preview"]] == [p["shown"] for p in result["preview"]]


def test_zero_collapse_guard_never_exceeds_source_digits():
    result = recommend_precision([1000, 0.5], role="label")
    # 0.5 needs one decimal; the guard must not invent digits beyond the source.
    assert result["decimals"] <= 1


def test_precision_derived_from_range_not_individual_values():
    result = recommend_precision([12483, 9210, 15040])
    # range ~5830 -> two sig figs of the range -> round to hundreds.
    assert result["recommended_place"] == 2
    assert [p["shown"] for p in result["preview"]] == ["12,500", "9,200", "15,000"]

    assert result["zero_collapse_prevented"] is False
    assert result["exact_override"] is False


def test_precision_uniform_place_across_column():
    result = recommend_precision([1.02, 1.44, 1.09])
    places = {len(p["shown"].split(".")[1]) for p in result["preview"]}
    assert len(places) == 1  # every value shown with the same number of decimals


def test_precision_honours_explicit_smallest_difference():
    result = recommend_precision([100, 200, 300], smallest_meaningful_difference=1)
    assert result["recommended_place"] == 0


def test_precision_all_equal_uses_magnitude():
    result = recommend_precision([5000, 5000])
    assert result["recommended_place"] is not None
    assert result["preview"][0]["shown"] == result["preview"][1]["shown"]


def test_precision_empty_column_reports_error():
    result = recommend_precision([])
    assert result["recommended_place"] is None
    assert "error" in result
    assert result["exact_override"] is False


def test_exact_override_preserves_every_source_digit_and_flags_itself():
    # Same values that the spread rule would coarsen to hundreds.
    result = recommend_precision([12483, 9210, 15040], role="table_column", exact=True)
    assert result["exact_override"] is True
    assert [p["shown"] for p in result["preview"]] == ["12,483", "9,210", "15,040"]


def test_exact_override_keeps_decimals_the_spread_would_drop():
    result = recommend_precision([1.02, 1.44, 1.09], exact=True)
    assert result["exact_override"] is True
    assert result["recommended_place"] == -2  # hundredths preserved
    assert [p["shown"] for p in result["preview"]] == ["1.02", "1.44", "1.09"]

# ---- mark read ----


def test_log_interpolation_is_geometric_midpoint():
    # Halfway between 10 and 1000 on a log axis is 100, not 505.
    out = read_marks_from_anchors(
        [{"key": "a", "lo": 10, "hi": 1000, "fraction": 0.5}], transform="log"
    )
    assert out["results"][0]["value"] == pytest.approx(100.0)


def test_linear_interpolation_preserves_batch_order_and_keys():
    marks = [
        {"key": "2019|s1", "lo": 40, "hi": 60, "fraction": 0.5},
        {"key": "2019|s2", "lo": 40, "hi": 60, "fraction": 0.6},
    ]
    out = read_marks_from_anchors(marks)
    assert [r["key"] for r in out["results"]] == ["2019|s1", "2019|s2"]
    assert out["results"][0]["value"] == pytest.approx(50.0)
    assert out["results"][1]["value"] == pytest.approx(52.0)
    assert out["warnings"] == []


def test_descending_bracket_reads_from_lo_toward_hi():
    # A reversed axis: fraction runs from lo (60) toward hi (40), so 0.6 -> 48. No warning.
    out = read_marks_from_anchors([{"key": "a", "lo": 60, "hi": 40, "fraction": 0.6}])
    assert out["results"][0]["value"] == pytest.approx(48.0)
    assert out["warnings"] == []


def test_modest_extrapolation_below_lowest_tick_is_honoured():
    # A point just below the bottom gridline: fraction slightly negative, value below lo. No warning.
    out = read_marks_from_anchors([{"key": "a", "lo": 10, "hi": 15, "fraction": -0.12}])
    assert out["results"][0]["value"] == pytest.approx(9.4)
    assert out["warnings"] == []


def test_modest_extrapolation_above_top_tick_is_honoured():
    # A labelled peak above the top gridline: fraction > 1, value above hi. No warning.
    out = read_marks_from_anchors([{"key": "a", "lo": 20, "hi": 25, "fraction": 1.37}])
    assert out["results"][0]["value"] == pytest.approx(26.85)
    assert out["warnings"] == []


def test_gross_out_of_range_warns_but_still_returns_value():
    out = read_marks_from_anchors([{"key": "a", "lo": 40, "hi": 60, "fraction": 3.0}])
    assert out["results"][0]["value"] == pytest.approx(100.0)
    assert any("far outside the bracket" in w for w in out["warnings"])


def test_equal_anchors_yield_none():
    out = read_marks_from_anchors([{"key": "a", "lo": 50, "hi": 50, "fraction": 0.5}])
    assert out["results"][0]["value"] is None
    assert any("equal anchors" in w for w in out["warnings"])


def test_log_requires_positive_anchors():
    out = read_marks_from_anchors(
        [{"key": "a", "lo": 0, "hi": 100, "fraction": 0.5}], transform="log"
    )
    assert out["results"][0]["value"] is None
    assert any("positive anchors" in w for w in out["warnings"])


def test_missing_field_skips_mark_without_crashing():
    out = read_marks_from_anchors([{"key": "a", "lo": 40, "fraction": 0.5}])
    assert out["results"][0]["value"] is None
    assert any("missing or non-numeric" in w for w in out["warnings"])


def test_invalid_transform_raises():
    with pytest.raises(ValueError):
        read_marks_from_anchors([], transform="sqrt")


def test_compact_form_scales_a_pre_scaled_column() -> None:
    result = recommend_precision([70398, 77264], role="label", unit_multiplier=1e6)
    assert [p["compact"] for p in result["preview"]] == ["70.4B", "77.3B"]
    assert result["compact_suffix"] == "B"
    assert result["compact_step"] == "0.1B"


def test_compact_unit_suits_the_smallest_value() -> None:
    result = recommend_precision([11, 64, 162, 1653], role="label")
    assert [p["compact"] for p in result["preview"]] == ["10", "60", "160", "1,650"]


def test_integer_source_never_gains_a_decimal() -> None:
    result = recommend_precision([38, 43], role="label")
    assert [p["shown"] for p in result["preview"]] == ["38", "43"]
