---
name: dataviz-orchestrator
description: Orchestrate dataset-to-visual-story work by routing context, artifacts, and decisions through specialized visualization skills.
---

# Dataviz Orchestrator

The **creation front half**: raw data in, visual story out. Own the discovery-to-clean sequence and its handoffs, then hand into the shared construct process (`dataviz-construct`) that both creation and repair use to turn a brief-and-data into a finished chart. Use the smallest relevant companion skill and keep one source of truth for each decision. (To repair an existing chart from an image, use `dataviz-fix`, the repair front half - it feeds the same tail.)

## Run it as stages, not one context

The pipeline runs as an ordered sequence of **separate calls**, one per stage, each loading only that stage's skills plus a compact artifact handed forward. Loading every skill into one context rots it - the build stage has no use for the discovery or cleaning skills. Handoffs are structured text (one markdown section per content field, plus a small `routing` block where the driver must branch), not strict JSON, so the pipeline runs on cheaper/open-weight models. The content contract per stage is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE`; a driver loads each stage's skills with `stage_skill_bundle(stage)` and parses routing with `dataviz_mcp.handoff` (which also accepts JSON). This skill carries the reasoning, that module the shape - don't duplicate the schemas here.

```text
discover -> contract -> clean  ->  [ insight -> select -> idea -> build -> execution ]
```

The bracketed tail is `dataviz-construct`, shared verbatim with repair.

## Intake and context

Before stage 1, record the dataset, question/purpose, audience, medium, source constraints, and requested output. Distinguish user-supplied context from assumptions. If context is unavailable, proceed with an explicit assumption and state what the evidence can't support; don't suppress an otherwise valid artifact.

## Front-half stages

Each stage is one call. Load only the listed skill(s); pass the emitted artifact forward.

1. **Discover** - `dataset-question-generator`. In: dataset and context. Out: row grain, columns/types, likely denominators, candidate stories with the evidence each needs and its misleading risk, a recommended first story, and a "do not visualise yet" list. Use when the user gives data without a sharp claim.
2. **Contract** - `karthik-analysis-planner`. In: discovery artifact and chosen story. Out: the operational question, metric, numerator/denominator, grain, the comparison that makes the number mean something, data requirements, falsifiers, caveats. Don't chart.
3. **Clean** - `karthik-data-cleaning`. In: contract and data. Out: visible transformations, validation results, provenance, remaining limitations. Don't invent fields or values.

## Hand to the construct process

Pass the cleaned data and contract into `dataviz-construct` and run its tail (full detail there). Per-stage skills to load: **insight** `karthik-evidence-builder` (compute the facts from the data and name the **headline claim** plus candidate annotations, before a form is chosen), **select** `dataviz-selector` (simplest form for the claim; set routing flags and number-display decisions), **idea** `dataviz-idea-critique` (pre-render gate), **build** `karthik-data-visualization` (chart) or `karthik-table-style` (table) per the `builder` field, adding `chart-annotations`/`chart-explainer`/`dataviz-color`/`dataviz-precision` when the select artifact asks, **execution** `dataviz-execution` (post-render gate). How many passes either gate runs is the driver's budget.

## Stop and escalation rules

- If the data can't answer the question, narrow or reframe it at the contract stage; don't invent fields or values.
- If a transformation changes the analytical meaning, return to contract.
- If the insight isn't supported by the facts, return to insight.
- If the visual form can't support the comparison, return to select.
- If the rendered artifact fails, send only the concrete issues back to build or the execution gate.
- A downstream stage may reject or narrow an upstream artifact, but must state the reason and return a concrete handoff.
- Inspect the exact artifact under its intended delivery condition, then deliver the best valid output. An unavailable optional evaluator must not suppress it. Stop when the pass line is met; don't keep revising for taste.

Renderer availability must not change the chart design or force a translation into a weaker implementation. When the chosen renderer has a metadata-producing capability, render the exact deliverable through it and inspect that export; when it doesn't, keep the appropriate renderer and inspect the exact export visually (a real check that can support delivery), recording only what a picture can't settle (sub-pixel overlap, exact point size) as a limitation.

## Output package

Leave behind only artifacts useful for reproduction and review: source/analysis code, prepared-data notes when needed, facts and the headline claim, select artifact, exported media, matching render/inspection records when available, and an evaluation or caveat note. Keep one-off preferences and domain examples in the case record or optional references, not in this orchestration layer.
