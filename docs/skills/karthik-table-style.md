# Karthik Table Style Skill

`karthik-table-style` owns the craft of a table once the chosen form is a table. A well-formatted table is a visualization, not the absence of one: alignment, precision, and restraint do the same perceptual work that position and colour do in a chart. It is the table twin of `karthik-data-visualization`.

It is designed for the failure mode where data that wants exact lookup, or that mixes non-commensurable units, gets forced into a chart - or where a table is produced but left unformatted: everything bold, decimals ragged, one text column wrapping the grid out of shape, heat shading that carries no meaning.

## What it covers

- **Emphasis as scarce ink** - bold or shade only the cells that carry the claim (a total, a winner, an outlier), never the whole table.
- **Alignment** - numbers right-aligned and aligned on the decimal point; text left; decimals equalised down each column so digit-length itself reads as magnitude.
- **Precision keyed to variance** - the number of decimals that resolves the smallest meaningful difference in the column, not the maximum the data carries.
- **Column widths sized to content** - long text columns wrap deliberately without distorting the grid; number columns stay narrow and scannable.
- **Rules and whitespace** - no full gridlines, no vertical rules; a few horizontal rules and whitespace do the grouping.
- **Tabular (lining) figures** - mono-width digits so columns align, with a clean text font.
- **Conditional formatting, scoped deliberately** - by column (compare within a metric), by row (each row its own scale), or whole table (only when cells are commensurable); heat is a weak channel, for spotting hot and cold across many cells, not precise reading.

## Measured planning

`recommend_table_layout` accepts formatted headers/cells or a local JSON content
file, typography, delivery constraints and a skill-selected treatment. It returns
measured geometry, wrapped content and continuation pages while preserving type
minimums. Screen delivery accounts for display width as well as export size.
Bars, dots, shading and sparklines follow the reading task and scale semantics;
column count does not determine the treatment. See the [MCP interface](../mcp.md).

## Rendering

- **Delivered HTML or interactive tables:** the R `gt` package.
- **A gated raster for inspection:** build the table as a `grid` / `tableGrob` object and render it through the same `ragg` path the charts use. In the MCP, that is `render_and_inspect_chart` with `content="table"`, which captures nested text, inherited font sizes and cell overflow, and reports unsupported geometry as incomplete coverage.

## Relationship to other skills

`dataviz-selector` decides whether the data should be a table or a chart before this skill is used. `karthik-data-visualization` is the chart twin. `chart-explainer` writes the note that travels with the table. `dataviz-critique` diagnoses an existing table. Inside a repair, `dataviz-fix` routes here when cold selection returns a table.
