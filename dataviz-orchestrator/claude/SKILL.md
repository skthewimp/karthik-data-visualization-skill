---
name: dataviz-orchestrator
description: Orchestrate dataset-to-visual-story work by routing context, artifacts, and decisions through specialized visualization skills.
---

# Dataviz Orchestrator

The staged orchestrator for **dataset-to-visual-story** work: raw data in, visual story out.
Own the **sequence and handoffs**, not the substantive rules of every stage. Use the
smallest relevant companion skill and keep one source of truth for each decision. (For
repairing an existing chart from an image, use `dataviz-fix`, the repair orchestrator.)

## Run it as stages, not one context

The pipeline runs as an ordered sequence of **separate calls**, one per stage, each carrying
only the skills that stage needs plus a compact structured artifact handed forward from the
previous stage. Loading every skill into one context rots it: the build stage has no use for
the discovery or cleaning skills. Each stage below names the skills to load, the artifact it
receives, and the artifact it emits.

The machine-readable contract for this pipeline - the exact skill subset and the JSON handoff
schema for every stage - is `dataviz_mcp/stage_contracts.py:STORY_PIPELINE`. This skill
carries the *reasoning*; that module carries the *shape*. A driver loads each stage's skills
with `stage_skill_bundle(stage)` and validates each handoff against the stage's
`output_schema`. Do not duplicate the schemas here.

```text
discover -> contract -> clean -> facts -> select -> build -> refine
```

## Intake and context

Before stage 1, record the dataset, the question or purpose, audience, medium, source
constraints, and requested output. Distinguish user-supplied context from assumptions. If
context is unavailable, proceed with an explicit assumption and state what the evidence
cannot support; do not suppress an otherwise valid artifact.

## Stages

Each stage is one call. Load only the listed skill(s); pass the emitted artifact forward.

1. **Discover** - load `dataset-question-generator`. In: dataset and any context. Out: row
   grain, columns/types, likely denominators, candidate stories with the evidence each needs
   and its misleading risk, a recommended first story, and a "do not visualise yet" list.
   Use when the user gives data without a sharp claim.
2. **Contract** - load `karthik-analysis-planner`. In: discovery artifact and chosen story.
   Out: the operational question, metric, numerator/denominator, grain, the comparison that
   makes the number mean something, data requirements, falsifiers, and caveats. Do not chart.
3. **Clean** - load `karthik-data-cleaning`. In: contract and data. Out: visible
   transformations, validation results, provenance, and remaining limitations. Do not invent
   fields or values.
4. **Facts** - no dedicated skill yet (`karthik-evidence-builder` is a known gap). In:
   contract and prepared data. Out: computed facts - values, comparisons, uncertainty - and
   candidate claims, from the data not from priors. Do not chart.
5. **Select** - load `dataviz-selector`. In: contract and facts. Out: the chosen form. Set
   `builder` to `chart` or `table` (a table is a valid verdict for exact lookup or
   non-commensurable values); set `needs_annotations` / `needs_explainer` from the plan;
   emit design, layout plan, and acceptance checks.
6. **Build** - load `karthik-data-visualization` (chart) **or** `karthik-table-style`
   (table) per the `builder` field; add `chart-annotations` / `chart-explainer` /
   `dataviz-color` / `dataviz-precision` when the
   select artifact asks for them. In: contract, facts, select artifact. Out: the rendered
   artifact plus reproducible code and the maker's inspection of the exact export.
7. **Refine** - load `dataviz-critique`; add `dataviz-eval` only for an explicit audit,
   high-risk decision, or benchmark. In: the built candidate. Out: the checker verdict, any
   consolidated revision, and the delivered artifact with residual limitations.

## Stop and escalation rules

- If the data cannot answer the question, narrow or reframe it at the contract stage; do not
  invent fields or values.
- If a transformation changes the analytical meaning, return to the contract stage.
- If the visual form cannot support the comparison, return to the select stage.
- If the rendered artifact fails, send only the concrete issues back to build or refine.
- A downstream stage may reject or narrow an upstream artifact, but must state the reason and
  return a concrete handoff.
- Inspect the exact artifact once under its intended delivery condition, then deliver the
  best valid output. An unavailable optional evaluator must not suppress it. Stop when the
  stated pass line is met; do not keep revising for taste.

Renderer availability must not change the chart design or force a translation into a weaker
implementation. When the chosen renderer has a metadata-producing capability, render the
exact deliverable through it and inspect that export before delivery. When it does not, keep
the appropriate renderer, inspect the exact export visually, and record uncovered geometry as
unknown. Do not translate a sound ggplot2 chart into Matplotlib only to obtain richer
metadata.

## Output package

Leave behind only the artifacts useful for reproduction and review: source/analysis code,
prepared-data notes when needed, facts table, select artifact, exported media, matching
render/inspection records when available, and an evaluation or caveat note. Keep one-off
preferences and domain examples in the case record or optional references, not in this
orchestration layer.
