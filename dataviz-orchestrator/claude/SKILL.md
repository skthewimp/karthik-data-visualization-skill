---
name: dataviz-orchestrator
description: Orchestrate dataset-to-visual-story work by routing context, artifacts, and decisions through specialized visualization skills.
---

# Dataviz Orchestrator

Own the **sequence and handoffs**, not the substantive rules of every stage. Use the smallest relevant companion skill and keep one source of truth for each decision.

## Workflow

```text
intake → question/evidence contract → data preparation → facts → visual selection → implementation → independent evaluation → revise or deliver
```

### 1. Intake and context

Record the dataset or existing artifact, question or purpose, audience, medium, source constraints, and requested output. Distinguish user-supplied context from assumptions. If required context is unavailable, proceed with an explicit assumption or stop at the affected stage.

### 2. Route the work

- Discover candidate questions from a raw dataset: `dataset-question-generator`.
- Define an operational question and evidence contract: `karthik-analysis-planner`.
- Inspect and transform data: `karthik-data-cleaning`.
- Choose a visual form: `dataviz-selector`.
- Implement style, labels, layout, and export: `karthik-data-visualization`.
- Choose and place on-chart annotations: `chart-annotations`.
- Write accompanying prose: `chart-explainer`.
- Review an existing or rendered visual: `dataviz-critique` or `dataviz-eval`.
- Run a stateful repair case with feedback and acceptance: `dataviz-fix`.

Do not duplicate those skills' detailed rules here.

### 3. Required handoffs

Pass forward the smallest useful artifact at each boundary:

1. **Context brief** — question, audience, medium, constraints.
2. **Analysis contract** — definitions, grain, numerator/denominator, metric, comparison, data requirements, falsifiers, caveats.
3. **Prepared data** — visible transformations, validation results, provenance, and remaining limitations.
4. **Facts table** — computed values, comparisons, uncertainty, and candidate claims.
5. **Chart specification** — selected form, encodings, semantic mappings, context layers, and delivery condition.
6. **Rendered artifact** — exact file delivered, plus reproducible code.
7. **Evaluation report** — blind reads, evidence scope, required gates, release checks, verdict, and minimum pass set.

A downstream stage may reject or narrow an upstream artifact, but must state the reason and return a concrete handoff.

### 4. Stop and escalation rules

- If the data cannot answer the question, narrow or reframe the question; do not invent fields or values.
- If a transformation changes the analytical meaning, return to the analysis contract.
- If the visual form cannot support the comparison, return to `dataviz-selector`.
- If the rendered artifact fails, send only the concrete issues to the implementation or repair stage.
- Do not deliver until the exact artifact has been inspected under its intended delivery condition and the applicable evaluation gate passes.
- Stop when the stated pass line is met; do not keep revising for taste.

Renderer availability must not change the chart design or force a translation into a weaker visual implementation. When the chosen renderer has a metadata-producing capability, render the exact deliverable through it and inspect that export before critique, evaluation, or delivery. Do not bypass supported metadata generation and then substitute a raster-only check. When the chosen renderer lacks metadata support, keep the appropriate renderer, inspect the exact export anyway, record uncovered geometry as unknown, and require independent visual evaluation. Do not translate a sound ggplot2 chart into Matplotlib only to obtain richer metadata. Send reported mechanical defects through the owning implementation or annotation stage before reopening broader design choices.

### 5. Output package

Leave behind only the artifacts useful for reproduction and review: source/analysis code, prepared-data notes when needed, facts table, chart specification, exported media, matching render/inspection records when available, and evaluation or caveat note. Keep one-off preferences and domain examples in the case record or optional references, not in this orchestration layer.
