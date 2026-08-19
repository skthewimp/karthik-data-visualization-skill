# Dataviz MCP

This local stdio server handles the mechanical part of chart production. It probes ggplot2 and Matplotlib, chooses ggplot2 first for supported static output, executes trusted chart code, preserves renderer geometry, inspects the exact PNG, builds review views, and compares revisions. It does not decide the analytical question, claim, visual style, or release verdict.

See [`docs/mcp.md`](../docs/mcp.md) for the architectural boundary, generation and repair flows, hash/version guarantees, and the reasons for using render metadata.

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
- use `annotation:<id>` for callouts.

Untagged Matplotlib lines and annotations receive generated IDs, but those IDs are less stable across revisions.

## Tool contracts

### `probe_renderers`

Returns `Rscript`, ggplot2, ragg, and Matplotlib availability/version details, supported source/output types, and failure reasons. It makes no host changes.

### `render_and_inspect_chart`

Inputs include `source_path`, `output_dir`, `renderer` (`auto`, `ggplot2`, or `matplotlib`), `delivery_profile`, and explicit dimensions. `auto` applies the precedence above. The result contains the artifact, specification, normalized layout, inspection, artifact-bound review views, renderer-selection evidence, and hash-bound manifest.

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

The report includes artifact hash and dimensions, inspection mode, completeness, pass state, normalized defects, detailed collision and clipping lists, minimum text margin, limitations, and its own SHA-256 hash.

Supplying mismatched metadata is an error. Omitting metadata produces an explicit raster-only, incomplete report rather than a pass.

### `compare_chart_artifacts`

Inputs:

| Parameter | Required | Meaning |
|---|---:|---|
| `before_inspection_path` | Yes | Inspection JSON for the earlier artifact |
| `after_inspection_path` | Yes | Inspection JSON for the revision |
| `output_path` | No | Comparison JSON path; defaults beside the later report |

Both referenced PNGs are re-hashed before comparison. The result lists resolved, introduced, and persistent defects; blocking counts; dimensions; pixel difference; and whether the revision is mechanically improved. It does not make a substantive release decision.

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

The suite covers the MCP tools, a real stdio tool listing, repair-loop version binding, the local runner, deterministic geometry fixtures, and the end-to-end coffee annotation repair.

`dataviz_mcp.benchmark` loads caller-supplied repair-case roots read-only, de-duplicates case IDs, reports critique/design adoption and cycle counts, and compares a complete matched replay with its baseline. A replay only meets acceptance when every baseline case is present, evaluation cycles fall, and false `Send` events do not increase.

## Current limits

- Rendering supports trusted local Python/Matplotlib and R/ggplot2 PNG output.
- ggplot2 hierarchy, panel, and common child-mark geometry are deterministic; text boxes use deterministic font-metric estimates and uncommon grobs remain explicitly uncovered.
- Raster-only mode verifies identity and dimensions but does not use OCR or computer vision to infer geometry.
- Mechanical pass/fail does not replace visual critique, analytical evaluation, or user acceptance.

## Local security boundary

Rendering imports and executes the supplied Python or R file. Use it only with chart source you trust. The server is local-only, uses stdio, has no authentication layer, and does not sandbox arbitrary code.
