"""Prepare the plotting frame mechanically, so the builder reshapes nothing.

A weak build model that hand-builds its dataframe inline in the chart code makes two
recurring mistakes: it reverses a category/value association (plots the wrong column on the
wrong axis), and it lets an internal helper column leak in as a plotted series. Both are
determinism failures, not judgement calls - so they are removed in code, not warned against
in a prompt.

``prepare_plot_data`` takes the data (a file for dataset-to-story, or the recovered
``columns``/``rows`` already carried in a repair artifact) plus a role map naming which column
is the category/x, the value, the optional series and facet. It:

* keeps ONLY the mapped columns - an unmapped helper column cannot become a series;
* emits one tidy long-format frame with fixed canonical names (``category`` / ``value`` /
  ``series`` / ``facet``), so the builder always reads the same columns regardless of source;
* pins ONE canonical ordering (an explicit ``order`` column plus the row order) shared by every
  mark and every label, so a value stamped on a mark can never drift onto the wrong category.

The builder loads the returned file and plots it directly. It is the fourth mechanical
resolution beside ``recommend_colours`` / ``recommend_precision`` / ``reserve_frame``: a
decision made at ``select`` (the role map), resolved by a deterministic tool, applied at
``build`` (read the file) - never re-derived by the model.

Stdlib only (``csv``), matching the rest of the mechanical layer.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Optional

_AGGREGATORS = {
    "sum": lambda vals: sum(vals),
    "mean": lambda vals: sum(vals) / len(vals),
    "min": lambda vals: min(vals),
    "max": lambda vals: max(vals),
    "first": lambda vals: vals[0],
    "last": lambda vals: vals[-1],
}


def _load_records(
    dataset_path: Optional[str],
    columns: Optional[list[str]],
    rows: Optional[list[list[Any]]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Load the source as a header and a list of row dicts, from a file or inline table."""
    if dataset_path:
        path = Path(dataset_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"dataset_path does not exist: {dataset_path}")
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            records = [dict(row) for row in reader]
        return header, records
    if columns and rows is not None:
        header = list(columns)
        records = [dict(zip(header, row)) for row in rows]
        return header, records
    raise ValueError("Provide either dataset_path or both columns and rows.")


def _ordered(seen: list[str], explicit: Optional[list[str]]) -> tuple[list[str], list[str]]:
    """Canonical order for a key: explicit first (extras appended), else first-appearance.

    Returns the order and any values seen in the data but missing from an explicit list -
    they are appended (never dropped) and reported so a stale order is visible, not silent.
    """
    if not explicit:
        return seen, []
    tail = [value for value in seen if value not in explicit]
    order = [value for value in explicit if value in seen] + tail
    return order, tail


def prepare_plot_data(
    output_dir: str,
    x: str,
    value: str,
    dataset_path: Optional[str] = None,
    columns: Optional[list[str]] = None,
    rows: Optional[list[list[Any]]] = None,
    series: Optional[str] = None,
    facet: Optional[str] = None,
    category_order: Optional[list[str]] = None,
    series_order: Optional[list[str]] = None,
    aggregate: Optional[str] = None,
) -> dict[str, Any]:
    """Reshape the source into a tidy plotting frame with a whitelist and one canonical order.

    Reads the data from ``dataset_path`` (dataset-to-story) or inline ``columns``/``rows`` (a
    repair artifact's recovered table), keeps only the mapped columns, coerces ``value`` to a
    number, aggregates duplicate keys when told how, and writes a long-format
    ``plot-data.csv`` in canonical order. The builder reads that file and reshapes nothing.

    Args:
        output_dir: directory the tidy frame is written into.
        x: source column that is the category / x position (required).
        value: source column that is the numeric value (required).
        dataset_path: a CSV to read (dataset-to-story path).
        columns / rows: an inline table (repair path); ``rows`` is a list of value lists.
        series: source column that splits series / colour, if any.
        facet: source column that splits panels, if any.
        category_order / series_order: explicit canonical orders; values seen but not listed
            are appended and reported, never dropped. Default is first-appearance order.
        aggregate: sum / mean / min / max / first / last, applied when a
            (category, series, facet) key repeats. Duplicate keys with no aggregator is an
            error, not a silent pick.

    Returns ``plot_data_path``, the emitted ``columns`` (canonical names, in file order),
    ``category_order`` / ``series_order``, ``n_rows``, ``dropped_columns`` (unmapped source
    columns excluded by the whitelist - the proof a helper column cannot leak), and ``warnings``.
    """
    header, records = _load_records(dataset_path, columns, rows)
    warnings: list[str] = []

    mapping = {"category": x, "value": value}
    if series:
        mapping["series"] = series
    if facet:
        mapping["facet"] = facet
    missing = [src for src in mapping.values() if src not in header]
    if missing:
        raise ValueError(
            f"mapped column(s) not in the data: {missing}; available columns: {header}"
        )
    dropped = [col for col in header if col not in mapping.values()]

    # Whitelist + coerce value. An unmapped helper column is gone here; it cannot become a series.
    seen_cats: list[str] = []
    seen_series: list[str] = []
    groups: dict[tuple[str, str, str], list[float]] = {}
    for record in records:
        category = str(record[mapping["category"]])
        series_val = str(record[mapping["series"]]) if series else ""
        facet_val = str(record[mapping["facet"]]) if facet else ""
        raw = record[mapping["value"]]
        try:
            numeric = float(raw)
        except (TypeError, ValueError):
            warnings.append(f"non-numeric value {raw!r} at category {category!r} dropped")
            continue
        if category not in seen_cats:
            seen_cats.append(category)
        if series and series_val not in seen_series:
            seen_series.append(series_val)
        groups.setdefault((category, series_val, facet_val), []).append(numeric)

    duplicates = [key for key, vals in groups.items() if len(vals) > 1]
    if duplicates and aggregate is None:
        raise ValueError(
            f"{len(duplicates)} duplicate (category, series, facet) key(s) and no aggregate; "
            f"pass aggregate=sum|mean|min|max|first|last, e.g. {duplicates[0]}"
        )
    if aggregate is not None and aggregate not in _AGGREGATORS:
        raise ValueError(f"unknown aggregate {aggregate!r}; use one of {sorted(_AGGREGATORS)}")
    reducer = _AGGREGATORS.get(aggregate or "first")

    cat_order, cat_tail = _ordered(seen_cats, category_order)
    ser_order, ser_tail = _ordered(seen_series, series_order) if series else ([], [])
    if cat_tail:
        warnings.append(f"categories in data missing from category_order, appended: {cat_tail}")
    if ser_tail:
        warnings.append(f"series in data missing from series_order, appended: {ser_tail}")

    out_columns = ["order", "category"]
    if series:
        out_columns.append("series")
    if facet:
        out_columns.append("facet")
    out_columns.append("value")

    # Emit in one canonical order shared by marks and labels: facet, then category, then series.
    out_rows: list[dict[str, Any]] = []
    order_index = 0
    facet_values = _facet_values(groups, facet)
    for facet_val in facet_values:
        for category in cat_order:
            for series_val in (ser_order if series else [""]):
                key = (category, series_val, facet_val)
                if key not in groups:
                    continue
                row: dict[str, Any] = {"order": order_index, "category": category, "value": reducer(groups[key])}
                if series:
                    row["series"] = series_val
                if facet:
                    row["facet"] = facet_val
                out_rows.append(row)
                order_index += 1

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_data_path = out_dir / "plot-data.csv"
    with plot_data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_columns)
        writer.writeheader()
        writer.writerows(out_rows)

    return {
        "plot_data_path": str(plot_data_path),
        "columns": out_columns,
        "category_order": cat_order,
        "series_order": ser_order,
        "n_rows": len(out_rows),
        "dropped_columns": dropped,
        "warnings": warnings,
    }


def _facet_values(groups: dict[tuple[str, str, str], list[float]], facet: Optional[str]) -> list[str]:
    """First-appearance facet order (facets have no explicit-order input; keep it simple)."""
    if not facet:
        return [""]
    order: list[str] = []
    for (_category, _series, facet_val) in groups:
        if facet_val not in order:
            order.append(facet_val)
    return order
