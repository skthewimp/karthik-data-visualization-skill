from dataviz_mcp.precision import recommend_precision


def test_precision_derived_from_range_not_individual_values():
    result = recommend_precision([12483, 9210, 15040])
    # range ~5830 -> two sig figs of the range -> round to hundreds.
    assert result["recommended_place"] == 2
    assert [p["shown"] for p in result["preview"]] == ["12,500", "9,200", "15,000"]


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


def test_default_precision_is_not_an_exact_override():
    result = recommend_precision([12483, 9210, 15040])
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
