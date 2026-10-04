# dataviz-orchestrator

Use this skill for the full dataset-to-visual-story loop. It is the coordinating skill, not a replacement for the more focused skills. It should plan the analysis, inspect and clean the data in context, compute the evidence, choose the story, select the chart, render it in Karthik's style, critique the output, and iterate.

Use it when the request is broader than “pick a chart” or “clean this plot”. For example: “here is a dataset, find the story and make the chart”.

## What it coordinates

- `karthik-analysis-planner` for definitions, denominator, metric, comparison, and falsifiers.
- `karthik-data-cleaning` for contextual inspection, cleaning, reshaping, joins, and validation.
- `dataviz-selector` for chart form and encodings.
- `karthik-data-visualization` for visual style and rendered chart checks.
- `dataviz-critique` for final chart critique and redesign pressure.
- `karthik-powerpoint-style` only when the final artifact is a slide or deck.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Edit rule

If the workflow changes, update both `codex/SKILL.md` and `claude/SKILL.md`. Also update `docs/skills/dataviz-orchestrator.md` and the repo README if the relationship between skills changes.
