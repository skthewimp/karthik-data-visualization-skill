---
name: dataviz-selector
description: Choose charts for data stories, including S-curves, knee-bends, inflections, local peaks, and misleading/decorative forms.
---

# Dataviz Selector

Use this before making a chart when the user has a dataset and a question/hypothesis/story to answer.

Core job: pick the visual form that makes the intended claim easiest to see and hardest to misread.

For non-trivial chart selection, use the workflow and guardrails below; private local references may add nuance, but this public skill is self-contained.

## Workflow

1. State the one-sentence claim the chart must support. If there are multiple claims, split into multiple charts.
2. Identify the comparison: time, peers, baseline, target, counterfactual, distribution, spatial context, model expectation, or decomposition.
3. Identify the data grain: time series, category, entity, location, event/ball, survey response, model output, simulation, transaction, or scorecard metric.
4. For time-series charts, inspect shape before choosing annotations: mark visible knee-bends/inflection years, local maxima/minima, and temporary peaks/troughs when they change the story.
5. Choose the simplest chart that exposes that comparison.
6. Add only necessary context: direct labels, event line/band, threshold, uncertainty ribbon, counterfactual, facet, or annotation. For lines, include sparse labels for knee-bends and temporary extrema when visually salient and analytically meaningful.
7. Say what to avoid: misleading axis, overplotting, unnecessary regression, crowded legend, map-for-ranking, stacked bars for precise comparisons, etc.
8. If generating code, then also apply `karthik-data-visualization` styling before final output.

## Fast chooser

- Trend/intervention: line + points; vertical marker; optional pre-period trend/counterfactual. Mark knee-bend years where slope visibly changes.
- S-curve/adoption/diffusion pattern: line with muted raw points/annual values, emphasized smoothed line, labels for takeoff knee, acceleration/deceleration knees, plateau/peak, and any temporary local maximum/minimum. Avoid smooth-only lines that hide turns.
- Slowing growth: raw line + marked slowdown/knee + dotted earlier-growth projection; avoid YoY as main chart unless technical audience.
- Forecast/anomaly: actual line, forecast/dashed line, uncertainty ribbon, highlighted anomaly/intervention window.
- Many comparable series: small multiples or cluster prototypes; avoid spaghetti.
- If the chart will be consumed in chat or at thumbnail size, prefer forms that support direct labels and strong contrast; avoid designs that depend on faint colour differences or tiny legends.
- Choose colour by data role: focal-plus-grey for emphasis, qualitative hues for nominal identity, a perceptually ordered sequential scale for magnitude, and a diverging scale only around a meaningful midpoint. If colour is doing work that position or direct labels could do better, remove it.
- For slopegraphs, place endpoint labels where they remain paired and legible, then choose the aspect ratio from row density, label geometry, and delivery medium rather than a fixed orientation.
- For exactly two time points, prefer a slopegraph over a dumbbell if the comparison can be labeled on both ends and the connector line can carry the change; choose a dumbbell only when the paired endpoint values need to be read as discrete markers.
- Ranking: sorted horizontal bars; bar axis starts at 0; highlight an item only when the question, evidence, or stated story makes it focal. Otherwise keep equal-status items neutral.
- Composition/share substitution: use 100% stacked bars or areas only when broad mix is the story. Only segments that begin or end on an aligned baseline support precise visual comparison; a fixed-total stack aligns both outer edges, while internal segments still float. If the claim depends on component patterns across periods or groups, use small multiples, grouped bars, dot plots, lines, or a compact table instead.
- Distribution/skew/tails: histogram, density, ECDF, box, or violin; log scale for income/wealth/power-law data.
- Relationship: scatter with direct labels; regression only when relationship is the claim and uncertainty is shown.
- Normalized insight from canonical totals: when the source data's canonical measure is a total and the analysis adds a denominator (population, users, accounts, GDP, area), prefer a scatter of denominator vs total with diagonal iso-lines for the normalized metric. This preserves the original magnitude while showing per-capita/per-unit outliers. Use a ranked bar only when the normalized metric is itself the canonical measure or when ranking alone is the story.
- Elections: vote-seat scatter, swing-to-seats curves, margin/vote distributions, or selected maps depending on mechanism.
- Sports mechanism: win-probability/advantage trajectory, phase curves, impact-in-context; avoid scorecard-only visuals.
- Geography: map only when spatial pattern/shape matters; otherwise sorted bars/table.
- Survey ordinal shape: faceted rating histograms for polarisation; diverging stacked bars for broad Likert composition.
- Scenario/simulation: input-output scatter with threshold quadrants, density by alpha, fan/ribbon, or clustered representative paths.
- Decomposition/root cause: waterfall/bridge, ranked contribution bars, or compact root-cause table.
- Management scan: scorecard table first, diagnostic chart second, action implication explicit.
- Model explanation: observable category-rate/scenario-effect charts before coefficient tables.
- Risk/portfolio: distributions/scenarios/downside tails/utility curves; avoid mean-volatility alone.

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
- Never select pie charts, donut charts, 3D charts, animated/moving charts, interactive charts, gauges, radar/spider charts, or decorative infographic forms as the recommendation. If the user asks for one of these, say it is not recommended and offer the closest static alternative. Only mention the requested bad form as something to avoid.
- Never recommend dashboards as a substitute for an interpreted story.
- Bars start at zero; scatters need not.
- Do not extend regression/counterfactual lines beyond defensible range without marking them as projections.
- Label derived meaning directly when the evidence is a gap, quadrant, cluster, area between curves, knee-bend/inflection, or local maximum/minimum.
- Prefer direct labels to legends.
- Choose a form in which labels and marks pair without guesswork at delivery size. If the natural baseline pushes labels far from the marks they identify, use a compact row structure, restrained guides, a table-chart hybrid, faceting, or another form that restores immediate traceability.
- Size the canvas from the information and delivery medium. Whitespace should group, separate, or emphasize; do not retain blank regions merely because the plotting library or source aspect ratio created them.
- If part-to-whole is requested, prefer sorted bars, 100% stacked bars, tables, or small multiples over pies/donuts. Use stacking only when the reader needs broad composition, not precise component pattern comparison. Direct labels can support lookup of exact values; if comparison remains difficult or labels become crowded, change the form.
- Use maps only for spatial stories.
- If a clever chart needs too much explanation, use a simple chart plus annotation.
- For line charts with obvious slope changes or temporary extrema, do not leave the viewer to infer them. Mark the specific year/period on the chart, but keep markers sparse and defensible.
- Managers do not want dashboards; they want interpreted stories and actions.
