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
| `REDUNDANT_VALUE_AXIS` | Every mark is directly labelled yet the numeric value axis still renders ticks - duplicate ink (fires from a declared direct-label contract, or from mark geometry per panel when a facet grid labels every mark but declares none) | Low |
| `REDUNDANT_COLOUR` | Colour only restates a grouping the facet, category axis, or direct labels already show (one series per facet, one fill per named bar, or labelled series) - focal-plus-grey stays silent | Low |
| `EXTERNAL_LEGEND` | A legend round-trips series the plot already names via direct labels, facet titles, or category ticks | Low |
| `UNIDENTIFIED_SERIES` | Two or more series are distinguished only by colour with no legend, direct labels, or facet titles - the reader cannot tell which is which; direct labels are the preferred fix | High |
| `UNDERFILLED_CANVAS` | The canvas carries too little ink for its size (`occupied_utilization_ratio` below threshold) - mostly empty layout | Low, or Medium when text is also undersized |

`passes_geometry_checks` is true only when metadata is present, supported checks are complete, and no high- or medium-severity defect remains.

Every geometry defect now also carries its fix vector, so a revision is a number rather than a guess: clipped elements report per-edge `overflow_px` and `grow_margin_px`; colliding labels report `separation_needed_px`; `panel_heights_px` and `min_panel_height_px` expose squashed facets; and a `geometry_summary` block ranks the worst offenders and computes `suggested_dims` from the same `layout.py` math the forward sizing tool uses. Forward and backward geometry share one vocabulary.

## Forward geometry (size and place before render)

Two deterministic tools size the canvas and place the text *before* the render, so a weak model does not clip, squash, or collide in the first pass and then spend its revision budget guessing dimensions. Both are mechanism only - they never choose the chart or write the annotation.

- `recommend_layout` returns `width_px x height_px x dpi`, a facet grid, x-label rotation, and reserved title/subtitle/footer bands from the chart's shape expressed as counts (`x_slots` / `y_slots`, `filled_marks`, `n_panels`, line counts). Sizing is one rule - each axis needs `slots x per_slot_floor` px, a continuous axis takes a pleasant aspect, faceting multiplies via an aspect-fill grid, `y_slots` grows height while `x_slots` grows width and then triggers rotation. Demand past the delivery ceiling is warned, never squashed. No regime enum, no count thresholds.
- `recommend_text_placement` wraps every text block to fit its room and parks each movable label beside the mark it names. Text is placed in priority order so the least-free claims its spot first: data labels, then category/series labels, then free annotations. A movable label's `anchor` is the **mark**, and the box parks one small gap beside it - preferred side first (`placement` = right/above/below/left, default right) - with **no leader line**. A `label` may pass `anchors`, a list of candidate marks (e.g. several points along its line); it sits beside whichever is clear, since adjacency identifies the series, not the endpoint. Fixed roles (title/subtitle/footer/caption) sit at their anchor, wrapped, never moved. Role `data_label` is an on-mark label the plotting layer already centred on its mark (a stacked-bar segment value): wrapped, never moved, and exempt from obstacle de-collision - do not pass its own bar as an obstacle, or it is shoved off the segment it belongs on. `obstacles` are the data marks' bounding boxes - movable labels are always parked clear of them. Only when no adjacent spot exists at any of a label's marks does it travel to the nearest clear area (shrinking toward `min_font_pt`, default 8pt, the legibility floor, never below, if needed) and return a `leader_line` (`{from,to}` in canvas px) for the builder to draw as a thin connector back to its point. Returns each block's wrapped text and final `bbox` (authoritative - the anchor was the mark), plus `suggested_anchor` / `suggested_font_pt` / `suggested_wrap` when it changed side, mark, or size; a label parked on its preferred side carries none of those and no leader. When two moved labels land on each other's side so their leader lines cross, they are swapped back toward their own marks - each trades position with the other - whenever the swap keeps both boxes clear of every mark and label. It also returns a top-level `redundant_annotations` list (`{id, restated_value, data_label_id}`): a free annotation whose single data value a nearby `data_label` already prints only restates it and is recommended for removal; a comparison naming two values, or a computed delta whose number is on no label, is never flagged. When a landscape canvas stays too cramped even after moving and shrinking, it returns a canvas-level `suggested_orientation: "portrait"` and swapped `suggested_canvas` - advisory, for a later build stage to apply, re-render, and re-run against the new mark geometry.
- Every series/category, on-mark data, and axis label must carry the builder's readability judgment as `max_width_px` and `max_lines`, chosen from the delivery condition, density, and available region rather than inherited from the annotation allowance of 32% of canvas width. Curtailment is opt-in with `allow_curtail: true`; it returns ellipsized `wrapped_text`, `curtailed: true`, and intact `full_text`, which must appear in a compact key/footnote. Without permission, an over-budget label remains intact and returns `over_line_budget: true` for layout, wording, or form revision.
- `recommend_labels` selects *which* points on each series to label directly, within a per-series budget: endpoints and extremes first, then the largest step-to-step changes. "Keep every value" is a request to preserve every value in the data (table/note), not to print every value as ink - stamping all of them collides. It selects points, not placement; feed the chosen anchors to `recommend_text_placement`. `dataviz_mcp/labels.py`.

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
| `dataviz_mcp/layout.py` | Forward canvas sizing (`recommend_layout`) and shared geometry primitives |
| `dataviz_mcp/text_fit.py` | Forward text wrapping and annotation de-collision (`recommend_text_placement`) |
| `dataviz_mcp/labels.py` | Direct-label point selection within a budget (`recommend_labels`) |
| `dataviz_mcp/comparison.py` | Hash-validated revision comparison |
| `dataviz_mcp/server.py` | Stdio MCP surface (render, inspect, compare, and the recommend_* resolution tools) |
| `dataviz_mcp/review_views.py` | Full, delivery, panel, hierarchy, and dense-placement views |
| `dataviz-fix/*/scripts/case_manager.py` | Versioned case state and inspection/evaluation binding |
| `tester/local_runner.py` | Staged repair cycle (diagnose/select/build), inspection, and blind review |
| `dataviz_mcp/tests/` | Capability, protocol, geometry, and coffee repair tests |

Installation, client registration, tool parameters, and the chart-builder contract are in [`dataviz_mcp/README.md`](../dataviz_mcp/README.md).
