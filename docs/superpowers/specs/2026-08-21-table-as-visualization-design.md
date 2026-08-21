# Design: tables as a first-class visualization

Date: 2026-08-21
Status: approved shape, pre-implementation

## Problem

A well-formatted table is a visualization. The suite currently has no table
craft and no table exit:

- **No craft skill.** `karthik-data-visualization` owns chart ink/colour/labels;
  there is no table twin. Karthik's table principles (emphasis, alignment,
  precision-vs-variance, column widths, rules/whitespace, tabular figures,
  conditional formatting) live nowhere.
- **`dataviz-selector` treats table as a passing aside**, not a real verdict.
  Data that should be a table gets forced into a chart.
- **`dataviz-fix` hard-routes to a chart.** It extracts the full data table then
  always rebuilds a chart; a chart that should have been a table becomes a
  tidier chart.
- **No raster path for tables.** The MCP rasters only via `ragg::agg_png`
  (ggplot) and matplotlib Agg. No headless HTML/screenshot mechanism exists, so
  a table output cannot be inspected/gated like a chart.

## Decisions (locked)

1. **New standalone skill `karthik-table-style`** (codex + claude + README),
   parallel to `karthik-data-visualization`. 15 skills -> 16.
2. **`dataviz-selector`** gains an explicit table-vs-chart heuristic and a
   `table` verdict routing to `karthik-table-style`.
3. **`dataviz-fix`** gains a `form = table` exit: build via `karthik-table-style`,
   render, inspect, gate.
4. **MCP raster path:** tables render via `gridExtra`/`grid` `tableGrob` through
   the **existing `ragg::agg_png` path** - zero new dependencies. No
   chromote/webshot. `gt` remains the recommended authoring idiom for delivered
   HTML/interactive tables; craft rules are engine-agnostic so both share them.
5. **Table inspection profile differs from charts:** column alignment,
   decimal-point alignment, no wrap/overflow collision, minimum font size -
   not axis/baseline/zero checks.

## Skill content: `karthik-table-style` (generalized heuristics)

- **Emphasis is scarce ink** - bold/shade only cells carrying the claim
  (a total, a winner, an outlier); never the whole table. Eraser test applies.
- **Alignment** - numbers right-aligned and aligned on the decimal point; text
  left; equalize decimal count down each column so digit-length reads as
  magnitude.
- **Precision keyed to variance** - decimals match the smallest meaningful
  difference in the column, not the maximum available.
- **Column widths sized to content** - wrap long text columns; never let one
  column's wrap distort the grid; keep number columns narrow and scannable.
- **Rules & whitespace** - no full gridlines, no vertical rules; a few
  horizontal rules (header, group, total) plus whitespace to group.
- **Tabular/lining figures** - mono-width digits so columns align; clean text
  font.
- **Conditional formatting, scope chosen deliberately** - by column (compare
  within a metric, most common), by row (each row its own scale), or
  whole-table (only when cells are commensurate). Heat is colour = weak channel:
  for spotting hot/cold across many cells, not precise reading. It earns its ink
  or it is removed.
- **R idiom:** `gt` for delivered HTML tables; `grid`/`tableGrob` for the gated
  raster; markdown/HTML fallback for non-R.

## Selection heuristic (into `dataviz-selector`)

Table wins when: the task is looking up exact values; few rows; values are not
commensurable on one scale (mixed units/metrics); reference or monitoring use;
or the chart would be a bar-chart-of-~8-numbers read precisely.
Chart wins when the message is a shape/trend/comparison the eye should grab
pre-attentively.

## Repair exit (into `dataviz-fix`)

Cold selection may return `form = table`. The existing extract step already
produces the full data table; the new branch builds the table via
`karthik-table-style`, renders through the grid/ragg path, runs the table
inspection profile, and gates it - same discipline as a chart.

## Build order (all ship)

1. `karthik-table-style` skill (codex + claude + README).
2. `dataviz-selector` table verdict + heuristic.
3. `dataviz-fix` `form = table` exit.
4. MCP grid/`tableGrob` render on ragg + table inspection profile.
5. Plumbing: `docs/skills/karthik-table-style.md`, folder + root README (15->16),
   CHANGELOG, DEVLOG, `sync.sh` validation, orchestrator routing note.

MCP raster sits last so the judgement layer is testable first.

## Non-goals

- No chromote/webshot/headless Chrome dependency.
- No interactive/sortable table runtime.
- No change to chart rendering or existing chart inspection.
