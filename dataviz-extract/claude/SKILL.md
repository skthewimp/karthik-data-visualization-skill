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

1. **The category members**, one per visually distinct series - listed by name where the source identifies them. If the chart encodes more distinct series than the legend names, still list every distinct series: name the ones you can and label the rest generically (an unlabelled series is still a row). Never shrink the category count to only the ones you could name - a missing label is not a missing category. A series you cannot read is carried by its position with an explicit placeholder (`series 4`, `[unreadable]`, `[partial: "GP…"]`), never a plausible name filled in from the headline, a neighbouring label, or what a model "should" be called.
2. **The periods or x-positions**, listed - and alongside them the axis anchors exactly as printed: every legible axis tick label (a year, a category name, a value gridline), its position, and the axis's stated meaning and unit. Tick labels are read directly off the image, not inferred - preserve them exactly, and keep them separate from any finer per-observation position you infer. Uncertainty about where an individual observation sits inside a labelled interval (which month within a printed year, which day within a printed week) never licenses discarding the coarser labels the axis actually prints: carry the printed labels through, and record the finer uncertainty on its own. Synthetic sequential ids (P01, P02 ...) stand in for positions only when the axis prints no labels at all - never as a replacement for labels you could read.
3. **A value for every (period × category) cell.** No gaps. If a cell cannot be read, estimate it - but it must exist.
4. **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

- Use exact values when the prompt supplies them or they are printed as source labels.
- Reading values off an image is inherently approximate - self-evident, so it doesn't need announcing on the chart or repeating through the brief. Don't fabricate precision (no digits the image can't support, no rounding toward rounder numbers), but don't hedge every number either; the messages rarely depend on exact precision, and reading difficulty is never a reason to drop a category. Keep per-cell confidence for your own reasoning, not as chart furniture. At most one plain source line ("reconstructed from the source image"), and only if the medium expects a source note.
- **Values may be estimated; labels may not be invented.** A cell value can be read approximately to fill the grid - that is estimation within a known scale. A category name, series label, or axis tick is read-only text, like a printed tick: you read it off the image, or you carry it as an explicit placeholder tied to its position. Never manufacture a plausible-sounding name from the headline, a neighbouring label, or what a thing "should" be called - and never normalise a name you did read toward a more familiar one your prior expects (snapping an unfamiliar label to the nearest well-known name is the same fabrication, driven by the prior instead of a gap). A label that reads as novel or unexpected is data as-read; when the letters don't resolve, placeholder them rather than round to a name you recognise. A confident wrong name is worse than a blank one - it looks real, so every downstream gate passes it through. The pressure to keep every category and fill every cell is about count and values; it is never a licence to invent identity.
- Don't invent categories or periods not in the source, or silently merge series. If a region is genuinely unreadable, note the cells you were least sure of when handing the table on - internally, not as a caption.

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
- Do not replace readable axis labels with synthetic indices because individual observations are hard to place. A printed label is directly-read data; erasing it over per-observation uncertainty discards information the source actually gave you, exactly as dropping a hard-to-read category would.
