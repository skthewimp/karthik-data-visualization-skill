---
name: dataviz-fix
description: Repair an existing visualization quickly, return a real artifact, and improve it from concrete feedback.
---

# Dataviz Fix

Return an improved chart. The workflow exists to help produce an artifact, not to prevent one from reaching the user.

## Two anchors

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable reviewer, or an imperfect score must not suppress the best available output. Label limitations honestly; do not relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is not sacred - if a different form serves the question better, change it. But any instruction that arrives with it (requested chart type, annotations, what to fix, wording, brand or style preferences) is authoritative and must survive the whole process. When the prompt and a redesign impulse conflict, the prompt wins.

## Inputs

- The image or artifact to repair.
- The prompt, if any: the requested change, preferences, and constraints. Treat everything the user states here as a requirement, not a suggestion.

## Default workflow

### 1. Critique the source once

Run `dataviz-critique` in the current chat as a single pass. Do not spawn a reviewer, do not run a maker-checker on the critique, and do not iterate it - one critique, one output (JSON is fine). Using the prompt and image together, judge:

- **Right form?** Is this the right choice of visualisation for the question the prompt implies?
- **Trifecta** - question, data, visual, and their pairwise fit.
- **Message** - does the chart convey what it should, or invite a wrong reading? Run the semantic scan (measure, denominator/universe, time/context, claim strength, units).
- **Key messages and required content** - name the one or few messages the chart must carry, the content each message needs (series, periods, breakdowns, comparisons), and any source information dropped as *not* key, explicitly and with a reason. This is a judgment, not a keep-everything rule, and it may span more than one chart's worth of content. The chart's own form declares its messages: a stacked or multi-series chart has the category comparison as a key message. Do not drop that dimension because values are approximate, the legend is crowded, or exact precision can't be read from a screenshot - those call for a better form (small multiples, direct-labelled lines, top-N plus "other"), never deletion. See `dataviz-critique`'s "Key messages and required content".
- **Style** - what stylistic changes the prompt asks for, plus any installed writing or brand-style skill. Load that skill only if it is available in this environment; it is not part of this repository and many users will not have it. If none is installed, apply the prompt's stated preferences and skip.
- **Repair or redesign** - bias toward redesign. Choose repair only when the existing form already serves the question; when the form, evidence-to-claim fit, or comparison is weak, redesign.

In parallel, infer the raw data from the image thoroughly. Not the totals or the envelope - the full table: a value for every time period and every category, series, stack, or facet the chart encodes (colour is data, not decoration). List the category members explicitly. Use exact values when the prompt supplies them; mark screenshot-derived values as approximate unless they are clearly printed source labels. If a cell cannot be read, estimate and mark it approximate - but every cell in the period-by-category grid must exist. A chart that stacks ten models by week needs ten values per week, not one.

Do not build a design contract, semantic-preflight JSON, plan audit, case record, or review packet in the default path. The single critique above is the whole diagnosis stage.

### 2. Reconstruct

Rebuild from the critique, the prompt, the inferred data, and the inferred headings and style. Load:

- `dataviz-selector` by default, unless the source form is clearly correct and the prompt does not question it. A many-series stacked bar or area is *not* clearly correct when the key message is per-series comparison or trajectory - run the selector and expect a form change (small multiples, direct-labelled lines, a ranked or indexed view), not a re-render of the stack. Preserving the categories means keeping the data, not keeping the chart type: a cleaner version of the same illegible form is not a repair.
- `karthik-data-visualization` for implementation and Karthik-style defaults.
- `chart-annotations` whenever the chart plausibly has a point worth marking. Whether any mark is warranted is a judgment the skill itself makes: it decides what, if anything, clears the bar, ranks the candidates, words the label, and places it - or leaves the chart unmarked and puts the finding in the title. Do not annotate by default, and do not skip the skill's judgment either; invoke it and let it decide.

Compose the headline and subhead as part of this step. There is no dedicated skill for it; the authorship is split: `chart-annotations` decides the claim the title asserts (title vs annotation division of labour), `karthik-data-visualization` sets title/subtitle style (claim, question, measure, or honest null; subtitle carries the insight, not the mechanics), and the installed writing or brand-style skill, if available, sets the voice. Do not manufacture a claim to sound decisive; let the evidence choose the headline.

Carry every key message the critique identified, showing the required content it named for each. This can mean more than one chart - a whole-and-parts split, a totals view alongside a per-category breakdown; decide the chart count, decomposition, and form here, in reconstruction. Redesigning the form is encouraged - small multiples, lines, whatever serves the messages. Do not silently drop anything the critique judged key: collapsing a ten-category stacked chart into a bare total is a failure only because the breakdown carried a key message. Honour the critique's explicit drop decisions for information it judged not key. Preserving the source's value is a judgment about which messages must survive, made in the critique and executed here - not a rule to reproduce every mark, and not something a later reviewer is expected to catch.

Honour every prompt constraint - requested chart type, annotations, wording, and preferences - even while redesigning everything the prompt left open. Produce one PNG, SVG, or PDF from reproducible R, Python, JavaScript, or editable vector code. Reuse the project's renderer when one exists; otherwise prefer ggplot2 when available, but do not delay output for a renderer preference.

### 3. In-context checker loop

Critique the exact export at its delivery size, in this same chat, using `dataviz-critique`. Check clipping and collisions, typography hierarchy, label-to-mark association, duplicated scaffolding, missing categories/periods/units, colour and contrast, and whether every prompt constraint is honoured.

Use `render_and_inspect_chart` when available. If the MCP tool fails, render locally and inspect visually, and state that deterministic inspection was unavailable. Never invent layout metadata or claim an incomplete check is complete.

Consolidate the issues into one focused revision and reinspect the changed regions and their neighbours. **Cap the loop at two passes.** Exit as soon as no fatal or major defect remains; minor polish does not justify another pass. This checker is the same session that built the chart, so it catches mechanical defects well and conceptual blind spots poorly - that is what step 4 is for.

### 4. One independent evaluation

Spawn **exactly one** subagent to run `dataviz-eval` as a blind reviewer on the converged candidate. This is the only spawn in the flow.

- Give it only: the rendered artifact and a short brief (the prompt, the inferred style, the inferred headings and subheadings, and the intended message). Do **not** give it the source image, the maker's diagnosis, the claimed fixes, or the rendering code - withholding these is what keeps the read blind.
- It returns one verdict and ranked findings. It does not render, does not iterate, and is never re-spawned.
- **Skip this step** for a purely literal or cosmetic edit the maker can fully verify in-context.

### 5. One final revision

Apply at most one in-context revision from the eval findings. Do not spawn again and do not re-enter the loop. If eval calls for a redesign that is expensive or structural, apply it when cheap; otherwise deliver the current candidate and surface eval's concern to the user in one sentence.

### 6. Deliver and continue

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
