---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

The staged orchestrator for **chart repair**: image in, repaired artifact out. Return an
improved chart. The workflow exists to help produce an artifact, not to prevent one from
reaching the user.

## Run it as stages, not one context

Repair runs as an ordered sequence of **separate calls**, one per stage, each carrying only
the skills that stage needs plus a compact structured artifact handed forward from the
previous stage. This is deliberate: loading every skill into one context rots it, and a
build call has no use for the discovery or evaluation skills. Each stage below names the
skills to load, the artifact it receives, and the artifact it emits.

Handoffs are **structured text, not strict JSON**: each stage emits one markdown section
per content field (read by the next stage) plus, where the driver must branch, a small
`routing` block of `key: value` lines. This keeps the pipeline runnable on cheaper /
open-weight models that break on nested JSON. The content contract for every stage - the
required fields and the routing keys - is `dataviz_mcp/stage_contracts.py:REPAIR_PIPELINE`;
this skill carries the *reasoning*, that module the *shape*. When an application drives the
pipeline it loads each stage's skills with `stage_skill_bundle(stage)` and parses the routing
block with `dataviz_mcp.handoff` (which also accepts a JSON object, so strong-model output
still works). Do not duplicate the schemas here.

```text
diagnose+extract  ->  select  ->  build  ->  refine
```

## Two anchors

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable
   reviewer, or an imperfect score must not suppress the best available output. Label
   limitations honestly; do not relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is
   not sacred - the source form gets no vote in what the repair becomes. But any instruction
   that arrives with it (requested chart type, annotations, what to fix, wording, brand or
   style preferences) is authoritative and must survive the whole process. When the prompt
   and a redesign impulse conflict, the prompt wins.

**Repair is forward design, not critique-plus-patch.** The flow does not start by critiquing
the source chart - that anchors everything on the existing image and makes "re-render the
source form, tidied" the path of least resistance. It extracts the intent and the data
first, selects a form cold from those, builds, and only then checks. Preserving a message is
not preserving a form: the data and the messages must survive; the encoding must not, and
usually should not when the source form was the weakness.

## Inputs

- The image or artifact to repair.
- The prompt, if any: the requested change, preferences, and constraints. Treat everything
  the user states here as a requirement, not a suggestion.

## Stage 1 - Diagnose and extract

**Load:** `dataviz-brief`, `dataviz-extract`, `dataviz-critique`. **In:** source image and
any prompt. **Out:** the diagnose artifact (`DIAGNOSE_SCHEMA`).

State what the replacement must say and carry, and recover the underlying data - do not
choose a form here. Run the brief cold: the key messages and the required content for each,
anything explicitly dropped as not key with a reason, the audience and medium, and the
**edit-vs-redesign mode**. In parallel, extract the full period-by-category table: a value
for every period and every category, series, stack, or facet the chart encodes (colour is
data), so any chosen form can be built. Inventory and diagnose the whole chart, including
neighbouring zones, and list what must be preserved unchanged.

Difficulty of recovery is never grounds to drop a message or a category. Uncertain values
and unreadable labels go in the limitations; the categories stay. Do not critique the
source's execution as the first move - forward design needs the intent the chart should have
served, not a diagnosis of how the old chart failed.

The mode governs the rest of the flow:

- **`bounded-edit`** - a literal, self-contained change that leaves the source form intact
  and correct ("fix the axis labels", "recolour series 3"). Skip stage 2, apply the named
  edit to the source form in stage 3, re-render, and check. Stage 4 eval is skipped for a
  purely literal or cosmetic edit.
- **`redesign`** - everything else, and the default when unsure. Run the full flow.

## Stage 2 - Select the form

**Load:** `dataviz-selector`. **In:** the diagnose artifact (not the image). **Out:** the
select artifact (`SELECT_SCHEMA`).

Choose the form **cold**: the source chart's form is not an input and gets no vote. Select
the simplest form that makes the key messages easiest to see and hardest to misread, for the
stated audience and medium. For "many series over time, compare trajectories" this is small
multiples or direct-labelled lines, because that is what the data shape and message want -
the source stack is not in the room. There is no "unless the source form is clearly correct"
escape hatch in the redesign path.

A **table is a valid cold verdict**: when the intent is exact lookup or the values are not
commensurable on one scale, a well-formatted table can be the right repair - set the
`builder` field to `table`, otherwise `chart`. That field decides which builder skill stage 3
loads. Set `needs_annotations` and `needs_explainer` from whether the plan genuinely calls
for on-chart marks or accompanying prose. Emit the design, the layout plan under the declared
delivery condition, and an observable acceptance check for every fatal or major problem and
every preservation requirement.

## Stage 3 - Build

**Load:** `karthik-data-visualization` (when `builder` is `chart`) **or** `karthik-table-style`
(when `builder` is `table`); add `chart-annotations` when `needs_annotations`,
`chart-explainer` when `needs_explainer`, `dataviz-color` when `needs_color_plan`, and
`dataviz-precision` when `needs_precision_plan`. **In:** source, diagnose artifact, select artifact.
**Out:** the build artifact (`BUILD_SCHEMA`).

Build the deliverable to the plan, carrying every key message with its required content -
which may take more than one chart (a totals view alongside a per-category breakdown). When
`chart-annotations` is loaded, let it judge whether any mark clears the bar, rank candidates,
word the label, and place it - or leave the chart unmarked and put the finding in the title.
Compose the headline and subhead here: `chart-annotations` decides the claim the title
asserts, `karthik-data-visualization` sets title/subtitle style, and the installed writing or
brand-style skill, if one exists in this environment, sets the voice; if none is installed,
apply the prompt's stated preferences.

Honour every prompt constraint even while redesigning everything the prompt left open.
Produce one PNG, SVG, or PDF from reproducible code, reusing the project's renderer; prefer
ggplot2 when available but do not delay output for a renderer preference. For a table build,
use `karthik-table-style` with `gt` (or markdown/HTML where R is unavailable) and render the
inspected raster through the same `render_and_inspect_chart` ragg path the charts use, so it
is gated on the same footing. Inspect that exact export at delivery size and correct
consequential defects before returning; record each acceptance check as pass, fail, or
unknown against observed evidence. For a `bounded-edit`, apply the named edit to the source
form and re-render - staying anchored is the point.

## Stage 4 - Inspect and revise

**Load:** `dataviz-critique`; add `dataviz-eval` only for an explicit audit or high-risk
decision. **In:** source, plan, built candidate. **Out:** the refine artifact (`REFINE_SCHEMA`).

Run `dataviz-critique` on the exact export at delivery size as a **checker, not a designer**:
it does not re-derive the messages (the brief owns those) and does not reopen the form unless
the candidate genuinely fails a message. It answers two questions - does the candidate carry
the stage-1 intent (every key message with its required content, nothing key silently
dropped, prompt constraints honoured), and is it a good chart (mechanical: clipping,
collisions, typography hierarchy, label-to-mark association, duplicated scaffolding, missing
categories/periods/units, colour and contrast; semantic: measure, denominator/universe,
time/context, claim strength, units). Use `render_and_inspect_chart` when available;
otherwise render locally, inspect visually, and say deterministic inspection was unavailable.

Consolidate defects into one focused revision and re-inspect the changed regions and their
neighbours. Cap the loop at two passes; exit as soon as no fatal or major defect remains.

**One independent evaluation, only when warranted.** For an explicit audit or high-risk
decision, spawn exactly one subagent to run `dataviz-eval` as a blind reviewer on the
converged candidate. Give it only the rendered artifact and a short brief (prompt, inferred
style, inferred headings, intended message); withhold the source image, the maker's
diagnosis, and the rendering code so the read stays blind. It returns one verdict and ranked
findings; it does not render, iterate, or get re-spawned. Apply at most one final revision
from its findings, then deliver. If eval calls for an expensive redesign, apply it when
cheap; otherwise deliver the current candidate and surface the concern in one sentence.

## Deliver and continue

Deliver the artifact. State what changed and any inspection limitation that affects
confidence. Then treat user feedback as the main release signal: change the smallest relevant
part of the latest candidate, render again, inspect the named element, and return it. Do not
restart from the source unless the user asks for a redesign or the current form cannot
support the change.

## Optional case logging

Use `case_manager.py` only when the user wants an audit trail, comparison history, bounded
benchmark, or reusable learning record. It owns the loop state, budget limits,
best-candidate preservation, and terminal states for a repeatable, resumable run. Case state
never overrides the delivery anchor: if a valid artifact exists, deliver it with its actual
status. When used, keep it minimal - start the case, record each rendered artifact, attach
real inspection evidence when available, and record feedback and acceptance.

## Failure handling

- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic
  inspection.
- **Eval subagent failure:** deliver the inspected candidate as unreviewed and say so.
- **External resource constraint:** deliver the best candidate and name the unresolved issue.
- **Renderer failure with no artifact:** report the concrete error and return any earlier
  valid candidate.
- **Missing evidence:** preserve visible source values, avoid invented claims, and label the
  limitation.

## Learning after acceptance

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule
or tool defect. Do not turn a chart-specific object, phrase, layout, or count into a
universal rule. Express reusable lessons as relationships or decision tests, and keep
case-specific details in the case record. Prefer simplifying or repairing the failing stage
over adding prose, schemas, or tests.
