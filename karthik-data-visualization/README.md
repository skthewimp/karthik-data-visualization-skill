# karthik-data-visualization

Use this skill after the chart form is chosen, or when reviewing a chart's visual execution. It captures Karthik's chart style: direct, sparse, honest, and designed around the claim rather than decoration.

The skill is about the finished visual. It covers typography, colour, labels, annotation, axes, gridlines, density, export choices, and rendered-output inspection.

## What it does

- Uses claim-first titles and direct labels wherever possible.
- Keeps grey for context and colour for the story.
- Removes chartjunk, decorative palettes, unnecessary legends, and weak gridlines.
- Checks graphical integrity: scales, baselines, proportional encodings, and missing context.
- Encourages rendering and inspecting the actual chart, not just reading the code.

## Files

- [`codex/SKILL.md`](codex/SKILL.md) - Codex version of the skill.
- [`claude/SKILL.md`](claude/SKILL.md) - Claude version with Claude-safe frontmatter.
- [`codex/README.md`](codex/README.md) and [`claude/README.md`](claude/README.md) - surface-specific notes.

## Relationship to other skills

Use `dataviz-selector` before this if the chart form is still unclear. Use `dataviz-critique` when the task is to diagnose an existing chart and propose redesigns. Use `karthik-powerpoint-style` when the chart is part of a slide or deck.

## Edit rule

If style guidance changes, update both `codex/SKILL.md` and `claude/SKILL.md` unless the change is surface-specific. Local style references may exist in `references/`, but ignored private files should not be described as public assets.
