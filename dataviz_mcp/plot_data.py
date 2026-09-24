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
import json
import re
from pathlib import Path
from typing import Any, Optional

# One signed decimal / scientific number, possibly with thousands separators.
_NUMBER_RE = re.compile(r"[-+]?(?:\d[\d,]*)?\.?\d+(?:[eE][-+]?\d+)?")


def _coerce_number(raw: Any) -> Optional[float]:
    """Read a value as a number, tolerating a qualifier or unit the producer fused in.

    A weak extract model writes the geometry into the value cell with a qualifier or unit
    attached - ``approximately 4.3``, ``~5``, ``50.2%``, ``1,234`` - and hard ``float()`` drops
    every one, losing a real observation. So pull the numeric token out and keep the row; the
    value is just the number, the approximation is already known and needs no annotating here.
    Genuinely non-numeric text (``NA``, ``n/a``, ``""``) has no number and returns ``None``.
    """
    if isinstance(raw, bool):  # bool is an int subclass; not a measured value
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    match = _NUMBER_RE.search(text)
    if match is None:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


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


# Canonical column names the frame emits; a label measure may not take one of them.
_RESERVED = frozenset({"order", "category", "series", "facet", "value", "start", "end", "approximate", "region"})


def _label_roles(labels: Any) -> dict[str, dict[str, Any]]:
    """Normalise the label-measure map to ``{name: {column, prefix, suffix, signed}}``."""
    roles: dict[str, dict[str, Any]] = {}
    for name, spec in dict(labels or {}).items():
        spec = {"column": spec} if isinstance(spec, str) else dict(spec or {})
        if not spec.get("column"):
            raise ValueError(f"label measure {name!r} needs a source column")
        key = re.sub(r"\W+", "_", str(name).strip().lower()).strip("_")
        if not key or key in _RESERVED:
            raise ValueError(f"label measure name {name!r} is reserved or empty; pick another name")
        roles[key] = {
            "column": str(spec["column"]),
            "prefix": str(spec.get("prefix") or ""),
            "suffix": str(spec.get("suffix") or ""),
            "signed": bool(spec.get("signed")),
        }
    return roles


def prepare_plot_data(
    output_dir: str,
    x: str,
    value: Any = None,
    dataset_path: Optional[str] = None,
    columns: Optional[list[str]] = None,
    rows: Optional[list[list[Any]]] = None,
    series: Optional[str] = None,
    facet: Optional[str] = None,
    category_order: Optional[list[str]] = None,
    series_order: Optional[list[str]] = None,
    aggregate: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    labels: Optional[dict[str, Any]] = None,
    approximate: Optional[str] = None,
) -> dict[str, Any]:
    """Reshape the source into a tidy plotting frame with a whitelist and one canonical order.

    Reads the data from ``dataset_path`` (dataset-to-story) or inline ``columns``/``rows`` (a
    repair artifact's recovered table), keeps only the mapped columns, coerces the geometry to
    numbers, aggregates duplicate keys when told how, and writes a long-format
    ``plot-data.csv`` in canonical order, plus ``plot-data.json`` describing its roles. The
    builder reads that file and reshapes nothing.

    Args:
        output_dir: directory the tidy frame is written into.
        x: source column that is the category / x position (required).
        value: source column that is the numeric value the marks are drawn to. Pass a list of
            source columns for a wide frame (one value column per series, e.g. one per model):
            each column melts into a series whose label is the column name. A list of value
            columns and an explicit ``series`` column are mutually exclusive. Optional when
            ``start`` and ``end`` give the geometry.
        start / end: source columns holding each mark's two ends on the value axis - a range,
            a dumbbell, a stacked or floating segment. Both are emitted as read; a missing end
            stays blank (the row is kept) and nothing is derived to fill it.
        labels: measures printed as labels but never drawn as geometry, as ``{name: column}``
            or ``{name: {column, prefix, suffix, signed}}`` - a growth rate on a revenue bar, a
            share beside a count. Each becomes its own column on the observation's row, with its
            own units, never a series and never part of the value scale.
        approximate: source column flagging an estimated observation; emitted as
            ``approximate`` (true/false) for the run report, never for the chart.
        dataset_path: a CSV to read (dataset-to-story path).
        columns / rows: an inline table (repair path); ``rows`` is a list of value lists.
        series: source column that splits series / colour, if any (long-format input only).
        facet: source column that splits panels, if any.
        category_order / series_order: explicit canonical orders; values seen but not listed
            are appended and reported, never dropped. Default is first-appearance order.
        aggregate: sum / mean / min / max / first / last, applied when a
            (category, series, facet) key repeats. Duplicate keys with no aggregator is an
            error, not a silent pick; intervals are never aggregated.

    Returns ``plot_data_path``, ``roles_path``, the emitted ``columns`` (canonical names, in
    file order), ``geometry`` (value / interval), ``label_columns``, ``category_order`` /
    ``series_order``, ``n_rows``, ``dropped_columns`` (unmapped source columns excluded by the
    whitelist - the proof a helper column cannot leak), and ``warnings``.
    """
    header, records = _load_records(dataset_path, columns, rows)
    warnings: list[str] = []

    # A wide value map (list of value columns) melts each column into a series named by the
    # column - so a dense multi-series frame needs no hand-built inline dataframe. It is
    # incompatible with an explicit series column: the wide columns already are the series.
    value_cols = [] if value is None else ([value] if isinstance(value, str) else list(value))
    interval = bool(start or end)
    if interval and not (start and end):
        raise ValueError("an interval needs both start and end columns")
    if not value_cols and not interval:
        raise ValueError("value must name at least one source column, or give start and end")
    wide = len(value_cols) > 1
    if wide and (series or interval):
        raise ValueError(
            "multiple value columns and a series column or an interval are mutually exclusive; "
            "wide value columns already define the series"
        )
    has_series = wide or bool(series)
    label_roles = _label_roles(labels)

    key_cols = {"category": x}
    if series:
        key_cols["series"] = series
    if facet:
        key_cols["facet"] = facet
    mapped = list(key_cols.values()) + value_cols + [c for c in (start, end, approximate) if c]
    mapped += [role["column"] for role in label_roles.values()]
    missing = [src for src in mapped if src not in header]
    if missing:
        raise ValueError(
            f"mapped column(s) not in the data: {missing}; available columns: {header}"
        )
    dropped = [col for col in header if col not in mapped]

    # Whitelist + coerce. An unmapped helper column is gone here; it cannot become a series.
    # Wide input iterates value columns per record, so each cell becomes one long-format row.
    seen_cats: list[str] = []
    seen_series: list[str] = []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in records:
        category = str(record[key_cols["category"]])
        facet_val = str(record[key_cols["facet"]]) if facet else ""
        if category not in seen_cats:
            seen_cats.append(category)
        ends = {k: _coerce_number(record[c]) for k, c in (("start", start), ("end", end)) if c}
        aux: dict[str, Any] = {}
        for name, role in label_roles.items():
            raw = record[role["column"]]
            aux[name] = _coerce_number(raw) if _is_number_text(raw) else None
            if aux[name] is None and raw not in (None, "") and str(raw).strip().upper() not in _NA_TOKENS:
                warnings.append(f"label {name}: {raw!r} at category {category!r} is not a number; left blank")
        flag = _flag(record[approximate]) if approximate else None
        for value_col in value_cols or [None]:
            if wide:
                series_val = value_col
            elif series:
                series_val = str(record[key_cols["series"]])
            else:
                series_val = ""
            numeric = _coerce_number(record[value_col]) if value_col else None
            if interval and ends["start"] is None and ends["end"] is None:
                warnings.append(f"interval at category {category!r} has neither end; dropped")
                continue
            if interval and None in ends.values():
                warnings.append(f"interval at category {category!r} is missing an end; kept blank, not derived")
            if not interval and numeric is None:
                warnings.append(f"non-numeric value {record[value_col]!r} at category {category!r} dropped")
                continue
            if has_series and series_val not in seen_series:
                seen_series.append(series_val)
            groups.setdefault((category, series_val, facet_val), []).append(
                {"value": numeric, **ends, "approximate": flag, "labels": aux}
            )

    duplicates = [key for key, vals in groups.items() if len(vals) > 1]
    if duplicates and interval:
        raise ValueError(
            f"{len(duplicates)} duplicate (category, series, facet) key(s) in an interval frame; "
            f"intervals are not aggregated - add the column that tells them apart, e.g. {duplicates[0]}"
        )
    if duplicates and aggregate is None:
        raise ValueError(
            f"{len(duplicates)} duplicate (category, series, facet) key(s) and no aggregate; "
            f"pass aggregate=sum|mean|min|max|first|last, e.g. {duplicates[0]}"
        )
    if aggregate is not None and aggregate not in _AGGREGATORS:
        raise ValueError(f"unknown aggregate {aggregate!r}; use one of {sorted(_AGGREGATORS)}")
    reducer = _AGGREGATORS.get(aggregate or "first")

    cat_order, cat_tail = _ordered(seen_cats, category_order)
    ser_order, ser_tail = _ordered(seen_series, series_order) if has_series else ([], [])
    if cat_tail:
        warnings.append(f"categories in data missing from category_order, appended: {cat_tail}")
    if ser_tail:
        warnings.append(f"series in data missing from series_order, appended: {ser_tail}")

    out_columns = ["order", "category"]
    if has_series:
        out_columns.append("series")
    if facet:
        out_columns.append("facet")
    if value_cols:
        out_columns.append("value")
    if interval:
        out_columns += ["start", "end"]
    if approximate:
        out_columns.append("approximate")
    out_columns += list(label_roles)

    # Emit in one canonical order shared by marks and labels: facet, then category, then series.
    # Every row keeps its full (category, series, facet) key, whatever columns ride along.
    out_rows: list[dict[str, Any]] = []
    order_index = 0
    facet_values = _facet_values(groups, facet)
    for facet_val in facet_values:
        for category in cat_order:
            for series_val in (ser_order if has_series else [""]):
                key = (category, series_val, facet_val)
                if key not in groups:
                    continue
                obs = groups[key]
                row: dict[str, Any] = {"order": order_index, "category": category}
                if value_cols:
                    present = [o["value"] for o in obs if o["value"] is not None]
                    row["value"] = reducer(present) if present else ""
                if interval:
                    row["start"] = _blank(obs[0]["start"])
                    row["end"] = _blank(obs[0]["end"])
                if approximate:
                    row["approximate"] = str(any(o["approximate"] for o in obs)).lower()
                for name in label_roles:
                    # A label is read, never combined: rows folded by the aggregate keep it only
                    # when they all print the same number.
                    seen = {o["labels"][name] for o in obs}
                    if len(seen) > 1:
                        warnings.append(f"label {name} differs across the rows folded into {key}; left blank")
                    row[name] = _blank(seen.pop()) if len(seen) == 1 else ""
                if has_series:
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
    geometry = "interval" if interval else "value"
    label_units = {name: {k: v for k, v in role.items() if k != "column"} for name, role in label_roles.items()}
    # The roles travel beside the frame, so the scaffold formats each label measure in its own
    # units without the caller carrying them across.
    roles_path = out_dir / "plot-data.json"
    roles_path.write_text(json.dumps({"geometry": geometry, "labels": label_units}, indent=2), encoding="utf-8")

    return {
        "plot_data_path": str(plot_data_path),
        "roles_path": str(roles_path),
        "columns": out_columns,
        "geometry": geometry,
        "label_columns": label_units,
        "category_order": cat_order,
        "series_order": ser_order,
        "n_rows": len(out_rows),
        "dropped_columns": dropped,
        "warnings": warnings,
    }


def _blank(value: Optional[float]) -> Any:
    return "" if value is None else value


def _flag(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"true", "yes", "y", "1", "approximate", "approx", "estimated"}


# Cells that mean "no value" rather than a value that failed to parse.
_NA_TOKENS = frozenset({"NA", "N/A", "NAN", "NONE", "NULL", "-", "—", "–"})
# A cell that is a number and nothing else: a sign, a currency, separators, a unit suffix or an
# approximation mark may ride along, but no words - "Q1'24" or a sentence with a digit is text.
_NUMBER_TEXT_RE = re.compile(
    r"(?:~|≈|approx\.?|approximately|about)?\s*[-+−]?\s*[$€£¥₹]?\s*"
    r"(?:\d[\d,]*)?\.?\d+(?:[eE][-+]?\d+)?\s*(?:%|pp|k|K|m|M|MM|bn|B)?",
    re.IGNORECASE,
)


def _is_number_text(raw: Any) -> bool:
    if isinstance(raw, bool):
        return False
    if isinstance(raw, (int, float)):
        return raw == raw
    return raw is not None and bool(_NUMBER_TEXT_RE.fullmatch(str(raw).strip()))


def default_plot_data_map(columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    """A role map read off the table itself, for when the plan did not give one.

    Deterministic and form-blind: a column whose filled cells are mostly bare numbers is a
    measure, anything else is a key. The first key is the category, the next the series, the
    next the facet; the first measure is the value and every other measure rides along as a
    label measure, so no number becomes a series or joins the value scale by accident. The plan's
    own map is always better - this only keeps the build on the mechanical path.
    """
    keys: list[str] = []
    measures: list[str] = []
    for i, name in enumerate(columns):
        cells = [row[i] for row in rows if i < len(row) and row[i] not in (None, "")
                 and str(row[i]).strip().upper() not in _NA_TOKENS]
        numeric = sum(1 for cell in cells if _is_number_text(cell))
        (measures if cells and numeric * 2 > len(cells) else keys).append(name)
    if not keys or not measures:
        raise ValueError("the table needs at least one text column and one numeric column to plot")
    mapping: dict[str, Any] = {"x": keys[0], "value": measures[0]}
    if len(keys) > 1:
        mapping["series"] = keys[1]
    if len(keys) > 2:
        mapping["facet"] = keys[2]
    if len(measures) > 1:
        names = [re.sub(r"\W+", "_", m.lower()).strip("_") for m in measures[1:]]
        mapping["labels"] = {
            (name if name and name not in _RESERVED else f"label_{i}"): column
            for i, (name, column) in enumerate(zip(names, measures[1:]), 1)
        }
    return mapping


def _facet_values(groups: dict[tuple[str, str, str], list[Any]], facet: Optional[str]) -> list[str]:
    """First-appearance facet order (facets have no explicit-order input; keep it simple)."""
    if not facet:
        return [""]
    order: list[str] = []
    for (_category, _series, facet_val) in groups:
        if facet_val not in order:
            order.append(facet_val)
    return order
