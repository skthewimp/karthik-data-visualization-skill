# Dataviz Construct

Use `dataviz-construct` when the job is bigger than one build call: a dataset and a loose question that should end as a visual story (**create**), or an existing chart that needs to be repaired and returned as a real artifact (**repair**). The two have their own front half and share one tail. The front half figures out *what to say and from what data*; the tail turns that into a finished chart.

```text
create:  discover -> contract -> clean ─┐
                                        ├─> insight -> select -> idea -> build -> execution
repair:  diagnose + extract ────────────┘                               \-> explain
```

- **`explain`** is off the render path: it writes the accompanying note from the finding and the plan, only when the exhibit ships with prose.
- A repair **`bounded-edit`** (a literal, self-contained change keeping the source form - "recolour series 3", "fix the axis labels") skips `insight -> select -> idea` and goes straight to `build -> execution`: the claim and form are unchanged on purpose.

## Front half: create

`dataset-question-generator` finds candidate stories (skipped when the claim is already sharp), `karthik-analysis-planner` pins down the metric, denominator, comparison and falsifiers, and `karthik-data-cleaning` makes the transformations visible. If the data can't answer the question, the question is narrowed at the contract stage rather than filled with invented fields.

## Front half: repair

**Repair is forward design, not critique-plus-patch.** Starting from a critique of the source anchors everything on the existing image and makes "re-render the same form, tidied" the path of least resistance. So one call loads `dataviz-critique` (in its repair-brief role) and `dataviz-extract`: the brief states the key messages and required content, explicit drops, audience, authoritative prompt constraints, and the edit-vs-redesign mode; extract recovers the full period-by-category table so any chosen form can be built.

Two anchors govern repair. A valid rendered candidate must always be delivered. And the repair may redesign freely against the input image - the source form gets no vote - while staying faithful to the prompt. Preserving a message is not preserving a form: the data and messages survive, the encoding usually should not. When cold selection returns a table, the repair builds it with `karthik-table-style` and gates it through the same render path as a chart.

## The stages

Each stage is one call loading only its own skill(s) plus the compact artifact handed forward. Loading every skill into one context rots it.

1. **Insight** - `karthik-evidence-builder`. Compute the facts and name the **headline claim** plus candidate annotation claims, from the data, before a form is chosen. The headline is decided here, not improvised at build.
2. **Select** - `dataviz-selector`. Choose the simplest form that makes the claim easiest to see and hardest to misread; for a repair, choose it **cold** (source form gets no vote). Hand forward the form plus these routing flags: `builder` (chart or table); `needs_annotations` (true only when insight named an external-fact annotation, not because the form could host one); `needs_explainer` (true only when the exhibit needs a note beside it); `needs_color_plan` (true when at least one series in a panel must be told apart or emphasised by colour - then write the `colour_plan` below); `needs_precision_plan` (true whenever numbers are shown - then one `exact_lookup_required` flag per axis, numeric column or labelled series, true only when the reader needs verbatim values such as codes or reference figures, with a one-line reason).
3. **Idea-critique** - `dataviz-idea-critique`. The **pre-render gate**: is the data right, the expression right, the insight right, honest? Route back to `insight` (wrong claim/evidence) or `select` (wrong form) until the idea holds.
4. **Build** - one builder skill from `select.builder`: `karthik-data-visualization` for a chart or `karthik-table-style` for a table, never both. A chart may also load `chart-annotations` (on-chart marks - chart-only, never a table); that is the only conditional skill build carries. Colour, precision, and the explainer note load no skill here (see below). Assert the headline claim in the title, word and place the annotation claims insight named, and render one real artifact.
5. **Execution-critique** - `dataviz-execution`. The **post-render gate**, run as one review then one correction then a verification: it finds the rendering defects (geometry, overlap, labels, colour, precision, ink) *and* the composition problems (first read, competing emphasis, unearned ink, whitespace) in the **same** review, consolidates both into one revision, and verifies it - no separate composition loop. Route back to `build`, or rarely to `idea` if the render shows the idea itself is wrong.
6. **Explain** (`chart-explainer`, only when `select.needs_explainer`) - the short note beside the exhibit, written from the finding and the plan (not the render), so it needs no chart and runs in parallel with build/execution. A null result is an honest note.

## Colour and precision: decided at select, resolved by a tool, applied at build

Neither is a build judgment. Each splits three ways so the build call decides nothing about it and the two heaviest skill bodies (`dataviz-color`, `dataviz-precision`) never enter it:

- **Decision (at `select`; claim-text numbers at `insight`).** *Precision*: the only judgment - exact digits vs the spread rule - is one `exact_lookup_required` flag per display group; numbers in the headline or an annotation get their precision at `insight`, where the value is computed. *Colour*: the `colour_plan` names the available source (brand skill / prompt / source-extracted / accessibility default, in that precedence) and its colours, the focal series (or none when every series competes), and a semantic colour only where this audience already reads one (a loss in red, a party colour), with an away-kit alternate.
- **Resolution (a deterministic tool).** `recommend_precision` turns values + the flag into a format; `recommend_colours` turns the colour_plan into an ordered, self-checked palette. Run these between select and build. Without the tools, apply the same rules by hand from the two skills.
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
- **Check the export (at `execution`).** Render at delivery size and look at the exact file: clipping, label collisions, squashed panels, text too small to read. Grow the canvas for clipping and squashed panels; everything else - collisions, hierarchy, colour, ink - goes back to build as one consolidated correction.

## The plan carries across the gate

The tail is not a straight pipe. `insight` names the headline claim and candidate annotations; `select` reads that and adds the form. But the `idea` gate emits a *critique*, not a plan - so `build` cannot read the stage right before it for what to draw. The insight artifact is the plan that must persist **across** the gate: `idea` and `build` both receive the insight artifact (facts, headline claim, candidate annotations) **and** the select artifact. On a weak-model harness feed both forward explicitly - don't rely on the model to remember the claim from two stages back. If only the select artifact reaches build, the headline claim vanishes and the title gets improvised again, the exact failure the insight stage exists to prevent.

One authoritative claim, not a copy per stage. The headline claim lives in the insight artifact; `select` and every later stage **reference** it, never restate a diverging version into their own handoff. When a stage narrows or rewords the claim, that edit routes back to `insight` so the one authoritative version changes - otherwise two handoffs carry two claims and a re-run has to reconcile them.

Revision is a bounded correction, not a fresh composition. When the idea gate returns `revise`, the stage it routes to (`insight` or `select`) receives **its own previous handoff** alongside the critique, and changes only what the critique names - preserving every part the critique left alone. "Preserve the unaffected part" is only possible if the stage is given the part to preserve; a revise call that withholds the prior draft forces a rewrite from scratch, which silently mutates settled decisions (palette source, layout wording, label rules) and hands the gate new things to object to. On the re-review after a revise, the gate also receives its **prior critique** so it can reconcile fixed / still-open / regression rather than restart cold (see `dataviz-idea-critique`).

## Two gates, in order

The idea gate runs **before** the chart is drawn; the execution gate **after**. That is the whole point of splitting them: no sense fixing label overlaps on a chart that is the wrong chart. Ideas can be judged from the plan and data (an LLM needn't see the render to know the form can't carry the claim), so that check comes first; execution can only be judged from pixels, so it comes second. Substance before craft.

## The loop is a unit; the driver owns the count

Post-render revision is recovery from unexpected defects, not the planned stage for resolving layout. Resolve known sizing and placement issues before the candidate render.

Each gate runs the same shape: **find everything wrong, decide the fixes, redo, re-check**. Whether that runs zero, one, or several times is the **driver's/harness's budget** - never a fixed pass count baked into this skill or any stage. Exit a gate as soon as no fatal or major defect remains; don't keep revising for taste past the pass line.

## Deliver a valid artifact

A valid rendered candidate must be delivered. Missing infrastructure, an unavailable optional evaluator, or an acceptance check left `unknown` for want of an external denominator or dataset must not suppress the best available output - disclose the limitation and still deliver. Reserve a blocked outcome for a genuine inability to produce any valid artifact.

## Delivery and feedback

Deliver the artifact with what changed and any inspection limitation. User feedback is then the main release signal: change the smallest relevant part of the latest candidate, render, inspect the named element, return it. Don't restart from the source unless a redesign is asked for or the current form can't support the change.

## Staged, not one context

Separate calls per stage is the default and the right way to run this: each call carries only that stage's skills plus the artifact handed forward. When nothing external orchestrates the calls - you were handed the plan and this skill in one turn - and you have a subagent/task capability, **you become the driver** and dispatch each stage as its own isolated subagent call. The isolation is the point: build (maker) and the idea/execution gates (checkers) must sit in separate contexts, or a checker inherits and rationalises the build's shortcuts and the gates stop biting. Only when you genuinely cannot spawn subagents do you fall back to walking every stage inline in one context, opening each stage's skills as you reach it and letting the previous stage's detail fall away; "separate call" is the architecture, never a licence to skip a stage. Handoffs are structured text (markdown sections plus, at the select branch, a small `routing` block of `key: value` lines), not strict JSON, so the pipeline runs on cheaper/open-weight models too.
