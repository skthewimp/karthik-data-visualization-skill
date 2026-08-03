# Chart Annotations Skill

`chart-annotations` decides what a chart should mark, and what the mark should say.

It exists because "add annotations" is not one decision but four, and each has its own failure mode:

- **What to mark** - the reader cannot see the point, but the chart has six interesting features
- **Which one wins** - a record cluster and a slow trend both look interesting; only one can lead
- **How to word it** - the label is a full sentence, or repeats the title, or quotes a number with nothing to compare it to
- **Where to put it** - the text sits on the data, or needs an arrow crossing three other series

## Trigger examples

Use it for prompts like:

```text
This line chart is fine but nobody can tell what the point is. What should I call out?
```

```text
Which year should I mark on this adoption curve?
```

```text
The annotation says "an exceptionally wet November driven by sustained rainfall" - is that right?
```

```text
I have four things worth marking on this chart. Which do I keep?
```

## The core moves

**Title states, annotation locates.** The title carries the claim in words. The annotation is a short fragment placed at the evidence. The same sentence never appears twice.

**Concentration check.** Before annotating any aggregate, test whether a small subset explains most of it. A record month driven by two days is not a sustained wet month, and calling it one is the most common annotation error. It is invisible from summary statistics and only shows up when you look at the distribution behind the total.

**Significance ladder.** Records and boundary breaches beat sustained departures, which beat events with visible effects, which beat persistence, which beats plain aggregates. Then two filters: keep one dominant frame, and never annotate a value the reader can read off the chart.

**One primary, at most two supporting.** More than three surviving candidates means the chart is doing more than one job. Split it.

**Wording constraints.** Under 18 words. One claim. Every number attached to its baseline and window in the same label. No causal verb without causal evidence. No report-speak - "just 1mm vs 58mm usual", not "a rainfall shortfall of 57mm against normal".

**Placement by proximity.** Bare text in whitespace next to the thing. A hairline connector only when the nearest free space is ambiguous. No boxes, no fills, no callout bubbles, no connector crossing data.

**Render and inspect.** Placement cannot be verified from code. Export the image, look for clipping and collisions, fix, re-render.

**Derive annotation coordinates from the data.** Hand-typed coordinates attach labels to the wrong observation, and a label one row off looks entirely correct while stating something false. Build an annotation frame filtered from the plotting data and compute positions as offsets from the value being labelled.

**Absence is annotatable.** A series with no trend is a real finding. Show the expected variation as a band and mark that everything stays inside it, rather than promoting the largest wiggle to a story it cannot support.

**Derived features carry a higher bar.** A knee from a breakpoint scan is the best of many candidates, not a tested one. Word it with the precision the method actually has, and never let a fitted line outshout the observations behind it.

## Where the rules come from

The significance ladder, the concentration check, and the wording constraints are generalised from a real annotation system: a daily weather report where an LLM writes the chart's headline commentary, and where a bank of reviewed historical examples was built specifically to teach the model which signal to lead with. The failure it kept making - reading an aggregate as a trend when a burst explained it - is the reason the concentration check is a separate step rather than a footnote.

The placement, absence, and derived-feature rules came from testing the first version of the skill on three real charts: a 140-year All-India rainfall series with no trend, a Bangalore maximum-temperature series with a scanned breakpoint, and a state liquor-revenue dumbbell. Each chart broke the skill in a different place, and each rule traces to a specific defect in a rendered image rather than to a principle.

## Relationship to other skills

Run `dataviz-selector` first if the chart form is still open. Use `karthik-data-visualization` for palette, typography, and surrounding style; this skill sets only the annotation's own weight relative to the data. Use `dataviz-critique` when reviewing an existing annotated chart. `dataviz-orchestrator` calls this skill at the charting step, between choosing the visual and running the critique pass.
