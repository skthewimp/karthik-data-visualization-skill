from dataviz_mcp.axis import recommend_axis_range


def test_percentage_extent_does_not_earn_a_0_100_axis():
    # The bollywood regression: values run 1-44, a build model reflexively used 0-100.
    result = recommend_axis_range([44, 43, 41, 40, 39, 38, 36, 34, 25, 24, 15, 9, 8, 3, 1])
    assert result["recommended_min"] == 0
    assert result["recommended_max"] < 60  # fitted just above 44, nowhere near 100
    assert result["recommended_max"] >= 44  # but the top mark is contained


def test_zero_based_includes_zero():
    result = recommend_axis_range([20, 35, 44], zero_based=True)
    assert result["recommended_min"] == 0


def test_movement_band_line_drops_the_zero_baseline():
    # A narrow-band line whose story is movement: a zero baseline would flatten it.
    result = recommend_axis_range([98.1, 98.6, 99.0, 99.4], zero_based=False)
    assert result["recommended_min"] > 90


def test_hard_max_honoured_and_flagged():
    result = recommend_axis_range([1, 44], zero_based=True, hard_max=100)
    assert result["recommended_max"] == 100
    assert result["hard_max_applied"] is True
    # A hard max far above the data is flagged, not silent.
    assert "Warning" in result["rationale"]


def test_top_mark_is_never_on_the_frame_edge():
    # A max that lands exactly on the data gets a step of headroom.
    result = recommend_axis_range([0, 50], zero_based=True)
    assert result["recommended_max"] > 50
    assert result["headroom_fraction"] > 0


def test_breaks_span_the_frame_inclusive():
    result = recommend_axis_range([1, 44])
    breaks = result["breaks"]
    assert breaks[0] == result["recommended_min"]
    assert breaks[-1] == result["recommended_max"]


def test_single_value_opens_a_band():
    result = recommend_axis_range([42], zero_based=True)
    assert result["recommended_min"] == 0
    assert result["recommended_max"] > 42


def test_empty_values_raise():
    try:
        recommend_axis_range([])
    except ValueError:
        return
    raise AssertionError("empty values must raise")
