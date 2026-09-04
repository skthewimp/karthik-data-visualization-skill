---
name: karthik-data-visualization
description: Create or review charts, dashboards, and data visualizations in Karthik's style. Use for plots, labels, palettes, annotations, and visual analysis.
---

# Karthik Data Visualization

Use for any chart, graph, dashboard, or data-visualization work: chart code, visual-analysis pages, annotations, captions, labels, palettes, and chart review. Apply the workflow below before finalizing design or code. This public skill is self-contained.

## Workflow

**Semantic preflight (before choosing a form):** identify the measure's dimensional meaning, the displayed universe and denominator, the relevant time/context boundaries, the strength of any claim, and whether the units are interpretable for the audience. Make these unmistakable through wording, scale, labels, annotations, form, and context. A chart that is numerically faithful but invites a materially different reading is not repaired.

1. **Clarify the job:** what comparison matters, what the viewer should learn, what evidence supports it. Separate what the supplied data supports from what a screenshot only suggests.
2. **Choose the structure** from comparison, evidence, density, audience, and medium. Use `dataviz-selector` when the form is not settled. Don't infer a form from one field type or invent detail the evidence doesn't support.
3. **Build data-outward:** data first, direct labels second, annotations third, grids/axes last.
4. **Check graphical integrity:** scales, baselines, proportional encoding, missing context, any effect that exaggerates or understates the data.
5. **Eraser test:** remove any ink that doesn't carry data, labels, or necessary context.
6. **Render and inspect the export.** Fix anything clipped, overlapping, or misaligned from the actual image, then re-render. Confirm the House defaults below. Once defect-free, read the whole image as a composition (`dataviz-aesthetic`): one focal element seen first, every mark earning its place, whitespace grouping not filling. A defect-free chart can still read as styled-default; the composition pass is what makes it premium.

## House visual defaults

Properties the exported image must satisfy, whatever the renderer, verified at render-and-inspect. Override only on an explicit prompt instruction or an established project/brand system - not a model's sense that it "looks better," not a renderer's theme default.

- **Light background.** White or near-white plot and canvas. Dark/inverted only when explicitly asked; if the fallback renderer defaults dark, set it light.
- **Proportional sans typeface.** Clean legible sans (project/brand face if specified, else Inter, Helvetica/Arial, or the platform sans). Monospace only for a requested code/terminal look.
- **Direct labels are the default identity route.** Name marks and series on the plot where they read legibly, and drop the legend and any axis they make redundant. Default, not an enhancement.
- **Claim-first title, trend subtitle.** Title states the finding; subtitle summarises the trend/comparison; neither restates mechanics. Fall back to a question, measure, or explicit null only when the evidence genuinely won't support a claim - never manufacture one.

A dark, monospace, legend-dependent, or mechanically-titled chart is a defect to fix before delivery, like clipping or a wrong scale. Prefer static PNG/SVG exports unless interactivity is explicitly needed.

## Surfacing the finding

- Put the finding on the chart, not only the title: where one mark carries it, direct-label the few points that carry the claim, never all of them.
- A change or comparison ("X to Y", "+38%", "doubled") is neither a label nor an annotation - the shape shows it, so its claim goes in the title.
- Reserve annotations for a fact from outside the data that explains the finding (a cause, event, regime change). `chart-annotations`, when loaded, makes that call and places both labels and annotations.
- When an installed writing or brand-voice skill is present, use it to word headline, claims, subtitle, and annotation text; this skill sets their style and placement. Otherwise follow the prompt and the title rules above.
- Let the evidence set whether the title states a claim, question, measure, or null; don't manufacture a claim to sound decisive. Let complexity come from the data, not decoration.

## Labels and scaffolding

- **Editorial scope first.** A direct label earns its place; it is not the default for every point. Label only what carries the reading: a series' identity, an endpoint, the focal comparison, a genuine exception, or a value the reader must look up exactly. Points that only repeat a shape or level a labelled neighbour shows stay in the data. Over-labelling is the main reason a chart reads busy and cheap. The author sets this scope; `recommend_labels`/`recommend_text_placement` pick and place feasible points within it - they never widen it.
- **One consistent labelling system.** Place each point value with one small offset from its mark, each series name adjacent to its line endpoint. Pass point values as `data_label` blocks, series/category names as `label` blocks. Draw a connector only when the tool returns a `leader_line`. When anchors came from `place_on_marks`, draw label and connector from the returned native coordinates (`placed_data` top-left-anchored, `leader_line_data`) - never a hand-written `geom_segment`. If several ordinary labels need leaders, revise the label set, anchor, or layout instead.
- **One identification route per series.** When a direct label carries the identity a legend or categorical axis would, remove that axis/legend. Same for quantitative scaffolding: when the marks that carry the reading are labelled, drop the value axis, ticks, and gridlines that only repeat them. Keep a scale/baseline/reference line only for a task the labels don't do - estimating an unlabelled mark, alignment, a threshold. Default is remove.
- **Shared legends across panels:** replace the lookup in every panel that uses the mapping unless a shared labelling system makes each panel independently readable. Don't direct-label only the easiest panel; enumerate expected labels per panel before rendering.
- **Bind labels by proximity.** The intended label-mark link must be visually stronger than competing ones. Judge distance to the visible target, not a shared row or edge; alignment alone doesn't bridge whitespace. If labels would collide or drift, change the label system or structure.
- **Type by hierarchy** at delivery size, not a fixed point recipe. Data labels/values may lead within the plot; axis titles, ticks, sources, notes stay readable without competing. Oversized secondary text is a hierarchy failure even when legible.
- Check rendered text and mark bounds for collisions, clipping, occlusion; fix layout/wrapping/placement before shrinking legible type. Tune labels and spacing after rendering, not from code inspection alone.
- **Whitespace does one of three jobs:** group, separate, or emphasise. Inspect title-to-plot, label-to-mark, panel-to-panel, plot-to-note, and outer gaps; trim blank area that serves none.

## Grouping and emphasis

The reader groups marks perceptually before reading labels. Use those groupings:

- **Proximity / common region:** near or shared-panel marks read as one group. Keep related marks and labels close; separate unrelated series.
- **Similarity:** shared hue/shape/weight reads as the same kind. One meaning, one encoding; never give unrelated series a similar encoding.
- **Connectedness:** a line, or a label on its mark, binds more strongly than a colour the eye must match - why direct labels beat legends and a slope beats two dots.
- **Enclosure:** a light band or box says "these belong / look here" more quietly than an arrow or heavy outline; reach for it first.
- **Figure-ground:** one focal element against muted context. Keep exactly one thing as figure; when two compete, neither wins.

**Preattentive first read:** exactly one channel makes the single most important thing pop without search. Decide this focal element before drawing, and verify after rendering that the eye lands there first (`dataviz-aesthetic` owns that post-render check).

## Colour (craft summary)

Full selection and validation workflow: `dataviz-color` (backed by `recommend_colours`, `validate_palette`). Essentials:

- Colour earns its place. Position, length, order, labels carry the comparison; colour clarifies identity, order, direction, or emphasis. Default to neutral marks; use one focal colour plus grey context only when the focal item is named by the question, supported by evidence, or requested. Never manufacture a highlight.
- Match scale to data: qualitative hues for nominal categories, one ordered sequential scale for magnitude, diverging only around a meaningful midpoint. No rainbow; don't encode order with arbitrary categories. Use domain-specific palettes where meaningful; avoid decorative or arbitrary series colours.
- Same meaning, same colour across panels and revisions. Reserve the most saturated/warm colour for the focal series or warning; equal-status series get comparable weight. Preserve an existing semantic palette unless changing it solves a stated problem; derive every mark, connector, label, annotation, legend entry from the same mapping.
- Don't give a residual/catch-all bucket (Other, Misc, remainder) the focal colour or the first slot, even when largest; relegate it and spend emphasis on named categories.
- For signed/directional change, define the comparison direction first, then derive every mark, gap, label, and legend entry from that sign; reinforce direction with sign, position, wording, or shape, not colour alone.
- Every encoded colour stays distinct from background and neighbours at display size and after compression; adjacent or stacked regions differ in both hue and lightness, with a restrained boundary only when separation otherwise fails. WCAG is a diagnostic (≈4.5:1 text, 3:1 large/marks). Don't rely on hue alone; avoid red-vs-green as the sole distinction; prefer Okabe-Ito, ColorBrewer, or viridis. Inspect the export at delivery size, after compression, and in grayscale.

## Form and layout

- Match visual hierarchy to information hierarchy: data, labels, annotations, grids, borders. Always answer "compared to what?" - show comparison and context explicitly. Favour forms that make comparison and change easy to read.
- Line charts over stacked bars when the question is trend, not composition. Use stacked bars only for broad composition: only segments on an aligned baseline compare precisely, so if exact component comparison matters, switch to a form with aligned baselines.
- **Fit the value axis to the data**; the unit's ceiling is not the axis maximum. Values running 1-44 don't earn a 0-100 axis. Resolve the range with `recommend_axis_range` (from the plotted values) rather than defaulting it to the measure's natural domain, and pass its `limits`/`breaks` to the renderer - a build model reflexively stamping 0-100 on a percentage is the failure this prevents. Decide only the judgment it takes: keep a zero baseline where the encoding needs it (bars, or where zero is a compared reference, or a line whose absolute level matters), so pass `zero_based=true`; a non-zero baseline is fine for a line whose story is movement in a narrow band, if it isn't disguising a change's magnitude. Pass `hard_max` (e.g. 100) only when that full range is genuinely the point.
- **Shared/compressed scale:** buys comparability at the cost of resolution - a small series flattens toward the baseline. When a needed value can't be read off the scale, put the number on the mark (endpoints or focal value) before abandoning the shared scale or adding a second one. But when several small series converge into a baseline cluster, labelling every point makes it worse: split them into their own panel/inset or a table instead.
- **Small multiples** for comparison across groups - see `dataviz-selector` for the full grid/ordering/scale rules. In brief: grid (rows×columns) proportioned to the delivery frame, panel count that stays legible, panels ordered by decreasing peak value or story importance (never input order), shared scale whenever panels are compared, per-panel scales marked when free.
- Consider sparklines or compact tables when many series need shape plus current value; range frames, rug marks, or labelled points when axes can carry more.
- Include enough source, scale, timeframe, and transformation notes for a stranger to evaluate the evidence. Make the chart stand alone without caveats doing the work. Save public outputs with stable descriptive filenames when the project expects artifacts.

## Optional: audited repair plan

Work output-first by default - build and inspect, no up-front plan. Only when an audited repair is explicitly requested, record a short plan first: measure and evidence scope; selected form and why the source form was rejected; one identification route per series; intended contents of title/subtitle/legend/plot/annotation/footer zones; colour's semantic role; one implementation requirement per fatal/major finding with affected zones and observable outcome; one preservation mapping per required source item with the observable state proving no regression; a layout plan for the delivery size naming longest text, dense regions, likely collisions, and their mitigation. Treat the plan as executable scope. A revision continues from the latest candidate and changes the smallest relevant region; a redesign returns to the evidence.

## Renderers and code

- Preserve the renderer the project already uses. For a new Karthik-style static chart with no precedent, prefer R/ggplot2 when available - an implementation preference, not permission to keep `theme_gray()` or any library default unexamined.
- Rendering/inspection tools are mechanical infrastructure, not a style system. Don't port a sound ggplot2 chart to Matplotlib for richer metadata. If Matplotlib is the practical fallback, set typography, palette, grid, axes, labels, and spacing deliberately; default Matplotlib aesthetics fail this skill.
- The ladder: the project's own renderer, then a deterministic backend if the harness has one (this repo's `renderer="auto"` picks ggplot2 when `Rscript`+`ggplot2`+`ragg` are present, else a deliberately-configured Matplotlib; an explicit user requirement wins; record why Matplotlib was used), then whatever suits the medium with typography/palette/background set by hand. What fails this skill is the default unconsidered look (dark canvas, monospace, raw library defaults), not the choice of renderer - a hand-authored HTML/SVG chart built to the House defaults is legitimate; a theme-default ggplot2/Matplotlib chart is not. If no renderer can meet the House defaults, report that as a failure rather than shipping a violation.
- After changing any identification, scale, or encoding element, inspect that exact relationship in the export; confirm every required item stays identifiable and correctly bound, and that any key represents only mappings present in the chart. Text over a mark is an inside label - verify contrast and padding. Inspect the worst example of each repeated placement pattern, since direction, sign, length, or panel side can move where the same rule lands.
- In ggplot2, make `build_chart()` return a ggplot or `list(plot=<ggplot>, metadata=<list>)`, and export through `ragg`. See [references/ggplot2-repair-patterns.md](references/ggplot2-repair-patterns.md) for sorted-bar, diverging-bar, slopegraph, direct-labelled-trend, and multi-panel implementations.
