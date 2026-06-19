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
