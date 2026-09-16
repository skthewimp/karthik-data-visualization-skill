import math

import pytest

from dataviz_mcp.mark_read import read_marks_from_anchors


def test_linear_interpolation_midpoint():
    out = read_marks_from_anchors([{"key": "a", "lo": 40, "hi": 60, "fraction": 0.5}])
    assert out["results"][0]["value"] == pytest.approx(50.0)
    assert out["warnings"] == []


def test_linear_interpolation_three_fifths():
    out = read_marks_from_anchors([{"key": "a", "lo": 40, "hi": 60, "fraction": 0.6}])
    assert out["results"][0]["value"] == pytest.approx(52.0)


def test_log_interpolation_is_geometric_midpoint():
    # Halfway between 10 and 1000 on a log axis is 100, not 505.
    out = read_marks_from_anchors(
        [{"key": "a", "lo": 10, "hi": 1000, "fraction": 0.5}], transform="log"
    )
    assert out["results"][0]["value"] == pytest.approx(100.0)


def test_batch_preserves_order_and_keys():
    marks = [
        {"key": "2019|s1", "lo": 0, "hi": 100, "fraction": 0.25},
        {"key": "2019|s2", "lo": 0, "hi": 100, "fraction": 0.75},
    ]
    out = read_marks_from_anchors(marks)
    assert [r["key"] for r in out["results"]] == ["2019|s1", "2019|s2"]
    assert out["results"][0]["value"] == pytest.approx(25.0)
    assert out["results"][1]["value"] == pytest.approx(75.0)


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
