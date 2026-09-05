from dataviz_mcp.labels import recommend_labels


def test_short_series_is_labelled_in_full():
    result = recommend_labels([{"id": "a", "values": [1, 2, 3]}], max_labels_per_series=4)
    entry = result["per_series"][0]
    assert entry["label_indices"] == [0, 1, 2]
    assert entry["labelled"] == 3


def test_long_series_labels_endpoints_and_extremes_within_budget():
    values = [10, 12, 40, 11, 9, 13, 8, 30, 7, 6]
    result = recommend_labels([{"id": "a", "values": values}], max_labels_per_series=4)
    entry = result["per_series"][0]
    assert entry["labelled"] == 4
    assert 0 in entry["label_indices"]  # start endpoint
    assert 9 in entry["label_indices"]  # end endpoint
    assert 2 in entry["label_indices"]  # maximum (40)


def test_skips_non_numeric_but_preserves_positions():
    result = recommend_labels([{"id": "a", "values": [1, None, "x", 5, 9]}], max_labels_per_series=4)
    entry = result["per_series"][0]
    assert entry["total"] == 3  # three finite values
    assert all(isinstance(i, int) for i in entry["label_indices"])
