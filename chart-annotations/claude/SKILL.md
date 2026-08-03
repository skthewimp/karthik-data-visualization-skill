---
name: chart-annotations
description: Choose what to mark on a chart, rank competing candidates, word the label tightly, and place it without clutter.
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
7. Place by proximity; add a connector only if proximity fails.
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

If the chart has none of these, the chart probably has no story and the fix is a different chart, not a label.

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

## Step 5: how many

**One primary, at most two supporting.** More than three candidates survive the ranking? Split the chart.

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

Default is bare text sitting in whitespace beside the thing it labels. No box, no fill, no callout bubble.

- Connector only when the nearest free space is far enough that the pairing is ambiguous. Then a hairline grey segment, no arrowhead.
- Arrowhead only when the target is one point among several similar points.
- A connector must never cross other data.
- Text must never sit on top of data, gridlines, or another label.
- If no honest placement exists, change the chart - widen margins, expand the axis range, move the panel - before dropping the annotation.

## Visual weight

Two tiers:

- **Primary**: accent colour, bold, slightly larger. The data element it points at also takes the accent.
- **Supporting**: grey, regular weight, smaller than the axis labels. Context only.

Never let annotation text outweigh the data mark it explains. Grey carries context; the single accent carries the story.

## Step 8: render and inspect - mandatory

Placement cannot be verified from code. Export the image and look at it.

Check:

- Is any text clipped at a panel edge?
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
| Declared done without rendering | Export and inspect |

## Relationship to other skills

Use `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and the surrounding chart style. Use `dataviz-critique` when reviewing someone else's annotated chart. Use `chart-improver` when the whole chart is being rebuilt. `dataviz-orchestrator` calls this skill at the charting step.
