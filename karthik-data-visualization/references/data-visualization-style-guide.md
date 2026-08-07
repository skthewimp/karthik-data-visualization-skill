# Karthik Data Visualization Style Guide

## Core Principle

Karthik's chart style is Tufte's principles, not Tufte's colors.

The constant is low-chartjunk minimalism, direct labeling, high data-ink ratio, and
careful typography. The variable is color: palettes should be chosen per project, not
copied blindly from one chart family.

The canonical implementation is R/ggplot2 with `theme_minimal()` or
`ggthemes::theme_tufte()`. Other languages should reproduce that aesthetic. Never let
default matplotlib styling leak through.

## Non-Negotiables

- Always static: PNG or SVG.
- Never interactive unless explicitly requested: no Plotly, D3, Bokeh, hover, zoom, or
  tooltips.
- No legends. Direct-label every series.
- White background by default.
- Warm beige `#e5e1d8` only for Bangalore weather charts or charts explicitly continuing
  that family.
- Use charcoal `#3C3C3C` text, not pure black.
- Remove top/right spines.
- Remove all gridlines by default.
- Use clean sans fonts: Helvetica Neue, Helvetica, Arial.
- Reorder facets by a meaningful metric, never alphabetically.
- Inspect final exported image and adjust labels manually if needed.

## Background

Default:
- White background.
- No panel border.
- No decorative rectangle.

Bangalore weather family only:
- Background: `#e5e1d8`
- Primary/focal: `#490000`
- Historical bands: `#d4cbaa`
- Baseline/normal: `#888888`
- Accent: `#005566`, `#5f3946`, or `firebrick3`

Do not generalize the beige background to unrelated projects.

## Color

There is no single canonical palette. Pick color deliberately for the project.

Use:

- Categorical, few series: ColorBrewer `Set1`, `Set2`, or `Dark2`.
- Diverging: ColorBrewer `RdBu`, anchored at zero.
- Sequential or ordered: `viridis`, especially mako/magma-like options for heatmaps.
- Single focal series: one strong color for the focal data, neutral grey for baselines/
  context.
- Domain-specific palettes when meaningful: weather, wind direction, cricket teams,
  political parties, etc.

Text:
- Main text: `#3C3C3C`
- Muted text: `#666666`
- Baselines/context: `grey50`, `#888888`
- Record/outlier annotation: one bright accent, e.g. `firebrick3` / `#CD3333`

Avoid:
- Raw matplotlib default colors.
- Pure black text.
- Too many saturated colors.
- Color without semantic purpose.

## Typography

Use sans fonts:
- Helvetica Neue
- Helvetica
- Arial
- DejaVu Sans only as fallback

Rules:
- Title: bold, charcoal.
- Subtitle: regular, smaller, muted or accent color. Make it carry the analytical message, benchmark, or surprise; do not waste it explaining chart mechanics that labels/annotations can handle. Keep it insight-first, not process-first.
- Axis text: bold, charcoal.
- Facet labels: bold.
- Caption/source: small, regular, charcoal or grey.
- Annotation text: usually bold in R, readable at final export size.
- No italics.

Typical sizing:
- Base size: 11pt.
- Axis text: 8-11pt depending on output.
- Annotation text in ggplot: `size = 2.5-3`.

## Gridlines

Default: remove all gridlines.

Add back only when the chart is genuinely harder to read without them:
- Horizontal major gridlines only.
- Color: `grey90` or `grey92`.
- Linewidth: `0.3`.
- No vertical gridlines.
- No minor gridlines.

For long time series, thin month-boundary vertical lines can be used if they encode time
structure, but they should not look like default gridlines.

## Axes

- Drop axis titles when redundant.
- Dates usually do not need an x-axis title.
- Obvious categories do not need an axis title.
- Use thin axis lines: `linewidth = 0.2-0.3`.
- Remove top and right spines.
- Drop tick marks when labels suffice.
- Use few ticks.
- Format numbers humanly: SI labels, percentages, currency, commas.
- Never show raw `1e+05`.

For subjective or illustrative values:
- Drop tick numbers entirely.
- If the exact scale is fake precision, the relative position is the message.

## Legends

No legends. Ever.

Use direct labels:
- Prefer direct labels over legends whenever the labels can fit cleanly on the chart.
- End-of-line labels for line charts.
- `geom_text()` / `annotate()` for small static labels.
- `ggrepel::geom_text_repel()` for collision-prone labels.
- Inline visual keys made with annotated segments and text are acceptable.

If a legend feels necessary, rethink the chart:
- Fewer series.
- Facet it.
- Label only focal lines.
- Use end-of-line labels.
- Split into small multiples.

Legends force eye ping-pong and usually signal lazy chart construction.

## Annotations

Annotations should clarify, not decorate.

Use them for:
- Peaks.
- Breaks.
- Records.
- Regime changes.
- Important outliers.
- Final values in multi-series time charts.

Rules:
- Annotation density should be conservative.
- Do not label every point.
- Labels must be legible at final export size.
- No overlaps between labels, leader lines, or data.
- Wrap long labels.
- Tune labels after rendering the chart.

In R:
- Use `ggrepel::geom_text_repel()`.
- Tune `force`, `box.padding`, `max.iter`, and `nudge_x/y`.

In Python:
- Use `adjustText.adjust_text(..., ensure_inside_axes=True)`.

If labels overflow:
- Increase figure size first.
- Then tune label positions.
- Do not simply shrink text until unreadable.

## Faceting

Small multiples are strongly preferred over crowded multi-series panels.

Rules:
- Use `facet_wrap()` heavily.
- Reorder facets by a meaningful metric.
- Never leave facets alphabetical unless alphabetical order is the point.
- Use `scales = "free"` or `scales = "free_y"` when magnitudes differ materially.
- Keep facet labels bold and readable.

## Chart Type Preferences

Preferred, roughly in order:

1. Line + point for time series and trend comparison.
2. Segment/range plots for bands, especially current vs historical range.
3. Small multiples for cross-category comparison.
4. Horizontal bar charts for ranked categories.
5. Heatmaps/tiles with viridis for matrices.
6. Ribbon/area charts for uncertainty or cumulative ranges.
7. Scatter + smooth for relationships.
8. Ridgelines for distributions across groups.

Avoid:
- Pie charts.
- Donut charts.
- 3D charts.
- Radar/spider charts.
- Stacked bars when comparison matters, especially when the viewer needs to compare trends over time.
- Interactive charts by default.

## Composition

Default single-panel export:
- Width: 12
- Height: 6
- For chat delivery, scale up rather than squeeze; larger canvases and larger labels survive compression better.

Use:

```r
ggsave(filename, plot, width = 12, height = 6)
```

For multi-panel charts:

- Use patchwork.
- Use `plot_layout()` for panel layout.
- Use `plot_annotation()` for shared title, subtitle, and caption.

Margins:

- Use generous margins.
- Do not crowd the edges.
- Default: `plot.margin = margin(15, 15, 15, 15)`.

## R ggplot Template

```r
library(ggplot2)
library(ggthemes)
library(patchwork)
library(ggrepel)
library(scales)

ggplot(data, aes(x = x_var, y = y_var)) +
  geom_line(color = "#3366cc", linewidth = 0.8) +
  geom_point(color = "#3366cc") +
  geom_text_repel(
    aes(label = label),
    size = 2.8,
    fontface = "bold",
    col = "#3C3C3C"
  ) +
  scale_y_continuous("", labels = label_number_si()) +
  scale_x_date("", date_labels = "%b") +
  theme_minimal(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(color = "grey92", linewidth = 0.3),
    axis.text = element_text(face = "bold", color = "#3C3C3C"),
    axis.line.x = element_line(colour = "grey30", linewidth = 0.2),
    axis.ticks = element_blank(),
    legend.position = "none",
    plot.title = element_text(face = "bold", color = "#3C3C3C"),
    plot.subtitle = element_text(color = "#666666"),
    plot.caption = element_text(color = "#666666"),
    plot.margin = margin(15, 15, 15, 15)
  ) +
  labs(
    title = "Clear Title",
    subtitle = "Key insight in one line",
    caption = "Source"
  )
```

Pick the focal color per project. Use ColorBrewer or viridis scales for multi-series or
ordered data.

## R Bangalore Weather Template

Use only for the Bangalore weather family.

```r
ggthemes::theme_tufte(base_size = 11) +
  theme(
    panel.background = element_rect(fill = "#e5e1d8", linewidth = 0),
    plot.background = element_rect(fill = "#e5e1d8", linewidth = 0),
    panel.grid = element_blank(),
    axis.text = element_text(face = "bold", color = "#3C3C3C"),
    axis.ticks = element_blank(),
    legend.position = "none",
    plot.title = element_text(face = "bold", color = "#3C3C3C"),
    plot.subtitle = element_text(color = "#5f3946"),
    plot.margin = margin(15, 15, 15, 15)
  )
```

Palette:

- Background: `#e5e1d8`
- Primary/current: `#490000`
- Historical bands: `#d4cbaa`
- Normal/baseline: `#888888`
- Teal accent: `#005566`
- Muted maroon: `#5f3946`
- Text: `#3C3C3C`

## Python Preference

Prefer plotnine when possible because it maps naturally to ggplot.

Use matplotlib only when needed, and explicitly override defaults.

## Python plotnine Template

```python
from plotnine import *

theme_karthik = (
    theme_minimal(base_size=11) +
    theme(
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="grey92", size=0.3),
        axis_text=element_text(weight="bold", color="#3C3C3C"),
        axis_ticks=element_blank(),
        legend_position="none",
        plot_title=element_text(weight="bold", color="#3C3C3C"),
        plot_subtitle=element_text(color="#666666"),
    )
)
```

## Python matplotlib Template

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = [
    "Helvetica Neue",
    "Helvetica",
    "Arial",
    "DejaVu Sans",
]
mpl.rcParams["font.size"] = 10

fig, ax = plt.subplots(figsize=(12, 6))

fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.spines["left"].set_linewidth(0.3)
ax.spines["bottom"].set_linewidth(0.3)
ax.spines["left"].set_color("#3C3C3C")
ax.spines["bottom"].set_color("#3C3C3C")

ax.tick_params(colors="#3C3C3C", labelsize=9, length=0)

for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontweight("bold")

ax.grid(False)

ax.set_title(
    "Clear Title",
    fontweight="bold",
    color="#3C3C3C",
    loc="left",
)

# No legends. Direct-label every series with ax.text / annotate / adjustText.

plt.savefig(
    "output.png",
    dpi=150,
    facecolor="white",
    bbox_inches="tight",
)
```

## Tufte-Inspired Analytical Rules

This style follows Tufte's principles, not Tufte's exact palette.

Graphical excellence:
- Show the data, not the software or the designer's technique.
- Make comparison easy. A chart should answer "compared to what?"
- Show both overview and useful local detail when the data supports it.
- Integrate words, numbers, and visuals near the evidence they explain.
- Let complexity come from the data, not decoration.

Graphical integrity:
- Keep visual effect proportional to data effect.
- Use consistent scales, intervals, units, and baselines.
- Do not encode a linear value with area, volume, 3D depth, or decoration.
- Include enough source, timeframe, denominator, scale, and transformation notes for a stranger to evaluate the evidence.
- Avoid charts that show design variation more strongly than data variation.

Data-ink and chartjunk:
- Maximize useful data-ink.
- Remove non-data ink and redundant data ink.
- Remove boxes, heavy grids, decorative gradients, shadows, icons, hatching, and other effects that do not encode data.
- Use the eraser test: if an element can disappear without losing data, labels, or necessary context, remove it.

High-density design:
- Dense is good when the display remains readable.
- Prefer small multiples to animation or crowded multi-series panels.
- Consider sparklines or compact chart-tables when many metrics need trend shape plus current value.
- Use micro/macro design: the chart should reward both a glance and a close read.
- Use layering and separation: primary data strongest, context quiet, scaffolding faint.

Multifunctioning elements:
- Prefer elements that do more than one job.
- Direct labels can replace legends and identify data.
- Range frames can make axes show observed extent.
- Rug marks can turn an axis into a distribution summary.
- Meaningful reference lines should encode thresholds, baselines, or policy targets, not just decoration.

Sparklines:
- Use for word-sized trends in tables, dashboards, and prose.
- Remove axes, grids, and decoration.
- Mark only current, min, max, or meaningful anomalies.
- Pair the sparkline with a precise number nearby.
- Do not use sparklines when precise point reading or part-to-whole comparison is the task.

Where Karthik diverges from strict Tufte:

- Uses color freely.
- Bolds axis text.
- Uses larger fonts than Tufte micro-chart defaults.
- Uses modern ggplot-style composition.

These are deliberate choices.

## Common Mistakes And Fixes

| Mistake | Fix |
|---|---|
| Using beige for every chart | Use white by default. Beige only for Bangalore weather lineage. |
| Using default matplotlib | Override fonts, colors, spines, grid, and background. |
| Using pure black | Use `#3C3C3C`. |
| Adding a legend | Direct-label or rethink the chart. |
| Keeping gridlines everywhere | Remove all; add subtle horizontal major only if needed. |
| Alphabetical facets | Reorder by a meaningful metric. |
| Thick axis lines | Use `linewidth = 0.2-0.3` or remove. |
| Showing fake-precision tick labels | Drop ticks or simplify labels. |
| Exaggerating change with scale tricks | Fix the scale, baseline, or annotation context. |
| Using 3D, area, or volume for linear values | Use position or length. |
| Showing pattern without comparison | Add baseline, prior period, target, peer group, or normal range. |
| Too many annotations | Label only meaningful points. |
| Overlapping labels | Use ggrepel/adjustText and manually inspect. |
| Shrinking text to fit | Increase figure size first. |
| Making charts interactive | Export static PNG/SVG. |
| Using stacked bars for comparison | Use facets, lines, or horizontal bars. |

## Final Checklist

Before considering a chart done:

- Is it static?
- Is the background white unless it is a Bangalore weather chart?
- Are top/right spines removed?
- Are gridlines removed or minimal?
- Is text charcoal, not black?
- Are fonts sans and non-default-looking?
- Are axis labels/titles removed where redundant?
- Are numbers formatted humanly?
- Is every series directly labeled?
- Are there zero legends?
- Does the chart answer "compared to what?"
- Is the visual effect proportional to the data effect?
- Are scales, baselines, units, timeframes, and transformations clear?
- Are annotations selective and legible?
- Are labels non-overlapping in the exported image?
- Are facets ordered meaningfully?
- Is color doing semantic work?
- Are primary data, context, labels, and scaffolding properly layered?
- Would the chart still work at a glance and on a close read?
- Does the chart look like ggplot/Tufte, not default matplotlib?
