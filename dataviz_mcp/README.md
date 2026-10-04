# Dataviz MCP

This local stdio server does the arithmetic behind two chart decisions: which colours go to which series, and how many digits to show. It does not render or inspect charts, and it does not decide the analytical question, claim, visual style, or release verdict.

See [`docs/mcp.md`](../docs/mcp.md) for the boundary between the tools and the skills.

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

## Tool contracts

Both report and recommend; none hard-blocks.

### `recommend_colours`

Picks and assigns colours for one graph from an `available` set (brand/context/default). Inputs: `available`, `n_series`, `background` (default `#FFFFFF`), optional `focal` (pinned to series 0), and `semantic_hints` (a list of `{series_index, colour}` hard pins or `{series_index, hue_family}` soft families, each with optional `alternates`). Chooses by max-min separation and background contrast; priority is series distinctness (hard), then meaning over contrast/CVD. Unmet or collided hints are reported in `semantic_findings`. Optional `available_source` (the colour plan's): brand and prompt colours (`brand-skill`, `prompt`, `provided`, or a supplied pool with no source) fill the first slots as given and generation only covers a count shortage; any other supplied pool (`source-extracted`, a proposed set) is a prior - a slot takes a pool colour only if it reads on the background and passes the distinctness and CVD tests against the placed series, else a generated colour that does. The default pool is left as it is. Use even when colours are given - a specific chart still needs a which-and-how-assigned decision.

### `recommend_precision`

Recommends significant digits / a uniform rounding place for a numeric column, derived from the spread (max - min), not individual values. Inputs: `values`, `role` (`axis`/`label`/`table_column`), `target_steps` (default 2), optional `smallest_meaningful_difference`, `exact` (identifiers or exact-lookup only - preserves every digit and flags `exact_override`), and `unit_multiplier` (base units per source unit for a pre-scaled column, e.g. `1e6` for "$MM"). Every value is rounded to one uniform place. Each preview row carries `shown` (source units) and `compact` (the largest short-scale unit the column supports, e.g. `70.4B`), plus `compact_suffix` and `compact_step`.

## Run the tests

Use the same environment as the MCP clients:

```bash
"$MCP_PYTHON" -m pytest -q
```

The suite covers each tool's arithmetic and a real MCP tool listing.
