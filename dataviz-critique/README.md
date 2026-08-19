# dataviz-critique

Use this skill when there is already a visual on the table: a chart, dashboard, slide graphic, AI-generated plot, or infographic-style draft. The skill diagnoses what works, what fails, and what a better version should do.

It combines Kaiser Fung's question-data-visual trifecta with Karthik's preference for direct, honest, low-decoration charts. The output is not just “make it cleaner”. It should say whether the question, data, and visual form actually fit each other.

## What it does

- Identifies the apparent question, data, visual encoding, and likely viewer interpretation.
- Flags denominator issues, bad aggregation, distorted scales, missing baselines, over-colouring, and unsupported claims.
- Separates fatal issues from smaller presentation fixes.
- Proposes only alternatives that solve a diagnosed mismatch, without filling a fixed option count.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use this after a chart exists. Use `dataviz-selector` earlier if the task is still “what chart should this be?” Use `karthik-data-visualization` when the fix is mainly visual styling. Use `dataviz-orchestrator` when the whole dataset-to-chart workflow needs to be run end to end.

## Edit rule

If critique behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep `docs/skills/dataviz-critique.md` aligned with the public behaviour.
