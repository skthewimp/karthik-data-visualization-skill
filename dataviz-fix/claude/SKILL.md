---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

Return an improved chart. The workflow exists to help produce an artifact, not to prevent one from reaching the user.

**Repair is forward design, not critique-plus-patch.** The flow does not start by critiquing the source chart - that anchors everything on the existing image and makes "re-render the source form, tidied" the path of least resistance. Instead it extracts the intent and the data first, selects a form cold from those, builds, and only then checks. Critique is a downstream checker here, not the first move.

## Two anchors

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable reviewer, or an imperfect score must not suppress the best available output. Label limitations honestly; do not relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is not sacred - the source form gets no vote in what the repair becomes. But any instruction that arrives with it (requested chart type, annotations, what to fix, wording, brand or style preferences) is authoritative and must survive the whole process. When the prompt and a redesign impulse conflict, the prompt wins.

Preserving a message is not preserving a form. The data and the messages must survive; the encoding must not, and usually should not when the source form was the weakness.

## Inputs

- The image or artifact to repair.
- The prompt, if any: the requested change, preferences, and constraints. Treat everything the user states here as a requirement, not a suggestion.

## Default workflow

The order matters: intent and data come before form, and form is chosen cold. Do not reorder to start from the source chart.

### 1. Intent - build the brief

Run `dataviz-brief` in the current chat on the image and any prompt. It produces: the key messages and the required content for each, anything explicitly dropped as not key (with a reason), the audience and medium, the story, the authoritative prompt constraints, a thin set of keep-notes (source ideas worth carrying, not a fault-list), and the **edit-vs-redesign mode**.

The mode governs the rest of the flow:

- **`bounded-edit`** - a literal, self-contained change that leaves the source form intact and correct ("fix the axis labels", "recolour series 3"). Stay anchored: skip steps 2 and 3, apply the named edit to the source form in step 4, re-render, and check. Step 6 (eval) is skipped for a purely literal or cosmetic edit.
- **`redesign`** - everything else, and the default when unsure. The form is reopened; run the full flow below.

Do not critique the source chart's execution here. Forward design needs the intent the chart should have served, not a diagnosis of how the old chart failed.

### 2. Data - extract the full table

In parallel with step 1, run `dataviz-extract` on the image to recover the full period-by-category table: a value for every period and every category, series, stack, or facet the chart encodes (colour is data). Not totals or the envelope - every cell, so any chosen form can be built. Mark screenshot-derived values approximate; never drop a category because its values are hard to read.

### 3. Select - choose the form cold

Run `dataviz-selector` on the intent (step 1) and data (step 2). Run it **cold**: the source chart's form is not an input and gets no vote. Select the simplest form that makes the key messages easiest to see and hardest to misread, for the stated audience and medium. For "many series over time, compare trajectories" this is small multiples or direct-labelled lines, because that is what the data shape and message want - the source stack is not in the room. There is no "unless the source form is clearly correct" escape hatch in the redesign path; the form is chosen from the brief, not inherited.

### 4. Build

Construct the chart(s) with `karthik-data-visualization` for implementation and Karthik-style defaults. Carry every key message the brief named, showing the required content for each - which may take more than one chart (a whole-and-parts split, a totals view alongside a per-category breakdown). Decide the chart count, decomposition, and form here, from the brief and the selector's recommendation.

- Invoke `chart-annotations` whenever the chart plausibly has a point worth marking; the skill itself judges whether any mark clears the bar, ranks candidates, words the label, and places it - or leaves the chart unmarked and puts the finding in the title. Do not annotate by default and do not skip the skill's judgment.
- Compose the headline and subhead here. There is no dedicated skill: `chart-annotations` decides the claim the title asserts, `karthik-data-visualization` sets title/subtitle style, and the installed writing or brand-style skill, if available, sets the voice. Load a writing/brand skill only if it exists in this environment; if none is installed, apply the prompt's stated preferences and skip.

Honour every prompt constraint - requested chart type, annotations, wording, preferences - even while redesigning everything the prompt left open. Produce one PNG, SVG, or PDF from reproducible R, Python, JavaScript, or editable vector code. Reuse the project's renderer when one exists; otherwise prefer ggplot2 when available, but do not delay output for a renderer preference.

For a `bounded-edit`: skip the cold selection, apply the named edit to the source form, and re-render - staying anchored is the point.

### 5. Critique - the downstream checker loop

Now, and only now, run `dataviz-critique` on the exact export at its delivery size, in this same chat. Critique here is a **checker**, not a designer: it does not re-derive the messages (the brief owns those) and it does not reopen the form choice unless the candidate genuinely fails a message. It answers two questions:

- **Does the candidate carry the step-1 intent?** Every key message present, with its required content; nothing key silently dropped; prompt constraints honoured.
- **Is it a good chart?** Mechanical (clipping, collisions, typography hierarchy, label-to-mark association, duplicated scaffolding, missing categories/periods/units, colour and contrast) and semantic (measure, denominator/universe, time/context, claim strength, units).

Use `render_and_inspect_chart` when available. If the MCP tool fails, render locally and inspect visually, and state that deterministic inspection was unavailable. Never invent layout metadata or claim an incomplete check is complete.

Consolidate the issues into one focused revision and reinspect the changed regions and their neighbours. **Cap the loop at two passes.** Exit as soon as no fatal or major defect remains; minor polish does not justify another pass. This checker is the same session that built the chart, so it catches mechanical defects well and conceptual blind spots poorly - that is what step 6 is for.

### 6. One independent evaluation

Spawn **exactly one** subagent to run `dataviz-eval` as a blind reviewer on the converged candidate. This is the only spawn in the flow.

- Give it only: the rendered artifact and a short brief (the prompt, the inferred style, the inferred headings and subheadings, and the intended message). Do **not** give it the source image, the maker's diagnosis, or the rendering code - withholding these is what keeps the read blind and stops it anchoring on the original.
- It returns one verdict and ranked findings. It does not render, does not iterate, and is never re-spawned.
- **Skip this step** for a purely literal or cosmetic edit the maker can fully verify in-context.

### 7. One final revision

Apply at most one in-context revision from the eval findings. Do not spawn again and do not re-enter the loop. If eval calls for a redesign that is expensive or structural, apply it when cheap; otherwise deliver the current candidate and surface eval's concern to the user in one sentence.

### 8. Deliver and continue

Deliver the artifact. Briefly state what changed and any inspection limitation that affects confidence. Then treat user feedback as the main release signal: change the smallest relevant part of the latest candidate, render again, inspect the named element, and return it. Do not restart from the source unless the user asks for a redesign or the current form cannot support the change.

## Optional case logging

Use `case_manager.py` only when the user wants an audit trail, comparison history, bounded benchmark, or reusable learning record. Case state never overrides the delivery anchor: if a valid artifact exists, deliver it with its actual status. When used, keep it minimal - start the case, record each rendered artifact, attach real inspection evidence when available, and record feedback and acceptance.

## Failure handling

- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic inspection.
- **Eval subagent failure:** deliver the inspected candidate as unreviewed and say so.
- **External resource constraint:** deliver the best candidate and name the unresolved issue.
- **Renderer failure with no artifact:** report the concrete error and return any earlier valid candidate.
- **Missing evidence:** preserve visible source values, avoid invented claims, and label the limitation.

## Learning after acceptance

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule or tool defect. Do not turn a chart-specific object, phrase, layout, or count into a universal rule. Express reusable lessons as relationships or decision tests, and keep case-specific details in the case record. Prefer simplifying or repairing the failing step over adding prose, schemas, or tests.
