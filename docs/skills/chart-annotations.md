# Chart Annotations Skill

`chart-annotations` decides what a chart should mark, and what the mark should say. Its whole discipline rests on one distinction.

## The one distinction

**An annotation carries a fact that is not in the data. A direct label carries a fact that is.**

A chart's encoding - position, length, slope - already draws every quantity in the dataset. So a callout of a quantity is never an annotation; it is a label, or it is nothing. An annotation exists only to add what the chart structurally cannot draw, because the fact lives outside the data:

- the spike is a rainy day, and rainfall is not a column in this data
- the level shifts because a regulation, a tax, or a ban came into force
- the trend breaks at an acquisition, an election, a war, a strike
- the series jumps because the definition or the collection method changed

**Not an annotation, and mostly not a label either** - a change or comparison ("from X to Y", "+38%", "doubled", "up 9 points", "peak", "all-time high", a rank, a crossover, a gap) narrates the shape the chart already draws. It is not an annotation (it is in the data) and not a direct label (a label carries one mark's *value*, not a movement). "42% → 37%" belongs nowhere on the plot - the claim goes in the title, in words, or is left off. The only in-data text on the chart is a direct label: a single mark's value, on the few points that carry the claim.

## The bar this creates

You cannot get an annotation by looking at the chart harder. The fact comes from outside the dataset - the brief, the domain, the source, the person who owns the data - or you do not have it. **The default is no annotation, and most charts stay that way.** If you cannot name the outside event and where you know it from, there is nothing to mark. A cause invented to fill the slot - a made-up "likely due to..." - is worse than a blank chart.

This is why the skill needs no value-earning gate and no list of what "qualifies": a fact is external, or it is not. There is nothing to rationalise.

## Trigger examples

```text
The spike in March - can I mark what caused it on the chart?
```

```text
The annotation says "fell because of the new tax" - is that right, or should it say "coincides with"?
```

```text
I've labelled every point and it's a mess. Which few should carry labels?
```

## The core moves

**Title states, labels quantify, annotation explains.** Three jobs, no overlap. The title carries the claim in words; direct labels carry the quantities that matter; the annotation carries the outside cause the chart cannot draw. If your annotation restates the title or a label, cut it.

**Correlation is not cause.** Unless the causal link is established, word the mark as timing, not explanation - "coincides with the GST rollout", not "fell because of GST". Cite where the fact comes from; an annotation is a factual claim about the world.

**A label is one mark's value; label only the few that carry the point.** Not a change, rank, or comparison - those narrate the shape and go in the title. Labels carry no external bar - a single value is always legitimate - but a wall of 200 values is as unreadable as clutter callouts. Endpoints, the extreme, the one the claim rests on. "Keep every value" means every value stays reconstructable in the data, not printed on the chart.

**Compute every number and every comparative word.** A hand-typed count is right until a filter changes and then silently wrong. "Flat", "doubled", "unchanged" are quantitative claims in plain clothes - a label reading "flat for the 45 years before" is false if that period rises 1.5 points per decade, and a false mark is worse than none.

**Placement by proximity.** Anchor the mark to the datum it explains and compute the offset from it, so it stays correct under filtering and rescaling. Bare text in whitespace next to the thing; a hairline connector only when the nearest free space is ambiguous, and never crossing data. Anchor on a group, then offset to the outside edge - a centroid is the worst resting place.

**Reserve room in the scale limits.** Text clips on every edge. Extend the limits in the direction the text runs and turn clipping off before rendering, not after.

**Render and inspect.** Placement cannot be verified from code. Export the image, check each mark sits on the datum it describes, look for clipping and collisions, fix, re-render.

## Where the rule comes from

An earlier version of this skill tried to police annotations with a value bar - "mark the interesting data feature, then filter out the ones that restate what the reader already sees." Every failure produced a new clause, and the model found a new loophole around each one ("it's a ratio, so it reframes"). The apparatus grew; the bar did not. The fix was to stop describing worth and change the category: annotations are external facts, quantities are labels. A model cannot manufacture an external fact from the data, so the over-generation it kept doing has nowhere to come from.

## Relationship to other skills

Run `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and surrounding style; this skill sets only the annotation's own weight relative to the data. Use `dataviz-critique` when reviewing an existing annotated chart. In the construct pipeline, the insight stage (`karthik-evidence-builder`) names any external-fact annotation; this skill words and places it and the direct labels at build.
