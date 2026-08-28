---
name: dataviz-construct
description: The shared process both chart creation and repair hand into - insight, select, idea-critique, build, execution-critique - run as a driver-budgeted loop.
---

# Dataviz Construct

The **one process that is the last step of both** dataset-to-story creation and chart repair.
Each has its own front half - creation discovers a story, contracts it, and cleans the data;
repair diagnoses a source image and extracts its data - and once the front half has figured
out *what to say and from what data*, both hand into this shared construct process to turn it
into a finished chart.

```text
insight -> select -> idea -> build -> execution
```

- **Creation** hands in after `clean`.
- **Repair** hands in after `diagnose+extract`.
- A repair **`bounded-edit`** (a literal, self-contained change that keeps the source form -
  "recolour series 3", "fix the axis labels") skips `insight -> select -> idea` and goes
  straight to `build -> execution`, because the claim and the form are unchanged on purpose.

## The stages

Each stage is one call that loads only its own skill(s) plus the compact artifact handed
forward. Loading every skill into one context rots it.

1. **Insight** - `karthik-evidence-builder`. Compute the facts and name the **headline claim**
   plus candidate annotation claims, from the data, before a form is chosen. The headline is
   decided here, not improvised at build.
2. **Select** - `dataviz-selector`. Choose the simplest form that makes the claim easiest to
   see and hardest to misread. For a repair, choose it **cold** - the source form gets no vote.
   Set the routing flags (`builder`, `needs_annotations`, `needs_explainer`, `needs_color_plan`,
   `needs_precision_plan`) and the number-display decisions.
3. **Idea-critique** - `dataviz-idea-critique`. The **pre-render gate**: is the data right, the
   expression right, the insight right, and honest? Route back to `insight` (wrong claim or
   evidence) or `select` (wrong form) until the idea holds.
4. **Build** - `karthik-data-visualization` (chart) or `karthik-table-style` (table), plus
   `chart-annotations` / `chart-explainer` / `dataviz-color` / `dataviz-precision` when the
   select artifact asks for them. Assert the headline claim in the title; word and place the
   annotation claims the insight stage named. Render one real artifact.
5. **Execution-critique** - `dataviz-execution` (add `dataviz-eval` for an explicit audit or
   high-risk decision). The **post-render gate**: geometry, overlap, labels, colour, precision,
   ink. Route back to `build`, or - rarely - to `idea` if the render shows the idea itself is
   wrong.

## Two gates, in order

The idea gate runs **before** the chart is drawn; the execution gate runs **after**. This is
the whole point of splitting them: there is no sense fixing label overlaps on a chart that is
the wrong chart. Ideas can be judged from the plan and the data - an LLM does not need to see
the render to know the form cannot carry the claim - so that check comes first. Execution can
only be judged from pixels, so it comes second. Substance before craft.

## The loop is a unit; the driver owns the count

Each gate runs the same shape: **find everything wrong, decide the fixes, redo, re-check**.
Whether that runs zero, one, or several times is the **driver's / harness's budget** - it is
never a fixed pass count baked into this skill or any stage. Exit a gate as soon as no fatal or
major defect remains. Do not keep revising for taste past the pass line.

## Deliver a valid artifact

A valid rendered candidate must be delivered. Missing infrastructure, an unavailable optional
evaluator, or an acceptance check left `unknown` for want of an external denominator or dataset
must not suppress the best available output - disclose the limitation honestly and still
deliver. Reserve a blocked outcome for a genuine inability to produce any valid artifact at
all.

## Staged, not one context

Separate calls per stage is the default and the right way to run this: each call carries only
that stage's skills plus the artifact handed forward. When nothing is orchestrating the calls -
you were handed the plan and this skill in one turn - you still walk every stage in order,
opening each stage's skills as you reach it and letting the previous stage's detail fall away;
"separate call" is the architecture, never a licence to skip a stage. Handoffs are structured
text (markdown sections plus, at the select branch, a small `routing` block of `key: value`
lines), not strict JSON, so the pipeline runs on cheaper / open-weight models too. The content
contract - the exact skill subset and required fields per stage - is the construct tail in
`dataviz_mcp/stage_contracts.py`; this skill carries the reasoning, that module the shape.
