---
name: dataviz-orchestrator
description: End-to-end analytical data visualization workflow for Karthik. Use when the user points Codex to a dataset and gives a loose exploratory question, possible hypothesis, story idea, or desired audience, and wants Codex to plan the analysis, run the analysis, find the defensible story, choose the best visual representation, make chart outputs in Karthik's design aesthetic, critique the result, and iterate until the visual story is good enough to use.
---

# Dataviz Orchestrator

Own the full loop from loose question to usable visual story:

```text
dataset + loose question + audience
→ analysis contract
→ contextual data inspection/cleaning
→ analysis
→ facts table
→ story candidates
→ visual choice
→ chart implementation
→ rendered-output critique
→ iteration
→ final chart + notes
```

This skill sits above the existing analysis and dataviz skills. Load/use them at the right stage instead of duplicating their rules.

## Required companion skills

Use these skills during the workflow when available:

- `karthik-analysis-planner`: turn the loose question into measurable definitions, denominator, grain, comparison, caveats, falsifiers.
- `karthik-data-cleaning`: inspect, clean, reshape, join, and validate tabular data in context before charting.
- `r-analysis-rules`: for R/tidyverse analysis code, notebooks, and pipelines.
- `dataviz-selector`: choose chart form, encodings, context layers, and what to avoid.
- `karthik-data-visualization`: apply Karthik's visual style and render-inspect-adjust loop.
- `chart-annotations`: choose what the chart marks, rank competing candidates, word the label, and place it.
- `dataviz-critique`: critique the rendered chart, not just the code, and propose fixes.
- `babbage-visual-style`: only when making Babbage-branded visuals.
- `karthik-powerpoint-style`: only when the final artifact is a slide/deck.

## Operating defaults

- Do not ask for clarification unless the dataset/question/audience is impossible to infer. Make reasonable assumptions and state them.
- Prefer doing the analysis over writing a plan. The plan is a guardrail, not the output.
- Never let prose outrun computed evidence. Make a compact facts table before writing the claim.
- If the data cannot answer the question, say so and pivot to the closest defensible question.
- Prefer one strong interpreted visual over a dashboard.
- Keep outputs reproducible: leave analysis/chart code in a sensible project file unless the user asks for a one-off.
- Render charts and inspect the actual output image before calling the work done.
- Make the narrowest repo change needed. Do not regenerate unrelated artifacts.

## Workflow

### 1. Intake and repo orientation

Identify:

- dataset path(s), format, source, and size;
- user's loose question or suspected pattern;
- intended audience and medium: notebook, blog, slide, social post, internal memo, or exploratory scratch;
- existing repo conventions: language, filenames, output folders, chart style, themes, and prior examples.

If the user gives no audience, assume: “Karthik exploring first, then possibly public-facing if the story is strong.”

### 2. Create a lightweight analysis contract

Use `karthik-analysis-planner`, but keep it compact unless the user asks for a full contract.

Must decide before coding:

- unit of analysis;
- denominator and numerator;
- key metric(s);
- primary comparison/baseline;
- filters/exclusions;
- sanity checks;
- what would weaken or falsify the likely story.

### 3. Inspect and clean the data

Use `karthik-data-cleaning`. Run quick data checks before analysis:

- schema, row count, key columns, types;
- date/time coverage and timezone where relevant;
- missingness and duplicates;
- grain check: one row per what?;
- category cardinality and small-n groups;
- outliers/extreme values;
- whether the dataset contains the fields needed for the intended question.

Clean only what the analysis needs. Make every non-trivial rule visible: type conversions, filters, recodes, joins, reshape steps, impossible-value handling, and missingness decisions. Preserve raw/canonical files; do not create working files unless repeated parsing is genuinely costly.

Validate after cleaning:

- raw rows vs analysis rows;
- key uniqueness at the chosen grain;
- denominator sanity;
- join mismatches or dropped records that affect the answer.

Save or print only the useful profile/cleaning summary. Avoid noisy dumps.

### 4. Analyse before charting

Build the smallest analysis table that can answer the question. Compute:

- main metric at chosen grain;
- denominator/sample-size columns;
- relevant baselines or comparison groups;
- sensitivity checks when definitions are fuzzy;
- a compact facts table with the numbers that would appear in title/annotations.

For exploratory work, try 2-4 plausible cuts, then choose. Do not produce a gallery unless the user explicitly asks.

### 5. Find the story

From the facts, write 2-3 candidate claims:

- **Main claim**: strongest defensible point.
- **Alternative lens**: a different useful comparison if the first claim is weak.
- **Caveated claim**: what can be said safely if data quality or causality is limited.

Pick one main claim for the first chart. If no claim survives, show the diagnostic result instead.

### 6. Select the visual

Use `dataviz-selector`.

Specify:

- recommended chart form;
- x/y/colour/facet/label encodings;
- ordering and scale choices;
- context layers: benchmark, event line, counterfactual, uncertainty, knee-bend, local maximum/minimum, annotation;
- what not to use and why.

Default to simple static visuals: line, sorted bars, scatter, small multiples, distribution, compact table/sparkline, or map only when spatial pattern matters.

### 7. Implement in Karthik's style

Use `karthik-data-visualization` and repo conventions. Use `chart-annotations` to decide what the chart marks and how the label reads: the title states the claim, the annotation locates it on the evidence. Cap the chart at one primary annotation plus at most two supporting ones.

Defaults:

- chart-first, low decoration, high data-ink;
- claim-first title;
- direct labels over legends;
- grey for context, colour for story emphasis;
- source/timeframe/definition note where needed;
- no decorative palettes, 3D, pies, donuts, gauges, radar charts, or dashboard clutter;
- stable descriptive output filename.

If using R, follow `r-analysis-rules`: tidyverse-first, `%>%`, concise notebooks/scripts, no noisy status chatter.

### 8. Render, inspect, critique, iterate

Render the chart to PNG/SVG/PDF as appropriate. Inspect the actual exported image.

Use `dataviz-critique` on the rendered output:

- Does the question-data-visual triangle hold?
- Is the main claim visible in 3 seconds?
- Are denominators, units, source, and timeframe clear?
- Are labels legible and non-overlapping?
- Does every colour/annotation earn its place?
- Is any conclusion overstated?

Iterate until fatal and major issues are fixed. Usually do 1-3 passes; stop when remaining issues are minor or require a different dataset/question.

### 9. Final response

Keep the final response short. Include:

- what artifact(s) changed/created;
- the final defensible story in one sentence;
- key caveat(s);
- path to output chart and code/notebook;
- any next chart worth doing, only if useful.

## Output package

For a completed run, aim to leave behind:

- analysis/chart code or notebook;
- exported chart file;
- compact facts table, either in code output, CSV, or notebook cell;
- short note with the claim, definitions, caveats, and source.

Do less if the user asked for quick exploration; do more only if they asked for publication/deck-ready output.

## Failure handling

- **Dataset missing or unreadable**: report the exact path/error and the next command/user action needed.
- **Question not answerable**: show which required field/comparison is missing and propose a nearby answerable question.
- **Weak/no story**: provide the negative finding or diagnostic visual rather than forcing a story.
- **Crowded visual**: split into small multiples, rank to top-N with context, or switch to table/sparkline.
- **Causality gap**: rename “effect” to “association/difference” unless there is a defensible design.
