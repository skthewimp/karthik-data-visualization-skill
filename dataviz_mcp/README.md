# Dataviz MCP

This local stdio server handles the mechanical part of chart production. Its current renderer adapter executes trusted Matplotlib code, preserves renderer geometry, inspects the exact PNG, and compares revisions. It does not decide what question to ask, what the chart should say, which rendering library defines the visual style, or whether an annotation makes a defensible causal claim.

See [`docs/mcp.md`](../docs/mcp.md) for the architectural boundary, generation and repair flows, hash/version guarantees, and the reasons for using render metadata.

## Requirements and installation

- Python 3.10 or newer
- a Python virtual environment
- Codex, Claude Code, or Hermes Agent as the MCP client

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

## Deploy on Hermes

On a Hermes host, clone the repository, install the package into an isolated environment, and sync the Claude-compatible skill surface:

```bash
git clone https://github.com/skthewimp/karthik-data-visualization-skill.git
cd karthik-data-visualization-skill
python3 -m venv .venv
.venv/bin/python -m pip install -e .
./sync.sh --no-pull --surface hermes
```

Add the server under the existing `mcp_servers:` key in `~/.hermes/config.yaml`, using the checkout's absolute interpreter path:

```yaml
  karthik_dataviz:
    command: /absolute/path/to/karthik-data-visualization-skill/.venv/bin/python
    args:
      - -m
      - dataviz_mcp
    timeout: 180
    connect_timeout: 30
```

Restart the Hermes gateway or client and begin a new session so it reloads both the MCP server and newly synced skill text.

### Karthik's current Hermes host

Hermes runs on the SSH host `server`. Its checkout is `/home/karthik/apps/karthik-data-visualization-skill` and its skills live under `~/.hermes/skills/data-science/`.

Pull the committed repository, create the server's isolated MCP environment, install the package, and sync the skills:

```bash
ssh server
cd /home/karthik/apps/karthik-data-visualization-skill
git pull --ff-only
~/.hermes/hermes-agent/venv/bin/python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
./sync.sh --no-pull --surface hermes
```

The host's system Python lacks `ensurepip`, so the command uses Hermes's bundled Python only to create the new environment. The environments remain separate. The Hermes agent environment at `~/.hermes/hermes-agent/venv` currently uses MCP SDK 1.x; the dataviz server requires MCP SDK 2.x. Installing the package into the agent environment would force an avoidable dependency upgrade.

Karthik's deployed config uses:

```yaml
  karthik_dataviz:
    command: /home/karthik/apps/karthik-data-visualization-skill/.venv/bin/python
    args:
      - -m
      - dataviz_mcp
    timeout: 180
    connect_timeout: 30
```

Restart the gateway and check that both the service and stdio server start cleanly:

```bash
systemctl --user restart hermes-gateway.service
systemctl --user is-active hermes-gateway.service

cd /home/karthik/apps/karthik-data-visualization-skill
.venv/bin/python -m pytest -q
```

Hermes starts the configured stdio process when it loads the MCP server.

## Renderer boundary

The MCP API should remain backend-neutral even though the current adapter is Matplotlib-specific. Rendering infrastructure must not become the style system.

- Preserve a project's established renderer.
- For a new Karthik-style static chart with no project precedent, prefer R/ggplot2 when available.
- Do not convert a sound ggplot2 chart to Matplotlib just to obtain richer geometry metadata.
- If Matplotlib is used, apply the rules in `karthik-data-visualization`; an unthemed default chart is not an acceptable MCP result.

The current trade-off is explicit: Matplotlib text and line paths receive deterministic geometry inspection. A ggplot2 PNG can be inspected in raster-only mode and evaluated visually, but collision and clipping checks remain unknown. The next renderer extension should be a ggplot2 adapter that emits the same PNG, spec, layout, and manifest contract. It should not introduce a separate ggplot-only MCP API or move theme judgement into the server.

## Chart builder contract

Create a Python file containing a no-argument builder. By default the function is named `build_chart`. It must return either a Matplotlib `Figure` or `(figure, chart_spec_dict)`.

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

## Repair-loop integration

The existing case manager preserves the bundle and inspection beside an iteration:

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

## Current limits

- Rendering supports trusted local Python and Matplotlib PNG output only.
- Annotation-to-series collision checks cover recorded line paths. Non-line marks make the report incomplete.
- Raster-only mode verifies identity and dimensions but does not use OCR or computer vision to infer geometry.
- Mechanical pass/fail does not replace visual critique, analytical evaluation, or user acceptance.

## Local security boundary

`render_chart` imports and executes the supplied Python file. Use it only with chart source you trust. The server is local-only, uses stdio, has no authentication layer, and does not sandbox arbitrary Python.
