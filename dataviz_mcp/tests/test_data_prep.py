from __future__ import annotations

# ---- from test_plot_data.py ----

import csv
from pathlib import Path

import pytest

from dataviz_mcp.plot_data import prepare_plot_data


def _read(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_only_mapped_columns_survive_helper_column_cannot_leak(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["region", "sales", "_internal_id", "note"],
        rows=[["North", "10", "x1", "hi"], ["South", "20", "x2", "yo"]],
        x="region",
        value="sales",
    )
    assert result["dropped_columns"] == ["_internal_id", "note"]
    frame = _read(result["plot_data_path"])
    assert set(frame[0].keys()) == {"order", "category", "value"}
    assert [r["category"] for r in frame] == ["North", "South"]


def test_category_value_association_is_fixed_by_role_map(tmp_path):
    # value maps to sales regardless of column position - no reversal possible.
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["sales", "region"],
        rows=[["10", "North"], ["20", "South"]],
        x="region",
        value="sales",
    )
    frame = _read(result["plot_data_path"])
    assert {r["category"]: r["value"] for r in frame} == {"North": "10.0", "South": "20.0"}


def test_one_canonical_order_shared_via_explicit_order_column(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["q", "v"],
        rows=[["Q3", "3"], ["Q1", "1"], ["Q2", "2"]],
        x="q",
        value="v",
        category_order=["Q1", "Q2", "Q3"],
    )
    frame = _read(result["plot_data_path"])
    assert [r["category"] for r in frame] == ["Q1", "Q2", "Q3"]
    assert [int(r["order"]) for r in frame] == [0, 1, 2]
    assert result["category_order"] == ["Q1", "Q2", "Q3"]


def test_series_kept_and_ordered(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["yr", "party", "seats"],
        rows=[["2020", "A", "5"], ["2020", "B", "7"], ["2021", "A", "6"], ["2021", "B", "8"]],
        x="yr",
        value="seats",
        series="party",
    )
    frame = _read(result["plot_data_path"])
    assert set(frame[0].keys()) == {"order", "category", "series", "value"}
    assert result["series_order"] == ["A", "B"]
    assert len(frame) == 4


def test_categories_missing_from_explicit_order_are_appended_not_dropped(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "v"],
        rows=[["a", "1"], ["b", "2"], ["c", "3"]],
        x="k",
        value="v",
        category_order=["a", "b"],
    )
    assert result["category_order"] == ["a", "b", "c"]
    assert any("appended" in w for w in result["warnings"])


def test_duplicate_keys_without_aggregate_raise(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        prepare_plot_data(
            output_dir=str(tmp_path),
            columns=["k", "v"],
            rows=[["a", "1"], ["a", "2"]],
            x="k",
            value="v",
        )


def test_duplicate_keys_aggregate_sum(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "v"],
        rows=[["a", "1"], ["a", "2"], ["b", "5"]],
        x="k",
        value="v",
        aggregate="sum",
    )
    frame = _read(result["plot_data_path"])
    assert {r["category"]: r["value"] for r in frame} == {"a": "3.0", "b": "5.0"}


def test_missing_mapped_column_raises(tmp_path):
    with pytest.raises(ValueError, match="not in the data"):
        prepare_plot_data(
            output_dir=str(tmp_path),
            columns=["k", "v"],
            rows=[["a", "1"]],
            x="k",
            value="nope",
        )


def test_non_numeric_value_dropped_with_warning(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "v"],
        rows=[["a", "1"], ["b", "NA"]],
        x="k",
        value="v",
    )
    assert result["n_rows"] == 1
    assert any("non-numeric" in w for w in result["warnings"])


def test_qualified_values_kept_as_numeric(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "v"],
        rows=[
            ["a", "95.0"],
            ["b", "approximately 4.3"],
            ["c", "~0.5"],
            ["d", "50.2%"],
            ["e", "1,234"],
        ],
        x="k",
        value="v",
    )
    frame = _read(result["plot_data_path"])
    assert {r["category"]: float(r["value"]) for r in frame} == {
        "a": 95.0,
        "b": 4.3,
        "c": 0.5,
        "d": 50.2,
        "e": 1234.0,
    }
    assert result["n_rows"] == 5
    assert result["warnings"] == []


def test_reads_from_dataset_path(tmp_path):
    src = tmp_path / "data.csv"
    with src.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["region", "sales", "helper"])
        writer.writerow(["North", "10", "junk"])
        writer.writerow(["South", "20", "junk"])
    out = tmp_path / "out"
    result = prepare_plot_data(
        output_dir=str(out),
        dataset_path=str(src),
        x="region",
        value="sales",
    )
    assert result["dropped_columns"] == ["helper"]
    frame = _read(result["plot_data_path"])
    assert {r["category"]: r["value"] for r in frame} == {"North": "10.0", "South": "20.0"}


def test_facets_kept_and_ordered(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["panel", "k", "v"],
        rows=[["P1", "a", "1"], ["P2", "a", "2"], ["P1", "b", "3"], ["P2", "b", "4"]],
        x="k",
        value="v",
        facet="panel",
    )
    frame = _read(result["plot_data_path"])
    assert set(frame[0].keys()) == {"order", "category", "facet", "value"}
    # canonical order groups by facet first
    assert [r["facet"] for r in frame] == ["P1", "P1", "P2", "P2"]


def test_wide_value_columns_melt_into_series_named_by_column(tmp_path):
    # A 3-model wide frame: each value column becomes a series, no hand-built inline frame.
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["prompt", "gpt", "claude", "llama"],
        rows=[["p1", "10", "12", "8"], ["p2", "20", "18", "15"]],
        x="prompt",
        value=["gpt", "claude", "llama"],
    )
    frame = _read(result["plot_data_path"])
    assert set(frame[0].keys()) == {"order", "category", "series", "value"}
    assert result["series_order"] == ["gpt", "claude", "llama"]
    assert len(frame) == 6
    assert {(r["category"], r["series"]): r["value"] for r in frame}[("p1", "claude")] == "12.0"
    # canonical order: category first, then series in value-column order
    assert [(r["category"], r["series"]) for r in frame][:3] == [
        ("p1", "gpt"), ("p1", "claude"), ("p1", "llama")
    ]


def test_single_element_value_list_matches_scalar(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "v"],
        rows=[["a", "1"], ["b", "2"]],
        x="k",
        value=["v"],
    )
    frame = _read(result["plot_data_path"])
    assert set(frame[0].keys()) == {"order", "category", "value"}
    assert [r["category"] for r in frame] == ["a", "b"]


def test_wide_value_and_series_column_are_mutually_exclusive(tmp_path):
    with pytest.raises(ValueError, match="mutually exclusive"):
        prepare_plot_data(
            output_dir=str(tmp_path),
            columns=["k", "grp", "a", "b"],
            rows=[["x", "g1", "1", "2"]],
            x="k",
            value=["a", "b"],
            series="grp",
        )


def test_wide_value_column_not_in_data_raises(tmp_path):
    with pytest.raises(ValueError, match="mapped column"):
        prepare_plot_data(
            output_dir=str(tmp_path),
            columns=["k", "a"],
            rows=[["x", "1"]],
            x="k",
            value=["a", "missing"],
        )


def test_wide_series_order_can_be_pinned(tmp_path):
    result = prepare_plot_data(
        output_dir=str(tmp_path),
        columns=["k", "a", "b"],
        rows=[["x", "1", "2"]],
        x="k",
        value=["a", "b"],
        series_order=["b", "a"],
    )
    assert result["series_order"] == ["b", "a"]

# ---- from test_labels.py ----

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
    # The series is named once, at its line end; the other chosen points print values alone.
    assert entry["name_index"] == 9


def test_skips_non_numeric_but_preserves_positions():
    result = recommend_labels([{"id": "a", "values": [1, None, "x", 5, 9]}], max_labels_per_series=4)
    entry = result["per_series"][0]
    assert entry["total"] == 3  # three finite values
    assert all(isinstance(i, int) for i in entry["label_indices"])


# ---- interval and label-measure roles ----

import json

from dataviz_mcp.plot_data import default_plot_data_map

SHARES = ["panel", "part", "share", "from", "to", "printed"]
SHARE_ROWS = [
    ["tokens", "reads", 95, 0, 95, "95.0%"],
    ["tokens", "writes", 4.3, 95, 99.3, ""],
    ["dollars", "reads", 50.2, 0, 50.2, "50.2%"],
    ["dollars", "input", None, 99.2, None, ""],
]


def test_interval_ends_are_emitted_as_read_and_a_missing_end_stays_blank(tmp_path):
    result = prepare_plot_data(
        str(tmp_path), x="panel", series="part", start="from", end="to", columns=SHARES, rows=SHARE_ROWS,
    )
    frame = _read(result["plot_data_path"])
    assert result["geometry"] == "interval"
    assert "value" not in frame[0] and {"start", "end"} <= set(frame[0])
    input_row = [r for r in frame if r["series"] == "input"][0]
    # Nothing derived: the unread end is not filled from 100 - 99.2 or anything else.
    assert input_row["start"] == "99.2" and input_row["end"] == ""
    assert any("missing an end" in w for w in result["warnings"])


def test_label_measures_ride_on_their_row_in_their_own_units(tmp_path):
    result = prepare_plot_data(
        str(tmp_path), x="panel", value="share", series="part", columns=SHARES, rows=SHARE_ROWS[:3],
        labels={"printed share": {"column": "printed", "suffix": "%"}},
    )
    frame = _read(result["plot_data_path"])
    assert [r["printed_share"] for r in frame] == ["95.0", "", "50.2"]
    # A label measure never becomes a series.
    assert result["series_order"] == ["reads", "writes"]
    roles = json.loads(Path(result["roles_path"]).read_text())
    assert roles["labels"]["printed_share"]["suffix"] == "%"


def test_a_label_measure_cannot_take_a_canonical_name(tmp_path):
    with pytest.raises(ValueError, match="reserved"):
        prepare_plot_data(str(tmp_path), x="panel", value="share", columns=SHARES, rows=SHARE_ROWS[:1],
                          labels={"value": "printed"})


def test_intervals_are_never_aggregated(tmp_path):
    with pytest.raises(ValueError, match="not aggregated"):
        prepare_plot_data(str(tmp_path), x="panel", start="from", end="to", columns=SHARES,
                          rows=SHARE_ROWS[:2], aggregate="sum")


def test_default_map_keeps_numbers_off_the_series():
    mapping = default_plot_data_map(SHARES, SHARE_ROWS)
    assert mapping["x"] == "panel" and mapping["series"] == "part" and mapping["value"] == "share"
    # Printed "95.0%" is a number; it and the ends ride along as label measures, never as keys.
    assert set(mapping["labels"].values()) == {"from", "to", "printed"}


def test_default_map_reads_a_quarter_label_as_text():
    mapping = default_plot_data_map(["period", "revenue"], [["Q1'24", "$70,398"], ["Q1'25", "$77,264"]])
    assert mapping == {"x": "period", "value": "revenue"}
