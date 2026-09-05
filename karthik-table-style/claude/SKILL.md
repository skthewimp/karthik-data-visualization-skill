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
2. Order rows and columns for that task (see Craft principles).
3. Format from data outward: values and their alignment first, emphasis second,
   rules and shading last.
4. Apply the eraser test: remove any ink that does not carry data or necessary
   structure - full gridlines, vertical rules, repeated units, redundant
   precision, decorative shading.
5. Render and inspect the actual table, not just the code: check that columns
   align, decimals line up, nothing wraps into a collision, and the smallest
   font meets the supplied delivery minimum at displayed size.

## Craft principles

- **Information before whitespace.** Default to a compact, readable table with
  small outer margins and modest cell padding. Space earns its place by separating
  columns, grouping rows, or preventing collisions. Avoid oversized margins,
  spacious dashboard-card styling, and tall rows around small text. Keep type
  readable and tighten the surrounding space; never shrink type to create air.

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
- **Precision keyed to variance.** Full rule and computation: `dataviz-precision` (the `recommend_precision` MCP tool), which derives one uniform rounding place from the column's spread. Inside the construct pipeline each column's format is resolved upstream and handed to you - apply and align to it, don't re-derive. In brief: significant digits not decimal places; round every value in a column to the same place; coarse-round the noise off large widely-spread values (12,483 → 12,500 or 12,000); never show or manufacture precision the data can't support.
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

## Treatment and layout

Choose treatment from the reading task, before sizing. Keep exact display strings
separate from raw values: strings determine geometry; values determine scales.

- **Lookup:** aligned text may be sufficient.
- **Focal entity or winners:** identify the focal rows/cells and preserve ties.
  Give the claim visible emphasis through weight or colour, not a barely changed grey.
- **Magnitude comparison:** consider in-cell bars or dots with explicit domains
  and baselines. Reserve space for both the number and its graphic.
- **Hot/cold scanning:** use shading with an explicit scope: column, row, or whole
  table. A shared scale requires comparable meaning and units, not just numeric
  columns or percent signs. Diverging scales need a meaningful midpoint.
- **Change over an ordered sequence:** consider a sparkline, specifying whether
  its scale is shared across rows. Unrelated metrics are not a time series.

State the treatment's scope, domain, direction, missing-value handling, and focal
entities where relevant. Column count does not decide bars versus shading. Use
`recommend_colours` for categorical/focal assignments and `recommend_precision`
for display strings. For shading, choose an ordered sequential or meaningful
midpoint diverging scale from the brand/style palette or renderer; the categorical
picker's distinct-hue ordering is inappropriate. Use `validate_palette` as a
diagnostic and inspect text contrast against the actual cell fills. A plain table needs no
palette call; a magnitude or focal treatment must not disappear behind “no series”.

When available, call `recommend_table_layout` with the formatted headers/cells,
identifier columns, typography, and delivery constraints. For larger inputs pass
a local JSON `content_path` rather than putting the table into the conversation.
The planner balances measured header/body wrapping against shared row heights
before construction, choosing compact columns without reducing type. A long
header or occasional long cell must not leave the whole column needlessly wide.
Do not equalise column widths or stretch cells to fill the delivery canvas. Keep
padding compact and preserve space needed for graphics. Specify
`visual_width_px` for inline graphics; `max_width_px` is an optional ceiling,
not a requirement for automatic wrapping. Headers can use the full column width;
body text shares it with its reserved inline graphic. Use the returned wrapped strings, column widths, row
heights, font sizes, text bands, and continuation pages in the builder. Page column
indices are zero-based and row ranges are half-open; repeat identifiers and headers.
Do not silently drop rows or columns. Check that a split still supports the reading
task; revise grouping or delivery if comparisons would be separated.

Set the intended display width and minimum displayed text pixels for screen
outputs. DPI alone says nothing about readability after an image is fitted into a
container. For print, use the intended physical size and point-size minimums.
Never fit by shrinking below the supplied minimum. Widen within delivery limits,
wrap, split/paginate, or revise supported wording/form. Reduce scope only when
authorized. `cannot_fit` requires a revised plan, not acceptance of oversize pages.
Fallback font metrics are estimates until checked in the target renderer.

Without the MCP, use the renderer's text metrics to do the same work and inspect
at delivery size; do not substitute a chart's slot-count layout for table content.

## Rendering

- **Delivered HTML or interactive tables:** author with the R `gt` package; it
  carries alignment, precision, grouping, and conditional formatting cleanly.
  Markdown or hand-built HTML is an acceptable fallback for non-R contexts.
- **A gated raster (for inspection):** build the table as a `grid` / `tableGrob`
  object and render it through the same `ragg::agg_png` path as charts, so it
  can be inspected and gated deterministically. The craft principles are
  engine-agnostic and apply identically to both.
- Pass the typography floor and screen constraints to inspection (the combined
  renderer accepts `minimum_text_size_pt`, `display_width_px`, and
  `minimum_text_size_px` in `dimensions`). Inspect each delivered page. Nested
  text must be captured individually; `checks_complete: false` is incomplete
  evidence, never a pass. Resolve `CELL_OVERFLOW` by changing cell geometry or
  wrapping, not by moving table labels off their cells. Read decimal alignment,
  contrast against cell fills, and treatment effectiveness from the actual render.

## Guardrails

- A table is chosen because the task is exact lookup or non-commensurable values,
  not as a dumping ground for data a chart could show as a shape. If the message
  is a trend or comparison the eye should grab at once, it is a chart - return to
  `dataviz-selector`.
- Never widen precision to fill space or narrow it to hide spread; precision is a
  data decision, not a layout one.
- One table, one main task. Split a table that serves two unrelated comparisons.
- Do not repeat in shading what alignment and ordering already show.
