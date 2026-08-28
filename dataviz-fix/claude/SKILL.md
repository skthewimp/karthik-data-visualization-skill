---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

The **repair front half**: image in, repaired artifact out. Return an improved chart. The
workflow exists to help produce an artifact, not to prevent one from reaching the user.

Repair has one job of its own - **diagnose the source and recover its data** - and then it
hands into the shared construct process (`dataviz-construct`) that both repair and
dataset-to-story creation use to turn a brief-and-data into a finished chart:

```text
diagnose+extract  ->  [ insight -> select -> idea -> build -> execution ]   (dataviz-construct)
```

Everything from `insight` onward is the shared tail; this skill owns only the diagnose+extract
front half and the handoff into it.

## Run every stage, whether or not a driver splits them

**The default, and the right way to run this, is separate calls per stage.** When an
application or harness drives the pipeline, each stage is its **own call** that loads only that
stage's skills plus the compact artifact handed forward from the previous stage. Loading every
skill into one context rots it, and a build call has no use for the discovery or evaluation
skills.

**Only if nothing is orchestrating the calls** - no driver, no harness, you were simply handed
the image and this skill in one turn - are the calls yours to make. Even then you do not dump
every skill in at once: walk the stages in order, opening each stage's named skills as you
reach that stage and letting the previous stage's detail fall away. "Separate call" is the
architecture, not a licence to skip a stage or to assume some other call already did it.

Handoffs are **structured text, not strict JSON**: each stage emits one markdown section per
content field plus, where the driver must branch, a small `routing` block of `key: value`
lines. This keeps the pipeline runnable on cheaper / open-weight models that break on nested
JSON. The content contract for every stage - the required fields and the routing keys - is
`dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE` (the diagnose stage plus the shared construct
tail); this skill carries the *reasoning*, that module the *shape*.

## Two anchors

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable
   reviewer, or an imperfect score must not suppress the best available output. Label
   limitations honestly; do not relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is not
   sacred - the source form gets no vote in what the repair becomes. But any instruction that
   arrives with it (requested chart type, annotations, what to fix, wording, brand or style
   preferences) is authoritative and must survive the whole process. When the prompt and a
   redesign impulse conflict, the prompt wins.

**Repair is forward design, not critique-plus-patch.** The flow does not start by critiquing
the source chart - that anchors everything on the existing image and makes "re-render the
source form, tidied" the path of least resistance. It extracts the intent and the data first,
then the construct process computes the insight, selects a form cold from it, builds, and
checks. Preserving a message is not preserving a form: the data and the messages must survive;
the encoding must not, and usually should not when the source form was the weakness.

## Inputs

- The image or artifact to repair.
- The prompt, if any: the requested change, preferences, and constraints. Treat everything the
  user states here as a requirement, not a suggestion.

## Stage 1 - Diagnose and extract

**Load:** `dataviz-brief`, `dataviz-extract`, `dataviz-critique`. **In:** source image and any
prompt. **Out:** the diagnose artifact (`DIAGNOSE_SCHEMA`).

State what the replacement must say and carry, and recover the underlying data - do not choose
a form here. Run the brief cold: the key messages and the required content for each, anything
explicitly dropped as not key with a reason, the audience and medium, and the **edit-vs-redesign
mode**. In parallel, extract the full period-by-category table: a value for every period and
every category, series, stack, or facet the chart encodes (colour is data), so any chosen form
can be built. Inventory and diagnose the whole chart, including neighbouring zones, and list
what must be preserved unchanged.

Difficulty of recovery is never grounds to drop a message or a category. Uncertain values and
unreadable labels go in the limitations; the categories stay. Do not critique the source's
execution as the first move - forward design needs the intent the chart should have served, not
a diagnosis of how the old chart failed.

The mode governs how the construct tail runs:

- **`bounded-edit`** - a literal, self-contained change that leaves the source form intact and
  correct ("fix the axis labels", "recolour series 3"). The construct tail skips
  `insight -> select -> idea`: apply the named edit to the source form at `build`, record the
  retained form, and check it at `execution`.
- **`redesign`** - everything else, and the default when unsure. Run the full construct tail.

## Hand to the construct process

Pass the diagnose artifact into `dataviz-construct` and run its tail:

- **Insight** (`karthik-evidence-builder`) computes the facts from the **recovered data** and
  names the headline claim + candidate annotations **freshly** - it does not inherit whatever
  the source chart asserted.
- **Select** (`dataviz-selector`) chooses the form **cold**: the source chart's form is not an
  input and gets no vote. A table is a valid cold verdict.
- **Idea-critique** (`dataviz-idea-critique`) checks the plan before any render - data,
  expression, insight, honesty - and routes back to insight or select until it holds.
- **Build** constructs the deliverable, carrying every key message with its required content and
  honouring every prompt constraint.
- **Execution-critique** (`dataviz-execution`) checks the rendered export - geometry, overlap,
  colour, precision, ink - and confirms a redesign build carries a cold form decision (a tidied
  re-render of the source form with no form choice behind it routes back to select).

How many revision passes either gate runs is the driver's budget; do not bake in a pass count.
See `dataviz-construct` for the shared tail in full.

## Deliver and continue

Deliver the artifact. State what changed and any inspection limitation that affects confidence.
Then treat user feedback as the main release signal: change the smallest relevant part of the
latest candidate, render again, inspect the named element, and return it. Do not restart from
the source unless the user asks for a redesign or the current form cannot support the change.

## Optional case logging

Use `case_manager.py` only when the user wants an audit trail, comparison history, bounded
benchmark, or reusable learning record. It owns the loop state, budget limits, best-candidate
preservation, and terminal states for a repeatable, resumable run. Case state never overrides
the delivery anchor: if a valid artifact exists, deliver it with its actual status. When used,
keep it minimal - start the case, record each rendered artifact, attach real inspection
evidence when available, and record feedback and acceptance.

## Failure handling

- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic
  inspection.
- **Eval subagent failure:** deliver the inspected candidate as unreviewed and say so.
- **External resource constraint:** deliver the best candidate and name the unresolved issue.
- **Renderer failure with no artifact:** report the concrete error and return any earlier valid
  candidate.
- **Missing evidence:** preserve visible source values, avoid invented claims, and label the
  limitation.

## Learning after acceptance

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule or
tool defect. Do not turn a chart-specific object, phrase, layout, or count into a universal
rule. Express reusable lessons as relationships or decision tests, and keep case-specific
details in the case record. Prefer simplifying or repairing the failing stage over adding prose,
schemas, or tests.
