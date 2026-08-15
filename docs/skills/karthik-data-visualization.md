# Karthik Data Visualization Skill

`karthik-data-visualization` is the styling and execution companion to `dataviz-selector`.

Use `dataviz-selector` to decide **what chart to make**. Use `karthik-data-visualization` to decide **how the chart should look**.

## What it covers

The skill encodes Karthik's preferred chart style:

- static charts by default
- high data-ink ratio
- low chartjunk
- direct labels instead of legends
- white backgrounds by default
- careful typography
- restrained gridlines
- meaningful colour
- small multiples over crowded overlays
- annotations that explain, not decorate

Direct labels are not universal. Choose them when the chart's density and geometry allow every important mark or series to be named legibly and unambiguously at delivery size; otherwise use a categorical axis, legend, grouping, or small multiples.

Give each category or series one primary identification route. When a direct label carries the identity that an axis or legend would carry, remove the redundant scaffolding. Keep quantitative scales, baselines, and references when they add information. In every system, the intended label-mark bond must be perceptually stronger than competing nearby relationships. Judge distance to the visible mark, not merely to a shared row, plot edge, or baseline; alignment alone does not bridge blank space. If direct labels would collide or drift away, change the identification system rather than forcing them.

When one removed legend served several panels, replace its lookup in every panel that uses the mapping unless one shared replacement keeps every panel immediately interpretable. Count the expected labels panel by panel; completing the easiest panel is not enough.

Colour mappings are literal and end to end. Derive marks, connectors, direct labels, annotations, and legend entries from the same semantic mapping. A legend contains only meanings present in the chart, and each key matches the plotted colour plus line, point, or fill form. For directional change, define the comparison direction once and apply its sign consistently everywhere. Use the audience's established hue convention, but retain sign, position, wording, shape, or another non-colour channel. Preserve a source palette when it already has meaning; change it only to solve a stated comparison, contrast, or accessibility problem, then verify the full mapping in the export.

Every encoded colour must remain perceptually distinct from the background, adjacent series, and its compressed delivery rendering. The broader system is restrained rather than monochrome: neutral equal-status marks unless a focal item is established, small qualitative palettes for identity, perceptually ordered scales for magnitude, and diverging scales only around a real midpoint.

WCAG ratios are used as diagnostics, not as a palette generator. The practical targets are 4.5:1 for normal chart text, 3:1 for large text, and 3:1 against the background for small or thin essential marks. Large fills can rely on direct labels and restrained boundaries when the reading remains robust. Colour never carries identity alone; labels, position, shape, line style, or ordering provide a second channel.

Stacked bars need a specific reason. Only segments beginning or ending on an aligned baseline support precise visual comparison; fixed-total stacks align both outer edges, but internal segments still float. Direct labels support lookup, not easy component-pattern comparison. If those patterns matter, use small multiples, grouped bars, lines, dots, or a table instead.

## Design principles

The basic style is Tufte-inspired, but not Tufte cosplay.

It values:

- comparison
- context
- proportional visual encoding
- sparse scaffolding
- direct labels
- charts that can stand alone in an article or deck

It rejects:

- default matplotlib aesthetics
- unnecessary legends
- heavy gridlines
- fake precision
- over-decorated infographic styling
- interactivity as a default

## Renderer preference

Preserve the renderer already established by the project. For a new Karthik-style static chart without project precedent, prefer R/ggplot2 when it is available. The preference comes from the working grammar and the way Karthik's charts are usually built; it does not mean accepting ggplot2's default theme unchanged.

The MCP renderer is infrastructure, not the visual style. Its current Matplotlib adapter exists because Matplotlib exposes reliable text and path geometry. It must not cause an agent to replace a sound ggplot2 implementation with a default-looking Matplotlib chart. When Matplotlib is the practical fallback, every visible choice—type, colour, grid, axes, labels, spacing, and annotation—must be set deliberately and checked in the exact export.

## Typical use

Use it after the chart form is decided:

```text
Make this chart in Karthik's style.
```

```text
Review this plot and make it cleaner.
```

```text
Generate ggplot code for this time-series chart.
```

```text
The selector says this should be a sorted horizontal bar chart. Now implement it.
```

## Relationship with `dataviz-selector`

A good workflow is:

1. Use `dataviz-selector` to identify the chart form and encodings.
2. Use `karthik-data-visualization` to implement the chart cleanly.
3. Inspect the rendered output.
4. Fix labels, spacing, annotations, scales, and title after seeing the export.

The last step matters. A chart is not done when the code runs. It is done when the exported image reads correctly.
