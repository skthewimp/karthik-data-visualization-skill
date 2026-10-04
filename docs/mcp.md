# The MCP helpers

The skills hold the judgement: question, evidence, claim, chart choice, annotation, critique, release. A few decisions inside that judgement are plain arithmetic, and a model doing them by eye gets them wrong in predictable ways - it picks two near-identical blues, rounds every value to its own place, or eyeballs a bar height. The MCP server does those sums.

| Tool | Decision it computes | Used by |
|---|---|---|
| `recommend_colours` | Which colour goes to which series, given brand or source colours, the background, a focal series and any colour meanings | `dataviz-color`, `dataviz-construct`, `karthik-data-visualization` |
| `recommend_precision` | One uniform rounding place for a column, from its spread | `dataviz-precision`, `dataviz-construct`, `karthik-data-visualization`, `karthik-table-style`, `karthik-evidence-builder`, `chart-annotations` |
| `recommend_scale_transform` | Linear or log10 for a continuous axis | `dataviz-selector` |
| `read_marks_from_anchors` | A mark's value, interpolated between the two printed ticks that bracket it | `dataviz-extract` |

Every tool is advisory. Each returns a recommendation and its reasons; the skill decides.

The server is optional. Without it, the skills apply the same rules by hand, and the rendered chart is checked by eye at delivery size.

## What it deliberately does not do

It does not render or inspect charts. An earlier version shipped renderer adapters, exact-artifact geometry inspection, canvas refitting, palette and scale validators, and image palette extraction. They were removed on 2026-10-04: the inspection loop added tool calls and round trips to every chart without the pixel read it was meant to replace, and the validators duplicated checks `recommend_colours` already runs internally.

## Implementation map

| Path | Responsibility |
|---|---|
| `dataviz_mcp/palette.py` | `recommend_colours`, plus the contrast, distinctness, CVD and grayscale scoring it runs on its own choice; uses `color_math.py` |
| `dataviz_mcp/precision.py` | `recommend_precision` |
| `dataviz_mcp/scale_transform.py` | `recommend_scale_transform` |
| `dataviz_mcp/mark_read.py` | `read_marks_from_anchors` |
| `dataviz_mcp/server.py` | Stdio MCP surface |
| `dataviz_mcp/tests/` | Tool and protocol tests |

Installation, client registration and tool parameters are in [`dataviz_mcp/README.md`](../dataviz_mcp/README.md).
