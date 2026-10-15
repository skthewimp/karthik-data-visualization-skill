---
name: dataviz-eval
description: Decide whether a rendered chart can be sent as it is, needs a revision, or needs a different form, and list every real problem ranked by how much it matters.
---

# Dataviz Eval

Decide whether a rendered chart can go out. Eval gives the verdict and the list of problems. It does not redraw the chart.

## What eval checks

Four things, in this order of importance:

1. **The analysis is right.** The values match the data or source. The measure suits the claim (a rate or share where raw totals would mostly show size, a total where the claim is about volume). The scale and baseline don't exaggerate or hide the change. Panels that compare levels share a scale. The title claims no more than the chart shows, and keeps its subject and scope: who, where, what.
2. **The point lands fast.** At a quick look the reader gets one clear point, and the eye lands on the finding first, not on furniture or a decorative highlight. The form makes the comparison directly: positions on a common scale, a sorted dimension, lines the eye can follow. Categories and panels are in a meaningful order.
3. **It reads at the size it will be seen.** Judge the exported image at display width, not native pixels. Effective text size is rendered size times display width over image width. When the display width isn't stated, assume a content column or chat bubble, well under a 1200 px export. Text the reader has to zoom for blocks the read; text that reads but is on the small side (under about 10 px at display width, roughly 19 px in a 1200 px image shown at 640 px) is polish. So do overlaps, clipping, labels away from their marks, ticks that collide, and series the reader has to tell apart by near-identical colours. The canvas should fit the content: a grid crammed into a narrow canvas, data in a small corner of the image, or big margins reserved for text all shrink what matters.
4. **No junk on the chart.** Copy talks about the data, never about how the chart was made: no "approximate", "reconstructed", "values read from the source", "not shown in the source". Qualifications about the data's world (projected, provisional, excludes X, fiscal year, survey population) are content and stay. A subtitle adds a fact the title doesn't. An axis title, legend or note that only repeats what the ticks, direct labels or title already say is junk. Numbers carry the digits needed to see the difference, not the digits the source printed (`dataviz-precision`).

## Karthik's preferences

Judge against these. A chart that follows them is not wrong for doing so.

- **Name things on the chart, not in a legend.** Label series at their line ends and bars with their values. When end labels would collide, nudge them apart with leader lines rather than fall back to a legend.
- **Labels replace axes.** When endpoints or every bar carry their values, the value axis and gridlines go. A year or date axis gets no axis title.
- **Points on lines.** Mark each observation on a time series.
- **Fit the axis to the data.** A rate moving from 52% to 58% gets an axis around that range, not 0-100%.
- **Whole numbers when the spread allows.** Values spread over tens of points read as 23%, not 23.4%.
- **Claim titles.** The title states the finding. A subtitle is optional, not expected.
- **Definitions and source sit on the chart, small.** A metric definition ("draws count as half a win") goes in a footnote; a short source line sits at the bottom.
- **Events get a dotted line and a two- or three-word label**, not a paragraph and not nothing.
- **One item among several: shared panel while it stays readable, small multiples once it crowds.** Up to about five lines can share a panel with the focal one coloured and the rest muted; beyond that, or whenever the lines tangle, small multiples with the focal item first. Trade crowding against too many panels.
- **Small multiples of very different sizes use free scales**, so each panel's shape shows.
- **Explain the shape.** Two or three short callouts on the peaks, dips or turns that matter are welcome on a published chart; they explain the data, they don't restate it.
- **Neutral marks can still have colour.** With no focal item, one colour for all marks is right, and it needn't be grey.
- **Few parts, a pie is fine.** A labelled pie works for two or three parts; sorted bars aren't required.
- **Shares over time are lines**, one per part and labelled at the end, not stacked areas or bars.
- **Different units get separate panels** on a shared time axis, never a dual y-axis.
- **Values spanning orders of magnitude get a log axis.**
- **Many metrics for many items can be a table.** A sorted table with light emphasis is a fine answer for dense lookup; it needn't be forced into a chart.

## How strict

**Send unless something misleads or blocks a quick read.**

- **Must fix** - the chart misleads (wrong value, wrong measure, distorting scale, a claim the data doesn't support), or the reader can't get the point without effort (unreadable text, overlaps, a form that hides the comparison, colours that can't be told apart where it matters).
- **Polish** - anything else that would make it better. Listed, never required.

Verdicts:

- **Send** - no must-fix problem. Polish may be listed. A clean chart passes: say so and stop. Don't invent a problem to justify another round.
- **Revise** - the form works but at least one must-fix problem needs a bounded change. Execution, copy, layout and legibility problems, however many, are `Revise`.
- **Redesign** - the form can't carry the point, or the question itself is wrong. Say which, so `dataviz-critique` or `dataviz-selector` can rerun. A form that works when a different one would be a bit clearer is `Send`, with the alternative listed as polish.
- **Not evaluable** - the image can't be inspected, or the verdict depends on information you don't have.

## Ground rules

- **Look at the actual export** at display size. A preview or code is not the chart.
- **Only the user's stated constraints bind.** "Keep the bars" or "only change the title" are conditions. The creator's own choices (canvas, form, legend, notes) are what you are judging.
- **Don't ask for what the evidence can't supply.** If the unit, population or source isn't known, its absence isn't a problem, and no fix may ask the creator to invent it.
- **Every problem names what the reader loses**: what becomes misleading, unreadable or slow to get. A contrast that already reads or a palette that already separates is not a problem.
- **List every problem, not just the first.** A review that names one issue and calls the rest fine sends the chart round the loop once per issue.
- **Fixes remove before they add.** The fix for a hedge is to delete it; the fix for a repeated axis title is to drop it.
- **An honest null is fine.** If the point is "no clear pattern", judge whether the reader gets that, not whether the story is dramatic.

## Output

```markdown
**Verdict:** Send / Revise / Redesign / Not evaluable - one sentence why.

1. [Must fix] <element> - <problem> - <reader loses> - <fix>
2. [Must fix] ...
3. [Polish] ...
```

Rank by how much the reader loses, must-fix first. One line each. No tables, no codes.

## Stop

Stop when nothing must-fix remains. Hand executable fixes to `dataviz-fix`; send form problems to `dataviz-critique`.
