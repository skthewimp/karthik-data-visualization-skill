---
name: karthik-data-visualization
description: Create or review charts, dashboards, and data visualizations in Karthik's style. Use for plots, labels, palettes, annotations, and visual analysis.
---

# Karthik Data Visualization

Use this skill for any chart, graph, dashboard, or data visualization work, including chart-generating code, visual analysis pages, annotations, captions, labels, palettes, and chart review.

Apply the workflow below before finalizing design decisions or chart code. Private local references may add nuance, but this public skill is self-contained.

Workflow:

1. Clarify the analytical job: what comparison matters, what the viewer should learn, and what evidence supports it.
2. Choose the structure: line/point for time, range plot for intervals, small multiples for category comparison, table/sparkline for dense metric scans, bar/table for part-to-whole.
3. Build from data outward: data first, direct labels second, annotations third, grids/axes last.
4. Check graphical integrity: scales, baselines, proportional encoding, missing context, and any visual effect that exaggerates or understates the data effect.
5. Apply the eraser test: remove any ink that does not carry data, labels, or necessary context.
6. Render and inspect the exported image; if anything is clipped, overlapping, or misaligned, adjust labels, spacing, hierarchy, and source notes from the actual output, then render again.

Core operating rules:

- Follow low-chartjunk, high data-ink, direct-labeling principles.
- Use white backgrounds by default; reserve warm beige only for Bangalore weather lineage or explicit continuation of that family.
- Prefer static PNG/SVG exports unless interactivity is explicitly needed.
- Choose the identification system from the chart's density and geometry. Prefer direct labels when every important mark or series can be named legibly and unambiguously at delivery size; otherwise use a categorical axis, legend, grouping, or small multiples.
- Give each category or series one primary identification route. When a direct label carries the identity that a categorical axis or legend would carry, remove that redundant axis or legend. Keep quantitative scales, baselines, and references only when they add information the direct labels do not.
- When one removed legend served several panels, replace its lookup in every panel that uses the mapping unless an equally immediate shared labelling system makes each panel independently interpretable. Do not direct-label only the easiest panel. Enumerate the expected labels per panel before rendering.
- Use perceptual proximity to bind labels to marks. The intended label-mark relationship must be visually stronger than competing relationships with nearby labels or marks. Judge distance to the visible target, not merely to a shared row, plot edge, or baseline; alignment alone does not bridge unstructured whitespace. Use adjacency or a restrained guide. If direct labels would collide or drift away from their targets, change the label system or chart structure rather than forcing them.
- Preserve an existing semantic palette unless changing it solves a stated problem. When colour encodes a series, category, state, or direction, derive every mark, connector, direct label, annotation, and legend entry from the same mapping.
- Every encoded colour must remain perceptually distinct from the background and adjacent series at the intended display size and after compression. Replace, darken, outline, or add another channel when a light or low-contrast colour disappears.
- Use domain-specific palettes where meaningful; avoid decorative or arbitrary series colours and do not copy one chart family's colours blindly.
- Tune labels and spacing after rendering, not just from code inspection.
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
- Let complexity come from the data, not decoration.

## Colour system

Colour must earn its place. Position, length, ordering, direct labels, and annotation should carry the main comparison; colour should clarify identity, order, direction, or emphasis.

- Default to neutral marks when the question and insight do not establish a focal item. Use one focal colour plus neutral grey context only when the focal item is named by the question, supported by the evidence, or explicitly requested. Never manufacture a highlight to make a chart look designed. Use several categorical hues only when several identities genuinely need equal status; when they cease to remain separable at delivery size, use grouping, direct labels, or small multiples instead of more hues.
- Match the scale to the data: qualitative hues for nominal categories, one perceptually ordered sequential scale for magnitude, and a diverging scale only around a meaningful midpoint. Do not use a rainbow scale or encode ordered values with arbitrary categories.
- Keep the same meaning in the same colour across panels and revisions. Reserve the most saturated or warm colour for the focal series, exception, or warning; equal-status series should have comparable visual weight.
- For signed or directional change, define the comparison direction first, then derive every relevant mark, gap, label, and legend entry from that same sign. Follow an established audience or brief convention for hues; reinforce the direction with sign, position, wording, shape, or another non-colour channel.
- Use WCAG as a diagnostic, not a design substitute. Target at least 4.5:1 for normal chart text, 3:1 for large text, and 3:1 against the background for small or thin essential marks. Large fills may use direct labels or boundaries, but they must remain immediately distinguishable.
- Do not rely on hue alone. Pair colour with direct labels, position, shape, line style, or ordering when identity matters. Avoid red-versus-green as the only distinction; prefer colour-blind-safe starting palettes such as Okabe-Ito, ColorBrewer, or viridis when appropriate.
- Adjacent or stacked regions must differ in both hue and lightness where possible. Add a restrained boundary only when separation otherwise fails. Essential marks cannot disappear into their background; adjust luminance, boundary, or encoding when they do.
- Inspect the exact export at its delivery size, after chat compression, and in grayscale. Simulate common colour-vision deficiencies when tools are available. If the comparison disappears, revise the encoding rather than adding stronger decoration.

When writing or changing chart code:

- Keep the visual design deliberate, not library-default.
- Check that text is legible and non-overlapping at the intended output size. Text placed over a mark is an inside label, not clear space: verify contrast and padding against the mark. Inspect the worst example in each repeated placement pattern because direction, sign, length, or panel side can change where the same labelling rule lands.
- After changing an axis label, legend, or colour, inspect that exact element in the export. Confirm every required category remains identifiable and correctly bound to its marks. A legend may contain only mappings that appear in the chart, and each key must match the plotted colour plus its relevant line, point, or fill form—not colour alone.
- Make the chart stand alone without caveats doing all the work.
- Save public chart outputs with stable, descriptive filenames when the project expects exported artifacts.
- Prefer small multiples to crowded multi-series panels when comparison across groups is the task.
- Consider sparklines or compact tables when many series need shape plus current value.
- Consider range frames, rug marks, or labeled data points when axes or ticks can carry more information.
- Include enough source, scale, timeframe, and transformation notes for a stranger to evaluate the evidence.
