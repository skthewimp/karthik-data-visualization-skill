---
name: dataviz-selector
description: Choose charts for data stories, including S-curves, knee-bends, inflections, local peaks, and misleading/decorative forms.
---

# Dataviz Selector

Use this before making a chart when the user has a dataset and a question/hypothesis/story to answer.

Core job: pick the visual form that makes the intended claim easiest to see and hardest to misread.

For non-trivial chart selection, use the workflow and guardrails below; private local references may add nuance, but this public skill is self-contained.

## Cold selection in a repair

When this skill is invoked inside a chart repair (`dataviz-fix`), it runs on the intent (from `dataviz-brief`) and the extracted data - not on the source chart. Run it **cold**: the source chart's form is not an input and gets **no vote**. Choose the form the messages and data want, as if drawing the chart for the first time. There is no "the source form is clearly correct, so keep it" shortcut: a many-series stacked bar or area whose message is per-series comparison or trajectory is not correct enough to inherit - it becomes small multiples, direct-labelled lines, or a ranked/indexed view. Preserving the categories means keeping the data, not the chart type; a tidier version of the same illegible form is not a selection. A table is a legitimate cold verdict: if the intent and data want exact lookup or non-commensurable values, choosing a well-formatted table over the source chart is a selection, not a refusal to chart.

## Workflow

0. **Disambiguate semantics before choosing a chart:** identify the measure, denominator, displayed universe, relevant time/context boundaries, claim strength, and audience meaning of the units. Choose a form and semantic cues that make the intended comparison hard to misread; do not prescribe a chart type, vocabulary, or annotation when another defensible design communicates the distinction equally well.

1. State the one-sentence claim the chart must support. If there are multiple claims, split into multiple charts.
2. Identify the comparison: time, peers, baseline, target, counterfactual, distribution, spatial context, model expectation, or decomposition.
3. Identify the data grain: time series, category, entity, location, event/ball, survey response, model output, simulation, transaction, or scorecard metric.
4. Inspect the data's structure for features relevant to the stated claim. Treat apparent breaks, extremes, clusters, or changes as candidates only when they are robust enough, materially informative, and useful at the intended viewing scale; detailed candidate selection belongs to `chart-annotations`.
5. Choose the simplest chart that exposes that comparison.
- Add only necessary context: direct labels, event line/band, threshold, uncertainty ribbon, counterfactual, facet, or annotation. Detailed annotation selection belongs to `chart-annotations`.
7. Say what to avoid: misleading axis, overplotting, unnecessary regression, crowded legend, map-for-ranking, stacked bars for precise comparisons, etc.
8. If generating code, then also apply `karthik-data-visualization` styling before final output. If the verdict is a table, apply `karthik-table-style` instead.

## Table or chart?

A well-formatted table is a visualization, not the absence of one; treat it as a real candidate every time, not a fallback. Ask what the reader's main task is:

- **Table** when the task is reading exact values; when the rows are few and the reader looks numbers up by name; when the columns are not commensurable on one scale (mixed units or unrelated metrics) so no shared axis is honest; when the artifact is a reference or monitoring surface consulted cell by cell; or when the "chart" would just be a bar-chart of a handful of numbers read precisely. A table with decimal-aligned figures, sized columns, and scarce emphasis often out-reads that bar chart.
- **Chart** when the message is a shape, trend, comparison, or distribution the eye should grab pre-attentively - when position, length, or slope carries the claim faster than the reader could scan a grid of numbers.

When both could work, decide by the dominant task: precise lookup and heterogeneous values lean table; one pre-attentive comparison leans chart. A table is chosen for exact lookup or non-commensurable values, never as a dumping ground for data a chart could show as a shape. When the verdict is a table, hand off to `karthik-table-style` for its craft.

## Fast chooser

- Trend/intervention: choose a form that exposes level, change, comparison, and uncertainty; add a supported event or baseline context when it changes interpretation.
- Nonlinear or changing trajectories: show the observations and use a derived summary only when its assumptions and uncertainty remain visible.
- Slowing growth: show the level and the comparison that establishes slowing; use a derivative or projection only when it answers the stated question and is interpretable to the audience.
- Forecast/anomaly: actual line, forecast/dashed line, uncertainty ribbon, highlighted anomaly/intervention window.
- Many comparable series: small multiples or cluster prototypes; avoid spaghetti.
- If the chart will be consumed in chat or at thumbnail size, prefer forms that support direct labels and strong contrast; avoid designs that depend on faint colour differences or tiny legends.
- Choose colour by data role: focal-plus-grey for emphasis, qualitative hues for nominal identity, a perceptually ordered sequential scale for magnitude, and a diverging scale only around a meaningful midpoint. If colour is doing work that position or direct labels could do better, remove it.
- For slopegraphs, place endpoint labels where they remain paired and legible, then choose the aspect ratio from row density, label geometry, and delivery medium rather than a fixed orientation.
- For two-point comparisons, choose among slopegraphs, dumbbells, paired bars, dot plots, or tables according to whether the main task is seeing change, comparing endpoint values, or reading exact values. The number of time points alone does not determine the form.
- Ranking: sorted horizontal bars; bar axis starts at 0; highlight an item only when the question, evidence, or stated story makes it focal. Otherwise keep equal-status items neutral.
- Composition/share substitution: use 100% stacked bars or areas only when broad mix is the story. Only segments that begin or end on an aligned baseline support precise visual comparison; a fixed-total stack aligns both outer edges, while internal segments still float. If the claim depends on component patterns across periods or groups, use small multiples, grouped bars, dot plots, lines, or a compact table instead.
- Distribution/skew/tails: histogram, density, ECDF, box, or violin; log scale for income/wealth/power-law data.
- Relationship: scatter with direct labels; regression only when relationship is the claim and uncertainty is shown.
- Normalization: preserve the relationship between numerator and denominator, then choose a form based on whether the task is ranking, scale diagnosis, temporal/spatial variation, or distribution.
- Domain-specific questions: derive the form from the mechanism, comparison, uncertainty, and audience rather than applying a domain recipe.

## Output format for recommendations

Use this concise structure:

```markdown
Recommended visual: <chart form>
Why: <claim-comparison fit>
Encoding: X = ..., Y = ..., colour/facet/label = ...
Context layers: <thresholds/events/counterfactuals/knee-bends/local extrema/annotations>
Avoid: <bad alternatives or pitfalls>
If implementing: <short code/design note>
```

## Hard guardrails

- One chart, one main job.
- A form must let every message the brief carries be read off it; a form that serves one message can silently hide another. An aggregate and its decomposition are the common pair - the total and the mix, the whole and the parts - and one form rarely carries both: a breakdown (small multiples, decomposed lines, grouped bars) shows the parts but not the sum, and a single total line shows the sum but not the parts. When the brief needs both, that is two jobs; pair a totals view with the breakdown rather than committing to one and dropping the other. Before finalizing, check each brief message against a visible element and treat any message with no element as a dropped message, not a detail.
- Match the visual channel to the job the data does, and give the reader's most important comparison the most accurate channel. Roughly, from most to least accurate for reading values: position on a common scale, then length, then angle/slope, then area, then colour and density. Apply it to what the chart is actually asking the reader to do:
  - Magnitude or quantity to compare: position on a common scale or length (dots, bars, lines) - not area (bubble), angle (pie), or colour intensity.
  - Change or trajectory over time: position (lines, slopes) - not colour shifts across cells.
  - Rank or order: position, or an ordered sequential scale.
  - Category or identity: hue - a qualitative palette, not lightness (which implies order that is not there).
  - Relationship between two measures: x-y position (scatter).
  - Part-to-whole: length from an aligned baseline.

  When the chart's main quantity sits on a weak channel - a value the reader must read off colour, a trend read off shading, a size compared by area - move it to a stronger one. Reserve the weak channels for what they are good at: colour and density for emphasis, grouping, or spotting hot/cold regions across many cells; area and angle for rough proportion, not precise reading.
Treat commonly problematic forms as risk conditions, not universal prohibitions. Recommend the simplest form that preserves the intended comparison in the actual medium. A form that is often misleading may still be appropriate when its purpose, encoding, audience, and limitations are explicit; reject it when it obscures magnitude, comparison, uncertainty, or interpretation.
- Bars start at zero; scatters need not.
- Keep the graphic proportional to the data (graphical integrity). The size of the visual effect should match the size of the effect in the data: anything encoding a value by length or position needs a common, untruncated baseline; a one-dimensional quantity should not be encoded by area or volume, which the eye reads as exaggerated; and do not add a dimension the data does not have (3D, perspective, decorative depth). Bars-start-at-zero is one instance. If a form can only make the story look larger than it is, choose another.
- Do not extend regression/counterfactual lines beyond defensible range without marking them as projections.
- Label derived meaning directly when the evidence is a gap, quadrant, cluster, area between curves, knee-bend/inflection, or local maximum/minimum.
- Prefer direct labels to legends.
- Let perception group and link, not just colour. The reader groups by proximity and similarity, and links by connection, before consulting a legend: prefer directly labelled and connected forms (lines, slopes) to a colour the eye must match; use separate panels, spacing, or a light enclosure to separate or mark groups; and keep one focal element as figure against muted ground. Do not hand unrelated series a similar encoding, and do not make several channels compete to be seen first.
- Choose a form in which labels and marks pair without guesswork at delivery size. If the natural baseline pushes labels far from the marks they identify, use a compact row structure, restrained guides, a table-chart hybrid, faceting, or another form that restores immediate traceability.
- Size the canvas from the information and delivery medium. Whitespace should group, separate, or emphasize; do not retain blank regions merely because the plotting library or source aspect ratio created them.
- If part-to-whole is requested, prefer sorted bars, 100% stacked bars, tables, or small multiples over pies/donuts. Use stacking only when the reader needs broad composition, not precise component pattern comparison. Direct labels can support lookup of exact values; if comparison remains difficult or labels become crowded, change the form.
- Use maps only for spatial stories.
- If a clever chart needs too much explanation, use a simple chart plus annotation.
- Add a label or annotation only when it materially improves the intended reading; detailed candidate selection and wording belong to `chart-annotations`.
- Choose between a chart, table, dashboard, or interactive view according to whether the task is monitoring, exploration, comparison, or narrative explanation.
