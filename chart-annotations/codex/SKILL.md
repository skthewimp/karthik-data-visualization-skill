---
name: chart-annotations
description: Decide what to mark on a chart, how to rank competing candidates, how to word the label, and where to place it. Use when a chart needs on-chart annotation, callouts, direct labels for a key point, event markers, threshold lines, knee-bend or inflection labels, outlier calls, highlighted bars or points, or when a chart is finished but the reader cannot see the point without narration. Also use when annotation text is too long, too many things are marked, the label repeats the title, or a marked number is not tied to a stated baseline.
metadata:
  short-description: Choose, rank, word, and place chart annotations
  claude-description: Choose what to annotate on a chart, rank competing candidates, word the label tightly, and place it without clutter.
---

# Chart Annotations

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

Exception: a chart designed to travel alone with no title bar or surrounding text may carry the claim in the annotation. State that this is the case before doing it.

## Workflow

1. Write the one-sentence claim the chart must support.
2. Enumerate annotation candidates from the chart's geometry.
3. Run the concentration check.
4. Rank candidates by significance.
5. Apply the cap: one primary, at most two supporting.
6. Write each label under the wording constraints.
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

## Step 3: the concentration check

**Before annotating any aggregate, test whether a small subset explains most of it.**

This is the most common annotation error and it is invisible from summary numbers.

```text
"Wettest November on record, 371mm"        <- aggregate frame
170mm of that fell on Nov 15-16.
"Record November, driven by one deluge"    <- correct frame
```

Rule: if fewer than ~20% of the observations carry more than ~50% of the effect, annotate the subset, not the aggregate. Do not call a window sustained, steady, or accumulating when a short burst explains it.

The mirror error also applies: if the effect really is spread evenly, say so directly. "Rained every day" beats "wet period".

**The check gates the title, not only the annotation.** Compute the share before writing either. If one state contributes 39% of a total increase, neither the annotation nor the title may say "drives almost all" - the honest frame is "the sharpest jump", which is a rank claim, not a share claim. Rank claims and share claims fail in different ways; know which one you are making.

## Step 4: significance ladder

When several candidates compete, rank in this order. It is a default, not a law - override it when the data says otherwise, and say why.

1. **Record or boundary breach** covering most of the window. Extremes beat trends.
2. **Large sustained departure from a stated baseline.** A big departure beats a modest one anywhere else on the chart.
3. **Event with a visible downstream effect.** Annotate the effect, not just the event date.
4. **Persistence** - a run with no exceptions. Say it plainly.
5. **Aggregate excess or shortfall** - use only when nothing sharper exists.

Two filters applied after ranking:

- **One dominant frame.** A second signal earns its place only if it strengthens the first. Two unrelated signals means two charts.
- **Skip the obvious value.** Annotate what the reader cannot compute by looking. The tallest bar being tallest is not an annotation.

## When nothing clears the bar

**No story, no annotation.** A noisy series with no trend, no breakpoint, and no outlier beyond ordinary variation gets no marks on it. This is a finding, not a failure to look hard enough, and the chart should be left clean.

Do not manufacture a lead by promoting the largest wiggle. The wettest year in a 140-year record with no trend is not a story; it is the top of the distribution, which some year had to be. Marking it tells the reader it means something.

Test before promoting any candidate: **would this feature still be there in a different sample?** A trend with p = 0.74, a run of six that a coin flip produces routinely, a single extreme inside one standard deviation - none survive that question, and none get annotated.

The absence itself belongs in the title, where claims live. There is nothing on the chart to locate, so there is nothing to annotate.

What still earns its place is **context that lets the reader verify the absence** - a variation band, a reference line, a decade average over noisy annual values. These are context layers, not annotations: they encode data or a stated baseline rather than pointing at a feature, and they are not subject to the annotation cap.

```text
Title:          India's annual rainfall has not shifted in 140 years
Context layers: +/- 1 SD band, mean line, decade averages
Annotations:    none
```

The difference matters. A band showing expected variation is evidence. A callout reading "every decade average falls inside the band" is the title said twice, taking up chart space to restate what the reader can already see.

## Annotating derived features

A knee, a slope, a smoothed peak, or a cluster boundary comes from a model. Three extra rules apply:

- **Validate before marking.** A breakpoint picked as the minimum of a scan is the best of many candidates, not a tested finding. Check it survives a sensitivity test, or word it as approximate.
- **Word it with the uncertainty the method carries.** "around the mid-1950s" is honest for a scanned breakpoint; "in 1956" claims a precision the method does not have. Do not put a bare year on a derived knee unless the year is itself the result.
- **Never let the fit outshout the data.** If a fitted line is the loudest element and the observations are faint grey behind it, the chart is arguing for the model rather than showing the evidence. Give the fit the accent only when the observations remain clearly readable.

## Step 5: how many

**One primary, at most two supporting.** More than three candidates survive the ranking? Split the chart.

Orienting labels are a separate class and do not count against the cap: series names, period labels, axis units, a legend replacement. They must still be collision-checked against the claim annotations - a period label sitting on top of the primary annotation is the same defect as two annotations overlapping.

## Step 6: writing the label

Constraints, all of them hard:

- **Under 18 words.** Most good annotations are under eight.
- **One simple claim.** No semicolons, no nested clauses, no "however" or "otherwise".
- **Every number tied to its baseline and window in the same label.** "1mm vs 58mm expected", never a floating "1mm".
- **No causal verb without causal evidence.** "followed", "coincided with" are safe; "caused", "drove", "led to" need the evidence.
- **No inferred category the data does not contain.** Do not name a season, a phase, or a regime the dataset never labelled.

Register - write like an observant person, not a report:

| Banned | Use instead |
|---|---|
| drought, severe, gripped, collapse, soared | dry, sharp, fell, rose |
| rainfall shortfall of, against normal, totalled just, the period saw | just 1mm vs 58mm usual |
| unprecedented, dramatic, remarkable | give the number and let it be remarkable |

Four label shapes that cover most cases:

```text
[event] on [date], then [effect]          Rain after Mar 10, then a 5C drop
[state] from [date] to [date]. [gap]      Dry Oct 13-25. 1mm vs 58mm usual
[extreme] for [window], [magnitude]       11 record days in a fortnight
[aggregate], mostly [subset]              Record November, mostly Nov 15-16
```

## Step 7: placement

**Derive every annotation coordinate from the row it labels. Never hand-type coordinates.**

This is the rule that prevents the worst annotation defect: a label attached to the wrong observation. Hand-placed coordinates drift as data, sort order, or scale limits change, and a label one row off is not a cosmetic problem - it states something false about a different entity, and it looks entirely correct.

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

Default is bare text sitting in whitespace beside the thing it labels. No box, no fill, no callout bubble.

- Connector only when the nearest free space is far enough that the pairing is ambiguous. Then a hairline grey segment, no arrowhead.
- Arrowhead only when the target is one point among several similar points.
- A connector must never cross other data.
- Text must never sit on top of data, gridlines, or another label.
- If no honest placement exists, change the chart - widen margins, expand the axis range, move the panel - before dropping the annotation.
- **Reserve room for the text when setting scale limits.** A right-hand label needs axis headroom past the last data point, not just a wider figure. Extend the limits and set clipping off; do not discover the clip after rendering.

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
| Bare year on a knee found by scanning | Word it as approximate, or validate first |
| Fitted line louder than the observations | Chart argues for the model; requiet the fit |
| Share language on a rank finding | Compute the share before writing the claim |
| Text clipped at the right edge | Reserve axis headroom before rendering |
| Declared done without rendering | Export and inspect |

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and the surrounding chart style. Use `dataviz-critique` when reviewing someone else's annotated chart. Use `chart-improver` when the whole chart is being rebuilt. `dataviz-orchestrator` calls this skill at the charting step.
