---
name: chart-annotations
description: Decide what to mark on a chart, how to rank competing candidates, how to word the label, and where to place it. Use when a chart needs on-chart annotation, callouts, direct labels for a key point, event markers, threshold lines, knee-bend or inflection labels, outlier calls, highlighted bars or points, or when a chart is finished but the reader cannot see the point without narration. Also use when annotation text is too long, too many things are marked, the label repeats the title, or a marked number is not tied to a stated baseline.
metadata:
  short-description: Choose, rank, word, and place chart annotations
  claude-description: "Choose what to mark on a chart, rank competing candidates, word the label tightly, and place it without clutter."
---

# Chart Annotations

Own on-chart annotation selection, wording, visual weight, and placement. Do not choose the chart form, global visual system, adjacent explanatory note, critique structure, or release verdict; those belong to `dataviz-selector`, `karthik-data-visualization`, `chart-explainer`, `dataviz-critique`, and `dataviz-eval`.

Use this when a chart exists or is being built and the reader should not have to infer the point. Annotation is not decoration and not a caption. It is the act of marking the specific evidence that carries the claim.

This skill covers four decisions: what to mark, which candidate wins, how to word it, where to put it.

## Division of labour: title vs annotation

**The title states the claim in words. The annotation locates it on the chart.**

Do not write the same sentence twice.

```text
Title:       Haryana saw the sharpest per-capita jump
Annotation:  +38%          <- placed at the Haryana point
```

If the annotation is a full sentence restating the title, cut it to the locating fragment. If the title is a neutral chart description while the annotation carries the whole argument, move the claim up into the title.

**They must be the same claim.** The opposite failure to repetition is divergence: a title about the whole cloud ("cities with low literacy are also the least equal") with an annotation about a subgroup ("Rajasthan holds 12 of the 20 widest gaps"). Both may be true, and the chart still fails, because the reader is handed two findings and told which to care about by neither. Decide which claim the chart is making, put it in the title, and mark the evidence for that one. The other claim is a second chart.

Exception: a chart designed to travel alone with no title bar or surrounding text may carry the claim in the annotation. State that this is the case before doing it.

## Workflow

1. Take the one-sentence claim the chart must support. In the construct pipeline this is the **headline claim** from the insight stage (`karthik-evidence-builder`), and the marks worth considering arrive as its `candidate_annotations` (each a claim tied to the datum that supports it) - your job is to rank, word, and place them, not to originate a different claim. Standalone, write the claim yourself.
2. Enumerate annotation candidates from the chart's geometry, folding in any `candidate_annotations` the insight stage supplied.
3. Run the concentration check.
4. Apply the value-add gate - drop candidates that only restate a label, axis, or obvious rank, or that recompute what labelled marks already show - then rank the survivors by relevance to the chart's claim, evidentiary strength, reader payoff, and visual salience.
5. Select only as many as the chart can support without competing claims; there is no universal count, and none is the common, correct answer.
6. Write each label so it identifies the evidence and qualifies the claim appropriately.
7. Place by proximity, with coordinates derived from the data; add a connector only if proximity fails.
8. Render, inspect the image, fix collisions.

## Step 2: candidate inventory

Look at the rendered shape, not the summary statistics. Candidates:

- knee-bend or visible slope change; inflection point
- local maximum or minimum; temporary peak or trough
- crossover where two series swap order
- threshold breach; record or boundary value
- start and end of a run or streak
- event date with a visible before/after difference
- outlier far from the pattern
- the gap between two series at a specific point
- first or last observation when the endpoint is the point

An absence - no trend, no gap, no change - is a finding, but it is not a candidate here. It goes in the title and gets no mark (see "When nothing clears the bar").

Separate observed candidates from derived ones as you list them. A record year, a crossover, and an actual gap are **observed** - they are in the data. A knee from a breakpoint scan, a trend slope, a smoothed peak, a cluster boundary are **derived** - they are outputs of a model you chose. Derived features are annotatable, but they carry a higher bar (see "Annotating derived features").

## Step 3: concentration and candidate strength

Before annotating an aggregate or apparent feature, inspect how the evidence is distributed, concentrated, and uncertain. If a subset materially changes the interpretation, expose it. Choose thresholds and robustness checks appropriate to the metric and claim rather than applying fixed percentages or universal tests.

Rank candidates by relevance to the stated claim, evidentiary strength, interpretive value, and visual salience. Records, departures, events, persistence, gaps, and other features are candidate classes, not a fixed hierarchy.

Distinguish observed description, exploratory signal, and inferential claim. Annotate a feature when it is relevant and accurately qualified; use uncertainty, sensitivity checks, or tentative wording when evidence is limited. If no feature clears the claim's evidentiary and communication bar, leave the chart unmarked and state the absence in the title or accompanying explanation.

**The value-add gate: reject restatements before you rank.** An annotation earns ink only when its content cannot be recovered from the marks the reader already sees - their direct labels, the axes, and the title - and it carries the chart's one claim. Before ranking, drop every candidate that only: restates a value a direct label or axis tick already prints; names a rank or extreme the geometry already shows (a 'highest' or 'peak' callout on the visibly tallest, already-labelled mark); or restates a change two labelled endpoints already display ('up 9 points' when both ends are labelled).

**Aggregate and difference are forms, not licenses.** Summing two labelled series, subtracting two labelled endpoints, or averaging a handful of visible values is arithmetic the reader does at a glance from numbers already on the chart. That it took a calculation to produce does not exempt it - it is a restatement wearing a computation's clothes, and it drops like any other. A callout of the form "A + B: 30 -> 35" next to two series whose endpoints are already labelled, or "+11 points" between two printed values, adds nothing the eye did not already have. The recovery test is *effort*, not whether a calculation exists: what survives is a quantity the reader genuinely cannot get by eye - a share or rank across many *unlabelled* marks, a ratio or multiple that reframes the comparison (not a one-step subtraction of two visible numbers), a count over a long run - together with what is not in the chart at all: a cause, a consequence, the meaning of a threshold crossed, outside context, or attention pulled to a feature easy to miss (a crossover, an inflection). Rank only the survivors, and among them keep only the ones that carry the claim; a true but incidental aggregate is still cut. When the title and direct labels already deliver the claim, the honest annotation count is zero - default there rather than manufacturing a computed callout to fill the space.

**The survivor list is a filter, not a menu.** These categories describe what *can* clear the bar; they are not a checklist to satisfy, and clearing one ("this is technically a ratio", "this is a rank") does not by itself earn a mark. The quantity must be the thing the chart's claim actually rests on and non-obvious enough that marking it changes what the reader takes away. If you find yourself constructing a ratio, a rank, or a comparison mainly so the chart has something to point at, that is the signal to place none. The mechanical half of this - an annotation whose one data value a nearby on-mark `data_label` already prints - is caught at build by `recommend_text_placement`, which returns those ids in `redundant_annotations`; drop them.

## Annotating derived features

- **Validate before marking.** A breakpoint, trend, smoothed peak, or cluster boundary is a chosen or model-derived feature; test sensitivity or word it as approximate.
- **A split point chosen by eye is derived too.** Test it or describe it as approximate, and describe both sides honestly.
- **Word it with the uncertainty the method carries.** "around the mid-1950s" is honest for a scanned breakpoint; "in 1956" claims a precision the method does not have. Do not put a bare year on a derived knee unless the year is itself the result.
- **Keep the evidence visible.** A fitted or smoothed layer must not become more persuasive than the observations it summarizes.

## Step 5: whether to annotate, then how many

**Start from zero, not from one.** The default annotation count is none. A chart whose title states the claim and whose key marks are directly labelled is already finished - and most charts are. Do not begin with a slot to fill. Add the first annotation only when a specific mark clears the value-add gate *and* the reader would genuinely miss or misread the claim without it; add a second only when it independently survives the same test. Never place an annotation to look thorough, to balance the composition, to use empty space, or because a chart "ought to have one". If you cannot name what the reader loses when you delete it, it should not be there.

Only if the chart is annotated at all: keep a single clear primary focus, and size the rest to density, medium, and traceability. Additional labels are acceptable when they improve identification without creating clutter; split the chart when competing claims cannot be separated.

**Contrast pairs are one annotation, not two.** When a claim is inherently about two ends - the highest and the lowest, the state that breaks the pattern against the one that follows it - the two labels are halves of a single point and share equal weight. Do not tier them into primary and supporting; that would say one end matters more, when the comparison is the finding. A contrast pair spends the primary slot; at most one supporting annotation may follow it, and often none should.

Orienting labels are a separate class and do not count against the cap: series names, period labels, axis units, a legend replacement. They must still be collision-checked against the claim annotations - a period label sitting on top of the primary annotation is the same defect as two annotations overlapping.

**"Keep every value" preserves data, not ink.** A request to keep every visible value means every value must survive in the chart's data - reconstructable, in a table or note - not that every point gets a printed label. Stamping a label on all of them collides into a repeated-value pile-up; that is the failure, not the fix. On a multi-series or small-multiples chart, call `recommend_labels(series, max_labels_per_series)` for the points that earn ink - endpoints, extremes, and the largest changes - and leave the rest in the data.

## Step 6: writing the label

**Every number and every comparative word in a label must be computed, never typed.**

Position is not the only thing that drifts. A hand-typed count that was right when you wrote it is wrong after a filter changes, and nothing in the chart will tell you. Build the label string from the same computation that produced the mark:

```r
mutate(lbl = paste0("Rajasthan: ", sum(top$state == "Rajasthan"),
                    " of the 20 widest gaps"))
```

Comparative words are quantitative claims wearing plain clothes. **flat, unchanged, steady, stagnant, doubled, tripled, halved, no different, as many as** - each one asserts a number and each one needs the number checked before it goes in the label. "Flat for the 45 years before" is a testable statement; if the pre-period slope is 1.5 points per decade at p = 0.0002, the label is false and the chart is worse than unannotated, because it invents a plateau the reader will believe.

Keep each label concise, single-purpose, and audience-appropriate. Tie numbers to their relevant baseline and window; qualify causal or inferential language; do not impose a universal word count or editorial vocabulary.

## Step 7: placement

- Anchor data-linked labels to the underlying data or chart geometry so they remain correct under filtering, sorting, and rescaling. Literal coordinates are valid when the annotation is intentionally independent of a data observation, such as chart furniture or a fixed reference caption.

Build a small annotation frame filtered from the plotting data, compute the offset from the value being labelled, and let the plotting layer position it:

```r
ann <- d %>%
  filter(state %in% c("Haryana", "Andhra Pradesh", "Tamil Nadu")) %>%
  mutate(tier  = if_else(state == "Haryana", "primary", "supporting"),
         x     = pc_2026 + 40,                      # offset from the point itself
         label = paste0("+Rs ", round(delta_pc)))

geom_text(data = filter(ann, tier == "supporting"),
          aes(x = x, y = state_f, label = label), hjust = 0, ...)
```

The label text is computed from the same columns as the mark, so the number and its position cannot disagree. `annotate()` with literal coordinates is fine for chart furniture - a period label, a band caption - but not for anything pointing at a specific observation.

**Derive the anchor, then offset into whitespace.** A derived coordinate is the right anchor and usually the wrong resting place. Labelling a group of points at its centroid puts the text in the densest part of the cloud, where it is least readable - the centroid is the worst position available. Anchor on the group, then push the label to the outside edge of the cloud, into space no point occupies.

Use the least distracting treatment that preserves label-to-mark association and legibility. Choose bare text, a halo, box, fill, or connector based on background, density, contrast, and medium.

- Preserve direct links between labels and the marks or groups they describe. Use a connector only when proximity and layout do not make the relationship clear.
- A connector must never cross other data.
- Text must never sit on top of data, gridlines, or another label.
- If no honest placement exists, change the chart - widen margins, expand the axis range, move the panel - before dropping the annotation.
- **Reserve room for the text when setting scale limits, on every edge the text can reach.** Labels clip left, right, top and bottom, and a centred label on a point near an axis extreme clips on whichever side it overhangs. Extend the limits in the direction the text runs and set clipping off; do not discover the clip after rendering.

## Visual weight

Two tiers:

- **Primary**: accent colour, bold, slightly larger. The data element it points at also takes the accent.
- **Supporting**: grey, regular weight, smaller than the axis labels. Context only.

Never let annotation text outweigh the data mark it explains. Grey carries context; the single accent carries the story.

## Step 8: render and inspect - mandatory

Placement cannot be verified from code. Export the image and look at it.

Check:

- Is any text clipped at a panel edge, or running past the figure boundary?
- **Does each label sit on the row or point it describes?** Check one label against the underlying number by hand. A label one row off looks perfectly fine.
- Does any label overlap data, another label, or an axis?
- Is the primary annotation visibly the loudest thing after the data itself?
- At final output size, is the smallest annotation still legible?
- Does the eye land on the primary annotation before the supporting ones?

Fix and re-render. Do not declare done from code inspection.

## Common mistakes

| Mistake | Fix |
|---|---|
| Annotation repeats the title verbatim | Cut to the locating fragment |
| Aggregate annotated when a burst explains it | Run the concentration check |
| Five things marked because five are interesting | Cap at 1 + 2; split the chart |
| Floating number with no baseline | Attach the comparator in the same label |
| Causal claim from a coincidence | Use "followed", or drop the annotation |
| Boxed callout with a fill | Bare text in whitespace |
| Annotation louder than the data | Move accent to the data mark |
| Label attached to the neighbouring row | Derive coordinates from the data, not by hand |
| Largest wiggle in a noisy series promoted to a finding | Ask whether it survives a different sample; if it fails, mark nothing |
| Callout announcing that nothing is happening | Put the absence in the title; leave the chart unmarked |
| Callout restates a value or rank the label/geometry already shows | Drop it; annotate only what the marks do not give |
| Aggregate/difference annotated because "it's a computation" | Recover-by-eye arithmetic on visible labels is a restatement; only quantities the reader can't get by eye survive |
| Computed callout added to fill space when title + labels already carry the claim | The honest count is zero; leave it unmarked |
| Bare year on a knee found by scanning | Word it as approximate, or validate first |
| Fitted line louder than the observations | Chart argues for the model; requiet the fit |
| Share language on a rank finding | Compute the share before writing the claim |
| Text clipped at any panel edge | Reserve axis headroom in the direction the text runs |
| Hand-typed count in the label text | Build the label string from the same computation as the mark |
| "Flat", "doubled", "unchanged" asserted but never tested | Comparative words are numbers; check them |
| Split point chosen by eye, then described as found | Test it, or word it loosely; describe both segments honestly |
| Group label parked at the cluster centroid | Anchor on the group, offset to the outside edge |
| Title claims one thing, annotation marks another | Pick one claim; the other is a second chart |
| Declared done without rendering | Export and inspect |

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and the surrounding chart style. Use `dataviz-critique` when reviewing someone else's annotated chart. Use `dataviz-fix` when the whole chart enters a repair loop. In the construct pipeline (`dataviz-construct`), the headline claim and the candidate marks are decided upstream at the insight stage (`karthik-evidence-builder`); this skill is loaded at build to rank, word, and place them.
