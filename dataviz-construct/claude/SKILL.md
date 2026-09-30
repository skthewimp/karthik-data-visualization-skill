---
name: dataviz-construct
description: Make a chart from a dataset, or repair one from an image - the staged pipeline (discover or diagnose, then insight, select, idea-critique, build, execution) that delivers a real artifact.
---

# Dataviz Construct

The staged pipeline for a chart that is bigger than one build call: raw data in and a visual story out (**create**), or an existing chart image in and a repaired artifact out (**repair**). The two have their own front half and share one tail. The front half figures out *what to say and from what data*; the shared tail turns that into a finished chart.

```text
create:  discover -> contract -> clean ─┐
                                        ├─> insight -> select -> idea -> build -> execution
repair:  diagnose + extract ────────────┘                               \-> explain
```

- **`explain`** is not on the render path. It writes the accompanying note from the finding and the plan, needs no chart, and runs in parallel with build/execution - only when the plan ships with prose.
- A repair **`bounded-edit`** (a literal, self-contained change keeping the source form - "recolour series 3", "fix the axis labels") skips `insight -> select -> idea` and goes straight to `build -> execution`: the claim and form are unchanged on purpose.

The workflow exists to produce an artifact, not to prevent one from reaching the user. Use the smallest relevant skill for each stage and keep one source of truth for each decision.

## Intake

Record the input (dataset, or source image), question/purpose, audience, medium, source constraints, and requested output. Distinguish user-supplied context from assumptions. If context is unavailable, proceed with an explicit assumption and state what the evidence can't support; don't suppress an otherwise valid artifact.

## Front half: create

Use when the task starts with a dataset and a loose question. Each stage is one call; load only the listed skill and pass the emitted artifact forward.

1. **Discover** - `dataset-question-generator`. In: dataset and context. Out: row grain, columns/types, likely denominators, candidate stories with the evidence each needs and its misleading risk, a recommended first story, and a "do not visualise yet" list. Skip when the user already has a sharp claim.
2. **Contract** - `karthik-analysis-planner`. In: discovery artifact and chosen story. Out: the operational question, metric, numerator/denominator, grain, the comparison that makes the number mean something, data requirements, falsifiers, caveats. Don't chart.
3. **Clean** - `karthik-data-cleaning`. In: contract and data. Out: visible transformations, validation results, provenance, remaining limitations. Don't invent fields or values.

If the data can't answer the question, narrow or reframe it at the contract stage. If a transformation changes the analytical meaning, return to contract. Then hand the cleaned data and contract to `insight`.

## Front half: repair

Use when an existing chart (image or artifact) needs to be repaired and returned. Two anchors:

1. **A valid rendered candidate must be delivered.** Missing infrastructure, an unavailable reviewer, or an imperfect score must not suppress the best available output. Label limitations honestly; don't relabel an unreviewed candidate as approved, but do send it.
2. **Redesign freely against the image; stay faithful to the prompt.** The input image is not sacred - the source form gets no vote. But any instruction arriving with it (requested chart type, annotations, what to fix, wording, brand/style) is authoritative and must survive the whole process. When the prompt and a redesign impulse conflict, the prompt wins.

**Repair is forward design, not critique-plus-patch.** Starting from a critique of the source anchors everything on the existing image and makes "re-render the source form, tidied" the path of least resistance. Extract the intent and data first, then let the tail compute the insight, select a form cold, build, and check. Preserving a message is not preserving a form: the data and messages must survive; the encoding usually should not when the source form was the weakness.

**Diagnose + extract** - one call loading `dataviz-critique` (its repair-brief role) and `dataviz-extract`. In: source image and any prompt. Out: the repair brief (key messages and required content, explicit drops with reasons, audience and medium, authoritative constraints, the **mode**) and the full period-by-category table (a value for every period and every category, series, stack, or facet - colour is data), so any chosen form can be built. Don't choose a form here. Difficulty of recovery is never grounds to drop a message or category - uncertain values and unreadable labels go in the limitations; the categories stay.

The mode governs the tail: **`bounded-edit`** applies the named edit to the source form at `build`, records the retained form, and checks at `execution`; **`redesign`** (the default when unsure) runs the full tail. In a redesign, insight names the headline claim **freshly** from the recovered data rather than inheriting what the source asserted, and select chooses the form **cold** - a table is a valid cold verdict.

## The stages

Each stage is one call loading only its own skill(s) plus the compact artifact handed forward. Loading every skill into one context rots it.

1. **Insight** - `karthik-evidence-builder`. Compute the facts and name the **headline claim** plus candidate annotation claims, from the data, before a form is chosen. The headline is decided here, not improvised at build.
2. **Select** - `dataviz-selector`. Choose the simplest form that makes the claim easiest to see and hardest to misread; for a repair, choose it **cold** (source form gets no vote). Set the routing flags (`builder`, `needs_annotations`, `needs_explainer`, `needs_color_plan`, `needs_precision_plan`) and the number-display decisions.
3. **Idea-critique** - `dataviz-idea-critique`. The **pre-render gate**: is the data right, the expression right, the insight right, honest? Route back to `insight` (wrong claim/evidence) or `select` (wrong form) until the idea holds.
4. **Build** - one builder skill from `select.builder`: `karthik-data-visualization` for a chart or `karthik-table-style` for a table, never both. A chart may also load `chart-annotations` (on-chart marks - chart-only, never a table); that is the only conditional skill build carries. Colour, precision, and the explainer note load no skill here (see below). Assert the headline claim in the title, word and place the annotation claims insight named, and render one real artifact.
5. **Execution-critique** - `dataviz-execution`. The **post-render gate**, run as one review then one correction then a verification: it finds the rendering defects (geometry, overlap, labels, colour, precision, ink) *and* the composition problems (first read, competing emphasis, unearned ink, whitespace) in the **same** review - not defects first and composition in a second loop - then consolidates both into one revision and verifies it. Route back to `build`, or rarely to `idea` if the render shows the idea itself is wrong.
6. **Explain** (`chart-explainer`, only when `select.needs_explainer`) - the short note beside the exhibit, written from the finding and the plan (not the render), so it needs no chart and runs in parallel with build/execution. A null result is an honest note.

## Colour and precision: decided at select, resolved by a tool, applied at build

Neither is a build judgment. Each splits three ways so the build call decides nothing about it and the two heaviest skill bodies (`dataviz-color`, `dataviz-precision`) never enter it:

- **Decision (at `select`; claim-text numbers at `insight`).** *Precision*: the only judgment - exact digits vs the spread rule - is one `exact_lookup_required` flag per display group; numbers in the headline or an annotation get their precision at `insight`, where the value is computed. *Colour*: the `colour_plan` names the available source (brand skill / prompt / source-extracted / accessibility default), the focal series, and any semantic meaning a series carries.
- **Resolution (a deterministic tool).** `recommend_precision` turns values + the flag into a format; `recommend_colours` turns the colour_plan into an ordered palette, checked by `validate_palette`. Run these between select and build. Without the tools, apply the same rules by hand from the two skills.
- **Application (at `build`).** Build uses the resolved palette and number format as given and re-decides neither; claim-text numbers are reproduced verbatim. In a table the same per-column format is what `karthik-table-style` aligns to. `dataviz-execution` still re-checks contrast and CVD/grayscale on the render as the safety net.

## Plotting data and copy: fixed before build

- **One tidy frame.** Decide which column is the category/x, the value, and any series and facet before writing chart code. Keep only the mapped columns, so a helper column cannot leak in as a plotted series, and use one canonical category/series order for every mark and label, so a value can never land on the wrong category. Build plots that frame; it does not reshape data inline.
- **Frozen copy.** The title (the insight headline claim, verbatim), subtitle, axis titles, direct labels, and annotation wording are settled before build and reproduced, not reworded. A copy-only defect at the execution gate is corrected in the copy alone, not by re-running the whole build.

## Canvas, frame and labels: let the renderer do it, then check the export

Geometry is where charts go wrong most visibly: clipped titles, squashed facets, labels on top of each other. Use the renderer's own layout rather than hand-computing pixels - in ggplot2, `plot.margin`, `ggrepel` for data-glued labels, `patchwork` for panels of different forms - and then look at the real export at delivery size.

- **Size the design that will be drawn.** Finalize copy, wrapping, legend position, and panel structure before choosing the canvas. A dense axis needs width; long category labels need a left band that doesn't starve the plot; small multiples need a grid that keeps every panel legible. Warn when a design doesn't fit - never squash it to fit.
- **Several panels are not one uniform grid.** An overview set apart from its detail, or panels of different forms or measures, get their own regions sized by what each holds; never flatten an overview and its detail into equally weighted cells.
- **Data-glued labels.** Values stamped on bars and callouts at peaks depend on the data. Draw them from the same data, grouping and position adjustment as their marks (dodge with dodged bars, stack with stacks) and let a repel layer keep them clear of each other and of the marks. Never guess a label's position separately from its mark.
- **Connected time series.** Group paths by series identity, not observation status. At an observed/projected transition, draw the connecting segment in the projected style. Missing values remain breaks; do not interpolate them or invent rows.
- **Keep coordinate systems separate.** Data scales represent the data domain; titles, labels, annotations, legends, and their whitespace live in layout coordinates. Never change a quantitative scale to reserve room for non-data content.
- **Check the export (at `execution`).** `render_and_inspect_chart` renders and measures the exact file: per-edge overflow, label collisions, squashed panels, text below the size floor. `refit_chart` grows the canvas in code when clipping or squashed panels are the only problem, so no model turn is spent on arithmetic. Everything else - collisions, hierarchy, colour, ink - goes back to build as one consolidated correction. Without the tools, render and inspect the export by eye at delivery size.

## The plan carries across the gate

The tail is not a straight pipe. `insight` names the headline claim and candidate annotations; `select` reads that and adds the form. But the `idea` gate emits a *critique*, not a plan - so `build` cannot read the stage right before it for what to draw. The insight artifact is the plan that must persist **across** the gate: `idea` and `build` both receive the insight artifact (facts, headline claim, candidate annotations) **and** the select artifact. On a weak-model harness feed both forward explicitly - don't rely on the model to remember the claim from two stages back. If only the select artifact reaches build, the headline claim vanishes and the title gets improvised again, the exact failure the insight stage exists to prevent.

One authoritative claim, not a copy per stage. The headline claim lives in the insight artifact; `select` and every later stage **reference** it, never restate a diverging version into their own handoff. When a stage narrows or rewords the claim, that edit routes back to `insight` so the one authoritative version changes - otherwise two handoffs carry two claims and a re-run has to reconcile them.

Revision is a bounded correction, not a fresh composition. When the idea gate returns `revise`, the stage it routes to (`insight` or `select`) receives **its own previous handoff** alongside the critique, and changes only what the critique names - preserving every part the critique left alone. "Preserve the unaffected part" is only possible if the stage is given the part to preserve; a revise call that withholds the prior draft forces a rewrite from scratch, which silently mutates settled decisions (palette source, layout wording, label rules) and hands the gate new things to object to. On the re-review after a revise, the gate also receives its **prior critique** so it can reconcile fixed / still-open / regression rather than restart cold (see `dataviz-idea-critique`).

## Two gates, in order

The idea gate runs **before** the chart is drawn; the execution gate **after**. That is the whole point of splitting them: no sense fixing label overlaps on a chart that is the wrong chart. Ideas can be judged from the plan and data (an LLM needn't see the render to know the form can't carry the claim), so that check comes first; execution can only be judged from pixels, so it comes second. Substance before craft.

## The loop is a unit; the driver owns the count

Post-render revision is recovery from unexpected defects, not the planned stage for resolving layout. Resolve known sizing and placement issues before the candidate render.

Each gate runs the same shape: **find everything wrong in one review, decide one consolidated correction, redo, verify**. At the execution gate "everything wrong" means the rendering defects **and** the composition problems named together in that one review (not defects first, composition second) - so a single revision handles both and a composition fix can't reopen a geometry defect a later loop would have to catch. Verification is a distinct step, not another review: it confirms the fixes landed, checks the touched regions for regressions, picks baseline-or-revision, and stops. Whether the correct-and-verify cycle runs zero, one, or several times is the **driver's/harness's budget** - never a fixed pass count baked into this skill or any stage. Exit a gate as soon as no fatal or major defect remains; don't keep revising for taste past the pass line.

## Deliver a valid artifact

A valid rendered candidate must be delivered. Missing infrastructure, an unavailable optional evaluator, or an acceptance check left `unknown` for want of an external denominator or dataset must not suppress the best available output - disclose the limitation and still deliver. Reserve a blocked outcome for a genuine inability to produce any valid artifact.

## Stop and escalation

- If the insight isn't supported by the facts, return to insight. If the visual form can't support the comparison, return to select. If the rendered artifact fails, send only the concrete issues back to build or the execution gate.
- A downstream stage may reject or narrow an upstream artifact, but must state the reason and return a concrete handoff.
- Renderer availability must not change the chart design or force a translation into a weaker implementation. When the chosen renderer has a metadata-producing capability, render the exact deliverable through it and inspect that export; when it doesn't, keep the renderer and inspect the exact export by eye, recording only what a picture can't settle (sub-pixel overlap, exact point size) as a limitation.
- **MCP failure:** fall back to direct local rendering and disclose the missing deterministic inspection. **Renderer failure with no artifact:** report the concrete error and return any earlier valid candidate. **Missing evidence:** preserve visible source values, avoid invented claims, label the limitation.

## Deliver and continue

Deliver the artifact; state what changed and any inspection limitation affecting confidence. Leave behind only what is useful for reproduction and review: source/analysis code, prepared-data notes when needed, the facts and headline claim, the select artifact, the exported media, and matching render/inspection records when available.

Then treat user feedback as the main release signal: change the smallest relevant part of the latest candidate, render again, inspect the named element, return it. Don't restart from the source unless the user asks for a redesign or the current form can't support the change.

After explicit acceptance, record a reusable lesson only when the miss reveals a general rule or tool defect. Don't turn a chart-specific object, phrase, layout, or count into a universal rule; prefer simplifying or repairing the failing stage over adding prose, schemas, or tests.

## Staged, not one context

Separate calls per stage is the default and the right way to run this: each call carries only that stage's skills plus the artifact handed forward. When nothing external orchestrates the calls - you were handed the plan and this skill in one turn - and you have a subagent/task capability, **you become the driver** and dispatch each stage as its own isolated subagent call. The isolation is the point: build (maker) and the idea/execution gates (checkers) must sit in separate contexts, or a checker inherits and rationalises the build's shortcuts and the gates stop biting. Only when you genuinely cannot spawn subagents do you fall back to walking every stage inline in one context, opening each stage's skills as you reach it and letting the previous stage's detail fall away; "separate call" is the architecture, never a licence to skip a stage. Handoffs are structured text (markdown sections plus, at the select branch, a small `routing` block of `key: value` lines), not strict JSON, so the pipeline runs on cheaper/open-weight models too.
