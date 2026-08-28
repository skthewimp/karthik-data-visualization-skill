# Unify creation + repair into one construct process, split into idea and execution gates

Status: implemented (2026-08-28). See the CHANGELOG "Coalesce creation and repair into one construct process" entry and the DEVLOG for the same date.

## Problem

`dataviz-orchestrator` (create) and `dataviz-fix` (repair) already converged on the same
`select -> build -> refine` tail, duplicated as prose in both skills and as two near-identical
stage tuples in `dataviz_mcp/stage_contracts.py`. Three things were wrong:

1. The tail should be **one process**, not two copies.
2. The single `refine` stage conflated *ideas* (is the data right, the expression right, the
   message right) with *execution* (overlaps, geometry, ink). Ideas can be judged before the
   chart is rendered; execution cannot. They belong in separate, ordered gates.
3. Insight for headlines was thin and misplaced: create's `facts` stage was skill-less, repair
   recovered messages rather than computing them, and the headline/annotation claim was decided
   late at build with nothing validating it pre-render. Iteration was hardcoded to two passes.

## Design

One shared terminal process (`dataviz-construct`) both front halves hand into:

```text
insight -> select -> idea -> build -> execution
```

- **Create** hands in after `clean`; **repair** after `diagnose+extract`. A repair
  `bounded-edit` skips `insight -> select -> idea`.
- **Insight** (`karthik-evidence-builder`, new) computes the facts and names the headline claim
  + candidate annotations from the data, before a form is chosen.
- **Idea-critique** (`dataviz-idea-critique`, new) is the pre-render gate (data / expression /
  insight / honesty), routing back to insight or select.
- **Execution-critique** (`dataviz-execution`, new) is the post-render gate (geometry, overlap,
  colour, precision, ink), leaning on `render_and_inspect_chart`.
- The loop is a `find -> fix -> redo` unit; **the pass count is the driver's / harness's
  budget**, not a fixed cap. `dataviz-critique` is untouched (standalone review + repair
  diagnose).

## Machine shape

In `dataviz_mcp/stage_contracts.py`, the `select`, `idea`, `build`, and `execution` stages are
the *same* `Stage` objects in `REPAIR_PIPELINE` and `STORY_PIPELINE` (via `_construct_tail`);
only `insight` is parameterised by its input schema. `INSIGHT_SCHEMA` supersedes `FACTS_SCHEMA`
(adds `headline_claim`, `candidate_annotations`); `EXECUTION_SCHEMA` replaces `REFINE_SCHEMA`;
`IDEA_CRITIQUE_SCHEMA` is new. Contract tests assert the shared tail and that no stage hardcodes
a pass count.
