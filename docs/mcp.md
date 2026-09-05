# Mechanical rendering and inspection through MCP

The motivating failure was not analytical. An agent produced a reasonable account of ten years of global coffee prices, but the delivered chart still had labels crossing the series, poor wrapping, and overlapping annotations. The skills already described what good annotation and evaluation looked like. What they lacked was a reliable way to test the file that had actually been rendered.

This MCP layer addresses that narrow problem. The skills still contain the judgement; the server supplies mechanical capabilities beneath them.

## Architectural boundary

| Layer | Owns |
|---|---|
| Skills and agent | Question, definitions, denominators, evidence, claim, chart choice, annotation significance and wording, critique, release verdict |
| MCP capabilities | Renderer adapters, export bundles, geometry metadata, exact-file hashing, clipping and collision checks, revision comparison |

The MVP deliberately does not include `profile_dataset` or `run_analysis`. There is no reusable profiler or query engine in this repo yet. Adding generic versions would create a second analytical stack instead of exposing existing reliable machinery.

It also does not make a `Send`, `Revise`, or `Redesign` decision. A collision detector cannot decide whether the title states the right claim, whether the comparison set is honest, or whether an event annotation implies causality without evidence.

## Renderer boundary

The MCP contract is backend-neutral through `render_and_inspect_chart`. It accepts trusted Python/Matplotlib or R/ggplot2 builders and emits one normalized bundle.

Renderer choice remains with the project and `karthik-data-visualization`:

1. An explicit user requirement overrides automatic selection.
2. Otherwise choose ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available and the adapter supports the requested output.
3. Use Matplotlib only when the probe fails or ggplot2 cannot produce the requested output, recording the reason in the manifest.
4. Specify every visible design choice rather than accepting either library's defaults.

`probe_renderers` returns executable/package availability, versions, supported source/output types, and failure reasons. The ggplot2 adapter uses `build_chart()` returning a ggplot or `list(plot, metadata)`, exports through `ragg`, and captures title, subtitle, legend, panel, text, plot, and footer zones from the drawn gtable/grob tree. Uncovered child geometry remains explicit rather than being converted into a pass.

## Why render metadata is primary

The renderer already knows where it placed axes, text, annotations, and paths. Recovering all of that from pixels would be less accurate and harder to test.

`render_and_inspect_chart` therefore produces one bundle:

```text
chart.png
chart-spec.json
layout-metadata.json
manifest.json
inspection.json
review-*.png
```

The PNG remains the deliverable and source of truth. `layout-metadata.json` records normalized geometry. `manifest.json` binds the artifact, spec, metadata, inspection, review views, renderer probe/selection, delivery profile, dimensions, and fallback reason.

`inspect_rendered_chart` rejects metadata whose artifact hash or dimensions do not match the PNG. If no metadata is available, it records the raster hash and dimensions but marks geometry checks incomplete. It does not convert an unknown result into a pass.

`refit_chart` closes the render -> inspect -> resize loop in code. When a first render clips the canvas edge or squashes its facet panels, the fix is not a judgement call - the inspector already reports the exact overflow in pixels and `suggest_dims_for_overflow` already turns it into a grown canvas. `refit_chart` runs that loop: render, inspect, and while a resize-fixable defect remains, grow the canvas by the measured overflow and re-render - up to `max_iterations`, honouring the delivery-profile ceiling (warned, never squashed) and stopping when a grow no longer reduces the residual. It fixes only what growing fixes (edge clipping, overflow, squashed panels); underfill has no exact shrink vector, so it is reported (`underfilled` + a warning) but never resized, and label collisions stay `place_on_marks`' job. `max_iterations`, `dimensions`, and `delivery_profile` are inputs with profile defaults. It returns the final artifact, inspection path, `final_dimensions`, a per-pass `history` (dimensions and residual metrics each pass), `warnings`, and a `resolved` flag - so a driver runs it deterministically first at the execution gate and escalates only the residual, non-resize defects to the model. `dataviz_mcp/refit.py`.

## Generation sequence

The intellectual stages remain unchanged:

```text
intake
→ analysis contract
→ data preparation
→ insight (facts + headline claim + candidate annotations)
→ chart selection
→ idea critique (pre-render gate: data / expression / insight / honesty)
→ chart spec
→ render bundle
→ execution critique (post-render gate; deterministic inspection of the exact PNG)
→ delivery
→ narrow repair from user feedback when required
```

Creation and repair share this tail from `insight` onward (`dataviz-construct`); they differ only in the front half that reaches it (a dataset, or a diagnosed source image).

When the chosen renderer is supported, pass the exact deliverable through the metadata-producing adapter and then exact-artifact inspection. When the appropriate renderer is not supported, inspect the exact export visually and keep missing geometry marked unknown. Use independent evaluation only for an explicit audit, high-risk decision, or benchmark. Metadata availability must not force a weaker visual implementation or suppress a valid artifact.

## Optional audited repair sequence

The default `dataviz-fix` path renders one candidate, inspects it once, and delivers it. It does not require a case record or independent evaluation. Use the sequence below only when the user requests an audit trail, a high-risk review, or a benchmark.

```text
render candidate
→ inspect exact artifact and matching metadata
→ attach the artifact and inspection hashes to the case iteration
→ issue the blind review request
→ run dataviz-eval against that exact version
→ reveal context only after the blind read
→ apply the minimum pass set
→ render and inspect again
→ stop when the release line passes
```

When used, the `dataviz-fix` state machine owns original, current, best, and historical artifacts. Case schema 14 requires critique, design, build, inspection, blind evaluation, revision/redesign, and user review records. It rejects:

- a bundle whose artifact, spec, or metadata hash no longer matches;
- layout metadata whose internal artifact hash names a different PNG;
- an inspection report for a different artifact;
- an evaluation that cites the wrong deterministic inspection hash;
- a first build without critique and a complete design contract;
- a `Revise` build that omits an open evaluator action or user correction;
- a `Redesign` build without a fresh critique and chart-selection decision when form is implicated;
- an unexplained Matplotlib render when auto could use ggplot2;
- a `Send` verdict while a known high- or medium-severity deterministic defect remains.

The independent evaluator receives named defects and element IDs rather than a clean-looking overview alone. A failed check becomes part of the minimum pass set. The repairer fixes those mechanical failures before reopening broader design choices, preserves elements that already pass, and stops when the pass line is met.

## Mechanical checks

Inspection reports the original five codes plus hierarchy, mark, delivery, contrast, and completeness defects, including:

| Code | Meaning | Severity |
|---|---|---|
| `OUT_OF_BOUNDS` | A rendered text element extends outside the canvas | High |
| `TEXT_CLIPPED` | An annotation or label crosses an active plot clipping boundary | High |
| `LABEL_LABEL_COLLISION` | Two annotation boxes intersect | High |
| `ANNOTATION_SERIES_COLLISION` | An annotation box intersects a recorded line path | High |
| `LONG_UNWRAPPED_ANNOTATION` | Annotation text exceeds the configured character limit without a line break | Medium |
| `HIERARCHY_TEXT_COLLISION` | Title, subtitle, panel heading, or footer text overlaps another text zone | High |
| `LEGEND_TEXT_COLLISION` | Legend geometry overlaps neighbouring text | High |
| `TEXT_MARK_COLLISION` | Text intersects a bar, point, patch, or common collection without inside-label intent | High |
| `DELIVERY_TEXT_TOO_SMALL` | Text is below the configured delivery-scale size | Medium |
| `LOW_TEXT_CONTRAST` | Text contrast misses the practical delivery target | Medium |
| `DIRECT_LABELS_INCOMPLETE` | A declared repeated-panel/direct-label count is incomplete | High |
| `REDUNDANT_VALUE_AXIS` | The declared reading-carrying marks are directly labelled (contract path), or - with no contract - every mark-bearing panel labels at least two of its marks (two labels fix the linear scale), yet the numeric value axis still renders ticks - duplicate ink | Medium |
| `REDUNDANT_COLOUR` | Colour only restates a grouping the facet, category axis, or direct labels already show (one series per facet, one fill per named bar, or labelled series) - focal-plus-grey stays silent | Low |
| `EXTERNAL_LEGEND` | A legend round-trips series the plot already names via direct labels, facet titles, or category ticks | Low |
| `UNIDENTIFIED_SERIES` | Two or more series are distinguished only by colour with no legend, direct labels, or facet titles - the reader cannot tell which is which; direct labels are the preferred fix | High |
| `CELL_OVERFLOW` | Table text exceeds its cell; revise wrapping or cell geometry | High |
| `UNDERFILLED_CANVAS` | The canvas carries too little ink for its size (`occupied_utilization_ratio` below threshold) - mostly empty layout | Low, or Medium when text is also undersized |

`geometry_status` distinguishes pass, fail and incomplete coverage. Nested table text is
measured individually; unsupported grobs/viewports leave coverage incomplete. Display-size
font checks use the exact PNG DPI and supplied container width.

`passes_geometry_checks` is true only when metadata is present, supported checks are complete, and no high- or medium-severity defect remains.

Every geometry defect now also carries its fix vector, so a revision is a number rather than a guess: clipped elements report per-edge `overflow_px` and `grow_margin_px`; colliding labels report `separation_needed_px`; `panel_heights_px` and `min_panel_height_px` expose squashed facets; and a `geometry_summary` block ranks the worst offenders and computes `suggested_dims` from the same `layout.py` math the forward sizing tool uses. Forward and backward geometry share one vocabulary.

Each defect also carries a `defect_class`, and the report groups the defects into a `correction_plan` with three classes, so the cycle routes deterministically instead of the model re-deriving the split each turn: **canvas** - clipping/overflow the canvas can grow out of, resolved by `refit_chart` and only when the group's shared `growth_vector` (the same `suggested_dims`) is non-null; **placement** - a local text move the geometry tools compute exactly (collisions, an over-long unwrapped annotation, a missing direct label, and a label crossing the *plot* boundary, which canvas growth cannot fix), resolved by `place_on_marks` / `recommend_text_placement` / `recommend_labels` and applied literally; **semantic** - a judgement only the model makes (contrast, redundant ink, an external legend, an unidentified series, undersized text, an underfilled canvas). A new defect code without a class is a test failure, not a silent default.

## Forward geometry (size and place before render)

Deterministic tools size the canvas, reserve the frame, and place the text *before* (or with a single measure render), so a weak model does not clip, squash, or collide in the first pass and then spend its revision budget guessing dimensions. `reserve_frame` settles the chrome blind and `place_on_marks` settles on-mark labels from one measure render - between them the top four first-version defects (clipping, text-text, text-mark, underfill) are decided by geometry, not by the model's eye. All are mechanism only - they never choose the chart or write the annotation.

- `recommend_table_layout` measures formatted headers/cells with grid/ragg font metrics,
  returns widths, wrapped strings, row heights, fonts and concrete continuation pages.
  It holds type size and splits content rather than treating columns as chart slots.
  Supply screen display width and a displayed text minimum to account for downscaling.
  Treatment comes from the table skill's reading task, not a column-count heuristic.
  See [table tool inputs and example](../dataviz_mcp/README.md#recommend_table_layout).
- `recommend_layout` returns `width_px x height_px x dpi`, a facet grid, x-label rotation, and reserved title/subtitle/footer bands from the chart's shape expressed as counts (`x_slots` / `y_slots`, `filled_marks`, `n_panels`, line counts). Sizing is one rule - each axis needs `slots x per_slot_floor` px, a continuous axis takes a pleasant aspect, faceting multiplies via an aspect-fill grid, `y_slots` grows height while `x_slots` grows width and then triggers rotation. Demand past the delivery ceiling is warned, never squashed. No regime enum, no count thresholds.
- `recommend_text_placement` wraps every text block to fit its room and parks each movable label beside the mark it names. Text is placed in priority order so the least-free claims its spot first: data labels, then category/series labels, then free annotations. A movable label's `anchor` is the **mark**, and the box parks one small gap beside it - preferred side first (`placement` = right/above/below/left, default right) - with **no leader line**. A `label` may pass `anchors`, a list of candidate marks (e.g. several points along its line); it sits beside whichever is clear, since adjacency identifies the series, not the endpoint. Fixed roles (title/subtitle/footer/caption) sit at their anchor, wrapped, never moved. Role `data_label` is an on-mark label the plotting layer already centred on its mark (a stacked-bar segment value): wrapped, never moved, and exempt from obstacle de-collision - do not pass its own bar as an obstacle, or it is shoved off the segment it belongs on. `obstacles` are the data marks' bounding boxes - movable labels are always parked clear of them. Only when no adjacent spot exists at any of a label's marks does it travel to the nearest clear area (shrinking toward `min_font_pt`, default 8pt, the legibility floor, never below, if needed) and return a `leader_line` (`{from,to}` in canvas px) for the builder to draw as a thin connector back to its point. Returns each block's wrapped text and final `bbox` (authoritative - the anchor was the mark), plus `suggested_anchor` / `suggested_font_pt` / `suggested_wrap` when it changed side, mark, or size; a label parked on its preferred side carries none of those and no leader. When two moved labels land on each other's side so their leader lines cross, they are swapped back toward their own marks - each trades position with the other - whenever the swap keeps both boxes clear of every mark and label. It also returns a top-level `redundant_annotations` list (`{id, restated_value, data_label_id}`): a free annotation whose single data value a nearby `data_label` already prints only restates it and is recommended for removal; a comparison naming two values, or a computed delta whose number is on no label, is never flagged. When a landscape canvas stays too cramped even after moving and shrinking, it returns a canvas-level `suggested_orientation: "portrait"` and swapped `suggested_canvas` - advisory, for a later build stage to apply, re-render, and re-run against the new mark geometry.
- Every series/category, on-mark data, and axis label must carry the builder's readability judgment as `max_width_px` and `max_lines`, chosen from the delivery condition, density, and available region rather than inherited from the annotation allowance of 32% of canvas width. Curtailment is opt-in with `allow_curtail: true`; it returns ellipsized `wrapped_text`, `curtailed: true`, and intact `full_text`, which must appear in a compact key/footnote. Without permission, an over-budget label remains intact and returns `over_line_budget: true` for layout, wording, or form revision.
- `recommend_labels` selects *which* points on each series to label directly, within a per-series budget: endpoints and extremes first, then the largest step-to-step changes. "Keep every value" is a request to preserve every value in the data (table/note), not to print every value as ink - stamping all of them collides. It selects points, not placement; feed the chosen anchors to `recommend_text_placement`. `dataviz_mcp/labels.py`.
- `reserve_frame` places the chart's chrome - title, subtitle, caption, footer, axis and legend bands - **blind, with no render**, because chrome lives in the margins and its position does not depend on the data. It wraps each raw frame string to the canvas width, reserves a pixel band per block, and returns the `plot_area` rectangle the marks may fill plus placement-ready `frame_blocks` (fixed roles). Canvas size, dpi, and per-role font sizes are all inputs (`width_px`/`height_px`/`dpi`/`font_pt`, else the delivery-profile defaults); a frame too big for the canvas is warned, never squashed. This removes clipped titles (the largest first-version defect) and the half-empty canvas deterministically, and for a chart with no on-mark labels costs no render at all. `dataviz_mcp/frame.py`.
- `place_on_marks` places labels glued to specific marks (a value on a bar, a callout on a point) using their **real pixel positions instead of a guess**. After one measure render, the layout metadata carries the exact `data_to_pixel` `transform` and every mark's bounding box; this projects each label's `(data_x, data_y)` through the transform, hands the marks in as obstacles, and delegates to `recommend_text_placement`. So text-mark and text-text overlaps (59% and 67% of first versions) are de-collided against where the marks actually landed, on the first *delivered* chart, rather than after a revision loop. Pass `transform` and `marks` straight from the render's layout metadata and `frame_blocks` from `reserve_frame`; returns everything `recommend_text_placement` returns plus `projected_anchors`. It also inverts its own affine to hand the builder **native data coordinates** for every movable label - `placed_data` (the label box's top-left corner, drawn left/top-anchored), `anchor_data` (the mark), and, when a leader is drawn, `leader_line_data` (`{from, to}`, the box-edge end and the mark end) - so a data-space `geom_segment`/`annotate` is drawn from exact coordinates instead of an improvised `xend`/`yend` that misses the mark and runs the connector through a neighbour; the leader terminates at the label's bounding-box edge and the mark, and a singular affine omits the data coordinates rather than fabricating them. Pass `plot_area` (from `reserve_frame`) and a movable label left straddling the plot boundary is nudged wholly inside - a clip canvas growth cannot fix - carrying the exact `plot_boundary_correction` `{dx, dy}` applied. Both renderers supply the transform: matplotlib always (from `transData`), and the ggplot2 adapter for any `CoordCartesian` plot - `coord_flip` included (the affine carries cross terms, since the flip maps x to the vertical axis and y to the horizontal), log/sqrt/reverse scales (each panel also carries its `x_trans`/`y_trans`, which `place_on_marks` applies before the affine because the affine lives in the scale-transformed space), and facets (one transform per panel, keyed to that panel's `axes_id`, so free scales resolve per panel). A non-Cartesian coord (`coord_trans`, polar, sf) or an unreproducible scale transform (date, logit, custom) emits no transform on purpose, and `place_on_marks` then refuses rather than project through a wrong map - route those labels through the renderer's own repel (ggrepel) and verify with `inspect_rendered_chart`. `dataviz_mcp/text_fit.py`.

Current collision coverage is deliberately honest:

- Matplotlib text, lines, bars, patches, points, and common collections are supported;
- ggplot2 drawn gtable tracks, panels, and common rect, point, polygon, polyline, and text grobs are supported while uncommon grobs remain named limitations;
- the report sets `checks_complete` false for uncovered geometry;
- raster-only inspection does not attempt OCR or infer hidden geometry from pixels.

## Revision comparison

`compare_chart_artifacts` validates both artifact hashes before comparing them. It reports:

- resolved, introduced, and persistent defects;
- before-and-after blocking defect counts;
- dimensions and pixel-change measurements;
- `mechanically_improved`, which is true only when blocking defects fall and no new defect is introduced.

This is a mechanical result, not a taste score. A substantively worse chart can still have fewer collisions, so the skills and independent evaluator retain the final decision.

## Tested failure cases

The core suite creates deterministic fixtures for:

- an annotation crossing a line;
- two annotation boxes overlapping;
- an annotation outside the canvas;
- clipped text;
- long unwrapped annotation text;
- a clean chart;
- missing-data line segments, to prevent false bridges across `NaN` gaps;
- uncommon or adapter-unsupported marks, to verify that incomplete coverage stays explicit.

The end-to-end coffee fixture renders a deliberately bad multi-annotation time series, detects four geometry defects, and records a `Revise` result in the real case state machine. It then changes annotation placement only, renders and inspects again, reaches zero defects, records `Send`, and moves the case to `user_review`. The comparison report confirms that the second artifact resolves the failures without introducing a new one.

## Implementation map

| Path | Responsibility |
|---|---|
| `dataviz_mcp/rendering.py` | Trusted builder execution and metadata-first render bundle |
| `dataviz_mcp/inspection.py` | Exact-artifact geometry checks, defect report, and fix vectors |
| `dataviz_mcp/refit.py` | Deterministic render -> inspect -> grow loop that clears clipping/overflow/squash (`refit_chart`) |
| `dataviz_mcp/layout.py` | Forward canvas sizing (`recommend_layout`) and shared geometry primitives |
| `dataviz_mcp/frame.py` | Blind frame reservation - plot rectangle from title/axis/legend text (`reserve_frame`) |
| `dataviz_mcp/text_fit.py` | Forward text wrapping and annotation de-collision (`recommend_text_placement`), plus data-coord label placement from a measure render (`place_on_marks`) |
| `dataviz_mcp/labels.py` | Direct-label point selection within a budget (`recommend_labels`) |
| `dataviz_mcp/palette.py` | Colour selection, assignment, WCAG/CVD scoring, and image sampling (`recommend_colours`, `validate_palette`, `extract_palette_from_image`); uses `color_math.py` |
| `dataviz_mcp/precision.py` | Spread-derived significant digits for a numeric column (`recommend_precision`) |
| `dataviz_mcp/comparison.py` | Hash-validated revision comparison |
| `dataviz_mcp/server.py` | Stdio MCP surface (render, inspect, compare, and the recommend_* resolution tools) |
| `dataviz_mcp/review_views.py` | Full, delivery, panel, hierarchy, and dense-placement views |
| `dataviz-fix/*/scripts/case_manager.py` | Versioned case state and inspection/evaluation binding |
| `tester/local_runner.py` | Staged repair cycle (diagnose/select/build), inspection, and blind review |
| `dataviz_mcp/tests/` | Capability, protocol, geometry, and coffee repair tests |

Installation, client registration, tool parameters, and the chart-builder contract are in [`dataviz_mcp/README.md`](../dataviz_mcp/README.md).
