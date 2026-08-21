# Dataviz Selector Skill

`dataviz-selector` helps choose the right chart for a dataset plus analytical question, hypothesis, or story.

It is designed for situations where the failure mode is not bad styling, but bad chart choice. For example:

- choosing a map when a sorted bar chart is clearer
- using YoY growth when a raw time series plus counterfactual is easier to understand
- leaving S-curve knee-bends, inflection years, or temporary local peaks unmarked
- using a regression line when labelled points tell the story better
- using a dashboard when management needs a decision and an action
- using a pie chart because the data is technically "part-to-whole"

## Cold selection inside a repair

When `dataviz-selector` is invoked inside a chart repair (`dataviz-fix`), it runs on the extracted intent (`dataviz-brief`) and data, **cold**: the source chart's form is not an input and gets no vote. There is no "the source form is clearly correct, so keep it" shortcut. A many-series stacked bar whose message is per-series comparison is not correct enough to inherit - it becomes small multiples, direct-labelled lines, or a ranked view. Preserving the categories means keeping the data, not the chart type.

## Trigger examples

Use it for prompts like:

```text
I have monthly sales by channel and want to show which channel is becoming less efficient.
```

```text
Here is constituency-level vote share and seats. How should I show vote efficiency?
```

```text
We have actual vs budget vs prior year by division. What visual should go into the management deck?
```

```text
The user wants a pie chart of market share. What should we use instead?
```

## Recommendation format

The skill asks the assistant to answer in this structure:

```markdown
Recommended visual: <chart form>
Why: <claim-comparison fit>
Encoding: X = ..., Y = ..., colour/facet/label = ...
Context layers: <thresholds/events/counterfactuals/annotations>
Avoid: <bad alternatives or pitfalls>
If implementing: <short code/design note>
```

## Core decision rules

- One chart, one main job.
- Start from the claim, not the chart taxonomy.
- Identify the comparison: time, peers, baseline, threshold, counterfactual, distribution, spatial context, model expectation, or decomposition.
- Use the simplest chart that exposes that comparison.
- Add context only when it helps: event markers, thresholds, ribbons, counterfactuals, direct labels, facets, or short annotations.
- Choose colour by analytical role: focal-plus-grey for emphasis, qualitative hues for identity, sequential scales for magnitude, and diverging scales only around a meaningful midpoint.
- Match the visual channel to the job the data does: give the reader's main comparison the most accurate channel. Position on a common scale and length read magnitude and trends best; hue carries identity; area, angle, and colour intensity are for rough proportion, emphasis, or spotting regions - not for values a reader must compare. When the main quantity sits on a weak channel, move it to a stronger one.
- For S-curves and other shaped time series, mark visible knee-bends/inflections, local maxima/minima, and temporary peaks/troughs when they change the story.
- If the dataset does not support the user's question, say so and chart the evidence that exists.

## Hard bans

The skill should not recommend:

- pie charts
- donut charts
- 3D charts
- animated or moving charts
- interactive charts as the main answer
- gauges or speedometers
- radar/spider charts
- decorative infographic forms

If the user asks for one of these, the skill should say it is not recommended and offer the closest static alternative.

## Common mappings

| Problem | Recommended visual |
|---|---|
| Trend or intervention | Line + event marker, optionally counterfactual |
| S-curve/adoption/diffusion | Line with muted raw values, emphasized smoothed trend, and sparse labels for takeoff knee, acceleration/deceleration knees, plateau/peak, and temporary local extrema |
| Slowing growth | Raw line + marked slowdown/knee + dotted earlier-growth projection |
| Forecast miss | Actual vs forecast + ribbon/gap annotation |
| Ranking | Sorted horizontal bars, axis from zero |
| Distribution/skew | Histogram, density, ECDF, boxplot, or violin |
| Vote efficiency | Vote-share vs seat-share scatter |
| Swing scenarios | Seat curves by swing, faceted by state |
| Survey polarisation | Faceted response histograms |
| Share substitution | 100% stacked bars/area only if broad mix is the story; use small multiples, grouped bars, lines, dots, or a table when intermediate or top components need precise comparison |
| Many series × time, compare trajectories | Small multiples or direct-labelled lines (reduce to top-N + explicit "other" if crowded). Put the trajectory on position, not on colour. |
| Risk | Downside distributions, scenarios, utility curves |
| Root cause | Waterfall if reconciled; otherwise ranked driver bars or action table |
| Management scan | Scorecard first, diagnostic chart second |
| Geography | Map only when spatial pattern or shape matters |

## Public red-team suite

Keep adversarial eval prompts local-only; do not commit `references/` or `scripts/` to the public repo.
