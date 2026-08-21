# karthik-table-style

Use this skill once the chosen form is a table, or when reviewing a table's
formatting. A well-formatted table is a visualization: alignment, precision, and
restraint do the perceptual work that position and colour do in a chart.

The skill is about the finished table. It covers emphasis, decimal alignment,
precision keyed to variance, column widths, rules and whitespace, tabular
figures, and conditional formatting.

## What it does

- Emphasises only the cells that carry the claim; keeps a neutral ground.
- Right-aligns numbers on the decimal point and equalises decimals down a column
  so digit-length reads as magnitude.
- Sets precision from the smallest meaningful difference, not the maximum the
  data carries.
- Sizes columns to content and stops one column's wrap from distorting the grid.
- Removes full gridlines and vertical rules; groups with a few horizontal rules
  and whitespace.
- Chooses conditional-formatting scope deliberately - by column, by row, or
  whole table - and only when scanning for magnitude is the task.
- Encourages rendering and inspecting the actual table, not just the code.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `dataviz-selector` before this to decide whether the data should be a table
or a chart. Use `karthik-data-visualization` for the chart twin of this skill.
Use `chart-explainer` for the note that travels with the table, and
`dataviz-critique` to diagnose an existing table. Inside a repair, `dataviz-fix`
routes here when cold selection returns a table.

## Edit rule

If table guidance changes, update both `codex/SKILL.md` and `claude/SKILL.md`
unless the change is surface-specific.
