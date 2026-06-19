---
name: karthik-data-visualization
description: Create or review charts, dashboards, and data visualizations in Karthik's style. Use for plots, labels, palettes, annotations, and visual analysis.
---

# Karthik Data Visualization

Use this skill for any chart, graph, dashboard, or data visualization work, including chart-generating code, visual analysis pages, annotations, captions, labels, palettes, and chart review.

Before finalizing design decisions or chart code, read `references/data-visualization-style-guide.md` and apply it directly. It is the single source of truth for this skill.

For quick chart edits, apply the workflow below without loading every reference.

Workflow:

1. Clarify the analytical job: what comparison matters, what the viewer should learn, and what evidence supports it.
2. Choose the structure: line/point for time, range plot for intervals, small multiples for category comparison, table/sparkline for dense metric scans, bar/table for part-to-whole.
3. Build from data outward: data first, direct labels second, annotations third, grids/axes last.
4. Check graphical integrity: scales, baselines, proportional encoding, missing context, and any visual effect that exaggerates or understates the data effect.
5. Apply the eraser test: remove any ink that does not carry data, labels, or necessary context.
6. Render and inspect the exported image; adjust labels, spacing, hierarchy, and source notes from the actual output.

Core operating rules:

- Follow low-chartjunk, high data-ink, direct-labeling principles.
- Use white backgrounds by default; reserve warm beige only for Bangalore weather lineage or explicit continuation of that family.
- Prefer static PNG/SVG exports unless interactivity is explicitly needed.
- Label data directly when possible instead of relying on legends.
- Use domain-specific palettes where meaningful; avoid copying one chart family's colors blindly.
- Tune labels and spacing after rendering, not just from code inspection.
- Favor visual forms that make comparison and change easy to read.
- Make visual hierarchy match information hierarchy: data, labels, annotations, grids, borders.
- Show comparison and context explicitly; a chart should answer "compared to what?"
- Use color sparingly: gray for context, color for emphasis or true encoding.
- Let complexity come from the data, not decoration.

When writing or changing chart code:

- Keep the visual design deliberate, not library-default.
- Check that text is legible and non-overlapping at the intended output size.
- Make the chart stand alone without caveats doing all the work.
- Save public chart outputs with stable, descriptive filenames when the project expects exported artifacts.
- Prefer small multiples to crowded multi-series panels when comparison across groups is the task.
- Consider sparklines or compact tables when many series need shape plus current value.
- Consider range frames, rug marks, or labeled data points when axes or ticks can carry more information.
- Include enough source, scale, timeframe, and transformation notes for a stranger to evaluate the evidence.

Reference:

- `references/data-visualization-style-guide.md`
