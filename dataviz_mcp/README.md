# Dataviz MCP

This local stdio server handles the mechanical part of chart production. It probes ggplot2 and Matplotlib, chooses ggplot2 first for supported static output, executes trusted chart code, preserves renderer geometry, inspects the exact PNG, and builds review views. It does not decide the analytical question, claim, visual style, or release verdict.

See [`docs/mcp.md`](../docs/mcp.md) for the architectural boundary, generation and repair flows, hash/version guarantees, and the reasons for using render metadata.

## Requirements and installation

- Python 3.10 or newer
- an existing Python environment
- Codex, Claude Code, or another MCP-compatible client

From the repository root, install the package and retain the absolute interpreter path:

```bash
python3 -m pip install -e .
MCP_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
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

### `inspect_rendered_chart`

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `artifact_path` | Yes | Exact PNG to inspect |
| `layout_metadata_path` | No | Matching `layout_metadata_path` from `render_and_inspect_chart` |
| `output_path` | No | Inspection JSON path; defaults beside the PNG |
| `series_clearance_px` | No | Padding around annotation boxes for line collision checks; defaults to 2 |
| `max_unwrapped_annotation_chars` | No | Unwrapped annotation limit; defaults to 45 |
| `delivery_profile` | No | Delivery context recorded with the inspection |
| `minimum_text_size_pt` | No | Delivery-scale text threshold; defaults to 8 pt |

The report includes artifact hash and dimensions, inspection mode, completeness, pass state, normalized defects, detailed collision and clipping lists, minimum text margin, limitations, and its own SHA-256 hash. Every defect carries a `defect_class` - `canvas` (grow it out), `placement` (move a label), or `semantic` (a model judgement) - and the report groups them into a `correction_plan` of those three classes so a driver routes the cycle without re-deriving the split: the `canvas` group rides a shared `growth_vector` (the same `suggested_dims`, null when nothing can grow), `placement` goes back to the chart code as a label move, and only `semantic` earns a model patch.

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

Scope is only what growing fixes - edge clipping, overflow, squashed panels. Underfill (no exact shrink vector) is reported (`underfilled` + a warning) but never resized; label collisions are left to the chart code. The loop exits when geometry is clean, the delivery ceiling is reached (warned, never squashed), `max_iterations` is hit, or a grow stops reducing the residual. Returns the final artifact, inspection path, `final_dimensions`, a per-pass `history`, `warnings`, and a `resolved` flag.

## Colour and precision advisors

Analytical mechanism for two decisions a chart always needs. They report and recommend; they never hard-block.

### `recommend_colours`

Picks and assigns colours for one graph from an `available` set (brand/context/default). Inputs: `available`, `n_series`, `background` (default `#FFFFFF`), optional `focal` (pinned to series 0), and `semantic_hints` (a list of `{series_index, colour}` hard pins or `{series_index, hue_family}` soft families, each with optional `alternates`). Chooses by max-min separation and background contrast; priority is series distinctness (hard), then meaning over contrast/CVD. Unmet or collided hints are reported in `semantic_findings`. Optional `available_source` (the colour plan's): brand and prompt colours (`brand-skill`, `prompt`, `provided`, or a supplied pool with no source) fill the first slots as given and generation only covers a count shortage; any other supplied pool (`source-extracted`, a proposed set) is a prior - a slot takes a pool colour only if it reads on the background and passes `validate_palette`'s distinctness and CVD tests against the placed series, else a generated colour that does. The default pool is left as it is. Use even when colours are given - a specific chart still needs a which-and-how-assigned decision.

### `validate_palette`

Scores a palette on WCAG contrast, series distinctness, CVD, and grayscale survival. Inputs: `colours`, `background`, optional `text_colours`, `min_contrast_text` (default 4.5), `min_contrast_mark` (default 3.0). Returns a verdict plus ranked findings, each with a concrete nudge. Targets are soft: findings are reported, not hard-blocked.

### `recommend_continuous_scale`

Recommends a continuous colour scale for one ordered quantity (heatmap fill, colour-mapped value) - not categorical series, which go through `recommend_colours`. Inputs: `values`, optional `available` (brand/context colours for the poles), `background`, optional `reference` (a real centre), and `kind` (`auto`, `sequential`, `diverging`). Returns the scale `kind`, a data-derived `domain` and `midpoint`, ordered `stops`, and an off-scale `missing_colour` for NA cells. `auto` diverges only when the data has a real centre (a `reference` or values straddling zero); a forced `diverging` scale without a reference centres on the data median.

### `validate_scale`

Checks a continuous scale by its ends, not as categorical series. Inputs: `stops`, `scale_kind`, `background`, `min_contrast_mark` (default 3.0). At least one stop must read on the background and the two poles must stay apart in lightness so the extremes survive grayscale and CVD. Interior stops are not flagged for being close - a ramp is meant to have close neighbours.

### `extract_palette_from_image`

Samples dominant hues from a source chart image as a repair prior (brand/WCAG may override). Inputs: `image_path`, `max_colours` (default 8), `ignore_near_white_black` (default true).

### `recommend_precision`

Recommends significant digits / a uniform rounding place for a numeric column, derived from the spread (max - min), not individual values. Inputs: `values`, `role` (`axis`/`label`/`table_column`), `target_steps` (default 2), optional `smallest_meaningful_difference`, `exact` (identifiers or exact-lookup only - preserves every digit and flags `exact_override`), and `unit_multiplier` (base units per source unit for a pre-scaled column, e.g. `1e6` for "$MM"). Every value is rounded to one uniform place. Each preview row carries `shown` (source units) and `compact` (the largest short-scale unit the column supports, e.g. `70.4B`), plus `compact_suffix` and `compact_step`.

### `read_marks_from_anchors`

The arithmetic half of reading a value off a chart, used by `dataviz-extract`. The model does the perception - for an unlabelled mark, which two printed ticks bracket it and the `fraction` (0-1) between them - and this tool interpolates so no absolute magnitude is eyeballed. Inputs: `marks` (a list of `{key, lo, hi, fraction}`, where `lo`/`hi` are the bracketing tick **values**) and `transform` (`linear` or `log`; log interpolates in log10 space and needs positive anchors). Returns raw floats (rounding is a separate `recommend_precision` decision), preserving input order, plus non-silent `warnings` for far-out fractions and unusable brackets. A fraction just outside [0,1] is honoured as a short extrapolation (a series minimum below the lowest gridline, a peak above the top one), not clamped. A descending bracket (`hi < lo`, a reversed axis) reads correctly with no special handling.

### `recommend_scale_transform`

Advisory recommendation of a linear vs `log10` axis transform for a continuous axis. Inputs: `values` (every value that maps to the axis) and `encoding` (`position` for points/lines/dots/box/violin, or `length` for bars/area, which need a true zero and almost never take log). Computes the positive dynamic range, orders of magnitude, and quartile-skew reduction under logging, and returns a graded `strength`/`confidence`, the `transform` scalar the builder branches on, the `signals`, a `rationale`, and `caveats`. It is one input to the model's decision, not a gate - override it when the prompt wants absolute magnitudes, the audience won't read a log axis, or it would mislead. Log-only: with non-positive values `log10` cannot apply, so it returns `applicable: false` and notes that symlog/log1p exist rather than recommending them.

## Run the tests

Use the same environment as the MCP clients:

```bash
MPLCONFIGDIR=/tmp/mpl-cache "$MCP_PYTHON" -m pytest -q
```

The default suite covers MCP tools, a real stdio tool listing, deterministic geometry fixtures, and the end-to-end coffee annotation repair (render, inspect, fix placement, re-inspect).


## Current limits

- Rendering supports trusted local Python/Matplotlib and R/ggplot2 PNG output.
- ggplot2 hierarchy, panel, and common child-mark geometry are deterministic; text boxes use deterministic font-metric estimates and uncommon grobs remain explicitly uncovered.
- Raster-only mode verifies identity and dimensions but does not use OCR or computer vision to infer geometry.
- Mechanical pass/fail does not replace visual critique, analytical evaluation, or user acceptance.

## Local security boundary

Rendering imports and executes the supplied Python or R file. Use it only with chart source you trust. The server is local-only, uses stdio, has no authentication layer, and does not sandbox arbitrary code.

### Review views

`build_review_views(..., display_width_px=...)` generates a proportional delivery view at the actual viewing width (640px when unspecified), alongside native diagnostic crops. `render_and_inspect_chart` forwards `dimensions.display_width_px`. External reviewers should judge this delivery view; native crops diagnose defects, not establish readability. Review wrappers must keep creator repair scopes out of user constraints.
