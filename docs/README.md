# Documentation

Human-facing documentation for the public data visualization skills.

## Skill docs

- [`skills/dataviz-selector.md`](skills/dataviz-selector.md) - how to use the chart-selection skill
- [`skills/karthik-data-visualization.md`](skills/karthik-data-visualization.md) - how to use the chart-styling skill
- [`skills/karthik-powerpoint-style.md`](skills/karthik-powerpoint-style.md) - how to use the presentation-slide style skill

## Project notes

- [`../DEVLOG.md`](../DEVLOG.md) - session devlog
- [`blog/building-the-dataviz-selector-skill.md`](blog/building-the-dataviz-selector-skill.md) - short blog-style writeup about building the selector skill

## Development workflow

1. Edit skills in `<skill>/codex/SKILL.md` and `<skill>/claude/SKILL.md`.
2. Keep human documentation in `docs/`.
3. Run `./sync.sh --no-pull` to install local copies.
4. Commit source and docs only; do not commit generated distributions.

Keep README files in public folders. They are part of the repo navigation contract for newcomers.
