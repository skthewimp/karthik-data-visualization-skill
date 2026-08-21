---
name: karthik-table-style
description: Format tables as visualizations in Karthik's style - emphasis, decimal alignment, precision, column widths, minimal rules, tabular figures, and deliberate conditional formatting.
metadata:
  short-description: Craft a well-formatted table as a visualization
  claude-description: Format a table as a visualization in Karthik's style - emphasis, decimal alignment, precision, column widths, minimal rules, and deliberate conditional formatting. Use once the form is chosen as a table.
---

# Karthik Table Style

Use this skill when the chosen form is a table, or when reviewing a table's
formatting. A well-formatted table is a visualization: alignment, precision, and
restraint do the same perceptual work that position and colour do in a chart.

This skill owns table craft only. Whether the data should be a table or a chart
is `dataviz-selector`'s decision; the two-line note beside the table is
`chart-explainer`; diagnosing an existing table is `dataviz-critique`. Apply the
workflow below before finalizing a table or table-generating code. Private local
references may add nuance, but this public skill is self-contained.

## Workflow

**Semantic preflight:** before formatting, identify each column's measure, unit,
denominator, and the smallest difference that is meaningful to the reader. A
table that is numerically faithful but hard to scan, or that shows more
precision than the data supports, is not finished.

1. State the reader's task: look up one value, compare down a column, compare
   across a row, or scan for outliers. The task decides ordering, emphasis, and
   any conditional formatting.
2. Order rows and columns for that task - by the value being compared, not
   alphabetically or by source order, unless lookup by name is the task.
3. Format from data outward: values and their alignment first, emphasis second,
   rules and shading last.
4. Apply the eraser test: remove any ink that does not carry data or necessary
   structure - full gridlines, vertical rules, repeated units, redundant
   precision, decorative shading.
5. Render and inspect the actual table, not just the code: check that columns
   align, decimals line up, nothing wraps into a collision, and the smallest
   font is still readable at delivery size.

## Craft principles

- **Order for the reader's task.** Sort rows and columns by the value being
  compared, not alphabetically or by source order, unless lookup by name is the
  task. Time runs across columns; rankings run top to bottom. Ordering is more
  load-bearing than any formatting: a badly ordered table cannot be rescued by
  alignment.
- **Make the header row distinct.** The header must read as a different layer
  from the body - weight plus a single rule beneath it, not merely alignment.
  This is the most common table failure; do not rely on position alone.
- **Emphasis is scarce ink.** Bold or shade only the cells that carry the claim
  - a total, a winner, an outlier, the row the reader came for. Emphasising
  everything emphasises nothing. Keep one focal element as figure against a
  neutral ground.
- **Alignment.** Right-align numbers and align them on the decimal point;
  left-align text; align each header with its column body. Equalise the decimal
  count down a column so digit-length itself reads as magnitude - the number's
  size becomes a small bar chart.
- **Precision keyed to variance.** Show the number of decimals that resolves the
  smallest meaningful difference in the column, not the maximum the data
  carries. A column of large, widely spread values needs fewer decimals, not
  more. Do not show precision the data cannot support.
- **Column widths sized to content.** Give each column the width its content
  needs; wrap long text columns deliberately and never let one column's wrap
  distort the grid or push number columns out of scanning range. Number columns
  stay narrow and dense.
- **Rules and whitespace.** No full gridlines, no vertical rules. Use a few
  horizontal rules - header, group boundaries, total - and whitespace to group
  rows. Whitespace groups and separates; it is not filler.
- **Group related rows and set totals apart.** Cluster rows that belong together
  with a little whitespace, keep the column structure identical across groups,
  and give a total or summary row a distinct weight or rule so it is not read as
  just another row.
- **Put the main comparison down a column.** The eye compares down a column far
  more accurately than across a row, so orient the table so the comparison the
  reader came for runs vertically; prefer more rows than columns (portrait).
- **Tabular (lining) figures.** Use mono-width digits so columns align
  vertically; pair with a clean text font. Proportional figures break decimal
  alignment.
- **Units and headers.** Put the unit once - in the header or a note - not in
  every cell. Keep headers short and their meaning unmistakable.

## Conditional formatting

Use it only when scanning for magnitude is part of the reader's task, and choose
the scope deliberately:

- **By column** (most common) - shade within each metric, so the scale compares
  like with like down the column.
- **By row** - shade within each row when the row is its own scale and
  cross-row comparison is not the task.
- **Whole table** - one shared scale only when every cell is commensurable
  (same unit, same meaning).

Shading is colour, a weak channel for reading exact values: reserve it for
spotting hot and cold regions across many cells, not for values the reader must
read precisely. A perceptually ordered sequential scale for magnitude, a
diverging scale only around a meaningful midpoint. If the shading does not change
what the reader can see, remove it.

## Inline micro-visualization

A table can embed a visualization in a cell - an in-cell bar, a sparkline, a
small dot plot. This is the strongest form of "a table is a visualization": it
keeps the exact number for lookup while putting magnitude or trend on a strong
channel (length, position) that shading cannot match. Prefer an in-cell bar or
sparkline over heat shading when the reader needs to *compare* magnitudes or see
a *shape*, not just spot hot cells. Keep it subordinate - one micro-visual
column, aligned to a common scale, not a cell-by-cell zoo of glyphs.

## Rendering

- **Delivered HTML or interactive tables:** author with the R `gt` package; it
  carries alignment, precision, grouping, and conditional formatting cleanly.
  Markdown or hand-built HTML is an acceptable fallback for non-R contexts.
- **A gated raster (for inspection):** build the table as a `grid` / `tableGrob`
  object and render it through the same `ragg::agg_png` path as charts, so it
  can be inspected and gated deterministically. The craft principles are
  engine-agnostic and apply identically to both.

## Guardrails

- A table is chosen because the task is exact lookup or non-commensurable values,
  not as a dumping ground for data a chart could show as a shape. If the message
  is a trend or comparison the eye should grab at once, it is a chart - return to
  `dataviz-selector`.
- Never widen precision to fill space or narrow it to hide spread; precision is a
  data decision, not a layout one.
- One table, one main task. Split a table that serves two unrelated comparisons.
- Do not repeat in shading what alignment and ordering already show.
