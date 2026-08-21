# Dataviz Extract

Use `dataviz-extract` during a chart repair, in parallel with `dataviz-brief`, to read the underlying data out of the source image. The rebuild is designed forward from this table plus the brief - not traced from the picture - so the table has to be complete enough to build any chosen form on.

## Why it exists

If the repair is going to change the form (a stack becomes small multiples, say), it needs every cell of the data, not just the totals or the envelope. Colour is data, not decoration: a chart that stacks ten models by week carries ten numbers per week, and the new form needs all of them. Reading the totals off the source is not enough.

It is a vision task, not a rendering task - there is no MCP tool for it. The numbers are read off the image with judgment.

## What it produces

- The **category members**, listed by name.
- The **periods** or x-positions, listed.
- A value for **every (period × category) cell** - no gaps. Cells that cannot be read cleanly are estimated and marked approximate, but they still exist.
- **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

Exact values are used when the prompt supplies them or when they are printed as labels; screenshot-derived values are marked approximate. Approximate values, labelled approximate, are fine - the messages rarely depend on exact precision. Difficulty of reading a value is never a reason to drop the category it belongs to; deciding a category is not key is the brief's job, made in message terms.

## Relationship to other skills

Step 2 of `dataviz-fix`, running in parallel with `dataviz-brief`. The table feeds `dataviz-selector` (form choice) and the build step.
