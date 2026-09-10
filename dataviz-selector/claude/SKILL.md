---
name: dataviz-selector
description: Choose charts for data stories, including S-curves, knee-bends, inflections, local peaks, and misleading/decorative forms.
---

# Dataviz Selector

Use before making a chart when the user has a dataset and a question/hypothesis/story. Core job: pick the visual form that makes the intended claim easiest to see and hardest to misread. This public skill is self-contained.

## Form constraints

- **Prompt precedence.** Honour a chart form explicitly requested in the prompt; it overrides these default form exclusions. A form merely present in a source image is not a request. Preserve honest quantities, scales, and claims in the requested form.
- **Default exclusions.** Do not choose pies, donuts, radar/spider charts, gauges/speedometers, decorative infographic forms, 3D charts, or animation/interaction as the main answer unless explicitly requested.
- **Points and comparisons.** Scatter requires two quantitative axes. For categorical magnitudes, use bars rather than isolated dots or lollipops. Dumbbells are valid for paired comparisons; point-and-interval plots are valid for estimates with uncertainty.
- **Magnitude channel.** Use length or position for precise quantity comparisons, not area or volume. Heatmaps are valid when colour reveals patterns or clusters across a matrix. Default to equal-size scatter points; do not add a bubble-size measure or choose a treemap. An explicit form request overrides this preference.
  - **A heatmap's scale must resolve the cells that carry the reading.** A single sequential colour scale only separates values whose magnitudes are within reach of one another. When one cell, row, or column dwarfs the rest (a dominant category, a runaway "Other", one huge period), a linear scale saturates on that outlier and flattens everyone else into one indistinguishable near-baseline shade - the matrix then hides the very comparison it exists for. Before choosing a heatmap, check the spread the colour must span: if the max is many times the bulk of the cells, don't map raw magnitude on one linear ramp. Pull the dominant series out (its own panel, a total line, or an annotation) and heat only the comparable remainder; or map a within-row/within-column share or rank so each strip's pattern shows; or, only when the skew is genuinely the honest story and must be read, a quantile-binned or log scale (marked as such). If none of these fits the claim, the quantity belongs on length/position, not colour.
- **Connections and accumulation.** Lines require a meaningful sequence or relationship between connected observations. Waterfall steps must reconcile a meaningful starting and ending quantity; unrelated changes do not form a waterfall.
- **Reading task and space.** Choose an encoding that makes the intended comparison readable at delivery size. Grouped bars still fail if group identities or values cannot be followed. Related claims may share a chart; separate views only when the reading requires them. Arrange panels in a grid or strip according to the comparison and available space.

## Cold selection in a repair

When selecting a form for a repair, run on the recovered intent and data, not the source chart. Run it **cold**: the source form gets no vote - choose the form the messages and data want, as if drawing for the first time. There is no "source form is clearly correct, keep it" shortcut; a many-series stacked bar/area whose message is per-series comparison or trajectory becomes small multiples, direct-labelled lines, or a ranked/indexed view. Preserving the categories means keeping the data, not the chart type - a tidier version of the same illegible form is not a selection. A well-formatted table is a legitimate cold verdict when the intent wants exact lookup or non-commensurable values.

## Workflow

0. **Disambiguate semantics first:** measure, denominator, displayed universe, time/context boundaries, claim strength, audience meaning of the units. Choose a form and cues that make the comparison hard to misread; don't prescribe a type or vocabulary when another defensible design communicates the distinction as well.
1. State the claim or related claims the chart must support. Split views when one form cannot carry them readably.
2. Identify the comparison: time, peers, baseline, target, counterfactual, distribution, spatial, model expectation, or decomposition.
3. Identify the data grain: time series, category, entity, location, event/ball, survey response, model output, simulation, transaction, or scorecard metric.
4. Inspect the data's structure for features relevant to the claim; treat breaks, extremes, clusters, or changes as candidates only when robust, informative, and useful at viewing scale. Candidate selection belongs to `chart-annotations`.
5. Choose the simplest chart that exposes that comparison.
6. Add only necessary context: direct labels, event line/band, threshold, uncertainty ribbon, counterfactual, facet, or annotation.
7. Say what to avoid: misleading axis, overplotting, unnecessary regression, crowded legend, map-for-ranking, stacked bars for precise comparison, etc.
8. If generating code, apply `karthik-data-visualization` styling before final output; if the verdict is a table, apply `karthik-table-style` instead.

## Table or chart?

A well-formatted table is a visualization, not the absence of one; treat it as a real candidate every time.

- **Table** when the task is reading exact values; rows are few and looked up by name; columns aren't commensurable on one scale (no honest shared axis); the artifact is a reference/monitoring surface read cell by cell; or a "chart" would just be a bar-chart of a handful of numbers read precisely. Columns sharing one unit (all %, all $, all counts) are commensurable by definition; do not cite non-commensurability to justify a table when they share a unit.
- **Chart** when the message is a shape, trend, comparison, or distribution the eye grabs pre-attentively - position, length, or slope carrying the claim faster than scanning numbers.

When both work, decide by the dominant task. A table is chosen for exact lookup or non-commensurable values, never as a dumping ground for data a chart could show as a shape. When the headline is a trend or shape across an ordered sequence but exact values are also wanted, the answer is a table-chart hybrid - a sparkline column per row, or small-multiple sparklines - not a plain table that hides the shape the headline asserts; route these to the sparkline rows in `karthik-table-style`. On a table verdict, hand off to `karthik-table-style` with the reading task,
comparison scope and focal entities. Use `recommend_table_layout` after formatting
content. Conditional or focal colour still needs a colour plan even without chart
series; record sequential/diverging scales in `colour_role` and the comparison
strategy, preserving their order rather than selecting distinct categorical hues.

## Fast chooser

- **Trend/intervention:** expose level, change, comparison, and uncertainty; add a supported event or baseline when it changes interpretation.
- **Nonlinear/changing trajectories:** show the observations; use a derived summary only when its assumptions and uncertainty stay visible.
- **Slowing growth:** show level and the comparison that establishes slowing; a derivative or projection only when it answers the question and is interpretable.
- **Forecast/anomaly:** actual line, dashed forecast, uncertainty ribbon, highlighted anomaly/intervention window.
- **Multiple comparable trajectories:** when observations have a meaningful sequence, default to a single panel with direct-labelled lines. Move to small multiples only when the single panel fails - too many series to direct-label, or overplotting into spaghetti. Series count and overplotting are the trigger; crossing lines or a noisy shape are not. When the claim compares trend/slope across series, faceting is a poor fit even before overplotting forces it (separated frames make the reader compare angles from memory, and free per-panel scales let equal-looking slopes stand for unequal rates) - keep slopes on one shared axis (single panel, slopegraph, or indexed lines) and face only when overplotting leaves no option, at which point the panels carry each series' shape, not the cross-panel slope. See the small-multiples layout rules below.
- **Smoothing a dense series:** when one series has so many points that connecting them all buries the trend, either overlay a smoothed trend (loess/regression) on the faint raw series, or drop the connecting line and show points as a scatter with the smoother through them. Driven by point density in one series, unrelated to series count. At most one or two smoothers per graph; show the smoother's uncertainty; don't let it erase real turning points; mark extrapolation as a projection.
- **Chat/thumbnail consumption:** prefer forms with direct labels and strong contrast; avoid faint colour differences or tiny legends.
- **Colour by data role:** focal-plus-grey for emphasis, qualitative hues for nominal identity, one ordered sequential scale for magnitude, diverging only around a meaningful midpoint. If colour does work position or direct labels could do better, remove it. (Full workflow: `dataviz-color`.)
- **Slopegraphs** aren't limited to two periods - carry several ordered positions as one labelled line per category, label both end columns, show every value; choose aspect ratio from row density, label geometry, and medium.
- **Two-state comparison** (before/after, share-A/share-B, expected/actual): prefer the orientation where each state is self-identifying - its own labelled axis or position, the connecting line/bar carrying the category - so the reader reads states off position, not a colour/shape legend. Dumbbells are valid for paired comparisons: connect the two compared values within each category and make the endpoint identities clear. Choose a slopegraph when separately labelled state positions make the comparison easier to follow. Don't split the two states into two side-by-side panels sharing one category axis: that puts each category's two values in separate frames, so the reader matches position across a gap instead of reading the pair at a glance, and two half-panels squander the frame on chrome. One frame carrying both values per category (dumbbell, slope, or diverging bars from a shared baseline) is the default; reach for separate panels only when the two states are genuinely non-commensurable (different units/scales the reader looks up apart), not merely two shares.
- **Two-point comparisons:** choose among slopegraphs, dumbbells, paired bars, or tables by whether the task is seeing change, comparing endpoints, or reading exact values. Number of time points alone doesn't fix the form.
- **Ranking:** sorted horizontal bars, longest at top, descending - the order carries the ranking, so never leave them in input/alphabetical order. (Vertical bars read left-to-right matter less but still order by a meaningful key.) Bar axis starts at 0; highlight an item only when the question/evidence/story makes it focal.
- **Ordered category axis** - time (quarters, months, years), stages, sizes, ranked bins - is not a ranking to sort by magnitude; its reading direction is fixed by the sequence (left-to-right horizontal, top-to-bottom vertical, never inverted). Sort by magnitude down the y-axis only for nominal categories. This holds inside small multiples too.
- **Single value per category as magnitude is a bar** - filled length is the cue, the zero baseline anchors it. For multiple values per category, choose grouped bars, suitable facets, or a table.
- **Composition/share:** use 100% stacked bars/areas only when one period's broad mix is the story. That the parts sum to 100% is a property of the numbers, not a reason to choose a stack. If the claim describes how components move across periods or groups, those are component trajectories - use lines, slopes, small multiples, grouped bars, or a table - even when shares total 100%. (See the aggregate-and-parts guardrail.) A quantity that is itself a signed net, delta, or difference (a year-on-year change, a waterfall step, a variance) is not a part of a whole and has no honest share of a total - never frame it as a share, 100% stack, or pie; show the signed change directly (a waterfall, diverging bars, or a slope).
- **Distribution/skew/tails:** histogram, density, ECDF, box, or violin; log scale for income/wealth/power-law data.
- **Relationship:** scatter only for quantitative × quantitative axes, with direct labels; regression only when relationship is the claim and uncertainty is shown.
- **Normalization:** preserve the numerator-denominator relationship, then choose a form by whether the task is ranking, scale diagnosis, temporal/spatial variation, or distribution.
- **Domain-specific questions:** derive the form from mechanism, comparison, uncertainty, and audience, not a domain recipe.

## Small-multiples layout

Once faceting is warranted, the recommendation isn't complete until you specify:

- **Arrangement.** Choose a grid or strip from the comparison and delivery frame. Aligned strips can make shared-time comparisons easier; grids can accommodate more panels. Keep panels legible without dropping required content to make them fit.
- **Ordering.** Preserve meaningful sequences; otherwise order panels by the comparison, magnitude, story importance, or a relevant grouping. Input order alone is not a reason.
- **Shared vs free scale.** Shared whenever the claim asks the reader to compare across panels at all (levels or slopes/rates), because free scales let equal-looking panels hide unequal magnitudes and slopes. Free per-panel scales only when the message is each panel's own shape/turning points, panels aren't compared, and magnitudes differ enough that a shared scale flattens small series - and mark free scales per panel.
- **Comparable scales.** Share value scales only when quantities are commensurable; matching unit labels alone do not establish that. Different measures can use separately titled panels with their own labelled value scales, aligned on a common time axis when useful. Use a table when the task is lookup across measures.
- **Faceting by series.** When each panel is one series - the panels *are* the categories, each titled by its series name - colour is not an encoding channel: do not add a legend or a per-series colour key, which only round-trip against the panel titles. Use one ink across panels, or focal-plus-grey to mark a single focal series. Equally, don't set a 100%-composition or share mini-panel beside per-series share panels: shares summing to a constant restate the breakdown the panels already carry (see the aggregate-and-parts guardrail) - drop it.

## Output format for recommendations

```markdown
Recommended visual: <chart form>
Why: <claim-comparison fit>
Encoding: X = ..., Y = ..., colour/facet/label = ...
Context layers: <thresholds/events/counterfactuals/knee-bends/local extrema/annotations>
Avoid: <bad alternatives or pitfalls>
If implementing: <short code/design note>
```

## Hard guardrails

- **One chart, one main job.** A form must let every message the brief carries be read off it; check each brief message against a visible element before finalizing and treat any message with no element as dropped.
- **Aggregate and its parts.** The total and the mix rarely fit one form: a breakdown shows the parts not the sum, a total line shows the sum not the parts. When the brief needs both, that's two jobs - pair a plain total line (aggregate carried on position) with the breakdown, not a stacked bar/area, whose floating segments read worse than a breakdown and whose moving height reads worse than a direct total line. This pairing is justified only when the aggregate is a genuinely separate, independently-varying absolute quantity. When parts are shares summing to a constant 100%, the total carries no information and a composition panel only restates the breakdown - use one view. When the pairing uses a small-multiples breakdown, set the total apart (a separate larger panel with its own labelled scale and a clear break), never as one more cell of the grid - it's a different quantity at a different scale, and mixing it in implies a false commensurability.
- **No redundant panels.** Don't emit two panels encoding the same data grain and the same numbers; a second view earns its place only by carrying a message the first cannot, and you must name that message.
- **Match channel to job.** Give the most important comparison the most accurate channel. Reading accuracy, most to least: position on a common scale, length, angle/slope, area, colour/density.
  - Magnitude to compare → length or common-scale position (not area/angle/colour intensity).
  - Change/trajectory over time → position (lines, slopes), not colour shifts.
  - Rank/order → position or an ordered sequential scale.
  - Category/identity → hue (qualitative palette, not lightness, which implies order).
  - Relationship between two measures → x-y position (scatter).
  - Part-to-whole → length from an aligned baseline.

  When the main quantity sits on a weak channel (a value read off colour, a trend off shading, a size compared by area), move it to a stronger one. Reserve weak channels for what they're good at: colour/density for emphasis, grouping, or hot/cold regions across many cells; do not use area/angle as a substitute for length or position when comparing quantities.
- **Coordinate mapping ≠ scaffolding.** A shared or fixed scale preserves comparable positions without requiring visible ticks, tick labels, an axis title, or gridlines. State both decisions in the plan. When direct labels on the reading-carrying marks give the needed values, keep the common domain but drop scaffolding that only repeats them. An unlabelled supporting mark doesn't itself earn an axis - keep scaffolding only to estimate that mark's value, align values, or read a baseline/threshold. When the form is direct-labelled (lines, slopes, or points whose marks carry their own values), emit the direct-label contract with the plan - name the labelled key set (which axis/role, endpoints and exceptions included) - and state explicitly that the value axis carries no reading, so the build drops its ticks, gridlines, axis line, and axis title, keeping only a zero baseline if a mark needs it. Naming the key set is what lets the execution gate fire on your editorial labels, not only on near-complete coverage.
- **Graphical integrity.** The size of the visual effect matches the size of the effect in the data: anything encoding value by length/position needs a common untruncated baseline; a one-dimensional quantity isn't encoded by area/volume; don't add a dimension the data lacks (3D, perspective, depth). Bars start at zero; scatters need not. If a form can only make the story look larger than it is, choose another.
- **No dual value axis to imply a correlation.** Two series on two independent y-scales manufactures an apparent relationship from arbitrary scaling - the reader reads a co-movement the data doesn't assert. When the claim is that two series move together, put them on one axis (index or normalise to a shared base), use two stacked panels sharing the x-axis, or a scatter if the relationship itself is the claim. A single second axis is defensible for a genuinely different unit the reader looks up separately, and an explicit prompt instruction to use a dual axis overrides this - honour it (keep the scales honest and don't imply a correlation the data doesn't carry); otherwise don't overlay two trends as if correlated.
- **Don't invent groupings to manufacture a claim.** Merging categories (a forced two-way split, a bucketed range, combined series) changes what the data says, so grouping needs a reason in the data or question - a meaningful taxonomy, a domain threshold, a grain the audience reads - never that the coarser cut looks cleaner. Keep finer categories separate when the claim is about their distinct trajectories. Exception: rolling an immaterial long tail into "Other" declutters without touching the categories the claim rests on.
- Don't extend regression/counterfactual lines beyond defensible range without marking them projections.
- Label derived meaning directly when the evidence is a gap, quadrant, cluster, area between curves, knee-bend/inflection, or local max/min.
- **Prefer direct labels to legends; let perception group and link.** The reader groups by proximity/similarity and links by connection before consulting a legend - prefer directly labelled and connected forms (lines, slopes) to a colour the eye must match; use panels, spacing, or a light enclosure to separate or mark groups; keep one focal element as figure against muted ground. Don't hand unrelated series a similar encoding or make several channels compete to be seen first. Choosing the form chooses what the reader sees first (the composition gate `dataviz-aesthetic` checks exactly that).
- Choose a form where labels and marks pair without guesswork at delivery size. If the natural baseline pushes labels far from their marks, use a compact row structure, restrained guides, a table-chart hybrid, or faceting to restore traceability.
- Size the canvas from the information and medium; whitespace should group, separate, or emphasise - don't keep blank regions the library or source aspect ratio created.
- Part-to-whole: prefer sorted bars, 100% stacked bars, tables, or small multiples over pies/donuts; stack only for broad composition, not precise component comparison.
- Maps only for spatial stories.
- If a clever chart needs too much explanation, use a simple chart plus annotation. Add a label/annotation only when it materially improves the reading (wording and candidate selection: `chart-annotations`).
- Choose among chart, table, or dashboard by whether the task is monitoring, exploration, comparison, or narrative explanation; use interaction as the main answer only when requested.
