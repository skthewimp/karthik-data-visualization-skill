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


def test_fraction_out_of_range_is_clamped_with_warning():
    out = read_marks_from_anchors([{"key": "a", "lo": 40, "hi": 60, "fraction": 1.3}])
    assert out["results"][0]["value"] == pytest.approx(60.0)
    assert any("outside [0,1]" in w for w in out["warnings"])


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
