---
name: dataviz-extract
description: Read the full period-by-category data table out of a chart image by vision - every value for every period and every series - so a repair can rebuild from data, not from the picture.
---

# Dataviz Extract

Use this during a chart repair, in parallel with `dataviz-brief`, to recover the underlying data from the source image. The rebuild is designed forward from this table plus the brief - not traced from the source picture - so the table must be complete enough to build any chosen form on.

This is a vision task, but the value read is not a single "look and say a number" guess. A guessed absolute magnitude is the read models are worst at - fuzzy, biased toward round numbers, and worse still on a log axis. And a lone glyph read of a printed label is no safer: a `6%` transcribed as `0%`, a decimal shifted, a thousands separator dropped, a `3` read as an `8` all leave the pass unchallenged when nothing else grounds the number. So read **every** cell the same way - one path, not two - grounding the value in the mark's position whether or not a label is printed:

- **Always read the mark's position.** Name the two nearest printed reference ticks that bracket the mark and the fraction (0-1) of the way from the lower to the upper. This is a judgment models read reliably; it stays local, so scale error does not accumulate; and a log axis needs no special reasoning - the same two-ticks-and-a-fraction read interpolates in log space. It only has to be coarse enough to say **which band** the mark sits in.
- **If a label is printed, transcribe it too** - glyph by glyph, at resolution - and read it *together with* the position, in the same pass. Then pick the value once, inline:
  - the transcribed label falls inside (or one neighbour past) the band the mark sits in → use the label; the position confirmed it and the label carries the exact digits.
  - the label lands nowhere near the band → the transcription is a gross misread (`6`→`0`, a decimal shift, a dropped separator all blow whole bands past the mark) → trust the position and move on.

  This is one shot, not a loop: hold both numbers at once, pick, emit. No flag, no re-read stage. Occasionally wrong is fine; a second pass is not the goal.
- **If no label is printed,** the position *is* the value.

Do the position arithmetic with the `read_marks_from_anchors` MCP tool - the normal path for **every** cell now, labelled or not: pass each mark as `{key, lo, hi, fraction}` (the two bracketing tick **values** and the fraction between them) and the axis `transform` (`linear` or `log`), and it returns the position values you reconcile the labels against. The tool does the scale arithmetic the model slips on; the perception - which ticks bracket the mark, how far between - stays with you. If the MCP server is genuinely not available, interpolate the bracket by hand the same way (`lo + fraction*(hi-lo)`, or the log-space form) - never fall back to eyeballing an absolute value.

## What to produce

The **full period-by-category table**: a value for every period and every category, series, stack, or facet the chart encodes. Colour is data, not decoration - a chart encoding N series across a period needs N values for that period, not one total. The envelope, the totals, or the top line alone are not enough; any later form change needs each cell.

Produce, explicitly:

1. **The category members**, one per visually distinct series - listed by name where the source identifies them. If the chart encodes more distinct series than the legend names, still list every distinct series: name the ones you can and label the rest generically (an unlabelled series is still a row). Never shrink the category count to only the ones you could name - a missing label is not a missing category. A series you cannot read is carried by its position with an explicit placeholder (`series 4`, `[unreadable]`, `[partial: "GP…"]`), never a plausible name filled in from the headline, a neighbouring label, or what a model "should" be called.
2. **The periods or x-positions**, listed - and alongside them the axis anchors exactly as printed: every legible axis tick label (a year, a category name, a value gridline), its position, and the axis's stated meaning and unit. Tick labels are read directly off the image, not inferred - preserve them exactly, and keep them separate from any finer per-observation position you infer. Uncertainty about where an individual observation sits inside a labelled interval (which month within a printed year, which day within a printed week) never licenses discarding the coarser labels the axis actually prints: carry the printed labels through, and record the finer uncertainty on its own. Synthetic sequential ids (P01, P02 ...) stand in for positions only when the axis prints no labels at all - never as a replacement for labels you could read. A period is a position the source plots values at. One named only in a title, legend or note, with no marks drawn for it (a note that its values are withheld), is not a position to carry: record it as context for the caption, never as a row, a gap, or an axis tick - the rebuild ticks where there is data.
3. **A value for every (plotted period × category) cell.** No gaps. If a cell cannot be read, estimate it - but it must exist.
4. **Units and any transformation** visible on the source (counts, %, index, log axis, share-of-total, cumulative), so the rebuild does not silently change the measure.

## Precision and honesty

- Use exact values when the prompt supplies them or they are printed as source labels.
- Reading values off an image is inherently approximate - self-evident, so it doesn't need announcing on the chart or repeating through the brief. Don't fabricate precision (no digits the image can't support, no rounding toward rounder numbers), but don't hedge every number either; the messages rarely depend on exact precision, and reading difficulty is never a reason to drop a category. Keep per-cell confidence for your own reasoning, not as chart furniture. At most one plain source line ("reconstructed from the source image"), and only if the medium expects a source note.
- **Values may be estimated; labels may not be invented.** A cell value can be read approximately to fill the grid - that is estimation within a known scale. A category name, series label, or axis tick is read-only text, like a printed tick: you read it off the image, or you carry it as an explicit placeholder tied to its position. Never manufacture a plausible-sounding name from the headline, a neighbouring label, or what a thing "should" be called - and never normalise a name you did read toward a more familiar one your prior expects (snapping an unfamiliar label to the nearest well-known name is the same fabrication, driven by the prior instead of a gap). A label that reads as novel or unexpected is data as-read; when the letters don't resolve, placeholder them rather than round to a name you recognise. A confident wrong name is worse than a blank one - it looks real, so every downstream gate passes it through. The pressure to keep every category and fill every cell is about count and values; it is never a licence to invent identity.
- Don't invent categories or periods not in the source, or silently merge series. If a region is genuinely unreadable, note the cells you were least sure of when handing the table on - internally, not as a caption.

## Output shape

A tidy long table is preferred (one row per period × category), or a wide period-by-category grid. Include a units line. One row is one observation - one mark:

- A number printed beside a mark but not drawn by it (a growth rate on a revenue bar, a share printed on a count) is its own column on that mark's row, with its unit in the column name. Never give it rows of its own: a "YouTube Ads growth" row is a second observation the chart does not have, and it lands on the value scale as if it were revenue.
- A mark drawn between two numbers (a stacked or floating segment, a range, a dumbbell) carries both ends as columns, as read. Carry a printed value beside them if the chart prints one.
- A visible mark is read from its geometry like any other, printed label or not. A cell with nothing to read stays empty: never compute it from its neighbours (the residual of a 100% bar) and carry it as if read.

For example:

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
