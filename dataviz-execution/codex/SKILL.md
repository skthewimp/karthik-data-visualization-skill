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

The geometry verdict is not yours to eyeball. Run `render_and_inspect_chart` (or
`inspect_rendered_chart` on the exact export) - it gives deterministic geometry - and record what
it measured in the `inspection` block: the source tool, the smallest text size, the overlap
count, and whether anything is clipped. Only when the inspector genuinely cannot run (check
`probe_renderers`) may you fall back to a visual look; then set `geometry_source: visual-only`,
leave the measured numbers empty, and report geometry as **unknown** - never as a pass. A
`deliver` verdict can rest on a visual read of colour or ink, but its geometry claim must come
from the tool or be marked unknown. Never describe an incomplete check as complete or fabricate
metadata.

When the inspector flags a geometry defect it also hands you the fix vector, so a revision is a
number, not a guess: `geometry_summary.suggested_dims` (a grown `width_px`/`height_px` from the
same math `recommend_layout` uses), per-edge `overflow_px` / `grow_margin_px` on clipped
elements, `separation_needed_px` on colliding labels, and `panel_heights_px` /
`min_panel_height_px` for squashed facets. Apply the suggested dims and re-render rather than
nudging by eye; for colliding annotations, feed the marks back through `recommend_text_placement`
instead of hand-placing them. On-mark data labels are the exception: a value the plotting layer
already centred on its mark (a stacked-bar segment value, a point label) is position-fixed by the
data. Pass it as role `data_label` - wrapped, never moved - and never list its own bar in
`obstacles`. Only free callouts get de-collided; feeding segment values through obstacle-avoidance
shoves every one off its bar and clips them off-canvas.

A `REDUNDANT_VALUE_AXIS` flag (low severity, so it never blocks) is the eraser test made
mechanical: when every mark carries its own value label, the numeric value axis ticks and
gridlines are duplicate ink - drop them unless the axis still earns its place with a zero
baseline or a scale reference. Category (non-numeric) ticks are never flagged. It fires from a
declared direct-label contract, and also - for a facet grid that labels every mark but declares
nothing - from the mark geometry itself, once every mark-bearing panel carries a value label on
each of its marks.

An `EXTERNAL_LEGEND` flag and a `REDUNDANT_COLOUR` flag (both low, non-blocking) are the same
eraser test for the other two round-trips. Colour is duplicate ink when it only restates a
grouping the plot already encodes another way - one series per facet, one fill per named bar, or
series that already carry direct labels; drop it, or reserve it for a single focal series. A
legend is a round-trip whenever the series are already named on the plot - by direct labels
(however many lines share the panel), facet titles, or category ticks - so label them in place
and remove it. Both stay silent when colour or a legend genuinely carries what no other channel
does: several series crossing one panel with no direct labels, or a focal-plus-grey highlight
(fewer fills than bars). The trigger, not the severity, is what keeps those honest.

The `UNIDENTIFIED_SERIES` flag is the inverse failure, and it blocks (high). Colour can only
carry identity for several series if something keys it: a legend, direct labels, or facet
titles. Two or more series told apart by colour with none of those - no legend, no labels, no
per-facet naming - leave the reader unable to say which series is which. Every series needs
exactly one identity route: a redundant legend over already-labelled lines is an eraser-test
nicety, but zero routes is a real read failure. The fix is to label the lines directly
(preferred) rather than to add back a legend.

An `UNDERFILLED_CANVAS` flag (from the measured `occupied_utilization_ratio`) is the opposite
failure: the canvas is mostly empty. On its own it is a low suggestion - a single big number is
allowed to sit in space - but paired with undersized text it turns medium, the empty-and-tiny
layout that should be a denser view or the table the request asked for.

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

Emit the verdict, the summary, the delivered artifact path, the `inspection` evidence (the
geometry source and its measured numbers), the changes made, and the residual limitations. The
exact fields are `dataviz_mcp/stage_contracts.py:EXECUTION_SCHEMA`; this skill carries the
reasoning, that module the shape.
