---
name: dataviz-extract
description: Read the full period-by-category data table out of a chart image by vision - every value for every period and every series - so a repair can rebuild from data, not from the picture.
---

# Dataviz Extract

Use this during a chart repair, in parallel with `dataviz-brief`, to recover the underlying data from the source image. The rebuild is designed forward from this table plus the brief - not traced from the source picture - so the table must be complete enough to build any chosen form on.

This is a vision task, not a rendering task. There is no MCP tool for it: read the numbers off the image with judgment.

## What to produce

The **full period-by-category table**: a value for every period and every category, series, stack, or facet the chart encodes. Colour is data, not decoration - a chart encoding N series across a period needs N values for that period, not one total. The envelope, the totals, or the top line alone are not enough; any later form change needs each cell.

Produce, explicitly:

1. **The category members**, listed by name. If the source shows ten series, name all ten.
2. **The periods or x-positions**, listed.
3. **A value for every (period × category) cell.** No gaps. If a cell cannot be read, estimate it and mark it approximate - but it must exist.
4. **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

- Use exact values when the prompt supplies them or when they are printed as source labels.
- Mark screenshot-derived values as approximate unless they are clearly printed. Approximate values, labelled approximate, are fine - the messages rarely depend on exact precision, and difficulty of reading a value is never a reason to drop the category it belongs to.
- Do not invent categories or periods that are not in the source. Do not silently merge series. If the source is genuinely unreadable in a region, say which cells are estimates and how confident you are.

## Output shape

A tidy long table is preferred (one row per period × category), or a wide period-by-category grid. Include a units line. For example:

```markdown
Units: weekly requests (millions), approximate unless printed
Categories: <c1, c2, ... cN>
Periods: <p1 ... pM>

period, category, value, approx?
p1, c1, 12.4, ~
p1, c2,  3.1, ~
...
```

## Boundaries

- Do not choose a chart form or decide what matters - that is `dataviz-brief` and `dataviz-selector`.
- Do not drop a category because its values are hard to read; extract it approximately and label it. Deciding a category is not key is the brief's job, made in message terms, not a consequence of extraction difficulty.
