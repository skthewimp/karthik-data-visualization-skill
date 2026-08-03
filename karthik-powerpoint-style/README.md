# karthik-powerpoint-style

Use this skill when analysis needs to become slides: a PowerPoint-style deck, slide outline, chart slide, management recommendation, or speaker notes.

The style is claim-first and chart-led. Slides should have a clear point, sparse layout, direct labels, visible source notes, and enough caveat to avoid overclaiming. It is deliberately not a generic business-deck template.

## What it does

- Writes slide titles as analytical claims, not section labels.
- Chooses simple layouts: chart-first, scorecard, recommendation, comparison, or compact table.
- Keeps typography, colour, and annotation restrained.
- Makes source, timeframe, denominator, and caveat visible when they matter.
- Avoids dashboard clutter, decorative icons, vague agenda slides, and consultant filler.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `dataviz-selector` and `karthik-data-visualization` for the chart itself. Use this skill when the chart or analysis has to sit inside a slide narrative.

## Edit rule

If slide guidance changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Keep `docs/skills/karthik-powerpoint-style.md` aligned with the public behaviour.
