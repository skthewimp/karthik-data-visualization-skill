---
name: dataviz-execution
description: Post-render gate that critiques a built chart's execution - geometry, overlap, labels, colour, precision, and ink - not its idea.
---

# Dataviz Execution

The **post-render gate** of the construct process. It receives the built candidate at its
delivery size and checks the **rendering, not the idea**. The idea gate already decided the
chart is the right chart saying the right thing; this stage decides whether the actual export
is clean enough to hand a reader. Judgement here needs the pixels - which is exactly why it
runs *after* build, where the idea gate ran before it.

## Check the execution

Inspect the exact export at the declared delivery size and find every consequential defect:

- **Geometry:** clipping, elements running off the canvas, misalignment, overlapping marks or
  text, collisions between labels, labels and axes, or panels.
- **Association:** every label, value, and annotation clearly tied to the mark it belongs to;
  no legend round-trips where a direct label would read.
- **Hierarchy and scaffolding:** the title, subtitle, and emphasis read in the intended order;
  no duplicated axes, redundant gridlines, or leftover default furniture.
- **Colour:** sufficient contrast against the background, series distinguishable, and the
  palette surviving grayscale and common colour-vision deficiencies - not reliant on
  red/green alone.
- **Precision as displayed:** the number of digits shown matches the decided plan (the spread
  rule, or an exact-lookup override with its reason) - no fabricated or ragged precision.
- **Eraser test:** remove any ink that carries no data, no label, and no necessary context.

## Rendering and inspection

Use `render_and_inspect_chart` when it is available - it gives deterministic geometry from the
exact export. If it fails or is unavailable, render locally, inspect the export visually, and
**say deterministic inspection was unavailable**; never describe an incomplete check as
complete or fabricate metadata.

## Flow check before craft

Before judging a **redesign** candidate, confirm the build carries a recorded cold form
decision. A redesign that is a tidied re-render of the source form with no form choice behind
it is a flow violation on its own - route it back to `select` to choose the form cold and
rebuild, rather than polishing the wrong chart. (A `bounded-edit` legitimately keeps the source
form; it records the retained form and is not a violation.)

## Loop, routing, and delivery

Consolidate the defects into **one focused revision**, re-render, and re-inspect the changed
regions and their neighbours. Exit as soon as no fatal or major defect remains. **How many
revision passes to run is the driver's budget, not a fixed number in this stage** - do not
bake a pass count into the work.

If the render reveals that the *idea* is wrong (the form cannot carry the claim after all, the
message does not land), route back to the idea gate rather than patching pixels.

Deliver the best valid candidate with a plain summary and any residual limitation. An
acceptance check left `unknown` because its external validation was unavailable is a footnote
in `residual_limitations`, not a defect, and never a reason to withhold - still return
`deliver`. Reserve `blocked` for a genuine inability to produce any valid artifact at all.

## Handoff

Emit the verdict, the summary, the delivered artifact path, the changes made, and the residual
limitations. The exact fields are `dataviz_mcp/stage_contracts.py:EXECUTION_SCHEMA`; this skill
carries the reasoning, that module the shape.
