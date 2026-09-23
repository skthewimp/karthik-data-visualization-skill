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
5. **Reserve the whole table by measurement before you render** - see the numbered
   steps below. Geometry is settled up front, not discovered by clipping.
6. Render and inspect the actual table as the safety net, not just the code:
   the geometry was reserved at step 5; this pass confirms columns align, decimals
   line up, nothing wraps into a collision, and the smallest font meets the
   supplied delivery minimum at displayed size.

## Reserve the frame before you render

Table geometry is measured, never eyeballed. A clipped title or a header band
overlapping the rows is a reservation skipped on the first pass, not a revision
owed later. Before you render, in order:

1. **Call `recommend_table_layout`** with the formatted headers and cells, raw
   values, the treatment list, identifier columns, typography, and delivery
   constraints. Apply the column
   widths, wrapping, header band, row heights, and continuation pages it returns.
   This is the mandatory sizing path, not an optional aid.
2. **Reserve the frame like the columns.** The title, subtitle, and footer/notes
   are wrapped to the table width and given their own bands; the header band is its
   own layer that must not overlap the subtitle above it or the first data row
   below it.
3. **A block wider than the canvas is `cannot_fit`** - resolve it by narrowing,
   wrapping, or splitting, and never ship it clipped at the edge. Do not drop rows
   or columns to force a fit.
4. **Draw the plan through the shared constructor**, not by hand-positioning rows.
   Where the harness provides it, `render_table_from_plan` (R when its required packages are available,
   Python only when that backend is unavailable) applies the measured column widths, row heights, header band, and the
   title/subtitle/notes bands verbatim, so nothing you reserved gets re-normalised
   away - the failure mode where a hand-rolled table ignores measured heights and
   clips the footer.

Where the harness has no such tool, do the same by hand: measure each column,
header, and frame block, keep them within the delivery width, apply those exact
widths and heights when you draw, render, and confirm by eye before delivering.

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

A table of comparable numbers is formatted by default. Numbers alone make the reader
do the comparison in their head; a magnitude channel in the cell (a bar or a shade)
lets the eye see the pattern while the number stays there for lookup. Plain text is
the exception, justified only when the task is looking up a single value and nothing
in the table is compared.

Decide the treatment before sizing, for every block of numbers:

1. **Which cells compare with which?** That is the scale's scope.
   - **Column** - each column is its own metric (revenue next to headcount next to
     margin). Each column gets its own scale.
   - **Row** - each row is one series whose cells compare with each other (a metric
     across periods, a measure across segments, one entity's values across
     comparable categories). Each row gets its own scale; mark it
     `commensurable`.
   - **Table** - every cell shares one honest scale (the same unit and meaning
     everywhere, such as a matrix of scores on one 0-100 scale). One
     scale; mark it `commensurable`.
2. **Which magnitude channel?**
   - **Data bars** when the table has room: they read as length, the most accurate
     cue. The bar trails its number, so the value is read first with its decimal
     alignment intact.
   - **Shading** when the table is dense (many columns, a matrix) or space is tight:
     a heat fill costs no width. Sequential for a one-sided magnitude, diverging
     around a meaningful midpoint (zero, an average, a target) for signed or
     above/below values.
   - Column count does not decide this; room and density do.
3. **Which direction is good?** Set `higher_is_better: false` where lower wins (cost,
   latency, error, pace), so the strongest shade marks the best cell rather than the
   biggest number.
4. **Is there an ordered sequence?** When a row's values run over time or distance,
   add a sparkline column at the end so the shape is visible next to the exact
   values. Each sparkline shows its own row's shape unless the rows share a unit and
   the comparison between their levels matters. Unrelated metrics are not a
   sequence.
5. **Is there a focal entity?** Emphasise the row the claim is about (bold plus a
   tint), and preserve ties.
6. **Would a summary help the reading?** A row average or total column (such as each
   entity's mean across the columns) often answers the question the matrix raises.
   Compute it, add it as a column, and give it the same treatment.

A table may combine treatments: row-wise shading on the value block, a sparkline
column, and a focal row.

Pass the treatments to `recommend_table_layout` as a list, with raw `values` on each
column (a list of lists for a sparkline column whose cells are blank). The tool
computes every scale, fill, ink, bar extent and sparkline point, reserves the
graphic width, and right-aligns numbers. Do not compute fills or bar lengths
yourself, and do not re-derive them at build. The plan warns when comparable
numeric columns are left untreated; resolve that warning or state why the task is
single-value lookup. Use `recommend_precision` for display strings. For shading, the
tool builds an ordered sequential or diverging scale that keeps every number legible
on its fill. Pass brand pole colours as `colours` if there is a brand; never run the
categorical colour picker on shades.

The `recommend_table_layout` call from the reservation steps above takes the
formatted headers/cells, identifier columns, typography, and delivery constraints.
Supply each complete
header, including units and explanatory sublabels; use explicit newlines for
semantic breaks. Character counts or an omitted description cannot establish fit.
Choose a per-column `max_header_lines` when the reading task or delivery limits
how tall a heading may become; this is a constraint, not permission to clip it.
For larger inputs pass
a local JSON `content_path` rather than putting the table into the conversation.
The planner balances measured header/body wrapping against shared row heights
before construction, choosing compact columns without reducing type. A long
header or occasional long cell must not leave the whole column needlessly wide.
Do not equalise column widths or stretch cells to fill the delivery canvas. Keep
padding compact and preserve space needed for graphics. Specify
`visual_width_px` for inline graphics; `max_width_px` is an optional ceiling,
not a requirement for automatic wrapping. Headers can use the full column width;
body text shares it with its reserved inline graphic. Draw the returned `headers`
verbatim at `header_pt` in bold inside `header_height_px`, using the returned
column widths and padding. Do not flatten those line breaks, substitute the raw
unwrapped names, or add unmeasured labels above/below them. The tallest complete
wrapped header determines the header band; compact body rows are a separate layer.
Use the returned body wrapping/heights, text bands and continuation pages too. Page column
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
- **A gated raster (for inspection):** use `render_table_from_plan`. It draws the
  resolved treatment (fills, bars, sparklines, emphasis) with the geometry. It uses
  R/grid/ragg when available, otherwise Python/Matplotlib, with measured cell bounds
  for inspection on both paths. A failed R render is reported, never retried in
  Python. The same craft principles and delivery constraints apply to both.
- Pass the typography floor and screen constraints to inspection (the combined
  renderer accepts `minimum_text_size_pt`, `display_width_px`, and
  `minimum_text_size_px` in `dimensions`). Inspect each delivered page. Nested
  text must be captured individually; `checks_complete: false` is incomplete
  evidence, never a pass. Resolve `CELL_OVERFLOW` by changing cell geometry or
  wrapping, not by moving table labels off their cells. Read decimal alignment,
  contrast against cell fills, and treatment effectiveness from the actual render.

## Guardrails

- A table is not a dumping ground for data a chart could show as a shape. If the
  message is one comparison the eye should grab at once (a ranking of a handful of
  values, a single trend), it is a chart - return to `dataviz-selector`. A matrix of
  many entities against several metrics or periods, where the reader wants both the
  exact values and the pattern, is a formatted table.
- Never widen precision to fill space or narrow it to hide spread; precision is a
  data decision, not a layout one.
- One table, one main task. Split a table that serves two unrelated comparisons.
- A shaded or barred table is not finished until the render shows the treatment.
  `TREATMENT_NOT_DRAWN` means the plan was bypassed; draw it through
  `render_table_from_plan`.
