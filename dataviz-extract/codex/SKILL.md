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

1. **The category members**, one per visually distinct series - listed by name where the source identifies them. If the chart encodes more distinct series than the legend names, still list every distinct series: name the ones you can and label the rest generically (an unlabelled series is still a row). Never shrink the category count to only the ones you could name - a missing label is not a missing category.
2. **The periods or x-positions**, listed.
3. **A value for every (period × category) cell.** No gaps. If a cell cannot be read, estimate it - but it must exist.
4. **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

- Use exact values when the prompt supplies them or when they are printed as source labels.
- Reading values off an image is inherently approximate. That is self-evident - a reconstruction is obviously not the raw data - so it does not need announcing on the chart or repeating through the brief. Do not fabricate precision: no digits the image cannot support, and no rounding toward rounder-sounding numbers. But do not hedge every number either; the messages rarely depend on exact precision, and difficulty of reading a value is never a reason to drop the category it belongs to. Keep any per-cell confidence for your own reasoning, not as chart furniture. At most, one plain source line ("reconstructed from the source image") is enough - and even that only if the medium expects a source note.
- Do not invent categories or periods that are not in the source. Do not silently merge series. If the source is genuinely unreadable in a region, note which cells you were least sure of when you hand the table on - internally, not as a caption.

## Output shape

A tidy long table is preferred (one row per period × category), or a wide period-by-category grid. Include a units line. For example:

```markdown
Units: weekly requests (millions)
Categories: <c1, c2, ... cN>
Periods: <p1 ... pM>

period, category, value
p1, c1, 12.4
p1, c2,  3.1
...
```

## Boundaries

- Do not choose a chart form or decide what matters - that is `dataviz-brief` and `dataviz-selector`.
- Do not drop a category because its values are hard to read; estimate it and keep it. Deciding a category is not key is the brief's job, made in message terms, not a consequence of extraction difficulty.
