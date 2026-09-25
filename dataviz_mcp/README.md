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
A stage can select a named section through `skill_sections`: idea review receives the
selector's current **Form constraints**, without its selection workflow. Missing or
ambiguous section headings fail bundling rather than silently omitting the constraints.

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
- Otherwise `auto` chooses ggplot2 when `Rscript`, `ggplot2`, and `ragg` are available. Probe before generating source.
- Matplotlib is the automatic fallback only when the R backend is unavailable; the manifest records why. R build errors are not retried in Python. A source-language mismatch requires regenerating source, not silently switching backends.
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
text with grid/ragg when the R table backend is available; otherwise it uses
Matplotlib/Agg metrics for the Python fallback. No new
packages are required. The skill chooses the treatment (which cells compare, which
channel, which direction is better); the tool resolves it into per-cell fills, inks,
bar extents and sparkline points, reserves the graphic width, and right-aligns numbers.

```json
{
  "columns": [
    {"header": "Region", "identifier": true, "max_width_px": 190,
     "cells": ["Northern district", "Central", "South"]},
    {"header": "Revenue ($m)", "cells": ["12.5", "8.3", "15.0"],
     "values": [12.5, 8.3, 15.0]},
    {"header": "Cost ($m)", "cells": ["4.1", "6.0", "3.2"]}
  ],
  "title": "Revenue by region",
  "typography": {"family": "sans", "body_pt": 11, "header_pt": 12,
                 "minimum_body_pt": 11, "minimum_header_pt": 11},
  "delivery": {"max_width_px": 1200, "max_height_px": 900,
               "display_width_px": 600, "minimum_text_px": 14},
  "treatment": [
    {"kind": "bar", "columns": [1]},
    {"kind": "shading", "columns": [2], "higher_is_better": false},
    {"kind": "emphasis", "rows": [2]}
  ]
}
```

Alternatively, `content_path` reads a local JSON object containing `columns` and
optional `title`, `subtitle`, `notes`. Cells are final display strings; retain raw
values separately for bars, shading, and sparklines. Each column has the same
number of cells. `None` becomes a blank; use explicit strings for other missing
value conventions. Every column must supply `header` and `cells`; character-count
metadata is insufficient. Use `header: ""` only for an intentionally blank header.
Pass the whole header, including units and descriptions; explicit newlines preserve
semantic breaks. Optional `max_header_lines` sets the heading's line budget.
The planner widens/splits to honour it or returns `cannot_fit`. `max_width_px`
includes padding and inline graphics and is a ceiling: an unbreakable token is
preserved for review, but cannot silently override that ceiling with a fit verdict.
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
font family and sizes, and padding. Draw returned `headers` verbatim in bold at
`header_pt` within `header_height_px`. Never replace them with raw unwrapped names
or add descriptions that were absent from the measured content. `blocks` use `block_font_pt` in bold; their
reserved height is `reserved_band_px`. Render each page with
`render_and_inspect_chart(content="table")`, passing its dimensions and `dpi`,
plus `minimum_text_size_pt`, `display_width_px`, and `minimum_text_size_px` in
`dimensions`. These inspection settings also work on `inspect_rendered_chart`.
Check the exact artifact and its actual displayed size; export DPI is not a
readability guarantee. Unsupported nested viewport references or graphics are
reported as incomplete coverage, not silently passed. Decimal alignment, contrast
against cell fills and visual emphasis still need visual review.

`treatment` is one object or a list, so a table can combine row-wise shading, a
sparkline column and a focal row. Each item: `kind` (`bar`, `shading`, `sparkline`,
`emphasis`, `text`), `columns` (zero-based; required except for emphasis), optional
`rows`, `scope` (`column` - each column its own scale; `row` - each row its own;
`table` - one scale), `higher_is_better` (false reverses the shading so the best
cell is strongest), `scale` (`auto`/`sequential`/`diverging`), `midpoint`, `domain`,
`baseline` (bars, default 0), `colour` (bars, sparklines, focus tint) and `colours`
(brand poles for shading). Shading and bars shared across a `row` or `table`, and a
sparkline scale shared across rows (`column`/`table`; sparklines default to each
row's own shape), require `commensurable: true`. Emphasis requires `rows`.

Raw numbers come from each column's `values` (a list of lists for a sparkline column,
whose cells can be blank), or are parsed from numeric display strings (currency, %,
separators, K/M/B, parenthesised negatives). The result carries `cell_styles`
(per column, per row: `fill`, `ink`, `bold`, `bar` {start, end, colour}, `spark`
{points, colour}), `col_align`, `visual_width_px` and `untreated_numeric_columns`.
Heat fills stop short of the pole and are eased until the chosen ink clears 4.5:1,
so every number stays legible. A warning flags comparable numeric columns left as
plain text. The `chat` profile assumes an 800 px display with a 12 px text minimum
unless `delivery` says otherwise, which caps export width so text survives
downscaling.

### `recommend_layout`

Sizes a clip-safe canvas from the chart's shape expressed as counts. Inputs: `x_slots`, `y_slots`, `filled_marks`, `n_panels`, `facet_scales` (`fixed`/`free`/`free_x`/`free_y`), `n_direct_labels`, `title_lines`/`subtitle_lines`/`footer_lines`, `x_labels`, `longest_x_label_chars`, `delivery_profile` (`chat`/`slide`/`document`), optional `target_aspect` (the source image's width:height when repairing; default the profile's aspect), optional `longest_facet_label_chars` (the longest panel heading, so a heading that wraps to its panel gets its lines), and optional `panel_groups`. Each facet row reserves its heading strip and the frame's edge margin is reserved once, so the returned panel floor is what the render draws. Returns `width_px x height_px x dpi`, a facet grid, x-label rotation, reserved title/subtitle/footer bands, `regions`, and a structured `fit` verdict. The grid is chosen so the whole image lands near `target_aspect` given each panel's floored shape (compact rows/cols, tall panels get more columns and wide panels more rows), and nothing is squashed below the legibility floor: when content needs more room than the profile, *both* width and height are grown (the image is resized up) instead of clamping and cramming. `fit` reports `status` (`ok`/`over_ceiling`), `legible`, `over_width`/`over_height`, required vs ceiling dims, `min_panel_height_px`, and ranked `directives` (`reduce_slots`/`reduce_panels`/`split_pages`/`drop_group`). Also returns `font_pt`, the canvas-scaled house font sizes per role, resolved for the final canvas so they equal what `reserve_frame` will use and the reserved text bands stay honest on a grown canvas (on-mark value labels remain the separate slot-driven `recommended_data_label_pt`). Call at select, before build; feed the dims into the renderer and `recommend_text_placement`.

For a heterogeneous layout - an aggregate/overview panel set apart from a small-multiple detail grid (the aggregate-and-parts guardrail) - pass `panel_groups`: a list of `{role, n_panels, emphasis?, filled_marks?, x_slots?, y_slots?}`. Each group is sized as its own sub-grid and stacked as a full-width band whose height follows what it has to show - a band of discrete rows takes its rows plus the axis expansion, so a one-bar overview is not given the same height as a four-bar detail (`emphasis` >1 makes a band taller so the overview reads apart); the tool picks each group's column count against the aspect target; the per-band structure comes back as `regions` (`{role, facet_ncol, facet_nrow, n_panels, x, y, width, height}`) for the renderer to place. `role` is a free-text label echoed back per band. Without `panel_groups`, `regions` is `null` and the single-grid behaviour is unchanged.

### `reserve_frame`

Places the chrome - title, subtitle, caption, footer, axis titles, tick bands, legend - blind, with no render, because chrome lives in the margins and does not depend on the data. Inputs: the frame strings (`title`, `subtitle`, `caption`, `footer`, `x_axis_title`, `y_axis_title`, `longest_x_tick`, `longest_y_tick`, `legend_side`, `longest_legend_label`), plus `width_px`/`height_px`/`dpi`/`delivery_profile`, per-role `font_pt` overrides, and `edge_margin_px`. Returns `plot_margin_px` (the outer edge margin to set as `plot.margin`), an advisory `plot_area` rectangle, `reserved_px` band sizes, and placement-ready `frame_blocks`. The renderer lays out the chrome natively inside the `recommend_layout`-sized canvas: set `plot.margin` to `plot_margin_px` and never derive margins from the reserved bands, or the chrome is reserved twice and the panel collapses. `plot_area` is advisory - the blind clip check and the `place_on_marks` boundary; `frame_blocks` are obstacles. A frame too big for the canvas is warned, never squashed. Call at build, before the first render.

### `place_on_marks`

Places labels glued to specific marks using their real pixel positions instead of a guess. Required inputs: `width_px`, `height_px`, `dpi`, `transform` (the `data_to_pixel` affine from the render's layout metadata), and `labels` (each with `data_x`/`data_y`). Optional: `marks` (bounding boxes, handed in as obstacles), `fixed_blocks` (from `reserve_frame`), `plot_area` (the panel rectangle from `reserve_frame`), `x_trans`/`y_trans` for log/sqrt/reverse ggplot axes, `max_annotation_width_frac`, `edge_margin_px`, `min_font_pt`. Projects each label through the transform and delegates to `recommend_text_placement`, so text-mark and text-text overlaps are de-collided on the first delivered chart. A `data_label` with no `placement` whose point is the first or last vertex of a path mark (a dumbbell or range bar, a line's start or end - ggplot `geom_segment` segments export as two-point paths) parks outward along the run: left of the start and right of the end of a horizontal run, below/above for a vertical one, clear of the dot drawn there. Any `data_label` with a `placement` side parks one gap beyond its anchor on that side, centred on it. It never raises: a non-Cartesian coord or unreproducible scale emits no transform, and a label whose data position cannot be projected is returned in `unplaced` (with its `anchor_data` and a reason) for the builder to draw at its mark with the renderer's own repel, rather than projected through a wrong map. A wrong or ambiguous `mark_id` is flagged in `unverified_attachments` and as a warning, not refused. Returns everything `recommend_text_placement` returns plus `projected_anchors`, and, for every movable label, **native data coordinates** the builder draws from directly - `placed_data` (the label box's top-left corner; draw the label left/top-anchored, `hjust=0, vjust=1` / `ha="left", va="top"`), `anchor_data` (the mark), and `leader_line_data` (`{from, to}`, the box-edge end and the mark end) when a leader is drawn - so no data-space `geom_segment`/`annotate` is improvised. The leader terminates at the label's bounding-box edge and the mark; a singular affine omits the data coordinates rather than fabricating them.

### `recommend_labels`

Selects *which* points on each series to label directly, within a per-series budget (`max_labels_per_series`, default 4). Pass one `{id, values:[...]}` entry per `series` in order; it claims endpoints and extremes first, then the largest step-to-step changes. Returns per-series `label_indices`, `reasons` and `name_index` - the line end, where the series name is printed once; the other chosen points print the value alone. It selects points, not placement - feed the chosen anchors to `recommend_text_placement`.

### `recommend_text_placement`

Wraps a chart's text to fit its room and parks each movable label beside the mark it names, in priority order (data labels, then category/series labels, then free annotations). Required inputs: `width_px`, `height_px`, `dpi`, `blocks` (each `{id, text, role, anchor:{x,y}, placement?, anchors?, font_pt?, max_width_px?, max_lines?}`). Optional: `obstacles` (data-mark bounding boxes), `plot_area` (the panel rectangle - a movable label left straddling the plot boundary is nudged wholly inside and carries the exact `plot_boundary_correction` `{dx, dy}`), `max_annotation_width_frac`, `edge_margin_px`, `min_font_pt`. Fixed roles (`title`/`subtitle`/`footer`/`caption`/`axis_label`/`data_label`) are wrapped, never moved; `label` and `annotation` are movable and de-collided against obstacles, travelling to the nearest clear area with a `leader_line` only when no adjacent spot exists. Returns each block's wrapped text and final `bbox`, `suggested_anchor`/`suggested_font_pt`/`suggested_wrap` when changed, a `redundant_annotations` list, and a canvas-level `suggested_orientation`/`suggested_canvas` when a portrait flip would help. It fits the labels already chosen; it invents none.

## Scaffold and check the chart source

### `scaffold_chart`

Writes the chart source from the plan, so the build model never writes the mechanical half. The generated ggplot2 `.R` (or Matplotlib `.py`) loads the `prepare_plot_data` frame, types the x column (`x_kind: date` parses time labels to real dates, ticked at the data's own dates when each clears its neighbour by a label's width and with the renderer's own breaks otherwise, in short date labels; a label that is not a date, such as a period range, keeps the axis discrete with a warning), and applies the number format (`fmt_value`, from a `recommend_precision` result plus optional `prefix`/`suffix`), the palette (`palette`/`ink` from `recommend_colours`, or a gradient from `recommend_continuous_scale` stops), canvas, fonts, facet grid and category wrap (`recommend_layout`), the outer margin (`reserve_frame`), titles from `public_copy` (axis titles only where declared, by displayed position), a legend only for `identification: legend`, and a coloured subtitle key for `subtitle_key` (ggplot2 only; each name in its series hue, darkened where needed to read as text at 4.5:1). The value axis and its gridlines are dropped when `value_labels` reaches the same two-label floor `REDUNDANT_VALUE_AXIS` uses; limits appear only for `zero_baseline`; `orientation: horizontal` (or the layout's `bar_orientation`) adds `coord_flip()`.

The model writes only the body of `chart_marks` between the `# ==== marks` markers: layers mapping `x = category`, `y = value`, coloured from `palette`/`ink`, numbers through `fmt_value`, text at `label_size` (a free annotation at `annotation_size`), stacked bars with `position = stack` and their labels with `stack_mid` (Matplotlib: `stack(ax, rows)`), which keep the first series at the baseline, and text on a mark coloured `on_fill_ink(series)` (`on_fill_ink()` for the single-colour `ink`; Matplotlib: `ON_INK[series]`; `stack()` returns each segment's ink) - the light or dark ink with the higher contrast against that series' fill, the same rule `place_bar_value_labels` uses. Two ggplot2 layers apply the placement tools' rules at draw time, from the drawn geometry and the label's own glyphs: `bar_values(aes(..., label, fill), position = <the bars' position>)` prints each bar's value inside its end in the ink that reads on its fill, or just past the end in ink when the bar is too short (stacked segments centre; one with another beyond it stays inside), through dodge, stack and `coord_flip`; `end_labels(aes(..., label, colour), data = <each line's last row>)` names lines past their last points, each name in its line's hue darkened where needed to read as text (`page_ink()` gives the same ink for other page text), wraps a long name on whole words to the capped band the margin reserved (`end_label_chars`; a letterless token such as the " - 37%" joining a value stays with its neighbour), and spreads names that would overlap apart along the value axis by the least total movement, with short leaders; `point_labels(aes(..., label, colour, group), data = <the line's rows>)` prints values beside their points (a line's first point, a peak, a dumbbell's ends) at the first spot inside the panel clear of the drawn lines, markers and other labels - toward the panel's middle, then above, below, the diagonals, the outer side - with rows whose label is `NA` kept as the path. `check_chart` flags hand-set text on a drawn line or segment as `TEXT_ON_MARK`. The category axis keeps the planned order over the categories the marks draw (`limits`), so a layer drawn from a subset cannot reorder it, and a panel heading wider than its panel wraps to the panel (`label_wrap_gen`) instead of being cut. The scaffold adds its scales, `labs()` and `theme()` after the slot, so an override in the slot loses by ggplot's own ordering. A `<source>.scaffold.json` record beside the file holds the scaffold regions for `check_chart`. Returns `source_path`, `frame` (the `reserve_frame` result as drawn, including any end-label room - pass this, not the original, to `place_on_marks` and `inspection_contract.frame`), `dimensions` for the render, `value_axis_hidden`, `decided` (what was applied, for `recommendations_used`), a `marks_brief` for the build model and `warnings`. Frame text is drawn as `reserve_frame` wrapped it; panels draw with `clip = "off"` so a label past the panel reaches the canvas where the inspector measures it; and when series are direct-labelled at the line ends (or values sit past horizontal bar ends) the right margin is widened by the measured label width beyond what the axis expansion already holds - for line-end names, the widest line once wrapped to a band capped like a horizontal bar's category band, widened only as far as the stacked names need to fit the panel height. Routing scalars are read the way the routing block reads them (`direct labels` resolves; an unknown word such as `length` takes the default with a warning), and a missing title is a warning, so a stray word never turns a build off the scaffold.

The frame decides what a mark is. An interval frame (`start`/`end` from `prepare_plot_data`) scales and checks each mark between its two ends; `bar_values()` takes `ymin`/`ymax` for a segment that does not start at zero. Each label measure the frame carries (its `plot-data.json` roles) gets its own formatter, `fmt_<name>()`, from `label_formats` or from its own values by the spread rule, in the units the role map gave - a growth rate never borrows the revenue format. On bars it goes in `bar_values(aes(..., note = fmt_<name>(<name>)))`, which prints it past the bar's end, after the value when the value is outside too, so the two never collide.

Panel groups: when `layout.regions` (from `recommend_layout(panel_groups=...)`) name their `categories` - one group may name none and take the rest - the source draws one native ggplot per region, `chart_regions()`, each from its own rows through the same `chart_marks(d)`, under one page frame reserved once for the title, subtitle and caption. Regions of one measure share the value range unless `facet_scales` frees it. `regions` returns each region's box on the page (`x`, `y`, `width_px`, `height_px`, its categories) for a compositor that places the native plots; `build_chart()` composes the same boxes with patchwork into one image. Matplotlib draws one grid (warned).

### `check_chart`

Takes the scaffolded `source_path`. Restores any edited scaffold region from the record, then builds the plot object and lays it out at the delivery size recorded in the sidecar (no PNG is rendered): every text box comes from its own glyphs and justification, every mark from its trained position, and each built row carries the observation it draws (category, series, facet), so a label is matched to a bar by identity, never by a number parsed from its text. It reports each deviation in the slot as `{code, severity, message}`: `BUILD_ERROR` (including a value mapped to a discrete position, which fails the continuous value axis), `MARKS_NON_LAYER` (a scale, coord, facet, labs or theme returned from the slot), `GEOM_LABEL`, `COLOUR_NOT_IN_PALETTE` (neutral greys allowed), `TEXT_TOO_SMALL`, `COLOUR_UNMAPPED` (a mapped colour column the palette does not name, which falls to the NA grey), `LABEL_ON_WRONG_MARK` (a label whose drawn box sits on another observation's bar; the fix names the bars' own position adjustment - a dodge, never a stack the plan did not choose), `LABEL_OFF_ITS_MARK` (a label drawn more than a few lines along the value axis from its own observation's mark - a stack applied to line labels, a hand offset), `LOW_CONTRAST_ON_MARK` (text whose box centre sits on a fill, below 4.5:1 against the fill painted over the page with its alpha; a label past a bar's end reads on the page, not the bar), `LOW_CONTRAST_ON_PAGE` (text off any mark below 3:1 on the page in an ink the palette does not own - on-fill white spilled off a short bar), `STACK_ORDER` (stacked segments not running in series order from the baseline - ggplot's default stack puts the first series furthest out), `DECORATION_STRETCHES_AXIS` (a layer that is not a data mark - a finite band or backdrop tile - reaching well past the data marks on the value axis, so it sets the range and flattens the data), `VALUE_NOT_ON_POSITION` (the non-text marks reach less than half the data's value range along the value axis, compared in the value scale's own space so a log axis compares logs - a slopegraph drawn flat with the value only in its labels; skipped for colour-encoded values), `VALUE_LABELS_MISSING` (fewer drawn labels than `value_labels` promised once the axis was dropped), `MARKS_SLOT_MISSING`, and `UNSCAFFOLDED_BUILD` (a source with no scaffold record - a hand-written chart; re-scaffold and move the marks into the slot). A page of regions is checked region by region, each at its own size, and marks are matched to an interval frame's ends. `fix_list` is the same list numbered for the correcting model; `ok` with a clean inspection means no model correction is needed.

## Colour and precision advisors

Analytical mechanism for two decisions a chart always needs. They report and recommend; they never hard-block.

### `recommend_colours`

Picks and assigns colours for one graph from an `available` set (brand/context/default). Inputs: `available`, `n_series`, `background` (default `#FFFFFF`), optional `focal` (pinned to series 0), and `semantic_hints` (a list of `{series_index, colour}` hard pins or `{series_index, hue_family}` soft families, each with optional `alternates`). Chooses by max-min separation and background contrast; priority is series distinctness (hard), then meaning over contrast/CVD. Unmet or collided hints are reported in `semantic_findings`. Optional `available_source` (the colour plan's): brand and prompt colours (`brand-skill`, `prompt`, `provided`, or a supplied pool with no source) fill the first slots as given and generation only covers a count shortage; any other supplied pool (`source-extracted`, a proposed set) is a prior - a slot takes a pool colour only if it reads on the background and passes `validate_palette`'s distinctness and CVD tests against the placed series, else a generated colour that does. The default pool is left as it is. Use even when colours are given - a specific chart still needs a which-and-how-assigned decision.

### `validate_palette`

Scores a palette on WCAG contrast, series distinctness, CVD, and grayscale survival. Inputs: `colours`, `background`, optional `text_colours`, `min_contrast_text` (default 4.5), `min_contrast_mark` (default 3.0). Returns a verdict plus ranked findings, each with a concrete nudge. Targets are soft: findings are reported, not hard-blocked.

### `extract_palette_from_image`

Samples dominant hues from a source chart image as a repair prior (brand/WCAG may override). Inputs: `image_path`, `max_colours` (default 8), `ignore_near_white_black` (default true).

### `recommend_precision`

Recommends significant digits / a uniform rounding place for a numeric column, derived from the spread (max - min), not individual values. Inputs: `values`, `role` (`axis`/`label`/`table_column`), `target_steps` (default 2), optional `smallest_meaningful_difference`, `exact` (identifiers or exact-lookup only - preserves every digit and flags `exact_override`), and `unit_multiplier` (base units per source unit for a pre-scaled column, e.g. `1e6` for "$MM"). Every value is rounded to one uniform place. Each preview row carries `shown` (source units) and `compact` (the largest short-scale unit the column supports, e.g. `70.4B`), plus `compact_suffix` and `compact_step`. `precision.number_formats(columns, rows)` runs this over a whole data table and returns the markdown formats block a driver hands the insight stage.

### `read_marks_from_anchors`

The arithmetic half of reading a value off a chart, used by `dataviz-extract`. The model does the perception - for an unlabelled mark, which two printed ticks bracket it and the `fraction` (0-1) between them - and this tool interpolates so no absolute magnitude is eyeballed. Inputs: `marks` (a list of `{key, lo, hi, fraction}`, where `lo`/`hi` are the bracketing tick **values**) and `transform` (`linear` or `log`; log interpolates in log10 space and needs positive anchors). Returns raw floats (rounding is a separate `recommend_precision` decision), preserving input order, plus non-silent `warnings` for far-out fractions and unusable brackets. A fraction just outside [0,1] is honoured as a short extrapolation (a series minimum below the lowest gridline, a peak above the top one), not clamped. A descending bracket (`hi < lo`, a reversed axis) reads correctly with no special handling.

### `recommend_scale_transform`

Advisory recommendation of a linear vs `log10` axis transform for a continuous axis. Inputs: `values` (every value that maps to the axis) and `encoding` (`position` for points/lines/dots/box/violin, or `length` for bars/area, which need a true zero and almost never take log). Computes the positive dynamic range, orders of magnitude, and quartile-skew reduction under logging, and returns a graded `strength`/`confidence`, the `transform` scalar the builder branches on, the `signals`, a `rationale`, and `caveats`. It is one input to the model's decision, not a gate - override it when the prompt wants absolute magnitudes, the audience won't read a log axis, or it would mislead. Log-only: with non-positive values `log10` cannot apply, so it returns `applicable: false` and notes that symlog/log1p exist rather than recommending them.

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

### Verify the chart build against its measured plan

`render_and_inspect_chart` and `refit_chart` accept an `inspection_contract` on
both backends. Pass `frame: <reserve_frame result>` and
`placements: <place_on_marks result.placements>`. The contract is stored with the
exact export's layout metadata, so standalone inspection repeats the checks.
The driver's contract overrides corresponding builder-supplied metadata.

`FRAME_PLAN_MISMATCH` blocks a stale canvas, panels in the reserved edge margin,
or panels running into the title, subtitle or footer. The `plot_area` itself is an
estimate a renderer that measures its own axes lays out slightly differently, so a
panel past it is not a defect. `TEXT_PLAN_MISMATCH` blocks changed copy, wrapping
or text placement. Placed text is matched by content and the returned top-left
position (2 px rounding tolerance), not ggplot IDs or `label`/`data_label`
classification; title, subtitle, caption and footer, which the renderer stacks
itself, are matched by content inside their reserved header or footer band. Repeated text must have a
separate rendered element for each planned occurrence. Forward glyph widths are
estimates, so actual glyph extents still use the export's clipping/collision checks.
`plan_checks` records
`not_supplied` when these inputs are absent; ordinary collision checks alone do
not verify the planned design. Remeasure a changed design before rendering it. With a supplied frame, refit
stops with `remeasure_required` if further canvas growth is needed.

For forward attachment checks, a label passed to `place_on_marks` may name its
intended rendered `mark_id`. The tool rejects missing/ambiguous targets or an
anchor that misses that target's bounds (or actual path for a line). This applies
regardless of label role. Derive the target and anchor from the same transformed
data; this check cannot establish semantic identity from pixels. Labels lacking
a target appear in `unverified_attachments`. Every data-anchored label receives
`placed_data`, including labels nudged to clear nearby text, so builders can apply
the returned position directly.

### Portable table rendering

`render_table_from_plan(plan, output_dir, page=1)` prefers the R constructor
(`Rscript`, `ggplot2`, `ragg`, `gridExtra`, `gtable`, `jsonlite`). Only when that
backend is unavailable does it use the Python constructor. `probe_renderers`
reports the selected table backend, `r_available` and `r_failure_reasons`;
table rendering remains available on a normal Python-only installation.
An R measurement or render failure is reported without retrying in Python.

Both constructors consume wrapped headers/cells, measured widths and heights,
frame bands, fonts, padding, continuation pages and the resolved `cell_styles` from
the same plan: right-aligned numbers, heat fills with their ink, bold/tinted focal
cells, data bars trailing the number, and sparklines. Python exports include measured
cell bounds, so overflow and delivery-size checks remain active. Treatment graphics
are captured as marks and series; `render_table_from_plan` passes the planned count
to inspection, which reports `TREATMENT_NOT_DRAWN` when any are missing.
The Python dependencies already include Matplotlib; R is optional.
