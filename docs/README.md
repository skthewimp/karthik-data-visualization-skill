# Documentation

Human-facing documentation for the public data visualization skills.

## Skill docs

- [`skills/dataviz-selector.md`](skills/dataviz-selector.md) - how to use the chart-selection skill
- [`skills/karthik-data-visualization.md`](skills/karthik-data-visualization.md) - how to use the chart-styling skill

## Project notes

- [`../DEVLOG.md`](../DEVLOG.md) - session devlog
- [`blog/building-the-dataviz-selector-skill.md`](blog/building-the-dataviz-selector-skill.md) - short blog-style writeup about building the selector skill

## Development workflow

1. Edit source skills at repo root.
2. Keep human documentation in `docs/`.
3. Run `./sync.sh --no-pull` to rebuild `dist/` and install local copies.
4. Commit source, docs, and rebuilt distributions when skill files change.

Do not put general README files inside skill directories unless they are meant to ship as skill resources.
