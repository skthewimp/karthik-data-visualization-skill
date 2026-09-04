---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

The **repair front half**: image in, repaired artifact out. The workflow exists to help produce an artifact, not to prevent one from reaching the user.

Repair has one job of its own - **diagnose the source and recover its data** - then hands into the shared construct process (`dataviz-construct`) that both repair and dataset-to-story creation use to turn a brief-and-data into a finished chart:

```text
diagnose+extract  ->  [ insight -> select -> idea -> build -> execution ]   (dataviz-construct)
```

Everything from `insight` onward is the shared tail; this skill owns only diagnose+extract and the handoff.

## Run every stage as its own call

Separate calls per stage is the default and the right way to run this - each call loads only that stage's skills plus the artifact handed forward; loading every skill into one context rots it. If nothing external orchestrates the calls and you have a subagent/task capability, **you become the driver** and dispatch each stage as an isolated subagent call: the isolation keeps build (maker) and the idea/execution gates (checkers) in separate contexts, so a checker can't inherit and rationalise the build's shortcuts. Only when you genuinely cannot spawn subagents, walk the stages inline in order, opening each stage's skills as you reach it - never dumping every skill in at once, and never skipping a stage. Handoffs are structured text (markdown sections plus a small `routing` block where the driver must branch), not strict JSON, so the pipeline runs on cheaper/open-weight models. The full contract is `dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE`; see `dataviz-construct` for the shared tail. This skill carries the reasoning, that module the shape.

## Two anchors

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable reviewer, or an imperfect score must not suppress the best available output. Label limitations honestly; don't relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is not sacred - the source form gets no vote. But any instruction arriving with it (requested chart type, annotations, what to fix, wording, brand/style preferences) is authoritative and must survive the whole process. When the prompt and a redesign impulse conflict, the prompt wins.

**Repair is forward design, not critique-plus-patch.** Don't start by critiquing the source - that anchors everything on the existing image and makes "re-render the source form, tidied" the path of least resistance. Extract the intent and data first, then let construct compute the insight, select a form cold, build, and check. Preserving a message is not preserving a form: the data and messages must survive; the encoding usually should not when the source form was the weakness.

## Inputs

- The image or artifact to repair.
- The prompt, if any: the requested change, preferences, constraints - treat everything stated here as a requirement, not a suggestion.

## Stage 1 - Diagnose and extract

**Load:** `dataviz-brief`, `dataviz-extract`, `dataviz-critique`. **In:** source image and any prompt. **Out:** the diagnose artifact (`DIAGNOSE_SCHEMA`).

State what the replacement must say and carry, and recover the underlying data - don't choose a form here. Run the brief cold: key messages and required content for each, anything explicitly dropped as not key with a reason, the audience and medium, and the **edit-vs-redesign mode**. In parallel, extract the full period-by-category table (a value for every period and every category, series, stack, or facet the chart encodes - colour is data) so any chosen form can be built. Inventory and diagnose the whole chart including neighbouring zones, and list what must be preserved unchanged.

Difficulty of recovery is never grounds to drop a message or category - uncertain values and unreadable labels go in the limitations; the categories stay. Don't critique the source's execution as the first move.

The mode governs how the construct tail runs:

- **`bounded-edit`** - a literal, self-contained change leaving the source form intact and correct ("fix the axis labels", "recolour series 3"). The tail skips `insight -> select -> idea`: apply the named edit to the source form at `build`, record the retained form, check at `execution`.
- **`redesign`** - everything else, and the default when unsure. Run the full construct tail.

## Hand to the construct process

Pass the diagnose artifact into `dataviz-construct`. Its tail computes the insight from the **recovered data** (`karthik-evidence-builder`, naming the headline claim + annotations freshly, not inheriting what the source asserted), selects the form **cold** (`dataviz-selector`; a table is a valid cold verdict), gates the plan before any render (`dataviz-idea-critique`), builds carrying every key message and prompt constraint, and gates the rendered export (`dataviz-execution`, which also confirms a redesign build carries a cold form decision - a tidied re-render with no form choice routes back to select). How many passes either gate runs is the driver's budget; don't bake in a count.

## Deliver and continue

Deliver the artifact; state what changed and any inspection limitation affecting confidence. Then treat user feedback as the main release signal: change the smallest relevant part of the latest candidate, render again, inspect the named element, return it. Don't restart from the source unless the user asks for a redesign or the current form can't support the change.

## Optional case logging

Use `case_manager.py` only when the user wants an audit trail, comparison history, bounded benchmark, or reusable learning record. It owns loop state, budget limits, best-candidate preservation, and terminal states for a repeatable, resumable run. Case state never overrides the delivery anchor: if a valid artifact exists, deliver it with its actual status. Keep it minimal - start the case, record each rendered artifact, attach real inspection evidence when available, record feedback and acceptance.

## Failure handling

- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic inspection.
- **External resource constraint:** deliver the best candidate and name the unresolved issue.
- **Renderer failure with no artifact:** report the concrete error and return any earlier valid candidate.
- **Missing evidence:** preserve visible source values, avoid invented claims, label the limitation.

## Learning after acceptance

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule or tool defect. Don't turn a chart-specific object, phrase, layout, or count into a universal rule. Express lessons as relationships or decision tests, keep case-specific detail in the case record, and prefer simplifying or repairing the failing stage over adding prose, schemas, or tests.
