---
name: chart-annotations
description: Annotate a chart only with a fact from outside the dataset that explains it - a rainy day, a regulation, an acquisition, a change of government. Use when a chart needs an on-chart mark for an external cause, an event, or a regime change the data itself cannot show. In-data quantities - "peak", "all-time high", "from X to Y", a rank, a trend, a crossover - are direct labels, not annotations; this skill also words and places those. Also use when annotation text is too long, too many marks compete, the mark repeats the title, or a number is not tied to a baseline.
---

# Chart Annotations

Own on-chart annotation and direct-label wording, visual weight, and placement. Don't choose the chart form, global visual system, adjacent explanatory note, critique structure, or release verdict; those belong to `dataviz-selector`, `karthik-data-visualization`, `chart-explainer`, `dataviz-critique`, and `dataviz-eval`.

## The one distinction everything rests on

**An annotation carries a fact that is not in the data. A direct label carries a fact that is.**

A chart's encoding - position, length, slope, colour - already draws every quantity in the dataset. So a callout of a quantity is never an annotation; it is a label, or nothing. An annotation exists only to add what the chart structurally cannot draw, because the fact lives outside the dataset:

- the spike is a rainy day, and rainfall is not a column here
- the level shifts because a regulation, tax, or ban came into force
- the trend breaks at an acquisition, a change of government, a war, a strike
- the series jumps because the definition or collection method changed

None of that is in the picture - that is why it earns ink.

**A change or comparison is neither annotation nor label.** "from X to Y", "+38%", "doubled", "up 9 points", "peak", "all-time high", "record low", a rank, a crossover, a gap between two series - all narrate the shape the encoding already draws. "42% → 37%" belongs nowhere on the plot; the claim goes in the **title**, in words, or is left off. The only in-data text that earns a place on the plot is a direct label: one mark's value, on the few marks that carry the point.

## The bar this creates

You cannot get an annotation by looking at the chart harder - the fact comes from outside the dataset (the brief, the domain, the source, the data owner) or you don't have it. **The default is no annotation, and most charts stay that way.** If you can't name the outside event and where you know it from, there is nothing to mark. Don't invent a cause to fill the slot; a made-up "likely due to..." is worse than a blank chart. If you only *suspect* a cause, leave it off or word it as coincidence in time (see Honesty), never as explanation.

## Division of labour

Three jobs, no overlap:

- **Title** states the claim in words: *"Sales collapsed in the second quarter."*
- **Direct labels** carry the quantities that matter: the Q2 value on its mark.
- **Annotation** carries the outside cause the chart can't draw: *"Factory shut for flood repairs."*

If an annotation restates the title or a label, cut it. It survives only if it says something neither the title, the shape, nor a label can.

## Honesty

- **Correlation is not cause.** Unless the causal link is established, word the mark as timing: "coincides with the GST rollout", not "fell because of GST". "followed"/"coincides with" are honest; "caused by" is a claim you must stand behind.
- **Cite where the fact comes from** when it isn't common knowledge - an annotation is a factual assertion about the world.
- **Never manufacture the external fact.** No fact, no annotation.

## Direct labels

A direct label is **one mark's value** or its name - "42%", "Karnataka", the endpoint's number - never a change, rank, or comparison. Labels carry no external bar (a single value on a mark is always legitimate) but need the same restraint as annotations: **label only the few marks that carry the point** - endpoints, the one extreme, the mark the claim rests on. A chart stamped with 200 values is as unreadable as one full of callouts. On a multi-series or small-multiples chart, call `recommend_labels(series, max_labels_per_series)` to pick those points. "Keep every value" means every value stays *reconstructable* in a table or note, not that every point gets stamped.

## Wording

- **Every number and comparative word is computed, never typed.** A hand-typed count is wrong the moment a filter changes; **flat, unchanged, doubled, halved, steady** each assert a number - check it before writing it ("Flat for 45 years" is false if the slope is 1.5 points/decade). Build the label string from the same computation that produced the mark.
- Keep each mark concise and single-purpose. Name the outside event plainly; tie any number to its baseline and window.

## Placement

Anchor a mark to the datum it explains, so it stays correct under filtering, sorting, and rescaling. Compute the offset from that datum and let the plotting layer position the text; `annotate()` with literal coordinates is fine only for chart furniture (a period band, a reference caption), never for anything pointing at an observation.

```r
ann <- d %>%
  filter(quarter == "2024 Q2") %>%
  mutate(x = quarter, y = sales + 40,
         label = "Factory shut for flood repairs")

geom_text(data = ann, aes(x, y, label = label), hjust = 0, ...)
```

Where the harness ships forward placement tools, let them settle the geometry deterministically: `reserve_frame` fixes the title, caption, axis, and legend bands blind so the plot area is known before anything is drawn, and `place_on_marks` projects the annotated datum to its real pixel position (from one measure render), anchors the text, and de-collides it against marks and other labels through `recommend_text_placement`. Pass `plot_area` so a callout straddling the plot edge is pulled inside. When the tool returns a leader, draw the connector from its `leader_line_data` and place the text at its `placed_data` (native data coordinates) rather than improvising a `geom_segment` by eye - a guessed endpoint misses the datum and runs the connector through another mark. A free callout tied to no single datum routes through `recommend_text_placement` directly. Where those tools are absent, apply the same principles by eye:

- **Anchor on the datum, then offset into whitespace.** A group's centroid is the worst resting place; push the text to the outside edge where no mark sits.
- Text must never sit on data, gridlines, or another label. A connector must never cross other data; use one only when proximity alone doesn't make the link clear.
- **Reserve room for text in the margin, not by stretching the data scale.** Labels clip on every edge the text can reach, so make the room before rendering - widen the plot margin (or let `reserve_frame` reserve the band) rather than extending the axis limits to hold non-data content, and never reserve the same room twice. Turn clipping off; don't discover the clip after rendering.
- If no honest placement exists, change the chart (widen margins, expand the range, move the panel) before dropping the mark.

## Visual weight

- **Primary** (the annotation, or the one label the claim rests on): accent colour, bold, slightly larger; the datum it points at also takes the accent.
- **Supporting** (context labels, series names, period labels): grey, regular weight, smaller than axis labels.

Never let the text outweigh the mark it explains. Orienting furniture (series names, period labels, axis units) doesn't compete with the annotation but must still be collision-checked against it.

## Render and inspect - mandatory

Placement cannot be verified from code. Export the image and look:

- Is any text clipped at a panel edge or running past the figure boundary?
- **Does each mark sit on the datum it describes?** Check one by hand - a label one row off looks fine.
- Does any text overlap data, an axis, or other text?
- Is the annotation the loudest thing after the data itself, reached before the supporting labels?
- At final output size, is the smallest text still legible?

Fix and re-render. Don't declare done from code inspection.

## Common mistakes

| Mistake | Fix |
|---|---|
| "Peak", "+38%", "doubled", "X → Y" put on the chart | Change/comparison narration - the shape already shows it. Neither annotation nor label; the claim goes in the title, or nowhere |
| A direct label that is a change, not a value | A label is one point's value; the change is the shape. Label an endpoint's value if it matters, not the movement |
| A wall of values - every point labelled | Label only the few marks the claim rests on; the rest stay reconstructable in the data |
| A cause invented to fill the annotation slot | No external fact, no annotation. A made-up "likely due to" is worse than blank |
| "Caused by X" from a coincidence in time | Word it "coincides with"/"followed"; claim cause only if established |
| Annotation restates the title | Cut it; the title already said it |
| Hand-typed count or "flat"/"doubled" never checked | Numbers and comparative words are computed from the same data as the mark |
| Text clipped at a panel edge | Reserve room in the margin (or via `reserve_frame`), not by stretching the data scale |
| Group label parked at the cluster centroid | Anchor on the group, offset to the outside edge |
| External fact asserted with no source | Cite where it comes from; it is a factual claim about the world |
| Declared done without rendering | Export and inspect |

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open, `karthik-data-visualization` for palette/typography/surrounding style, `dataviz-critique` when reviewing someone else's annotated chart, `dataviz-fix` when the whole chart enters a repair loop. In the construct pipeline (`dataviz-construct`), the insight stage (`karthik-evidence-builder`) decides the headline claim and any external-fact annotations; this skill is loaded at build to word and place them and the direct labels.
