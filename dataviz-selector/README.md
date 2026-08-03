# dataviz-selector

Use this skill when the question is: what chart should this be? It chooses a visual form from the analytical question, dataset shape, comparison, audience, and intended claim.

This is not a chart-style skill. It should decide whether the evidence is best shown as a line chart, sorted bars, scatter, small multiples, distribution, map, table, waterfall, or something else. Styling comes later.

## What it does

- Identifies the real comparison: time, peers, baseline, target, counterfactual, distribution, geography, or decomposition.
- Chooses chart form, encodings, ordering, scale, facets, labels, and context layers.
- Explains why worse alternatives should be avoided.
- Has hard guardrails against pie, donut, 3D, radar, gauge, decorative infographic, and animation-first recommendations.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `karthik-analysis-planner` first if the metric or denominator is still fuzzy. Use `karthik-data-visualization` after this skill picks the chart form. Use `dataviz-critique` when reviewing a chart that already exists.

## Edit rule

If chart-selection behaviour changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Local `references/` and `scripts/` may exist for development, but they are ignored and not part of the public repo.
