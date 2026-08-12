---
name: dataviz-orchestrator
description: End-to-end analytical data visualization workflow for Karthik. Use when the user points Codex to a dataset and gives a loose exploratory question, possible hypothesis, story idea, or desired audience, and wants Codex to plan the analysis, run the analysis, find the defensible story, choose the best visual representation, make chart outputs in Karthik's design aesthetic, critique the result, and iterate until the visual story is good enough to use.
metadata:
  claude-description: "Orchestrate dataset-to-visual-story work: plan analysis, run it, choose visuals, style, critique, and iterate."
---

# Dataviz Orchestrator

Own sequencing and hand-offs from dataset to usable visual story. Do not duplicate the rules of companion skills.

```text
dataset + question + audience
→ contract
→ prepared evidence
→ facts and candidate claims
→ selected visual
→ rendered artifact
→ critique or release evaluation
→ final package
```

## Skill ownership

Invoke only the stages the task needs:

- `dataset-question-generator` discovers candidate questions when the user has data but no useful question.
- `karthik-analysis-planner` defines the chosen question, grain, denominator, metric, comparison, caveats, and falsifiers.
- `karthik-data-cleaning` owns profiling, parsing, reshaping, joins, recodes, missingness decisions, and validation.
- `karthik-r-analysis-style` owns R notebook structure, code texture, and exploratory branching.
- `dataviz-selector` owns chart-form and encoding choice.
- `karthik-data-visualization` owns visual implementation and rendered-output inspection.
- `chart-annotations` owns what to mark, annotation wording, and placement.
- `chart-explainer` owns the short note beside a finished chart or table.
- `dataviz-critique` owns broad diagnosis and alternative interventions.
- `dataviz-eval` owns formal artifact release and creator-system benchmarks.
- `karthik-powerpoint-style` owns slide composition when the deliverable is a deck.
- `babbage-visual-style` owns Babbage branding when explicitly applicable.

Use `dataviz-fix`, not this skill, when the primary job is repairing an uploaded chart through a persistent feedback loop.

## Workflow

### 1. Orient

Identify the dataset, live question or hypothesis, audience, medium, and local project conventions. Infer non-critical context rather than blocking; state material assumptions.

If no useful question exists, call `dataset-question-generator`. Otherwise continue with the supplied question.

### 2. Contract

Call `karthik-analysis-planner`. Do not restate its contract fields here. Stop or reframe when the available data cannot support the question.

### 3. Prepare and analyse

Call `karthik-data-cleaning` for any data preparation. Use `karthik-r-analysis-style` when working in R or an exploratory RMarkdown/Quarto notebook.

Build the smallest analysis table that answers the contract. Produce a compact facts table before writing a claim. Keep computed evidence, uncertainty, caveats, and sensitivity results attached to the facts they qualify.

### 4. Choose the story

Write up to three candidate claims from the facts, including an honest null result when no pattern survives. Choose one main claim for the first artifact. Do not force a story that the evidence does not support.

### 5. Select and implement

Call `dataviz-selector` for the form and encodings. Call `karthik-data-visualization` for implementation. Call `chart-annotations` only when the evidence benefits from on-chart marking.

Keep the analysis and chart reproducible in the project's existing language and file structure. Make the narrowest repo change needed.

### 6. Inspect and decide

Render the exact deliverable and inspect it. Use `dataviz-critique` when the design or story still needs open diagnosis. Use `dataviz-eval` when a formal send/revise/redesign decision or regression benchmark is required.

Return to the owning stage for each failure. Do not patch a later stage to compensate for an upstream problem.

### 7. Package

Deliver only the artifacts the request needs. A completed analytical chart normally includes:

- analysis or chart code;
- exact exported chart;
- compact facts table or equivalent computed evidence;
- short claim, definitions, caveats, and source note;
- `chart-explainer` copy when another reader will receive the chart without the analyst.

For slides, hand the chart and evidence to `karthik-powerpoint-style`; do not duplicate slide rules here.

## Operating constraints

- Prefer doing the analysis over presenting a long plan.
- Never let prose outrun computed evidence.
- Prefer one interpreted visual over a gallery or dashboard unless the task genuinely requires monitoring.
- Preserve raw data and unrelated repo artifacts.
- Render before claiming completion.
- When a stage fails, report the exact missing input or failed condition and the next executable action.
