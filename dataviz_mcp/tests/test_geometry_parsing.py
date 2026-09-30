from __future__ import annotations

from dataviz_mcp.rendering import _cell_bbox_field, _geometry_gap_message, _parse_finite, _row_bbox


def test_parse_finite_reads_numbers_and_treats_blanks_na_and_infinities_as_unavailable():
    assert _parse_finite("12.5") == 12.5
    assert _parse_finite(3) == 3.0
    assert _parse_finite("-4") == -4.0
    for token in ("", " ", "NA", "na", "NaN", "null", "None", None, "Inf", "-Inf", "+inf",
                  float("nan"), float("inf")):
        assert _parse_finite(token) is None, token


def test_row_bbox_returns_rounded_bbox_when_all_bounds_finite():
    bbox, missing = _row_bbox({"x": "1.0001", "y": "2", "width": "3", "height": "4"})
    assert missing == []
    assert bbox == {"x": 1.0, "y": 2.0, "width": 3.0, "height": 4.0}


def test_censored_rectangle_reports_missing_width_without_zeroing():
    bbox, missing = _row_bbox({"x": "10", "y": "20", "width": "", "height": "5"})
    assert bbox is None
    assert missing == ["width"]


def test_infinite_reference_bound_is_unavailable_not_a_crash():
    bbox, missing = _row_bbox({"x": "-Inf", "y": "0", "width": "Inf", "height": "2"})
    assert bbox is None
    assert missing == ["x", "width"]


def test_gap_message_names_a_cause_to_check_without_asserting_it():
    message = _geometry_gap_message(
        {"id": "geom_rect.1/rect.3", "kind": "rect", "missing": ["width"]}
    )
    assert "Rectangle geom_rect.1/rect.3 has unavailable width" in message
    assert "scale limits censored its boundary" in message
    assert "does not prove that cause" in message


def test_cell_bbox_read_only_for_table_rows_with_four_finite_bounds():
    assert _cell_bbox_field({"x_points": "1;2;3;4"}, "table") == {
        "cell_bbox": {"x": 1.0, "y": 2.0, "width": 3.0, "height": 4.0}
    }
    assert _cell_bbox_field({"x_points": "1;2;3;"}, "table") == {}
    assert _cell_bbox_field({"x_points": "1;2;3;4"}, "chart") == {}
