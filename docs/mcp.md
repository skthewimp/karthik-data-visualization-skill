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
2. Otherwise choose ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available. Probe before generating R or Python source.
3. Use Matplotlib only when that R backend is unavailable, recording the reason in the manifest. Do not switch after an R build error; fix the source. `auto` does not translate source languages.
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

`refit_chart` closes the render -> inspect -> resize loop in code. When a first render clips the canvas edge or squashes its facet panels, the fix is not a judgement call - the inspector already reports the exact overflow in pixels and `suggest_dims_for_overflow` already turns it into a grown canvas. `refit_chart` runs that loop: render, inspect, and while a resize-fixable defect remains, grow the canvas by the measured overflow and re-render - up to `max_iterations`, honouring the delivery-profile ceiling (warned, never squashed) and stopping when a grow no longer reduces the residual. It fixes only what growing fixes (edge clipping, overflow, squashed panels); underfill has no exact shrink vector, so it is reported (`underfilled` + a warning) but never resized, and label collisions stay placement fixes in the chart code. `max_iterations`, `dimensions`, and `delivery_profile` are inputs with profile defaults. It returns the final artifact, inspection path, `final_dimensions`, a per-pass `history` (dimensions and residual metrics each pass), `warnings`, and a `resolved` flag - so a driver runs it deterministically first at the execution gate and escalates only the residual, non-resize defects to the model. `dataviz_mcp/refit.py`.

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

When the chosen renderer is supported, pass the exact deliverable through the metadata-producing adapter and then exact-artifact inspection. When the appropriate renderer is not supported, inspect the exact export visually and keep missing geometry marked unknown. Use independent evaluation (`dataviz-eval`) only for an explicit audit, high-risk decision, or benchmark. Metadata availability must not force a weaker visual implementation or suppress a valid artifact.

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
| `TEXT_MARK_COLLISION` | Text straddles the edge of a bar, point, patch, or common collection. Text wholly inside one filled mark is placed there, not colliding; its legibility is the against-fill contrast check | High |
| `DELIVERY_TEXT_TOO_SMALL` | Text is below the configured delivery-scale size | Medium |
| `LOW_TEXT_CONTRAST` | Text contrast misses the practical delivery target | Medium |
| `DIRECT_LABELS_INCOMPLETE` | A declared repeated-panel/direct-label count is incomplete | High |
| `REDUNDANT_VALUE_AXIS` | The declared reading-carrying marks are directly labelled (contract path), or - with no contract - every mark-bearing panel labels at least two of its marks (two labels fix the linear scale), yet the value axis still renders ticks - likely duplicate ink. Only an axis whose own tick scale places the labelled values (read per panel and pixel direction) is flagged; year or rank ticks and undrawn ticks never are. A suggestion for the reviewer to confirm against the reading task | Low |
| `REDUNDANT_COLOUR` | Colour only restates a grouping the facet, category axis, or direct labels already show (one series per facet, one fill per named bar, or labelled series) - focal-plus-grey stays silent | Low |
| `EXTERNAL_LEGEND` | A legend round-trips series the plot already names via direct labels, facet titles, or category ticks | Low |
| `UNIDENTIFIED_SERIES` | Two or more series are distinguished only by colour with no legend, direct labels, or facet titles - the reader cannot tell which is which; direct labels are the preferred fix | High |
| `CELL_OVERFLOW` | Table text exceeds its cell, or a facet panel heading is wider than its strip and cut at the panel edge; revise wrapping or cell geometry | High |
| `UNDERFILLED_CANVAS` | The canvas carries too little ink for its size (`occupied_utilization_ratio` below threshold) - mostly empty layout | Low, or Medium when text is also undersized |

`geometry_status` distinguishes pass, fail and incomplete coverage. Nested table text is
measured individually; unsupported grobs/viewports leave coverage incomplete. Display-size
font checks use the exact PNG DPI and supplied container width.

`passes_geometry_checks` is true only when metadata is present, supported checks are complete, and no high- or medium-severity defect remains.

Every geometry defect now also carries its fix vector, so a revision is a number rather than a guess: clipped elements report per-edge `overflow_px` and `grow_margin_px`; colliding labels report `separation_needed_px`; `panel_heights_px` and `min_panel_height_px` expose squashed facets; and a `geometry_summary` block ranks the worst offenders and computes `suggested_dims`, the grown canvas that would clear them.

Each defect also carries a `defect_class`, and the report groups the defects into a `correction_plan` with three classes, so the cycle routes deterministically instead of the model re-deriving the split each turn: **canvas** - clipping/overflow the canvas can grow out of, resolved by `refit_chart` and only when the group's shared `growth_vector` (the same `suggested_dims`) is non-null; **placement** - a local text move (collisions, an over-long unwrapped annotation, a missing direct label, and a label crossing the *plot* boundary, which canvas growth cannot fix), resolved in the chart code; **semantic** - a judgement only the model makes (contrast, redundant ink, an external legend, an unidentified series, undersized text, an underfilled canvas). A new defect code without a class is a test failure, not a silent default.

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

The end-to-end coffee fixture renders a deliberately bad multi-annotation time series and detects four geometry defects. It then changes annotation placement only, renders and inspects again, and reaches zero defects. The comparison report confirms that the second artifact resolves the failures without introducing a new one.

## Implementation map

| Path | Responsibility |
|---|---|
| `dataviz_mcp/rendering.py` | Trusted builder execution and metadata-first render bundle |
| `dataviz_mcp/inspection.py` | Exact-artifact geometry checks, defect report, and fix vectors |
| `dataviz_mcp/refit.py` | Deterministic render -> inspect -> grow loop that clears clipping/overflow/squash (`refit_chart`) |
| `dataviz_mcp/layout.py` | Delivery profiles and the overflow-to-canvas arithmetic shared by inspection and refit |
| `dataviz_mcp/mark_read.py` | Values read off a chart image between two printed ticks (`read_marks_from_anchors`) |
| `dataviz_mcp/palette.py` | Colour selection, assignment, WCAG/CVD scoring, and image sampling (`recommend_colours`, `validate_palette`, `recommend_continuous_scale`, `validate_scale`, `extract_palette_from_image`); uses `color_math.py` |
| `dataviz_mcp/precision.py` | Spread-derived significant digits for a numeric column (`recommend_precision`) |
| `dataviz_mcp/scale_transform.py` | Advisory linear-vs-log10 axis recommendation from positive dynamic range and skew (`recommend_scale_transform`) |
| `dataviz_mcp/server.py` | Stdio MCP surface (render, inspect, compare, and the recommend_* resolution tools) |
| `dataviz_mcp/review_views.py` | Full, delivery, panel, hierarchy, and dense-placement views |
| `dataviz_mcp/tests/` | Capability, protocol, geometry, and coffee repair tests |

Installation, client registration, tool parameters, and the chart-builder contract are in [`dataviz_mcp/README.md`](../dataviz_mcp/README.md).
