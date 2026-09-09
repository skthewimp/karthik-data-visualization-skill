# Dataviz Extract

Use `dataviz-extract` during a chart repair, in parallel with `dataviz-brief`, to read the underlying data out of the source image. The rebuild is designed forward from this table plus the brief - not traced from the picture - so the table has to be complete enough to build any chosen form on.

## Why it exists

If the repair is going to change the form (a stack becomes small multiples, say), it needs every cell of the data, not just the totals or the envelope. Colour is data, not decoration: a chart that stacks ten models by week carries ten numbers per week, and the new form needs all of them. Reading the totals off the source is not enough.

It is a vision task, not a rendering task - there is no MCP tool for it. The numbers are read off the image with judgment.

## What it produces

- The **category members**, listed by name.
- The **periods** or x-positions, listed - together with the axis anchors exactly as printed: every legible tick label (a year, a category, a value gridline), its position, and the axis's stated meaning and unit. Those labels are read directly off the image, so they are preserved exactly and kept separate from any finer per-observation position that is only inferred. Uncertainty about where a single observation sits inside a labelled interval - which month within a printed year, which day within a printed week - never licenses discarding the coarser labels the axis actually prints; the printed labels carry through and the finer uncertainty is recorded on its own. Synthetic sequential ids (P01, P02 ...) stand in for positions only when the axis prints no labels at all, never as a replacement for labels that could be read.
- A value for **every (period × category) cell** - no gaps. Cells that cannot be read cleanly are estimated and marked approximate, but they still exist.
- **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

Exact values are used when the prompt supplies them or when they are printed as labels. Reading values off an image is inherently approximate - that is self-evident and does not need announcing on the chart or repeating through the brief, so the skill neither hedges every number nor stamps "approximate" as chart furniture. The real rule is the anti-fabrication one: no digits the image cannot support, no rounding toward rounder-sounding numbers. Difficulty of reading a value is never a reason to drop the category it belongs to; deciding a category is not key is the brief's job, made in message terms. The same guard covers axis labels: a printed label is directly-read data, so difficulty placing individual observations is never a reason to swap readable labels for synthetic indices - that erases what the source actually gave.

## Relationship to other skills

Step 2 of `dataviz-fix`, running in parallel with `dataviz-brief`. The table feeds `dataviz-selector` (form choice) and the build step.
