# Karthik Dataviz Selection Prior

This reference is distilled from Karthik's Mint charts/articles, `visualisations.substack.com`, local management/teaching decks, and calibration questions.

## Master principle

Start with the claim, not the chart type. A visualization should make one intended sentence visible. If there are two sentences, make two charts or one chart plus a clearly secondary annotation.

Ask:
1. What sentence must the chart prove or clarify?
2. Compared to what?
3. What data can be removed or muted so the sentence is clearer?
4. What would make the chart misleading?

## User-calibrated rules

### Slowing growth
When the story is “growth is slowing” but a derivative/YoY chart would confuse readers, use the raw time-series line. Mark the slowdown point and add a dotted counterfactual/projection showing where the series would have gone if earlier growth had continued.

### Vote efficiency
For multiple elections, use vote share on X and seat share on Y. One point per party-year. Use party colours. Label points with party abbreviation and year. Add party trendlines only with enough data.

### Ex-ante vs ex-post sports valuation
Use scatter when showing market rationality or high-price/high-performance clusters. Use slope graph when expected and actual are on the same scale. Watch price skew; transform or avoid price axis if it dominates.

### Diversity / heterogeneity by state
Use sorted horizontal bars. Diversity metric is preferably HHI-derived. Axis starts at zero. Highlight the surprising state even if not top-ranked.

### Promo vs stockout
Use actual sales as thick line and forecast as dotted line. Shade promo windows. Mark stockout days with distinct markers/highlights, especially overlaps with promo.

### Polarised survey response
Use faceted per-operator response distributions: one row per operator, five vertical bars for rating percentages. Highlight the bimodal/focal operator. Use averages only as secondary.

### Story shapes / trajectory clusters
Cluster trajectories first. Show facets for each cluster. Thin line per member, thick line for cluster average/prototype. Use descriptive facet titles, not cluster numbers.

### Income/wealth comparisons
PPP-adjust values. Use box/violin by country with log Y-axis. Log axis is acceptable because linear scale hides power-law differences; explain it.

## Chart family rules

### Time series
- Use line + point for one metric over time.
- Add event lines/bands for interventions.
- Add fitted/counterfactual only when answering “what changed?”
- For multiple related metrics, use small multiples unless only 2–3 lines matter.
- For current vs history, use thin grey historical lines and thick coloured current line.

### Forecast, anomaly, counterfactual
Use actual line + expected/forecast line + uncertainty ribbon where available. Highlight the period/event. If the story is the gap, label the gap or shortfall explicitly.

### Ranking
Use sorted horizontal bars. Start at zero. Label values when precision matters. Highlight the narratively important item, not necessarily only the max/min.

### Composition
Use 100% stacked bars or stacked area only when the story is share mix/substitution. Avoid stacked bars when precise cross-category comparison matters.

### Distributions
Use histograms, density, ECDF, boxplots, or violins when fighting intuition about averages, skew, tails, or thresholds. Add benchmark/median/policy threshold markers. Use log scales for power-law data when needed.

### Relationships
Use scatter with direct labels for important/outlier entities. Regression/smooth is optional and should not dominate unless relationship is the claim. Do not extrapolate regression beyond observed X range. Show uncertainty or model confidence if the line is persuasive evidence.

### Elections
- Vote-to-seat conversion: vote-share vs seat-share scatter.
- Swing sensitivity: seats vs swing curves, faceted by state, with majority/current-seat lines.
- Vote distribution/coordination: histograms/densities of constituency vote shares, margins, wasted votes.
- Gerrymandering/constituency shape: selected maps of extremes; do not default to choropleth.

### Sports
Chart the mechanism, not the scorecard. Use win-probability/advantage trajectories for match story, phase curves by over/minute, impact-in-context for player valuation, and clusters/prototypes for recurring shapes.

### Geography
Use maps only when location, adjacency, or boundary shape is the story. Use sorted bars/tables for state/district rankings.

### Surveys
- Broad Likert composition: diverging stacked bars.
- Distribution shape/polarisation: faceted response histograms.
- Cross-tabs: small multiples or fill bars with direct percentage labels.

### Simulation / Monte Carlo
Avoid pages of undifferentiated wiggly lines. Choose task-specific reduction: input-output scatter with threshold quadrants, density via alpha, fan/ribbon, distribution of outcomes, or clustered representative paths. State what each dot/path means. Label quadrant shares when possible.

### Decomposition and diagnosis
Use waterfall/bridge charts for drivers of change. Use ranked contribution bars for “largest drivers”. Use root-cause tables when exact owner/action/reason matters. In management contexts, pair chart with action implication.

### Management decks
Start with scorecard when many KPIs need scanning: actual, budget/target, prior year, variance, direction. Then show diagnostics: trend, bridge, division bars, exception table, action matrix. Do not dump dashboard pages without interpretation.

### Model explanation
Prefer observable category-rate or scenario-effect charts over coefficient tables. For each factor, show possible values/categories vs outcome rate. Use one panel per factor when category sets differ.

### Risk and portfolio
Averages and volatility hide skew, fat tails, and changing correlation. Use distributions, downside-tail views, bootstrapped scenario fans, utility curves, and drawdown/threshold probability charts.

## Substack-derived critique rules

- A good chart communicates one thing well.
- Removing data can increase information content if it mutes noise and preserves the claim.
- Label the interpretation: gap, quadrant, cluster, excess area, scenario.
- Small multiples beat crowded overlays for many series.
- Use quiet context and strong focal signal.
- Regression lines are dangerous rhetorical devices; use sparingly and honestly.
- Axis choices depend on chart type: bars zero, scatters tight/fair.
- Break convention only when the data structure demands it, and explain the custom form.
- Avoid 3D pies, decorative infographics, fake precision, and novelty that buries the data.


## Banned/default-avoid chart forms

Never pick these as the recommended visualization:
- pie charts or donut charts
- 3D charts of any kind
- animated/moving charts
- interactive charts/Plotly/D3 dashboards
- decorative infographic forms where area, icon size, or perspective distorts values
- gauges, speedometers, radar/spider charts

For part-to-whole, use sorted bars, 100% stacked bars, compact tables, treemaps only with caution, or small multiples. For time-varying part-to-whole, use share lines or 100% stacked bars/area only when mix is the story.

Interactivity is not a chart-selection crutch. Recommend static charts. If the user asks for an interactive dashboard, first propose the static decision graphic(s) that answer the question; mention interactivity only as an optional exploration layer, never as the core answer.

## Decision table

| Claim/problem | Preferred visual | Context layer | Avoid |
|---|---|---|---|
| Trend | Line + points | Event marker, direct label | Bar per period unless few periods |
| Slowing growth | Raw line + dotted earlier-growth projection | Slowdown point | YoY as main chart for general audience |
| Intervention impact | Line + pre/post marker + counterfactual | Vertical line/band | Before-after bars without trend |
| Forecast miss | Actual vs forecast line/ribbon | Gap label | Only actual trend |
| Ranking | Sorted horizontal bars | Highlight, value labels | Alphabetical bars |
| Distribution skew | Histogram/density/ECDF/box/violin | Thresholds, log scale | Mean-only chart |
| Two-variable relation | Scatter | Entity labels, fair axes | Regression-first chart |
| Vote-seat efficiency | Vote-seat scatter | Party colours, labels | Map-first |
| Swing scenarios | Seats vs swing lines | Majority line, facets | Single forecast number |
| Spatial shape | Selected maps | Highlight geography | Choropleth for non-spatial ranking |
| Survey polarisation | Faceted rating bars | Focal highlight | Average score only |
| Share substitution | 100% stacked bars/area | Direct share labels | Stacked when exact comparison needed |
| Simulation | Threshold scatter/fan/prototypes | Quadrant shares | Undifferentiated spaghetti |
| Root cause | Waterfall/ranked bars/table | Action labels | Headline KPI only |
| Risk | Scenario distribution/utility/downside | Threshold probability | Mean-vol only |
| Many metrics scan | Scorecard/table + sparklines | Variance arrows | Dense dashboard without story |

## Recommendation output checklist

Every recommendation should include:
- recommended visual form
- why it fits the claim
- encodings: x/y/color/facet/labels
- context layers: thresholds/events/projections/annotations
- what to avoid
- implementation note if code is requested

## Iteration notes from rendered OOS tests

### Data support before chart choice
If the dataset cannot directly support the user's question, do not invent a better chart for unavailable fields. Say what evidence is available, chart that evidence, and state the limitation. Example: if asked for fuel-price transmission but only category correlations and WPI weights exist, use weighted correlation/impact views and note that time-series causality is not available.

### Weight × effect stories
When categories have both an effect size/rate/correlation and a population/business weight, chart the weighted importance if the claim is impact. A high-effect tiny category may be less important than a moderate-effect large category. Good forms:
- ranked bars of `weight × effect`
- scatter of effect vs weight with bubble labels
- two-panel: effect ranking and weighted-impact ranking

### Waterfall integrity
Use a waterfall/bridge only when components reconcile from start to end. If driver numbers are partial, directional, overlapping, or quoted from commentary, use ranked adverse/favourable driver bars or a root-cause/action table instead. Label it as “drivers cited” or “directional impact”; do not imply accounting reconciliation.

### Scorecard + chart layout
Scorecard-plus-diagnostic can work, but only if labels do not collide. If driver labels are long or the scorecard has many columns, split into separate slides/figures or use a vertical layout. Do not shrink text to force a dashboard-like layout.
