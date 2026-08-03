# Documentation

Human-facing documentation for the public data visualization skills. Start here when you want to understand the repo without reading every `SKILL.md`.

## Skill docs

- [`skills/dataviz-selector.md`](skills/dataviz-selector.md) - how to use the chart-selection skill
- [`skills/karthik-data-visualization.md`](skills/karthik-data-visualization.md) - how to use the chart-styling skill
- [`skills/karthik-powerpoint-style.md`](skills/karthik-powerpoint-style.md) - how to use the presentation-slide style skill
- [`skills/dataviz-critique.md`](skills/dataviz-critique.md) - how to critique and redesign existing visuals
- [`skills/karthik-analysis-planner.md`](skills/karthik-analysis-planner.md) - how to turn fuzzy data questions into analysis contracts
- [`skills/dataviz-orchestrator.md`](skills/dataviz-orchestrator.md) - how to run the full dataset-to-visual-story workflow
- [`skills/dataset-question-generator.md`](skills/dataset-question-generator.md) - how to generate fresh visualisable questions from raw datasets
- [`skills/karthik-data-cleaning.md`](skills/karthik-data-cleaning.md) - how to clean tabular data in context before analysis or charting
- [`skills/chart-annotations.md`](skills/chart-annotations.md) - how to decide what a chart marks and what the label says

## Project notes

- [`../CHANGELOG.md`](../CHANGELOG.md) - release-style summary of public repo changes
- [`../DEVLOG.md`](../DEVLOG.md) - session devlog with prompts and work done
- [`blog/`](blog/) - longer project writeups
- [`plans/`](plans/) - planning docs for future skill work

## Development workflow

1. Edit skills in `<skill>/codex/SKILL.md` and `<skill>/claude/SKILL.md`.
2. Keep human documentation in `docs/`.
3. Run `./sync.sh --no-pull --validate-only` to check skill metadata.
4. Run `./sync.sh --no-pull` to install local copies.
5. Commit source and docs only; do not commit generated distributions.

Keep README files in public folders. They are part of the repo navigation contract for newcomers.
