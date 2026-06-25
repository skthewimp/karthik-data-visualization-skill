# Dataviz Critique

Use `dataviz-critique` when reviewing an existing chart, dashboard, slide visual, infographic, or AI-generated plot and asking:

- What does this visual seem to say?
- Does the data support that message?
- What is misleading, unclear, or under-specified?
- What should be fixed first?
- What alternative visualizations would tell the story better?

This is the repository's **review and redesign** skill. It is not just a style checker.

## How it fits with the other skills

- Use **`dataviz-selector`** before making a chart, when choosing the right visual form for a dataset and question.
- Use **`karthik-data-visualization`** when styling or implementing a chosen chart.
- Use **`dataviz-critique`** after a chart exists, when diagnosing whether it works and proposing better alternatives.
- Use **`karthik-powerpoint-style`** when the chart is part of an analytical slide or deck.

## Core diagnostic frame

The skill uses Kaiser Fung's **Question–Data–Visual** trifecta:

1. **Question** — What is the visual trying to answer? Is that question clear, useful, and singular enough?
2. **Data** — Does the data actually answer the question? Are the grain, units, denominator, baseline, source, transformations, and uncertainty appropriate?
3. **Visual** — Does the encoding reveal the answer clearly? Are chart type, scale, ordering, colour, labels, title, annotation, and hierarchy doing useful work?

It also checks the pairwise mismatches:

- **Question ↔ Data**: wrong metric, proxy, denominator, time window, or unit.
- **Data ↔ Visual**: distorted magnitude, rank, distribution, uncertainty, or comparison.
- **Visual ↔ Question**: a chart that visually answers a different question from the one intended.

## Karthik lens

The skill applies Karthik's stricter visualization standards:

- **Clarity first** — a visual must stand alone. Missing axes, unclear units, ambiguous chart types, unexplained shading, and mystery colours are serious failures.
- **Intentional design** — every colour, shade, line, label, sort order, and annotation must earn its place.
- **Fundamentals before polish** — check denominators, dimensions, sample sizes, uncertainty, and whether the comparison is meaningful before talking about aesthetics.
- **Narrative with evidence** — a chart should communicate a defensible point, not merely display numbers.
- **No tool worship** — do not excuse dashboard clutter, BI defaults, or AI-generated prettiness if the visual is hard to interpret.
- **Repeatable fixes** — prefer fixes that survive new data and reruns, not one-off cosmetic hacks.

## Expected inputs

The skill should work even with partial context, but better inputs produce better critique:

- the chart image, code output, screenshot, or chart description;
- the intended message or decision;
- the dataset fields, grain, units, time period, and source;
- the audience and medium;
- any constraints, such as slide space, print format, brand palette, or dashboard tool.

If context is missing, the skill should state assumptions and identify the exact checks needed.

## Output contract

A full critique should contain:

1. **Quick read** — what the visual is, what it seems to say, and a verdict.
2. **Trifecta checkup** — question, data, visual, and the main mismatch.
3. **Issues to fix** — prioritized by severity:
   - **Fatal**: changes the conclusion or makes the chart uninterpretable.
   - **Major**: materially slows or misleads interpretation.
   - **Minor**: readability or polish.
4. **Recommended alternatives** — two or three redesign options when useful.
5. **Implementation notes** — title, annotation, caveats, and checks.

For quick requests, the skill can compress this to verdict, top three fixes, and two redesign alternatives.

## Redesign alternatives

The redesign section is the main extension beyond ordinary critique. The skill should not list random chart types. Each alternative must correspond to a different analytical purpose, audience need, or intervention level.

Default alternatives:

### Option A — Minimal repair

Keep the current chart form if it is basically defensible. Fix execution:

- title and subtitle;
- axis labels and units;
- scale and baseline;
- ordering;
- colour meaning and accessibility;
- direct labels instead of legends;
- annotation and caveats.

Use when the chart type is right but the execution is weak.

### Option B — Better analytical redesign

Change the visual form to answer the stated question more clearly.

Examples:

- pie or donut → sorted horizontal bars;
- spaghetti lines → small multiples or highlighted focal series;
- stacked bars for small differences → grouped bars, dot plot, or slopegraph;
- map used for ranking → ranked bars, with map only as spatial context;
- dashboard metric grid → one interpreted chart plus concise scorecard.

Use when the current encoding is wrong for the comparison.

### Option C — Different story lens

Reframe the analysis when the original question is weak, incomplete, or less useful than another defensible view.

Common reframes:

- totals → rates or per-capita values;
- averages → distributions;
- snapshot → trend;
- levels → change;
- ranking → decomposition;
- category comparison → cohort or segment comparison;
- geography → comparison first, map second;
- dashboard → action-oriented narrative.

Use when a different question would reveal the real story better.

## Example output skeleton

```markdown
## Quick read
- What it is: ...
- What it seems to say: ...
- Verdict: partly works, but ...

## Trifecta checkup
- Question: ...
- Data: ...
- Visual: ...
- Main mismatch: ...

## Issues to fix
1. **Fatal** — ... Fix: ...
2. **Major** — ... Fix: ...
3. **Minor** — ... Fix: ...

## Recommended alternatives

### Option A — Minimal repair
- Best when: ...
- Chart: ...
- Encoding: ...
- What it fixes: ...
- Tradeoff: ...

### Option B — Better analytical redesign
- Best when: ...
- Chart: ...
- Encoding: ...
- What it fixes/reveals: ...
- Tradeoff: ...

### Option C — Different story lens
- Best when: ...
- Chart: ...
- Encoding: ...
- What it reveals: ...
- Tradeoff: ...
```

## What good output should feel like

Good critique is direct and useful. It should not say "nice chart" by default. It should identify what a viewer would misunderstand, explain why that matters, and offer practical redesign choices with tradeoffs.
