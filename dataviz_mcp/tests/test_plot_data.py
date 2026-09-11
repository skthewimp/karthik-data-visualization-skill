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
