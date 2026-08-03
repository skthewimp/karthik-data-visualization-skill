# dataset-question-generator

Use this skill when a dataset arrives before the question. Its job is not to chart immediately. Its job is to inspect the raw data, notice what comparisons might be interesting, and return a short ranked list of fresh, visualisable questions.

It is useful for workshops, exploratory analysis, and early-stage data stories where the obvious question is often too stale to be worth charting.

## What it does

- Profiles row grain, coverage, entities, measures, categories, missingness, and format breaks.
- Looks for visual signals: slope changes, crossings, outliers, clusters, concentration, seasonality, and denominator traps.
- Rejects generic prompts such as “trend of X over time” unless the comparison is clear.
- Returns questions in Karthik's analysis style: concrete, measurable, and chartable.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `karthik-data-cleaning` first if the raw source needs parsing, reshaping, joins, or domain cleaning before its signals are legible. Then use this skill to find candidate questions. Use `karthik-analysis-planner` to make one question operational, `dataviz-selector` to choose the chart, and `karthik-data-visualization` to style the final visual.

## Edit rule

If behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep this README and `docs/skills/dataset-question-generator.md` in sync with the user-facing behaviour.
