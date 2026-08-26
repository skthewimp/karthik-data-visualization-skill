---
name: dataviz-precision
description: "Decide how many significant digits to show for numbers in a chart or a table - axis ticks, data labels, and table cells. Use whenever numeric values are displayed and you must choose precision: how many digits on an axis, how many decimals on a bar label, how to round a column so it reads cleanly. Precision is keyed to the spread of the data (max minus min), not to individual values, and is expressed as significant digits, not decimal places; every value in a column or axis is rounded to one uniform place. Never fabricate precision the data cannot support and never round toward rounder-sounding numbers. Backed by the dataviz MCP tool recommend_precision."
metadata:
  short-description: Choose significant digits / rounding for chart and table numbers
  claude-description: Choose how many significant digits to show for chart and table numbers - keyed to the spread (max-min), not individual values, one uniform place per column. Never fabricate precision.
---

# Dataviz Precision

Own the significant-digits decision for numbers on a chart or in a table: axis ticks, data labels, and table cells. Do not choose the chart's form, its colours, or its prose - those belong to `dataviz-selector`, `dataviz-color`, and `chart-explainer`. This skill generalises the precision philosophy that also governs `karthik-table-style`; when formatting numbers anywhere, this is the authority.

The mechanical computation lives in the dataviz MCP: `recommend_precision`.

## The rule: precision is keyed to the spread, not the value

The question is never "how precise is this number" but "how precise must the reader be to tell these numbers apart". So precision is set by the **range of the column or axis** (max minus min), not by any single value.

Call `recommend_precision(values, role)` with the numbers that will be shown together (`role` = `axis`, `label`, or `table_column`). It computes:

- the **range** `max - min` over the values that must be distinguished,
- a single **uniform rounding place** for the whole set, from the formula `place = floor(log10(range)) - (target_steps - 1)` where `target_steps` (~2) is how many significant figures of the range the reader needs to just about resolve the information,
- a **formatted preview** of every value rounded to that place.

Example: `{12483, 9210, 15040}` has a range of ~5830, so the place is hundreds and the column shows `12,500 / 9,200 / 15,000` - two significant figures of the spread, and no more.

If you know the smallest difference that actually matters (`d`), pass `smallest_meaningful_difference=d`; the place is then `floor(log10(d))`.

## What this means in practice

- **Significant digits, not decimal places.** The place cuts to the *left* of the decimal point too: 12,483 becomes 12,500 or 12,000 when the spread is coarse. A column of large, widely spread values usually wants fewer digits, not more.
- **Round every value in a column to the same place.** Uniform digit-length down a column lets length itself read as magnitude, and lets the decimal points align.
- **Do not show precision the data cannot support**, and never manufacture it to fill space. Precision is a data decision, not a layout one.
- **Never round toward rounder-sounding numbers** - round to the place the spread dictates, not to whatever looks tidy.

## Precedence: the spread rule is the default; exact digits are the exception

By default, `recommend_precision` governs every displayed number. Source digits override it in exactly one case: **identifiers or a genuine exact-lookup requirement** - an account number, a code, a reference value the reader must read off verbatim. Call `recommend_precision(values, role, exact=True)` for those; it preserves every source digit and returns `exact_override: true`.

An exact override is never silent. Whenever you leave the spread rule behind, **record the reason** - why this column is an identifier or an exact lookup rather than a quantity to compare. If you cannot name why exact digits are needed, the spread rule stands.

If an upstream decision has already marked a column as an identifier or exact-lookup, obey that mark and carry its stated reason forward - do not silently re-decide it at build time. Absent any such mark, the spread rule stands and the exact-vs-spread call is yours to make here. Carrying the decision as an explicit flag with its reason, rather than leaving it to be re-inferred from prose, is what lets a weaker downstream model apply it reliably.

## Charts and tables

The rule is the same for both. On a chart it sets axis-tick and data-label formatting; in a table it sets each numeric column's rounding and, with `karthik-table-style`, the decimal alignment and tabular figures. Apply `recommend_precision` per axis and per column - each has its own spread.
