---
name: karthik-data-visualization
description: Create or review charts, dashboards, and data visualizations in Karthik's style. Use for plots, labels, palettes, annotations, and visual analysis.
---

# Karthik Data Visualization

Use this skill for any chart, graph, dashboard, or data visualization work, including chart-generating code, visual analysis pages, annotations, captions, labels, palettes, and chart review.

Apply the workflow below before finalizing design decisions or chart code. Private local references may add nuance, but this public skill is self-contained.

Workflow:

**Semantic preflight:** before selecting a form, identify the measure's dimensional meaning, the displayed universe and denominator, the relevant time/context boundaries, the strength of any claim, and whether the units are interpretable for the audience. Make these semantics unmistakable through the most appropriate combination of wording, scale, labels, annotations, chart form, and context. A chart that is numerically faithful but invites a materially different interpretation is not repaired.

1. Clarify the analytical job: what comparison matters, what the viewer should learn, and what evidence supports it. Separate what is directly supported by the supplied data from what is only inferred from a screenshot.
2. Choose the structure from the comparison, evidence, density, audience, and medium. Use `dataviz-selector` when the form is not already settled. Do not infer a chart form from one field type or invent more detail than the evidence supports.
3. Build from data outward: data first, direct labels second, annotations third, grids/axes last.
4. Check graphical integrity: scales, baselines, proportional encoding, missing context, and any visual effect that exaggerates or understates the data effect.
5. Apply the eraser test: remove any ink that does not carry data, labels, or necessary context.
6. Render and inspect the exported image; if anything is clipped, overlapping, or misaligned, adjust labels, spacing, hierarchy, and source notes from the actual output, then render again. Confirm the export also meets the House visual defaults below. Once it is clean of defects, step back and read the whole image as a composition (use `dataviz-aesthetic`): one focal element seen first with nothing competing, every box/rule/colour/bold phrase earning its place, whitespace grouping rather than filling. A chart with no defects can still read as styled-default output; the composition pass is what makes it look premium.

## House visual defaults

These bind the finished output regardless of which renderer produced it - the deterministic tool, ggplot2, or a hand-rolled fallback. They are properties the exported image must satisfy, verified at the render-and-inspect step, not styling that a busy fallback path may drop. Override any of them only on an explicit instruction in the prompt or an established project/brand system; a model's own sense that the chart "looks better" otherwise is not such an instruction, and a renderer's default theme is not a request.

- **Light background.** The plot and canvas are white or near-white. Dark, terminal, or inverted backgrounds appear only when the prompt or brand system explicitly asks. If the fallback renderer defaults to dark, set it light.
- **Proportional sans typeface.** Type is a clean, legible proportional sans; never a monospace/terminal face or an unstyled library default. Use the project or brand typeface when one is specified; otherwise default to a widely-available proportional sans (for example Inter, Helvetica/Arial, or the platform sans stack). Monospace only for a requested code/terminal aesthetic.
- **Direct labels are the default identity route.** Name marks and series on the plot wherever they read legibly, and drop the legend and any axis the labels make redundant (see the identification and scaffolding rules below). This is the default, not an enhancement added only if time allows.
- **Claim-first title, trend subtitle.** The title states the finding the chart supports; the subtitle summarises the trend or comparison; neither restates the chart's mechanics. Fall back to a question, measure, or explicit null only when the evidence genuinely does not support a claim - do not manufacture one (see the title/subtitle rules below).

Surface the finding on the chart, not only in the title: where a single mark, point, or span carries it, put a direct label on that mark - label the few that carry the point, not everything. Reserve annotations for a fact from outside the data that explains the finding (a cause, an event, a regime change); an in-data quantity is a label, never an annotation. When `chart-annotations` is loaded it makes that call and places both. When an installed writing or brand-voice skill is present in the environment, use it to word the headline, claims, subtitle, and annotation text; this skill sets their style and placement. If none is installed, follow the prompt's stated preferences and the title/subtitle rules below.

Check the export against these at inspection. A dark, monospace, legend-dependent, or mechanically-titled chart is a defect to fix before delivery, on the same footing as clipping or a wrong scale.

Core operating rules:

- Follow low-chartjunk, high data-ink, direct-labeling principles.
- Use light (white or near-white) backgrounds; a non-light background requires an explicit request or an established project/brand system, not a rendering default or a design hunch (see House visual defaults).
- Prefer static PNG/SVG exports unless interactivity is explicitly needed.
- Choose the identification system from the chart's density and geometry. Prefer direct labels when every important mark or series can be named legibly and unambiguously at delivery size; otherwise use a categorical axis, legend, grouping, or small multiples.
- A direct label earns its place; it is not the default for every point. Decide the editorial scope first - what deserves a label and why - and label only what carries the reading: a series' identity, an endpoint, the focal comparison the claim rests on, a genuine exception, or a value the reader must look up exactly. Points that only repeat a shape or level a labelled neighbour already shows stay in the data (table or note), not on the plot. This scope is the chart author's decision at select/build; the label tools (`recommend_labels`, `recommend_text_placement`) then pick feasible points within that scope and place them - they never widen it, add, or rewrite it. Over-labelling is the most common reason a chart reads busy and cheap rather than considered; a few chosen labels look premium, a stamped grid of values does not.
- Give each category or series one primary identification route. When a direct label carries the identity that a categorical axis or legend would carry, remove that redundant axis or legend. Apply the same drop-unless test to quantitative scaffolding: when the marks that carry the reading are directly labelled, remove the value axis, ticks, and gridlines that only repeat them - you do not need every point labelled for the axis to become redundant, only the ones the reader would otherwise read off the scale. Keep a scale, baseline, or reference line only when it performs a reading task the labels do not - estimating an unlabelled mark, alignment, a threshold, or comparing marks none of which is labelled. The default is to remove redundant scaffolding, not to keep it.
- When one removed legend served several panels, replace its lookup in every panel that uses the mapping unless an equally immediate shared labelling system makes each panel independently interpretable. Do not direct-label only the easiest panel. Enumerate the expected labels per panel before rendering.
- Use perceptual proximity to bind labels to marks. The intended label-mark relationship must be visually stronger than competing relationships with nearby labels or marks. Judge distance to the visible target, not merely to a shared row, plot edge, or baseline; alignment alone does not bridge unstructured whitespace. Use adjacency or a restrained guide. If direct labels would collide or drift away from their targets, change the label system or chart structure rather than forcing them.
- Preserve an existing semantic palette unless changing it solves a stated problem. When colour encodes a series, category, state, or direction, derive every mark, connector, direct label, annotation, and legend entry from the same mapping.
- Every encoded colour must remain perceptually distinct from the background and adjacent series at the intended display size and after compression. Replace, darken, outline, or add another channel when a light or low-contrast colour disappears.
- Use domain-specific palettes where meaningful; avoid decorative or arbitrary series colours and do not copy one chart family's colours blindly.
- Tune labels and spacing after rendering, not just from code inspection.
- Set type by hierarchy at the actual delivery size, not by a fixed point-size recipe. Direct labels and data values may lead within the plot; axis titles, ticks, sources, and notes should remain readable without competing with them or the chart title. Oversized secondary text is a hierarchy failure even when it is legible.
- Treat labels, values, marks, and annotations as relationship units. Place or connect them so the intended pairing is immediate at delivery size; mere row alignment is insufficient when large gaps or competing alignments make the association uncertain.
- Make whitespace do one of three jobs: group related elements, separate unrelated elements, or create emphasis. Inspect title-to-plot, label-to-mark, panel-to-panel, plot-to-note, and outer gaps independently; trim or restructure blank area that serves none of them.
- Check rendered text and mark bounds for collisions, clipping, and occlusion. Fix the layout, wrapping, placement, or form before reducing legible type.
- Favor visual forms that make comparison and change easy to read.
- Prefer line charts over stacked bars when the question is trend comparison rather than composition.
- Use stacked bars only for broad composition. Only segments that begin or end on an aligned baseline support precise visual comparison; fixed-total stacks align both outer edges, but internal segments still float. Direct labels support value lookup, not easy across-bar pattern comparison. If exact component comparison matters, switch to a form with aligned component baselines.
- Make visual hierarchy match information hierarchy: data, labels, annotations, grids, borders.
- Show comparison and context explicitly; a chart should answer "compared to what?"
- Use color sparingly: gray for context, color for emphasis or true encoding.
- Keep subtitles focused on the insight or comparison, not the mechanics of how the chart was made.
- Let the evidence determine whether the title states a claim, a question, a measure, or a null result. Do not manufacture a claim merely to make the chart sound decisive.
- Let complexity come from the data, not decoration.

## Optional: audited repair plan

Work output-first by default: build the chart and inspect the export, without writing a plan up front. Only when an audited repair is explicitly requested, record a short plan first, covering:

- the measure and evidence scope, including what a screenshot can support only approximately;
- the selected chart form, and the reason if the source form was rejected;
- one primary identification route for each series/category;
- the intended contents of the title, subtitle, legend, plot, annotation, and footer zones;
- colour's semantic role: identity, order, direction, emphasis, uncertainty, or none;
- one implementation requirement for every fatal and major finding, naming the affected zones and observable outcome;
- one preservation mapping for every required source item and semantic mapping, stating how it will be carried forward and what observable state proves it did not regress;
- a layout plan for the declared delivery size that names the longest text, densest regions, likely title/subtitle/legend/annotation/footer collisions, their mitigation, and the representative preview check.

Treat the plan as executable scope. In the default path, do not delay chart code for a plan. A revision continues from the latest candidate and changes the smallest relevant region; a redesign returns to the underlying evidence.

## Grouping and emphasis

The reader groups marks by perception before reading any label. Use those groupings as tools rather than fighting them:

- **Proximity and common region.** Near things, or things sharing a panel or band, read as one group. Keep related marks and their labels close; put unrelated series in separate panels or regions. (See the whitespace and label-binding rules above.)
- **Similarity.** Marks sharing a hue, shape, or weight read as the same kind. Give one meaning one encoding across the chart, and never hand unrelated series a similar encoding - a similarity the reader cannot switch off asserts a grouping that is not there.
- **Connectedness.** A line, or a label placed directly on its mark, binds two things more strongly than a shared colour the eye has to match. This is why direct labels beat a legend and a connected slope beats two coloured dots: prefer connection and adjacency to a colour lookup whenever the layout allows.
- **Enclosure.** A light band, box, or shaded region says "these belong together" or "look here" more quietly than an arrow or a heavy outline. Reach for a restrained enclosure before louder marks.
- **Figure-ground.** One focal element against muted context (the focal-colour-plus-grey rule below) works because the reader separates figure from ground before reading. Keep exactly one thing as figure; when two things compete to be seen first, neither is.

Preattentive first read: exactly one channel should make the single most important thing pop without search - a lone hue, a size, a position. When several channels shout at once, the reader searches instead of seeing. Decide this one focal element before you draw - it is the composition the chart is built around, not a highlight added at the end - and verify after rendering that it is what the eye actually lands on first (the composition gate, `dataviz-aesthetic`, owns that post-render check).

## Colour system

For the full colour-selection workflow - assigning specific hues to this graph's series from a brand or default palette, and validating them for contrast, colour-vision-deficiency, and grayscale - use `dataviz-color` (backed by the `recommend_colours` and `validate_palette` MCP tools). The rules below are the craft summary.

Colour must earn its place. Position, length, ordering, direct labels, and annotation should carry the main comparison; colour should clarify identity, order, direction, or emphasis.

- Default to neutral marks when the question and insight do not establish a focal item. Use one focal colour plus neutral grey context only when the focal item is named by the question, supported by the evidence, or explicitly requested. Never manufacture a highlight to make a chart look designed. Use several categorical hues only when several identities genuinely need equal status; when they cease to remain separable at delivery size, use grouping, direct labels, or small multiples instead of more hues.
- Match the scale to the data: qualitative hues for nominal categories, one perceptually ordered sequential scale for magnitude, and a diverging scale only around a meaningful midpoint. Do not use a rainbow scale or encode ordered values with arbitrary categories.
- Keep the same meaning in the same colour across panels and revisions. Reserve the most saturated or warm colour for the focal series, exception, or warning; equal-status series should have comparable visual weight.
- A residual or catch-all bucket (Other, Misc, Unclassified, remainder) aggregates the un-named and carries little information per unit of its size. Do not give it the focal colour or the first slot in any ordering (first bar, first panel, first labelled line) even when it is the largest category. Order by magnitude by default, but relegate residual buckets and spend emphasis, lead position, and the reader's first look on named, interpretable categories. When a residual dominates the scale, consider showing it apart from the categories that carry the story.
- For signed or directional change, define the comparison direction first, then derive every relevant mark, gap, label, and legend entry from that same sign. Follow an established audience or brief convention for hues; reinforce the direction with sign, position, wording, shape, or another non-colour channel.
- Use WCAG as a diagnostic, not a design substitute. Target at least 4.5:1 for normal chart text, 3:1 for large text, and 3:1 against the background for small or thin essential marks. Large fills may use direct labels or boundaries, but they must remain immediately distinguishable.
- Do not rely on hue alone. Pair colour with direct labels, position, shape, line style, or ordering when identity matters. Avoid red-versus-green as the only distinction; prefer colour-blind-safe starting palettes such as Okabe-Ito, ColorBrewer, or viridis when appropriate.
- Adjacent or stacked regions must differ in both hue and lightness where possible. Add a restrained boundary only when separation otherwise fails. Essential marks cannot disappear into their background; adjust luminance, boundary, or encoding when they do.
- Inspect the exact export at its delivery size, after chat compression, and in grayscale. Simulate common colour-vision deficiencies when tools are available. If the comparison disappears, revise the encoding rather than adding stronger decoration.

When writing or changing chart code:

- Preserve the renderer already used by the project. For a new Karthik-style static chart with no project precedent, prefer R/ggplot2 when it is available. This is an implementation preference, not permission to carry over `theme_gray()` or any other library default without examining the export.
- Treat rendering and inspection capabilities as mechanical infrastructure, not a style system. Do not translate a sound ggplot2 chart into Matplotlib only because one backend exposes richer metadata. If Matplotlib is the practical fallback, define typography, palette, grid, axes, labels, and spacing deliberately; default Matplotlib aesthetics fail this skill.
- Keep the visual design deliberate, not library-default.
- Check that text is legible and non-overlapping at the intended output size. Text placed over a mark is an inside label, not clear space: verify contrast and padding against the mark. Inspect the worst example in each repeated placement pattern because direction, sign, length, or panel side can change where the same labelling rule lands.
- After changing any identification, scale, or encoding element, inspect that exact relationship in the export. Confirm every required item remains identifiable and correctly bound to its marks. Any key must represent only mappings that appear in the chart and must match the relevant visual channels, not colour alone.
- Make the chart stand alone without caveats doing all the work.
- Save public chart outputs with stable, descriptive filenames when the project expects exported artifacts.
- Prefer small multiples to crowded multi-series panels when comparison across groups is the task. Lay the panels out as a grid (rows x columns) sized to the delivery medium, with the grid's proportions tracking the delivery frame's aspect ratio (wide frame: more columns than rows; tall frame: the reverse) and a panel count that keeps each panel legible at delivery size - reduce the number or move to a taller medium before shrinking panels. Not a single-column or single-row strip; a tall stack of many panels defeats the side-by-side comparison. Order panels in decreasing order of peak value or of story importance (or another meaningful key such as cluster), never input order, so the eye runs most-to-least top-left to bottom-right; when the key story is not the largest panel, give it a heavier line weight rather than moving it out of magnitude order. Mark per-panel scales when they are free.
- A shared or compressed scale buys comparability at the cost of resolution: any series sitting well below the axis maximum - a small series beneath a dominant one, a low panel in a shared-scale grid - flattens toward the baseline, so its level and change can no longer be read off the axis. When a value the reader needs cannot be resolved from the scale, recover it by putting the number on the mark - the endpoints, or the focal value - rather than leaving a flat line to be eyeballed. Reach for direct value labels before abandoning the shared scale that provides the comparison, or before adding a second scale that breaks it.
- Consider sparklines or compact tables when many series need shape plus current value.
- Consider range frames, rug marks, or labeled data points when axes or ticks can carry more information.
- Include enough source, scale, timeframe, and transformation notes for a stranger to evaluate the evidence.

Pick the renderer that fits the medium and the project. If your harness provides a backend-neutral deterministic renderer, prefer it for a static export, because it also yields the geometry metadata the inspection step reads: this repo ships one (`renderer="auto"`, which selects ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available, else a deliberately-configured Matplotlib; an explicit user requirement wins; record why Matplotlib was used whenever auto cannot use ggplot2). Where no such renderer is present, use what suits the output - a hand-authored HTML/SVG chart for a web or artifact target, a plotting library, ggplot2, or Matplotlib.

The ladder is the project's own renderer first, then a deterministic backend if the harness has one, then whatever renderer suits the medium with its typography, palette, and background set by hand. What fails this skill is the *default, unconsidered look* - a dark canvas, monospace type, raw library defaults - not the choice of renderer: a hand-authored HTML/SVG or JS chart is a legitimate rung when it is designed to the House visual defaults, and a ggplot2 or Matplotlib chart left at its theme default is not. If no available renderer can produce a chart that meets the House visual defaults, report that as a failure rather than shipping one that violates them.

When implementing in ggplot2, make `build_chart()` return either a ggplot or `list(plot = <ggplot>, metadata = <list>)`, and export through `ragg`. Read [references/ggplot2-repair-patterns.md](references/ggplot2-repair-patterns.md) for reusable sorted-bar, diverging-bar, slopegraph, direct-labelled-trend, and multi-panel implementations.
