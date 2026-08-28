---
name: dataviz-orchestrator
description: Orchestrate dataset-to-visual-story work by routing context, artifacts, and decisions through specialized visualization skills.
---

# Dataviz Orchestrator

The **creation front half**: raw data in, visual story out. Own the discovery-to-clean
sequence and its handoffs, then hand into the shared construct process (`dataviz-construct`)
that both creation and repair use to turn a brief-and-data into a finished chart. Use the
smallest relevant companion skill and keep one source of truth for each decision. (For
repairing an existing chart from an image, use `dataviz-fix`, the repair front half - it feeds
the same construct tail.)

## Run it as stages, not one context

The pipeline runs as an ordered sequence of **separate calls**, one per stage, each carrying
only the skills that stage needs plus a compact structured artifact handed forward from the
previous stage. Loading every skill into one context rots it: the build stage has no use for
the discovery or cleaning skills. Each stage below names the skills to load, the artifact it
receives, and the artifact it emits.

Handoffs are **structured text, not strict JSON**: each stage emits one markdown section per
content field (read by the next stage) plus, where the driver must branch, a small `routing`
block of `key: value` lines. This keeps the pipeline runnable on cheaper / open-weight models
that break on nested JSON. The content contract for every stage - the required fields and the
routing keys - is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE` (the discover/contract/clean
front half plus the shared construct tail); this skill carries the *reasoning*, that module
the *shape*. A driver loads each stage's skills with `stage_skill_bundle(stage)` and parses the
routing block with `dataviz_mcp.handoff` (which also accepts a JSON object, so strong-model
output still works). Do not duplicate the schemas here.

```text
discover -> contract -> clean  ->  [ insight -> select -> idea -> build -> execution ]
```

The bracketed tail is `dataviz-construct`, shared verbatim with repair.

## Intake and context

Before stage 1, record the dataset, the question or purpose, audience, medium, source
constraints, and requested output. Distinguish user-supplied context from assumptions. If
context is unavailable, proceed with an explicit assumption and state what the evidence cannot
support; do not suppress an otherwise valid artifact.

## Front-half stages

Each stage is one call. Load only the listed skill(s); pass the emitted artifact forward.

1. **Discover** - load `dataset-question-generator`. In: dataset and any context. Out: row
   grain, columns/types, likely denominators, candidate stories with the evidence each needs
   and its misleading risk, a recommended first story, and a "do not visualise yet" list. Use
   when the user gives data without a sharp claim.
2. **Contract** - load `karthik-analysis-planner`. In: discovery artifact and chosen story.
   Out: the operational question, metric, numerator/denominator, grain, the comparison that
   makes the number mean something, data requirements, falsifiers, and caveats. Do not chart.
3. **Clean** - load `karthik-data-cleaning`. In: contract and data. Out: visible
   transformations, validation results, provenance, and remaining limitations. Do not invent
   fields or values.

## Hand to the construct process

Pass the cleaned data and contract into `dataviz-construct` and run its tail:

- **Insight** - load `karthik-evidence-builder`. Compute the facts that answer the question -
  values, comparisons, uncertainty - from the data not priors, and name the **headline claim**
  the chart will assert plus any candidate annotation claims. This is the stage that fills what
  used to be a skill-less "facts" placeholder: the headline is decided here, from the data,
  before a form is chosen.
- **Select** - load `dataviz-selector`. Choose the simplest form that makes the claim easiest to
  see and hardest to misread; set the routing flags and number-display decisions.
- **Idea-critique** - load `dataviz-idea-critique`. The pre-render gate: is the data right, the
  expression right, the insight right, and honest? Route back to insight or select until it
  holds.
- **Build** - load `karthik-data-visualization` (chart) or `karthik-table-style` (table) per the
  `builder` field; add `chart-annotations` / `chart-explainer` / `dataviz-color` /
  `dataviz-precision` when the select artifact asks for them. Assert the headline claim in the
  title and place the annotation claims insight named.
- **Execution-critique** - load `dataviz-execution` (add `dataviz-eval` only for an explicit
  audit, high-risk decision, or benchmark). The post-render gate: geometry, overlap, colour,
  precision, ink.

How many revision passes either gate runs is the driver's budget. See `dataviz-construct` for
the shared tail in full.

## Stop and escalation rules

- If the data cannot answer the question, narrow or reframe it at the contract stage; do not
  invent fields or values.
- If a transformation changes the analytical meaning, return to the contract stage.
- If the insight is not supported by the facts, return to the insight stage.
- If the visual form cannot support the comparison, return to the select stage.
- If the rendered artifact fails, send only the concrete issues back to build or the execution
  gate.
- A downstream stage may reject or narrow an upstream artifact, but must state the reason and
  return a concrete handoff.
- Inspect the exact artifact under its intended delivery condition, then deliver the best valid
  output. An unavailable optional evaluator must not suppress it. Stop when the stated pass line
  is met; do not keep revising for taste.

Renderer availability must not change the chart design or force a translation into a weaker
implementation. When the chosen renderer has a metadata-producing capability, render the exact
deliverable through it and inspect that export before delivery. When it does not, keep the
appropriate renderer, inspect the exact export visually, and record uncovered geometry as
unknown. Do not translate a sound ggplot2 chart into Matplotlib only to obtain richer metadata.

## Output package

Leave behind only the artifacts useful for reproduction and review: source/analysis code,
prepared-data notes when needed, facts and the headline claim, select artifact, exported media,
matching render/inspection records when available, and an evaluation or caveat note. Keep
one-off preferences and domain examples in the case record or optional references, not in this
orchestration layer.
