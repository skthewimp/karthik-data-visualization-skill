# Dataviz MCP

This local stdio server handles the mechanical part of chart production. It probes ggplot2 and Matplotlib, chooses ggplot2 first for supported static output, executes trusted chart code, preserves renderer geometry, inspects the exact PNG, builds review views, and compares revisions. It does not decide the analytical question, claim, visual style, or release verdict.

See [`docs/mcp.md`](../docs/mcp.md) for the architectural boundary, generation and repair flows, hash/version guarantees, and the reasons for using render metadata.

## Staged pipeline contract

`dataviz_mcp.stage_contracts` is the provider-neutral, staged contract another
application can reuse. Two front halves feed one shared terminal process
(`dataviz-construct`): `REPAIR_PIPELINE` (image in: `diagnose`, then the construct tail)
and `STORY_PIPELINE` (dataset to story: `discover -> contract -> clean`, then the construct
tail). The shared tail is `insight -> select -> idea -> build -> execution`, and its
`select`, `idea`, `build`, and `execution` stages are the *same* `Stage` objects in both
pipelines - the literal coalescing of the two old `select -> build -> refine` tails. Only
`insight` differs, and only in the artifact it reads. `insight` names the headline claim and
candidate annotations before a form is chosen (`karthik-evidence-builder`); `idea` is the
pre-render gate (`dataviz-idea-critique`); `execution` is the post-render gate
(`dataviz-execution`). How many revision passes either gate runs is the driver's budget, not
a fixed cap. Each stage names the smallest skill subset it needs, the artifact it receives,
the artifact it emits, and a focused adapter. Handoffs are **structured text**
(markdown sections per content field, plus a small `routing` block of `key: value` lines at
the branch points), not strict JSON - so the pipeline runs on cheaper / open-weight models
too. `dataviz_mcp.handoff` parses the routing block leniently and also accepts a plain JSON
object; each stage's `output_schema` is retained as the machine-readable *content checklist*,
not a wire format.

A driver runs one model call per stage. `stage_skill_bundle(stage, builder, active_conditions)`
reads only that stage's `<skill>/codex/SKILL.md` sources - never the whole repository - so
a skill absent from a stage never enters its call. That per-stage bundling is the fix for
the context rot the old single-creator all-skills bundle caused. `build_stage_adapter(...)`
prepends the shared guardrails and the stage's focused instructions to that bundle.

The build stage's builder skill (`karthik-data-visualization` for a chart,
`karthik-table-style` for a table) is chosen from the select stage's `builder` routing key;
`chart-annotations`, `chart-explainer`, `dataviz-color`, and `dataviz-precision` load only
when the select artifact's routing block asks for them (parsed via
`dataviz_mcp.handoff.parse_routing`). The build stage asserts the headline claim named at
`insight` and places the candidate annotations it supplied.
`build_stage_adapter` also exposes the repository revision for reproducibility.

## Requirements and installation

- Python 3.10 or newer
- a Python virtual environment
- Codex, Claude Code, or another MCP-compatible client

From the repository root, install the package and retain the absolute interpreter path:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
MCP_PYTHON="$(pwd)/.venv/bin/python"
```

On Karthik's machine, the configured interpreter is:

```text
/Users/Karthik/envs/datascience/.venv/bin/python
```

The editable install means later changes in this checkout are used without reinstalling the package.

## Register with Codex

```bash
codex mcp add karthik-dataviz -- "$MCP_PYTHON" -m dataviz_mcp
```

Verify:

```bash
codex mcp get karthik-dataviz
```

Install the matching skill files, then start a new Codex session:

```bash
./sync.sh --no-pull --surface codex
```

## Register with Claude Code

```bash
claude mcp add-json --scope user karthik-dataviz \
  "{\"type\":\"stdio\",\"command\":\"$MCP_PYTHON\",\"args\":[\"-m\",\"dataviz_mcp\"]}"
```

Verify:

```bash
claude mcp get karthik-dataviz
```

Install the matching skill files, then start a new Claude Code session:

```bash
./sync.sh --no-pull --surface claude
```

No daemon is required. The client starts the Python process when it opens the stdio connection and stops it when the connection closes.

## Renderer boundary

The MCP API is backend-neutral. Rendering infrastructure must not become the style system.

- An explicit renderer requirement wins.
- Otherwise `auto` chooses ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available and the adapter supports the source/output.
- Matplotlib fallback records an unavailable/unsupported reason in the manifest.
- If Matplotlib is used, apply the rules in `karthik-data-visualization`; an unthemed default chart is not an acceptable MCP result.

Both adapters emit the same artifact, spec, layout, inspection, review-view, and manifest contract. Matplotlib supplies text, line, patch, bar, point, and common-collection geometry. ggplot2 resolves the drawn gtable tracks and captures every panel plus rect, point, polygon, polyline, and text grobs; uncommon grobs remain explicit limitations.

## Chart builder contract

For Matplotlib, create a Python file with a no-argument `build_chart()` returning a `Figure` or `(figure, chart_spec_dict)`. For ggplot2, create an R file with `build_chart()` returning a ggplot or `list(plot = <ggplot>, metadata = <list>)`; export is always through `ragg`.

```python
import matplotlib.pyplot as plt


def build_chart():
    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=120)
    line, = ax.plot([1, 2, 3], [2, 4, 3])
    line.set_gid("series:coffee-price")

    note = ax.annotate(
        "Brazil drought",
        xy=(2, 4),
        xytext=(20, 35),
        textcoords="offset points",
    )
    note.set_gid("annotation:brazil-drought")
    return fig, {"question": "How did coffee prices move?"}
```

Stable Matplotlib `gid` values make defects narrow and repairable:

- use `series:<id>` for plotted lines;
- use `annotation:<id>` for callouts;
- use `data_label:<id>` for a value printed on its own mark, and `label:<id>` for a free label.

Tag an on-mark value `data_label:`, never `label:`: a `data_label` sits on the mark it names by definition, so the inspector exempts it from the text-mark collision check (a `label` overlapping a mark is still flagged as an accidental overlap). Both count as a mark's direct value label for direct-label coverage and the redundant-value-axis check.

Untagged Matplotlib lines and annotations receive generated IDs, but those IDs are less stable across revisions.

## Tool contracts

### `probe_renderers`

Returns `Rscript`, ggplot2, ragg, and Matplotlib availability/version details, supported source/output types, and failure reasons. It makes no host changes.

### `render_and_inspect_chart`

Inputs include `source_path`, `output_dir`, `renderer` (`auto`, `ggplot2`, or `matplotlib`), `delivery_profile`, and optional dimension overrides. `auto` applies the renderer precedence above. The result contains the artifact, specification, normalized layout, inspection, artifact-bound review views, renderer-selection evidence, and hash-bound manifest.

### `render_chart`

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `source_path` | Yes | Existing trusted Python chart source |
| `output_dir` | Yes | Directory for the complete render bundle |
| `artifact_name` | No | Plain PNG filename; defaults to `chart.png` |
| `build_function` | No | Builder function; defaults to `build_chart` |
| `dpi` | No | Positive render DPI override |

Outputs:

```text
chart.png             exact delivery artifact
chart-spec.json       renderer, source hash, builder, DPI, and caller spec
layout-metadata.json  canvas, plot, text, annotation, line, legend, and transform geometry
manifest.json         hashes binding the bundle together
```

The tool response includes all four paths plus the artifact and manifest hashes.

### `inspect_rendered_chart`

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `artifact_path` | Yes | Exact PNG to inspect |
| `layout_metadata_path` | No | Matching metadata from `render_chart` |
| `output_path` | No | Inspection JSON path; defaults beside the PNG |
| `series_clearance_px` | No | Padding around annotation boxes for line collision checks; defaults to 2 |
| `max_unwrapped_annotation_chars` | No | Unwrapped annotation limit; defaults to 45 |
| `delivery_profile` | No | Delivery context recorded with the inspection |
| `minimum_text_size_pt` | No | Delivery-scale text threshold; defaults to 8 pt |

The report includes artifact hash and dimensions, inspection mode, completeness, pass state, normalized defects, detailed collision and clipping lists, minimum text margin, limitations, and its own SHA-256 hash. Every defect carries a `defect_class` - `canvas` (grow it out), `placement` (an exact geometry-tool move), or `semantic` (a model judgement) - and the report groups them into a `correction_plan` of those three classes so a driver routes the cycle without re-deriving the split: the `canvas` group rides a shared `growth_vector` (the same `suggested_dims`, null when nothing can grow), `placement` goes to `place_on_marks`/`recommend_text_placement`/`recommend_labels`, and only `semantic` earns a model patch.

Supplying mismatched metadata is an error. Omitting metadata produces an explicit raster-only, incomplete report rather than a pass.

### `refit_chart`

Closes the render -> inspect -> resize loop in code, so pure geometry arithmetic never costs a model turn. Renders, inspects, and while clipping/overflow/squash remains, grows the canvas by the exact overflow the inspector measured and re-renders.

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `source_path` | Yes | Trusted local `.py` (matplotlib) or `.R` (ggplot2) chart builder |
| `output_dir` | Yes | Directory the artifact bundle is written to |
| `renderer` | No | `auto` / `ggplot2` / `matplotlib`; defaults to `auto` |
| `delivery_profile` | No | `chat` / `slide` / `document`; sets base size and the growth ceiling. Defaults to `chat` |
| `dimensions` | No | Starting `width_px`/`height_px`/`dpi`; defaults to the profile |
| `max_iterations` | No | Maximum regrows after the first render; defaults to 3 |
| `content` | No | `chart` or `table`; defaults to `chart` |
| `artifact_name` / `build_function` | No | Passed through to the renderer |

Scope is only what growing fixes - edge clipping, overflow, squashed panels. Underfill (no exact shrink vector) is reported (`underfilled` + a warning) but never resized; label collisions stay `place_on_marks`' job. The loop exits when geometry is clean, the delivery ceiling is reached (warned, never squashed), `max_iterations` is hit, or a grow stops reducing the residual. Returns the final artifact, inspection path, `final_dimensions`, a per-pass `history`, `warnings`, and a `resolved` flag.

### `compare_chart_artifacts`

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `before_inspection_path` | Yes | Inspection JSON for the earlier artifact |
| `after_inspection_path` | Yes | Inspection JSON for the revision |
| `output_path` | No | Comparison JSON path; defaults beside the later report |

Both referenced PNGs are re-hashed before comparison. The result lists resolved, introduced, and persistent defects; blocking counts; dimensions; pixel difference; and whether the revision is mechanically improved. It does not make a substantive release decision.

## Forward geometry and text

These size the canvas, reserve the chrome, and place the text *before* (or with one measure render) so a weak model does not clip, squash, or collide on the first pass. All are mechanism only - they never choose the chart or write the annotation. See [`docs/mcp.md`](../docs/mcp.md) for the design rationale.

### `recommend_table_layout`

Table geometry comes from formatted content, not chart slots. The tool measures
text with grid/ragg when available; otherwise it identifies its Matplotlib/Agg
metrics as a fallback requiring verification in the target renderer. No new
packages are required. The skill chooses visual treatment; the tool validates
shared-scale scope and reserves space supplied for inline graphics.

```json
{
  "columns": [
    {"header": "Region", "identifier": true, "max_width_px": 190,
     "cells": ["Northern district", "Central", "South"]},
    {"header": "Revenue ($m)", "cells": ["12.5", "8.3", "15.0"],
     "visual_width_px": 90}
  ],
  "title": "Revenue by region",
  "typography": {"family": "sans", "body_pt": 11, "header_pt": 12,
                 "minimum_body_pt": 11, "minimum_header_pt": 11},
  "delivery": {"max_width_px": 1200, "max_height_px": 900,
               "display_width_px": 600, "minimum_text_px": 14},
  "treatment": {"kind": "bar", "scope": "column", "domain": [0, 15], "baseline": 0}
}
```

Alternatively, `content_path` reads a local JSON object containing `columns` and
optional `title`, `subtitle`, `notes`. Cells are final display strings; retain raw
values separately for bars, shading, and sparklines. Each column has the same
number of cells. `None` becomes a blank; use explicit strings for other missing
value conventions. Headers accept explicit newlines. `max_width_px` includes
padding and inline graphics; unbreakable tokens are preserved even when too wide.
Typography also accepts `padding_x_px` and `padding_y_px`. Defaults are compact:
0.35 em on each horizontal side and 0.15 em above/below, based on body type. Explicit
padding overrides those defaults. The R table renderer adds no outer margin beyond
builder-provided padding and text bands, so export dimensions follow the plan.

Construction compares measured word-wrap breakpoints for each column at unchanged
type and padding. It prefers feasible delivery and fewer continuations, then a
smaller total page footprint, accounting for shared header/row heights. Narrow and
wide starting arrangements help avoid a long header or isolated long body cell
inflating every row's whitespace. This is a local layout search, not a guarantee
of a globally optimal arrangement. Automatic wrapping does not require a manual
`max_width_px`. Headers may use the full column width; body text shares its width
with the reserved inline graphic. Do not stretch the resulting columns to fill
spare canvas width.

The result includes `status` (`fits`, `split`, `cannot_fit`), `measurement_backend`,
`col_widths_px`, `row_heights_px`, `header_height_px`, wrapped `headers` and
column-oriented `cells`, wrapped title/note `blocks`, and `pages`. Each page gives
its dimensions, zero-based column indices, and a half-open row range. Repeat
headers, identifiers and the returned text bands on each continuation. A reading
task that requires adjacent columns may require revising the proposed grouping.
`allow_split: false` produces `cannot_fit` when multiple pages would be required.
The tool does not remove content or reduce type to make it fit.

Apply the returned geometry to the table builder: grid widths/heights in inches
are pixels divided by `dpi`; fonts are points. Use the returned wrapped strings,
font family and sizes, and padding. `blocks` use `block_font_pt` in bold; their
reserved height is `reserved_band_px`. Render each page with
`render_and_inspect_chart(content="table")`, passing its dimensions and `dpi`,
plus `minimum_text_size_pt`, `display_width_px`, and `minimum_text_size_px` in
`dimensions`. These inspection settings also work on `inspect_rendered_chart`.
Check the exact artifact and its actual displayed size; export DPI is not a
readability guarantee. Unsupported nested viewport references or graphics are
reported as incomplete coverage, not silently passed. Decimal alignment, contrast
against cell fills and visual emphasis still need visual review.

Treatment kinds: `text`, `emphasis`, `bar`, `dot`, `shading`, `sparkline`. A `row` or
`table` scale for quantitative graphics requires `commensurable: true`; sharing a
unit alone is insufficient. The tool preserves scale and focal details for the
builder, but cannot validate their meaning from display strings. The table skill
owns that judgment. Categorical/focal assignments use the existing colour picker;
heat scales retain their sequential/diverging order and use palette validation as
a diagnostic, not the picker's distinct-hue ordering.

### `recommend_layout`

Sizes a clip-safe canvas from the chart's shape expressed as counts. Inputs: `x_slots`, `y_slots`, `filled_marks`, `n_panels`, `facet_scales` (`fixed`/`free`/`free_x`/`free_y`), `n_direct_labels`, `title_lines`/`subtitle_lines`/`footer_lines`, `x_labels`, `longest_x_label_chars`, `delivery_profile` (`chat`/`slide`/`document`). Returns `width_px x height_px x dpi`, a facet grid, x-label rotation, and reserved title/subtitle/footer bands. Demand past the delivery ceiling is warned, never squashed. Call at select, before build; feed the dims into the renderer and `recommend_text_placement`.

### `reserve_frame`

Places the chrome - title, subtitle, caption, footer, axis titles, tick bands, legend - blind, with no render, because chrome lives in the margins and does not depend on the data. Inputs: the frame strings (`title`, `subtitle`, `caption`, `footer`, `x_axis_title`, `y_axis_title`, `longest_x_tick`, `longest_y_tick`, `legend_side`, `longest_legend_label`), plus `width_px`/`height_px`/`dpi`/`delivery_profile`, per-role `font_pt` overrides, and `edge_margin_px`. Returns the `plot_area` rectangle the marks may fill and placement-ready `frame_blocks`. A frame too big for the canvas is warned, never squashed. Call at build, before the first render; pass `frame_blocks` on to `place_on_marks` as fixed obstacles.

### `place_on_marks`

Places labels glued to specific marks using their real pixel positions instead of a guess. Required inputs: `width_px`, `height_px`, `dpi`, `transform` (the `data_to_pixel` affine from the render's layout metadata), and `labels` (each with `data_x`/`data_y`). Optional: `marks` (bounding boxes, handed in as obstacles), `fixed_blocks` (from `reserve_frame`), `plot_area` (the panel rectangle from `reserve_frame`), `x_trans`/`y_trans` for log/sqrt/reverse ggplot axes, `max_annotation_width_frac`, `edge_margin_px`, `min_font_pt`. Projects each label through the transform and delegates to `recommend_text_placement`, so text-mark and text-text overlaps are de-collided on the first delivered chart. A non-Cartesian coord or unreproducible scale emits no transform and the tool refuses rather than project through a wrong map. Returns everything `recommend_text_placement` returns plus `projected_anchors`, and, for every movable label, **native data coordinates** the builder draws from directly - `placed_data` (the label box's top-left corner; draw the label left/top-anchored, `hjust=0, vjust=1` / `ha="left", va="top"`), `anchor_data` (the mark), and `leader_line_data` (`{from, to}`, the box-edge end and the mark end) when a leader is drawn - so no data-space `geom_segment`/`annotate` is improvised. The leader terminates at the label's bounding-box edge and the mark; a singular affine omits the data coordinates rather than fabricating them.

### `recommend_labels`

Selects *which* points on each series to label directly, within a per-series budget (`max_labels_per_series`, default 4). Pass one `{id, values:[...]}` entry per `series` in order; it claims endpoints and extremes first, then the largest step-to-step changes. Returns per-series `label_indices` and `reasons`. It selects points, not placement - feed the chosen anchors to `recommend_text_placement`.

### `recommend_text_placement`

Wraps a chart's text to fit its room and parks each movable label beside the mark it names, in priority order (data labels, then category/series labels, then free annotations). Required inputs: `width_px`, `height_px`, `dpi`, `blocks` (each `{id, text, role, anchor:{x,y}, placement?, anchors?, font_pt?, max_width_px?, max_lines?}`). Optional: `obstacles` (data-mark bounding boxes), `plot_area` (the panel rectangle - a movable label left straddling the plot boundary is nudged wholly inside and carries the exact `plot_boundary_correction` `{dx, dy}`), `max_annotation_width_frac`, `edge_margin_px`, `min_font_pt`. Fixed roles (`title`/`subtitle`/`footer`/`caption`/`axis_label`/`data_label`) are wrapped, never moved; `label` and `annotation` are movable and de-collided against obstacles, travelling to the nearest clear area with a `leader_line` only when no adjacent spot exists. Returns each block's wrapped text and final `bbox`, `suggested_anchor`/`suggested_font_pt`/`suggested_wrap` when changed, a `redundant_annotations` list, and a canvas-level `suggested_orientation`/`suggested_canvas` when a portrait flip would help. It fits the labels already chosen; it invents none.

## Colour and precision advisors

Analytical mechanism for two decisions a chart always needs. They report and recommend; they never hard-block.

### `recommend_colours`

Picks and assigns colours for one graph from an `available` set (brand/context/default). Inputs: `available`, `n_series`, `background` (default `#FFFFFF`), optional `focal` (pinned to series 0), and `semantic_hints` (a list of `{series_index, colour}` hard pins or `{series_index, hue_family}` soft families, each with optional `alternates`). Chooses by max-min separation and background contrast; priority is series distinctness (hard), then meaning over contrast/CVD. Unmet or collided hints are reported in `semantic_findings`. Use even when colours are given - a specific chart still needs a which-and-how-assigned decision.

### `validate_palette`

Scores a palette on WCAG contrast, series distinctness, CVD, and grayscale survival. Inputs: `colours`, `background`, optional `text_colours`, `min_contrast_text` (default 4.5), `min_contrast_mark` (default 3.0). Returns a verdict plus ranked findings, each with a concrete nudge. Targets are soft: findings are reported, not hard-blocked.

### `extract_palette_from_image`

Samples dominant hues from a source chart image as a repair prior (brand/WCAG may override). Inputs: `image_path`, `max_colours` (default 8), `ignore_near_white_black` (default true).

### `recommend_precision`

Recommends significant digits / a uniform rounding place for a numeric column, derived from the spread (max - min), not individual values. Inputs: `values`, `role` (`axis`/`label`/`table_column`), `target_steps` (default 2), optional `smallest_meaningful_difference`, and `exact` (identifiers or exact-lookup only - preserves every digit and flags `exact_override`). Every value is rounded to one uniform place.

## Optional audited repair integration

The default repair path can call `render_and_inspect_chart` without opening a case. When an audit trail or benchmark is requested, the case manager preserves the bundle and inspection beside an iteration:

```bash
python3 dataviz-fix/codex/scripts/case_manager.py iterate \
  --case CASE_ID \
  --output /path/to/chart.png \
  --bundle-manifest /path/to/manifest.json

python3 dataviz-fix/codex/scripts/case_manager.py inspect \
  --case CASE_ID \
  --report /path/to/inspection.json
```

Record inspection before `review-request`. The blind packet then carries the exact artifact and deterministic inspection hashes. The evaluator must return the same inspection hash. The case manager rejects `Send` while a known high- or medium-severity deterministic defect remains.

The local runner performs this order automatically. Raster-only candidates remain usable for visual review, but their deterministic geometry result stays incomplete.

## Run the tests

Use the same environment as the MCP clients:

```bash
MPLCONFIGDIR=/tmp/mpl-cache "$MCP_PYTHON" -m pytest -q
```

The default suite covers MCP tools, a real stdio tool listing, deterministic geometry fixtures, and the end-to-end coffee annotation repair. Run `pytest -q dataviz-fix/tests tester/tests` only when changing the optional audited case manager or local tester.

`dataviz_mcp.benchmark` loads caller-supplied repair-case roots read-only, de-duplicates case IDs, reports critique/design adoption and cycle counts, and compares a complete matched replay with its baseline. A replay only meets acceptance when every baseline case is present, evaluation cycles fall, and false `Send` events do not increase.

## Current limits

- Rendering supports trusted local Python/Matplotlib and R/ggplot2 PNG output.
- ggplot2 hierarchy, panel, and common child-mark geometry are deterministic; text boxes use deterministic font-metric estimates and uncommon grobs remain explicitly uncovered.
- Raster-only mode verifies identity and dimensions but does not use OCR or computer vision to infer geometry.
- Mechanical pass/fail does not replace visual critique, analytical evaluation, or user acceptance.

## Local security boundary

Rendering imports and executes the supplied Python or R file. Use it only with chart source you trust. The server is local-only, uses stdio, has no authentication layer, and does not sandbox arbitrary code.
