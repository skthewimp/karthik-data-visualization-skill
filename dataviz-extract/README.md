# dataviz-extract

Use this skill during a chart repair, in parallel with `dataviz-brief`, to read the underlying data out of the source image. The rebuild is designed forward from this table plus the brief - not traced from the picture - so the table must be complete enough to build any chosen form on.

It is a vision task, not a rendering task: there is no MCP tool for it. The skill recovers the **full period-by-category table** - a value for every period and every category, series, stack, or facet the chart encodes, because colour is data, not decoration. A chart that stacks ten models by week needs ten values per week, not one total, so that a later form change (small multiples, direct-labelled lines, a ranked view) has every cell it needs.

## What it produces

- The category members, listed by name.
- The periods or x-positions, listed.
- A value for every (period × category) cell - no gaps; unreadable cells estimated and marked approximate.
- Units and any visible transformation (counts, %, index, log, share, cumulative).

Difficulty of reading a value is never a reason to drop the category it belongs to; deciding a category is not key is the brief's job, made in message terms.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

`dataviz-extract` is step 2 of `dataviz-fix`, running in parallel with `dataviz-brief`. Its table feeds `dataviz-selector` (form choice) and the build step.

## Edit rule

Update both `codex/SKILL.md` and `claude/SKILL.md` together; keep them byte-identical. Keep `docs/skills/dataviz-extract.md` aligned with the public behaviour.
