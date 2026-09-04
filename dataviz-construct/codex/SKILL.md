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
                                \-> explain   (off the finding, when the exhibit ships with prose)
```

- **Creation** hands in after `clean`.
- **Repair** hands in after `diagnose+extract`.
- A repair **`bounded-edit`** (a literal, self-contained change that keeps the source form -
  "recolour series 3", "fix the axis labels") skips `insight -> select -> idea` and goes
  straight to `build -> execution`, because the claim and the form are unchanged on purpose.
- **`explain`** is not on the render path. It writes the accompanying note from the finding and
  the plan, needs no chart, and runs in parallel with build/execution - only when the plan ships
  with prose.

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
4. **Build** - one builder skill, chosen by `select.builder`: `karthik-data-visualization` for
   a chart or `karthik-table-style` for a table, never both. The build call differs by what is
   built: a chart may also load `chart-annotations` (on-chart marks - chart-only, never a
   table). That is the only conditional skill build carries. Colour, precision, and the
   explainer note load no skill here - colour and precision are decided at select and resolved
   by a tool (see below), and the note is written off the render path by the explain stage.
   Assert the headline claim in the title; word and place the annotation claims the insight
   stage named. Render one real artifact.
5. **Execution-critique** - `dataviz-execution`. The **post-render gate**: geometry, overlap,
   labels, colour, precision, ink. Route back to `build`, or - rarely - to `idea` if the render
   shows the idea itself is wrong.
6. **Explain** (`chart-explainer`, only when `select.needs_explainer`) - the short note that
   travels beside the exhibit. Written from the finding (the insight artifact) and the plan, not
   from the render - so it needs no chart and runs in parallel with build/execution, not inside
   the build call. A null result is an honest note.

## Colour and precision are decided at select, resolved by a tool, only applied at build

Neither is a build judgment. Each splits three ways so a weak build model decides nothing about
it and the two heaviest skill bodies (`dataviz-color`, `dataviz-precision`) never enter the
build call:

- **Decision (at `select`, and for claim-text numbers at `insight`).** *Precision*: the only
  judgment - exact digits versus the spread rule - is one `exact_lookup_required` flag per
  display group; numbers inside the headline or an annotation get their precision at `insight`,
  where the value is computed. *Colour*: the `colour_plan` names the available source
  (brand skill / prompt / source-extracted / accessibility default), the focal series, and any
  semantic meaning a series carries - decided at select as compact fields, not by loading the
  colour skill there. `colour_groups` and `colour_role` are already select's too.
- **Resolution (a deterministic tool).** `recommend_precision` turns values + the flag into a
  format; `recommend_colours` turns the colour_plan into an ordered palette, checked by
  `validate_palette`. The driver runs these between select and build (or build calls them).
  `needs_precision_plan` / `needs_color_plan` are the triggers - not signals to load a skill.
- **Application (at `build`).** Build applies the resolved format to every axis, label, and
  table cell (reproducing claim-text numbers verbatim), and assigns the resolved palette in its
  order. It re-decides neither. In a table the same resolved per-column format is what
  `karthik-table-style` aligns to. `dataviz-execution` still re-checks colour contrast and
  CVD/grayscale on the render as the post-build safety net.

## Canvas size and text placement are resolved by tools, not eyeballed

Geometry is mechanism, not build judgment - the same split as colour and precision. A weak model
that guesses canvas dimensions clips titles, squashes facets, and collides annotations. Where the
harness provides deterministic geometry tools, two of them remove the guess (described below).
Where it does not - the common case outside this repo's own harness, and for any renderer those
tools do not cover, such as a hand-authored HTML/SVG chart - the same guesses are settled by
rendering the export and inspecting it by eye at delivery size. The tool names below are this
repo's; read them as the mechanism, and apply the same checks visually when the tools are absent.

- **Canvas (at `select`, applied at `build`).** `recommend_layout` sizes a clip-safe
  `width_px x height_px x dpi`, a facet grid, and the x-label rotation from the chart's *shape*
  expressed as counts - `x_slots` / `y_slots` (discrete positions per axis, 0 = continuous),
  `filled_marks` (bar/tile vs point/line), `n_panels`, and the title/subtitle/footer line
  counts. It is one rule over counts, not a table of chart types: each axis needs
  `slots x per_slot_floor` px, a continuous axis takes a pleasant aspect, faceting multiplies via
  a grid, and any demand past the delivery ceiling is *warned*, never squashed. Feed its dims
  straight into `render_and_inspect_chart`. It sizes the box; it never picks the chart.
- **Frame (at `build`, blind - no render).** The chrome - title, subtitle, caption, footer,
  axis titles and ticks, legend - lives in the margins; where it sits does not depend on the
  data, so it is placed by text-measuring arithmetic *before the first render*, not discovered
  clipped after one. `reserve_frame` takes the raw frame strings plus the canvas and per-role
  font sizes (all inputs: pass `width_px`/`height_px`/`dpi`/`font_pt`, or take the profile
  defaults), wraps each block to the canvas width, reserves a pixel band per block, and returns
  the **`plot_area` rectangle** the marks may fill and the placed **`frame_blocks`** (roles the
  placement tools treat as fixed). Draw the marks into `plot_area`; a frame too big for the
  canvas is *warned*, never squashed. This is what removes clipped titles (the largest first-
  version defect) and the half-empty canvas - deterministically, with no revision loop and,
  for a chart with no on-mark labels, no extra render at all.
- **Data-glued labels (measure-then-place, at `build`).** A value stamped on a bar or a callout
  pointing at a peak sits at a pixel position that *does* depend on the data, so it cannot be
  placed blind. Do not guess its pixels and discover the collision after render - that guess is
  the revision loop. Instead render **once as a ruler**: the render's layout metadata carries the
  exact `data_to_pixel` `transform` and every mark's bounding box. Pass those, the labels in
  **data coordinates** (`data_x`/`data_y`), and the `frame_blocks` to `place_on_marks`; it
  projects each label to its true pixel spot, hands the marks in as obstacles, and de-collides
  through `recommend_text_placement` - so text-mark and text-text overlaps are gone on the first
  *delivered* chart, decided by geometry, not by the model's eye. Only charts that stamp labels
  on marks pay for the measure render; frame-only charts skip it. The transform is available on
  matplotlib always and on ggplot for any Cartesian plot - `coord_flip`, log/sqrt/reverse scales,
  and facets included (per panel). Only a non-Cartesian coord (polar/`coord_trans`/sf) or an
  unreproducible scale (date/logit/custom) emits none; there `place_on_marks` refuses - place
  those labels with the renderer's own repel (ggrepel) and verify with the execution gate.
- **Text engine (what the two front doors call).** `reserve_frame` and `place_on_marks` both
  resolve to `recommend_text_placement` - reach for it directly only when you already hold a
  block's canvas-pixel anchor and neither front door fits. Once the title, subtitle, caption, and
  annotations are written and their anchors chosen, `recommend_text_placement` wraps every block
  to fit its room and moves any annotation that would collide with another label, the canvas
  edge, **or a data mark** to the nearest clear spot - pass the marks' bounding boxes as
  `obstacles` so annotation-vs-data is de-collided every time, not just text-vs-text. A block with
  no clear spot at full size is shrunk toward the legibility floor (`min_font_pt`) before its wrap
  is tightened, so a cramped label returns a `suggested_font_pt`; and when a landscape canvas
  stays unresolvable it returns a `suggested_orientation: "portrait"` and swapped
  `suggested_canvas` for a later build stage to flip, re-render, and re-run. It returns the wrap,
  the moved anchor, the smaller size, and the flip; the model still owns which annotation to show
  and what it says.
- **Known text triggers placement.** Before the first render, pass every reader-facing block whose
  words and anchor are already known to `recommend_text_placement` and use its returned wrapping
  and placement. Derive this work from the blocks themselves; do not rely on a separate optional
  flag that can contradict the chosen design. For every series/category, on-mark data, and axis
  label, build decides and passes `max_width_px` and `max_lines` from the delivery condition,
  density, and available region; the tool enforces that judgment instead of inventing a universal
  character count. Set `allow_curtail: true` only when the intact `full_text` will also appear in
  a compact key or footnote. Otherwise an over-budget label stays intact and routes to layout,
  wording, or form revision.
- **Keep coordinate systems separate.** Data scales represent the intended data domain. Titles,
  labels, annotations, legends, and their whitespace live in layout/screen coordinates. Never
  change a quantitative scale merely to reserve room for non-data content, and never reserve the
  same room in both the data domain and the physical layout.
- **Backward check (at `execution`).** `inspect_rendered_chart` now reports the fix vectors for
  what it finds - per-edge `overflow_px` / `grow_margin_px`, `separation_needed_px`,
  `panel_heights_px`, and a `geometry_summary` whose `suggested_dims` is computed by the same
  layout math - so a weak model reads "grow the top by 14px" instead of judging by eye.

## The plan carries across the gate

The tail is not a straight pipe. `insight` names the headline claim and the candidate
annotations; `select` reads that and adds the form. But the `idea` gate emits a *critique*,
not a plan - so `build` cannot read the stage right before it for what to draw. The insight
artifact is the plan that has to persist **across** the gate: `idea` and `build` both receive
the insight artifact (its facts, headline claim, and candidate annotations) **and** the select
artifact. On a weak-model harness feed both forward explicitly - do not rely on the model to
remember the claim from two stages back. If only the select artifact reaches build, the
headline claim vanishes at the gate and the title gets improvised at build again, which is the
exact failure the insight stage exists to prevent. In `dataviz_mcp/stage_contracts.py` this is
`Stage.also_reads=("insight",)` on the `idea` and `build` stages.

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
that stage's skills plus the artifact handed forward. When nothing external is orchestrating
the calls - you were handed the plan and this skill in one turn - and you have a subagent / task
capability, **you become the driver** and dispatch each stage as its own isolated subagent call.
The isolation is the point: build (maker) and the idea / execution gates (checkers) must sit in
separate contexts, or a checker inherits and rationalises the build's shortcuts and the gates
stop biting. Only when you genuinely cannot spawn subagents do you fall back to walking every
stage inline in one context, opening each stage's skills as you reach it and letting the
previous stage's detail fall away; "separate call" is the architecture, never a licence to skip
a stage. Handoffs are structured
text (markdown sections plus, at the select branch, a small `routing` block of `key: value`
lines), not strict JSON, so the pipeline runs on cheaper / open-weight models too. The content
contract - the exact skill subset and required fields per stage - is the construct tail in
`dataviz_mcp/stage_contracts.py`; this skill carries the reasoning, that module the shape.
