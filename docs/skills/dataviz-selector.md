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

When `dataviz-selector` is invoked inside a chart repair (`dataviz-fix`), it runs on the extracted intent (`dataviz-brief`) and data, **cold**: the source chart's form is not an input and gets no vote. There is no "the source form is clearly correct, so keep it" shortcut. A many-series stacked bar whose message is per-series comparison is not correct enough to inherit - it becomes small multiples, direct-labelled lines, or a ranked view. Preserving the categories means keeping the data, not the chart type. Source features - how many categories sit in one view, that the source stacked or faceted, its grain, its series set - are properties of the old picture, not requirements. A form earns its place only by an **affirmative** test: for each message, name the comparison it needs and the visible element a reader traces it on at delivery size. "It keeps all the categories" and "it beats a table" are not justifications - the first confuses keeping the data with keeping a form, the second is a strawman.

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
The user explicitly requests a pie chart of market share. Honour that form and keep its encoding honest.
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

- One chart, one main job - justified by the reading it enables, not by fidelity to the source or beating a worse alternative.
- Start from the claim, not the chart taxonomy.
- Identify the comparison: time, peers, baseline, threshold, counterfactual, distribution, spatial context, model expectation, or decomposition.
- Use the simplest chart that exposes that comparison.
- Add context only when it helps: event markers, thresholds, ribbons, counterfactuals, direct labels, facets, or short annotations.
- Choose colour by analytical role: focal-plus-grey for emphasis, qualitative hues for identity, sequential scales for magnitude, and diverging scales only around a meaningful midpoint.
- Match the visual channel to the job the data does: give the reader's main comparison the most accurate channel. Position on a common scale and length read magnitude and trends best; hue carries identity; colour intensity may support emphasis or spotting regions; use length or position for quantities a reader must compare. When the main quantity sits on a weak channel, move it to a stronger one.
- Keep the graphic proportional to the data (graphical integrity / lie factor): the visual effect should be as big as the effect in the data, no bigger. A length encoding (bar, column, filled area/arc) is read as a ratio of lengths, so its baseline is the quantity's zero by construction - not an editorial choice, and calling a non-zero baseline "meaningful"/"natural"/"contextual" is the tell it is being truncated, not a defense. Position marks (dots, slope/dumbbell endpoints) carry no length and may zoom their scale - so small variation on a large common level goes to a dot/dumbbell/slope, never a bar above zero. No area or volume for a one-dimensional quantity, no dimension the data lacks (3D, perspective). The selector already leans Tufte elsewhere - comparison-first ("compared to what?"), the simplest form that exposes it, small multiples, showing the observations over a bare summary.
- Log vs linear is a computed, advisory decision. For a continuous position axis (points, lines, dots, box/violin - not bars/area, which need a true zero), `recommend_scale_transform` reports the positive dynamic range and skew and grades whether log earns its place; the model takes it as one input and can override for the prompt, the audience, or clarity, recording the chosen scale (and any override reason) in the plan. Log10 needs strictly positive values; symlog/log1p are noted but not auto-recommended.
- Shared value scales require commensurable quantities. Different-unit charts may align on time when each has its own title and labelled value scale; use a table for lookup across measures.
- For S-curves and other shaped time series, mark visible knee-bends/inflections, local maxima/minima, and temporary peaks/troughs when they change the story.
- If the dataset does not support the user's question, say so and chart the evidence that exists.

## Form constraints

- **Prompt precedence.** Honour a chart form explicitly requested in the prompt; it overrides these default form exclusions. A form merely present in a source image is not a request. Preserve honest quantities, scales, and claims in the requested form. A source-UI overlay in the image - a tooltip, hover card, crosshair readout - is chrome, not a chart element: never reproduce the floating box, and carry its value only if that mark carries the point (then as a direct label on its datum), else drop it - an incidental hover readout adds nothing.
- **Default exclusions.** Do not choose pies, donuts, radar/spider charts, gauges/speedometers, decorative infographic forms, 3D charts, or animation/interaction as the main answer unless explicitly requested.
- **Points and comparisons.** Scatter requires two quantitative axes. For categorical magnitudes, use bars rather than isolated dots or lollipops. Dumbbells are valid for paired comparisons; point-and-interval plots are valid for estimates with uncertainty.
- **Magnitude channel.** Use length or position for precise quantity comparisons, not area or volume. Heatmaps are valid when colour reveals patterns or clusters across a matrix. Default to equal-size scatter points; do not add a bubble-size measure or choose a treemap. An explicit form request overrides this preference.
- **Connections and accumulation.** Lines require a meaningful sequence or relationship between connected observations. Waterfall steps must reconcile a meaningful starting and ending quantity; unrelated changes do not form a waterfall.
- **Reading task and space.** Choose an encoding that makes the intended comparison readable at delivery size. Grouped bars still fail if group identities or values cannot be followed. Related claims may share a chart; separate views only when the reading requires them. Arrange panels in a grid or strip according to the comparison and available space.

## Common mappings

| Problem | Recommended visual |
|---|---|
| Trend or intervention | Line + event marker, optionally counterfactual |
| S-curve/adoption/diffusion | Line with muted raw values, emphasized smoothed trend, and sparse labels for takeoff knee, acceleration/deceleration knees, plateau/peak, and temporary local extrema |
| Slowing growth | Raw line + marked slowdown/knee + dotted earlier-growth projection |
| Forecast miss | Actual vs forecast + ribbon/gap annotation |
| Ranking | Sorted bars, largest first, axis from zero (nominal categories only); orientation is reasoned from label width - short labels stay vertical, labels too wide for their slot go horizontal (rows) |
| Ordered/time category | Keep the sequence order and its natural direction (left-to-right, or top-to-bottom if vertical); never sort by magnitude or invert onto the y-axis so time climbs upward |
| Single value per category, magnitude | Bars; grouped bars, suitable facets, or a table for multiple values |
| Distribution/skew | Histogram, density, ECDF, boxplot, or violin |
| Vote efficiency | Vote-share vs seat-share scatter |
| Swing scenarios | Seat curves by swing, faceted by state |
| Survey polarisation | Faceted response histograms |
| Share substitution | 100% stacked bars/area only if broad mix is the story; use small multiples, grouped bars, lines, or a table when intermediate or top components need precise comparison. Compositional data (parts summing to 100%) is not a compositional claim - a claim about how components move over time is a set of trajectories and goes to lines/small multiples regardless of the fixed total |
| Many series × time, compare trajectories | Small multiples or direct-labelled lines (reduce to top-N + explicit "other" if crowded). Put the trajectory on position, not on colour. |
| Risk | Downside distributions, scenarios, utility curves |
| Root cause | Waterfall if reconciled; otherwise ranked driver bars or action table |
| Management scan | Scorecard first, diagnostic chart second |
| Geography | Map only when spatial pattern or shape matters |

## Table or chart

A table is a first-class verdict, not a fallback. When the reader's task is exact lookup, the rows are few, the values are not commensurable on one scale, or the artifact is a reference or monitoring surface, the selector can choose a well-formatted table and hand off to `karthik-table-style`. A chart wins when the message is a shape, trend, or comparison the eye should grab pre-attentively. Inside a repair, a table is a legitimate cold verdict.

## Public red-team suite

Keep adversarial eval prompts local-only; do not commit `references/` or `scripts/` to the public repo.
