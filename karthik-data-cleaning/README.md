# karthik-data-cleaning

Use this skill when tabular data needs to be made analysable before charting, modelling, or writing. It is deliberately not an automated janitor. Cleaning is part of the analysis: the right choice depends on the question, the row grain, the source quirks, and the domain rules.

The core loop is: inspect the raw data, clean one layer, inspect again, encode the rule visibly, and validate before moving on.

## What it does

- Profiles schema, row count, grain, missingness, duplicates, date coverage, outliers, and category mess.
- Converts types, reshapes data, normalises strings, joins tables, and handles missingness only when the analysis justifies it.
- Keeps raw/canonical files untouched.
- Makes filters, recodes, join assumptions, and impossible-value rules visible in code.
- Validates row counts, key uniqueness, denominator sanity, and join mismatches before downstream analysis.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use this before `dataset-question-generator`, `karthik-analysis-planner`, `dataviz-orchestrator`, or charting when the data source is messy and the cleaning choices affect the claim. Do not create working files unless repeated parsing is genuinely costly.

## Edit rule

If cleaning behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep `docs/skills/karthik-data-cleaning.md` aligned with the public behaviour.
