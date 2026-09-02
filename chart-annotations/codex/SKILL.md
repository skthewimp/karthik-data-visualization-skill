---
name: chart-annotations
description: Annotate a chart only with a fact from outside the dataset that explains it - a rainy day, a regulation, an acquisition, a change of government. Use when a chart needs an on-chart mark for an external cause, an event, or a regime change the data itself cannot show. In-data quantities - "peak", "all-time high", "from X to Y", a rank, a trend, a crossover - are direct labels, not annotations; this skill also words and places those. Also use when annotation text is too long, too many marks compete, the mark repeats the title, or a number is not tied to a baseline.
---

# Chart Annotations

Own on-chart annotation and direct-label wording, visual weight, and placement. Do not choose the chart form, global visual system, adjacent explanatory note, critique structure, or release verdict; those belong to `dataviz-selector`, `karthik-data-visualization`, `chart-explainer`, `dataviz-critique`, and `dataviz-eval`.

## The one distinction everything rests on

**An annotation carries a fact that is not in the data.** A direct label carries a fact that is.

A chart's encoding - position, length, slope, colour - already draws every quantity in the dataset. That is what a chart *is*. So a callout of a quantity is never an annotation; it is a label, or it is nothing. An annotation exists only to add what the chart structurally cannot draw, because the fact lives outside the dataset:

- the spike is a rainy day, and rainfall is not a column in this data
- the level shifts because a regulation, a tax, or a ban came into force
- the trend breaks at an acquisition, a change of government, a war, a strike
- the series jumps because the definition or the collection method changed

None of that is in the picture. That is why it earns ink. The chart cannot show a cause it does not contain.

**Not an annotation - these are in the data, so they are labels or nothing:** "peak", "all-time high", "record low", "from X to Y", "+38%", "doubled", "up 9 points", a rank, a trend, a crossover, an inflection, a gap between two series. The reader already sees the shape; restating the shape in words adds nothing. If a specific number matters, print it as a **direct label** on the mark. If it does not matter enough to label, it does not matter enough to annotate.

## The bar this creates

You cannot get an annotation by looking at the chart harder. The fact comes from outside the dataset - the brief, the domain, the source, the person who owns the data - or you do not have it. **The default is no annotation, and most charts stay that way**, because most of the time no external fact is at hand. This is the whole gate: if you cannot name the outside event and where you know it from, there is nothing to mark. Do not invent a cause to fill the slot; a made-up "likely due to..." is worse than a blank chart. If you only *suspect* a cause, either leave it off or word it as coincidence in time (see honesty), never as explanation.

## Division of labour

- **Title** states the claim in words: *"Sales collapsed in the second quarter."*
- **Direct labels** carry the quantities that matter: the Q2 value on its mark.
- **Annotation** carries the outside cause the chart cannot draw: *"Factory shut for flood repairs."*

Three different jobs, no overlap. If your annotation restates the title, it is the title again - cut it. If it restates a label, it is the label again - cut it. It survives only if it says something neither the title nor the shape nor a label can.

## Honesty

- **Correlation is not cause.** Unless the causal link is established, word the mark as timing, not explanation: "coincides with the GST rollout", not "fell because of GST". "followed" and "coincides with" are honest; "caused by" is a claim you must be able to stand behind.
- **Cite where the fact comes from** when it is not common knowledge, so a reader can check it. An annotation is a factual assertion about the world, held to the same standard as any other.
- **Never manufacture the external fact.** No fact, no annotation.

## Direct labels

Labels are not annotations and carry no external bar - a value on a mark is always legitimate. The only discipline is restraint: **label the few marks that carry the point, not every mark.** Endpoints, the extreme, the one the claim rests on. On a multi-series or small-multiples chart, call `recommend_labels(series, max_labels_per_series)` to pick those points and leave the rest in the data. "Keep every value" means every value stays *reconstructable* - in a table or note - not that every point gets stamped, which just collides into a pile-up.

## Wording

- **Every number and every comparative word is computed, never typed.** A hand-typed count is wrong the moment a filter changes. **flat, unchanged, doubled, halved, steady** each assert a number - check it before you write it. "Flat for 45 years" is false if the slope is 1.5 points/decade, and a false mark is worse than none. Build the label string from the same computation that produced the mark.
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

- **Anchor on the datum, then offset into whitespace.** A group's centroid is the worst resting place - the densest part of the cloud. Anchor on the feature, push the text to the outside edge where no mark sits.
- Text must never sit on data, gridlines, or another label. A connector must never cross other data; use one only when proximity alone does not make the link clear.
- **Reserve room when setting scale limits, on every edge the text can reach** - labels clip left, right, top, and bottom. Extend the limits in the direction the text runs and turn clipping off; do not discover the clip after rendering.
- If no honest placement exists, change the chart - widen margins, expand the range, move the panel - before dropping the mark.

## Visual weight

- **Primary** (the annotation, or the one label the claim rests on): accent colour, bold, slightly larger; the datum it points at also takes the accent.
- **Supporting** (context labels, series names, period labels): grey, regular weight, smaller than the axis labels.

Never let the text outweigh the mark it explains. Series names, period labels, and axis units are orienting furniture - they do not compete with the annotation, but they must still be collision-checked against it.

## Render and inspect - mandatory

Placement cannot be verified from code. Export the image and look at it.

- Is any text clipped at a panel edge or running past the figure boundary?
- **Does each mark sit on the datum it describes?** Check one by hand - a label one row off looks perfectly fine.
- Does any text overlap data, an axis, or other text?
- Is the annotation the loudest thing after the data itself, and does the eye reach it before the supporting labels?
- At final output size, is the smallest text still legible?

Fix and re-render. Do not declare done from code inspection.

## Common mistakes

| Mistake | Fix |
|---|---|
| "Peak", "all-time high", "+38%", "doubled", "X → Y" marked as an annotation | That is in the data. It is a direct label, or nothing - not an annotation |
| A cause invented to fill the annotation slot | No external fact, no annotation. A made-up "likely due to" is worse than blank |
| "Caused by X" from a coincidence in time | Word it "coincides with" / "followed"; claim cause only if established |
| Annotation restates the title | Cut it; the title already said it |
| Every point labelled | Label the few marks that carry the point; leave the rest reconstructable in the data |
| Hand-typed count or "flat"/"doubled" never checked | Numbers and comparative words are computed from the same data as the mark |
| Text clipped at a panel edge | Reserve axis headroom in the direction the text runs |
| Group label parked at the cluster centroid | Anchor on the group, offset to the outside edge |
| External fact asserted with no source | Cite where it comes from; it is a factual claim about the world |
| Declared done without rendering | Export and inspect |

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and surrounding style. Use `dataviz-critique` when reviewing someone else's annotated chart, `dataviz-fix` when the whole chart enters a repair loop. In the construct pipeline (`dataviz-construct`), the insight stage (`karthik-evidence-builder`) decides the headline claim and any external-fact annotations; this skill is loaded at build to word and place them and the direct labels.
